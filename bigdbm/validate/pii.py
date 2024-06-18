"""Gender validator. Only show hems of a certain verified gender."""
from bigdbm.schemas import MD5WithPII, Gender
from bigdbm.validate.base import BaseValidator


class GenderValidator(BaseValidator):
    """Only show hems of a certain verified gender."""

    def __init__(self, *gender: Gender) -> None:
        """Initialize with the filtered gender."""
        self.genders: tuple[Gender] = gender

    def validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Only return hems whose gender exists in the initialized list of genders."""
        return [
            md5 for md5 in md5s if md5.pii.gender in self.genders
        ]
