"""Utility functions for the real_intent package."""
import time
from typing import Callable, TypeVar
from functools import wraps
import random

from real_intent.internal_logging import log


T = TypeVar("T")

def retry_with_backoff(max_retries: int = 1, initial_delay: float = 2):
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries.
        initial_delay: Initial delay between retries in seconds.

    Returns:
        A decorator function.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise e

                    jitter = delay * random.uniform(0.5, 1.5)
                    log("warning", f"Function {func.__name__} failed. Attempt {attempt + 1}. Retrying in {jitter:.2f} seconds. Error: {e}")
                    time.sleep(jitter)
                    delay *= 2  # exponential backoff
        return wrapper
    return decorator
