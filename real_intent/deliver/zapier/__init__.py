"""Deliverer for Zapier, via webhooks."""
import requests

from typing import Any
from functools import partial
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from real_intent.internal_logging import log
from real_intent.deliver.base import BaseOutputDeliverer
from real_intent.schemas import MD5WithPII


class ZapierDeliverer(BaseOutputDeliverer):
    """
    Delivers data to Zapier via webhooks.

    This class is responsible for formatting and delivering lead data to one or more Zapier webhooks.
    It handles batch processing of leads, multi-threading for multiple webhook URLs, and includes
    additional features such as DNC (Do Not Call) list checking and lead insights.

    Behavior:
    - Formats lead data into a Zapier-friendly structure.
    - Delivers formatted data to multiple Zapier webhooks concurrently.
    - Warns about leads on the DNC list.
    - Adds insights to leads if available.

    Functionality:
    - Converts MD5WithPII objects to dictionaries for lead export.
    - Formats leads with additional information like insights and delivery date.
    - Delivers leads to Zapier webhooks using POST requests.
    - Supports multiple webhook URLs for delivery.
    """

    def __init__(self, webhook_urls: list[str], per_lead_insights: dict[str, str] | None = None):
        """
        Initialize the ZapierDeliverer.

        Args:
            webhook_urls (list[str]): List of Zapier webhook URLs to deliver to.
            per_lead_insights (dict[str, str] | None, optional): Dictionary mapping MD5 hashes to insights. Defaults to None.
        """
        self.webhook_urls: list[str] = webhook_urls
        self.per_lead_insights: dict[str, str] = per_lead_insights or {}

    def _warn_dnc(self, pii_md5s: list[MD5WithPII]) -> None:
        """
        Log a warning if any of the leads are on the DNC list.

        Args:
            pii_md5s (list[MD5WithPII]): List of MD5WithPII objects to check for DNC status.
        """
        for md5_with_pii in pii_md5s:
            if any(phone.do_not_call for phone in md5_with_pii.pii.mobile_phones):
                log(
                    "warn",
                    (
                        f"At least 1 lead in the Zapier deliverer was on "
                        f"the DNC list. Please validate the lead before delivery."
                    )
                )
                break

    def _deliver(self, pii_md5s: list[MD5WithPII]) -> bool:
        """
        Deliver the formatted data to Zapier webhooks.

        Args:
            pii_md5s (list[MD5WithPII]): List of MD5WithPII objects to deliver.

        Returns:
            bool: True if all deliveries were successful, False otherwise.
        """

        self._warn_dnc(pii_md5s)
        payload = self._format(pii_md5s)

        # payload will be constant, so we can use partial to make it as a prefilled argument
        with ThreadPoolExecutor(max_workers=5) as executor:
            deliver_one = partial(self._deliver_one_url, payload)
            results = list(executor.map(deliver_one, self.webhook_urls))
        return all(results)

    def _deliver_one_url(self, payload: list[dict[str, Any]], webhook_url: str) -> bool:
        """
        Deliver batch of leads to a singular Zapier webhook.

        Args:
            payload (list[dict[str, Any]]): List of formatted lead data to deliver.
            webhook_url (str): Zapier webhook URL to deliver to.

        Returns:
            bool: True if delivery was successful, False otherwise.
        """
        response = requests.post(webhook_url, json=payload)

        if response.status_code != 200:
            log(
                "error",
                (
                    f"Failed to deliver to Zapier webhook {webhook_url}. "
                    f"Status code: {response.status_code}, "
                    f"Response: {response.text}"
                )
            )
            return False
            
        return True

    def _convert_dict_lead_export(self, pii_md5: MD5WithPII) -> dict[str, Any]:
        """
        Convert MD5WithPII object to dictionary for lead export.

        Args:
            pii_md5 (MD5WithPII): MD5WithPII object to convert.

        Returns:
            dict[str, Any]: Dictionary containing formatted lead data.
        """
        return {
            "md5": pii_md5.md5,
            "sentences": pii_md5.sentences,
            "pii": pii_md5.pii.as_lead_export()
        }

    def _format(self, pii_md5s: list[MD5WithPII]) -> list[dict[str, Any]]:
        """
        Format the leads into a deliverable format.

        Separates phone numbers and emails (convert_dict_lead_export()), adds insights to the dict, and combines 
        sentences into a single string.

        Args:
            pii_md5s (list[MD5WithPII]): List of MD5WithPII objects to format.

        Returns:
            list[dict[str, Any]]: List of formatted lead dictionaries with the following structure:
                [
                    {
                        "md5": "...",
                        "pii": {...},
                        "insight": "...",
                        "sentences": "..., ..., ..., ...",
                        "date_delivered": "...."
                    },
                    {
                        "md5": "...",
                        "pii": {...},
                        "insight": "",
                        "sentences": "..., ..., ...",
                        "date_delivered": "...."
                    }
                ]
        """
        formatted_leads: list[dict[str, Any]] = []
        for pii_md5 in pii_md5s:
            md5_dict: dict[str, Any] = self._convert_dict_lead_export(pii_md5)

            # convert all values to string, needed for Zapier consistency
            md5_dict["pii"] = {key: (str(value) if value else None) for key, value in md5_dict["pii"].items()}

            md5_dict["insight"] = self.per_lead_insights.get(md5_dict["md5"], "")
            md5_dict["sentences"] = ", ".join(md5_dict["sentences"])
            md5_dict["date_delivered"] = datetime.now().strftime("%Y-%m-%d")
            formatted_leads.append(md5_dict)

        return formatted_leads
