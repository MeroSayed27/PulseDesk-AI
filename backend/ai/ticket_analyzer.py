"""Legacy helper retained for compatibility."""
from backend.ml.predict import predict_category


def classify_ticket(message: str) -> str:
    return predict_category(message)
