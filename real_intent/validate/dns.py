"""Validation for the Do Not Sell list."""
import requests
from pymongo.collection import Collection

from real_intent.validate.base import BaseValidator
from real_intent.schemas import MD5WithPII


class FilloutDNSValidator(BaseValidator):
    """Removes leads with an email on the Do Not Sell (DNS) blacklist."""

    def __init__(self, fillout_api_key: str, fillout_form_id: str, question_id: str) -> None:
        self.fillout_api_key: str = fillout_api_key
        self.fillout_form_id: str = fillout_form_id
        self.question_id: str = question_id

        # Create a local cache of the DNS list (submissions)
        self.emails_cache: set[str] = self.all_emails()

    @property
    def fillout_api_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.fillout_api_key}",
        }

    def _get_submissions(self) -> list[dict]:
        """Pull all submissions from the Fillout form."""
        offset: int = 0
        submissions: list[dict] = []

        while True:
            submissions_res = requests.get(
                f"https://api.fillout.com/v1/api/forms/{self.fillout_form_id}/submissions", 
                headers=self.fillout_api_headers,
                params={"limit": 150, "offset": offset}
            )
            submissions_res.raise_for_status()
            submissions_res_json = submissions_res.json()

            submissions += submissions_res_json["responses"]

            if len(submissions_res_json["responses"]) < 150:
                break

            offset += 150

        return submissions

    def _update_emails_cache(self) -> None:
        """Update the local cache of submissions."""
        self.emails_cache = self.all_emails()

    def _email_from_submission(self, submission: dict) -> str:
        """Extract the requested email from a Fillout submission."""
        question_answers: list[dict] = submission["questions"]

        if not question_answers:
            raise ValueError("No questions found in submission.")

        if not any(q["id"] == self.question_id for q in question_answers):
            raise ValueError("No email question found in submission.")

        email_answer: dict = next(q for q in question_answers if q["id"] == self.question_id)
        return str(email_answer["value"])

    def all_emails(self) -> set[str]:
        """Get all emails from Fillout submissions."""
        return set(self._email_from_submission(s) for s in self._get_submissions())

    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove leads with an email on the Do Not Sell (DNS) blacklist."""
        return [
            md5 for md5 in md5s if all(
                email not in self.emails_cache for email in md5.pii.emails
            )
        ]

    
class MongoDNSValidator(BaseValidator):
    """Removes leads with an email on the Do Not Sell (DNS) blacklist."""

    def __init__(self, mongo_collection: Collection) -> None:
        self.mongo_collection: Collection = mongo_collection

    def _check_emails(self, emails: list[str]) -> set[str]:
        """Check which emails are on the Do Not Sell (DNS) blacklist.
        
        Args:
            emails: List of emails to check.
            
        Returns:
            Set of emails that are on the DNS blacklist.
        """
        # Use $in operator to check all emails in one query
        blacklisted = self.mongo_collection.find({"email": {"$in": emails}})
        return {doc["email"] for doc in blacklisted}

    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove leads with an email on the Do Not Sell (DNS) blacklist."""
        # Get all unique emails from the MD5s
        all_emails = {email for md5 in md5s for email in md5.pii.emails}
        
        # Check all emails at once
        blacklisted_emails = self._check_emails(list(all_emails))
        
        # Filter MD5s where none of their emails are blacklisted
        return [
            md5 for md5 in md5s if not any(
                email in blacklisted_emails for email in md5.pii.emails
            )
        ]
