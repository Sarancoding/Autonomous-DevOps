"""LangGraph agent nodes implementing the CI/CD self-healing pipeline."""

from __future__ import annotations

import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Callable

from .state import AgentState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: regex-based stack trace parser (LLM fallback only if ambiguous)
# ---------------------------------------------------------------------------

_COMMON_TRACE_PATTERNS = [
    re.compile(r'File\s+"([^"]+)",\s*line\s+(\d+)', re.IGNORECASE),
    re.compile(r'at\s+(.+):(\d+):(\d+)', re.IGNORECASE),
    re.compile(r'([\w/\\]+\.\w+):(\d+):(\d+)', re.IGNORECASE),
]


def _parse_stack_trace(log_text: str) -> dict[str, Any]:
    """Extract file path and line number from a stack trace using regex.

    Returns dict with file_path, line_number, error_type keys.
    Falls back to an empty dict when nothing is matched.
    """
    for pattern in _COMMON_TRACE_PATTERNS:
        match = pattern.search(log_text)
        if match:
            groups = match.groups()
            return {
                "file_path": groups[0],
                "line_number": int(groups[1]),
                "error_type": _extract_error_type(log_text),
            }
    return {"file_path": "", "line_number": 0, "error_type": ""}


def _extract_error_type(log_text: str) -> str:
    error_match = re.search(
        r"(?:Error|Exception|FAIL|AssertionError|TypeError|ValueError|KeyError|IndexError|AttributeError|ImportError|ModuleNotFoundError)\b.*",
        log_text,
        re.IGNORECASE,
    )
    return error_match.group(0).strip() if error_match else "UnknownError"


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def analyze_failure(state: AgentState, llm_call: Callable) -> AgentState:
    """Parse raw logs and extract failure context.

    Optimization: use regex first; only invoke LLM when the trace is ambiguous.
    """
    thoughts = list(state.get("agent_thoughts", []))
    thoughts.append("🔍 Analyzing failure logs...")

    parsed = _parse_stack_trace(state["failure_log"])
    file_path = parsed.get("file_path", "")
    line_number = parsed.get("line_number", 0)
    error_type = parsed.get("error_type", "")

    # If regex gave us nothing useful, fall back to LLM
    if not file_path:
        thoughts.append("⚙️ Regex parsing incomplete — querying LLM for trace analysis...")
        prompt = (
            "You are analyzing a CI/CD test failure log. Extract the following:\n"
            "1. The file path where the error occurred\n"
            "2. The line number (as an integer)\n"
            "3. The error type/message\n\n"
            f"Failure log:\n{state['failure_log'][:2000]}\n\n"
            "Respond in JSON: {\"file_path\": \"...\", \"line_number\": 0, \"error_type\": \"...\"}"
        )
        result = llm_call(prompt)
        try:
            import json
            parsed = json.loads(result)
            file_path = parsed.get("file_path", file_path)
            line_number = parsed.get("line_number", line_number)
            error_type = parsed.get("error_type", error_type)
        except (json.JSONDecodeError, TypeError):
            thoughts.append("⚠️ LLM fallback parsing failed; proceeding with partial data.")

    return {
        **state,
        "file_path": file_path,
        "line_number": line_number,
        "error_type": error_type or "UnknownError",
        "agent_thoughts": thoughts,
    }


def retrieve_context(state: AgentState, repo_manager: Any) -> AgentState:
    """Clone repo (or verify checkout) and read ±10 lines around the error."""
    thoughts = list(state.get("agent_thoughts", []))
    thoughts.append(f"📂 Retrieving context around {state['file_path']}:{state['line_number']}...")

    code_snippet = ""
    try:
        # Use the repo manager to get the file content
        code_snippet = repo_manager.get_file_context(
            state["file_path"],
            state["line_number"],
            context_lines=10,
        )
    except Exception as exc:
        logger.warning("Could not retrieve file context: %s", exc)
        code_snippet = ""

    history_entry = (
        f"[Attempt {state['attempts'] + 1}] "
        f"File: {state['file_path']}:{state['line_number']} | "
        f"Error: {state['error_type']}"
    )

    return {
        **state,
        "history": state.get("history", []) + [history_entry],
        "code_diff": code_snippet,
        "agent_thoughts": thoughts,
    }


def generate_fix(state: AgentState, llm_call: Callable) -> AgentState:
    """LLM-powered fix generation node.

    Loop engineering: if confidence < threshold, a refine sub-graph re-runs
    this node with the previous attempt's output as additional context.
    """
    thoughts = list(state.get("agent_thoughts", []))
    thoughts.append(f"🧠 Generating fix (attempt {state['attempts'] + 1}/{state['max_attempts']})...")

    # Build a context-aware prompt
    prev_attempt_context = ""
    attempt_count = state.get("attempts", 0)
    if attempt_count > 0 and state.get("history"):
        prev = state["history"][-1]
        prev_attempt_context = (
            f"\nPrevious fix attempt: {state.get('proposed_fix', '')}\n"
            f"Previous outcome: {prev}\n"
            "Please learn from the previous attempt and produce a corrected fix."
        )

    prompt = (
        "You are an expert software engineer fixing a CI/CD test failure.\n\n"
        f"**Error Type:** {state['error_type']}\n"
        f"**File:** {state['file_path']}:{state['line_number']}\n"
        f"**Stack Trace:**\n{state['stack_trace'][:1500]}\n"
        f"**Code Context:**\n{state['code_diff'][:2000]}\n"
        f"{prev_attempt_context}\n\n"
        "Provide a fix as a unified diff (---/+++ format). "
        "Include a confidence score between 0.0 and 1.0 at the end of your response "
        "on a line by itself: `CONFIDENCE: 0.95`\n"
        "Then rate the complexity: `COMPLEXITY: simple|moderate|complex`"
    )

    result = llm_call(prompt)

    # Parse confidence and fix
    confidence = 0.5
    fix = result
    for line in result.split("\n"):
        if line.startswith("CONFIDENCE:"):
            try:
                confidence = float(line.split(":")[1].strip())
            except (ValueError, IndexError):
                confidence = 0.5
            fix = fix.replace(line, "").strip()

    return {
        **state,
        "proposed_fix": fix,
        "confidence_score": confidence,
        "attempts": attempt_count + 1,
        "agent_thoughts": thoughts,
    }


def sandbox_verify(state: AgentState, sandbox: Any) -> AgentState:
    """Run the proposed fix through a sandboxed Docker test environment."""
    thoughts = list(state.get("agent_thoughts", []))
    thoughts.append("🧪 Running sandbox verification...")

    test_results = {}
    try:
        test_results = sandbox.run_tests(
            repo_url=state["repo_url"],
            commit_sha=state["commit_sha"],
            proposed_fix=state["proposed_fix"],
            file_path=state["file_path"],
        )
    except Exception as exc:
        logger.error("Sandbox verification failed: %s", exc)
        test_results = {
            "passed": False,
            "exit_code": -1,
            "logs": str(exc),
            "error": "Sandbox execution error",
        }

    passed = test_results.get("passed", False)
    if passed:
        thoughts.append("✅ All tests passed!")
    else:
        thoughts.append(f"❌ Tests failed: {test_results.get('logs', '')[:200]}")

    return {
        **state,
        "test_results": test_results,
        "agent_thoughts": thoughts,
    }


def decide_next_step(state: AgentState) -> str:
    """Conditional edge router.

    Returns the name of the next node to execute.
    """
    test_passed = state.get("test_results", {}).get("passed", False)
    attempts = state.get("attempts", 0)
    max_attempts = state.get("max_attempts", 3)

    if test_passed:
        return "submit_pr"

    if attempts < max_attempts:
        return "generate_fix"  # Loop: try again with new context

    # Max attempts exceeded — flag for human review
    return "flag_for_human"


def submit_pr(state: AgentState, github_client: Any) -> AgentState:
    """Submit a verified pull request with the fix."""
    thoughts = list(state.get("agent_thoughts", []))
    thoughts.append("🚀 Submitting pull request...")

    pr_url = ""
    try:
        pr_url = github_client.create_pull_request(
            repo_url=state["repo_url"],
            commit_sha=state["commit_sha"],
            proposed_fix=state["proposed_fix"],
            file_path=state["file_path"],
            error_type=state["error_type"],
        )
        thoughts.append(f"✅ PR submitted: {pr_url}")
    except Exception as exc:
        logger.error("Failed to submit PR: %s", exc)
        thoughts.append(f"❌ PR submission failed: {exc}")

    return {
        **state,
        "pr_url": pr_url or None,
        "agent_thoughts": thoughts,
    }


def flag_for_human(state: AgentState) -> AgentState:
    """Terminal node: mark the job as needing human intervention."""
    thoughts = list(state.get("agent_thoughts", []))
    thoughts.append(
        "⚠️ Max retry attempts reached. Escalating to human reviewer. "
        f"Details logged for job {state['job_id']}."
    )
    return {
        **state,
        "error": "Max attempts exceeded — requires human review.",
        "agent_thoughts": thoughts,
    }
