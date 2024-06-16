"""Client, etc."""
import pytest

import os

from bigdbm.client import BigDBMClient


@pytest.fixture(scope="session")
def bigdbm_client() -> BigDBMClient:
    """Create a BigDBM client object."""
    client_id: str = os.environ.get("CLIENT_ID", "")
    client_secret: str = os.environ.get("CLIENT_SECRET", "")

    if not (client_id and client_secret):
        raise ValueError("Need CLIENT_ID and CLIENT_SECRET variables to run tests.")

    return BigDBMClient(client_id, client_secret)
