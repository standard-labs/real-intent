"""Test the BigDBMClient class."""
import pytest

import os
from concurrent.futures import ThreadPoolExecutor, Future
from dotenv import load_dotenv

from real_intent.client import BigDBMClient


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
