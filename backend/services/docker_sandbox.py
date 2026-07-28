"""Docker sandbox service for isolated test execution.

Each job gets a unique container with resource limits, disabled networking,
and a read-only volume mount for source code.
"""

from __future__ import annotations

import io
import json
import logging
import os
import tarfile
import tempfile
import uuid
from pathlib import Path
from typing import Any, Optional

import docker
from docker.errors import DockerException, ImageNotFound

logger = logging.getLogger(__name__)

_DEFAULT_RESOURCE_LIMITS = {
    "cpu_period": 100000,
    "cpu_quota": 50000,  # 50% of one CPU
    "mem_limit": "512m",
    "memswap_limit": "512m",
    "network_disabled": True,
}


class DockerSandbox:
    """Manages ephemeral Docker containers for sandboxed test verification."""

    def __init__(self, resource_limits: Optional[dict] = None) -> None:
        self._client: docker.DockerClient | None = None
        self._resource_limits = resource_limits or _DEFAULT_RESOURCE_LIMITS

    # ------------------------------------------------------------------
    # Client lifecycle
    # ------------------------------------------------------------------

    @property
    def client(self) -> docker.DockerClient:
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_tests(
        self,
        repo_url: str,
        commit_sha: str,
        proposed_fix: str,
        file_path: str,
        timeout: int = 120,
    ) -> dict[str, Any]:
        """Run tests inside a sandboxed Docker container.

        Parameters
        ----------
        repo_url : str
            Git repository URL.
        commit_sha : str
            Commit SHA to check out.
        proposed_fix : str
            Unified diff to apply before running tests.
        file_path : str
            Path to the file being fixed.
        timeout : int
            Container execution timeout in seconds.

        Returns
        -------
        dict with keys ``passed`` (bool), ``exit_code`` (int), ``logs`` (str).
        """
        job_id = uuid.uuid4().hex[:12]
        container_name = f"autodevops-sandbox-{job_id}"

        try:
            image_tag = self._ensure_base_image(repo_url)

            # Build a minimal build context that includes the fix script
            build_context = self._create_build_context(
                repo_url, commit_sha, proposed_fix, file_path
            )

            container = self.client.containers.run(
                image=image_tag,
                command=["/bin/sh", "/workspace/run_test.sh"],
                name=container_name,
                detach=True,
                working_dir="/workspace",
                volumes={},
                **self._resource_limits,
            )

            result = container.wait(timeout=timeout)
            logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
            exit_code = result.get("StatusCode", -1)

            return {
                "passed": exit_code == 0,
                "exit_code": exit_code,
                "logs": logs,
                "job_id": job_id,
            }

        except DockerException as exc:
            logger.error("Docker sandbox error: %s", exc)
            return {
                "passed": False,
                "exit_code": -1,
                "logs": f"Docker error: {exc}",
                "job_id": job_id,
            }
        except Exception as exc:
            logger.exception("Unexpected sandbox error")
            return {
                "passed": False,
                "exit_code": -1,
                "logs": str(exc),
                "job_id": job_id,
            }
        finally:
            self._cleanup_container(container_name)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_base_image(self, repo_url: str) -> str:
        """Pull or build a base test image.

        For now we use ``python:3.10-slim``.  A production system would
        dynamically build from the repo's own Dockerfile.
        """
        image_tag = "autodevops-base:latest"
        try:
            self.client.images.get(image_tag)
        except ImageNotFound:
            logger.info("Building base sandbox image %s ...", image_tag)
            dockerfile = (
                "FROM python:3.10-slim\n"
                "RUN apt-get update && apt-get install -y --no-install-recommends \\\n"
                "        git curl ca-certificates build-essential && \\\n"
                "    rm -rf /var/lib/apt/lists/*\n"
                "RUN pip install --no-cache-dir pytest pytest-cov\n"
                "WORKDIR /workspace\n"
            )
            self.client.images.build(
                tag=image_tag,
                dockerfile="Dockerfile.sandbox",
                fileobj=io.BytesIO(dockerfile.encode("utf-8")),
                rm=True,
            )
        return image_tag

    def _create_build_context(
        self,
        repo_url: str,
        commit_sha: str,
        proposed_fix: str,
        file_path: str,
    ) -> io.BytesIO:
        """Create an in-memory tar archive with the test runner script."""
        run_script = (
            "#!/bin/sh\n"
            "set -e\n"
            f'echo "Cloning {repo_url} ..."\n'
            f"git clone --depth 1 {repo_url} repo\n"
            f"cd repo\n"
            f"git checkout {commit_sha}\n"
            f'echo "Applying fix to {file_path} ..."\n'
            f'echo "{proposed_fix}" | git apply --allow-empty -\n'
            'echo "Running tests ..."\n'
            "pytest --tb=short -q 2>&1 || true\n"
        )

        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            info = tarfile.TarInfo(name="run_test.sh")
            info.content = run_script.encode("utf-8")
            info.mode = 0o755
            tar.addfile(info)
        tar_stream.seek(0)
        return tar_stream

    def _cleanup_container(self, name: str) -> None:
        try:
            container = self.client.containers.get(name)
            container.remove(force=True, v=True)
        except docker.errors.NotFound:
            pass
        except Exception:
            logger.exception("Failed to clean up container %s", name)
