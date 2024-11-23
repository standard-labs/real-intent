"""Test the PII fake data generation."""
import pytest
from real_intent.schemas import PII, Gender


def test_create_fake():
    """Test creating a fake PII object."""
    # Create a fake PII object
    pii = PII.create_fake(seed=42)  # Use seed for reproducible results
    
    # Test that all required fields are present and of correct type
    assert isinstance(pii.id, str)
    assert isinstance(pii.first_name, str)
    assert isinstance(pii.last_name, str)
    assert isinstance(pii.address, str)
    assert isinstance(pii.city, str)
    assert isinstance(pii.state, str)
    assert isinstance(pii.zip_code, str)
    assert isinstance(pii.gender, Gender)
    
    # Test that numeric fields are within expected ranges
    assert 18 <= int(pii.age) <= 80  # Age should be between 18 and 80
    assert 0 <= int(pii.n_household_children) <= 5  # 0-5 children
    assert 1 <= int(pii.n_household_adults) <= 5  # 1-5 adults
    
    # Test email format
    assert len(pii.emails) > 0
    assert "@" in pii.emails[0]
    assert "." in pii.emails[0]
    
    # Test phone numbers
    assert 1 <= len(pii.mobile_phones) <= 3  # Should have 1-3 phone numbers
    for phone in pii.mobile_phones:
        assert len(phone.phone) == 10  # Should be 10 digits
        assert isinstance(phone.do_not_call, bool)
    
    # Test coordinates are within continental US
    assert 24.0 <= float(pii.latitude) <= 50.0
    assert -125.0 <= float(pii.longitude) <= -66.0


def test_reproducibility():
    """Test that using the same seed produces the same results."""
    pii1 = PII.create_fake(seed=42)
    pii2 = PII.create_fake(seed=42)
    
    assert pii1.first_name == pii2.first_name
    assert pii1.last_name == pii2.last_name
    assert pii1.address == pii2.address
    assert len(pii1.mobile_phones) == len(pii2.mobile_phones)
    for phone1, phone2 in zip(pii1.mobile_phones, pii2.mobile_phones):
        assert phone1.phone == phone2.phone
        assert phone1.do_not_call == phone2.do_not_call


def test_different_seeds():
    """Test that different seeds produce different results."""
    pii1 = PII.create_fake(seed=42)
    pii2 = PII.create_fake(seed=43)
    
    # At least some fields should be different
    assert any([
        pii1.first_name != pii2.first_name,
        pii1.last_name != pii2.last_name,
        pii1.address != pii2.address,
        len(pii1.mobile_phones) != len(pii2.mobile_phones) or
        pii1.mobile_phones[0].phone != pii2.mobile_phones[0].phone
    ])


def test_no_seed():
    """Test that not providing a seed still works."""
    pii = PII.create_fake()
    
    # Basic validation that all required fields are present
    assert pii.id.startswith("TEST_")
    assert pii.first_name
    assert pii.last_name
    assert pii.address
    assert pii.mobile_phones
    assert pii.emails
