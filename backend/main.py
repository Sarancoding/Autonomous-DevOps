"""FastAPI application — webhook listener, REST API, WebSocket logs, and LangGraph orchestration."""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Optional

from fastapi import FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent import create_agent_graph, AgentState, GraphConfig
from config import settings
from models import (
    AgentStatusResponse,
    GitHubWebhookPayload,
    JobConfig,
    JobLogEntry,
    JobResponse,
    MetricsResponse,
    TriggerRequest,
)
from services import DockerSandbox, GitHubService, LangfuseObserver, LLMService

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("autonomous-devops")

# ---------------------------------------------------------------------------
# In-memory stores (for demo / BYOK sessions)
# ---------------------------------------------------------------------------

_jobs: dict[str, dict[str, Any]] = {}
_websocket_connections: dict[str, list[WebSocket]] = {}
_user_keys: dict[str, dict[str, str]] = {}  # session_id -> {llm_key, github_key}

_start_time: float = time.time()

# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Autonomous DevOps Agent starting — Langfuse=%s Docker=%s",
        settings.langfuse_enabled,
        settings.docker_enabled,
    )
    yield
    logger.info("Autonomous DevOps Agent shutting down.")


app = FastAPI(
    title="Autonomous DevOps Agent",
    version="1.0.0",
    description="Self-healing CI/CD agent powered by LangGraph",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_user_keys(authorization: str = "") -> tuple[str, str]:
    """Extract user-provided API keys from the Authorization header.

    Format: ``Bearer <session_id>`` where the session stores keys.
    """
    if not authorization.startswith("Bearer "):
        return (settings.llm_api_key, settings.github_token)

    session_id = authorization[7:]
    keys = _user_keys.get(session_id, {})
    return (
        keys.get("llm_api_key", settings.llm_api_key),
        keys.get("github_token", settings.github_token),
    )


def _build_services(llm_key: str, github_key: str) -> dict[str, Any]:
    """Construct service objects for an agent run."""
    llm = LLMService(api_key=llm_key)
    github = GitHubService(token=github_key)
    sandbox = DockerSandbox() if settings.docker_enabled else None
    observer = LangfuseObserver()
    return {"llm": llm, "github": github, "sandbox": sandbox, "observer": observer}


async def _publish_log(job_id: str, node: str, message: str, level: str = "info") -> None:
    """Broadcast a log entry to all WebSocket clients for *job_id*."""
    entry = {
        "type": "log",
        "job_id": job_id,
        "node": node,
        "message": message,
        "level": level,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if job_id in _jobs:
        _jobs[job_id].setdefault("logs", []).append(JobLogEntry(**entry))

    if job_id in _websocket_connections:
        dead: list[WebSocket] = []
        for ws in _websocket_connections[job_id]:
            try:
                await ws.send_json(entry)
            except Exception:
                dead.append(ws)
        for ws in dead:
            _websocket_connections[job_id].remove(ws)


def _llm_call_wrapper(job_id: str, llm_service: LLMService) -> Any:
    """Return a callable that publishes logs for each LLM interaction."""

    async def _call(prompt: str) -> str:
        await _publish_log(job_id, "llm", "🤖 Querying LLM...")
        result = await llm_service.generate_fix(prompt)
        await _publish_log(job_id, "llm", "✅ LLM response received.")
        return result

    return _call


# ---------------------------------------------------------------------------
# REST Endpoints
# ---------------------------------------------------------------------------


@app.get("/api/status", response_model=AgentStatusResponse)
async def health_check():
    return AgentStatusResponse(
        status="ok",
        langfuse_enabled=settings.langfuse_enabled,
        jobs_running=sum(
            1 for j in _jobs.values() if j.get("status") == "running"
        ),
        uptime_seconds=time.time() - _start_time,
    )


@app.post("/api/trigger")
async def trigger_job(
    payload: TriggerRequest,
    authorization: str = Header(default=""),
):
    """Manually trigger an agent run for testing or ad-hoc fixes."""
    llm_key, github_key = _get_user_keys(authorization)

    job_id = uuid.uuid4().hex[:12]
    _jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "repo_url": payload.repo_url,
        "commit_sha": payload.commit_sha,
        "error_type": "",
        "proposed_fix": "",
        "pr_url": None,
        "confidence_score": 0.0,
        "attempts": 0,
        "max_attempts": payload.max_attempts,
        "logs": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    await _publish_log(job_id, "system", f"🚀 Job {job_id} created — analysing failure...")

    # Launch the agent graph in the background
    asyncio.create_task(
        _run_agent(job_id, payload, llm_key, github_key)
    )

    return {"job_id": job_id, "status": "pending"}


@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(""),
    x_hub_signature_256: str = Header(""),
):
    """Receive GitHub webhook events for CI/CD failures."""
    body = await request.body()

    # Verify signature
    if settings.github_webhook_secret:
        if not GitHubService.verify_webhook_signature(
            body, x_hub_signature_256, settings.github_webhook_secret
        ):
            raise HTTPException(403, "Invalid webhook signature")

    payload = await request.json()
    logger.info("Webhook received: event=%s repo=%s", x_github_event, payload.get("repository", {}).get("full_name", ""))

    # Only process check_run and push events with failures
    if x_github_event not in ("check_run", "push", "workflow_run"):
        return {"status": "ignored", "reason": f"Unsupported event: {x_github_event}"}

    repo_url = payload.get("repository", {}).get("clone_url", "")
    commit_sha = (
        payload.get("check_run", {}).get("head_sha", "")
        or payload.get("after", "")
        or payload.get("workflow_run", {}).get("head_commit", {}).get("id", "")
    )

    trigger = TriggerRequest(
        repo_url=repo_url,
        commit_sha=commit_sha,
        failure_log=json.dumps(payload.get("check_run", {}).get("output", {}), indent=2),
        max_attempts=3,
    )

    return await trigger_job(trigger)


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return JobResponse(**job)


@app.get("/api/metrics", response_model=MetricsResponse)
async def get_metrics():
    total = len(_jobs)
    if total == 0:
        return MetricsResponse()

    successes = sum(1 for j in _jobs.values() if j["status"] == "success")
    failed = sum(1 for j in _jobs.values() if j["status"] == "failed")
    review = sum(1 for j in _jobs.values() if j["status"] == "needs_review")

    return MetricsResponse(
        total_jobs=total,
        success_count=successes,
        failed_count=failed,
        needs_review_count=review,
        avg_attempts_per_job=sum(j["attempts"] for j in _jobs.values()) / total,
        avg_confidence=sum(j["confidence_score"] for j in _jobs.values()) / total,
    )


@app.post("/api/config")
async def update_config(config: JobConfig):
    """Update user-configurable job settings (per session)."""
    # In a production system this would persist per user.
    return {"message": "Config updated (in-memory)", **config.model_dump()}


@app.post("/api/session/keys")
async def store_user_keys(
    llm_api_key: str = "",
    github_token: str = "",
):
    """Store user API keys in an ephemeral session."""
    session_id = uuid.uuid4().hex[:16]
    _user_keys[session_id] = {
        "llm_api_key": llm_api_key,
        "github_token": github_token,
    }
    return {"session_id": session_id, "message": "Keys stored temporarily."}


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@app.websocket("/ws/jobs/{job_id}")
async def job_websocket(websocket: WebSocket, job_id: str):
    await websocket.accept()
    _websocket_connections.setdefault(job_id, []).append(websocket)
    try:
        # Send existing logs
        if job_id in _jobs:
            for log in _jobs[job_id].get("logs", []):
                await websocket.send_json({
                    "type": "log",
                    "job_id": job_id,
                    **log.model_dump() if hasattr(log, "model_dump") else log,
                })

        # Keep connection alive for new logs
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        _websocket_connections.setdefault(job_id, []).remove(websocket)


# ---------------------------------------------------------------------------
# Graph execution
# ---------------------------------------------------------------------------


async def _run_agent(
    job_id: str,
    payload: TriggerRequest,
    llm_key: str,
    github_key: str,
) -> None:
    """Execute the LangGraph agent in the background."""
    svc = _build_services(llm_key, github_key)

    try:
        _jobs[job_id]["status"] = "running"

        # Build the LangGraph
        graph = create_agent_graph(
            llm_call=_llm_call_wrapper(job_id, svc["llm"]),
            repo_manager=svc["github"],
            sandbox=svc["sandbox"],
            github_client=svc["github"],
        )

        # Initial state
        initial_state: AgentState = {
            "repo_url": payload.repo_url,
            "commit_sha": payload.commit_sha,
            "failure_log": payload.failure_log,
            "stack_trace": payload.failure_log,
            "file_path": "",
            "line_number": 0,
            "error_type": "",
            "proposed_fix": "",
            "code_diff": "",
            "test_results": {},
            "pr_url": None,
            "confidence_score": 0.0,
            "attempts": 0,
            "max_attempts": payload.max_attempts,
            "history": [],
            "error": None,
            "job_id": job_id,
            "agent_thoughts": [],
        }

        # Clone the repo before running the graph
        try:
            svc["github"].clone_repo(payload.repo_url, payload.commit_sha)
        except Exception as exc:
            logger.warning("Repo clone failed (continuing): %s", exc)

        # Execute the graph
        result = await graph.ainvoke(initial_state)

        # Update job record
        _jobs[job_id].update({
            "status": "success" if result.get("pr_url") else "needs_review",
            "error_type": result.get("error_type", ""),
            "proposed_fix": result.get("proposed_fix", ""),
            "pr_url": result.get("pr_url"),
            "confidence_score": result.get("confidence_score", 0.0),
            "attempts": result.get("attempts", 0),
            "updated_at": datetime.now(timezone.utc),
        })

        await _publish_log(job_id, "system", f"✅ Job {job_id} complete.")

    except Exception as exc:
        logger.exception("Agent run failed for job %s", job_id)
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(exc)
        _jobs[job_id]["updated_at"] = datetime.now(timezone.utc)
        await _publish_log(job_id, "system", f"❌ Job {job_id} failed: {exc}", level="error")

    finally:
        # Clean up
        if svc.get("observer"):
            svc["observer"].finalize(job_id)
        await svc.get("github", GitHubService()).__aexit__()
        await svc.get("llm", LLMService()).__aexit__()
