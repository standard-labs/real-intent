"""Client, etc."""
import pytest

import os
from dotenv import load_dotenv
import random
import string

from real_intent.client import BigDBMClient
from real_intent.schemas import MD5WithPII, PII


# Load env
load_dotenv()


# Configure logfire if write token is given
if os.getenv("LOGFIRE_WRITE_TOKEN"):
    try:
        import logfire
    except ImportError:
        pass
    else:
        logfire.configure(token=os.getenv("LOGFIRE_WRITE_TOKEN"), send_to_logfire=True)


@pytest.fixture(scope="session")
def bigdbm_client() -> BigDBMClient:
    """Create a BigDBM client object."""
    client_id: str = os.environ.get("CLIENT_ID", "")
    client_secret: str = os.environ.get("CLIENT_SECRET", "")

    if not (client_id and client_secret):
        raise ValueError("Need CLIENT_ID and CLIENT_SECRET variables to run tests.")

    return BigDBMClient(client_id, client_secret)


def generate_random_name(length=6):
    """Generate a random name of given length."""
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length)).capitalize()


@pytest.fixture(scope="session")
def sample_pii_md5s():
    """Create a sample MD5WithPII object using fake PII data."""
    # Create fake PII with a fixed seed for reproducibility
    pii = PII.create_fake(seed=42)
    
    # Create MD5WithPII with the fake PII
    return [
        MD5WithPII(
            md5="1234567890abcdef",
            sentences=["test sentence"],
            pii=pii
        )
    ]
