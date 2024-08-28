"""
kvCORE integration with no AI field mapping.
"""
from typing import Any
import requests
from datetime import datetime

from bigdbm.deliver.base import BaseOutputDeliverer
from bigdbm.schemas import MD5WithPII
from bigdbm.internal_logging import log


class KvCoreDeliverer(BaseOutputDeliverer):
    def __init__(self, api_key: str, source_name: str, base_url: str = "https://api.kvcore.com/v2/public"):
        super().__init__()
        self.api_key: str = api_key
        self.base_url: str = base_url
        self.source_name: str = source_name

    @property
    def api_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _deliver(self, pii_md5s: list[MD5WithPII]) -> list[dict[str, Any]]:
        """
        Deliver the PII data to kvCORE.

        Args:
            pii_md5s: A list of MD5WithPII objects containing the PII data to be delivered.

        Returns:
            A list of response dictionaries from the kvCORE API for each delivered contact.
        """
        responses: list[dict[str, Any]] = []

        for md5_with_pii in pii_md5s:
            try:
                response = self._deliver_single_lead(md5_with_pii)
                responses.append(response)
            except Exception as e:
                log("error", f"Failed to deliver lead {md5_with_pii.md5}: {str(e)}")
                responses.append({"status": "error", "message": str(e)})

        return responses

    def _deliver_single_lead(self, md5_with_pii: MD5WithPII) -> dict[str, Any]:
        """
        Deliver a single lead to kvCORE.

        Args:
            md5_with_pii: The MD5WithPII object containing the PII data for a single lead.

        Returns:
            A response dictionary from the kvCORE API for the delivered contact.
        """
        contact_data = self._prepare_contact_data(md5_with_pii)
        contact_id = self.create_contact(contact_data)
        
        note = self._prepare_note(md5_with_pii)
        self.add_note(contact_id, note)

        log(
            "trace",
            f"Delivered lead: {md5_with_pii.md5}, contact_id: {contact_id}"
        )

        return {"contact_id": contact_id, "status": "success"}

    def _prepare_contact_data(self, md5_with_pii: MD5WithPII) -> dict[str, Any]:
        """
        Prepare the contact data for a single MD5WithPII object.

        Args:
            md5_with_pii: The MD5WithPII object containing the PII data.

        Returns:
            A dictionary containing the prepared contact data for the kvCORE API.
        """
        pii = md5_with_pii.pii
        contact_data: dict[str, Any] = {
            "first_name": pii.first_name,
            "last_name": pii.last_name,
            "source": self.source_name,
            "status": 0,
            "primary_address": pii.address,
            "primary_city": pii.city,
            "primary_state": pii.state,
            "primary_zip": pii.zip_code
        }

        # Add emails
        for i, email in enumerate(pii.emails, start=1):
            contact_data[f"email_{i}"] = email

        # Add mobile phones
        for i, phone in enumerate(pii.mobile_phones, start=1):
            contact_data[f"cell_phone_{i}"] = phone.phone

        return contact_data

    def _prepare_note(self, md5_with_pii: MD5WithPII) -> str:
        """
        Prepare the note content from the sentences in MD5WithPII.

        Args:
            md5_with_pii: The MD5WithPII object containing the sentences.

        Returns:
            The prepared note content.
        """
        sentences = [sentence.split(">")[-1] if ">" in sentence else sentence for sentence in md5_with_pii.sentences]
        return f"Intents: {', '.join(sentences)}."

    def create_contact(self, contact_data: dict[str, Any]) -> str:
        """
        Create a contact in kvCORE.

        Args:
            contact_data: Dictionary containing contact information.

        Returns:
            The ID of the created contact.

        Raises:
            ValueError: If the API response does not contain an 'id' field.
            requests.RequestException: If the API request fails.
        """
        url = f"{self.base_url}/contact"

        response = requests.post(url, json=contact_data, headers=self.api_headers)
        response.raise_for_status()
        response_data = response.json()

        if 'id' not in response_data:
            raise ValueError("kvCORE API response did not contain an 'id' field")

        return response_data['id']

    def add_note(self, contact_id: str, note: str) -> None:
        """
        Add a note to a contact in kvCORE.

        Args:
            contact_id: The ID of the contact.
            note: The note to add.

        Raises:
            requests.RequestException: If the API request fails.
        """
        url = f"{self.base_url}/contact/{contact_id}/action/note"
        data: dict[str, str] = {
            "details": note,
            "date": datetime.now().isoformat()
        }

        response = requests.put(url, json=data, headers=self.api_headers)
        response.raise_for_status()
