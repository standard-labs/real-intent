"""Deliver leads to a webhook."""
from pydantic import HttpUrl
import requests

import datetime as dt
from concurrent.futures import ThreadPoolExecutor

from real_intent.internal_logging import log
from real_intent.deliver.base import BaseOutputDeliverer
from real_intent.schemas import MD5WithPII


class WebhookDeliverer(BaseOutputDeliverer):
    """Deliver leads to a webhook."""

    def __init__(self, webhook_url: str | HttpUrl, per_lead_insights: dict[str, str] | None = None):
        """Initialize the deliverer."""
        if not isinstance(webhook_url, (str, HttpUrl)):
            raise ValueError("Webhook URL must be a string or HttpUrl.")

        if isinstance(webhook_url, str):
            try:
                webhook_url = HttpUrl(webhook_url)
            except ValueError:
                raise ValueError("Invalid webhook URL provided.")

        self.webhook_url: str = str(webhook_url)
        self.per_lead_insights: dict[str, str] = per_lead_insights or {}

    def _deliver(self, pii_md5s: list[MD5WithPII]) -> bool:
        """
        Deliver the leads to the webhook.

        Returns True if all leads were delivered successfully.
        Otherwise, returns False.
        """
        with ThreadPoolExecutor(max_workers=5) as executor:
            return all(executor.map(self._deliver_one, pii_md5s))

    def _deliver_one(self, pii_md5: MD5WithPII) -> bool:
        """
        Deliver one lead to the webhook.

        Returns True if the lead was delivered successfully.
        Otherwise, returns False.
        """
        # Build the payload
        payload = {
            "md5": pii_md5.md5,
            "pii": pii_md5.pii.as_lead_export(),
            "insight": self.per_lead_insights.get(pii_md5.md5, ""),
            "sentences": pii_md5.sentences,
            "timestamp": dt.datetime.now().isoformat()
        }

        # Send the request
        response = requests.post(self.webhook_url, json=payload, timeout=10)

        if not response.ok:
            log("error", f"Failed to deliver to webhook with status {response.status_code}: {response.text}")
            return False

        log(
            "trace", 
            (
                f"Delivered lead to webhook. URL: {self.webhook_url}; "
                f"Response code: {response.status_code}; "
                f"Response text: {response.text}; "
                f"Payload: {payload}"
            )
        )

        return True
