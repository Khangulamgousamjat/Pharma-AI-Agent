"""
utils/retries.py — Exponential backoff retry logic with jitter.

Phase 3 addition: Used by webhook_service.py for warehouse fulfillment
retries. Also usable for any external service call that needs resilience.

Algorithm:
  delay = base_delay * (2 ** attempt) + random_jitter(0..1)
  Max delay is capped at 60 seconds to avoid excessive waiting.

Usage:
  result = await exponential_backoff_retry(
      func=my_async_func,
      args=(arg1, arg2),
      max_retries=5,
      base_delay=1.0,
      on_failure=lambda e, attempt: logger.warning(f"Attempt {attempt} failed: {e}"),
  )
"""

import asyncio
import random
import logging
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

# Maximum delay cap (seconds) regardless of attempt number
MAX_DELAY_SECONDS = 60.0


async def exponential_backoff_retry(
    func: Callable,
    args: tuple = (),
    kwargs: dict = None,
    max_retries: int = 5,
    base_delay: float = 1.0,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
    exceptions_to_retry: tuple = (Exception,),
) -> Any:
    """
    Execute an async function with exponential backoff retries.

    Retry strategy:
      - Attempt 1: immediate
      - Attempt 2: ~2s + jitter
      - Attempt 3: ~4s + jitter
      - Attempt 4: ~8s + jitter
      - Attempt 5: ~16s + jitter
      - Cap at 60 seconds

    Args:
        func: Async callable to execute
        args: Positional arguments to pass to func
        kwargs: Keyword arguments to pass to func
        max_retries: Maximum number of attempts total (including first)
        base_delay: Base delay in seconds (multiplied exponentially)
        on_retry: Optional callback(exception, attempt_number) called on each failed attempt
        exceptions_to_retry: Exception types that should trigger a retry

    Returns:
        Any: Return value of func on success

    Raises:
        Exception: The last exception raised if all retries exhausted
    """
    if kwargs is None:
        kwargs = {}

    last_exception: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            result = await func(*args, **kwargs)
            if attempt > 1:
                logger.info(f"[Retry] Success on attempt {attempt}/{max_retries}")
            return result

        except exceptions_to_retry as e:
            last_exception = e

            if attempt == max_retries:
                logger.error(
                    f"[Retry] All {max_retries} attempts exhausted. Final error: {e}"
                )
                break

            # Calculate delay with full-jitter strategy
            # Full jitter: sleep = random(0, min(cap, base * 2**attempt))
            raw_delay = base_delay * (2 ** attempt)
            capped_delay = min(raw_delay, MAX_DELAY_SECONDS)
            jitter = random.uniform(0, capped_delay)

            logger.warning(
                f"[Retry] Attempt {attempt}/{max_retries} failed: {e}. "
                f"Retrying in {jitter:.2f}s..."
            )

            if on_retry:
                on_retry(e, attempt)

            await asyncio.sleep(jitter)

    raise last_exception


def exponential_backoff_retry_sync(
    func: Callable,
    args: tuple = (),
    kwargs: dict = None,
    max_retries: int = 5,
    base_delay: float = 1.0,
) -> Any:
    """
    Synchronous version of exponential_backoff_retry.

    Use this when you cannot use async/await (e.g., inside a sync test fixture).

    Args:
        func: Sync callable to execute
        args: Positional arguments
        kwargs: Keyword arguments
        max_retries: Maximum attempts
        base_delay: Base delay seconds

    Returns:
        Any: Function result on success

    Raises:
        Exception: Last raised exception if all retries fail
    """
    import time

    if kwargs is None:
        kwargs = {}

    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt == max_retries:
                break
            raw_delay = base_delay * (2 ** attempt)
            delay = min(random.uniform(0, raw_delay), MAX_DELAY_SECONDS)
            logger.warning(f"[RetrySync] Attempt {attempt} failed: {e}. Sleeping {delay:.2f}s")
            time.sleep(delay)

    raise last_exception
