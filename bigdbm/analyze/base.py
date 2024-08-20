"""Defines the base analyzer."""
from abc import ABC, abstractmethod

from bigdbm.schemas import MD5WithPII


class BaseAnalyzer(ABC):
    """Base class for analyzers."""

    @abstractmethod
    def analyze(self, pii_md5s: list[MD5WithPII]) -> str:
        """
        Take a list of MD5s with PII and perform analysis according to the purpose
        of the analyzer.

        Returns:
            str: The result of the analysis as a string.
        """
        