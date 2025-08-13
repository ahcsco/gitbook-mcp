import asyncio
import json
import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from app.context_engine import find_relevant_content, initialize_context_engine
from app.github_fetcher import load_repo_files, get_all_code

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        logger.info(f"Received POST request with query: {query}, headers: {dict(request.headers)}")

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
    last_query = None  # Store last query for continuous results
    async def event_generator():
        nonlocal last_query
        try:
            # Log full request details
            logger.info(f"Establishing SSE connection for /context GET with params: {request.query_params}, headers: {dict(request.headers)}")

            # Send initial ready event
            logger.info("Sending initial 'ready' event")
            yield 'event: ready\ndata: {"results": []}\n\n'

            # Check for query in query params, headers, or body
            query = request.query_params.get("query", "").strip()
            if not query:
                query = request.headers.get("x-search-query", "").strip()  # Check headers
            if not query:
                try:
                    body = await request.json()
                    query = body.get("query", "").strip()
                except:
                    pass

            if query:
                logger.info(f"Received query: {query}")
                last_query = query
                results = find_relevant_content(query)
                yield f'event: results\ndata: {json.dumps({"results": results})}\n\n'
                yield f'event: message\ndata: {json.dumps({"results": results})}\n\n'
                yield f'event: search\ndata: {json.dumps({"results": results})}\n\n'
            else:
                logger.info("No query provided in GET request")

            # Keep connection alive with periodic pings and results
            while True:
                if await request.is_disconnected():
                    logger.info("🔌 Client disconnected from SSE stream")
                    break
                logger.debug("Sending ping event")
                yield 'event: ping\ndata: {"status": "alive"}\n\n'
                if last_query:  # Resend results for last query
                    results = find_relevant_content(last_query)
                    yield f'event: results\ndata: {json.dumps({"results": results})}\n\n'
                await asyncio.sleep(3)  # Reduced to 3 seconds for frequent updates
        except Exception as e:
            logger.error(f"❌ Error in SSE stream: {e}")
            yield 'event: error\ndata: {"error": "Internal server error"}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 MCP server shutting down.")

@app.get("/debug/files")
async def debug_files():
    files = []
    for root, dirs, files_list in os.walk("/tmp/nso-examples-main"):
        for f in files_list:
            files.append(os.path.join(root, f))
    logger.info(f"Returning list of {len(files)} files in /tmp/nso-examples-main")
    return JSONResponse(content={"files": files})
