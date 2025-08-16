from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

# Simple in-memory "index" for demo purposes.
# Replace with actual repo content later.
EXAMPLE_RESULTS = [
    {
        "title": "Match 1",
        "href": "https://github.com/NSO-developer/nso-examples",
        "body": "Nano Services for Staged Provisioning of a Virtual Router",
        "description": "Example NSO repo snippet"
    }
]

@app.get("/")
async def root():
    return {"status": "ok", "message": "MCP server is running."}

@app.post("/context")
async def context(request: Request):
    data = await request.json()
    query = data.get("query", "").lower()

    # For now, always return EXAMPLE_RESULTS (stub)
    # Later you can plug in real search logic here
    results = []
    for item in EXAMPLE_RESULTS:
        if query in item["body"].lower() or query in item["title"].lower():
            results.append(item)

    # If no matches, just return default
    if not results:
        results = EXAMPLE_RESULTS

    return JSONResponse(content={"results": results})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
