import datetime
import json
from typing import List
from pydantic import BaseModel
import datetime
from pydantic import BaseModel, ValidationError
import requests
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

class Event(BaseModel):
    title: str
    date: str
    description: str
    link: str

class EventsResponse(BaseModel):
    events: List[Event]
    summary: str

class EventsGenerator():

    def __init__(self, api_key: str, zip_code: str) -> None:
        
        self.key = api_key
        self.zip_code = zip_code
        self.start_date = datetime.datetime.now().strftime("%B %d, %Y")
        self.end_date = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%B %d, %Y")


    def generate_event_prompt(self) -> tuple[str, str]:

        system = f"""
                    You are a helpful assistant specializing in finding local events for users. You provide accurate, concise, 
                    and relevant event information based on the user's provided location and date range. Your responses are 
                    structured in valid JSON format, adhering strictly to the user's instructions.
                """

        user = f"""
                    Search for local events in {self.zip_code} between {self.start_date} and {self.end_date}. 
                    Focus on public events, community activities, festivals, and any special events happening 
                    during this time. Pay particular attention to any major holidays like Christmas and New Year's Eve,
                    but if there are no major holidays, feel free to include general events that might appeal to
                    locals during this period.

                    Find at least 3-5 unique local events that are happening in the specified zipcode and within the date range.

                    Return the result in a JSON object with one top level key called "events" that contains a list 
                    of events. Each event should have the following keys:
                        'title' - the name of the event, 
                        'date' - the date of the event in ISO 8601 format (YYYY-MM-DD),
                        'description' - a description of the event with relevant details and at least 2-3 sentences. Provide
                        information about the type of event, any special guests, or activities, and why it's significant to the community.
                        'link' - a URL to the event page or more information.
                    
                    Ensure that the events are all local to the specified zipcode and within the date range. These events
                    should help a real estate agent gain a better understand of the local community. 
                    You should not include any events that are not relevant to zip code {self.zip_code} or is not within {self.start_date} to {self.end_date}.

                    Your response should be structured in valid JSON format. Do not include any additional information apart
                    from the json object with the list of events.

        """

        return system, user
    

    def generate_summary_prompt(self, events) -> tuple[str, str]:
        
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


    def generate_insight(self, system, user):
        url = "https://api.perplexity.ai/chat/completions"

        payload = {
        "model": "llama-3.1-sonar-small-128k-online",
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
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.key}"
        }

        response = requests.request("POST", url, json=payload, headers=headers)

        return response.json()
    

    def generate_events(self) -> EventsResponse | None:
        try:
            system, user = self.generate_event_prompt()
            result = self.generate_insight(system, user)['choices'][0]['message']['content']
            result = result.replace("`", "").replace("json", "")
            result = json.loads(result)
            events = [Event(title=event['title'], date=event['date'], description=event['description'], link=event['link']) for event in result['events']]
            system, user = self.generate_summary_prompt(result)
            summary = self.generate_insight(system, user)['choices'][0]['message']['content']
            summary = summary.replace("`", "").replace("json", "").replace("\n", "")
            summary = json.loads(summary)
            return EventsResponse(events=events, summary=summary['summary'])
        except (ValidationError) as e:
            return e.errors()


    def generate_pdf(self, events_response: EventsResponse, filename: str):
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 40, "Upcoming Local Events")

        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 10
        normal_style.leading = 12  

        summary_paragraph = Paragraph(events_response.summary, normal_style)
        paragraph_width = width - 200  
        summary_height = summary_paragraph.getSpaceBefore() + summary_paragraph.getSpaceAfter() + summary_paragraph.wrap(paragraph_width, 100)[1]
        summary_paragraph.drawOn(c, 100, height - 60 - summary_height)  
        y_position = height - 60 - summary_height - 20  

 
        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 10
        normal_style.leading = 12 

        bottom_margin = 50  

        for idx, event in enumerate(events_response.events):

            if y_position < bottom_margin:
                break

            c.setFont("Helvetica-Bold", 14)
            c.drawString(100, y_position, f"Event: {event.title}")
            y_position -= 20

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
            c.drawString(100, y_position, f"More Info: {event.link}")
            y_position -= 20  

            c.setFillColor(colors.black)
        c.save()


# Example Usage ****************************************************************************************
event_generator = EventsGenerator("PERPLEXITY_KEY", "11801")
events_response = event_generator.generate_events()
event_generator.generate_pdf(events_response, "events.pdf")