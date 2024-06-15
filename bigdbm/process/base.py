"""Base processor."""
from abc import ABC, abstractmethod

from bigdbm.client import BigDBMClient
from bigdbm.schemas import IABJob, MD5WithPII


class BaseProcessor(ABC):
    """
    Base processor, takes an IAB job and finishes with a list of MD5s with PII.
    All implementations must follow the `.process()` schema.

    The MD5s with PII are the input for formatters.

    Comes with an __init__ that takes a BigDBM client. If overriding the __init__
    for some reason, be sure to super() and make sure self.client is defined.
    """

    def __init__(self, bigdbm_client: BigDBMClient) -> None:
        """Initialize with a client."""
        self.client = bigdbm_client

    @abstractmethod
    def process(self, iab_job: IABJob) -> list[MD5WithPII]:
        """Take an IABJob and process it into a list of MD5s with PII."""
