import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from app.context_engine import find_relevant_content, initialize_context_engine
from app.github_fetcher import load_repo_files, get_all_code
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    logger.info("🔄 Loading NSO examples repository...")
    try:
        load_repo_files()  # Download and extract repo
        initialize_context_engine()  # Initialize context engine
        logger.info("✅ MCP server with NSO content is ready.")
    except Exception as e:
        logger.error(f"❌ Failed to load repository: {e}")

@app.post("/context")
async def context_post(request: Request):
    try:
        data = await request.json()
        query = data.get("query", "").strip()
        logger.info(f"Received POST request with query: {query}")

        if not query:
            logger.info("No query provided, returning empty results")
            return JSONResponse(content={"results": []})

        results = find_relevant_content(query)
        logger.info(f"Returning {len(results)} results for query: {query}")
        return JSONResponse(content={"results": results})
    except Exception as e:
        logger.error(f"❌ Error in /context POST: {e}")
        return JSONResponse(content={"results": []}, status_code=500)

@app.get("/context")
async def context_get(request: Request):
    async def event_generator():
        try:
            # Send initial ready event
            logger.info("Sending initial 'ready' event")
            yield 'event: ready\ndata: {"results": []}\n\n'

            # Check for query parameter (GitBook might send query via GET)
            query = request.query_params.get("query", "").strip()
            if query:
                logger.info(f"Received GET query: {query}")
                results = find_relevant_content(query)
                yield f'event: results\ndata: {{"results": {json.dumps(results)}}}\n\n'

            # Keep the connection alive with periodic pings
            while True:
                if await request.is_disconnected():
                    logger.info("🔌 Client disconnected from SSE stream")
                    break
                logger.debug("Sending ping event")
                yield 'event: ping\ndata: {"status": "alive"}\n\n'
                await asyncio.sleep(10)  # Reduced to 10 seconds for more frequent pings
        except Exception as e:
            logger.error(f"❌ Error in SSE stream: {e}")
            yield 'event: error\ndata: {}\n\n'

    logger.info("Establishing SSE connection for /context GET")
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 MCP server shutting down.")

# Debug endpoint to list files (optional, for troubleshooting)
@app.get("/debug/files")
async def debug_files():
    files = []
    for root, dirs, files in os.walk("/tmp/nso-examples-main"):
        for f in files:
            files.append(os.path.join(root, f))
    logger.info(f"Returning list of {len(files)} files in /tmp/nso-examples-main")
    return JSONResponse(content={"files": files})
