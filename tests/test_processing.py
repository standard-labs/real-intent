"""Basic processing test. Make sure things work."""
import pytest

from real_intent.process import SimpleProcessor, FillProcessor
from real_intent.schemas import MD5WithPII, IABJob
from real_intent.validate.simple import ZipCodeValidator
from real_intent.validate.pii import HNWValidator, MNWValidator

@pytest.mark.skip(reason="temp skip")
def test_simple_processor(bigdbm_client) -> None:
    job = IABJob(
        intent_categories=["Real Estate>Real Estate Buying and Selling"],
        domains=[],
        keywords=[],
        zips=["22101"],
        n_hems=3
    )

    processor = SimpleProcessor(bigdbm_client)
    assert processor.process(job)

@pytest.mark.skip(reason="temp skip")
def test_fill_processor(bigdbm_client) -> None:
    job = IABJob(
        intent_categories=["Real Estate>Real Estate Buying and Selling"],
        domains=[],
        keywords=[],
        zips=["22101"],
        n_hems=3
    )

    processor = FillProcessor(bigdbm_client)
    processor.add_validator(ZipCodeValidator(["22101"]))
    processor.add_default_validators()

    result: list[MD5WithPII] = FillProcessor(bigdbm_client).process(job)
    assert result

@pytest.mark.skip(reason="temp skip")
def test_hnw_mnw(bigdbm_client) -> None:
    job = IABJob(
        intent_categories=["Real Estate>Real Estate Buying and Selling"],
        domains=[],
        keywords=[],
        zips=["22101"],
        n_hems=3
    )

    processor = FillProcessor(bigdbm_client)
    processor.add_validator(HNWValidator(), priority=2)
    processor.add_validator(MNWValidator())

    result: list[MD5WithPII] = FillProcessor(bigdbm_client).process(job)
    assert result

@pytest.mark.skip(reason="temp skip")
def test_multiple_priorities(bigdbm_client) -> None:
    job = IABJob(
        intent_categories=["Real Estate>Real Estate Buying and Selling"],
        domains=[],
        keywords=[],
        zips=["22101"],
        n_hems=3
    )

    processor = FillProcessor(bigdbm_client)
    processor.add_validator(HNWValidator(), priority=3)
    processor.add_validator(MNWValidator(), priority=2)
    processor.add_validator(ZipCodeValidator(["22101"]), priority=1)

    result: list[MD5WithPII] = processor.process(job)
    assert result
    assert len(result) == 3

@pytest.mark.skip(reason="temp skip")
def test_no_validators(bigdbm_client) -> None:
    job = IABJob(
        intent_categories=["Real Estate>Real Estate Buying and Selling"],
        domains=[],
        keywords=[],
        zips=["22101"],
        n_hems=3
    )

    processor = FillProcessor(bigdbm_client)
    result: list[MD5WithPII] = processor.process(job)

    assert result
    assert len(result) == 3

@pytest.mark.skip(reason="temp skip")
def test_invalid_priority(bigdbm_client) -> None:
    processor = FillProcessor(bigdbm_client)

    with pytest.raises((ValueError, TypeError)):
        processor.add_validator(HNWValidator(), priority=0)
