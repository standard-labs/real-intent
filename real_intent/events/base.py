"""Base abstraction for event generation."""
from pydantic import BaseModel, Field

from abc import ABC, abstractmethod

from real_intent.schemas import MD5WithPII
from real_intent.internal_logging import log, log_span


# ---- Models ----

class Event(BaseModel):
    """Event object."""
    title: str
    date: str
    description: str
    link: str | None = None
    
    @property
    def truncated_title(self) -> str:
        """Truncate the title to a maximum length."""
        if len(self.title) > 70:
            return self.title[:70] + "..."

        return self.title


class EventsResponse(BaseModel):
    """Response object, containing events and summary."""
    events: list[Event]
    summary: str


# ---- Abstraction ----

class BaseEventsGenerator(ABC):
    """Base class for event generators, by zipcode."""

    def generate(self, zip_code: str) -> EventsResponse:
        """
        Take a zipcode and generate events.

        Returns:
            EventsResponse: The generated events and summary.
        """
        with log_span(f"Generating events in {zip_code} with {self.__class__.__name__}", _level="debug"):
            log("debug", f"Starting event generation with {self.__class__.__name__}")
            result = self._generate(zip_code)
            log("debug", f"Event generation completed with {self.__class__.__name__}")
            return result

    @abstractmethod
    def _generate(self, zip_code: str) -> EventsResponse:
        """
        Internal method to be implemented by subclasses to perform the actual
        event generation.
        """
        pass
    