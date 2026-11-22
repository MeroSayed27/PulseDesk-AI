"""PulseDesk AI demo API: tickets -> retrieval -> drafts -> human review."""
from contextlib import asynccontextmanager
import json
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from backend.database import Ticket, Draft, create_db_and_tables, get_session, utc_now
from backend.ml.predict import predict_category, predict_with_confidence, get_model
from backend.ai.retriever import list_knowledge, search_knowledge
from backend.ai.draft_reply import generate_draft

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="PulseDesk AI",
    version="0.1.0",
    description="Human-in-the-loop customer support demo. No messages are actually sent.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=160)
    message: str = Field(min_length=8, max_length=5000)


class DraftReview(BaseModel):
    decision: Literal["approve", "reject"]
    edited_text: str | None = Field(default=None, max_length=10000)


def ticket_output(ticket: Ticket) -> dict:
    return jsonable_encoder({key: getattr(ticket, key) for key in (
        "id", "subject", "message", "category", "ml_intent", "ml_confidence", "status", "created_at"
    )})


def draft_output(draft: Draft) -> dict:
    data = jsonable_encoder({key: getattr(draft, key) for key in (
        "id", "ticket_id", "body", "provider", "status", "knowledge_sources",
        "warning", "edited_body", "reviewed_at", "created_at"
    )})
    data["knowledge_sources"] = json.loads(draft.knowledge_sources)
    return data


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    import os
    return {
        "status": "ok",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
        "banking_model_loaded": get_model() is not None,
        "email_sending_enabled": False,
    }


@app.get("/api/tickets")
@app.get("/tickets", include_in_schema=False)
def get_tickets(session: Session = Depends(get_session)):
    tickets = session.scalars(select(Ticket).order_by(Ticket.id.desc())).all()
    return {"tickets": [ticket_output(t) for t in tickets]}


@app.post("/api/tickets", status_code=201)
@app.post("/tickets", include_in_schema=False, status_code=201)
def create_ticket(ticket: TicketCreate, session: Session = Depends(get_session)):
    ml = predict_with_confidence(ticket.message)
    db_ticket = Ticket(
        subject=ticket.subject.strip(),
        message=ticket.message.strip(),
        category=predict_category(ticket.message),
        ml_intent=ml["intent"],
        ml_confidence=ml["confidence"],
    )
    session.add(db_ticket)
    session.commit()
    session.refresh(db_ticket)
    return ticket_output(db_ticket)


@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: int, session: Session = Depends(get_session)):
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    drafts = session.scalars(select(Draft).where(Draft.ticket_id == ticket_id).order_by(Draft.id.desc())).all()
    return {"ticket": ticket_output(ticket), "drafts": [draft_output(d) for d in drafts]}


@app.get("/api/knowledge")
def get_knowledge():
    return {"documents": list_knowledge()}


@app.get("/api/knowledge/search")
@app.get("/knowledge/search", include_in_schema=False)
def knowledge_search(question: str = Query(min_length=2, max_length=500)):
    sources = search_knowledge(question)
    return {"sources": sources, "answer": sources[0]["content"] if sources else None}


@app.post("/api/tickets/{ticket_id}/draft", status_code=201)
def draft_for_ticket(ticket_id: int, session: Session = Depends(get_session)):
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    result = generate_draft(ticket.message)
    draft = Draft(
        ticket_id=ticket.id,
        body=result.text,
        provider=result.provider,
        knowledge_sources=json.dumps([s["id"] for s in result.sources]),
        warning=result.warning,
    )
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return draft_output(draft)


@app.post("/ai/draft", include_in_schema=True)
def standalone_draft(ticket: TicketCreate):
    """Compatibility with the earlier standalone testing command; does not save/send."""
    result = generate_draft(ticket.message)
    return {
        "draft": result.text,
        "provider": result.provider,
        "sources": result.sources,
        "warning": result.warning,
        "status": "pending_approval",
    }


@app.post("/api/drafts/{draft_id}/review")
def review_draft(draft_id: int, review: DraftReview, session: Session = Depends(get_session)):
    draft = session.get(Draft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status != "pending_approval":
        raise HTTPException(status_code=409, detail="Draft has already been reviewed")
    if review.decision == "approve":
        if review.edited_text is not None and not review.edited_text.strip():
            raise HTTPException(status_code=422, detail="Approved reply cannot be empty")
        draft.edited_body = review.edited_text.strip() if review.edited_text is not None else None
        draft.status = "approved"
        ticket = session.get(Ticket, draft.ticket_id)
        if ticket:
            ticket.status = "reviewed"  # NOT sent
            session.add(ticket)
    else:
        draft.status = "rejected"
    draft.reviewed_at = utc_now()
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return draft_output(draft)


@app.get("/api/metrics")
def metrics(session: Session = Depends(get_session)):
    tickets = session.scalars(select(Ticket)).all()
    drafts = session.scalars(select(Draft)).all()
    by_category = {category: sum(t.category == category for t in tickets)
                   for category in ("billing", "account", "delivery", "general")}
    return {
        "total_tickets": len(tickets),
        "open_tickets": sum(t.status == "open" for t in tickets),
        "pending_drafts": sum(d.status == "pending_approval" for d in drafts),
        "approved_drafts": sum(d.status == "approved" for d in drafts),
        "rejected_drafts": sum(d.status == "rejected" for d in drafts),
        "knowledge_articles": len(list_knowledge()),
        "category_breakdown": by_category,
    }
