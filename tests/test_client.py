"""Test the BigDBMClient class."""
import pytest

import os
from concurrent.futures import ThreadPoolExecutor, Future
from dotenv import load_dotenv

from real_intent.client import BigDBMClient
from real_intent.schemas import IABJob


# Load environment variables
load_dotenv()


@pytest.fixture
def bigdbm_client() -> BigDBMClient:
    client_id: str | None = os.getenv("CLIENT_ID")
    client_secret: str | None = os.getenv("CLIENT_SECRET")

    if not client_id or not client_secret:
        pytest.skip("CLIENT_ID or CLIENT_SECRET not found in .env file")

    return BigDBMClient(client_id, client_secret)


def test_bigdbm_client_thread_safety(bigdbm_client: BigDBMClient) -> None:
    def access_token_operations() -> None:
        # Simulate multiple operations that could potentially cause race conditions
        bigdbm_client._update_token()
        assert bigdbm_client._access_token_valid()

        # Simulate a request by accessing the token
        token: str = bigdbm_client._access_token
        assert token != ""

    # Use ThreadPoolExecutor to run multiple threads concurrently
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures: list[Future[None]] = [executor.submit(access_token_operations) for _ in range(10)]
        
        # Wait for all threads to complete and check for any exceptions
        for future in futures:
            future.result()  # This will raise an exception if one occurred in the thread


def test_check_numbers(bigdbm_client: BigDBMClient) -> None:
    # Create a sample IABJob
    sample_iab_job = IABJob(
        intent_categories=["Real Estate>Real Estate Buying and Selling"],
        domains=[],
        keywords=[],
        zips=["22101"],
        n_hems=3
    )

    result = bigdbm_client.check_numbers(sample_iab_job)

    assert isinstance(result, dict), "Result should be a dictionary"
    assert "total" in result, "Result should contain 'total' key"
    assert "unique" in result, "Result should contain 'unique' key"
    assert isinstance(result["total"], int), "'total' value should be an integer"
    assert isinstance(result["unique"], int), "'unique' value should be an integer"
    assert result["total"] >= 0, "'total' should be non-negative"
    assert result["unique"] >= 0, "'unique' should be non-negative"
    assert result["unique"] <= result["total"], "'unique' should not exceed 'total'"


def test_phones_to_pii(bigdbm_client: BigDBMClient) -> None:
    phones = ["2017872909", "5712861350"]
    result = bigdbm_client.phones_to_pii(phones)
    
    assert isinstance(result, list), "Result should be a list"
    assert result[0].first_name == "Donna", "First name should be 'Donna'"
    assert result[0].last_name == "Weiss", "Last name should be 'Weiss'"

    assert result[1].first_name == "Clement", "First name should be 'Zhang'"
    assert result[1].last_name == "Zhang", "Last name should be 'Jiqiang'"
    

def test_pii_to_pii(bigdbm_client: BigDBMClient) -> None:
    result = bigdbm_client.pii_to_pii("Donna", "Weiss", "6350 Chowning Pl", "22101-4129", "519")

    assert isinstance(result, list), "Result should be a list"
    assert result[0].first_name == "Donna", "First name should be 'Donna'"
    assert result[0].last_name == "Weiss", "Last name should be 'Weiss'"
