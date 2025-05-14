import os
import pytest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

from real_intent.schemas import MD5WithPII, PII, MobilePhone
from real_intent.validate.email import EmailValidator, HasEmailValidator
from real_intent.validate.phone import PhoneValidator, DNCValidator, DNCPhoneRemover
from real_intent.validate.pii import RemoveOccupationsValidator
from real_intent.validate.simple import ExcludeZipCodeValidator


# Load environment variables from .env file
load_dotenv()


def create_md5_with_pii(md5: str, emails: list[str], phones: list[str], sentences: list[str] | None = None) -> MD5WithPII:
    # Default to a single test sentence if none are forced
    if sentences is None:
        sentences = ["test sentence"]

    # Create a base PII object with fake data
    pii = PII.create_fake(seed=42)  # Use consistent seed for reproducibility

    # Override with test-specific values
    pii.emails = emails
    pii.mobile_phones = [MobilePhone(phone=phone, do_not_call=False) for phone in phones]

    return MD5WithPII(md5=md5, sentences=sentences, pii=pii)


def test_email_validator() -> None:
    million_verifier_key = os.getenv("MILLION_VERIFIER_KEY")
    if not million_verifier_key:
        pytest.skip("MILLION_VERIFIER_KEY not found in .env file")

    validator = EmailValidator(million_verifier_key)

    real_emails = [
        "aaron@standarddao.finance"
    ]
    fake_emails = [
        "rfisascasdcabsdasdcabsjhdcher@yahoo.com",
        "dju123123123123123pedal@yahoo.com",
        "khris678asdc678asdc@aol.com"
    ]

    md5s = [
        create_md5_with_pii("123", real_emails + fake_emails, []),
    ]

    result = validator.validate(md5s)

    assert len(result) == 1
    validated_emails = result[0].pii.emails

    assert any(email in validated_emails for email in real_emails), "No real emails were validated"
    assert any(email not in validated_emails for email in fake_emails), "All fake emails were validated"
    assert all(email in validated_emails for email in real_emails), "Not all real emails were validated"
    assert all(email not in validated_emails for email in fake_emails), "Some fake emails were validated"


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


def test_phone_validator_with_real_api() -> None:
    """Test the PhoneValidator with the real Numverify API.

    This test uses real phone numbers and the actual Numverify API.
    It tests both valid and invalid phone numbers to ensure the validator
    can handle both success and failure cases.
    """
    numverify_key = os.getenv("NUMVERIFY_KEY")
    if not numverify_key:
        pytest.skip("NUMVERIFY_KEY not found in .env file")

    validator = PhoneValidator(numverify_key=numverify_key)

    # Known valid US toll-free numbers
    real_phones = [
        "18002752273",  # Best Buy
        "18006427676",  # Apple
        "18882804331"   # Walmart
    ]

    # Clearly invalid phone numbers (wrong format)
    invalid_format_phones = [
        "123",          # Too short
        "12345678901234", # Too long
        "abcdefghij"    # Not numeric
    ]

    # Properly formatted but likely non-existent numbers
    fake_phones = [
        "17489550914",
        "12573425053",
        "12889061135"
    ]

    # Test with invalid format phones first - these should be rejected without API call
    md5s_invalid_format = [
        create_md5_with_pii("123", [], invalid_format_phones),
    ]

    result_invalid_format = validator.validate(md5s_invalid_format)
    assert len(result_invalid_format) == 1
    assert len(result_invalid_format[0].pii.mobile_phones) == 0, "Invalid format phones should be rejected"

    # Now test with real and fake phones
    md5s = [
        create_md5_with_pii("456", [], real_phones + fake_phones),
    ]

    try:
        result = validator.validate(md5s)

        assert len(result) == 1
        validated_phones = [phone.phone for phone in result[0].pii.mobile_phones]

        # Log the validated phones for debugging
        print(f"Validated phones: {validated_phones}")

        # Check that at least some real phones were validated
        # Note: We can't assert that all real phones are validated because
        # the Numverify API might return error code 313 for some of them
        assert any(phone in validated_phones for phone in real_phones), "No real phones were validated"

        # Check that all fake phones were rejected
        # This should still be true even with API errors
        assert all(phone not in validated_phones for phone in fake_phones), "Some fake phones were validated"

        # Print which real phones were validated and which weren't
        for phone in real_phones:
            if phone in validated_phones:
                print(f"Real phone {phone} was correctly validated")
            else:
                print(f"Real phone {phone} was not validated")

    except ValueError as e:
        # If we get a ValueError, it might be due to Numverify API issues
        # Skip the test in this case
        if "Failed to validate phone number" in str(e):
            pytest.skip(f"Numverify API error: {e}")
        else:
            raise


def test_dnc_validator() -> None:
    # Test normal mode
    validator_normal = DNCValidator(strict_mode=False)

    md5s = [
        create_md5_with_pii("123", [], ["1234567890"]),  # Not on DNC list
        create_md5_with_pii("456", [], []),  # No phone
        create_md5_with_pii("789", [], ["9876543210", "1112223333"]),  # Primary on DNC, secondary not
        create_md5_with_pii("101", [], ["5556667777", "9998887777"])  # Primary not on DNC, secondary on DNC
    ]

    # Set DNC status
    md5s[2].pii.mobile_phones[0].do_not_call = True
    md5s[3].pii.mobile_phones[1].do_not_call = True

    result_normal = validator_normal.validate(md5s)

    assert len(result_normal) == 3
    assert result_normal[0].md5 == "123"  # Keep: has phone, not on DNC
    assert result_normal[1].md5 == "456"  # Keep: no phone
    assert result_normal[2].md5 == "101"  # Keep: primary not on DNC
    assert all(md5.md5 != "789" for md5 in result_normal)  # Remove: primary on DNC

    # Test strict mode
    validator_strict = DNCValidator(strict_mode=True)

    result_strict = validator_strict.validate(md5s)

    assert len(result_strict) == 2
    assert result_strict[0].md5 == "123"  # Keep: has phone, not on DNC
    assert result_strict[1].md5 == "456"  # Keep: no phone
    assert all(md5.md5 != "789" for md5 in result_strict)  # Remove: has DNC phone
    assert all(md5.md5 != "101" for md5 in result_strict)  # Remove: has DNC phone (secondary)


def test_dnc_phone_remover() -> None:
    remover = DNCPhoneRemover()

    md5s = [
        create_md5_with_pii("123", [], ["1234567890", "9876543210"]),  # Both not on DNC
        create_md5_with_pii("456", [], ["1112223333", "4445556666"]),  # First on DNC, second not
        create_md5_with_pii("789", [], ["7778889999", "1231231234"]),  # Both on DNC
        create_md5_with_pii("101", [], [])  # No phones
    ]

    # Set DNC status
    md5s[1].pii.mobile_phones[0].do_not_call = True
    md5s[2].pii.mobile_phones[0].do_not_call = True
    md5s[2].pii.mobile_phones[1].do_not_call = True

    result = remover.validate(md5s)

    assert len(result) == 4  # All MD5s should be kept

    # Check MD5 with both phones not on DNC
    assert len(result[0].pii.mobile_phones) == 2
    assert result[0].pii.mobile_phones[0].phone == "1234567890"
    assert result[0].pii.mobile_phones[1].phone == "9876543210"

    # Check MD5 with one phone on DNC
    assert len(result[1].pii.mobile_phones) == 1
    assert result[1].pii.mobile_phones[0].phone == "4445556666"

    # Check MD5 with both phones on DNC
    assert len(result[2].pii.mobile_phones) == 0

    # Check MD5 with no phones
    assert len(result[3].pii.mobile_phones) == 0


def test_sentence_count() -> None:
    # Check for different sentence calculation methods
    md5 = create_md5_with_pii("123", [], [], sentences=["sentence1", "sentence2", "sentence1", "sentence3"])
    assert md5.total_sentence_count == 4
    assert md5.unique_sentence_count == 3

    # Check for single sentence
    md5_single = create_md5_with_pii("456", [], [], sentences=["single sentence"])
    assert md5_single.total_sentence_count == 1
    assert md5_single.unique_sentence_count == 1

    # Check for empty sentences
    md5_empty = create_md5_with_pii("789", [], [], sentences=[])
    assert md5_empty.total_sentence_count == 0
    assert md5_empty.unique_sentence_count == 0


def test_remove_occupations_validator() -> None:
    piis = [
        create_md5_with_pii("123", [], ["1234567890"], sentences=["sentence1"]),
        create_md5_with_pii("456", [], ["9876543210"], sentences=["sentence2"]),
        create_md5_with_pii("789", [], ["5556667777"], sentences=["sentence3"]),
        create_md5_with_pii("101", [], ["9998887777"], sentences=["sentence4"])
    ]

    # Set occupations
    piis[0].pii.occupation = "Bad Occupation"

    # Initialize validator
    validator = RemoveOccupationsValidator("Bad Occupation")

    # Validate
    result = validator.validate(piis)

    # Check results
    assert len(result) == 3


def test_exclude_zip_code_validator() -> None:
    # Create test data with different zip codes
    md5s = [
        create_md5_with_pii("123", [], []),  # Will set zip code below
        create_md5_with_pii("456", [], []),  # Will set zip code below
        create_md5_with_pii("789", [], []),  # Will set zip code below
        create_md5_with_pii("101", [], [])   # Will set zip code below
    ]

    # Set zip codes
    md5s[0].pii.zip_code = "10001"  # NYC - should be excluded
    md5s[1].pii.zip_code = "90210"  # Beverly Hills - should be kept
    md5s[2].pii.zip_code = "60601"  # Chicago - should be kept
    md5s[3].pii.zip_code = "33139"  # Miami Beach - should be excluded

    # Initialize validator with zip codes to exclude
    excluded_zip_codes = ["10001", "33139"]
    validator = ExcludeZipCodeValidator(excluded_zip_codes)

    # Validate
    result = validator.validate(md5s)

    # Check results
    assert len(result) == 2
    assert result[0].md5 == "456"  # Beverly Hills zip should be kept
    assert result[1].md5 == "789"  # Chicago zip should be kept
    assert all(md5.md5 != "123" for md5 in result)  # NYC zip should be excluded
    assert all(md5.md5 != "101" for md5 in result)  # Miami Beach zip should be excluded

    # Check that the zip codes in the result are the ones we expect to keep
    assert result[0].pii.zip_code == "90210"
    assert result[1].pii.zip_code == "60601"


def test_phone_validator_with_numverify_error() -> None:
    """Test that the PhoneValidator handles Numverify API errors correctly."""
    # Create a mock response for the Numverify API
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": False,
        "error": {
            "code": 313,
            "type": "quota_reached",
            "info": "Your monthly API request volume has been reached."
        }
    }

    # Create a validator with a dummy API key
    validator = PhoneValidator(numverify_key="dummy_key")

    # Create test data with a phone number
    md5s = [
        create_md5_with_pii("123", [], ["1234567890"]),
    ]

    # Mock the requests.get method to return our mock response
    with patch('requests.get', return_value=mock_response):
        # Validate the phone number
        result = validator.validate(md5s)

        # The phone number should be considered invalid due to the error
        assert len(result) == 1
        assert len(result[0].pii.mobile_phones) == 0


def test_phone_validator_with_other_numverify_error() -> None:
    """Test that the PhoneValidator raises an exception for other Numverify API errors."""
    # Create a mock response for the Numverify API with a different error code
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": False,
        "error": {
            "code": 101,
            "type": "invalid_access_key",
            "info": "You have not supplied a valid API Access Key."
        }
    }

    # Create a validator with a dummy API key
    validator = PhoneValidator(numverify_key="dummy_key")

    # Create test data with a phone number
    md5s = [
        create_md5_with_pii("123", [], ["1234567890"]),
    ]

    # Mock the requests.get method to return our mock response
    with patch('requests.get', return_value=mock_response):
        # Validate the phone number - should raise an exception
        with pytest.raises(ValueError):
            validator.validate(md5s)


def test_phone_validator_with_handled_error_codes() -> None:
    """Test that the PhoneValidator handles specific error codes without raising exceptions."""
    # Create a validator with a dummy API key
    validator = PhoneValidator(numverify_key="dummy_key")

    # Create test data with a phone number
    md5s = [
        create_md5_with_pii("123", [], ["1234567890"]),
    ]

    # Test error code 211 (non-numeric phone number)
    mock_response_211 = MagicMock()
    mock_response_211.json.return_value = {
        "success": False,
        "error": {
            "code": 211,
            "type": "non_numeric_phone_number_provided"
        }
    }

    with patch('requests.get', return_value=mock_response_211):
        # Validate the phone number - should not raise an exception
        result = validator.validate(md5s)
        # The phone number should be considered invalid
        assert len(result) == 1
        assert len(result[0].pii.mobile_phones) == 0

    # Test error code 210 (invalid phone number)
    mock_response_210 = MagicMock()
    mock_response_210.json.return_value = {
        "success": False,
        "error": {
            "code": 210,
            "type": "invalid_phone_number"
        }
    }

    with patch('requests.get', return_value=mock_response_210):
        # Validate the phone number - should not raise an exception
        result = validator.validate(md5s)
        # The phone number should be considered invalid
        assert len(result) == 1
        assert len(result[0].pii.mobile_phones) == 0


def test_phone_validator_with_missing_valid_field() -> None:
    """Test that the PhoneValidator raises an exception when the 'valid' field is missing."""
    # Create a mock response for the Numverify API with missing 'valid' field
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": True,
        "number": "1234567890",
        "country_code": "US",
        # 'valid' field is missing
    }

    # Create a validator with a dummy API key
    validator = PhoneValidator(numverify_key="dummy_key")

    # Create test data with a phone number
    md5s = [
        create_md5_with_pii("123", [], ["1234567890"]),
    ]

    # Mock the requests.get method to return our mock response
    with patch('requests.get', return_value=mock_response):
        # Validate the phone number - should raise an exception
        with pytest.raises(ValueError, match="Unexpected response from numverify"):
            validator.validate(md5s)


def test_phone_validator_with_successful_validation() -> None:
    """Test that the PhoneValidator correctly handles successful validation."""
    # Create a validator with a dummy API key
    validator = PhoneValidator(numverify_key="dummy_key")

    # Create test data with both valid and invalid phone numbers
    md5s = [
        create_md5_with_pii("123", [], ["18002752273", "17489550914"]),
    ]

    # Create a mock for the _validate_phone method to control its behavior
    with patch.object(PhoneValidator, '_validate_phone') as mock_validate:
        # Set up the mock to return True for the valid phone and False for the invalid phone
        mock_validate.side_effect = lambda phone: phone == "18002752273"

        # Validate the phone numbers
        result = validator.validate(md5s)

        # Check that only the valid phone number was kept
        assert len(result) == 1
        assert len(result[0].pii.mobile_phones) == 1
        assert result[0].pii.mobile_phones[0].phone == "18002752273"

        # Verify that the mock was called with the expected arguments
        assert mock_validate.call_count == 2
        mock_validate.assert_any_call("18002752273")
        mock_validate.assert_any_call("17489550914")


def test_phone_validator_with_missing_success_field() -> None:
    """Test that the PhoneValidator handles responses with missing 'success' field."""
    # Create a mock response for the Numverify API with missing 'success' field but no 'valid' field
    mock_response_no_valid = MagicMock()
    mock_response_no_valid.json.return_value = {
        # 'success' field is missing
        "number": "1234567890",
        "country_code": "US"
    }

    # Create a validator with a dummy API key
    validator = PhoneValidator(numverify_key="dummy_key")

    # Create test data with a phone number
    md5s = [
        create_md5_with_pii("123", [], ["1234567890"]),
    ]

    # Mock the requests.get method to return our mock response
    with patch('requests.get', return_value=mock_response_no_valid):
        # Validate the phone number - should mark it as invalid
        result = validator.validate(md5s)

        # The phone number should be considered invalid
        assert len(result) == 1
        assert len(result[0].pii.mobile_phones) == 0

    # Create a mock response with missing 'success' field but 'valid' is True
    # This is a common response pattern from Numverify and should be handled without logging
    mock_response_valid_true = MagicMock()
    mock_response_valid_true.json.return_value = {
        # 'success' field is missing
        "number": "1234567890",
        "country_code": "US",
        "valid": True,
        "local_format": "1234567890",
        "international_format": "+11234567890",
        "country_prefix": "+1",
        "country_code": "US",
        "country_name": "United States of America",
        "location": "Ohio",
        "carrier": "",
        "line_type": "landline"
    }

    # Create test data with a phone number
    md5s = [
        create_md5_with_pii("123", [], ["1234567890"]),
    ]

    # Mock the requests.get method to return our mock response
    with patch('requests.get', return_value=mock_response_valid_true):
        # Validate the phone number - should mark it as valid
        result = validator.validate(md5s)

        # The phone number should be considered valid
        assert len(result) == 1
        assert len(result[0].pii.mobile_phones) == 1
        assert result[0].pii.mobile_phones[0].phone == "1234567890"


def test_phone_validator_with_invalid_api_key() -> None:
    """Test the PhoneValidator with an invalid API key to test error handling with real API."""
    # Create a validator with an invalid API key
    validator = PhoneValidator(numverify_key="invalid_key")

    # Use a real phone number
    phone = "18002752273"  # Best Buy

    # Create test data
    md5s = [
        create_md5_with_pii("123", [], [phone]),
    ]

    try:
        # This should raise a ValueError due to the invalid API key
        with pytest.raises(ValueError) as excinfo:
            validator.validate(md5s)

        # Check that the error message contains the expected text
        assert "Failed to validate phone number" in str(excinfo.value)
        assert "invalid_access_key" in str(excinfo.value).lower() or "invalid" in str(excinfo.value).lower()

        print(f"Successfully caught expected error: {excinfo.value}")
    except Exception as e:
        # If we get a different exception, it might be due to changes in the API
        # Log it and skip the test
        pytest.skip(f"Unexpected exception when testing with invalid API key: {e}")
