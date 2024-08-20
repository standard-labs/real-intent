"""Base abstract interface for validators."""
from abc import ABC, abstractmethod

from bigdbm.schemas import MD5WithPII


class BaseValidator(ABC):
    """Base validator for leads."""

    @abstractmethod
    def validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove leads that are considered invalid based on implemented criteria."""
