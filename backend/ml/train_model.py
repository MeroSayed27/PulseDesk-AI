"""Train the original BANKING77 TF-IDF + logistic regression baseline.

Expected files (not included): backend/ml/data/train.csv and test.csv
with columns text,category. Training should be run explicitly, not at server import.
"""
import csv
from pathlib import Path
from joblib import dump
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score

DATA_DIR = Path(__file__).resolve().parent / "data"


def load_data(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or not all("text" in row and "category" in row for row in rows):
        raise ValueError(f"{filename} must include text and category columns")
    return [row["text"] for row in rows], [row["category"] for row in rows]


def main():
    x_train, y_train = load_data("train.csv")
    x_test, y_test = load_data("test.csv")
    model = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2)),
        LogisticRegression(max_iter=1000),
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    print(f"Training examples: {len(x_train)}")
    print(f"Test examples: {len(x_test)}")
    print(f"Accuracy: {accuracy_score(y_test, predictions):.2%}")
    print(f"Macro F1: {f1_score(y_test, predictions, average='macro'):.2%}")
    print(classification_report(y_test, predictions, zero_division=0))
    dump(model, DATA_DIR / "ticket_model.joblib")
    print("Model saved to backend/ml/data/ticket_model.joblib")


if __name__ == "__main__":
    main()
