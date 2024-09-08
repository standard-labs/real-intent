"""Deliver to kvCORE."""
import requests

from real_intent.internal_logging import log
from real_intent.deliver.base import BaseOutputDeliverer
from real_intent.schemas import MD5WithPII


EMAIL_TEMPLATE: str = """First Name: {first_name}
Last Name: {last_name}
Email: {email}"""


class KVCoreDeliverer(BaseOutputDeliverer):
    """
    Deliver to kvCORE. Does not use the API - uses the inboxing address.

    The inboxing address is the email address that kvCORE uses to import leads.
    The tag is the hashtag that kvCORE uses to tag leads.
    """

    def __init__(self, postmark_server_token: str, from_email: str, inboxing_address: str, tag: str):
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
        for pii_md5 in pii_md5s:
            if not self._deliver_one(pii_md5):
                return False

        return True

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
            log.error(f"Failed to send email to kvCORE with status {response.status_code}: {response.text}")
            return False

        return True

    def _email_body(self, pii_md5: MD5WithPII) -> str:
        """Create the email body."""
        # Check for required PII data. The rest of the data is optional
        if not (pii_md5.pii.first_name and pii_md5.pii.last_name and pii_md5.pii.emails):
            log.error(f"Missing required PII data: first name, last name, or email: {pii_md5}")
            return ""

        email_body: str = EMAIL_TEMPLATE.format(
            first_name=pii_md5.pii.first_name,
            last_name=pii_md5.pii.last_name,
            email=pii_md5.pii.emails[0],
        )

        # Add phone number if available
        if pii_md5.pii.phone_numbers:
            if pii_md5.pii.mobile_phones[0].do_not_call:
                log.warn("Importing a DNC phone number into kvCORE.")

            email_body += f"\nPhone: {pii_md5.pii.mobile_phones[0].phone}"

        # Add zip code if available
        if pii_md5.pii.zip_code:
            email_body += f"\nZipcode: {pii_md5.pii.zip_code}"

        # Add tag if specified
        if self.tag:
            email_body += f"\nHashtag: {self.tag}"

        return email_body
