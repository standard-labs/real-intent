"""Basic kvCORE tests, without actually integrating."""
from real_intent.deliver.kvcore import KVCoreDeliverer


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
