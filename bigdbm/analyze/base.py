"""Defines the base analyzer."""
from abc import ABC, abstractmethod

from bigdbm.schemas import MD5WithPII
from bigdbm.internal_logging import log, log_span


class BaseAnalyzer(ABC):
    """Base class for analyzers."""

    def analyze(self, pii_md5s: list[MD5WithPII]) -> str:
        """
        Take a list of MD5s with PII and perform analysis according to the purpose
        of the analyzer.

        Returns:
            str: The result of the analysis as a string.
        """
        with log_span(f"Analyzing {len(pii_md5s)} MD5s with {self.__class__.__name__}", _level="debug"):
            log("debug", f"Starting analysis with {self.__class__.__name__}")
            result = self._analyze(pii_md5s)
            log("debug", f"Analysis completed with {self.__class__.__name__}")
            return result

    @abstractmethod
    def _analyze(self, pii_md5s: list[MD5WithPII]) -> str:
        """
        Internal method to be implemented by subclasses to perform the actual analysis.
        """
        pass
    