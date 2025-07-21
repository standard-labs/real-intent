"""An events generation implementation using the OpenAI deep research API."""
import json

from real_intent.internal_logging import log, instrument_openai
from real_intent.events.base import BaseEventsGenerator
from real_intent.events.models import EventsResponse
from real_intent.events.deep_research.prompts import DEEP_RESEARCHER_PROMPT


# ---- Implementation ----

class DeepResearchEventsGenerator(BaseEventsGenerator):
    """An events generation implementation using the OpenAI deep research API."""

    def __init__(self, openai_api_key: str):
        """
        Initialize the DeepResearchEventsGenerator.

        Args:
            openai_api_key: The API key for OpenAI.

        Raises:
            ImportError: If the OpenAI package is not installed.
            ValueError: If the API key is invalid.
        """
        if not isinstance(openai_api_key, str) or not openai_api_key:
            raise ValueError("OpenAI API key must be a truthy string.")

        try:
            from openai import OpenAI
        except ImportError:
            log("error", "Failed to import OpenAI. Make sure to install the package with the 'ai' extra.")
            raise ImportError("Please install this package with the 'ai' extra.") from None

        self.openai_client: OpenAI = OpenAI(api_key=openai_api_key)
        instrument_openai(self.openai_client)

    def _generate(self, zip_code: str) -> EventsResponse:
        """Use the OpenAI deep research API to generate events."""
        if not isinstance(zip_code, str) or not zip_code.isnumeric() or len(zip_code) != 5:
            raise ValueError("Invalid ZIP code. ZIP code must be a 5-digit numeric string.")

        response = self.openai_client.responses.create(
            model="o4-mini-deep-research",
            input=DEEP_RESEARCHER_PROMPT.format(
                zipcode=zip_code,
                json_schema=EventsResponse.model_json_schema()
            ),
            text={"format": {"type": "json_object"}},
            tools=[{"type": "web_search_preview"}]
        )

        return EventsResponse(**json.loads(response.output_text))
