"""Test the event generators (Scrapybara and Perplexity)."""
import pytest
import os
import warnings
from dotenv import load_dotenv
import datetime
import re

# Suppress reportlab deprecation warning
warnings.filterwarnings(
    "ignore",
    message="ast.NameConstant is deprecated",
    category=DeprecationWarning
)

from real_intent.events import (
    EventsResponse,
    PerplexityEventsGenerator,
    ScrapybaraEventsGenerator
)

# Load environment variables
load_dotenv()


@pytest.fixture
def events_generator_90210_scrapybara():
    """Create a ScrapybaraEventsGenerator instance for Beverly Hills."""
    scrapybara_api_key = os.getenv("SCRAPYBARA_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not scrapybara_api_key or not anthropic_api_key:
        pytest.skip("Scrapybara and Anthropic API keys required")
    
    return ScrapybaraEventsGenerator(
        scrapybara_api_key,
        anthropic_api_key
    )


@pytest.fixture
def events_generator_22101_scrapybara():
    """Create a ScrapybaraEventsGenerator instance for McLean."""
    scrapybara_api_key = os.getenv("SCRAPYBARA_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not scrapybara_api_key or not anthropic_api_key:
        pytest.skip("Scrapybara and Anthropic API keys required")
    
    return ScrapybaraEventsGenerator(
        scrapybara_api_key,
        anthropic_api_key
    )


@pytest.fixture
def events_generator_90210_perplexity():
    """Create a PerplexityEventsGenerator instance for Beverly Hills."""
    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    
    if not perplexity_api_key:
        pytest.skip("Perplexity API key not found")
    
    return PerplexityEventsGenerator(
        perplexity_api_key
    )


@pytest.fixture
def events_generator_22101_perplexity():
    """Create a PerplexityEventsGenerator instance for McLean."""
    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    
    if not perplexity_api_key:
        pytest.skip("Perplexity API key not found")
    
    return PerplexityEventsGenerator(
        perplexity_api_key
    )


def extract_date_from_range(date_str: str) -> str:
    """Extract the first date from a date range string."""
    # Try to match YYYY-MM-DD format first
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    
    # Try to extract first date from a range (e.g., "2024-12-22 to 2024-12-29")
    match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
    if match:
        return match.group(1)
    
    raise ValueError(f"Could not extract date from: {date_str}")


def test_beverly_hills_events_scrapybara(events_generator_90210_scrapybara):
    """Test generating events for Beverly Hills (90210) using Scrapybara."""
    response = events_generator_90210_scrapybara.generate("90210")
    
    # Verify response structure
    assert isinstance(response, EventsResponse)
    assert isinstance(response.events, list)
    assert isinstance(response.summary, str)
    
    # Verify we got some events
    assert len(response.events) >= 3, "Should have at least 3 events"
    
    # Verify each event
    for event in response.events:
        assert event.title, "Event should have a title"
        assert event.date, "Event should have a date"
        assert event.description, "Event should have a description"
        
        # Extract and verify date
        date_str = extract_date_from_range(event.date)
        event_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        # Allow events within the next month
        today = datetime.datetime.now() - datetime.timedelta(days=1)  # 1 day grace period
        month_from_now = today + datetime.timedelta(days=32)  # ~1 month + 1 day grace period
        assert today <= event_date <= month_from_now, f"Event date {event_date} should be within the next month"
        
        # Verify description is meaningful
        assert len(event.description.split()) >= 10, "Description should be meaningful"
    
    # Verify summary
    assert len(response.summary.split()) >= 20, "Summary should be meaningful"
    assert "Beverly Hills" in response.summary, "Summary should mention Beverly Hills"


def test_mclean_events_scrapybara(events_generator_22101_scrapybara):
    """Test generating events for McLean (22101) using Scrapybara."""
    response = events_generator_22101_scrapybara.generate("22101")
    
    # Verify response structure
    assert isinstance(response, EventsResponse)
    assert isinstance(response.events, list)
    assert isinstance(response.summary, str)
    
    # Verify we got some events
    assert len(response.events) >= 3, "Should have at least 3 events"
    
    # Verify each event
    for event in response.events:
        assert event.title, "Event should have a title"
        assert event.date, "Event should have a date"
        assert event.description, "Event should have a description"
        
        # Extract and verify date
        date_str = extract_date_from_range(event.date)
        event_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        # Allow events within the next month
        today = datetime.datetime.now() - datetime.timedelta(days=1)  # 1 day grace period
        month_from_now = today + datetime.timedelta(days=32)  # ~1 month + 1 day grace period
        assert today <= event_date <= month_from_now, f"Event date {event_date} should be within the next month"
        
        # Verify description is meaningful
        assert len(event.description.split()) >= 10, "Description should be meaningful"
    
    # Verify summary
    assert len(response.summary.split()) >= 20, "Summary should be meaningful"
    assert "McLean" in response.summary, "Summary should mention McLean"


def test_pdf_generation_scrapybara(events_generator_90210_scrapybara):
    """Test generating PDF from events using Scrapybara."""
    # First get some events
    response = events_generator_90210_scrapybara.generate("90210")
    
    # Generate PDF
    pdf_buffer = events_generator_90210_scrapybara.to_pdf_buffer(response)
    
    # Verify PDF was generated
    assert pdf_buffer.getvalue().startswith(b'%PDF'), "Should be a valid PDF"
    assert len(pdf_buffer.getvalue()) > 1000, "PDF should have meaningful content"


def test_invalid_zip_code_scrapybara(events_generator_90210_scrapybara):
    """Test generation with invalid zip code for Scrapybara."""
    # Test non-string zip code
    with pytest.raises(ValueError):
        events_generator_90210_scrapybara._generate(12345)
    
    # Test empty zip code
    with pytest.raises(ValueError):
        events_generator_90210_scrapybara._generate("")
    
    # Test wrong length zip code
    with pytest.raises(ValueError):
        events_generator_90210_scrapybara._generate("1234")
    
    # Test non-numeric zip code
    with pytest.raises(ValueError):
        events_generator_90210_scrapybara._generate("abcde")


def test_invalid_api_key_scrapybara():
    """Test initialization with invalid API key for Scrapybara."""
    # Test non-string API key
    with pytest.raises(ValueError):
        ScrapybaraEventsGenerator(12345, 54321)
    
    # Test empty API key
    with pytest.raises(ValueError):
        ScrapybaraEventsGenerator("", "")
    
    # Test None API key
    with pytest.raises(ValueError):
        ScrapybaraEventsGenerator(None, None)


def test_beverly_hills_events_perplexity(events_generator_90210_perplexity):
    """Test generating events for Beverly Hills (90210) using Perplexity."""
    response = events_generator_90210_perplexity.generate("90210")
    
    # Verify response structure
    assert isinstance(response, EventsResponse)
    assert isinstance(response.events, list)
    assert isinstance(response.summary, str)
    
    # Verify we got some events
    assert len(response.events) >= 3, "Should have at least 3 events"
    
    # Verify each event
    for event in response.events:
        assert event.title, "Event should have a title"
        assert event.date, "Event should have a date"
        assert event.description, "Event should have a description"
        
        # Extract and verify date
        date_str = extract_date_from_range(event.date)
        event_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        # Allow events within the next month
        today = datetime.datetime.now() - datetime.timedelta(days=1)  # 1 day grace period
        month_from_now = today + datetime.timedelta(days=32)  # ~1 month + 1 day grace period
        assert today <= event_date <= month_from_now, f"Event date {event_date} should be within the next month"
        
        # Verify description is meaningful
        assert len(event.description.split()) >= 10, "Description should be meaningful"
    
    # Verify summary
    assert len(response.summary.split()) >= 20, "Summary should be meaningful"
    assert "Beverly Hills" in response.summary, "Summary should mention Beverly Hills"


def test_mclean_events_perplexity(events_generator_22101_perplexity):
    """Test generating events for McLean (22101) using Perplexity."""
    response = events_generator_22101_perplexity.generate("22101")
    
    # Verify response structure
    assert isinstance(response, EventsResponse)
    assert isinstance(response.events, list)
    assert isinstance(response.summary, str)
    
    # Verify we got some events
    assert len(response.events) >= 3, "Should have at least 3 events"
    
    # Verify each event
    for event in response.events:
        assert event.title, "Event should have a title"
        assert event.date, "Event should have a date"
        assert event.description, "Event should have a description"
        
        # Extract and verify date
        date_str = extract_date_from_range(event.date)
        event_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        # Allow events within the next month
        today = datetime.datetime.now() - datetime.timedelta(days=1)  # 1 day grace period
        month_from_now = today + datetime.timedelta(days=32)  # ~1 month + 1 day grace period
        assert today <= event_date <= month_from_now, f"Event date {event_date} should be within the next month"
        
        # Verify description is meaningful
        assert len(event.description.split()) >= 10, "Description should be meaningful"
    
    # Verify summary
    assert len(response.summary.split()) >= 20, "Summary should be meaningful"
    assert "McLean" in response.summary, "Summary should mention McLean"


def test_pdf_generation_perplexity(events_generator_90210_perplexity):
    """Test generating PDF from events using Perplexity."""
    # First get some events
    response = events_generator_90210_perplexity.generate("90210")
    
    # Generate PDF
    pdf_buffer = events_generator_90210_perplexity.to_pdf_buffer(response)
    
    # Verify PDF was generated
    assert pdf_buffer.getvalue().startswith(b'%PDF'), "Should be a valid PDF"
    assert len(pdf_buffer.getvalue()) > 1000, "PDF should have meaningful content"


def test_invalid_zip_code_perplexity(events_generator_90210_perplexity):
    """Test generation with invalid zip code for Perplexity."""
    # Test non-string zip code
    with pytest.raises(ValueError):
        events_generator_90210_perplexity._generate(12345)
    
    # Test empty zip code
    with pytest.raises(ValueError):
        events_generator_90210_perplexity._generate("")
    
    # Test wrong length zip code
    with pytest.raises(ValueError):
        events_generator_90210_perplexity._generate("1234")
    
    # Test non-numeric zip code
    with pytest.raises(ValueError):
        events_generator_90210_perplexity._generate("abcde")


def test_invalid_api_key_perplexity():
    """Test initialization with invalid API key for Perplexity."""
    # Test non-string API key
    with pytest.raises(ValueError):
        PerplexityEventsGenerator(12345)
    
    # Test empty API key
    with pytest.raises(ValueError):
        PerplexityEventsGenerator("")
    
    # Test None API key
    with pytest.raises(ValueError):
        PerplexityEventsGenerator(None)
