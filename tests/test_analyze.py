import pytest
from bigdbm.analyze.base import BaseAnalyzer
from bigdbm.analyze.insights import OpenAIInsightsGenerator, ValidatedInsightsGenerator
from bigdbm.schemas import MD5WithPII, PII, IntentEvent
from unittest.mock import Mock, patch

class TestAnalyzer(BaseAnalyzer):
    def analyze(self, md5s: list[MD5WithPII]) -> str:
        return f"Analyzed {len(md5s)} MD5s"

def test_base_analyzer():
    analyzer = TestAnalyzer()
    md5s = [
        MD5WithPII(md5="123", sentences=["test"], pii=Mock(spec=PII)),
        MD5WithPII(md5="456", sentences=["test"], pii=Mock(spec=PII))
    ]
    result = analyzer.analyze(md5s)
    assert result == "Analyzed 2 MD5s"

@pytest.mark.skip(reason="Requires OpenAI API key")
def test_openai_insights_generator():
    generator = OpenAIInsightsGenerator("fake_api_key")
    md5s = [
        MD5WithPII(md5="123", sentences=["test sentence 1"], pii=Mock(spec=PII)),
        MD5WithPII(md5="456", sentences=["test sentence 2"], pii=Mock(spec=PII))
    ]
    with patch('openai.OpenAI') as mock_openai:
        mock_openai.return_value.beta.chat.completions.parse.return_value.choices[0].message.parsed = Mock(insights=["Insight 1", "Insight 2"])
        result = generator.analyze(md5s)
    assert isinstance(result, str)
    assert "1. Insight 1" in result
    assert "2. Insight 2" in result

@pytest.mark.skip(reason="Requires OpenAI API key")
def test_validated_insights_generator():
    mock_processor = Mock()
    mock_processor.required_validators = []
    mock_processor.fallback_validators = []
    generator = ValidatedInsightsGenerator("fake_api_key", mock_processor)
    md5s = [
        MD5WithPII(md5="123", sentences=["test sentence 1"], pii=Mock(spec=PII)),
        MD5WithPII(md5="456", sentences=["test sentence 2"], pii=Mock(spec=PII))
    ]
    with patch('openai.OpenAI') as mock_openai:
        mock_openai.return_value.beta.chat.completions.parse.return_value.choices[0].message.parsed = Mock(
            validation_insight="Validation insight",
            insights=["Insight 1", "Insight 2"]
        )
        result = generator.analyze(md5s)
    assert isinstance(result, str)
    assert "On validation: Validation insight" in result
    assert "1. Insight 1" in result
    assert "2. Insight 2" in result

# Add more specific tests for other analyzers as needed