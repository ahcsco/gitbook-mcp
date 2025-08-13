import asyncio
import json
import os
import logging
import uuid
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

# Define MCP tools with detailed descriptions
MCP_TOOLS = [
    {
        "name": "nso_search_content",
        "description": "Search for files and content in the NSO examples repository, such as vrouter.yang or device-management configurations.",
        "parameters": {
            "query": {
                "type": "string",
                "description": "Search terms to find relevant files or content (e.g., 'vrouter.yang', 'device-management').",
                "required": True
            }
        },
        "returns": {
            "type": "array",
            "description": "List of matching files with metadata (file name, path, snippet, score)."
        }
    },
    {
        "name": "nso_get_file",
        "description": "Retrieve the full content of a specific file from the NSO examples repository by its path.",
        "parameters": {
            "file_path": {
                "type": "string",
                "description": "Path to the file in the repository (e.g., 'examples.ncs/getting-started/using-ncs/1-configure-device/vrouter.yang').",
                "required": True
            }
        },
        "returns": {
            "type": "object",
            "description": "File details including name, path, and full content."
        }
    }
]

@app.on_event("startup")
async def startup_event():
    logger.info("🔄 Loading NSO examples repository...")
    try:
        load_repo_files()  # Download and extract repo
        initialize_context_engine()  # Initialize context engine
        logger.info("✅ MCP server with NSO content is ready.")
    except Exception as e:
        logger.error(f"❌ Failed to load repository: {e}")

@app.get("/tools")
async def list_tools():
    """Expose available MCP tools for GitBook AI to discover."""
    logger.info("Received request for /tools endpoint")
    return JSONResponse(content={"tools": MCP_TOOLS})

@app.post("/context")
async def context_post(request: Request):
    try:
        data = await request.json()
        query = data.get("query", "").strip()
        query_id = str(uuid.uuid4())
        logger.info(f"Received POST request with query: {query}, headers: {dict(request.headers)}, body: {data}")

        if not query:
            logger.info("No query provided, returning default results")
            results = find_relevant_content("vrouter")  # Default query
            payload = {
                "query_id": query_id,
                "context_id": str(uuid.uuid4()),
                "query": "vrouter",
                "results": results
            }
            return JSONResponse(content=payload)

        results = find_relevant_content(query)
        payload = {
            "query_id": query_id,
            "context_id": str(uuid.uuid4()),
            "query": query,
            "results": results
        }
        logger.info(f"Returning {len(results)} results for query: {query}")
        return JSONResponse(content=payload)
    except Exception as e:
        logger.error(f"❌ Error in /context POST: {e}")
        return JSONResponse(content={"results": [], "error": str(e)}, status_code=500)

@app.get("/context")
async def context_get(request: Request):
    query_id = str(uuid.uuid4())
    last_query = None
    async def event_generator():
        nonlocal last_query, query_id
        try:
            logger.info(f"Establishing SSE connection for /context GET with params: {request.query_params}, headers: {dict(request.headers)}")

            # Send initial ready event
            yield f'event: ready\ndata: {json.dumps({"query_id": query_id, "results": [], "tools": MCP_TOOLS})}\n\n'

            # Check for query in query params, headers, or body
            query = request.query_params.get("query", "").strip()
            if not query:
                query = request.headers.get("x-search-query", "").strip()
            if not query:
                try:
                    async for chunk in request.stream():
                        try:
                            body = json.loads(chunk.decode('utf-8'))
                            query = body.get("query", "").strip()
                            logger.info(f"Received body data: {body}")
                            if query:
                                break
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse body chunk as JSON: {chunk.decode('utf-8')}")
                except Exception as e:
                    logger.error(f"Error reading request body: {e}")

            # Use default query if none provided
            if not query:
                query = "vrouter"
                logger.info("No query provided, using default query: vrouter")

            if query:
                logger.info(f"Processing query: {query}")
                last_query = query
                results = find_relevant_content(query)
                payload = {
                    "query_id": query_id,
                    "context_id": str(uuid.uuid4()),
                    "query": query,
                    "results": results,
                    "tool": "nso_search_content"
                }
                yield f'event: results\ndata: {json.dumps(payload)}\n\n'
                yield f'event: message\ndata: {json.dumps(payload)}\n\n'
                yield f'event: search\ndata: {json.dumps(payload)}\n\n'
                yield f'event: update\ndata: {json.dumps(payload)}\n\n'
                yield f'event: data\ndata: {json.dumps(payload)}\n\n'

            # Keep connection alive with periodic pings and results
            while True:
                if await request.is_disconnected():
                    logger.info("🔌 Client disconnected from SSE stream")
                    break
                yield f'event: ping\ndata: {json.dumps({"status": "alive", "query_id": query_id})}\n\n'
                if last_query:
                    results = find_relevant_content(last_query)
                    payload = {
                        "query_id": query_id,
                        "context_id": str(uuid.uuid4()),
                        "query": last_query,
                        "results": results,
                        "tool": "nso_search_content"
                    }
                    yield f'event: results\ndata: {json.dumps(payload)}\n\n'
                await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"❌ Error in SSE stream: {e}")
            yield f'event: error\ndata: {json.dumps({"error": str(e), "query_id": query_id})}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/debug/files")
async def debug_files():
    files = []
    for root, dirs, files_list in os.walk("/tmp/nso-examples-main"):
        for f in files_list:
            files.append(os.path.join(root, f))
    logger.info(f"Returning list of {len(files)} files in /tmp/nso-examples-main")
    return JSONResponse(content={"files": files})
