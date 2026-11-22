# PulseDesk AI — Portfolio text (edit as needed)

## GitHub repository description (under 350 characters)

Human-in-the-loop customer-support MVP: FastAPI + SQLite ticket workflow, bilingual TF-IDF knowledge retrieval, optional Gemini reply drafts, editable human approvals, ticket analytics, responsive dashboard, and offline tests. Includes a clearly labeled template fallback when the AI API is unavailable.

## LinkedIn post

Built **PulseDesk AI**, a human-in-the-loop AI support dashboard. 🚀

It takes a customer ticket, identifies a support category, retrieves matching English/Arabic knowledge, and proposes a response using Google Gemini (or a clearly labeled offline demo template). A human can edit, approve, or reject every draft — **nothing gets sent automatically**.

**Stack:** Python, FastAPI, SQLAlchemy/SQLite, scikit-learn TF-IDF, Google GenAI SDK, HTML/CSS/JavaScript, Pytest, GitHub Actions.

The project includes a polished dashboard, source-linked suggestions, local ticket analytics, and automated workflow tests. This is a portfolio MVP, with auth, production retrieval evaluation, and deployment planned as future work.

GitHub: [ADD YOUR REPOSITORY LINK]

#Python #FastAPI #MachineLearning #RAG #GenAI #SoftwareEngineering

## Mercor — Project entry

**PulseDesk AI — AI Customer Support Copilot | Python / FastAPI / Retrieval / Gemini**

Developed a working local customer-support prototype covering intake, persisted tickets, categorization, bilingual TF-IDF knowledge retrieval, optional Gemini-generated drafts, explicit human review decisions, and live dashboard metrics. Built a resilient fallback mode for third-party AI outages and API tests that run entirely offline. Structured the backend into API, retrieval, model, and persistence modules and documented setup, limitations, and reproducibility.

**Scope:** Portfolio MVP, not multi-tenant production SaaS.

## Levels.fyi / personal project summary

**PulseDesk AI — AI-assisted support workflow (personal project)**

Designed and implemented a FastAPI/SQLite support-ticket workflow with bilingual knowledge retrieval, optional LLM-generated suggestions, a human approval queue, and a responsive dashboard. Added provenance-aware fallback behavior, test coverage for core API flows, and GitHub Actions CI. Separately supported inference with an optional locally trained BANKING77 classifier where available.

## Resume bullets (choose one or two)

- Built PulseDesk AI, a FastAPI-based customer support MVP combining bilingual TF-IDF retrieval, optional Gemini-generated reply suggestions, SQLite persistence, and human approval workflows.
- Implemented a responsive analytics dashboard and offline integration tests covering ticket intake, retrieval-backed drafting, edits, approval, and duplicate-review rejection.
- Designed a fault-tolerant LLM integration that labels template fallbacks separately from Gemini output during quota or availability incidents.

## Demo walkthrough (~45 seconds)

1. Open the local dashboard.
2. Click **Use sample** and **Create ticket**.
3. Select the ticket and click **Generate AI draft**.
4. Point out the retrieved knowledge source IDs and AI vs. template provider label.
5. Edit the draft and click **Approve edited draft**; confirm analytics update.
6. Explain that approval intentionally **does not send an email**.

Never claim the demo is deployed publicly, that Gemini was used when template mode is active, or that a banking model was evaluated from files not supplied.
