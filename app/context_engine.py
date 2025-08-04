from app.github_fetcher import get_all_code
import re

all_docs = []

def find_relevant_content(query: str) -> str:
    global all_docs
    if not all_docs:
        all_docs = get_all_code()

    query_words = set(re.findall(r"\w+", query.lower()))
    scored = []

    for doc in all_docs:
        doc_words = set(re.findall(r"\w+", doc.lower()))
        common = query_words.intersection(doc_words)
        score = len(common)  # number of matching words
        if score > 0:
            scored.append((doc, score))

    if not scored:
        return ""

    # Sort by score descending and take top 3
    best = sorted(scored, key=lambda x: x[1], reverse=True)[:3]

    # Join snippets with separators, limit to 1000 chars each
    return "\n---\n".join([b[0][:1000] for b in best])
