"""Event models."""
from pydantic import BaseModel, Field

import string


class Event(BaseModel):
    """Event object."""
    title: str = Field(..., description="The title of the event.")
    date: str = Field(..., description="The date of the event in ISO 8601 format (YYYY-MM-DD).")
    description: str = Field(..., description="A description of the event. This should be a couple sentences max.")
    link: str | None = Field(None, description="A link to the event. This should be the direct link to the event if possible.")
    
    @property
    def truncated_title(self) -> str:
        """Truncate the title to a maximum length."""
        if len(self.title) > 70:
            return string.capwords(self.title[:70] + "...")

        return string.capwords(self.title)


class EventsResponse(BaseModel):
    """Response object, containing events and summary."""
    events: list[Event]
    summary: str = Field(..., description="A summary of all events. A brief paragraph.")
    
    
class OrganicLink(BaseModel):
    """Model for organic links."""
    title: str | None = None
    link: str | None = None
    snippet: str | None = None
