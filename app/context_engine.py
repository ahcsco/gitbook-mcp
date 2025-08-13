import re
from app.github_fetcher import get_all_code

all_docs = []  # Global cache for repository content

def initialize_context_engine():
    """Initialize the context engine by loading repository content."""
    global all_docs
    if not all_docs:
        all_docs = get_all_code()
        print(f"✅ Loaded {len(all_docs)} documents into context engine.")

def find_relevant_content(query: str):
    """Find content relevant to the query from the NSO examples repository."""
    global all_docs
    if not all_docs:
        initialize_context_engine()

    query_words = set(re.findall(r"\w+", query.lower()))
    scored = []

    for doc in all_docs:
        doc_words = set(re.findall(r"\w+", doc.lower()))
        common = query_words.intersection(doc_words)
        score = len(common) / len(query_words)  # Normalize score by query length
        if score > 0:
            # Extract file name from the document (first line after ###)
            file_name = doc.split('\n')[0].replace('### ', '') if doc.startswith('### ') else 'Unknown'
            scored.append((doc, score, file_name))

    if not scored:
        return []

    # Sort by score and limit to top 3 results
    best = sorted(scored, key=lambda x: x[1], reverse=True)[:3]

    return [
        {
            "title": f"Match in {file_name}",
            "url": f"https://github.com/NSO-developer/nso-examples/blob/main/{file_name}",
            "content": f"Match Score: {score:.2f}\n\n{doc[:1500]}",
            "score": score
        }
        for i, (doc, score, file_name) in enumerate(best)
    ]
