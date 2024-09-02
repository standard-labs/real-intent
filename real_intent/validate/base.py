"""Base abstract interface for validators."""
from abc import ABC, abstractmethod

from real_intent.schemas import MD5WithPII
from real_intent.internal_logging import log, log_span


class BaseValidator(ABC):
    """Base validator for leads."""

    def validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove leads that are considered invalid based on implemented criteria."""
        with log_span(f"Validating {len(md5s)} leads with {self.__class__.__name__}", _level="debug"):
            initial_len = len(md5s)
            result = self._validate(md5s)
            removed_leads = initial_len - len(result)
            log("debug", f"{self.__class__.__name__} removed {removed_leads} leads.")
            return result

    @abstractmethod
    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Internal method to be implemented by subclasses to perform the actual validation."""
        pass
