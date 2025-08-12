from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.github_fetcher import load_repo_files
from app.context_engine import find_relevant_content

app = FastAPI()

# Enable CORS for GitBook to access it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to GitBook's domain if desired
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check / server info
@app.get("/")
async def root():
    return {
        "name": "NSO MCP Server",
        "description": "Provides external context for NSO example queries. Can search for file names like 'vrouter.yang' in the example repository."
    }

# Startup: preload the GitHub repo contents
@app.on_event("startup")
def startup_event():
    load_repo_files()
    print("✅ MCP server with NSO content is ready.")

# GET handler for GitBook's MCP discovery ping
@app.get("/context")
@app.get("/search")
async def context_get():
    return {
        "name": "NSO Context Provider",
        "description": "Searches the NSO repository for relevant documentation or file matches. Example: send 'vrouter.yang' to retrieve related context."
    }

# POST handler for actual context queries
@app.post("/context")
@app.post("/search")
async def context_post(request: Request):
    body = await request.json()
    query = body.get("query", "")
    print(f"📥 Received query: {query}")

    results = find_relevant_content(query)

    if not results:
        print("⚠️ No results found.")
        return JSONResponse(content=[{
            "title": "No relevant documentation found",
            "url": "",
            "content": f"No matches for query: '{query}'",
            "score": 0
        }])

    return JSONResponse(content=results)
