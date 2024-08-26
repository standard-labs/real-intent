"""Deliverer for FollowUpBoss CRM."""
import requests

from enum import StrEnum
import base64

from bigdbm.deliver.base import BaseOutputDeliverer
from bigdbm.schemas import MD5WithPII


class EventType(StrEnum):
    """Event types for adding a lead."""
    REGISTRATION = "Registration"
    INQUIRY = "Inquiry"
    SELLER_INQUIRY = "Seller Inquiry"
    PROPERTY_INQUIRY = "Property Inquiry"
    GENERAL_INQUIRY = "General Inquiry"
    VIEWED_PROPERTY = "Viewed Property"
    SAVED_PROPERTY = "Saved Property"
    VISITED_WEBSITE = "Visited Website"
    INCOMING_CALL = "Incoming Call"
    UNSUBSCRIBED = "Unsubscribed"
    PROPERTY_SEARCH = "Property Search"
    SAVED_PROPERTY_SEARCH = "Saved Property Search"
    VISITED_OPEN_HOUSE = "Visited Open House"
    VIEWED_PAGE = "Viewed Page"


class FollowUpBossDeliverer(BaseOutputDeliverer):
    """Delivers data to FollowUpBoss CRM."""
    def __init__(
            self, 
            api_key: str, 
            system: str, 
            system_key: str, 
            base_url: str = "https://api.followupboss.com/v1",
            event_type: EventType = EventType.REGISTRATION
        ):
        self.api_key: str = api_key
        self.base_url: str = base_url
        self.system: str = system
        self.system_key: str = system_key

        # Configuration stuff
        self.event_type: EventType = EventType(event_type)

    def deliver(self, pii_md5s: list[MD5WithPII]) -> list[dict]:
        responses: list[dict] = []

        for md5_with_pii in pii_md5s:
            event_data = self._prepare_event_data(md5_with_pii)
            responses.append(self._send_event(event_data))

        return responses

    def _prepare_event_data(self, md5_with_pii: MD5WithPII) -> dict:
        person_data = {}
        if md5_with_pii.pii.first_name:
            person_data["firstName"] = md5_with_pii.pii.first_name
        if md5_with_pii.pii.last_name:
            person_data["lastName"] = md5_with_pii.pii.last_name
        if md5_with_pii.pii.emails:
            person_data["emails"] = [{"value": email} for email in md5_with_pii.pii.emails]
        if md5_with_pii.pii.mobile_phones:
            person_data["phones"] = [{"value": phone.phone} for phone in md5_with_pii.pii.mobile_phones]

        return {
            "source": self.system,
            "system": self.system,
            "type": self.event_type.value,
            "person": person_data
        }

    def _send_event(self, event_data: dict) -> dict:
        headers = {
            "Authorization": f"Basic {base64.b64encode(f'{self.api_key}:'.encode()).decode()}",
            "Content-Type": "application/json",
            "X-System": self.system,
            "X-System-Key": self.system_key
        }
        response = requests.post(f"{self.base_url}/events", json=event_data, headers=headers)
        
        if response.status_code == 204:
            return {"status": "ignored", "message": "Lead flow associated with this source has been archived and ignored."}
        
        response.raise_for_status()
        return response.json()


class AIFollowUpBossDeliverer(FollowUpBossDeliverer):
    """
    Delivers data to FollowUpBoss CRM and uses AI to match fields with the user's
    custom fields. Reads the user's custom fields and matches them with fields in PII data.
    Creates new custom fields for the user's FUB account if they don't exist, and then
    maps the fields in the PII data to the custom fields.
    """

    def _prepare_event_data(self, md5_with_pii: MD5WithPII) -> dict:
        return super()._prepare_event_data(md5_with_pii)
