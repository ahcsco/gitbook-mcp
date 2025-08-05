from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import requests
import zipfile
import io
import difflib

app = FastAPI()

# Load repo on startup
REPO_URL = "https://github.com/NSO-developer/nso-examples"
ZIP_URL = f"{REPO_URL}/archive/refs/heads/main.zip"
REPO_PATH = "/tmp/nso-examples-main"
all_docs = []

def load_repo_files():
    print("🔄 Downloading and extracting NSO repo...")
    r = requests.get(ZIP_URL)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall("/tmp/")
    print("✅ Repo extracted.")

    collected = []
    for root, dirs, files in os.walk(REPO_PATH):
        for f in files:
            if f.endswith(('.py', '.xml', '.yang', '.md', '.txt', '.cfg')):
                try:
                    with open(os.path.join(root, f), encoding="utf-8") as file:
                        content = file.read()
                        collected.append(f"### {f}\n{content}")
                except:
                    continue
    return collected

def find_relevant_content(query: str) -> str:
    global all_docs
    if not all_docs:
        all_docs = load_repo_files()
    
    scored = [(doc, difflib.SequenceMatcher(None, query.lower(), doc.lower()).ratio()) for doc in all_docs]
    best = sorted(scored, key=lambda x: x[1], reverse=True)[:3]
    return "\n---\n".join([b[0][:1000] for b in best])

@app.post("/context")
async def get_context(request: Request):
    body = await request.json()
    query = body.get("query", "")
    print("📥 Received query:", query)

    relevant = find_relevant_content(query)

    return JSONResponse(content=[
        {
            "title": "NSO Examples Match",
            "url": REPO_URL,
            "content": relevant,
            "score": 1.0
        }
    ])

print("✅ MCP server with NSO content is ready.")
