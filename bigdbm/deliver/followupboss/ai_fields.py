"""Follow Up Boss delivery with AI field mapping. Requires OpenAI."""
import requests
from pydantic import BaseModel, Field

import json
from typing import Literal, Any

from bigdbm.schemas import MD5WithPII
from bigdbm.deliver.followupboss.vanilla import FollowUpBossDeliverer, EventType
from bigdbm.deliver.followupboss.ai_prompt import SYSTEM_PROMPT


class CustomField(BaseModel):
    """Custom field in Follow Up Boss."""
    id: int
    name: str
    label: str
    type: str
    choices: list[str] = Field(default_factory=list)
    orderWeight: int
    hideIfEmpty: bool
    readOnly: bool
    isRecurring: bool = False


class CustomFieldCreation(BaseModel):
    """Job to create a custom field in Follow Up Boss."""
    label: str = Field(
        ..., 
        description="The user-friendly name of the custom field (e.g. 'Anniversary')."
    )
    type: Literal["text", "date", "number", "dropdown"] = Field(
        ...,
        description="The type of the custom field. Can be 'text', 'date', 'number', or 'dropdown'."
    )
    choices: list[str] = Field(
        default_factory=list,
        description="List of choices for the custom field. Only if type is 'dropdown'."
    )
    isRecurring: bool = Field(
        False,
        description=(
            "Whether the custom field is recurring (e.g. 'Birthday'). "
            "Only set and returned for date fields."
        )
    )


class AIFollowUpBossDeliverer(FollowUpBossDeliverer):
    """
    Delivers data to FollowUpBoss CRM and uses AI to match fields with the user's
    custom fields. Reads the user's custom fields and matches them with fields in PII data.

    (Eventually will optionally create new custom fields for the user's FUB account 
    if they don't exist, and then maps the fields in the PII data to the custom fields.)
    """

    def __init__(
        self,
        api_key: str,
        system: str,
        system_key: str,
        openai_api_key: str,
        base_url: str = "https://api.followupboss.com/v1",
        event_type: EventType = EventType.REGISTRATION,
        **kwargs
    ):
        """
        Initialize the AIFollowUpBossDeliverer.

        Args:
            api_key (str): The API key for FollowUpBoss.
            system (str): The system identifier.
            system_key (str): The system key.
            openai_api_key (str): The API key for OpenAI.
            base_url (str, optional): The base URL for the FollowUpBoss API. Defaults to "https://api.followupboss.com/v1".
            event_type (EventType, optional): The event type for adding a lead. Defaults to Registration.
            **kwargs: Additional keyword arguments to be passed to the parent class.
        """
        super().__init__(api_key, system, system_key, base_url, event_type, **kwargs)

        try:
            import openai
        except ImportError:
            raise ImportError(
                "OpenAI is required for AI FollowUpBoss deliverer. pip install bigdbm[ai]."
            )

        self.openai_client = openai.OpenAI(api_key=openai_api_key)

    def _get_custom_fields(self) -> list[CustomField]:
        """Get the custom fields from the user's Follow Up Boss account."""
        response = requests.get(f"{self.base_url}/customFields", headers=self.api_headers)
        response.raise_for_status()
        raw_res = response.json()["customfields"]
        return [CustomField(**field) for field in raw_res]

    def _create_custom_field(self, custom_field: CustomFieldCreation) -> CustomField:
        """Create a custom field in the user's Follow Up Boss account."""
        # Create the custom field
        response = requests.post(
            f"{self.base_url}/customFields",
            headers=self.api_headers,
            json=custom_field.model_dump()
        )
        response.raise_for_status()
        field_id = response.json()["id"]
        
        # Get the custom field
        response = requests.get(
            f"{self.base_url}/customFields/{field_id}",
            headers=self.api_headers
        )
        response.raise_for_status()

        return CustomField(**response.json())

    def _prepare_event_data(self, md5_with_pii: MD5WithPII) -> dict:
        raw_event_data: dict = super()._prepare_event_data(md5_with_pii)

        # Get all the custom fields
        custom_fields: list[CustomField] = self._get_custom_fields()
        custom_fields_str: str = json.dumps(
            [field.model_dump() for field in custom_fields],
            indent=4
        )

        # Prepare the PII data
        filtered_pii_data: dict[str, Any] = {
            key: val for key, val in md5_with_pii.pii.model_dump().items() 
            if key not in {"first_name", "last_name", "emails", "mobile_phones"}
        }
        filtered_pii_data_str: str = json.dumps(filtered_pii_data, indent=4)

        # Match the custom fields with the PII data
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": (
                        f"PII data:\n{filtered_pii_data_str}\n\n"
                        f"Custom fields:\n{custom_fields_str}"
                    )
                }
            ],
            max_tokens=4095,
            temperature=0.7,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            response_format={"type": "json_object"}
        )

        # Try to parse
        try:
            ai_suggestions: dict[str, str | int | bool] = json.loads(
                response.choices[0].message.content
            )
        except json.JSONDecodeError:
            # LOG ERROR HERE ABOUT BAD PARSING
            ai_suggestions: dict[str, str | int | bool] = {}
        
        # Merge the AI suggestions with the protected person data
        custom_field_names: list[str] = [field.name for field in custom_fields]
        for key, val in ai_suggestions.items():
            if key in custom_field_names:
                raw_event_data["person"][key] = val

        return raw_event_data
