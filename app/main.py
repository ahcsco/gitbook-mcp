import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

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
    print("✅ MCP server with NSO content is ready.")

@app.post("/context")
async def context_post(request: Request):
    try:
        data = await request.json()
        query = data.get("query", "").strip()

        results = []
        if query:
            results.append({
                "title": f"Search result for {query}",
                "snippet": f"This is a mock result for '{query}'.",
                "url": f"https://example.com/search?q={query}"
            })

        return JSONResponse(content={"results": results})
    except Exception as e:
        print(f"❌ Error in /context POST: {e}")
        return JSONResponse(content={"results": []})

@app.get("/context")
async def context_get():
    async def event_generator():
        try:
            yield 'event: ready\ndata: {"results": []}\n\n'
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"❌ Error in SSE stream: {e}")
            yield 'event: error\ndata: {}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 MCP server shutting down.")
