"""Client, etc."""
import pytest

import os
from dotenv import load_dotenv

from real_intent.client import BigDBMClient


# Load env
load_dotenv()


# Configure logfire if write token is given
if os.getenv("LOGFIRE_WRITE_TOKEN"):
    try:
        import logfire
    except ImportError:
        pass
    else:
        logfire.configure(token=os.getenv("LOGFIRE_WRITE_TOKEN"))


@pytest.fixture(scope="session")
def bigdbm_client() -> BigDBMClient:
    """Create a BigDBM client object."""
    client_id: str = os.environ.get("CLIENT_ID", "")
    client_secret: str = os.environ.get("CLIENT_SECRET", "")

    if not (client_id and client_secret):
        raise ValueError("Need CLIENT_ID and CLIENT_SECRET variables to run tests.")

    return BigDBMClient(client_id, client_secret)
