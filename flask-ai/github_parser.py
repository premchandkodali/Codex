import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def parse_github_repo(url):
    owner, repo = url.strip('/').split('/')[-2:]
    api = f"https://api.github.com/repos/{owner}/{repo}/contents"
    chunks = []

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GitHub token not found. Please set GITHUB_TOKEN in your .env file")
        
    headers = {
        "Authorization": f"token {token}"
    }

    def fetch(url):
        res = requests.get(url, headers=headers).json()

        if isinstance(res, dict) and res.get("message"):
            print("Error:", res.get("message"))
            return

        for item in res:
            print(item)
            if item['type'] == 'file' and item['name'].endswith(('.py', '.js')):
                content = requests.get(item['download_url']).text
                chunks.extend(content.split('\n\n'))  # naive chunking
            elif item['type'] == 'dir':
                fetch(item['url'])

    fetch(api)
    return chunks