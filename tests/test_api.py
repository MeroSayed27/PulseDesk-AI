"""Offline integration tests: no Gemini key or trained ML model required."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from backend import database
from backend.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    db_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    monkeypatch.setattr(database, "engine", db_engine)
    with TestClient(app) as test_client:
        yield test_client
    db_engine.dispose()


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["email_sending_enabled"] is False


def test_ticket_draft_approval_workflow(client):
    ticket_response = client.post("/api/tickets", json={
        "subject": "Missing payment", "message": "My payment is missing. Can you help?"
    })
    assert ticket_response.status_code == 201
    ticket = ticket_response.json()
    assert ticket["category"] == "billing"
    result = client.post(f"/api/tickets/{ticket['id']}/draft")
    assert result.status_code == 201
    draft = result.json()
    assert draft["status"] == "pending_approval"
    assert draft["provider"] == "template_demo"
    assert "payment_missing" in draft["knowledge_sources"]
    edited = "Thanks. Please share the transaction reference."
    reviewed = client.post(f"/api/drafts/{draft['id']}/review", json={
        "decision": "approve", "edited_text": edited
    })
    assert reviewed.status_code == 200
    assert reviewed.json()["edited_body"] == edited
    assert reviewed.json()["status"] == "approved"
    assert client.post(f"/api/drafts/{draft['id']}/review", json={
        "decision": "approve"
    }).status_code == 409
    assert client.get("/api/metrics").json()["approved_drafts"] == 1
    assert client.get(f"/api/tickets/{ticket['id']}").json()["ticket"]["status"] == "reviewed"


def test_empty_knowledge_and_validation(client):
    assert client.get("/api/knowledge/search", params={"question": "xyzzq"}).status_code == 200
    assert client.post("/api/tickets", json={"subject": "x", "message": "short"}).status_code == 422
    assert client.post("/api/tickets/999/draft").status_code == 404


def test_legacy_draft_endpoint(client):
    response = client.post("/ai/draft", json={
        "subject": "Login issue", "message": "Cannot log in to my account."
    })
    assert response.status_code == 200
    assert response.json()["provider"] == "template_demo"
    assert response.json()["status"] == "pending_approval"
