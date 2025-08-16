from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
from app.context_engine import find_relevant_content, initialize_context_engine

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    logger.info("🔄 Initializing...")
    initialize_context_engine()
    logger.info("✅ Ready.")


@app.get("/")
async def root():
    return {"status": "ok", "message": "MCP server running"}


@app.post("/context")
async def context(request: Request):
    try:
        body = await request.json()
        query = body.get("query", "")
        logger.info(f"📥 Query: {query}")

        results = find_relevant_content(query)
        return JSONResponse(content={"results": results})
    except Exception as e:
        logger.error(f"❌ Error in /context: {e}")
        return JSONResponse(content={"results": []}, status_code=500)
