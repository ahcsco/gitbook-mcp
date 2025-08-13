import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from app.context_engine import find_relevant_content, initialize_context_engine
from app.github_fetcher import load_repo_files, get_all_code

app = FastAPI()

# Allow all origins for GitBook
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("🔄 Loading NSO examples repository...")
    try:
        load_repo_files()  # Download and extract repo
        initialize_context_engine()  # Initialize context engine
        print("✅ MCP server with NSO content is ready.")
    except Exception as e:
        print(f"❌ Failed to load repository: {e}")

@app.post("/context")
async def context_post(request: Request):
    try:
        data = await request.json()
        query = data.get("query", "").strip()

        if not query:
            return JSONResponse(content={"results": []})

        results = find_relevant_content(query)
        return JSONResponse(content={"results": results})
    except Exception as e:
        print(f"❌ Error in /context POST: {e}")
        return JSONResponse(content={"results": []}, status_code=500)

@app.get("/context")
async def context_get(request: Request):
    async def event_generator():
        try:
            # Send initial ready event
            yield 'event: ready\ndata: {"results": []}\n\n'
            
            # Keep the connection alive with periodic pings
            while True:
                if await request.is_disconnected():
                    print("🔌 Client disconnected from SSE stream")
                    break
                yield 'event: ping\ndata: {"status": "alive"}\n\n'
                await asyncio.sleep(30)  # Send ping every 30 seconds
        except Exception as e:
            print(f"❌ Error in SSE stream: {e}")
            yield 'event: error\ndata: {}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 MCP server shutting down.")

# Debug endpoint to list files (optional, for troubleshooting)
@app.get("/debug/files")
async def debug_files():
    files = []
    for root, dirs, files in os.walk("/tmp/nso-examples-main"):
        for f in files:
            files.append(os.path.join(root, f))
    return JSONResponse(content={"files": files})
