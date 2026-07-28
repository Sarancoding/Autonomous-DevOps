"""LangGraph state graph definition for the self-healing CI/CD agent."""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState, GraphConfig
from .nodes import (
    analyze_failure,
    decide_next_step,
    flag_for_human,
    generate_fix,
    retrieve_context,
    sandbox_verify,
    submit_pr,
)

logger = logging.getLogger(__name__)


def create_agent_graph(
    llm_call: Callable,
    repo_manager: Any,
    sandbox: Any,
    github_client: Any,
    checkpointer: Optional[Any] = None,
) -> StateGraph:
    """Build and compile the LangGraph state machine.

    Parameters
    ----------
    llm_call : Callable
        Function that takes a prompt string and returns an LLM response string.
    repo_manager : Any
        Object with ``get_file_context(file_path, line_number, context_lines)``.
    sandbox : Any
        Object with ``run_tests(...)`` for sandboxed verification.
    github_client : Any
        Object with ``create_pull_request(...)`` for submitting verified fixes.
    checkpointer : optional
        LangGraph checkpointer for persistence (default: MemorySaver).
    """
    checkpointer = checkpointer or MemorySaver()

    # ------------------------------------------------------------------ #
    # Build graph
    # ------------------------------------------------------------------ #
    workflow = StateGraph(AgentState)

    # Register nodes
    workflow.add_node("analyze_failure", lambda s: analyze_failure(s, llm_call))
    workflow.add_node("retrieve_context", lambda s: retrieve_context(s, repo_manager))
    workflow.add_node("generate_fix", lambda s: generate_fix(s, llm_call))
    workflow.add_node("sandbox_verify", lambda s: sandbox_verify(s, sandbox))
    workflow.add_node("submit_pr", lambda s: submit_pr(s, github_client))
    workflow.add_node("flag_for_human", flag_for_human)

    # Entry point
    workflow.set_entry_point("analyze_failure")

    # Edges
    workflow.add_edge("analyze_failure", "retrieve_context")
    workflow.add_edge("retrieve_context", "generate_fix")
    workflow.add_edge("generate_fix", "sandbox_verify")

    # Conditional edge: loop or terminate
    workflow.add_conditional_edges(
        "sandbox_verify",
        decide_next_step,
        {
            "submit_pr": "submit_pr",
            "generate_fix": "generate_fix",
            "flag_for_human": "flag_for_human",
        },
    )

    workflow.add_edge("submit_pr", END)
    workflow.add_edge("flag_for_human", END)

    # Compile
    return workflow.compile(checkpointer=checkpointer)
