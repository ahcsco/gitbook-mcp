import re
import logging
from app.github_fetcher import get_all_code

logger = logging.getLogger(__name__)

all_docs = []  # cache


def initialize_context_engine():
    """Load repo files into memory."""
    global all_docs
    if not all_docs:
        logger.info("Loading repo content...")
        all_docs = get_all_code()
        logger.info(f"✅ Loaded {len(all_docs)} docs.")


def find_relevant_content(query: str):
    """Naive keyword search across repo files."""
    global all_docs
    if not all_docs:
        initialize_context_engine()

    query_words = set(re.findall(r"\w+", query.lower()))
    if not query_words:
        return []

    scored = []
    for doc in all_docs:
        doc_words = set(re.findall(r"\w+", doc.lower()))
        common = query_words.intersection(doc_words)
        score = len(common) / len(query_words)
        if score > 0:
            file_name = doc.split('\n')[0].replace('### ', '') if doc.startswith('### ') else 'Unknown'
            scored.append((doc, score, file_name))

    if not scored:
        return []

    best = sorted(scored, key=lambda x: x[1], reverse=True)[:3]

    return [
        {
            "title": f"Match in {file_name}",
            "url": f"https://github.com/NSO-developer/nso-examples/blob/main/{file_name}",
            "content": f"Score: {score:.2f}\n\n{doc[:1200]}",
            "score": score,
        }
        for doc, score, file_name in best
    ]
