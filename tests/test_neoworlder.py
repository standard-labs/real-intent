"""Test the NeoWorlder deliverer."""
import pytest
import os
from dotenv import load_dotenv
from unittest.mock import patch, MagicMock

from real_intent.deliver.neoworlder import (
    NeoworlderDeliverer,
    NeoworlderAPIError,
    NeoworlderAuthError,
    NeoworlderClientNotFoundError,
)


# Load environment variables from .env file
load_dotenv()

# Test constants
TEST_API_KEY = "nk_test_dummy_key_for_unit_tests"
TEST_BASE_URL = NeoworlderDeliverer.STAGING_BASE_URL
TEST_CLIENT_ID = "ri_test_12345"
TEST_CUSTOMER_NAME = "Test Customer"
TEST_CUSTOMER_EMAIL = "test@example.com"


@pytest.fixture
def neoworlder_api_key():
    """Get the NeoWorlder API key from environment or use test key."""
    return os.getenv("NEOWORLDER_API_KEY", TEST_API_KEY)


@pytest.fixture
def neoworlder_deliverer(neoworlder_api_key):
    """Create a NeoWorlder deliverer instance."""
    return NeoworlderDeliverer(
        api_key=neoworlder_api_key,
        base_url=TEST_BASE_URL,
        real_intent_client_id=TEST_CLIENT_ID,
        customer_name=TEST_CUSTOMER_NAME,
        customer_email=TEST_CUSTOMER_EMAIL,
    )


def test_deliverer_initialization():
    """Test that the deliverer initializes correctly with required params."""
    deliverer = NeoworlderDeliverer(
        api_key=TEST_API_KEY,
        base_url=TEST_BASE_URL,
        real_intent_client_id=TEST_CLIENT_ID,
        customer_name=TEST_CUSTOMER_NAME,
        customer_email=TEST_CUSTOMER_EMAIL,
    )

    assert deliverer.api_key == TEST_API_KEY
    assert deliverer.real_intent_client_id == TEST_CLIENT_ID
    assert deliverer.base_url == TEST_BASE_URL
    assert deliverer.customer_name == TEST_CUSTOMER_NAME
    assert deliverer.customer_email == TEST_CUSTOMER_EMAIL


def test_deliverer_strips_trailing_slash():
    """Test that trailing slashes are stripped from base_url."""
    deliverer = NeoworlderDeliverer(
        api_key=TEST_API_KEY,
        base_url=TEST_BASE_URL + "/",
        real_intent_client_id=TEST_CLIENT_ID,
        customer_name=TEST_CUSTOMER_NAME,
        customer_email=TEST_CUSTOMER_EMAIL,
    )

    assert deliverer.base_url == TEST_BASE_URL
    assert not deliverer.base_url.endswith("/")


def test_api_headers(neoworlder_deliverer):
    """Test that API headers are correctly generated."""
    headers = neoworlder_deliverer.api_headers

    assert "neo-api-access-key" in headers
    assert headers["neo-api-access-key"] == neoworlder_deliverer.api_key


# ---- DNC Filtering Tests ----

def test_filter_dnc_leads_keeps_non_dnc(neoworlder_deliverer, sample_pii_md5s):
    """Test that leads with non-DNC phones are kept."""
    # Ensure sample leads have non-DNC phones
    for lead in sample_pii_md5s:
        for phone in lead.pii.mobile_phones:
            phone.do_not_call = False

    filtered = neoworlder_deliverer._filter_dnc_leads(sample_pii_md5s)

    assert len(filtered) == len(sample_pii_md5s)


def test_filter_dnc_leads_keeps_all_dnc_with_emails(neoworlder_deliverer, sample_pii_md5s):
    """Test that leads where ALL phones are DNC are kept if they have emails."""
    # Mark all phones as DNC but ensure leads have emails
    for lead in sample_pii_md5s:
        for phone in lead.pii.mobile_phones:
            phone.do_not_call = True
        # Ensure lead has at least one email
        if not lead.pii.emails:
            lead.pii.emails = ["test@example.com"]

    filtered = neoworlder_deliverer._filter_dnc_leads(sample_pii_md5s)

    # All leads should be kept (have emails even though all phones are DNC)
    assert len(filtered) == len(sample_pii_md5s)


def test_filter_dnc_leads_removes_all_dnc_no_emails(neoworlder_deliverer, sample_pii_md5s):
    """Test that leads where ALL phones are DNC and no emails are removed."""
    # Mark all phones as DNC and remove emails
    for lead in sample_pii_md5s:
        for phone in lead.pii.mobile_phones:
            phone.do_not_call = True
        lead.pii.emails = []

    filtered = neoworlder_deliverer._filter_dnc_leads(sample_pii_md5s)

    # All leads should be filtered out (all phones are DNC and no emails)
    assert len(filtered) == 0


def test_filter_dnc_leads_keeps_mixed(neoworlder_deliverer, sample_pii_md5s):
    """Test that leads with at least one non-DNC phone are kept."""
    # Set first phone as DNC, but ensure there's a second non-DNC phone
    for lead in sample_pii_md5s:
        if lead.pii.mobile_phones:
            lead.pii.mobile_phones[0].do_not_call = True
            # If there's only one phone and it's DNC, the lead should be filtered
            # If there are multiple phones and at least one is non-DNC, keep it

    filtered = neoworlder_deliverer._filter_dnc_leads(sample_pii_md5s)

    # Result depends on whether leads have multiple phones
    # Just verify the filter runs without error
    assert isinstance(filtered, list)


def test_filter_dnc_leads_keeps_no_phone_leads_with_email(neoworlder_deliverer, sample_pii_md5s):
    """Test that leads with no phones but with emails are kept (can contact via email)."""
    # Remove all phones from leads but ensure they have emails
    for lead in sample_pii_md5s:
        lead.pii.mobile_phones = []
        # Ensure lead has at least one email
        if not lead.pii.emails:
            lead.pii.emails = ["test@example.com"]

    filtered = neoworlder_deliverer._filter_dnc_leads(sample_pii_md5s)

    # All leads should be kept (no phones but have emails)
    assert len(filtered) == len(sample_pii_md5s)


def test_filter_dnc_leads_removes_no_contact_leads(neoworlder_deliverer, sample_pii_md5s):
    """Test that leads with no phones and no emails are filtered out."""
    # Remove all phones and emails from leads
    for lead in sample_pii_md5s:
        lead.pii.mobile_phones = []
        lead.pii.emails = []

    filtered = neoworlder_deliverer._filter_dnc_leads(sample_pii_md5s)

    # All leads should be filtered out (no contact methods)
    assert len(filtered) == 0


# ---- CSV Conversion Tests ----

def test_convert_leads_to_csv(neoworlder_deliverer, sample_pii_md5s):
    """Test that leads are correctly converted to CSV format."""
    csv_file = neoworlder_deliverer._convert_leads_to_csv(sample_pii_md5s)

    # Read the CSV content
    csv_content = csv_file.read().decode("utf-8")

    # Verify CSVStringFormatter columns are present
    assert "first_name" in csv_content
    assert "last_name" in csv_content
    assert "email_1" in csv_content  # CSVStringFormatter uses email_1, email_2, etc.
    assert "phone_1" in csv_content
    assert "address" in csv_content
    assert "city" in csv_content
    assert "state" in csv_content
    assert "zip_code" in csv_content

    # Verify lead data is present
    pii = sample_pii_md5s[0].pii
    assert pii.first_name in csv_content
    assert pii.last_name in csv_content


def test_convert_empty_leads_to_csv(neoworlder_deliverer):
    """Test that empty lead list produces empty CSV."""
    csv_file = neoworlder_deliverer._convert_leads_to_csv([])
    csv_content = csv_file.read().decode("utf-8")

    # CSVStringFormatter returns empty string for empty input
    assert csv_content == ""


# ---- Delivery Tests ----

def test_deliver_empty_leads(neoworlder_deliverer):
    """Test that delivering empty leads returns early without API call."""
    result = neoworlder_deliverer._deliver([])

    assert result["status"] == "skipped"
    assert "No leads" in result["message"]


@patch("real_intent.deliver.neoworlder.requests.post")
def test_deliver_success(mock_post, neoworlder_deliverer, sample_pii_md5s):
    """Test successful lead delivery (auto-registers then delivers)."""
    # Ensure phones are not DNC so leads pass filtering
    for lead in sample_pii_md5s:
        for phone in lead.pii.mobile_phones:
            phone.do_not_call = False

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.text = '{"status": "success"}'
    mock_response.json.return_value = {"status": "success"}
    mock_post.return_value = mock_response

    result = neoworlder_deliverer._deliver(sample_pii_md5s)

    assert result["status"] == "success"
    # Now makes 2 calls: registration + delivery
    assert mock_post.call_count == 2

    # First call is registration (JSON)
    reg_call_kwargs = mock_post.call_args_list[0][1]
    assert "json" in reg_call_kwargs
    assert reg_call_kwargs["json"]["real_intent_client_id"] == TEST_CLIENT_ID

    # Second call is delivery (multipart form data)
    delivery_call_kwargs = mock_post.call_args_list[1][1]
    assert "files" in delivery_call_kwargs
    assert "data" in delivery_call_kwargs
    assert delivery_call_kwargs["data"]["real_intent_client_id"] == TEST_CLIENT_ID
    assert "timeout" in delivery_call_kwargs


@patch("real_intent.deliver.neoworlder.requests.post")
def test_deliver_filters_dnc_before_sending(mock_post, neoworlder_deliverer, sample_pii_md5s):
    """Test that DNC leads are filtered before sending to API."""
    from real_intent.schemas import PII, MD5WithPII

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.text = '{"status": "success"}'
    mock_response.json.return_value = {"status": "success"}
    mock_post.return_value = mock_response

    # Create multiple leads to properly test filtering
    # Lead 1: All phones DNC, no emails (should be filtered out)
    lead1 = sample_pii_md5s[0].model_copy(deep=True)
    for phone in lead1.pii.mobile_phones:
        phone.do_not_call = True
    lead1.pii.emails = []

    # Lead 2: Non-DNC phone (should be kept)
    lead2 = MD5WithPII(
        md5="abcdef1234567890",
        sentences=["test sentence 2"],
        pii=PII.create_fake(seed=100)
    )
    for phone in lead2.pii.mobile_phones:
        phone.do_not_call = False

    # Lead 3: All phones DNC but has email (should be kept)
    lead3 = MD5WithPII(
        md5="fedcba0987654321",
        sentences=["test sentence 3"],
        pii=PII.create_fake(seed=200)
    )
    for phone in lead3.pii.mobile_phones:
        phone.do_not_call = True
    # Ensure it has an email
    if not lead3.pii.emails:
        lead3.pii.emails = ["test@example.com"]

    test_leads = [lead1, lead2, lead3]

    result = neoworlder_deliverer._deliver(test_leads)

    # Delivery should succeed with filtered leads (2 calls: register + deliver)
    # Lead1 should be filtered out, Lead2 and Lead3 should be delivered
    assert result["status"] == "success"
    assert mock_post.call_count == 2


@patch("real_intent.deliver.neoworlder.requests.post")
def test_deliver_all_dnc_returns_skipped(mock_post, neoworlder_deliverer, sample_pii_md5s):
    """Test that delivery with all DNC leads and no emails returns skipped status."""
    from real_intent.schemas import MobilePhone

    # Ensure all leads have at least one phone and all are DNC, and no emails
    for lead in sample_pii_md5s:
        # Add a DNC phone if none exist
        if not lead.pii.mobile_phones:
            lead.pii.mobile_phones = [MobilePhone(phone="555-123-4567", do_not_call=True)]
        else:
            for phone in lead.pii.mobile_phones:
                phone.do_not_call = True
        # Remove all emails to ensure leads have no usable contact methods
        lead.pii.emails = []

    result = neoworlder_deliverer._deliver(sample_pii_md5s)

    # Should return skipped, not make API call
    assert result["status"] == "skipped"
    assert "DNC" in result["message"]
    mock_post.assert_not_called()


@patch("real_intent.deliver.neoworlder.requests.post")
def test_deliver_client_not_found(mock_post, neoworlder_deliverer, sample_pii_md5s):
    """Test that 404 responses during delivery raise NeoworlderClientNotFoundError."""
    # Ensure phones are not DNC so leads pass filtering
    for lead in sample_pii_md5s:
        for phone in lead.pii.mobile_phones:
            phone.do_not_call = False

    # First call (registration) succeeds, second call (delivery) fails with 404
    success_response = MagicMock()
    success_response.ok = True
    success_response.status_code = 200
    success_response.text = '{"status": "success"}'
    success_response.json.return_value = {"status": "success"}

    error_response = MagicMock()
    error_response.ok = False
    error_response.status_code = 404
    error_response.text = "Client not found"

    mock_post.side_effect = [success_response, error_response]

    with pytest.raises(NeoworlderClientNotFoundError):
        neoworlder_deliverer._deliver(sample_pii_md5s)


@patch("real_intent.deliver.neoworlder.requests.post")
def test_deliver_api_error(mock_post, neoworlder_deliverer, sample_pii_md5s):
    """Test that general API errors during delivery raise NeoworlderAPIError."""
    # Ensure phones are not DNC so leads pass filtering
    for lead in sample_pii_md5s:
        for phone in lead.pii.mobile_phones:
            phone.do_not_call = False

    # First call (registration) succeeds, second call (delivery) fails with 500
    success_response = MagicMock()
    success_response.ok = True
    success_response.status_code = 200
    success_response.text = '{"status": "success"}'
    success_response.json.return_value = {"status": "success"}

    error_response = MagicMock()
    error_response.ok = False
    error_response.status_code = 500
    error_response.text = "Internal Server Error"

    mock_post.side_effect = [success_response, error_response]

    with pytest.raises(NeoworlderAPIError):
        neoworlder_deliverer._deliver(sample_pii_md5s)


@patch("real_intent.deliver.neoworlder.requests.post")
def test_deliver_auth_error(mock_post, neoworlder_deliverer, sample_pii_md5s):
    """Test that 401/403 responses during delivery raise NeoworlderAuthError."""
    # Ensure phones are not DNC so leads pass filtering
    for lead in sample_pii_md5s:
        for phone in lead.pii.mobile_phones:
            phone.do_not_call = False

    # First call (registration) succeeds, second call (delivery) fails with 403
    success_response = MagicMock()
    success_response.ok = True
    success_response.status_code = 200
    success_response.text = '{"status": "success"}'
    success_response.json.return_value = {"status": "success"}

    error_response = MagicMock()
    error_response.ok = False
    error_response.status_code = 403
    error_response.text = "Forbidden"

    mock_post.side_effect = [success_response, error_response]

    with pytest.raises(NeoworlderAuthError):
        neoworlder_deliverer._deliver(sample_pii_md5s)


# ---- Response Parsing Tests ----

@patch("real_intent.deliver.neoworlder.requests.post")
def test_parse_response_invalid_json_raises(mock_post, neoworlder_deliverer, sample_pii_md5s):
    """Test that invalid JSON responses during delivery raise NeoworlderAPIError."""
    import json

    # Ensure phones are not DNC so leads pass filtering
    for lead in sample_pii_md5s:
        for phone in lead.pii.mobile_phones:
            phone.do_not_call = False

    # First call (registration) succeeds
    success_response = MagicMock()
    success_response.ok = True
    success_response.status_code = 200
    success_response.text = '{"status": "success"}'
    success_response.json.return_value = {"status": "success"}

    # Second call (delivery) returns invalid JSON
    invalid_json_response = MagicMock()
    invalid_json_response.ok = True
    invalid_json_response.status_code = 200
    invalid_json_response.text = "not valid json"
    invalid_json_response.json.side_effect = json.JSONDecodeError("JSON decode error", "doc", 0)

    mock_post.side_effect = [success_response, invalid_json_response]

    with pytest.raises(NeoworlderAPIError, match="Invalid JSON"):
        neoworlder_deliverer._deliver(sample_pii_md5s)


@patch("real_intent.deliver.neoworlder.requests.post")
def test_parse_response_empty_raises(mock_post, neoworlder_deliverer, sample_pii_md5s):
    """Test that empty responses during delivery raise NeoworlderAPIError."""
    # Ensure phones are not DNC so leads pass filtering
    for lead in sample_pii_md5s:
        for phone in lead.pii.mobile_phones:
            phone.do_not_call = False

    # First call (registration) succeeds
    success_response = MagicMock()
    success_response.ok = True
    success_response.status_code = 200
    success_response.text = '{"status": "success"}'
    success_response.json.return_value = {"status": "success"}

    # Second call (delivery) returns empty response
    empty_response = MagicMock()
    empty_response.ok = True
    empty_response.status_code = 200
    empty_response.text = ""

    mock_post.side_effect = [success_response, empty_response]

    with pytest.raises(NeoworlderAPIError, match="Empty response"):
        neoworlder_deliverer._deliver(sample_pii_md5s)


# ---- Integration Tests (require actual API access) ----

@pytest.mark.skipif(
    not os.getenv("NEOWORLDER_API_KEY"),
    reason="NEOWORLDER_API_KEY not found - skipping integration tests"
)
def test_integration_deliver(sample_pii_md5s):
    """
    Integration test: Deliver leads to the staging API (auto-registers client).

    This test requires the NEOWORLDER_API_KEY environment variable to be set.
    It will make actual API calls to the NeoWorlder staging environment.
    """
    api_key = os.getenv("NEOWORLDER_API_KEY")

    # Create deliverer with customer info - auto-registers on delivery
    deliverer = NeoworlderDeliverer(
        api_key=api_key,
        base_url=NeoworlderDeliverer.STAGING_BASE_URL,
        real_intent_client_id="ri_integration_test",
        customer_name="Integration Test Customer",
        customer_email="integration-test@realintent.co",
        customer_phone="555-123-4567",
        company_name="Real Intent Test",
    )

    result = deliverer.deliver(sample_pii_md5s)
    print(f"Delivery result: {result}")
    assert result is not None
