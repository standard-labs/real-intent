"""Defines the base output deliverer, i.e. interface for ."""
from abc import ABC, abstractmethod
from typing import Any

from bigdbm.schemas import MD5WithPII


class BaseOutputDeliverer(ABC):
    """Base class for output deliverers."""

    @abstractmethod
    def deliver(self, pii_md5s: list[MD5WithPII]) -> Any:
        """
        Take a list of MD5s with PII and do whatever with it according to the purpose 
        of the delivery mechanism.
        """
