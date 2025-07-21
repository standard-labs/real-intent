"""Use Perplexity as the initial web researcher, then triage and compile with GPT-4o."""
import requests

import json

from real_intent.internal_logging import log, log_span
from real_intent.events.models import Event, EventsResponse
from real_intent.events.base import BaseEventsGenerator
from real_intent.events.deep_research.prompts import DEEP_RESEARCHER_PROMPT, TRIAGER_PROMPT


class PerplexityOpenAIEventsGenerator(BaseEventsGenerator):
    """
    Generate events by using a Perplexity-based deep researcher,
    then triaging and compiling with GPT-4o + structured outputs.
    """

    def __init__(self, perplexity_api_key: str, openai_api_key: str):
        self.perplexity_api_key: str = perplexity_api_key

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Needs openai. Please install this package with the [ai] extension.")
            
        self.openai_client = OpenAI(api_key=openai_api_key)

    def _perplexity_deep_research(self, zipcode: str) -> dict:
        """Deep research the zipcode and find a raw response of content."""
        with log_span(f"Deep researching {zipcode} events with Perplexity", _level="trace"):
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.perplexity_api_key}"
                },
                json={
                    "model": "sonar-deep-research",
                    "messages": [
                        {
                            "role": "user",
                            "content": DEEP_RESEARCHER_PROMPT.format(
                                zipcode=zipcode,
                                json_schema=EventsResponse.model_json_schema()
                            )
                        }
                    ],
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {"schema": EventsResponse.model_json_schema()}
                    }
                }
            )

            if not response.ok:
                log("error", f"Error deep researching {zipcode} with Perplexity: {response.text}")
                response.raise_for_status()
                return

        return response.json()
