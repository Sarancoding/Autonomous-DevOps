"""Pydantic models for API request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Webhook
# ---------------------------------------------------------------------------


class GitHubWebhookPayload(BaseModel):
    """Parsed payload from a GitHub webhook event."""

    event: str = ""
    delivery_id: str = ""
    repository: str = ""
    commit_sha: str = ""
    failure_log: str = ""
    stack_trace: str = ""


# ---------------------------------------------------------------------------
# Trigger
# ---------------------------------------------------------------------------


class TriggerRequest(BaseModel):
    """Manual trigger request body."""

    repo_url: str = Field(..., description="GitHub repository URL")
    commit_sha: str = Field("", description="Commit SHA to analyse")
    failure_log: str = Field(..., description="Test failure log or stack trace")
    max_attempts: int = Field(3, ge=1, le=10)
    model: str = Field("gpt-4o", description="LLM model to use")


# ---------------------------------------------------------------------------
# Job
# ---------------------------------------------------------------------------


class JobLogEntry(BaseModel):
    """A single log entry in a job's timeline."""

    timestamp: datetime
    node: str
    message: str
    level: str = "info"


class JobResponse(BaseModel):
    """Response returned when querying a job."""

    job_id: str
    status: str  # pending | running | success | failed | needs_review
    repo_url: str
    commit_sha: str
    error_type: str
    proposed_fix: str = ""
    pr_url: Optional[str] = None
    confidence_score: float = 0.0
    attempts: int = 0
    max_attempts: int = 3
    logs: list[JobLogEntry] = []
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Status & Metrics
# ---------------------------------------------------------------------------


class AgentStatusResponse(BaseModel):
    """Health check and status response."""

    status: str = "ok"
    version: str = "1.0.0"
    langfuse_enabled: bool = False
    jobs_running: int = 0
    uptime_seconds: float = 0.0


class JobConfig(BaseModel):
    """User-configurable job settings."""

    max_attempts: int = Field(3, ge=1, le=10)
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0)
    model_name: str = "gpt-4o"
    cheap_model: str = "gpt-4o-mini"


class MetricsResponse(BaseModel):
    """Aggregated metrics across all jobs."""

    total_jobs: int = 0
    success_count: int = 0
    failed_count: int = 0
    needs_review_count: int = 0
    total_tokens_used: int = 0
    total_cost_estimate: float = 0.0
    avg_attempts_per_job: float = 0.0
    avg_confidence: float = 0.0
