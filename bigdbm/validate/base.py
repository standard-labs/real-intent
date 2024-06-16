"""Base abstract interface for validators."""
from abc import ABC, abstractmethod

from bigdbm.schemas import MD5WithPII


class BaseValidator(ABC):
    """Base validator for MD5s."""

    @abstractmethod
    def validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove MD5s that are deemed invalid by implemented criteria."""
