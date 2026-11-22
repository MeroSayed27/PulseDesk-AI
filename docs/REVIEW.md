# Code review of the uploaded archive

The supplied `pulsedesk-review.zip` contained seven Python source files only. This portfolio pack **rebuilds and expands** that code; it does not include any original databases, trained models or CSV datasets because they were not in the archive.

## Findings in the supplied version

1. `backend/main.py` registered `POST /ai/draft` **twice**. FastAPI's first matching route can make the later error handler ineffective.
2. `backend/ai/draft_reply.py` created `genai.Client()` at **module import time**, which prevented FastAPI from starting whenever the shell lacked `GEMINI_API_KEY`.
3. Gemini outages (`503`) were exposed as unexplained `500 Internal Server Error` responses.
4. There was no frontend, test suite, documented installation, or sample knowledge document file.
5. The classifier's `.joblib` file and its training/test datasets were missing. The supplied classifier loaded its artifact at import time, which could crash the app when the model file was absent.
6. The local knowledge retriever always returned a result, even when nothing relevant matched.
7. The original classifier is a banking-intent model; a BANKING77 label is **not** a generic customer support category.

## Fixes and additions in this pack

- One deterministic ad-hoc `/ai/draft` route, plus a persisted ticket-specific drafting workflow.
- Lazy Gemini client creation at request time; no key is required to start the server.
- Visible and explicitly labeled `template_demo` / `template_fallback` responses during missing keys or outages.
- New SQLite database filename (`pulsedesk_portfolio.db`) so the older `pulsedesk.db` schema is not silently overwritten.
- Responsive one-page dashboard, ticket management, knowledge sources, editable human approval, and metrics.
- Optional trained model; never claim ML outputs when the model file is absent.
- Offline automated workflow and provider-mock tests.
- GitHub-ready README, ignore rules, licensing, CI, and profile descriptions.

## Remaining work before a real deployment

- Auth and authorization, per-user/per-company isolation, real audit logging, data retention and privacy controls.
- DB migrations, more robust exception and retry policies, tested deployment, structured observability and rate limiting.
- Real company knowledge ingestion, retrieval evaluations, human-rated LLM quality evaluations, and abuse protections.
- Real email integration only after security review; no outbound email is sent in the current app.
