"""Utility functions for OpenAI-related operations in insights generation."""
import time
from typing import Callable, TypeVar
from functools import wraps

from real_intent.internal_logging import log


T = TypeVar("T")

def retry_openai_with_backoff(max_retries: int = 1, initial_delay: float = 2):
    """
    Decorator to retry an OpenAI API call with exponential backoff.
    
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
                    log("warning", f"OpenAI API call failed. Attempt {attempt + 1}. Retrying in {delay} seconds. Error: {e}")
                    time.sleep(delay)
                    delay *= 2  # exponential backoff
        return wrapper
    return decorator
