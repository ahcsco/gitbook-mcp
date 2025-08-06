from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.github_fetcher import load_repo_files
from app.context_engine import find_relevant_content

app = FastAPI()

@app.on_event("startup")
def startup_event():
    # Load repo files into memory once on startup
    load_repo_files()
    print("✅ MCP server with NSO content is ready.")

@app.get("/context")
async def get_context_metadata():
    # GitBook expects this route to return MCP server metadata
    return {
        "name": "NSO MCP Server",
        "description": "Provides external context for NSO example queries."
    }

@app.post("/context")
async def get_context(request: Request):
    body = await request.json()
    query = body.get("query", "")
    print(f"📥 Received query: {query}")

    results = find_relevant_content(query)

    return JSONResponse(content=results)
