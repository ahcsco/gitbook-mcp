from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.github_fetcher import load_repo_files
from app.context_engine import find_relevant_content

app = FastAPI()

# Add CORS (optional but helpful)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to GitBook domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GitBook expects GET / to confirm it's live
@app.get("/")
async def root():
    return {
        "name": "NSO MCP Server",
        "description": "Provides external context for NSO example queries."
    }

# On startup, preload repo files
@app.on_event("startup")
def startup_event():
    load_repo_files()
    print("✅ MCP server with NSO content is ready.")

# GitBook will send POST /context
@app.post("/context")
async def get_context(request: Request):
    body = await request.json()
    query = body.get("query", "")
    print(f"📥 Received query: {query}")

    results = find_relevant_content(query)

    return JSONResponse(content=results)
