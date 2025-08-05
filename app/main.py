from fastapi import FastAPI
from pydantic import BaseModel
from app.github_fetcher import load_repo_files
from app.context_engine import find_relevant_content
from fastapi import Request
from fastapi.responses import JSONResponse

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: list[Message]
    temperature: float = 1.0

@app.post("/v1/chat/completions")
async def chat_completion(req: ChatRequest):
    last_user_msg = next((m.content for m in reversed(req.messages) if m.role == "user"), "")
    relevant = find_relevant_content(last_user_msg)
    
    return {
        "id": "chatcmpl-nso",
        "object": "chat.completion",
        "created": 1234567890,
        "model": req.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": relevant or "No relevant content found in nso-examples repo."
            },
            "finish_reason": "stop"
        }]
    }

@app.on_event("startup")
def init():
    load_repo_files()

@app.post("/context")
async def get_context(request: Request):
    body = await request.json()
    query = body.get("query", "")
    
    relevant_content = find_relevant_content(query)

    return JSONResponse(content=[
        {
            "title": "From NSO Examples Repo",
            "url": "https://github.com/NSO-developer/nso-examples",
            "content": relevant_content,
            "score": 1.0
        }
    ])
