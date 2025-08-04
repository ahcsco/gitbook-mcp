import requests
import os
import zipfile
import io

REPO_URL = "https://github.com/NSO-developer/nso-examples"
ZIP_URL = f"{REPO_URL}/archive/refs/heads/main.zip"
REPO_DIR = "/tmp/nso-examples"

def load_repo_files():
    print("🔄 Downloading repo...")
    r = requests.get(ZIP_URL)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall("/tmp/")
    print("✅ Repo loaded.")

def get_all_code():
    full_path = os.path.join("/tmp", "nso-examples-main")
    collected = []
    for root, dirs, files in os.walk(full_path):
        for f in files:
            if f.endswith(('.py', '.xml', '.yang', '.md', '.txt', '.cfg')):
                path = os.path.join(root, f)
                try:
                    with open(path, encoding="utf-8") as file:
                        collected.append(f"### {f}\n{file.read()}")
                except:
                    continue
    return collected
