"""An events generation implementation using the OpenAI deep research API."""
from openai import OpenAI

import json

from real_intent.internal_logging import log, log_span, instrument_openai
from real_intent.events.base import BaseEventsGenerator
from real_intent.events.models import Event, EventsResponse


# ---- Prompts ----

DEEP_RESEARCH_PROMPT: str = """
You are an expert on local events. Your job is to identify local events in {zipcode} that would be relevant to residents. These events need not be confined exactly to {zipcode}; surrounding areas are ok. 

The events you find must be within the date range of tomorrow and 14 days from now. 

Your objective is to extract event details (title, date, description, link) from the provided messages, focusing on engaging events such as networking meetups, educational opportunities, car shows, outdoor festivals, art exhibitions, and family-friendly activities. Also include need to know events like highway closures.

Keep your research process brief and limited. Wrap up your research after you have found enough valid events. Do not spend time digging too deep into minute details. Focus on getting enough events/event info to meet the requirements and fill the output schema.

Make sure your events
- are relevant to the community;
- fall within the correct timeframe (from yesterday to 14 days from now);  
- are located within or near {zipcode}
- have date attributes representing the date or date range of the event in ISO 8601 format (YYYY-MM-DD). Make sure to follow this format when providing the date.

**Important Notes:**
- Your links must be accurate. Always try to provide the direct link to the event in your final response. 
- Try to include events from a variety of the sources if possible, but above all prioritize the most relevant and engaging events for the community.
- Be concise in your titles and descriptions. Keep the descriptions limited to a couple sentences max.
            
**Exclusions:**  
Do **not** include:  
- Religious events.  
- Dating-focused events.  
- Events inappropriate for families.  
- Events outside the specified location or timeframe.  

Think from the perspective of a local resident; specifically, one with a family (adults and children). Find events that are interesting and relevant to them.

Your final answer must always be in JSON format, with this exact schema:
{json_schema}

If you are unable to find any events for any reason, stick to the schema as you always must, but with an empty list of events. With that said, you should be able to find events in almost all cases. Never respond with anything other than JSON in the exact format specified above.
"""


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
            raise ImportError("Please install this package with the 'ai' extra.")

        self.openai_client: OpenAI = OpenAI(api_key=openai_api_key)
        instrument_openai(self.openai_client)

    def _generate(self, zip_code: str) -> EventsResponse:
        """Use the OpenAI deep research API to generate events."""
        if not isinstance(zip_code, str) or not zip_code.isnumeric() or len(zip_code) != 5:
            raise ValueError("Invalid ZIP code. ZIP code must be a 5-digit numeric string.")

        with log_span(f"Generating events in {zip_code} with deep research", _level="debug"):
            response = self.openai_client.responses.create(
                model="o4-mini-deep-research",
                input=DEEP_RESEARCH_PROMPT.format(
                    zipcode=zip_code,
                    json_schema=EventsResponse.model_json_schema()
                ),
                text={"format": {"type": "json_object"}},
                tools=[{"type": "web_search_preview"}]
            )

        return EventsResponse(**json.loads(response.output_text))
