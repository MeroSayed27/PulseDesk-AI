"""Small bilingual, explainable TF-IDF knowledge retriever.

Educational RAG baseline: not a vector database, embeddings service or production RAG.
"""
import json
from pathlib import Path
from functools import lru_cache
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KNOWLEDGE_PATH = Path(__file__).with_name("knowledge.json")


@lru_cache(maxsize=1)
def _index():
    docs = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=True)
    embeddings = vectorizer.fit_transform([d["title"] + " " + d["content"] for d in docs])
    return docs, vectorizer, embeddings


def list_knowledge() -> list[dict]:
    return _index()[0]


def search_knowledge(question: str, top_k: int = 2, min_score: float = 0.08) -> list[dict]:
    if not question or not question.strip():
        return []
    docs, vectorizer, embeddings = _index()
    query = vectorizer.transform([question])
    scores = cosine_similarity(query, embeddings).ravel()
    indices = sorted(range(len(docs)), key=lambda i: float(scores[i]), reverse=True)
    return [
        {**docs[i], "score": round(float(scores[i]), 3)}
        for i in indices[:top_k]
        if float(scores[i]) >= min_score
    ]


def retrieve(question: str) -> str | None:
    """Compatibility helper for the original /knowledge/search endpoint."""
    results = search_knowledge(question, top_k=1)
    return results[0]["content"] if results else None
