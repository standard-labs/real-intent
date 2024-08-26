"""Test the Follow Up Boss deliverer."""
import pytest

import os
import random
import string
from dotenv import load_dotenv

from bigdbm.deliver.followupboss import FollowUpBossDeliverer
from bigdbm.schemas import MD5WithPII, PII, MobilePhone, Gender


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
                Email_Array=[email],
                Gender=Gender.MALE,
                Age="30",
                Children_HH="2",
                Credit_Range="Good",
                Home_Owner="Yes",
                Income_HH="100000-150000",
                Net_Worth_HH="500000-1000000",
                Marital_Status="Married",
                Occupation_Detail="Engineer",
                Veteran_HH="0",
                mobile_phones=[MobilePhone(phone="1234567890", do_not_call=False)]
            )
        )
    ]


@pytest.fixture
def followupboss_deliverer(api_key, system, system_key):
    return FollowUpBossDeliverer(api_key, system, system_key)


@pytest.mark.skipif(not os.getenv("FOLLOWUPBOSS_API_KEY"), reason="FUB API key not found")
def test_followupboss_deliverer_success(followupboss_deliverer, sample_pii_md5s):
    result = followupboss_deliverer.deliver(sample_pii_md5s)

    assert len(result) == 1
    assert "id" in result[0]
    assert result[0]["firstName"] == sample_pii_md5s[0].pii.first_name
    assert result[0]["lastName"] == sample_pii_md5s[0].pii.last_name
    assert any(email["value"] == sample_pii_md5s[0].pii.emails[0] for email in result[0]["emails"])
    assert any(phone["value"] == "1234567890" for phone in result[0]["phones"])


@pytest.mark.skipif(not os.getenv("FOLLOWUPBOSS_API_KEY"), reason="FUB API key not found")
def test_prepare_event_data(followupboss_deliverer, sample_pii_md5s):
    event_data = followupboss_deliverer._prepare_event_data(sample_pii_md5s[0])

    assert event_data["system"] == followupboss_deliverer.system
    assert event_data["person"]["firstName"] == sample_pii_md5s[0].pii.first_name
    assert event_data["person"]["lastName"] == sample_pii_md5s[0].pii.last_name
    assert event_data["person"]["emails"] == [{"value": sample_pii_md5s[0].pii.emails[0]}]
    assert event_data["person"]["phones"] == [{"value": "1234567890"}]
