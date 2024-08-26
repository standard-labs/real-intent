"""Validators for personal identifiable information (PII)."""
from bigdbm.schemas import MD5WithPII, Gender
from bigdbm.validate.base import BaseValidator


class GenderValidator(BaseValidator):
    """Remove leads with gender not matching specified gender(s)."""

    def __init__(self, *gender: Gender) -> None:
        """Initialize with the filtered gender."""
        self.genders: tuple[Gender] = gender

    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Only return leads whose gender exists in the initialized list of genders."""
        return [
            md5 for md5 in md5s if md5.pii.gender in self.genders
        ]


class AgeValidator(BaseValidator):
    """Remove leads with age outside specified range (inclusive)."""

    def __init__(self, min_age: int, max_age: int) -> None:
        """Initialize."""
        self.min_age = int(min_age)
        self.max_age = int(max_age)

    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove leads that do not match the age requirement."""
        def is_valid(md5: MD5WithPII) -> bool:
            """Check if the lead is in the age range."""
            try:
                age = int(md5.pii.age)
            except ValueError:
                return False

            return self.min_age <= age <= self.max_age
        
        return [md5 for md5 in md5s if is_valid(md5)]


class MNWValidator(BaseValidator):
    """Remove leads below Medium Net Worth (MNW): $100k+ income and $100k+ net worth."""

    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove leads that do not match the MNW requirement."""
        income_levels = {
            "K. $100,000-$149,999", 
            "L. $150,000-$174,999", 
            "M. $175,000-$199,999", 
            "N. $200,000-$249,999", 
            "O. $250K +"
        }
        
        net_worth_levels = {
            "H. $100,000 - $249,999", 
            "I. $250,000 - $499,999", 
            "J. Greater than $499,999"
        }
        
        return [
            md5 for md5 in md5s 
            if md5.pii.household_income in income_levels 
            and md5.pii.household_net_worth in net_worth_levels
        ]


class HNWValidator(BaseValidator):
    """Remove leads below High Net Worth (HNW): $200k+ income and $250k+ net worth."""

    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove leads that do not match the HNW requirement."""
        income_levels = {
            "N. $200,000-$249,999", 
            "O. $250K +"
        }
        
        net_worth_levels = {
            "I. $250,000 - $499,999", 
            "J. Greater than $499,999"
        }
        
        return [
            md5 for md5 in md5s 
            if md5.pii.household_income in income_levels 
            and md5.pii.household_net_worth in net_worth_levels
        ]
