"""Basic kvCORE tests, without actually integrating."""
from real_intent.deliver.kvcore import KVCoreDeliverer
from real_intent.schemas import MD5WithPII, PII


def test_kvcore_email_body(sample_pii_md5s) -> None:
    """
    Test generating the email body.

    We can assume the following values are in the email body _because_ they are
    in the sample PIIs.
    """
    deliverer = KVCoreDeliverer("", "", "", "")
    email_body: str = deliverer._email_body(sample_pii_md5s[0])

    assert "First Name" in email_body, "First Name should be in email body"
    assert "Last Name" in email_body, "Last Name should be in email body"
    assert "Email" in email_body, "Email should be in email body"
    assert "Phone" in email_body, "Phone should be in email body"
    assert "Agent Notes" in email_body, "Agent Notes should be in email body"

    # Verify address components appear in agent notes
    pii = sample_pii_md5s[0].pii
    if pii.address.strip():
        assert pii.address.strip() in email_body, "Street address should be in agent notes"
    if pii.city.strip():
        assert pii.city.strip() in email_body, "City should be in agent notes"
    if pii.state.strip():
        assert pii.state.strip() in email_body, "State should be in agent notes"
    if pii.zip_code.strip():
        assert pii.zip_code.strip() in email_body, "Zip code should be in agent notes"


def test_lead_deal_type() -> None:
    """Test the deal type prediction functionality."""
    deliverer = KVCoreDeliverer("", "", "", "")

    # Create test cases for different sentence types
    pii = PII.create_fake(seed=42)

    # Test seller detection
    seller_md5 = MD5WithPII(
        md5="seller123",
        sentences=["In-Market>Real Estate>Sellers", "Some other sentence"],
        pii=pii
    )
    assert deliverer._lead_deal_type(seller_md5) == "Seller", "Should identify as Seller"

    # Test pre-mover detection (also a seller)
    pre_mover_md5 = MD5WithPII(
        md5="premover123",
        sentences=["In-Market>Real Estate>Pre-Movers", "Some other sentence"],
        pii=pii
    )
    assert deliverer._lead_deal_type(pre_mover_md5) == "Seller", "Should identify as Seller"

    # Test buyer detection - mortgage
    buyer_md5_mortgage = MD5WithPII(
        md5="buyer123",
        sentences=["In-Market>Financial>Loans>Mortgages", "Some other sentence"],
        pii=pii
    )
    assert deliverer._lead_deal_type(buyer_md5_mortgage) == "Buyer", "Should identify as Buyer"

    # Test buyer detection - first-time home buyer
    buyer_md5_first_time = MD5WithPII(
        md5="buyer456",
        sentences=["In-Market>Real Estate>First-Time Home Buyer", "Some other sentence"],
        pii=pii
    )
    assert deliverer._lead_deal_type(buyer_md5_first_time) == "Buyer", "Should identify as Buyer"

    # Test no match
    unknown_md5 = MD5WithPII(
        md5="unknown123",
        sentences=["Some random sentence", "Another random sentence"],
        pii=pii
    )
    assert deliverer._lead_deal_type(unknown_md5) == "", "Should return empty string for no match"


def test_deal_type_in_email_body() -> None:
    """Test that deal type is included in the email body when it can be determined."""
    deliverer = KVCoreDeliverer("", "", "", "")

    # Create a test case with a seller intent
    pii = PII.create_fake(seed=42)
    seller_md5 = MD5WithPII(
        md5="seller123",
        sentences=["In-Market>Real Estate>Sellers"],
        pii=pii
    )

    email_body = deliverer._email_body(seller_md5)
    assert "Deal Type: Seller" in email_body, "Deal Type should be in email body for sellers"

    # Create a test case with no deal type
    unknown_md5 = MD5WithPII(
        md5="unknown123",
        sentences=["Some random sentence"],
        pii=pii
    )

    email_body = deliverer._email_body(unknown_md5)
    assert "Deal Type:" not in email_body, "Deal Type should not be in email body when not determined"
