"""Deliver to Zapier webhook"""
import requests
from typing import Any

from real_intent.internal_logging import log
from real_intent.deliver.base import BaseOutputDeliverer
from real_intent.schemas import MD5WithPII


class ZapierDeliverer(BaseOutputDeliverer):
    """Deliver to Zapier webhook"""

    def __init__(self, webhook_url: str, client_email, per_lead_insights: dict[str, str] = {}):
        """Initialize the deliverer"""

        self.webhook_url: str = webhook_url
        self.client_email: str = client_email
        self.per_lead_insights: dict[str, str] = per_lead_insights

    def _deliver(self, pii_md5s: list[MD5WithPII]) -> bool:
        """Deliver the formatted data to Zapier webhook."""

        payload = self._format(pii_md5s)
        response = requests.post(self.webhook_url, json=payload)
        
        if not response.ok:
            log.error(f"Failed to deliver to Zapier webhook {self.webhook_url}: {response.status_code}, {response.text}")
            return False
        
        return response.ok
    
    def _format(self, pii_md5s: list[MD5WithPII]) -> list[dict[str, Any]]:
        """
        Format the leads into a deliverable format.

        Seperates phone numbers and emails (convert_dict_lead_export()), adds insights to the dict, and seperates 
        unique sentences.
        
        Returns the formatted list of these dictionary objects:
        [
            {
                "md5": "123",
                "pii": {...},
                "insight": "insight for md5 123",
                "sentence_1": "...",
                "sentence_2": "...",
                "sentence_3": "...",
                "sentence_4": "...",
                ...
            },
            {
                "md5": "456",
                "pii": {...},
                "insight": "",
                "sentence_1": "...",
                "sentence_2": "...",
                "sentence_3": "...",
                ...
            },
        ]

        Note: Sentence seperation is done here, but might not be necessary if we don't need to send
        sentences. Only did it here because it is able to be sent easily for the WiseAgent webhook.
        Not sure if sentences are meant to be seperated or not...
        """

        formatted_leads = []
        for pii_md5 in pii_md5s:

            md5_dict = pii_md5.convert_dict_lead_export()

            md5_dict["insight"] = self.per_lead_insights.get(md5_dict["md5"], "")

            for pos, sentence in enumerate(md5_dict["sentences"], start=1):
                md5_dict[f"sentence_{pos}"] = sentence
            del md5_dict["sentences"]

            md5_dict["client_email"] = self.client_email

            formatted_leads.append(md5_dict)

        return formatted_leads
