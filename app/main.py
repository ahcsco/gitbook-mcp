import time
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.github_fetcher import load_repo_files
from app.context_engine import find_relevant_content

app = FastAPI()

# Enable CORS for GitBook
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPO_URL = "https://github.com/NSO-developer/nso-examples"

@app.get("/")
async def root():
    return {
        "name": "NSO MCP Server",
        "description": "Provides external context for NSO example queries."
    }

@app.on_event("startup")
def startup_event():
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

    try:
        body = await asyncio.wait_for(request.json(), timeout=5)
    except asyncio.TimeoutError:
        return JSONResponse(content=[{
            "title": "Timeout",
            "href": REPO_URL,
            "body": "Request body took too long to arrive."
        }], status_code=408)

    query = body.get("query", "").strip()
    print(f"📥 Received query: {query}")

    if not query:
        return JSONResponse(content=[{
            "title": "Empty query",
            "href": REPO_URL,
            "body": "Please provide a search term."
        }])

    # If user asks for examples, send repo context immediately
    if "example" in query.lower():
        return JSONResponse(content=[{
            "title": "NSO Example Repository",
            "href": REPO_URL,
            "body": "The NSO examples repository contains sample services, YANG models, and scripts."
        }])

    try:
        results = await asyncio.to_thread(find_relevant_content, query)
    except Exception as e:
        print(f"❌ Search error: {e}")
        return JSONResponse(content=[{
            "title": "Search error",
            "href": REPO_URL,
            "body": f"Error while searching: {e}"
        }], status_code=500)

    if not results:
        return JSONResponse(content=[{
            "title": "No relevant documentation found",
            "href": REPO_URL,
            "body": f"No matches for query: '{query}'"
        }])

    # Limit and clean results
    formatted = []
    for r in results[:3]:  # max 3 matches
        snippet = r.get("content", "")[:1000]  # truncate
        href = r.get("url") or REPO_URL
        formatted.append({
            "title": r.get("title", "Match"),
            "href": href,
            "body": snippet
        })

    elapsed = round(time.time() - start_time, 2)
    print(f"✅ Search completed in {elapsed}s, returning {len(formatted)} results.")

    return JSONResponse(content=formatted)
