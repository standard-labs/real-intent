"""Basic processing test. Make sure things work."""
from bigdbm.process import SimpleProcessor, FillProcessor
from bigdbm.schemas import MD5WithPII, IABJob
from bigdbm.validate.simple import ZipCodeValidator


def test_simple_processor(bigdbm_client):
    job = IABJob(
        intent_categories=["Real Estate>Real Estate Buying and Selling"],
        domains=[],
        keywords=[],
        zips=["22101"],
        n_hems=3
    )

    processor = SimpleProcessor(bigdbm_client)
    processor.add_default_validators()
    assert processor.process(job)


def test_fill_processor(bigdbm_client):
    job = IABJob(
        intent_categories=["Real Estate>Real Estate Buying and Selling"],
        domains=[],
        keywords=[],
        zips=["22101"],
        n_hems=3
    )

    processor = FillProcessor(bigdbm_client)
    processor.add_default_validators()
    processor.add_validator(ZipCodeValidator(["22101"]))

    result: list[MD5WithPII] = FillProcessor(bigdbm_client).process(job)
    assert result
