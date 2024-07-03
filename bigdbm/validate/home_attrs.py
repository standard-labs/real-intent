"""Validations for attributes related to home ownership or households."""
from bigdbm.schemas import MD5WithPII
from bigdbm.validate.base import BaseValidator


class NotRenterValidator(BaseValidator):
    """Remove hems that are renters."""

    def validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove hems that are renters."""
        return [
            md5 for md5 in md5s if md5.pii.home_owner_status != "Renter"
        ]
