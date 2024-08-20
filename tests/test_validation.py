import os
from unittest.mock import patch

import pytest
from dotenv import load_dotenv

from bigdbm.schemas import MD5WithPII, PII, MobilePhone
from bigdbm.validate.email import EmailValidator, HasEmailValidator
from bigdbm.validate.phone import PhoneValidator


# Load environment variables from .env file
load_dotenv()


def create_md5_with_pii(md5: str, emails: list[str], phones: list[str]) -> MD5WithPII:
    pii_dict = {
        "Id": "test_id",
        "First_Name": "John",
        "Last_Name": "Doe",
        "Address": "123 Test St",
        "City": "Test City",
        "State": "TS",
        "Zip": "12345",
        "Email_Array": emails,
        "Gender": "Male",
        "Age": "30",
        "Children_HH": "2",
        "Credit_Range": "Good",
        "Home_Owner": "Yes",
        "Income_HH": "100000-150000",
        "Net_Worth_HH": "500000-1000000",
        "Marital_Status": "Married",
        "Occupation_Detail": "Engineer",
        "Veteran_HH": "0"
    }
    
    pii = PII.from_api_dict(pii_dict)
    pii.mobile_phones = [MobilePhone(phone=phone, do_not_call=False) for phone in phones]
    
    return MD5WithPII(md5=md5, sentences=["test sentence"], pii=pii)


def test_email_validator() -> None:
    million_verify_key = os.getenv("MILLION_VERIFY_KEY")
    if not million_verify_key:
        pytest.skip("MILLION_VERIFY_KEY not found in .env file")
    
    validator = EmailValidator(million_verify_key)
    
    md5s = [
        create_md5_with_pii("123", ["valid@example.com", "invalid@example.com"], []),
        create_md5_with_pii("456", ["another_valid@example.com"], []),
        create_md5_with_pii("789", ["invalid2@example.com"], [])
    ]
    
    with patch.object(EmailValidator, '_validate_with_retry') as mock_validate:
        mock_validate.side_effect = [True, False, True, False]
        
        result = validator.validate(md5s)
        
        assert len(result) == 3
        assert result[0].pii.emails == ["valid@example.com"]
        assert result[1].pii.emails == ["another_valid@example.com"]
        assert result[2].pii.emails == []


def test_has_email_validator() -> None:
    validator = HasEmailValidator()
    
    md5s = [
        create_md5_with_pii("123", ["valid@example.com"], []),
        create_md5_with_pii("456", [], []),
        create_md5_with_pii("789", ["another@example.com"], [])
    ]
    
    result = validator.validate(md5s)
    
    assert len(result) == 2
    assert result[0].md5 == "123"
    assert result[1].md5 == "789"


def test_phone_validator() -> None:
    numverify_key = os.getenv("NUMVERIFY_KEY")
    if not numverify_key:
        pytest.skip("NUMVERIFY_KEY not found in .env file")
    
    validator = PhoneValidator(numverify_key=numverify_key)
    
    md5s = [
        create_md5_with_pii("123", [], ["1234567890", "invalid"]),
        create_md5_with_pii("456", [], ["9876543210"]),
        create_md5_with_pii("789", [], ["invalid"])
    ]
    
    with patch.object(PhoneValidator, '_validate_phone') as mock_validate_phone:
        mock_validate_phone.side_effect = [True, False, True, False]
        
        result = validator.validate(md5s)
        
        assert len(result) == 3
        assert result[0].pii.mobile_phones[0].phone == "1234567890"
        assert len(result[0].pii.mobile_phones) == 1
        assert result[1].pii.mobile_phones[0].phone == "9876543210"
        assert len(result[2].pii.mobile_phones) == 0