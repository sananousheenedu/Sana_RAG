import json
import re
from pathlib import Path

KB_DIR = Path(__file__).parent / "knowledge_base"

STOPWORDS = {"the", "is", "are", "my", "me", "to", "of", "and", "a", "in",
             "for", "on", "ka", "ki", "ke", "hai", "ho", "kya", "se", "ko"}


def _tokenize(text):
    return [t for t in re.findall(r"\w+", text.lower())
            if len(t) > 2 and t not in STOPWORDS]


def _flatten(value):
    if isinstance(value, dict):
        return " ".join(_flatten(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_flatten(v) for v in value)
    return str(value)


def load_documents():
    """Read every JSON file under knowledge_base/ into a list of documents."""
    docs = []
    for path in sorted(KB_DIR.rglob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        searchable = {k: v for k, v in data.items() if k != "source"}
        docs.append({
            "id": data.get("id", path.stem),
            "category": data.get("category", ""),
            "content": data,
            "source": data.get("source", {}),
            "keywords": [k.lower() for k in data.get("keywords", [])],
            "tokens": set(_tokenize(_flatten(searchable))),
        })
    return docs


_DOCS = load_documents()


def retrieve(query, top_k=3):
    """Return the best-matching knowledge-base entries for a user question."""
    q = query.lower()
    q_tokens = set(_tokenize(query))
    results = []
    for doc in _DOCS:
        score = 0
        for kw in doc["keywords"]:
            if kw in q:
                score += 3          # a keyword phrase matched
        score += len(q_tokens & doc["tokens"])   # shared words
        if score > 0:
            results.append({
                "id": doc["id"],
                "category": doc["category"],
                "score": score,
                "content": doc["content"],
                "source": doc["source"],
            })
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    for question in [
        "My FESCO bill is very high, what should I do?",
        "Bijli ka bill bohat zyada aa gaya hai, complaint kahan karun?",
    ]:
        print("\nQ:", question)
        for r in retrieve(question):
            print(f"  {r['id']}  (score {r['score']})  source: {r['source'].get('name')}")
