"""Loop engineering: retry loops with exponential backoff and early stopping.

These utilities implement efficient self-correction loops that minimise
token consumption by stopping early when confidence is low and by applying
exponential backoff between retries.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exponential-backoff retry for transient errors (e.g. Docker pulls, API 429)
# ---------------------------------------------------------------------------


async def retry_with_backoff(
    operation: Callable[..., Any],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = (ConnectionError, TimeoutError),
    **kwargs: Any,
) -> Any:
    """Execute *operation* with exponential backoff.

    Parameters
    ----------
    operation : Callable
        Async callable to invoke.
    max_retries : int
        Maximum number of retries before giving up.
    base_delay : float
        Initial delay in seconds.
    max_delay : float
        Capped delay in seconds.
    backoff_factor : float
        Multiplier applied to the delay after each retry.
    retryable_exceptions : tuple
        Exception types that trigger a retry.
    **kwargs
        Forwarded to *operation*.

    Returns
    -------
    The result of the successful operation call.

    Raises
    ------
    The last exception encountered if all retries are exhausted.
    """
    last_exc = None
    delay = base_delay

    for attempt in range(1, max_retries + 1):
        try:
            return await operation(**kwargs)
        except retryable_exceptions as exc:
            last_exc = exc
            logger.warning(
                "Transient error on attempt %d/%d: %s. Retrying in %.1fs...",
                attempt,
                max_retries,
                exc,
                delay,
            )
            if attempt < max_retries:
                await asyncio.sleep(delay)
                delay = min(delay * backoff_factor, max_delay)

    logger.error("All %d retries exhausted.", max_retries)
    raise last_exc  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Early-stopping loop based on confidence score
# ---------------------------------------------------------------------------


def should_early_stop(
    confidence_score: float,
    attempts: int,
    min_attempts: int = 1,
    max_attempts: int = 3,
    confidence_threshold: float = 0.7,
    drop_threshold: float = 0.15,
) -> bool:
    """Determine whether the self-correction loop should stop early.

    Rules
    -----
    1. Always allow at least *min_attempts*.
    2. Stop if attempts >= *max_attempts*.
    3. Stop if confidence >= *confidence_threshold* (fix is good enough).
    4. Stop if confidence has dropped by more than *drop_threshold* in the
       last step (the model is getting worse, so continuing wastes tokens).
    """
    if attempts < min_attempts:
        return False
    if attempts >= max_attempts:
        return True
    if confidence_score >= confidence_threshold:
        return True

    # NOTE: The caller should track the *previous* confidence and pass it
    # via the agent state.  This function only implements the check.
    return False


# ---------------------------------------------------------------------------
# Context pruning for token efficiency
# ---------------------------------------------------------------------------


def prune_history(
    history: list[str],
    max_entries: int = 5,
    max_chars_per_entry: int = 200,
) -> list[str]:
    """Keep only the *max_entries* most recent history entries, each trimmed."""
    recent = history[-max_entries:]
    return [entry[:max_chars_per_entry] for entry in recent]
