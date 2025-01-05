"""Base abstraction for event generation."""
from abc import ABC, abstractmethod

from real_intent.events.models import EventsResponse
from real_intent.events.utils import generate_pdf_buffer
from real_intent.internal_logging import log, log_span


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

    def to_pdf_buffer(self, events_response: EventsResponse) -> bytes:
        """
        Convert the events and summary to a PDF buffer.
        """
        return generate_pdf_buffer(events_response)
