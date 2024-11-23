import os

import pytest
from dotenv import load_dotenv

from real_intent.analyze.base import BaseAnalyzer
from real_intent.analyze.insights import OpenAIInsightsGenerator, ValidatedInsightsGenerator
from real_intent.analyze.insights.per_lead import PerLeadInsightGenerator
from real_intent.schemas import MD5WithPII, PII

from real_intent.process.fill import FillProcessor
from real_intent.validate.simple import SamePersonValidator
from real_intent.validate.pii import MNWValidator


# Load environment variables
load_dotenv()


class TestAnalyzer(BaseAnalyzer):
    """
    Dummy analyzer for structural that simply returns the number of MD5s analyzed.
    """

    def _analyze(self, md5s: list[MD5WithPII]) -> str:
        return f"Analyzed {len(md5s)} MD5s"


def test_base_analyzer() -> None:
    analyzer = TestAnalyzer()
    # Create two MD5WithPII objects with fake PII data
    md5s = [
        MD5WithPII(md5="123", sentences=["test"], pii=PII.create_fake(seed=42)),
        MD5WithPII(md5="456", sentences=["test"], pii=PII.create_fake(seed=43))
    ]
    result = analyzer.analyze(md5s)
    assert result == "Analyzed 2 MD5s"


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not found")
def test_openai_insights_generator() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    generator = OpenAIInsightsGenerator(api_key)
    # Create MD5WithPII objects with fake PII data and specific sentences
    md5s = [
        MD5WithPII(md5="123", sentences=["Interested in buying a new car"], pii=PII.create_fake(seed=42)),
        MD5WithPII(md5="456", sentences=["Looking for auto insurance"], pii=PII.create_fake(seed=43))
    ]
    result = generator.analyze(md5s)
    assert isinstance(result, str)
    assert len(result.split("\n")) >= 2  # Expecting at least two insights


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not found")
def test_validated_insights_generator(bigdbm_client) -> None:
    api_key = os.getenv("OPENAI_API_KEY")

    processor = FillProcessor(bigdbm_client)
    processor.add_validator(SamePersonValidator())
    processor.add_validator(MNWValidator(), priority=2)

    generator = ValidatedInsightsGenerator(api_key, processor)
    # Create MD5WithPII objects with fake PII data and specific sentences
    md5s = [
        MD5WithPII(md5="123", sentences=["Interested in buying a new car"], pii=PII.create_fake(seed=42)),
        MD5WithPII(md5="456", sentences=["Looking for auto insurance"], pii=PII.create_fake(seed=43))
    ]
    result = generator.analyze(md5s)
    assert isinstance(result, str)
    assert "On validation:" in result
    assert len(result.split("\n")) >= 3  # Expecting validation insight and at least two regular insights


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not found")
def test_individual_insights_generator(bigdbm_client) -> None:
    api_key = os.getenv("OPENAI_API_KEY")

    processor = FillProcessor(bigdbm_client)
    processor.add_validator(SamePersonValidator())
    processor.add_validator(MNWValidator(), priority=2)

    generator = ValidatedInsightsGenerator(api_key, processor)
    # Create MD5WithPII objects with fake PII data and specific sentences
    md5s = [
        MD5WithPII(md5="123", sentences=["Interested in buying a new car"], pii=PII.create_fake(seed=42)),
        MD5WithPII(md5="456", sentences=["Looking for auto insurance"], pii=PII.create_fake(seed=43))
    ]
    result = generator.analyze(md5s)

    individual_generator = PerLeadInsightGenerator(api_key, result)
    insights = individual_generator.analyze(md5s)

    assert isinstance(insights, dict)
    assert len(insights) == 2

    for md5, insight in insights.items():
        assert isinstance(md5, str)
        assert isinstance(insight, str)
        assert len(insight) > 0
