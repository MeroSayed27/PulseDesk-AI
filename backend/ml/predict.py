"""Optional BANKING77 trained classifier and transparent general-support fallback."""
from functools import lru_cache
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
MODEL_PATH = Path(__file__).resolve().parent / "data" / "ticket_model.joblib"


@lru_cache(maxsize=1)
def get_model():
    if not MODEL_PATH.is_file():
        return None
    try:
        from joblib import load
        return load(MODEL_PATH)  # Never load untrusted joblib files.
    except (ImportError, OSError, ValueError) as exc:
        logger.warning("Could not load classifier: %s", exc)
        return None


def predict_with_confidence(message: str) -> dict:
    """Report BANKING77 intent only when a compatible local model is available."""
    model = get_model()
    if model is None:
        return {"intent": None, "confidence": None, "model_loaded": False}
    try:
        probabilities = model.predict_proba([message])[0]
        best = int(probabilities.argmax())
        return {
            "intent": str(model.classes_[best]),
            "confidence": round(float(probabilities[best]), 3),
            "model_loaded": True,
        }
    except (AttributeError, ValueError) as exc:
        logger.warning("Classifier inference failed: %s", exc)
        return {"intent": None, "confidence": None, "model_loaded": False}


def predict_category(message: str) -> str:
    """Explainable broad support categories, separate from BANKING77 intents."""
    text = message.casefold()
    categories = {
        "billing": ("payment", "refund", "charge", "invoice", "billing", "transaction", "money", "دفع", "فاتورة", "استرداد", "فلوس"),
        "account": ("login", "password", "sign in", "account", "verify", "access", "دخول", "حساب", "كلمة المرور"),
        "delivery": ("delivery", "shipping", "shipment", "parcel", "tracking", "package", "توصيل", "شحن", "طلب"),
    }
    for category, tokens in categories.items():
        if any(token in text for token in tokens):
            return category
    return "general"
