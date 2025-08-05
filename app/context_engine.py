from app.github_fetcher import get_all_code
import re

all_docs = []

def find_relevant_content(query: str):
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
        return []

    best = sorted(scored, key=lambda x: x[1], reverse=True)[:3]

    return [
        {
            "title": f"Match {i+1}",
            "url": "https://github.com/NSO-developer/nso-examples",
            "content": f"Match Score: {score:.2f}\n\n{doc[:1500]}",
            "score": score
        }
        for i, (doc, score) in enumerate(best)
    ]
