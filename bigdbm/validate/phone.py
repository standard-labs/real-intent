"""Validate phone numbers using numverify."""
import requests

from bigdbm.schemas import MD5WithPII
from bigdbm.validate.base import BaseValidator


class PhoneValidator(BaseValidator):
    """
    Remove US phone numbers determined to not be 'valid' by MillionVerifier.
    """

    def __init__(self, numverify_key: str) -> None:
        """Initialize with numverify key."""
        self.api_key: str = numverify_key

    def _validate_phone(self, phone: str) -> bool:
        """Validate a US phone number with numverify."""
        phone = str(phone)
        if phone.startswith("+1"):
            phone = phone[2:]
        
        if len(phone) == 11 and phone.startswith("1"):
            phone = phone[1:]
        
        if len(phone) != 10:
            return False
        
        response = requests.get(
            "https://apilayer.net/api/validate",
            params={
                "access_key": self.api_key,
                "number": phone,
                "country_code": "US"
            }
        )

        response.raise_for_status()
        response_json = response.json()

        if "valid" not in response_json:
            raise ValueError(f"Unexpected response from numverify: {response_json}")

        return response_json["valid"]

    def validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove any phone numbers that are not 'good'."""
        for md5 in md5s:
            md5.pii.mobile_phones = [
                phone for phone in md5.pii.mobile_phones if self._validate_phone(phone.phone)
            ]

        return md5s
