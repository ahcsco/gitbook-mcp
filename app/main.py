import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.github_fetcher import load_repo_files
from app.context_engine import find_relevant_content

REPO_URL = "https://github.com/NSO-developer/nso-examples"

app = FastAPI()

# Enable CORS for GitBook to access it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to GitBook domains later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def safe_text(text: str) -> str:
    """Ensure text is UTF-8 safe and trimmed."""
    if not isinstance(text, str):
        text = str(text)
    return text.encode("utf-8", "ignore").decode("utf-8", "ignore")

@app.get("/")
async def root():
    return {
        "name": "NSO MCP Server",
        "description": "Provides external context for NSO example queries from the GitHub repository."
    }

@app.on_event("startup")
def startup_event():
    print("🔄 Downloading repo...")
    load_repo_files()
    print("✅ MCP server with NSO content is ready.")

@app.get("/context")
@app.get("/search")
async def context_get():
    return {
        "name": "NSO Context Provider",
        "description": "Searches the NSO repository for relevant documentation or file matches."
    }

@app.post("/context")
@app.post("/search")
async def context_post(request: Request):
    start_time = time.time()
    body = await request.json()
    query = body.get("query", "").strip()
    print(f"📥 Received query: {query}")

    if not query:
        return JSONResponse(content={
            "results": [{
                "title": "Empty query",
                "href": REPO_URL,
                "body": "You did not provide a search term.",
                "description": "Please enter a search keyword to get results from the NSO examples repository."
            }]
        })

    results = find_relevant_content(query)

    if not results:
        elapsed = round(time.time() - start_time, 2)
        print(f"⚠️ No results found in {elapsed}s.")
        return JSONResponse(content={
            "results": [{
                "title": "No relevant documentation found",
                "href": REPO_URL,
                "body": f"No matches for query: '{query}'",
                "description": "No files matched your search in the NSO examples repository."
            }]
        })

    formatted = []
    for r in results[:3]:  # limit to 3 results
        snippet = safe_text(r.get("content", "")[:1000])
        href = r.get("url") or REPO_URL
        formatted.append({
            "title": safe_text(r.get("title", "Match")),
            "href": href,
            "body": snippet,
            "description": "Result from NSO examples repository"
        })

    elapsed = round(time.time() - start_time, 2)
    print(f"✅ Search completed in {elapsed}s, returning {len(formatted)} results.")

    return JSONResponse(content={"results": formatted})
