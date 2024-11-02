"""Temp test logging works."""

def test_logs():
    import logfire
    import os
    
    assert os.getenv("LOGFIRE_WRITE_TOKEN")
    logfire.debug("TEST HERE.")
