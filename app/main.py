from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/context")
async def get_context(request: Request):
    body = await request.json()
    query = body.get("query", "")
    
    print("📥 Received query:", query)

    return JSONResponse(content=[
        {
            "title": "Test MCP Response",
            "url": "https://example.com",
            "content": f"You asked: {query}",
            "score": 1.0
        }
    ])

print("✅ MCP server started and /context route is active.")
