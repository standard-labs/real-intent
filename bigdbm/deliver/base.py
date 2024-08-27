"""Defines the base output deliverer, i.e. interface for ."""
from abc import ABC, abstractmethod
from typing import Any

from bigdbm.schemas import MD5WithPII
from bigdbm.internal_logging import log, log_span


class BaseOutputDeliverer(ABC):
    """Base class for output deliverers."""

    def deliver(self, pii_md5s: list[MD5WithPII]) -> Any:
        """
        Take a list of MD5s with PII and do whatever with it according to the purpose 
        of the delivery mechanism.
        """
        with log_span(f"Delivering {len(pii_md5s)} leads with {self.__class__.__name__}", _level="debug"):
            log("debug", f"Starting delivery process with {self.__class__.__name__}")
            result = self._deliver(pii_md5s)
            log("debug", f"Delivery completed with {self.__class__.__name__}")
            return result

    @abstractmethod
    def _deliver(self, pii_md5s: list[MD5WithPII]) -> Any:
        """
        Internal method to be implemented by subclasses to perform the actual delivery.
        """
        pass
