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


class MD5Validator(BaseValidator):
    """
    Remove hems that match a list of MD5s.

    Useful when ensuring uniqueness in generated hems.
    """

    def __init__(self, md5_strings: list[str]) -> None:
        """Initialize with a list of blacklisted MD5s."""
        self.md5_strings: list[str] = md5_strings

    def validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove hems that match the initialized list of MD5 strings."""
        return [
            md5 for md5 in md5s if md5.md5 not in self.md5_strings
        ]


class SamePersonValidator(BaseValidator):
    """
    Remove leads approximated to match to humans already in the lead list, i.e.
    the same person with different MD5s, thus appearing twice.
    """

    def validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """
        Remove leads approximated to match to humans already in the lead list, i.e.
        the same person with different MD5s, thus appearing twice.
        """
        unique_leads: list[MD5WithPII] = []
        for lead in md5s:
            if all(lead != other for other in unique_leads):
                unique_leads.append(lead)

        return unique_leads


class NumSentencesValidator(BaseValidator):
    """Ensure MD5s have at least a certain number of sentences."""
    
    def __init__(self, min_sentences: int) -> None:
        """Initialize with a minimum number of sentences."""
        self.min_sentences: int = min_sentences

    def validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove hems with fewer than the minimum number of sentences."""
        return [
            md5 for md5 in md5s if len(md5.sentences) >= self.min_sentences
        ]
