"""Implementation of event generation using Perplexity."""
import requests
import datetime as dt

from real_intent.events.base import Event, EventsResponse, BaseEventsGenerator
from real_intent.events.errors import NoValidJSONError, NoEventsFoundError
from real_intent.events.utils import extract_json_only, retry_generation
from real_intent.internal_logging import log


# ---- Implementation ----

class PerplexityEventsGenerator(BaseEventsGenerator):
    """Implementation of event generation using Perplexity."""

    def __init__(
        self, 
        perplexity_api_key: str,
        start_date: dt.datetime | None = None,
        end_date: dt.datetime | None = None
    ):
        """
        Initialize the EventsGenerator.

        Args:
            perplexity_api_key: API key for Perplexity
            start_date: Optional start date for event search, defaults to today
            end_date: Optional end date for event search, defaults to 14 days from start
        """
        if not isinstance(perplexity_api_key, str) or not perplexity_api_key:
            raise ValueError("Perplexity API key must be a truthy string.")

        self.key = perplexity_api_key

        # Set dates with defaults if not provided
        start = start_date or dt.datetime.now()
        end = end_date or (start + dt.timedelta(days=14))
        
        # Validate inputs are datetime objects
        if not isinstance(start, dt.datetime) or not isinstance(end, dt.datetime):
            raise ValueError("Invalid start or end date inputs.")
        
        # Convert to formatted strings for internal use
        self.start_date = start.strftime("%B %d, %Y")
        self.end_date = end.strftime("%B %d, %Y")

    def generate_event_prompt(self, zip_code: str) -> tuple[str, str]:
        """
        Generate the prompt for event generation.
        
        Args:
            zip_code: The zip code to generate events for.
            
        Returns:
            A tuple of (system prompt, user prompt).
        """
        system = f"""        
        You are a helpful assistant specializing in finding local events for users. You are expected to use the provided zip code 
        to determine the city or area that corresponds to it, and then search for events within that city or area. Your responses 
        should be relevant, concise, and structured in valid JSON format. Your responses should 
        strictly adhere to the user's instructions, without additional commentary or notes. The response must be 
        structured in valid JSON format only, with no other content included. Avoid wrapping them in code blocks or adding formatting like backticks."
        """

        user = f"""
        Based on the zip code {zip_code}, determine the city or area that corresponds to this zip code. Then, perform a search 
        for **all local events happening within the city and surrounding areas, between {self.start_date} and {self.end_date}. Focus on events 
        such as public events, community activities, festivals, and major holidays that occur during this period.

        I am NOT providing you with source data for this task. You must find the information based on the provided zip code and date range.

        The event search should strictly include events within the city or its surrounding areas that correspond to zip code {zip_code}. 
        Ensure that all results are relevant to this location and within the given date range of ({self.start_date} to {self.end_date}).

        Focus on public events, community activities, festivals, and any special events happening during this time. Pay particular attention 
        to any major holidays like Christmas and New Year's Eve. If there are no major holidays, include general events that might appeal 
        to locals during this period.

        Find at least 3-5 local events that are happening in the specified zipcode and within the date range. Do NOT repeat events.

        Return the result in a JSON object with 2 keys 'events' and 'thinking':
        The key called 'events" contains a list of events. Each event should have the following keys:
            'title' - the name of the event, 
            'date' - the date of the event in ISO 8601 format (YYYY-MM-DD). The date MUST be between today ({self.start_date}) and {self.end_date}. Do not return dates outside this range.
            'description' - a description of the event with relevant details and at least 2-3 sentences. Provide
            information about the type of event, any special guests, or activities, and why it's significant to the community.
            'link' - a URL to the event page or more information. You should list where you found the event information in here.
        
        If there are no events found, return an empty list under the "events" key. Do not add any extra notes, 
        explanations, or surrounding context.

        The second key should be called 'thinking' which is a string. 
            This key should briefly describe the logic or checks you performed to ensure that the events are 
            relevant, within the specified zip code, and fall within the given date range. Keep this explanation 
            short and relevant to the task. Refer back to the thinking key to ensure that you have followed the correct specifications.


        Ensure that the events are all local to the specified zipcode and within the date range. These events
        should help a real estate agent gain a better understand of the local community. 
        You should not include any events that are not relevant to area of zip code {zip_code} or is not within {self.start_date} to {self.end_date}.

        Your response should be structured in valid JSON format. Do not include any additional information apart
        from the JSON object with the list of events. Only include events that *exactly* match the provided zip code {zip_code}, 
        and ensure that all events are within the given date range. Do not add any other data or information apart from this structured output.

        There should be no additional information, explanations, or context provided in the response. The response should be structured in valid JSON format only. 
        Do not include any comments, notes, or additional content in the response.
        """

        return system, user

    def generate_summary_prompt(self, events: list[Event], zip_code: str) -> tuple[str, str]:
        """
        Generate the prompt for summary generation.
        
        Args:
            events: List of events to summarize.
            zip_code: The zip code the events are for.
            
        Returns:
            A tuple of (system prompt, user prompt).
        """
        system = f"""
            You will be helping the user generate a comprehensive summary of a specific zipcode, including details about 
            local events and general conditions. You will be given a list of events happening in the specified zipcode 
            and date range. Your task is to summarize the events in a concise and informative manner, highlighting the 
            key details and providing a general overview of the local community during that period. The summary should also include 
            weather conditions and any other relevant local insights. Your response should be structured in valid JSON format, 
            adhering strictly to the user's instructions.
            """

        user = f"""
            Summarize the events happening in {zip_code} between {self.start_date} and {self.end_date} provided to you here.
            \n{events}\n
            Your summary should be informative and engaging, providing a brief overview of the events, the local community,
            and any other relevant details such as weather conditions. Provide a maximum of 5 sentences! 
            
            You must only include the key events and highlights from the list provided. Do not include any additional events.
            
            It should be structured in valid JSON format with one top level key called "summary" that contains a string
            summarizing the events and the local community during the specified period with a maximum of 5 sentences. 
            The summary should be a detailed paragraph that provides an overview of the expected weather conditions for the week, {self.start_date} to {self.end_date},
            and highlights the key events happening in {zip_code} from the list provided. Include any relevant insights about the local community, 
            such as cultural aspects, holiday-specific activities, or any notable attractions during this period.
            If there are any major holidays (e.g., Christmas, New Year's), mention how the local events and community activities reflect these.
        """

        return system, user

    def call_perplexity_api(self, system: str, user: str) -> dict[str, str]:
        """
        Call the Perplexity API with the given prompts.
        
        Args:
            system: The system prompt.
            user: The user prompt.
            
        Returns:
            The API response content.
            
        Raises:
            requests.exceptions.RequestException: If the API request fails.
            KeyError, IndexError: If the API response is malformed.
        """
        url = "https://api.perplexity.ai/chat/completions"

        payload = {
            "model": "llama-3.1-sonar-large-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": system
                },
                {
                    "role": "user",
                    "content": user
                }
            ],
            "temperature": 0.3,
            "presence_penalty": 0.5,
            "return_images": False,
            "return_related_questions": False,
            "stream": False,
            "search_recency_filter": "month",
            "top_k": 0
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.key}"
        }

        try:
            response = requests.request("POST", url, json=payload, headers=headers)
            response.raise_for_status()
            response_json = response.json()
            log("debug", f"Received good response from Perplexity: {response_json}")
            return response_json['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            log("error", f"Error in Perplexity API request: {str(e)}", exc_info=e)
            raise
        except (KeyError, IndexError) as e:
            log("error", f"Error parsing Perplexity API response: {str(e)}", exc_info=e)
            raise
    
    @retry_generation
    def _generate_events(self, zip_code: str) -> EventsResponse:
        """
        Generate a list of events for the specified ZIP code and date range.
        """
        # Generate events
        system, user = self.generate_event_prompt(zip_code)
        result = self.call_perplexity_api(system, user)
        result = extract_json_only(result)
        events = [Event(title=event['title'], date=event['date'], description=event['description'], link=event['link']) for event in result['events']]
        
        log("debug", f"Thinking process: {result['thinking']}")
        log("debug", f"Generated {len(events)} events")

        # Make sure we have events
        if not events:
            raise NoEventsFoundError(zip_code)

        system, user = self.generate_summary_prompt(events, zip_code)
        summary = self.call_perplexity_api(system, user)
        summary_dict: dict = extract_json_only(summary)

        # Return events and summary
        log("debug", f"Events and summary generated successfully. Events: {events}")
        return EventsResponse(events=events, summary=summary_dict['summary'])

    def _generate(self, zip_code: str) -> EventsResponse:
        """
        Internal method to generate events for a given zip code.
        
        Args:
            zip_code: The zip code to generate events for.
            
        Returns:
            EventsResponse: The generated events and summary.
        """
        if not isinstance(zip_code, str) or not zip_code.isnumeric() or len(zip_code) != 5:
            raise ValueError("Invalid ZIP code. ZIP code must be a 5-digit numeric string.")

        return self._generate_events(zip_code)
