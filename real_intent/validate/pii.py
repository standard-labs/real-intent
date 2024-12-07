"""Validators for personal identifiable information (PII)."""
from real_intent.schemas import MD5WithPII, Gender
from real_intent.validate.base import BaseValidator


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


class RemoveOccupationsValidator(BaseValidator):
    """Remove leads with specified occupations."""

    def __init__(self, *occupations: str) -> None:
        """Initialize with the filtered occupations."""
        self.occupations: set[str] = set(occupations)

    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Only return leads whose occupation does not exist in the initialized list of occupations."""
        return [
            md5 for md5 in md5s if md5.pii.occupation not in self.occupations
        ]


class NoRealEstateAgentValidator(RemoveOccupationsValidator):
    """Remove leads that are real estate agents."""

    def __init__(self) -> None:
        """Initialize with the filtered occupation."""
        super().__init__("Real Estate/Realtor")


class MidIncomeValidator(BaseValidator):
    """Remove leads below $30k income."""

    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove leads that do not match the MNW requirement."""
        income_levels = {
            "D. $30,000-$39,999",
            "E. $40,000-$49,999",
            "F. $50,000-$59,999",
            "G. $60,000-$74,999",
            "H. $75,000-$99,999",
            "K. $100,000-$149,999", 
            "L. $150,000-$174,999", 
            "M. $175,000-$199,999", 
            "N. $200,000-$249,999", 
            "O. $250K +"
        }
        
        return [
            md5 for md5 in md5s 
            if md5.pii.household_income in income_levels
        ]


class HighIncomeValidator(BaseValidator):
    """Remove leads below $75k income."""

    def _validate(self, md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """Remove leads that do not match the high income requirement."""
        income_levels = {
            "H. $75,000-$99,999",
            "K. $100,000-$149,999", 
            "L. $150,000-$174,999", 
            "M. $175,000-$199,999", 
            "N. $200,000-$249,999", 
            "O. $250K +"
        }
        
        return [
            md5 for md5 in md5s 
            if md5.pii.household_income in income_levels
        ]
        

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
