"""Agent state definition using TypedDict for LangGraph state machine."""

from __future__ import annotations

from typing import Optional, TypedDict


class AgentState(TypedDict):
    """Persistent state that flows through all LangGraph nodes."""

    repo_url: str
    commit_sha: str
    failure_log: str
    stack_trace: str
    file_path: str
    line_number: int
    error_type: str
    proposed_fix: str
    code_diff: str
    test_results: dict
    pr_url: Optional[str]
    confidence_score: float
    attempts: int
    max_attempts: int
    history: list[str]
    error: Optional[str]
    job_id: str
    agent_thoughts: list[str]


class GraphConfig(TypedDict, total=False):
    """Configuration for the agent graph execution."""

    model_name: str
    max_attempts: int
    confidence_threshold: float
    repo_path: str
