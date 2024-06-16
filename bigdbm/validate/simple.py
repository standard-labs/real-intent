"""Basic validation: zip codes, contactable, etc."""
from bigdbm.schemas import MD5WithPII
from bigdbm.validate.base import BaseValidator


class ZipCodeValidator(BaseValidator):
    """Remove hems that do not match an input zip code."""

    def __init__(self, zip_codes: list[str]) -> None:
        """Initialize with a list of zip codes."""
        self.zip_codes: list[str] = zip_codes

    def validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove items that are not in the list of zip codes."""
        return [
            md5 for md5 in md5s if md5.pii.zip_code in self.zip_codes
        ]


class ContactableValidator(BaseValidator):
    """Remove hems that don't have at least one mode of contact."""

    def validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove hems that don't have at least one mode of contact."""
        return [
            md5 for md5 in md5s if any([md5.pii.mobile_phones, md5.pii.emails])
        ]
