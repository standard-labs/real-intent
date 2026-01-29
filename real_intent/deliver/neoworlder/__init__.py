"""Deliverer for NeoWorlder AI lead nurturing platform."""
import io
import json
import requests
from typing import Any

from real_intent.deliver.base import BaseOutputDeliverer
from real_intent.deliver.csv import CSVStringFormatter
from real_intent.schemas import MD5WithPII
from real_intent.internal_logging import log
from real_intent.deliver.utils import rate_limited


# ---- Constants ----

TIMEOUT_SECONDS = 30
MAX_RESPONSE_LOG_LENGTH = 200  # Maximum characters to log from response bodies


# ---- Helper Functions ----

def _truncate_response_body(response_body: str, max_length: int = MAX_RESPONSE_LOG_LENGTH) -> str:
    """
    Truncate response body for safe logging to prevent leaking sensitive data.

    Args:
        response_body: The full response body text.
        max_length: Maximum number of characters to include.

    Returns:
        Truncated response body with ellipsis if truncated.
    """
    if len(response_body) <= max_length:
        return response_body
    return response_body[:max_length] + "... [truncated]"


# ---- Exceptions ----

class NeoworlderAPIError(Exception):
    """Base exception for NeoWorlder API errors."""
    def __init__(self, message: str, status_code: int | None = None, response_body: str | None = None):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)


class NeoworlderAuthError(NeoworlderAPIError):
    """Raised when authentication fails (401/403) during API operations."""
    pass


class NeoworlderClientNotFoundError(NeoworlderAPIError):
    """Raised when the Real Intent client is not found on NeoWorlder."""
    pass


# ---- Deliverer ----

class NeoworlderDeliverer(BaseOutputDeliverer):
    """
    Delivers leads to NeoWorlder for autonomous AI-powered nurturing.

    NeoWorlder handles lead communication via AI personas until leads are
    ready to convert, at which point they notify the real estate agent.

    Usage:
        Create a deliverer with customer info and call `deliver()`. The client
        is automatically registered before each delivery (idempotent operation).

    Example:
        deliverer = NeoworlderDeliverer(
            api_key="...",
            base_url=NeoworlderDeliverer.STAGING_BASE_URL,
            real_intent_client_id="ri_12345",
            customer_name="John Doe",
            customer_email="john@example.com",
        )
        deliverer.deliver(leads)  # Auto-registers client, then delivers

    Note:
        The `base_url` parameter is required - there is no default to prevent
        accidentally sending data to the wrong environment (staging vs production).
    """

    # URL constants for reference - no default to force explicit choice
    STAGING_BASE_URL = "https://public-api.staging.neoworlder.com"
    # PRODUCTION_BASE_URL = "https://public-api.neoworlder.com"  # Update when available

    def __init__(
        self,
        api_key: str,
        base_url: str,
        real_intent_client_id: str,
        customer_name: str,
        customer_email: str,
        customer_phone: str = "",
        company_name: str = "",
        address: str = "",
    ):
        """
        Initialize the NeoWorlder deliverer.

        Args:
            api_key: NeoWorlder API key (neo-api-access-key).
            base_url: NeoWorlder API base URL (use STAGING_BASE_URL or production URL).
            real_intent_client_id: Unique identifier for the Real Intent client (e.g., "ri_12345").
            customer_name: Customer's full name (required).
            customer_email: Customer's email address (required).
            customer_phone: Customer's phone number (optional).
            company_name: Company name (optional).
            address: Customer address (optional).
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.real_intent_client_id = real_intent_client_id
        self.customer_name = customer_name
        self.customer_email = customer_email
        self.customer_phone = customer_phone
        self.company_name = company_name
        self.address = address

    @property
    def api_headers(self) -> dict[str, str]:
        """Generate the API headers for NeoWorlder requests."""
        return {
            "neo-api-access-key": self.api_key,
        }

    @rate_limited(crm="NeoWorlder")
    def _register_client(self) -> dict[str, Any]:
        """
        Register or update the client on NeoWorlder using stored customer info.

        This is called automatically at the start of each delivery.
        The endpoint is idempotent - calling it multiple times is safe.

        Returns:
            dict: Response from the NeoWorlder API.

        Raises:
            NeoworlderAuthError: If authentication fails.
            NeoworlderAPIError: If the API request fails.
        """
        url = f"{self.base_url}/api/v1/external-access/create-or-update-real-intent-client"

        payload = {
            "real_intent_client_id": self.real_intent_client_id,
            "customer_information": {
                "name": self.customer_name,
                "email": self.customer_email,
                "phone": self.customer_phone or "",
                "company_name": self.company_name or "",
                "address": self.address or "",
            }
        }

        headers = {
            "neo-api-access-key": self.api_key,
            "Content-Type": "application/json",
        }

        log("debug", f"Registering/updating NeoWorlder client: {self.real_intent_client_id}")

        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT_SECONDS)

        log("trace", f"Raw response: {_truncate_response_body(response.text)}, status_code: {response.status_code}")

        self._handle_response_errors(response, "register_client")

        log("info", f"Successfully registered/updated NeoWorlder client: {self.real_intent_client_id}")
        return self._parse_response(response)

    def _filter_dnc_leads(self, pii_md5s: list[MD5WithPII]) -> list[MD5WithPII]:
        """
        Filter out leads with no usable contact methods.

        Leads are kept if they have at least one non-DNC phone OR at least one email.
        Leads are filtered out only if they have no usable contact method (all phones
        are DNC and no emails, or no phones and no emails).

        Args:
            pii_md5s: List of leads with PII data.

        Returns:
            list[MD5WithPII]: Filtered list with only contactable leads.
        """
        filtered: list[MD5WithPII] = []

        for lead in pii_md5s:
            phones = lead.pii.mobile_phones
            emails = lead.pii.emails

            has_usable_phone = phones and any(not phone.do_not_call for phone in phones)
            has_email = bool(emails)

            # Keep lead if it has at least one non-DNC phone OR at least one email
            if has_usable_phone or has_email:
                filtered.append(lead)
            else:
                # Filter out leads with no usable contact methods
                if phones:
                    log("debug", f"Filtering out lead {lead.md5} - all phones are DNC and no emails")
                else:
                    log("debug", f"Filtering out lead {lead.md5} - no phones and no emails")

        removed_count = len(pii_md5s) - len(filtered)
        if removed_count > 0:
            log("info", f"Filtered out {removed_count} leads (no usable contact methods)")

        return filtered

    def _convert_leads_to_csv(self, pii_md5s: list[MD5WithPII]) -> io.BytesIO:
        """
        Convert a list of MD5WithPII leads to a CSV file in memory.

        Uses the standard CSVStringFormatter for consistent output format
        with all emails, phones, and detailed PII fields.

        Args:
            pii_md5s: List of leads with PII data.

        Returns:
            BytesIO: In-memory CSV file ready for upload.
        """
        csv_string = CSVStringFormatter().deliver(pii_md5s)
        bytes_output = io.BytesIO(csv_string.encode("utf-8"))
        bytes_output.seek(0)

        log("debug", f"Converted {len(pii_md5s)} leads to CSV ({bytes_output.getbuffer().nbytes} bytes)")
        return bytes_output

    @rate_limited(crm="NeoWorlder")
    def _deliver(self, pii_md5s: list[MD5WithPII]) -> dict[str, Any]:
        """
        Deliver leads to NeoWorlder via the Execute Inbound Flow endpoint.

        Automatically registers/updates the client before delivering leads.

        Args:
            pii_md5s: List of leads with PII data.

        Returns:
            dict: Response from the NeoWorlder API.

        Raises:
            NeoworlderAuthError: If authentication fails.
            NeoworlderAPIError: If the API request fails.
        """
        if not pii_md5s:
            log("warn", "No leads to deliver to NeoWorlder")
            return {"status": "skipped", "message": "No leads provided"}

        # Filter out leads where all phones are DNC (before registration to avoid unnecessary API calls)
        filtered_leads = self._filter_dnc_leads(pii_md5s)

        if not filtered_leads:
            log("warn", "All leads were filtered out (DNC)")
            return {"status": "skipped", "message": "All leads filtered out (DNC)"}

        # Auto-register client before delivery (idempotent - safe to call every time)
        self._register_client()

        url = f"{self.base_url}/api/v1/external-access/execute-inbound-flow"

        # Convert leads to CSV
        csv_file = self._convert_leads_to_csv(filtered_leads)

        # Prepare multipart form data
        files = {
            "file": ("leads.csv", csv_file, "text/csv"),
        }
        data = {
            "real_intent_client_id": self.real_intent_client_id,
        }

        log("info", f"Delivering {len(filtered_leads)} leads to NeoWorlder for client: {self.real_intent_client_id}")

        response = requests.post(
            url,
            headers=self.api_headers,
            files=files,
            data=data,
            timeout=TIMEOUT_SECONDS,
        )

        log("trace", f"Raw response: {_truncate_response_body(response.text)}, status_code: {response.status_code}")

        self._handle_response_errors(response, "execute_inbound_flow")

        log("info", f"Successfully delivered {len(filtered_leads)} leads to NeoWorlder")
        return self._parse_response(response)

    @staticmethod
    def _parse_response_static(response: requests.Response) -> dict[str, Any]:
        """
        Parse JSON response, raising on invalid/empty responses.

        Args:
            response: The requests Response object.

        Returns:
            dict: Parsed JSON response.

        Raises:
            NeoworlderAPIError: If response is empty or invalid JSON.
        """
        if not response.text:
            raise NeoworlderAPIError(
                "Empty response from NeoWorlder API",
                status_code=response.status_code,
                response_body="",
            )
        try:
            return response.json()
        except (json.JSONDecodeError, ValueError):
            raise NeoworlderAPIError(
                f"Invalid JSON response from NeoWorlder API: {_truncate_response_body(response.text)}",
                status_code=response.status_code,
                response_body=response.text,
            )

    def _parse_response(self, response: requests.Response) -> dict[str, Any]:
        """Instance method wrapper for _parse_response_static."""
        return self._parse_response_static(response)

    @staticmethod
    def _handle_response_errors_static(
        response: requests.Response,
        operation: str,
        real_intent_client_id: str,
    ) -> None:
        """
        Handle API response errors with specific exception types.

        Args:
            response: The requests Response object.
            operation: Name of the operation for logging.
            real_intent_client_id: Client ID for error messages.

        Raises:
            NeoworlderAuthError: For 401/403 responses.
            NeoworlderClientNotFoundError: For 404 responses.
            NeoworlderAPIError: For other error responses.
        """
        if response.ok:
            return

        status_code = response.status_code
        response_text = response.text

        log(
            "error",
            f"NeoWorlder API error during {operation}: status={status_code}, body={_truncate_response_body(response_text)}"
        )

        if status_code in (401, 403):
            raise NeoworlderAuthError(
                f"Authentication failed during {operation}: {_truncate_response_body(response_text)}",
                status_code=status_code,
                response_body=response_text,
            )

        if status_code == 404:
            raise NeoworlderClientNotFoundError(
                f"404 Not Found during {operation} for client '{real_intent_client_id}'. "
                f"This could indicate the client doesn't exist or the base_url/endpoint is misconfigured. "
                f"Response: {_truncate_response_body(response_text)}",
                status_code=status_code,
                response_body=response_text,
            )

        if status_code == 429:
            # Let the rate_limited decorator handle retries
            response.raise_for_status()

        raise NeoworlderAPIError(
            f"NeoWorlder API request failed during {operation}: {_truncate_response_body(response_text)}",
            status_code=status_code,
            response_body=response_text,
        )

    def _handle_response_errors(self, response: requests.Response, operation: str) -> None:
        """Instance method wrapper for _handle_response_errors_static."""
        self._handle_response_errors_static(response, operation, self.real_intent_client_id)
