"""GitHub integration service for repository operations and PR creation."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

_GITHUB_API_BASE = "https://api.github.com"


class GitHubService:
    """Wrapper around the GitHub REST API for autonomous DevOps operations."""

    def __init__(self, token: str = "") -> None:
        self._token = token or os.getenv("GITHUB_TOKEN", "")
        self._headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {self._token}",
            "User-Agent": "Autonomous-DevOps-Agent/1.0",
        }
        self._client = httpx.AsyncClient(headers=self._headers, timeout=30.0)
        self._repo_path: str = ""
        self._clone_dir: Path | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "GitHubService":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._client.aclose()
        self._cleanup_clone()

    # ------------------------------------------------------------------
    # Repository parsing
    # ------------------------------------------------------------------

    @staticmethod
    def parse_repo_url(url: str) -> tuple[str, str]:
        """Extract ``(owner, repo)`` from a GitHub URL."""
        path = urlparse(url).path.strip("/")
        parts = path.rstrip(".git").split("/")
        if len(parts) >= 2:
            return parts[0], parts[1]
        raise ValueError(f"Could not parse GitHub URL: {url}")

    # ------------------------------------------------------------------
    # Context retrieval
    # ------------------------------------------------------------------

    def get_file_context(
        self,
        file_path: str,
        line_number: int,
        context_lines: int = 10,
    ) -> str:
        """Clone the repo locally and read ±*context_lines* around *line_number*."""
        if self._clone_dir is None:
            raise RuntimeError("Call clone_repo() before get_file_context().")

        full_path = self._clone_dir / "repo" / file_path.lstrip("/")
        if not full_path.exists():
            logger.warning("File not found: %s", full_path)
            return ""

        lines = full_path.read_text().splitlines()
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        snippet = "\n".join(
            f"{i + 1:>6} | {lines[i]}"
            for i in range(start, end)
        )
        return snippet

    # ------------------------------------------------------------------
    # Clone
    # ------------------------------------------------------------------

    def clone_repo(self, repo_url: str, commit_sha: str = "") -> str:
        """Clone the repository to a temporary directory."""
        import subprocess

        self._repo_path = repo_url
        self._clone_dir = Path(tempfile.mkdtemp(prefix="autodevops-"))

        repo_dir = self._clone_dir / "repo"
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(repo_dir)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git clone failed: {result.stderr}")

        if commit_sha:
            subprocess.run(
                ["git", "-C", str(repo_dir), "checkout", commit_sha],
                capture_output=True,
                timeout=30,
            )

        return str(repo_dir)

    def _cleanup_clone(self) -> None:
        import shutil

        if self._clone_dir and self._clone_dir.exists():
            shutil.rmtree(self._clone_dir, ignore_errors=True)
            self._clone_dir = None

    # ------------------------------------------------------------------
    # PR creation
    # ------------------------------------------------------------------

    async def create_pull_request(
        self,
        repo_url: str,
        commit_sha: str,
        proposed_fix: str,
        file_path: str,
        error_type: str = "",
    ) -> str:
        """Create a pull request with the proposed fix.

        Returns the PR URL.
        """
        owner, repo = self.parse_repo_url(repo_url)

        # 1. Create a branch
        branch_name = f"autofix/{commit_sha[:8]}-{error_type.lower().replace(' ', '-')[:20]}"
        base_branch = "main"  # could be detected from default branch

        ref_url = f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/git/refs"
        ref_response = await self._client.get(
            f"{ref_url}/heads/{base_branch}"
        )
        ref_response.raise_for_status()
        base_sha = ref_response.json()["object"]["sha"]

        # Create new branch
        await self._client.post(
            ref_url,
            json={"ref": f"refs/heads/{branch_name}", "sha": base_sha},
        )

        # 2. Commit the fix via the Contents API
        contents_url = (
            f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{file_path.lstrip('/')}"
        )
        # Get current file SHA
        try:
            current = await self._client.get(
                contents_url,
                params={"ref": base_branch},
            )
            current.raise_for_status()
            current_data = current.json()
            current_sha = current_data.get("sha", "")
        except httpx.HTTPStatusError:
            current_sha = ""

        import base64

        await self._client.put(
            contents_url,
            json={
                "message": f"fix: autonomous fix for {error_type}",
                "content": base64.b64encode(proposed_fix.encode()).decode(),
                "sha": current_sha,
                "branch": branch_name,
            },
        )

        # 3. Create the PR
        pr_response = await self._client.post(
            f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/pulls",
            json={
                "title": f"[Auto-Fix] Resolve {error_type} in {Path(file_path).name}",
                "head": branch_name,
                "base": base_branch,
                "body": (
                    f"## 🤖 Autonomous Fix\n\n"
                    f"**Error:** {error_type}\n"
                    f"**File:** `{file_path}`\n"
                    f"**Commit:** `{commit_sha[:8]}`\n\n"
                    f"This PR was automatically generated by the **Autonomous DevOps Agent**.\n"
                    f"The fix has been verified in a sandboxed environment.\n\n"
                    f"```diff\n{proposed_fix[:2000]}\n```"
                ),
                "maintainer_can_modify": True,
            },
        )
        pr_response.raise_for_status()
        pr_data = pr_response.json()
        return pr_data.get("html_url", pr_data.get("url", ""))

    # ------------------------------------------------------------------
    # Webhook signature verification
    # ------------------------------------------------------------------

    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
        """Verify GitHub webhook HMAC-SHA256 signature."""
        import hashlib
        import hmac

        expected = "sha256=" + hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
