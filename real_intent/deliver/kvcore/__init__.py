"""Deliver to kvCORE."""
import requests

from typing import Any
from concurrent.futures import ThreadPoolExecutor

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
            tag: str = "",
            per_lead_insights: dict[str, str] | None = None
        ):
        """Initialize the deliverer."""
        # Postmark setup
        self.postmark_server_token = postmark_server_token
        self.from_email = from_email

        # kvCORE setup
        self.inboxing_address = inboxing_address
        self.tag = tag

        # Per-lead insights
        self.per_lead_insights: dict[str, str] = per_lead_insights or {}

    def _deliver(self, pii_md5s: list[MD5WithPII]) -> bool:
        """
        Deliver the leads to kvCORE.

        Returns True if all leads were delivered successfully.
        Otherwise, returns False.
        """
        with ThreadPoolExecutor(max_workers=5) as executor:
            return all(executor.map(self._deliver_one, pii_md5s))

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

    @staticmethod
    def _address_str(pii_md5: MD5WithPII) -> str:
        """Generate a string representation of the address."""
        address_parts: list[str] = []

        # Add street address if available
        if addr := pii_md5.pii.address.strip():
            address_parts.append(addr)

        # Add city if available
        if city := pii_md5.pii.city.strip():
            address_parts.append(city)

        # Add state if available
        if state := pii_md5.pii.state.strip():
            address_parts.append(state)

        # Add zip code and zip4 if available
        if zip_code := pii_md5.pii.zip_code.strip():
            zip_str: str = zip_code

            if zip4 := pii_md5.pii.zip4.strip():
                zip_str += f"-{zip4}"

            address_parts.append(zip_str)

        # Join all parts with appropriate separators
        return ", ".join(address_parts)

    def _agent_notes(self, pii_md5: MD5WithPII) -> str:
        """Generate custom agent notes for a single lead."""
        attrs: dict[str | Any] = {}

        if pii_md5.pii.household_income:
            attrs["Household Income"] = pii_md5.pii.household_income
        
        if pii_md5.pii.household_net_worth:
            attrs["Household Net Worth"] = pii_md5.pii.household_net_worth

        if (insight := self.per_lead_insights.get(pii_md5.md5)):
            attrs["Insight"] = insight

        if (address := self._address_str(pii_md5)):
            attrs["Address"] = address

        return "\n".join([f"{k}: {v}" for k, v in attrs.items()])
    
    def _lead_deal_type(self, pii_md5: MD5WithPII) -> str:
        """Calculated guess if the lead is a buyer or a seller."""
        seller_sentence_matches: set[str] = {
            "In-Market>Real Estate>Sellers", 
            "In-Market>Real Estate>Pre-Movers"
        }

        buyer_sentence_matches: set[str] = {
            "In-Market>Financial>Loans>Mortgages",
            "In-Market>Real Estate>First-Time Home Buyer"
        }

        if any([sentence in seller_sentence_matches for sentence in pii_md5.sentences]):
            return "Seller"

        if any([sentence in buyer_sentence_matches for sentence in pii_md5.sentences]):
            return "Buyer"

        return ""

    def _email_body(self, pii_md5: MD5WithPII) -> str:
        """Create the email body."""
        # Check for required first name, last name, and either an email or a phone number
        if not (pii_md5.pii.first_name and pii_md5.pii.last_name and any([pii_md5.pii.emails, pii_md5.pii.mobile_phones])):
            log("warn", f"Missing required PII data: first name, last name, or email: {pii_md5}")
            return ""

        email_body: str = EMAIL_TEMPLATE.format(
            first_name=pii_md5.pii.first_name,
            last_name=pii_md5.pii.last_name
        )

        # Add email if available
        if pii_md5.pii.emails:
            email_body += f"\nEmail: {pii_md5.pii.emails[0]}"

        # Add phone number if available
        if pii_md5.pii.mobile_phones:
            if pii_md5.pii.mobile_phones[0].do_not_call:
                log("trace", "Importing a DNC phone number into kvCORE.")

            email_body += f"\nPhone: {pii_md5.pii.mobile_phones[0].phone}"

        # Add zip code if available
        if pii_md5.pii.zip_code:
            email_body += f"\nZipcode: {pii_md5.pii.zip_code}"

        # Add deal type if matched
        if (deal_type := self._lead_deal_type(pii_md5)):
            email_body += f"\nDeal Type: {deal_type}"

        # Add tag if specified
        if self.tag:
            email_body += f"\nHashtag: {self.tag}"

        # Add custom agent notes
        if agent_notes := self._agent_notes(pii_md5):
            email_body += f"\nAgent Notes: {agent_notes}"

        return email_body
