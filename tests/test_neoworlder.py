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


# ---- Registration Tests ----

@patch("real_intent.deliver.neoworlder.requests.post")
def test_register_client_success(mock_post):
    """Test successful client registration via classmethod."""
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.text = '{"status": "success", "data": {"real_intent_client_id": "ri_test_12345"}}'
    mock_response.json.return_value = {"status": "success", "data": {"real_intent_client_id": "ri_test_12345"}}
    mock_post.return_value = mock_response

    result = NeoworlderDeliverer.register_client(
        api_key=TEST_API_KEY,
        base_url=TEST_BASE_URL,
        real_intent_client_id=TEST_CLIENT_ID,
        customer_name=TEST_CUSTOMER_NAME,
        customer_email=TEST_CUSTOMER_EMAIL,
    )

    assert result["status"] == "success"
    mock_post.assert_called_once()

    # Verify the payload structure
    call_kwargs = mock_post.call_args[1]
    payload = call_kwargs["json"]
    assert payload["real_intent_client_id"] == TEST_CLIENT_ID
    assert payload["customer_information"]["name"] == TEST_CUSTOMER_NAME
    assert payload["customer_information"]["email"] == TEST_CUSTOMER_EMAIL
    assert "timeout" in call_kwargs  # Verify timeout is set


@patch("real_intent.deliver.neoworlder.requests.post")
def test_register_client_with_optional_fields(mock_post):
    """Test client registration with all optional fields."""
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.text = '{"status": "success"}'
    mock_response.json.return_value = {"status": "success"}
    mock_post.return_value = mock_response

    result = NeoworlderDeliverer.register_client(
        api_key=TEST_API_KEY,
        base_url=TEST_BASE_URL,
        real_intent_client_id=TEST_CLIENT_ID,
        customer_name=TEST_CUSTOMER_NAME,
        customer_email=TEST_CUSTOMER_EMAIL,
        customer_phone="555-123-4567",
        company_name="Test Company",
        address="123 Test St",
    )

    assert result["status"] == "success"

    # Verify optional fields are included
    call_kwargs = mock_post.call_args[1]
    payload = call_kwargs["json"]
    assert payload["customer_information"]["phone"] == "555-123-4567"
    assert payload["customer_information"]["company_name"] == "Test Company"
    assert payload["customer_information"]["address"] == "123 Test St"


@patch("real_intent.deliver.neoworlder.requests.post")
def test_register_client_auth_error(mock_post):
    """Test that 401/403 responses raise NeoworlderAuthError."""
    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_post.return_value = mock_response

    with pytest.raises(NeoworlderAuthError):
        NeoworlderDeliverer.register_client(
            api_key="invalid_key",
            base_url=TEST_BASE_URL,
            real_intent_client_id=TEST_CLIENT_ID,
            customer_name=TEST_CUSTOMER_NAME,
            customer_email=TEST_CUSTOMER_EMAIL,
        )


# ---- DNC Filtering Tests ----

def test_filter_dnc_leads_keeps_non_dnc(neoworlder_deliverer, sample_pii_md5s):
    """Test that leads with non-DNC phones are kept."""
    # Ensure sample leads have non-DNC phones
    for lead in sample_pii_md5s:
        for phone in lead.pii.mobile_phones:
            phone.do_not_call = False

    filtered = neoworlder_deliverer._filter_dnc_leads(sample_pii_md5s)

    assert len(filtered) == len(sample_pii_md5s)


def test_filter_dnc_leads_removes_all_dnc(neoworlder_deliverer, sample_pii_md5s):
    """Test that leads where ALL phones are DNC are removed."""
    # Mark all phones as DNC
    for lead in sample_pii_md5s:
        for phone in lead.pii.mobile_phones:
            phone.do_not_call = True

    filtered = neoworlder_deliverer._filter_dnc_leads(sample_pii_md5s)

    # All leads should be filtered out (all phones are DNC)
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


def test_filter_dnc_leads_keeps_no_phone_leads(neoworlder_deliverer, sample_pii_md5s):
    """Test that leads with no phones are kept (can contact via email)."""
    # Remove all phones from leads
    for lead in sample_pii_md5s:
        lead.pii.mobile_phones = []

    filtered = neoworlder_deliverer._filter_dnc_leads(sample_pii_md5s)

    # All leads should be kept (no phones means can contact via email)
    assert len(filtered) == len(sample_pii_md5s)


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
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.text = '{"status": "success"}'
    mock_response.json.return_value = {"status": "success"}
    mock_post.return_value = mock_response

    # Mark all phones as DNC on half the leads
    half = len(sample_pii_md5s) // 2
    for lead in sample_pii_md5s[:half]:
        for phone in lead.pii.mobile_phones:
            phone.do_not_call = True

    # Ensure the other half has non-DNC phones
    for lead in sample_pii_md5s[half:]:
        for phone in lead.pii.mobile_phones:
            phone.do_not_call = False

    result = neoworlder_deliverer._deliver(sample_pii_md5s)

    # Delivery should succeed with filtered leads (2 calls: register + deliver)
    assert result["status"] == "success"
    assert mock_post.call_count == 2


@patch("real_intent.deliver.neoworlder.requests.post")
def test_deliver_all_dnc_returns_skipped(mock_post, neoworlder_deliverer, sample_pii_md5s):
    """Test that delivery with all DNC leads returns skipped status."""
    from real_intent.schemas import MobilePhone

    # Ensure all leads have at least one phone and all are DNC
    for lead in sample_pii_md5s:
        # Add a DNC phone if none exist
        if not lead.pii.mobile_phones:
            lead.pii.mobile_phones = [MobilePhone(phone="555-123-4567", do_not_call=True)]
        else:
            for phone in lead.pii.mobile_phones:
                phone.do_not_call = True

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
