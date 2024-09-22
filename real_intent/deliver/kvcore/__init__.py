"""Deliver to kvCORE."""
import requests

from typing import Any

from real_intent.internal_logging import log
from real_intent.deliver.base import BaseOutputDeliverer
from real_intent.schemas import MD5WithPII


EMAIL_TEMPLATE: str = """First Name: {first_name}
Last Name: {last_name}"""


class KVCoreDeliverer(BaseOutputDeliverer):
    """
    Deliver to kvCORE. Does not use the API - uses the inboxing address.

    The inboxing address is the email address that kvCORE uses to import leads.
    The tag is the hashtag that kvCORE uses to tag leads.
    """

    def __init__(
            self, 
            postmark_server_token: str, 
            from_email: str, 
            inboxing_address: str, 
            tag: str = ""
        ):
        """Initialize the deliverer."""
        # Postmark setup
        self.postmark_server_token = postmark_server_token
        self.from_email = from_email

        # kvCORE setup
        self.inboxing_address = inboxing_address
        self.tag = tag

    def _deliver(self, pii_md5s: list[MD5WithPII]) -> bool:
        """
        Deliver the leads to kvCORE.

        Returns True if all leads were delivered successfully.
        Otherwise, returns False.
        """
        all_good: bool = True
        for pii_md5 in pii_md5s:
            if not self._deliver_one(pii_md5):
                all_good = False
                continue

        return all_good

    def _deliver_one(self, pii_md5: MD5WithPII) -> bool:
        """
        Email one lead into the inboxing address.

        Returns True if the lead was delivered successfully.
        Otherwise, returns False.
        """
        if not (email_body := self._email_body(pii_md5)):
            return False

        response = requests.post(
            "https://api.postmarkapp.com/email",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Postmark-Server-Token": self.postmark_server_token
            },
            json={
                "From": self.from_email,
                "To": self.inboxing_address,
                "Subject": "Add Contact",
                "TextBody": email_body
            }
        )

        if not response.ok:
            log("error", f"Failed to send email to kvCORE with status {response.status_code}: {response.text}")
            return False

        return True

    def _agent_notes(self, pii_md5: MD5WithPII) -> str:
        """Generate custom agent notes for a single lead."""
        attrs: dict[str | Any] = {}

        if pii_md5.pii.household_income:
            attrs["Household Income"] = pii_md5.pii.household_income
        
        if pii_md5.pii.household_net_worth:
            attrs["Household Net Worth"] = pii_md5.pii.household_net_worth

        return "\n".join([f"{k}: {v}" for k, v in attrs.items()])

    def _email_body(self, pii_md5: MD5WithPII) -> str:
        """Create the email body."""
        # Check for required first name, last name, and either an email or a phone number
        if not (pii_md5.pii.first_name and pii_md5.pii.last_name and any([pii_md5.pii.emails, pii_md5.pii.mobile_phones])):
            log("warn", f"Missing required PII data: first name, last name, or email: {pii_md5}")
            return ""

        email_body: str = EMAIL_TEMPLATE.format(
            first_name=pii_md5.pii.first_name,
            last_name=pii_md5.pii.last_name,
            email=pii_md5.pii.emails[0],
        )

        # Add email if available
        if pii_md5.pii.emails:
            email_body += f"\nEmail: {pii_md5.pii.emails[0]}"

        # Add phone number if available
        if pii_md5.pii.mobile_phones:
            if pii_md5.pii.mobile_phones[0].do_not_call:
                log("warn", "Importing a DNC phone number into kvCORE.")

            email_body += f"\nPhone: {pii_md5.pii.mobile_phones[0].phone}"

        # Add zip code if available
        if pii_md5.pii.zip_code:
            email_body += f"\nZipcode: {pii_md5.pii.zip_code}"

        # Add tag if specified
        if self.tag:
            email_body += f"\nHashtag: {self.tag}"

        # Add custom agent notes
        if agent_notes := self._agent_notes(pii_md5):
            email_body += f"\nAgent Notes: {agent_notes}"

        return email_body
