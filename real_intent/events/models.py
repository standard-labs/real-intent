"""Event models."""
from pydantic import BaseModel


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
