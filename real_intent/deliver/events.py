"""Generate events for a given zip code."""
from pydantic import BaseModel, ValidationError
import requests

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from typing import Callable, Any
import datetime
import json
from io import BytesIO

from real_intent.internal_logging import log


# ---- Models ----

class Event(BaseModel):
    """Event object."""
    title: str
    date: str
    description: str
    link: str | None = None


class EventsResponse(BaseModel):
    """Response object, containing events and summary."""
    events: list[Event]
    summary: str


# ---- Helpers ----

def retry_generation(func: Callable):
    """Retry the generation four times if it fails validation."""
    MAX_ATTEMPTS: int = 4

    def wrapper(*args, **kwargs):
        """Run the function, catch error, then retry up to four times."""
        for attempt in range(1, MAX_ATTEMPTS+1):
            try:
                return func(*args, **kwargs)
            except (ValidationError, KeyError, json.decoder.JSONDecodeError):
                if attempt < 3:  # Log warning for first n-1 attempts
                    log("warn", f"Function {func.__name__} failed validation, attempt {attempt} of {MAX_ATTEMPTS}.")
                else:  # Log error for the last attempt
                    log("error", f"Function {func.__name__} failed validation after {MAX_ATTEMPTS} attempts.")
        
        # If we've exhausted all attempts, raise the last exception
        raise

    return wrapper


def extract_json_only(response_str: str) -> dict[str, Any]:
    """
    Parse a string response and pull out everything between the first { and last }
    then return it as a dictionary. Allows excess text before and after valid JSON
    without causing an error.
    """
    start_index = response_str.find("{")
    end_index = response_str.rfind("}")

    if start_index == -1 or end_index == -1:
        raise ValueError("No valid JSON object found in the response.")

    return json.loads(response_str[start_index:end_index+1])


class EventsGenerator:
    """
    Class for generating events for a given zip code.
    """

    def __init__(self, zip_code: str, perplexity_api_key: str) -> None:
        if not perplexity_api_key and isinstance(perplexity_api_key, str):
            raise ValueError("Perpelxity API key must be a truthy string.")

        if not zip_code and isinstance(zip_code, str) and len(zip_code) == 5 and zip_code.isnumeric():
            raise ValueError("Zip code invalid.")

        self.key = perplexity_api_key
        self.zip_code = zip_code
        self.start_date = datetime.datetime.now().strftime("%B %d, %Y")
        self.end_date = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%B %d, %Y")

    def generate_event_prompt(self) -> tuple[str, str]:
        """
        Generate the prompt for the event generation task.
        """
        system = f"""        
        You are a helpful assistant specializing in finding local events for users. You are expected to use the provided zip code 
        to determine the city or area that corresponds to it, and then search for events within that city or area. Your responses 
        should be relevant, concise, and structured in valid JSON format.  Your responses should 
        strictly adhere to the user's instructions, without additional commentary or notes. The response must be 
        structured in valid JSON format only, with no other content included. Avoid wrapping them in code blocks or adding formatting like backticks."
        """

        user = f"""
        Based on the zip code {self.zip_code}, determine the city or area that corresponds to this zip code. Then, perform a search 
        for **all local events happening within the city and surrounding areas, between {self.start_date} and {self.end_date}. Focus on events 
        such as public events, community activities, festivals, and major holidays that occur during this period.

        I am NOT providing you with source data for this task. You must find the information based on the provided zip code and date range.

        The event search should strictly include events within the city or its surrounding areas that correspond to zip code {self.zip_code}. 
        Ensure that all results are relevant to this location and within the given date range of ({self.start_date} to {self.end_date}).

        Focus on public events, community activities, festivals, and any special events happening during this time. Pay particular attention 
        to any major holidays like Christmas and New Year's Eve. If there are no major holidays, include general events that might appeal 
        to locals during this period.

        Find at least 3-5 local events that are happening in the specified zipcode and within the date range. Do NOT repeat events.

        Return the result in a JSON object with 2 keys 'events' and 'thinking':
        The key called 'events" contains a list of events. Each event should have the following keys:
            'title' - the name of the event, 
            'date' - the date of the event in ISO 8601 format (YYYY-MM-DD),
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
        You should not include any events that are not relevant to area of zip code {self.zip_code} or is not within {self.start_date} to {self.end_date}.

        Your response should be structured in valid JSON format. Do not include any additional information apart
        from the json object with the list of events. Only include events that*exactly match the provided zip code {self.zip_code}, 
        and ensure that all events are within the given date range. Do not add any other data or information apart from this structured output.

        There should be no additional information, explanations, or context provided in the response. The response should be structured in valid JSON format only. 
        Do not include any comments, notes, or additional content in the response.
        """

        return system, user

    def generate_summary_prompt(self, events: list[Event]) -> tuple[str, str]:
        """
        Generate the prompt for the summary generation task.
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
            Summarize the events happening in {self.zip_code} between {self.start_date} and {self.end_date} provided to you here.
            \n{events}\n
            Your summary should be informative and engaging, providing a brief overview of the events, the local community,
            and any other relevant details such as weather conditions. Provide a maximum of 5 sentences! 
            
            You must only include the key events and highlights from the list provided. Do not include any additional events.
            
            It should be structured in valid JSON format with one top level key called "summary" that contains a string
            summarizing the events and the local community during the specified period with a maximum of 5 sentences. 
            The summary should be a detailed paragraph that provides an overview of the expected weather conditions for the week, {self.start_date} to {self.end_date},
            and highlights the key events happening in {self.zip_code} from the list provided. Include any relevant insights about the local community, 
            such as cultural aspects, holiday-specific activities, or any notable attractions during this period.
            If there are any major holidays (e.g., Christmas, New Year's), mention how the local events and community activities reflect these.
        """

        return system, user

    def generate(self, system: str, user: str) -> dict[str, str]:
        """
        Generate a response from the Perplexity API.
        """
        log("debug", "Generating response from Perplexity API")
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
            log("error", f"Error in Perplexity API request: {str(e)}")
            raise
        except (KeyError, IndexError) as e:
            log("error", f"Error parsing Perplexity API response: {str(e)}")
            raise
    
    @retry_generation
    def generate_events(self) -> EventsResponse:
        """
        Generate events for a given zip code.
        """
        # Generate events
        system, user = self.generate_event_prompt()
        result = self.generate(system, user)
        result = extract_json_only(result)
        events = [Event(title=event['title'], date=event['date'], description=event['description'], link=event['link']) for event in result['events']]
        
        log("debug", f"Thinking process: {result['thinking']}")
        log("debug", f"Generated {len(events)} events")

        system, user = self.generate_summary_prompt(events)
        summary = self.generate(system, user)
        summary_dict: dict = extract_json_only(summary)

        # Return events and summary
        log("debug", f"Events and summary generated successfully. Events: {events}")
        return EventsResponse(events=events, summary=summary_dict['summary'])

    def generate_pdf_buffer(self, events_response: EventsResponse) -> BytesIO:
        """
        Generate a PDF file with the events and summary.
        """
        output_buffer = BytesIO()
        c = canvas.Canvas(output_buffer, pagesize=letter)
        width, height = letter

        # background color
        c.setFillColor(colors.aliceblue)
        c.rect(0, 0, width, height, fill=1)  

        title = "Upcoming Local Events"
        title_font_size = 16

        text_width = c.stringWidth(title, "Helvetica-Bold", title_font_size)
        x_position = (width - text_width) / 2  

        # Title
        c.setFillColor(colors.red)
        c.rect(0, height - 50, width, 50, fill=1) 
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", title_font_size)
        c.drawString(x_position, height - 30, title)

        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 10
        normal_style.leading = 12

        # Summary
        summary_paragraph = Paragraph(events_response.summary, normal_style)
        paragraph_width = width - 200
        summary_height = summary_paragraph.getSpaceBefore() + summary_paragraph.getSpaceAfter() + summary_paragraph.wrap(paragraph_width, 100)[1]
        summary_paragraph.drawOn(c, 100, height - 60 - summary_height)
        y_position = height - 60 - summary_height - 20

        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 10
        normal_style.leading = 12

        bottom_margin = 70

        for idx, event in enumerate(events_response.events):
            if y_position < bottom_margin:
                log("warning", f"Not all events could fit on the PDF. Truncated at event {idx+1}")
                break

            c.setFillColor(colors.red) 
            c.setFont("Helvetica-Bold", 14)
            c.drawString(100, y_position, f"{event.title}")
            y_position -= 20

            c.setFillColor(colors.green) 
            c.setFont("Helvetica", 12)
            c.drawString(100, y_position, f"Date: {event.date}")
            y_position -= 20

            paragraph = Paragraph(event.description, normal_style)
            paragraph_width = width - 200
            paragraph_height = paragraph.getSpaceBefore() + paragraph.getSpaceAfter() + paragraph.wrap(paragraph_width, 100)[1]
            paragraph.drawOn(c, 100, y_position - paragraph_height)
            y_position -= paragraph_height + 20

            c.setFont("Helvetica-Oblique", 10)
            c.setFillColor(colors.blue)
            c.drawString(100, y_position, f"Link: {event.link if event.link else 'N/A'}")
            y_position -= 20

            c.setFillColor(colors.black) 

            c.setStrokeColor(colors.gold)
            c.setLineWidth(1)
            c.line(100, y_position, width - 100, y_position)
            y_position -= 20 

        c.save()

        output_buffer.seek(0)
        return output_buffer
