"""Implementation of event generation using olostep api."""

import json
import requests
import datetime as dt
import time
import random

from typing import List, Dict
from pydantic import BaseModel

from anthropic import Anthropic, APIStatusError

from real_intent.events.base import BaseEventsGenerator
from real_intent.events.errors import NoValidJSONError
from real_intent.events.scrapy_claude import extract_json_array
from real_intent.internal_logging import log
from real_intent.events.models import Event, EventsResponse
from real_intent.events.utils import extract_json_only


# --- Begin Models & Utils ---

def validate_json_content(v):
    log("trace", f"Validating json_content: {v}")
    if v is None:
        raise NoValidJSONError("json_content is None")
    if isinstance(v, str):
        return json.loads(v)
    return v

class OrganicLink(BaseModel):
    title: str | None = None
    link: str | None = None
    snippet: str | None = None


# --- End Models & Utils ---

class SerpEventsGenerator(BaseEventsGenerator):
    """Implementation of event generation using serp through olostep API"""

    def __init__(
        self, 
        serp_key: str,
        anthropic_key: str,
        start_date: dt.datetime | None = None,
        end_date: dt.datetime | None = None,
        geo_key: str | None = None,
    ):
        """
        Initialize the EventsGenerator.

        Args:
            serp_key: API key for olostep serp API,
            anthropic_key: API key for anthropic API
            start_date: Optional start date for event search, defaults to today
            end_date: Optional end date for event search, defaults to 14 days from start
            geo_key: Optional API key for geolocation service (e.g., zipcode lookup)

        """
        if not isinstance(serp_key, str) or not serp_key:
            raise ValueError("serp API key must be a truthy string.")

        if not isinstance(anthropic_key, str) or not anthropic_key:
            raise ValueError("anthropic API key must be a truthy string.")
        
        self.serp_key = serp_key
        self.geo_key = geo_key

        self.anthropic_client = Anthropic(api_key=anthropic_key)

        # Set dates with defaults if not provided
        start = start_date or dt.datetime.now()
        end = end_date or (start + dt.timedelta(days=14))
        
        # Validate inputs are datetime objects
        if not isinstance(start, dt.datetime) or not isinstance(end, dt.datetime):
            raise ValueError("Invalid start or end date inputs.")
        
        # Convert to formatted strings for internal use
        self.start_date = start.strftime("%B %d, %Y")
        self.end_date = end.strftime("%B %d, %Y")


    def get_city_state(self, zip_code: str) -> str | None:
        """
        Get the city and state for a given zip code.

        Args:
            zip_code (str): The zip code to look up.

        Returns:
            tuple[str, str]: A tuple containing the city and state.
        """
        if not self.geo_key:
            return None

        endpoint = f"https://api.api-ninjas.com/v1/zipcode?zip={zip_code}"
        headers = {
            "X-Api-Key": self.geo_key, 
        }
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()

        data = response.json()

        if not data or not isinstance(data, list) or len(data) == 0:
            return None

        data = data[0]
        
        city_state = ""

        if not data:
            return None
        if data.get("city", None):
            city_state += f"{data.get("city")}, "
        if data.get("state", None):
            city_state += f"{data.get("state")}, "
        if data.get("county", None):
            city_state += f"{data.get("county")}"

        return city_state


    def _request(self, endpoint: str, method: str = "GET", payload: dict = None):
        """Make a request to the specified URL with the given method and payload."""

        log("trace", f"Making {method} request to {endpoint} with payload: {payload}")

        headers = {
            "Authorization": f"Bearer {self.serp_key}",
            "Content-Type": "application/json"
        }
        if method == "GET":
            response = requests.get(f"https://api.olostep.com/v1{endpoint}", headers=headers)
        else:
            response = requests.post(f"https://api.olostep.com/v1{endpoint}", json=payload, headers=headers)
        
        response.raise_for_status()

        log("trace", f"Response status for {method} request to {endpoint}: {response.status_code}")
        
        return response.json()


    def poll_batch_status(self, batch_id: str, max_retries: int = 5, initial_wait_time: int = 10, max_wait_time: int = 6):
        """
        Polls the batch status until it is completed with exponential backoff.

        Args:
            batch_id (str): The batch ID to check.
            max_retries (int): Maximum number of retries before raising an error.
            initial_wait_time (int): Initial wait time (in seconds) before polling again.
            max_wait_time (int): Maximum wait time (in seconds) between polls.

        Returns:
            dict: The final batch status if successful.

        Raises:
            Exception: If the polling fails after the maximum retries.
        """
        wait_time = initial_wait_time
        retries = 0

        while retries < max_retries:
            try:
                # Poll the batch status
                status_response = self._request(f"/batches/{batch_id}", "GET")

                # Check if the batch status is completed
                if status_response.get("status") == "completed":
                    log("trace", "Batch completed successfully.")
                    return
                
                log("trace", f"Batch {batch_id} status: {status_response.get('status')}. Retrying...")
            except Exception as e:
                log("error", f"Error while polling: {e}")

            wait_time = min(wait_time * 2, max_wait_time)
            wait_time += random.randint(1, 5)  
            retries += 1

            log("trace", f"Waiting for {wait_time} seconds before retrying...")
            time.sleep(wait_time)

        # If max retries exceeded
        raise Exception(f"Polling failed after {max_retries} attempts. Batch status not completed.")


    def extract_links(self, query: str) -> List[OrganicLink]:
        """Extract organic links from Google search results for the given query."""

        payload = {
            "formats": ["parser_extract"],
            "parser_extract": {
                "parser_id": "@olostep/google-search"
            },
            "screen_size": "desktop",
            "url_to_scrape": f"https://www.google.com/search?q={query}&gl=us&hl=en",
            "wait_before_scraping": 0
        }

        serp_response = self._request("/scrapes", method="POST", payload=payload)

        parsed_json_content = validate_json_content(serp_response['result']['json_content'])

        organic_links = [
            OrganicLink(**item) for item in parsed_json_content.get('organic', [])
        ]

        log("trace", f"Links Extracted: {organic_links}")

        filtered_domains = ["facebook.com", "wikipedia.org"]

        filtered_links = [
            link for link in organic_links if link.link and not any(domain in link.link for domain in filtered_domains)
        ]

        return filtered_links


    def start_batch(self, organic_links: List[OrganicLink]) -> Dict[str, str]:
        """
            start batch processing for the given organic links and return a mapping of custom_id to retrieve_id.
        """

        payload = {
            "items": [],
            "country": "US",
            "formats": ["parser_extract"],
            "parser_extract": {
                "parser_id": "@olostep/google-search"
            }
        }

        # form payload for batch request
        for i, link in enumerate(organic_links):
            if link.link:
                payload["items"].append({
                    "custom_id": str(i),
                    "url": link.link
                })
                
        serp_response = self._request("/batches", "POST", payload)

        batch_id = serp_response.get("id", None)
        if not batch_id:
            raise Exception("No valid batch ID found in the response.")

        log("trace", f"Started Batch ID: {batch_id}")

        self.poll_batch_status(batch_id)

        # if no exception was raised, the batch is completed
        log("trace", f"Batch {batch_id} completed.")

        serp_response = self._request(f"/batches/{batch_id}/items", "GET")

        id_mapping = {item['custom_id']: item['retrieve_id'] for item in serp_response['items']}

        log("trace", f"Items response: {id_mapping}")

        return id_mapping


    def get_events(self, organic_links: List[OrganicLink], id_mapping: Dict[str, str], zip_code: str, city_state: str | None = None) -> str | None:

        def _get_content(retrieve_id: str) -> Dict[str, str]:
            """get the content for a given link position and retrieve id"""

            serp_response = self._request(f"/retrieve?retrieve_id={retrieve_id}&formats=markdown", "GET")

            markdown_content = serp_response.get("markdown_content", None)
            if not markdown_content:
                raise Exception(f"No valid markdown_content for retrieve_id: {retrieve_id}")
                                    
            return markdown_content

        prompt = (
                f"You are a helpful events aggregator expert. You will be given multiple messages containing a link, the link's title, and the link's content for an events page for zipcode {zip_code}. These links will be related to community events in the zipcode {zip_code}. "
                f"Your job is to parse through all of them, extract community events in the zipcode {zip_code} {city_state if city_state else ""}, and validate them to ensure they are relevant to the community and fall within the correct zipcode of {zip_code} and timeframe of {self.start_date} to {self.end_date}. "
                f"The events given are NOT guaranteed to be relevant or appropriate for the community, so you must validate them nor are they guaranteed to be in {zip_code} {city_state if city_state else ""} or within {self.start_date} to {self.end_date}. "
                "Your task is to prioritize fun, engaging events such as networking events, educational opportunities, car shows, outdoor festivals, art exhibitions, and family-friendly activities. "
                "Please avoid religious events, dating events (including speed dating), or events that are not appropriate for the general community. You must go through EVERY message provided."
                "For each event, extract the title, date, description, and link (which is given to you already)."
                "Maintain a list of as many events that fit the criteria as possible, but your final response should be a JSON list of the top 5 most relevant events, with the events you are the most confident about adhering to this prompt"
                f"The events should match the given zipcode {zip_code} {city_state if city_state else ""} and timeframe of {self.start_date} to {self.end_date}. "
                "If you are not sure about an event's link, BUT it meets the criteria, please just include the link of the source page which was provided to you initially with the content where you extracted the event from. "
                "If you cannot find any events, return an empty JSON list. If you find less than 5, return only the events you found, but ensure you return at least 3 events. "
                "If you find any events that are not relevant to the community or are outside the specified zipcode or timeframe, ignore them."
                "Before returning the results, ensure no event is part of the invalid events list, which includes religious events, dating events, or any other events that do not fit the criteria. "
                "You must also ensure that the events are not duplicated, so if you find any duplicates, remove them from the final list. "
                f"Ensure that each event is appropriate for the community and aligns with the specified criteria. You must NOT include any event that isn't within the zipcode {zip_code} {city_state if city_state else ""} or the specified timeframe {self.start_date} to {self.end_date}. "
                f"Return the results in the following format: {json.dumps(Event.model_json_schema())}, where one of these objects represents a single event. "
        )

        messages = [
            {"role": "assistant", "content": prompt}
        ]

        for i, link in enumerate(organic_links):
            retrieve_id = id_mapping.get(str(i))
            if retrieve_id:
                content = _get_content(retrieve_id)
                if content:
                    data = {
                        "title": link.title,
                        "link": link.link,
                        "content": content
                    }
                    messages.append({
                        "role": "user",
                        "content": json.dumps(data)  
                    })
        
        log("trace", "Sending messages to Anthropic for processing.")
        
        message = self.anthropic_client.messages.create(
            model="claude-3-7-sonnet-20250219",
            messages=messages,
            temperature=1,
            max_tokens=4000,
            thinking={
                "type": "enabled",
                "budget_tokens": 2000            
            },

        )

        log("trace", f"Anthropic response FULL: {message}")

        content = message.content  
        if content:
            for block in content:
                if block.type == "text":
                    event_text = block.text
                    log("trace", f"Anthropic response: {event_text}")
                    return event_text
            log("error", "No text block found in Anthropic response.")
            raise Exception("No text block found in Anthropic response.")
        
        else:
            log("error", "No content returned from Anthropic.")
            raise Exception("No content returned from Anthropic.")
        

    def summary_prompt(self, events: list[Event], zip_code: str, city_state: str | None = None) -> tuple[str, str]:
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
            Summarize the events happening in {zip_code} {city_state if city_state else ""} between {self.start_date} and {self.end_date} provided to you here.
            \n{events}\n
            Your summary should be informative and engaging, providing a brief overview of the events, the local community,
            and any other relevant details such as weather conditions. Provide a maximum of 5 sentences! 
            
            You must only include the key events and highlights from the list provided. Do not include any additional events.
            
            It should be structured in valid JSON format with one top level key called "summary" that contains a string
            summarizing the events and the local community during the specified period with a maximum of 5 sentences. 
            The summary should be a detailed paragraph that provides an overview of the expected weather conditions for the week, {self.start_date} to {self.end_date},
            and highlights the key events happening in {zip_code} {city_state if city_state else ""} from the list provided. Include any relevant insights about the local community, 
            such as cultural aspects, holiday-specific activities, or any notable attractions during this period.
            If there are any major holidays (e.g., Christmas, New Year's), mention how the local events and community activities reflect these.
        """

        return system, user


    def generate_summary(self, events: list[Event], zip_code: str, city_state: str | None = None) -> str:
        """Generate a summary of the events."""
        system, user = self.summary_prompt(events=events, zip_code=zip_code, city_state=city_state)        
        log("trace", "Generating summary with Anthropic.")

        try:
            response = self.anthropic_client.completions.create(
            model="claude-2.1",  
            prompt=system + "\n\nHuman:" + user + "\n\nAssistant:", 
            max_tokens_to_sample=500,
            temperature=0.5,
        )

            
            return response.completion
        except APIStatusError as e:
            log("error", f"APIStatusError generating summary with Anthropic: {e}")
            raise

        
    def _generate_events(self, zip_code: str) -> EventsResponse:

        city_state = self.get_city_state(zip_code)  # Ensure we have the city and state for the zip code
        log("trace", f"City and state for zip code {zip_code}: {city_state}")

        # test out not specifying a date range
        links: List[OrganicLink] = self.extract_links(f"Events in {zip_code} {city_state if city_state else ""}")
   
        id_mappings = self.start_batch(links)
        response = self.get_events(links, id_mappings, zip_code, city_state)

        response = extract_json_array(response)
        events = [Event(title=event['title'], date=event['date'], description=event['description'], link=event['link']) for event in response]
        if not events:
            log("error", f"No events generated for {zip_code}.")
            raise Exception(f"No events found for {zip_code} between {self.start_date} and {self.end_date}.")
        
        log("debug", f"Generated {len(events)} for {zip_code} between {self.start_date} and {self.end_date}")

        summary = self.generate_summary(events, zip_code, city_state)
        summary_dict = extract_json_only(summary)
        
        log("debug", f"Events and summary generated successfully. Events: {events}, Summary: {summary_dict['summary']}")
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


"""
    Notes
    -------
    definety high token usage, could cut out searching 12-13 links to 5-6 

    thinking extends the time for processign (by a significant amount too), so also keep that in mind

    overall, the olostep api is pretty cheap relatively. it's probably the tokens which will cost us

"""