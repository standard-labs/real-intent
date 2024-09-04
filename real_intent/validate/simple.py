"""Basic validation: zip codes, contactable, etc."""
from real_intent.schemas import MD5WithPII
from real_intent.validate.base import BaseValidator


class ZipCodeValidator(BaseValidator):
    """Remove leads not matching specified zip codes."""

    def __init__(self, zip_codes: list[str]) -> None:
        """Initialize with a list of zip codes."""
        self.zip_codes: list[str] = zip_codes

    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove leads that are not in the list of zip codes."""
        return [
            md5 for md5 in md5s if md5.pii.zip_code in self.zip_codes
        ]


class ContactableValidator(BaseValidator):
    """Remove leads without a contact method (mobile or email)."""

    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove leads that don't have at least one mode of contact."""
        return [
            md5 for md5 in md5s if any([md5.pii.mobile_phones, md5.pii.emails])
        ]


class MD5Validator(BaseValidator):
    """Remove leads with specific MD5 hashes."""

    def __init__(self, md5_strings: list[str]) -> None:
        """Initialize with a list of blacklisted MD5s."""
        self.md5_strings: list[str] = md5_strings

    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove leads that match the initialized list of MD5 strings."""
        return [
            md5 for md5 in md5s if md5.md5 not in self.md5_strings
        ]


class SamePersonValidator(BaseValidator):
    """
    Remove duplicate leads likely representing the same person.
    Uses hash() method to identify duplicates, merging 'sentences' for matches.
    """

    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove duplicate leads based on hash() method."""
        unique_leads: dict[str, MD5WithPII] = {}

        lead: MD5WithPII
        for lead in md5s:
            if lead.hash() in unique_leads:
                unique_leads[lead.hash()].sentences += lead.sentences
                continue
                
            unique_leads[lead.hash()] = lead
        
        return list(unique_leads.values())


class NumSentencesValidator(BaseValidator):
    """Remove leads with fewer than the specified number of sentences."""
    
    def __init__(self, min_sentences: int) -> None:
        """Initialize with a minimum number of sentences."""
        self.min_sentences: int = min_sentences

    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove leads with fewer than the minimum number of sentences."""
        return [
            md5 for md5 in md5s if len(md5.sentences) >= self.min_sentences
        ]
