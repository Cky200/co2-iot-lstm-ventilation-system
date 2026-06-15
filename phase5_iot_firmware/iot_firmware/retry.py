"""Async retry helpers with exponential backoff and jitter."""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    attempts: int = 5,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    retry_exceptions: tuple[type[BaseException], ...] = (Exception,),
    logger: logging.Logger | None = None,
    operation_name: str = "operation",
) -> T:
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    last_error: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await operation()
        except retry_exceptions as exc:
            last_error = exc
            if attempt == attempts:
                break
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay = delay * (0.75 + random.random() * 0.5)
            if logger:
                logger.warning(
                    "%s failed on attempt %s/%s: %s; retrying in %.2fs",
                    operation_name,
                    attempt,
                    attempts,
                    exc,
                    delay,
                )
            await asyncio.sleep(delay)

    assert last_error is not None
    raise last_error
