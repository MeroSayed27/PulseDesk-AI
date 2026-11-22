"""Gemini is mocked: these tests never call a paid/external API."""
from types import ModuleType, SimpleNamespace
import sys
from backend.ai.draft_reply import generate_draft
from backend.ai.retriever import search_knowledge


def _fake_google(monkeypatch, *, fail=False):
    gemini = ModuleType("google.genai")

    class Client:
        def __init__(self, api_key):
            assert api_key == "local-test-key"
            self.models = self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def generate_content(self, model, contents):
            assert model == "gemini-3.8-flash"
            assert "payment" in contents.lower()
            if fail:
                raise ConnectionError("simulated 503 outage")
            return SimpleNamespace(text="Hello, please share the payment reference.")

    gemini.Client = Client
    google = ModuleType("google")
    google.genai = gemini
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.genai", gemini)


def test_retrieval_works_in_english_and_arabic():
    english = search_knowledge("My payment is missing")
    arabic = search_knowledge("الدفعة مفقودة أريد معرفة الرقم المرجعي")
    assert english and english[0]["id"] == "payment_missing"
    assert arabic and any(doc["id"] == "payment_ar" for doc in arabic)


def test_gemini_generation_with_mocked_sdk(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "local-test-key")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    _fake_google(monkeypatch)
    result = generate_draft("My payment is missing")
    assert result.provider == "gemini"
    assert "payment reference" in result.text


def test_gemini_outage_is_clearly_labeled(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "local-test-key")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    _fake_google(monkeypatch, fail=True)
    result = generate_draft("My payment is missing")
    assert result.provider == "template_fallback"
    assert "ConnectionError" in result.warning
