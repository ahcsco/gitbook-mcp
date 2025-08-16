import requests
import os
import zipfile
import io

REPO_URL = "https://github.com/NSO-developer/nso-examples"
ZIP_URL = f"{REPO_URL}/archive/refs/heads/main.zip"
EXTRACT_DIR = "/tmp/nso-examples-main"


def load_repo_files():
    """Download and extract repo as ZIP into /tmp."""
    if os.path.exists(EXTRACT_DIR):
        return EXTRACT_DIR  # Already extracted

    print("🔄 Downloading repo ZIP...")
    try:
        r = requests.get(ZIP_URL, timeout=30)
        r.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall("/tmp/")
        print("✅ Repo extracted.")
    except Exception as e:
        print(f"❌ Failed to download or extract repo: {e}")
        raise

    return EXTRACT_DIR


def get_all_code():
    """Return list of text contents from repo files."""
    repo_dir = load_repo_files()
    collected = []

    for root, _, files in os.walk(repo_dir):
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
