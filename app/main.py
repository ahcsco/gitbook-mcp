from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.github_fetcher import load_repo_files
from app.context_engine import find_relevant_content

app = FastAPI()

# Enable CORS for GitBook to access it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to GitBook's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GitBook uses GET / to check the server is alive and to understand what it can do
@app.get("/")
async def root():
    return {
        "name": "NSO MCP Server",
        "description": (
            "Search and retrieve exact matches for files, configuration snippets, "
            "and technical references from the NSO example repository. "
            "Use this tool whenever a query contains a filename "
            "(e.g., vrouter.yang, netconf-config.xml) or needs specific YANG models, "
            "XML configurations, or service templates from the repo. "
            "The server returns relevant file paths, matching snippets, and context "
            "directly from the source repository."
        ),
        "usage_examples": [
            "Find where vrouter.yang is defined",
            "Show the XML config for vpn-service-template.xml",
            "Locate service templates that define vpn",
            "Get the YANG model for ietf-interfaces.yang"
        ],
        "input_format": {
            "query": "String containing filename, config keyword, or technical term"
        },
        "output_format": {
            "results": [
                {
                    "file": "relative/path/to/file",
                    "snippet": "matching lines or block",
                    "score": "float between 0 and 1"
                }
            ]
        }
    }

# Preload the GitHub repo contents at startup
@app.on_event("startup")
def startup_event():
    load_repo_files()
    print("✅ MCP server with NSO content is ready.")

# GitBook will call this endpoint to get additional context
@app.post("/context")
async def get_context(request: Request):
    body = await request.json()
    query = body.get("query", "")
    print(f"📥 Received query: {query}")

    results = find_relevant_content(query)

    # Return a default response if no match is found
    if not results:
        print(f"⚠️ No results found for '{query}'.")
        return JSONResponse(content=[{
            "title": "No relevant documentation found",
            "url": "",
            "content": f"No matches for query: '{query}'",
            "score": 0
        }])

    print(f"✅ Returning {len(results)} results for '{query}'.")
    return JSONResponse(content=results)
