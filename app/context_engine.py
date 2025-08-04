from app.github_fetcher import get_all_code
import difflib

all_docs = []

def find_relevant_content(query: str) -> str:
    global all_docs
    if not all_docs:
        all_docs = get_all_code()
    
    scored = [(doc, difflib.SequenceMatcher(None, query.lower(), doc.lower()).ratio()) for doc in all_docs]
    best = sorted(scored, key=lambda x: x[1], reverse=True)[:3]
    return "\n---\n".join([b[0][:1000] for b in best])
