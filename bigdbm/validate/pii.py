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


class AgeValidator(BaseValidator):
    """
    Only show hems of people above or below a certain age.
    Works inclusively, ex. 50 means 50 or higher/50 or lower.

    If above is True, only takes people above or equal to the age.
    If above is False, only takes people below or equal to the age.
    """

    def __init__(self, min_age: int, max_age: int) -> None:
        """Initialize."""
        self.min_age = int(min_age)
        self.max_age = int(max_age)

    def validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove hems that do not match the age requirement."""
        def is_valid(md5: MD5WithPII) -> bool:
            """Check if the MD5 is in the age range."""
            try:
                age = int(md5.pii.age)
            except ValueError:
                return False

            return self.min_age <= age <= self.max_age
        
        return [md5 for md5 in md5s if is_valid(md5)]


class MNWValidator(BaseValidator):
    """
    Only show hems of people with at least $100k in household 
    income _and_ $100k in household net worth.
    """

    def validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove hems that do not match the HNW requirement."""
        return [
            md5 for md5 in md5s if md5.pii.household_income in {"N. $200,000-$249,999", "O. $250K +"}
            and md5.pii.household_net_worth in {"I. $250,000 - $499,999", "J. Greater than $499,999"}
        ]


class HNWValidator(BaseValidator):
    """
    Only show hems of people with at least $200k in household 
    income _and_ $250k in household net worth.
    """

    def validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove hems that do not match the HNW requirement."""
        return [
            md5 for md5 in md5s if md5.pii.household_income in {"N. $200,000-$249,999", "O. $250K +"}
            and md5.pii.household_net_worth in {"I. $250,000 - $499,999", "J. Greater than $499,999"}
        ]
