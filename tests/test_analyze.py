import os

import pytest
from dotenv import load_dotenv

from real_intent.analyze.base import BaseAnalyzer
from real_intent.analyze.insights import OpenAIInsightsGenerator, ValidatedInsightsGenerator
from real_intent.schemas import Gender, MD5WithPII, PII, MobilePhone

from real_intent.process.fill import FillProcessor
from real_intent.validate.simple import SamePersonValidator
from real_intent.validate.pii import MNWValidator


# Load environment variables
load_dotenv()


class TestAnalyzer(BaseAnalyzer):
    def _analyze(self, md5s: list[MD5WithPII]) -> str:
        return f"Analyzed {len(md5s)} MD5s"


def create_test_pii() -> PII:
    return PII(
                Id="test_id",
                First_Name="Tuna",
                Last_Name="Sandwich",
                Address="123 Test St",
                City="Test City",
                State="TS",
                Zip="12345",
                Zip4="2224",
                Fips_State_Code="01",
                Fips_County_Code="002",
                County_Name="Columbia",
                Latitude="34.1234",
                Longitude="-87.1234",
                Address_Type="Residential",
                Cbsa="12345",
                Census_Tract="123456",
                Census_Block_Group="1",
                Census_Block="1",
                Gender=Gender.MALE,
                SCF="123",
                DMA="333",
                MSA="222",
                Congressional_District="7",
                HeadOfHousehold="Yes",
                Birth_Month_and_Year="01/1990",
                Age="45",
                Prop_Type="Single Family",
                Email_Array=["tunasandwich@gmail.com"],
                mobile_phones=[MobilePhone(phone="1234567890", do_not_call=False)],
                Children_HH="2",
                Credit_Range="Good",
                Income_HH="100000-150000",
                Net_Worth_HH="500000-1000000",
                Home_Owner="Yes",
                Marital_Status="Married",
                Occupation_Detail="Engineer",
                Median_Home_Value="200000",
                Education="Bachelors",
                Length_of_Residence="5",
                Num_Adults_HH="2",
                Political_Party="Republican",
                Health_Beauty_Products="Yes",
                Cosmetics="Yes",
                Jewelry="Yes",
                Investment_Type="Stocks",
                Investments="Yes",
                Pet_Owner="No",
                Pets_Affinity="Cats",
                Health_Affinity="Fitness",
                Diet_Affinity="Low Carb",
                Fitness_Affinity="Gym",
                Outdoors_Affinity="Hiking",
                Boating_Sailing_Affinity="Yes",
                Camping_Hiking_Climbing_Affinity="Yes",
                Fishing_Affinity="Yes",
                Hunting_Affinity="Yes",
                Aerobics="Yes",
                NASCAR="Yes",
                Scuba="Yes",
                Weight_Lifting="Yes",
                Healthy_Living_Interest="Yes",
                Motor_Racing="Yes",
                Travel_Foreign="Yes",
                Self_Improvement="Yes",
                Walking="Yes",
                Fitness="Yes",
                Ethnicity_Detail="Caucasian",
                Ethnic_Group="Caucasian",
    )


def test_base_analyzer() -> None:
    analyzer = TestAnalyzer()
    md5s = [
        MD5WithPII(md5="123", sentences=["test"], pii=create_test_pii()),
        MD5WithPII(md5="456", sentences=["test"], pii=create_test_pii())
    ]
    result = analyzer.analyze(md5s)
    assert result == "Analyzed 2 MD5s"


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not found")
def test_openai_insights_generator() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    generator = OpenAIInsightsGenerator(api_key)
    md5s = [
        MD5WithPII(md5="123", sentences=["Interested in buying a new car"], pii=create_test_pii()),
        MD5WithPII(md5="456", sentences=["Looking for auto insurance"], pii=create_test_pii())
    ]
    result = generator.analyze(md5s)
    assert isinstance(result, str)
    assert len(result.split("\n")) >= 2  # Expecting at least two insights


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not found")
def test_validated_insights_generator(bigdbm_client) -> None:
    api_key = os.getenv("OPENAI_API_KEY")

    processor = FillProcessor(bigdbm_client)
    processor.add_validator(SamePersonValidator())
    processor.add_validator(MNWValidator(), priority=2)

    generator = ValidatedInsightsGenerator(api_key, processor)
    md5s = [
        MD5WithPII(md5="123", sentences=["Interested in buying a new car"], pii=create_test_pii()),
        MD5WithPII(md5="456", sentences=["Looking for auto insurance"], pii=create_test_pii())
    ]
    result = generator.analyze(md5s)
    assert isinstance(result, str)
    assert "On validation:" in result
    assert len(result.split("\n")) >= 3  # Expecting validation insight and at least two regular insights
