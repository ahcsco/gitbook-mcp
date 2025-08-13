import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.github_fetcher import load_repo_files
from app.context_engine import find_relevant_content

REPO_URL = "https://github.com/NSO-developer/nso-examples"

app = FastAPI()

# Allow GitBook to call this from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    print("✅ Repo loaded.")
    print("✅ MCP server with NSO content is ready.")

# GitBook MCP handshake endpoint
@app.get("/context")
async def get_context_metadata():
    """Return MCP capabilities metadata so GitBook knows how to use this server."""
    return JSONResponse(
        content={
            "name": "nso-mcp-context",
            "description": "Provides search results from the NSO examples GitHub repository.",
            "capabilities": {
                "search": True
            }
        },
        media_type="application/json; charset=utf-8"
    )

@app.post("/context")
async def search_context(request: Request):
    """Handle search queries from GitBook MCP."""
    start_time = time.time()
    body = await request.json()
    query = body.get("query", "").strip()

    print(f"📥 Received query: {query}")

    if not query:
        return JSONResponse(
            content={"results": [{
                "title": "Empty query",
                "href": REPO_URL,
                "body": "Please enter a search term.",
                "description": "No query provided."
            }]},
            media_type="application/json; charset=utf-8"
        )

    results = find_relevant_content(query)

    if not results:
        elapsed = round(time.time() - start_time, 2)
        print(f"⚠️ No results found in {elapsed}s.")
        return JSONResponse(
            content={"results": [{
                "title": "No matches found",
                "href": REPO_URL,
                "body": f"No matches for '{query}'.",
                "description": "No relevant content found in NSO examples repository."
            }]},
            media_type="application/json; charset=utf-8"
        )

    # Prepare MCP-friendly results (limit body to prevent overload)
    final_results = []
    for r in results[:5]:  # send max 5
        final_results.append({
            "title": r.get("title", "Match"),
            "href": r.get("url") or REPO_URL,
            "body": r.get("content", "")[:500],
            "description": "Snippet from NSO examples repository"
        })

    elapsed = round(time.time() - start_time, 2)
    print(f"✅ Search completed in {elapsed}s, returning {len(final_results)} results.")

    return JSONResponse(
        content={"results": final_results},
        media_type="application/json; charset=utf-8"
    )
