from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.github_fetcher import load_repo_files
from app.context_engine import find_relevant_content

app = FastAPI()

# Enable CORS for GitBook
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Optionally restrict to GitBook's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    try:
        body = await asyncio.wait_for(request.json(), timeout=5)
    except asyncio.TimeoutError:
        return JSONResponse(content=[{
            "title": "Timeout reading request",
            "href": "",
            "body": "The request body could not be read in time."
        }], status_code=408)

    query = body.get("query", "").strip()
    print(f"📥 Received query: {query}")

    if not query:
        return JSONResponse(content=[{
            "title": "Empty query",
            "href": "",
            "body": "Please provide a search query."
        }])

    try:
        results = find_relevant_content(query)
    except Exception as e:
        print(f"❌ Search error: {e}")
        return JSONResponse(content=[{
            "title": "Search error",
            "href": "",
            "body": f"An error occurred: {e}"
        }], status_code=500)

    if not results:
        return JSONResponse(content=[{
            "title": "No relevant documentation found",
            "href": "",
            "body": f"No matches for query: '{query}'"
        }])

    # Ensure payload is small & in GitBook's expected format
    formatted = []
    for r in results:
        snippet = r.get("content", "")[:1000]  # Truncate to 1000 chars
        formatted.append({
            "title": r.get("title", "Match"),
            "href": r.get("url", ""),
            "body": snippet
        })

    return JSONResponse(content=formatted)
