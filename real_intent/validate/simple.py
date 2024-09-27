"""Basic validation: zip codes, contactable, etc."""
from real_intent.schemas import MD5WithPII
from real_intent.validate.base import BaseValidator


class ZipCodeValidator(BaseValidator):
    """
    Remove leads not matching specified zip codes.

    Args:
        zip_codes: List of zip codes to keep.
    """

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
    """
    Remove leads with specific MD5 hashes.

    Args:
        md5_strings: List of MD5 strings to remove.
    """

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
        lead_hash: str
        for lead in md5s:
            if (lead_hash := lead.hash()) in unique_leads:
                unique_leads[lead_hash].sentences += lead.sentences
                unique_leads[lead_hash]._raw_sentences += lead._raw_sentences
                continue
                
            unique_leads[lead_hash] = lead
        
        return list(unique_leads.values())


class NumSentencesValidator(BaseValidator):
    """
    Remove leads with fewer than the specified number of sentences.

    Args:
        min_sentences: Minimum number of intent events (sentences) required.
        use_unique: If True, use unique sentences count; if False, use total sentences count.
            If True, counts the number of _types_ of events, as duplicates are removed.
    """
    
    def __init__(self, min_sentences: int, use_unique: bool = False) -> None:
        """Initialize with a minimum number of sentences and counting method."""
        self.min_sentences: int = min_sentences
        self.use_unique: bool = use_unique

    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove leads with fewer than the minimum number of sentences."""
        if self.use_unique:
            return [
                md5 for md5 in md5s if md5.unique_sentences_count >= self.min_sentences
            ]

        return [
            md5 for md5 in md5s if md5.total_sentences >= self.min_sentences
        ]
