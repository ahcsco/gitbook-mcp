import os
import shutil
import subprocess
import tempfile
import asyncio  # ✅ FIX: Needed for sleep in async functions
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

app = FastAPI()

# Allow all CORS origins for GitBook
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPO_URL = os.environ.get("REPO_URL", "https://github.com/your/repo.git")
TEMP_DIR = tempfile.mkdtemp()

def clone_or_pull_repo():
    repo_path = os.path.join(TEMP_DIR, "repo")
    if os.path.exists(repo_path):
        print("🔄 Downloading repo...")
        subprocess.run(["git", "-C", repo_path, "pull"], check=False)
    else:
        print("🔄 Downloading repo...")
        subprocess.run(["git", "clone", REPO_URL, repo_path], check=False)
    print("✅ Repo loaded.")
    return repo_path

@app.on_event("startup")
async def startup_event():
    repo_path = clone_or_pull_repo()
    print("✅ MCP server with NSO content is ready.")

@app.post("/context")
async def context_post(request: Request):
    try:
        data = await request.json()
        query = data.get("query", "").strip()
        print(f"📥 Received query: {query}")

        # Example search simulation
        results = []
        if query:
            results.append({
                "title": f"Search result for {query}",
                "snippet": f"This is a mock result for '{query}'.",
                "url": f"https://example.com/search?q={query}"
            })

        print(f"✅ Search completed, returning {len(results)} results.")
        return JSONResponse(content={"results": results})
    except Exception as e:
        print(f"❌ Error in /context POST: {e}")
        return JSONResponse(content={"results": []})

@app.get("/context")
async def context_get():
    print("📡 GET /context")

    async def event_generator():
        try:
            yield 'event: ready\ndata: {"results": []}\n\n'
            await asyncio.sleep(0.1)  # Short pause to keep connection alive briefly
        except Exception as e:
            print(f"❌ Error in SSE stream: {e}")
            yield 'event: error\ndata: {}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.on_event("shutdown")
async def shutdown_event():
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
