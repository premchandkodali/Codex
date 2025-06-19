import os
from llama_index.readers.github import GithubRepositoryReader
from llama_index.readers.github import GithubClient
import requests
from urllib.parse import urlparse
import base64
from typing import Dict, Any
from github import Github as PyGithub
from typing import List, Dict, Any

def get_github_branches(repo_url: str) -> List[Dict[str, str]]:
    """Fetch all branches for a GitHub repository."""
    try:
        github_token = os.getenv("GITHUB_TOKEN")
        g = PyGithub(github_token)
        
        # Extract owner and repo name from URL
        parts = repo_url.strip('/').split('/')
        owner = parts[-2]
        repo_name = parts[-1]
        
        # Get the repository
        repo = g.get_repo(f"{owner}/{repo_name}")
        
        # Get all branches
        branches = []
        for branch in repo.get_branches():
            branches.append({
                'name': branch.name,
                'commit_sha': branch.commit.sha[:7],
                'protected': branch.protected
            })
            
        return branches
    except Exception as e:
        print(f"Error fetching branches: {str(e)}")
        return []

def parse_github_repo(repo_url: str, branch: str = "main") -> Any:
    """Parse a GitHub repository from the given URL and branch."""
    try:
        # Extract owner and repo name
        parts = repo_url.strip('/').split('/')
        owner = parts[-2]
        repo = parts[-1]

        # GitHub personal access token
        github_token = os.getenv("GITHUB_TOKEN")
        github_client = GithubClient(github_token)


        reader = GithubRepositoryReader(
            github_client=github_client,
            owner=owner,
            repo=repo,
            filter_directories=(
                # Exclude common irrelevant folders
                [".vscode", "__pycache__", "node_modules", ".github", "dist", "build", "coverage"],
                GithubRepositoryReader.FilterType.EXCLUDE,
            ),
            filter_file_extensions=(
                # Exclude non-code files (keep only relevant ones)
                [".md", ".json", ".lock", ".log", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".svg"],
                GithubRepositoryReader.FilterType.EXCLUDE,
            ),
        )

        # Load repo contents from the specified branch
        print(f"Loading repository data from branch: {branch}")
        docs = reader.load_data(branch=branch)
        return docs
    except Exception as e:
        print(f"Error parsing repository: {str(e)}")
        raise
    # Load repo contents
    docs = reader.load_data(branch="main")  # or "master" if that’s the default

    return docs

class GitHubParser:
    """
    Advanced parser for extracting metadata, file tree, and raw contents
    independently of llama_index.

    All API requests are authenticated using a GitHub token if available.
    """
    def __init__(self, github_url):
        self.github_url = github_url
        self.owner, self.repo = self._parse_github_url(github_url)
        self.api_base = f"https://api.github.com/repos/{self.owner}/{self.repo}"
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            print("WARNING: No GITHUB_TOKEN found. You may hit rate limits.")

        # Extensions to skip parsing
        self.skip_extensions = [
            ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".mp4",
            ".mp3", ".wav", ".ogg", ".webm", ".mov", ".avi", ".wmv", ".flv",
            ".mkv", ".bmp", ".tiff", ".tif", ".webp", ".apng", ".m4a", ".aac",
            ".flac", ".opus", ".zip", ".tar", ".gz", ".rar", ".7z", ".pdf",
            ".exe", ".dll"
        ]
        self.skip_filenames = [
            "package-lock.json", ".gitignore"
        ]

    def _get_headers(self):
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        return headers

    def _parse_github_url(self, url):
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            raise ValueError("Invalid GitHub repository URL")
        return path_parts[0], path_parts[1]

    def _should_skip(self, file_path):
        norm_path = file_path.replace("\\", "/").lower()
        fname = os.path.basename(norm_path)
        ext = os.path.splitext(fname)[1].lower()

        # Skip if in skip list
        if (
            norm_path.startswith("node_modules/")
            or "/node_modules/" in norm_path
            or norm_path.startswith(".git/")
            or "/.git/" in norm_path
            or norm_path.startswith("dist/")
            or "/dist/" in norm_path
            or norm_path.startswith("build/")
            or "/build/" in norm_path
            or norm_path.startswith("coverage/")
            or "/coverage/" in norm_path
            or norm_path.startswith("__pycache__/")
            or "/__pycache__/" in norm_path
        ):
            return True
        if ext in self.skip_extensions:
            return True
        if fname in self.skip_filenames:
            return True
        # Skip readme or similar
        if fname.lower().startswith("readme"):
            return True
        return False

    def get_repo_data(self):
        repo_resp = requests.get(self.api_base, headers=self._get_headers())
        if repo_resp.status_code != 200:
            raise Exception(f"Could not fetch repo metadata: {repo_resp.text}")
        repo_json = repo_resp.json()

        branch = repo_json.get("default_branch", "main")
        tree_url = f"{self.api_base}/git/trees/{branch}?recursive=1"
        tree_resp = requests.get(tree_url, headers=self._get_headers())
        if tree_resp.status_code != 200:
            raise Exception(f"Could not fetch repo tree: {tree_resp.text}")
        tree_json = tree_resp.json()
        files = {}
        for item in tree_json.get("tree", []):
            if item["type"] == "blob":
                file_path = item["path"]
                if self._should_skip(file_path):
                    continue
                print(f"Parsing file: {file_path}")
                content = ""
                # Only certain extensions will be parsed for content
                if any(file_path.endswith(ext) for ext in [
                    ".js", ".py", ".json", ".md", ".txt", ".ts",
                    ".jsx", ".tsx", ".html", ".yml", ".yaml"
                ]):
                    file_url = f"{self.api_base}/contents/{file_path}"
                    file_resp = requests.get(file_url, headers=self._get_headers())
                    if file_resp.status_code == 200:
                        content_json = file_resp.json()
                        if content_json.get("encoding") == "base64":
                            try:
                                raw = base64.b64decode(content_json["content"])
                                content = raw.decode("utf-8", errors="replace")[:20000]
                            except Exception:
                                content = ""
                files[file_path] = {
                    "type": "file",
                    "content": content
                }
        return {
            "name": repo_json.get("name"),
            "description": repo_json.get("description"),
            "language": repo_json.get("language"),
            "stars": repo_json.get("stargazers_count"),
            "created_at": repo_json.get("created_at"),
            "files": files
        }

    def get_all_chunks(self, max_chunk_size=1000):
        """
        Returns a list of dicts:
        [{"text": ..., "file_path": ...}, ...]
        Splits files longer than max_chunk_size.
        """
        repo_data = self.get_repo_data()
        chunks = []
        for file_path, fdict in repo_data["files"].items():
            content = fdict["content"]
            if not content:
                continue
            # For markdown and small files, one chunk
            if file_path.endswith(('.md', '.txt', '.json', '.yml', '.yaml')):
                chunks.append({"text": content, "file_path": file_path})
            else:
                # Code: split by double-newline or max_chunk_size
                code_chunks = [c for c in content.split('\n\n') if c.strip()]
                for c in code_chunks:
                    if len(c) > max_chunk_size:
                        # further split
                        for i in range(0, len(c), max_chunk_size):
                            chunks.append({"text": c[i:i+max_chunk_size], "file_path": file_path})
                    else:
                        chunks.append({"text": c, "file_path": file_path})
        return chunks

    def get_file_list(self):
        repo_data = self.get_repo_data()
        return list(repo_data["files"].keys())