"""Langfuse observer for tracing, token tracking, and cost monitoring."""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

from langfuse import Langfuse
from langfuse.decorators import langfuse_context, observe

logger = logging.getLogger(__name__)


class LangfuseObserver:
    """Wrapper around Langfuse for agent execution tracing.

    Usage::

        observer = LangfuseObserver()
        trace_id = observer.start_trace(job_id="...", repo_url="...")
        observer.update_trace(trace_id, step="analyze_failure", ...)
        observer.score_trace(trace_id, ...)
        observer.finalize(trace_id)
    """

    def __init__(self) -> None:
        self._client: Langfuse | None = None
        self._enabled = bool(
            os.getenv("LANGFUSE_PUBLIC_KEY")
            and os.getenv("LANGFUSE_SECRET_KEY")
        )
        self._traces: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @property
    def client(self) -> Langfuse:
        if self._client is None and self._enabled:
            self._client = Langfuse(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            )
        return self._client  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Trace management
    # ------------------------------------------------------------------

    def start_trace(
        self,
        job_id: str,
        repo_url: str = "",
        commit_sha: str = "",
        model: str = "",
    ) -> str:
        """Create a new Langfuse trace and return its ID."""
        if not self._enabled:
            return job_id

        trace = self.client.trace(
            name="autonomous-devops-run",
            user_id="system",
            metadata={
                "job_id": job_id,
                "repo_url": repo_url,
                "commit_sha": commit_sha,
                "model": model,
            },
        )
        self._traces[job_id] = trace.id
        logger.info("Langfuse trace started: %s (job=%s)", trace.id, job_id)
        return trace.id

    def update_trace(
        self,
        job_id: str,
        step: str,
        input_data: str = "",
        output_data: str = "",
        tokens_in: int = 0,
        tokens_out: int = 0,
        duration_ms: float = 0.0,
    ) -> None:
        """Record a step/span inside an existing trace."""
        if not self._enabled:
            return

        trace_id = self._traces.get(job_id)
        if not trace_id:
            logger.warning("No trace found for job %s", job_id)
            return

        self.client.span(
            trace_id=trace_id,
            name=step,
            input=input_data[:500],
            output=output_data[:500],
            usage={
                "input": tokens_in,
                "output": tokens_out,
                "unit": "TOKENS",
            },
        )
        logger.debug("Trace %s | Step %s recorded.", trace_id, step)

    def score_trace(
        self,
        job_id: str,
        name: str = "success",
        value: float = 1.0,
        comment: str = "",
    ) -> None:
        """Attach a score to the trace (e.g. for evaluation)."""
        if not self._enabled:
            return

        trace_id = self._traces.get(job_id)
        if not trace_id:
            return

        self.client.score(
            trace_id=trace_id,
            name=name,
            value=value,
            comment=comment,
        )

    def finalize(self, job_id: str) -> None:
        """Finalise the trace (flush)."""
        if not self._enabled:
            return

        self.client.flush()
        self._traces.pop(job_id, None)
        logger.info("Langfuse trace finalized for job %s", job_id)

    # ------------------------------------------------------------------
    # Convenience decorator-based observation
    # ------------------------------------------------------------------

    @staticmethod
    def observe_agent_node(fn: Any) -> Any:
        """Decorate a LangGraph node function with Langfuse observation."""
        return observe(name=fn.__name__)(fn)
