from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.github_fetcher import load_repo_files
from app.context_engine import find_relevant_content

app = FastAPI()

# Enable CORS for GitBook to access it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to GitBook domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GitBook uses GET / to check the server is alive
@app.get("/")
async def root():
    return {
        "name": "NSO MCP Server",
        "description": "Provides external context for NSO example queries."
    }

# Preload the GitHub repo contents at startup
@app.on_event("startup")
def startup_event():
    load_repo_files()
    print("✅ MCP server with NSO content is ready.")

# GitBook will call this endpoint to get additional context
@app.post("/context")
async def get_context(request: Request):
    body = await request.json()
    query = body.get("query", "")
    print(f"📥 Received query: {query}")

    results = find_relevant_content(query)

    # Return a default response if no match is found
    if not results:
        print("⚠️ No results found.")
        return JSONResponse(content=[{
            "title": "No relevant documentation found",
            "url": "",
            "content": f"No matches for query: '{query}'",
            "score": 0
        }])

    return JSONResponse(content=results)
