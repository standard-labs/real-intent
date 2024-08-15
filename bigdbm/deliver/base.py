"""Defines the base output formatter."""
from abc import ABC, abstractmethod
from typing import Any

from bigdbm.schemas import MD5WithPII


class BaseOutputFormatter(ABC):
    """Base class for output formatters."""

    @abstractmethod
    def format_md5s(self, pii_md5s: list[MD5WithPII]) -> Any:
        """
        Take a list of MD5s with PII and do whatever with it according to the purpose 
        of the formatter.
        """
