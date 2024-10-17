"""Test the Fillout DNS validator."""
import pytest
import os
from dotenv import load_dotenv

from real_intent.validate.dns import FilloutDNSValidator
from real_intent.schemas import MD5WithPII

# Load environment variables from .env file
load_dotenv()

@pytest.fixture
def fillout_dns_validator():
    return FilloutDNSValidator(
        os.getenv('FILLOUT_API_KEY'),
        os.getenv('FILLOUT_DNS_FORM_ID'),
        os.getenv('FILLOUT_DNS_QUESTION_ID')
    )

@pytest.fixture
def dns_test_md5s(sample_pii_md5s):
    # Create a copy of the sample_pii_md5s and modify it
    test_md5s = sample_pii_md5s.copy()
    
    # Add a new MD5WithPII object with the email we want to test
    new_pii = test_md5s[0].pii.model_copy(deep=True)
    new_pii.emails.append("preritdas@gmail.com")
    test_md5s.append(MD5WithPII(
        md5="0123456789abcdef",
        sentences=["another test sentence"],
        pii=new_pii
    ))
    
    return test_md5s

@pytest.mark.skipif(
    not os.getenv("FILLOUT_API_KEY")
    or not os.getenv("FILLOUT_DNS_FORM_ID")
    or not os.getenv("FILLOUT_DNS_QUESTION_ID"),
    reason="Fillout API credentials not found",
)
def test_fillout_dns_validator_initialization(fillout_dns_validator):
    assert fillout_dns_validator.fillout_api_key == os.getenv('FILLOUT_API_KEY')
    assert fillout_dns_validator.fillout_form_id == os.getenv('FILLOUT_DNS_FORM_ID')
    assert fillout_dns_validator.question_id == os.getenv('FILLOUT_DNS_QUESTION_ID')

@pytest.mark.skipif(
    not os.getenv("FILLOUT_API_KEY")
    or not os.getenv("FILLOUT_DNS_FORM_ID")
    or not os.getenv("FILLOUT_DNS_QUESTION_ID"),
    reason="Fillout API credentials not found",
)
def test_fillout_api_headers(fillout_dns_validator):
    expected_headers = {
        "Authorization": f"Bearer {os.getenv('FILLOUT_API_KEY')}"
    }
    assert fillout_dns_validator.fillout_api_headers == expected_headers

@pytest.mark.skipif(
    not os.getenv("FILLOUT_API_KEY")
    or not os.getenv("FILLOUT_DNS_FORM_ID")
    or not os.getenv("FILLOUT_DNS_QUESTION_ID"),
    reason="Fillout API credentials not found",
)
def test_get_submissions(fillout_dns_validator):
    submissions = fillout_dns_validator._get_submissions()
    assert isinstance(submissions, list)
    assert len(submissions) > 0

@pytest.mark.skipif(
    not os.getenv("FILLOUT_API_KEY")
    or not os.getenv("FILLOUT_DNS_FORM_ID")
    or not os.getenv("FILLOUT_DNS_QUESTION_ID"),
    reason="Fillout API credentials not found",
)
def test_all_emails(fillout_dns_validator):
    emails = fillout_dns_validator.all_emails()
    assert isinstance(emails, set)
    assert len(emails) > 0
    assert all(isinstance(email, str) for email in emails)

@pytest.mark.skipif(
    not os.getenv("FILLOUT_API_KEY")
    or not os.getenv("FILLOUT_DNS_FORM_ID")
    or not os.getenv("FILLOUT_DNS_QUESTION_ID"),
    reason="Fillout API credentials not found",
)
def test_validate(fillout_dns_validator, dns_test_md5s):
    result = fillout_dns_validator.validate(dns_test_md5s)
    assert isinstance(result, list)
    assert len(result) == 1  # Expecting 1 out of 2 to pass validation
    assert all("preritdas@gmail.com" not in md5.pii.emails for md5 in result)
    assert result[0].md5 == dns_test_md5s[0].md5
