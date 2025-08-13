import requests
import os
import zipfile
import io

REPO_URL = "https://github.com/NSO-developer/nso-examples"
ZIP_URL = f"{REPO_URL}/archive/refs/heads/main.zip"
REPO_DIR = "/tmp/nso-examples"

def load_repo_files():
    """Download and extract the NSO examples repository."""
    try:
        print("🔄 Downloading repo...")
        r = requests.get(ZIP_URL, timeout=30)
        r.raise_for_status()  # Raise an exception for bad HTTP responses
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall("/tmp/")
        print("✅ Repo loaded.")
    except Exception as e:
        print(f"❌ Failed to download or extract repo: {e}")
        raise

def get_all_code():
    """Read all relevant files from the extracted repository."""
    full_path = os.path.join("/tmp", "nso-examples-main")
    collected = []
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Repository directory {full_path} does not exist. Run load_repo_files() first.")
    
    for root, dirs, files in os.walk(full_path):
        for f in files:
            if f.endswith(('.py', '.xml', '.yang', '.md', '.txt', '.cfg')):
                path = os.path.join(root, f)
                try:
                    with open(path, encoding="utf-8") as file:
                        collected.append(f"### {f}\n{file.read()}")
                except Exception as e:
                    print(f"❌ Error reading file {path}: {e}")
                    continue
    return collected
