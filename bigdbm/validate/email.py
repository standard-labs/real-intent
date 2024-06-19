"""Validate emails using MillionVerifier."""
import requests

from bigdbm.schemas import MD5WithPII
from bigdbm.validate.base import BaseValidator


class EmailValidator(BaseValidator):
    """
    Remove emails determined to not be 'good' by MillionVerifier.
    """

    def __init__(self, million_key: str) -> None:
        """Initialize with MillionVerifier key."""
        self.api_key: str = million_key

    def _validate_email(self, email: str) -> bool:
        """Validate an email with MillionVerifier."""
        response = requests.get(
            "https://api.millionverifier.com/api/v3",
            params={
                "api": self.api_key,
                "email": email,
                "timeout": 10
            }
        )

        response.raise_for_status()
        response_json = response.json()

        if "resultcode" not in response_json:
            raise ValueError(f"Unexpected response from MillionVerifier: {response_json}")

        return response_json["resultcode"] == 1

    def validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove any emails that are not 'good'."""
        for md5 in md5s:
            md5.pii.emails = [
                email for email in md5.pii.emails if self._validate_email(email)
            ]

        return md5s
