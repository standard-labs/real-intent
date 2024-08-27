"""Validations for attributes related to home ownership or households."""
from bigdbm.schemas import MD5WithPII
from bigdbm.validate.base import BaseValidator


class NotRenterValidator(BaseValidator):
    """Remove leads where 'home_owner_status' is "Renter"."""

    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove leads that are renters."""
        return [
            md5 for md5 in md5s if md5.pii.home_owner_status != "Renter"
        ]
