import re
from collections import Counter

def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\u0900-\u097F]", " ", text)
    return text

def tokenize(text):
    return normalize(text).split()

def keyword_retrieve(query, kb, top_k=3):
    """Return top_k documents from kb (list of dicts with 'text') by token overlap."""
    qtokens = set(tokenize(query))
    scores = []
    for item in kb:
        text = item.get("text", "")
        ttokens = set(tokenize(text))
        # score = overlap count
        overlap = len(qtokens & ttokens)
        scores.append((overlap, item))
    scores.sort(key=lambda x: x[0], reverse=True)
    results = [it for sc, it in scores if sc>0][:top_k]
    # if no overlap, fallback to first top_k
    if not results:
        results = [it for _, it in scores][:top_k]
    return results
