"""Common error classes for event generation."""


class NoValidJSONError(ValueError):
    """Exception raised when no valid JSON is found in the response."""

    def __init__(self, content: str):
        super().__init__(content)


class NoEventsFoundError(Exception):
    """Exception raised when no events are found for a zip code."""

    def __init__(self, zip_code: str):
        super().__init__(f"No events found for zip code {zip_code}")
