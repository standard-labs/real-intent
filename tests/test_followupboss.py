"""Test the Follow Up Boss deliverer."""
import pytest

import os
import random
import string
from dotenv import load_dotenv

from real_intent.deliver.followupboss import FollowUpBossDeliverer
from real_intent.deliver.followupboss.ai_fields import AIFollowUpBossDeliverer
from real_intent.schemas import MD5WithPII, PII, MobilePhone, Gender


# Load environment variables from .env file
load_dotenv()


def generate_random_name(length=6):
    """Generate a random name of given length."""
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length)).capitalize()


@pytest.fixture
def api_key():
    return os.getenv('FOLLOWUPBOSS_API_KEY')


@pytest.fixture
def system():
    return os.getenv('FOLLOWUPBOSS_SYSTEM')


@pytest.fixture
def system_key():
    return os.getenv('FOLLOWUPBOSS_SYSTEM_KEY')


@pytest.fixture
def openai_api_key():
    return os.getenv('OPENAI_API_KEY')


@pytest.fixture
def sample_pii_md5s():
    first_name = generate_random_name()
    last_name = generate_random_name()
    email = f"{first_name.lower()}.{last_name.lower()}@example.com"
    return [
        MD5WithPII(
            md5="1234567890abcdef",
            sentences=["test sentence"],
            pii=PII(
                Id="test_id",
                First_Name=first_name,
                Last_Name=last_name,
                Address="123 Test St",
                City="Test City",
                State="TS",
                Zip="12345",
                Zip4="2224",
                Fips_State_Code="001",
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
                Email_Array=[email],
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
                Health_Beauty_Products="1",
                Cosmetics="1",
                Jewelry="1",
                Investment_Type="1",
                Investments="1",
                Pet_Owner="1",
                Pets_Affinity="1",
                Health_Affinity="1",
                Diet_Affinity="1",
                Fitness_Affinity="1",
                Outdoors_Affinity="1",
                Boating_Sailing_Affinity="1",
                Camping_Hiking_Climbing_Affinity="1",
                Fishing_Affinity="1",
                Hunting_Affinity="1",
                Aerobics="1",
                NASCAR="1",
                Scuba="1",
                Weight_Lifting="1",
                Healthy_Living_Interest="1",
                Motor_Racing="1",
                Travel_Foreign="1",
                Self_Improvement="1",
                Walking="1",
                Fitness="1",
                Ethnicity_Detail="Caucasian",
                Ethnic_Group="Caucasian",
            )
        )
    ]


@pytest.fixture
def followupboss_deliverer(api_key, system, system_key):
    return FollowUpBossDeliverer(api_key, system, system_key)


@pytest.fixture
def ai_followupboss_deliverer(api_key, system, system_key, openai_api_key):
    return AIFollowUpBossDeliverer(api_key, system, system_key, openai_api_key)


@pytest.mark.skipif(not os.getenv("FOLLOWUPBOSS_API_KEY"), reason="FUB API key not found")
def test_followupboss_deliverer_success(followupboss_deliverer, sample_pii_md5s):
    """
    Test the successful delivery of PII data using the FollowUpBossDeliverer, including tag functionality.

    This test verifies that:
    1. The deliverer successfully sends the PII data to Follow Up Boss.
    2. The response contains the expected data (id, first name, last name, email, phone).
    3. The delivered data matches the input sample PII data.
    4. The tags are correctly included in the delivered data.

    Args:
        followupboss_deliverer (FollowUpBossDeliverer): The FollowUpBossDeliverer instance.
        sample_pii_md5s (list): A list containing a sample MD5WithPII object.

    Raises:
        AssertionError: If any of the assertions fail, indicating that the delivery was not successful,
                        the returned data does not match the expected values, or the tags are not correctly included.
    """
    # Add tags to the existing deliverer
    tags = ["Test Tag 1", "Test Tag 2"]
    followupboss_deliverer.tags = tags

    # Test that tags are included in the prepared event data
    event_data = followupboss_deliverer._prepare_event_data(sample_pii_md5s[0])
    assert "tags" in event_data["person"], "Tags not found in prepared event data"
    assert set(event_data["person"]["tags"]) == set(tags), "Prepared event data does not contain the correct tags"

    # Test delivery and verify tags in the result
    result = followupboss_deliverer.deliver(sample_pii_md5s)

    assert len(result) == 1
    assert "id" in result[0]
    assert result[0]["firstName"] == sample_pii_md5s[0].pii.first_name
    assert result[0]["lastName"] == sample_pii_md5s[0].pii.last_name
    assert any(email["value"] == sample_pii_md5s[0].pii.emails[0] for email in result[0]["emails"])
    assert any(phone["value"] == "1234567890" for phone in result[0]["phones"])

    # Verify tags in the delivered data
    assert "tags" in result[0], "Tags not found in delivered person data"
    assert set(result[0]["tags"]) == set(tags), "Delivered person data does not contain the correct tags"


@pytest.mark.skipif(not os.getenv("FOLLOWUPBOSS_API_KEY"), reason="FUB API key not found")
def test_prepare_event_data(followupboss_deliverer, sample_pii_md5s):
    """
    Test the _prepare_event_data method of the FollowUpBossDeliverer.

    This test verifies that:
    1. The method correctly prepares the event data from the input PII data.
    2. The prepared event data contains the correct system information.
    3. The person data in the event includes the correct first name, last name, email, and phone number.

    Args:
        followupboss_deliverer (FollowUpBossDeliverer): The FollowUpBossDeliverer instance.
        sample_pii_md5s (list): A list containing a sample MD5WithPII object.

    Raises:
        AssertionError: If any of the assertions fail, indicating that the event data was not prepared correctly
                        or does not contain the expected information.
    """
    event_data = followupboss_deliverer._prepare_event_data(sample_pii_md5s[0])

    assert event_data["system"] == followupboss_deliverer.system
    assert event_data["person"]["firstName"] == sample_pii_md5s[0].pii.first_name
    assert event_data["person"]["lastName"] == sample_pii_md5s[0].pii.last_name
    assert event_data["person"]["emails"] == [{"value": sample_pii_md5s[0].pii.emails[0]}]
    assert event_data["person"]["phones"] == [{"value": "1234567890"}]


@pytest.mark.skipif(not os.getenv("FOLLOWUPBOSS_API_KEY") or not os.getenv("OPENAI_API_KEY"), reason="FUB API key or OpenAI API key not found")
def test_ai_followupboss_deliverer_success(ai_followupboss_deliverer, sample_pii_md5s):
    """
    Test the successful delivery of PII data using the AIFollowUpBossDeliverer.

    This test verifies that:
    1. The AI-powered deliverer successfully sends the PII data to Follow Up Boss.
    2. The response contains the expected basic data (id, first name, last name, email, phone).
    3. The AI has added the "Net Worth" custom field to the person data.
    4. The "Net Worth" value is correctly mapped from the PII data.
    5. The AI did not fall back to the non-AI method.

    Args:
        ai_followupboss_deliverer (AIFollowUpBossDeliverer): The AIFollowUpBossDeliverer instance.
        sample_pii_md5s (list): A list containing a sample MD5WithPII object.

    Raises:
        AssertionError: If any of the assertions fail, indicating that the AI-powered delivery was not successful,
                        the returned data does not match the expected values, the "Net Worth" field was not added,
                        or the AI fell back to the non-AI method.
    """
    result = ai_followupboss_deliverer.deliver(sample_pii_md5s)

    assert len(result) == 1
    assert "id" in result[0]
    assert result[0]["firstName"] == sample_pii_md5s[0].pii.first_name
    assert result[0]["lastName"] == sample_pii_md5s[0].pii.last_name
    assert any(email["value"] == sample_pii_md5s[0].pii.emails[0] for email in result[0]["emails"])
    assert any(phone["value"] == "1234567890" for phone in result[0]["phones"])

    # Check if the "Net Worth" custom field was added by the AI
    custom_fields = ai_followupboss_deliverer._get_custom_fields()
    event_data = ai_followupboss_deliverer._prepare_event_data(sample_pii_md5s[0])
    
    net_worth_field = next((field for field in custom_fields if field.label == "Net Worth"), None)
    assert net_worth_field is not None, "Net Worth custom field not found"
    
    assert net_worth_field.name in event_data["person"], "Net Worth field not added to person data"
    assert event_data["person"][net_worth_field.name] == sample_pii_md5s[0].pii.household_net_worth, "Net Worth value not correctly mapped"

    # Check that the AI didn't fall back to the non-AI method
    assert len(event_data["person"]) > 4, "AI seems to have fallen back to non-AI method"


@pytest.mark.skipif(
    not os.getenv("FOLLOWUPBOSS_API_KEY")
    or not os.getenv("FOLLOWUPBOSS_SYSTEM")
    or not os.getenv("FOLLOWUPBOSS_SYSTEM_KEY")
    or not os.getenv("OPENAI_API_KEY"),
    reason="FUB API keys or OpenAI API key not found",
)
def test_ai_followupboss_credential_validation(api_key, system, system_key, openai_api_key):
    # Test valid credentials and ensure that they work correctly
    AIFollowUpBossDeliverer(api_key, system, system_key, openai_api_key)

    # Test invalid credentials and ensure that they don't throw exception
    with pytest.raises(ValueError):
        AIFollowUpBossDeliverer("invalid_api_key", system, system_key, openai_api_key)


@pytest.mark.skipif(
    not os.getenv("FOLLOWUPBOSS_API_KEY")
    or not os.getenv("FOLLOWUPBOSS_SYSTEM")
    or not os.getenv("FOLLOWUPBOSS_SYSTEM_KEY"),
    reason="FUB API keys not found",
)
def test_vanilla_followupboss_credential_validation(api_key, system, system_key):
    # Test valid credentials and ensure that they work correctly
    FollowUpBossDeliverer(api_key, system, system_key)

    # Test invalid credentials and ensure that they don't throw exception
    with pytest.raises(ValueError):
        FollowUpBossDeliverer("invalid_api_key", system, system_key)
