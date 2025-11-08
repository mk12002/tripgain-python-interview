"""
Unit tests for the automation/scraping module
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.extractors import extract_flights_from_card_text, KNOWN_AIRLINES
from app.utils.validators import validate_flight_data, create_flight_id, deduplicate_flights
from app.utils.format_converter import automation_to_api_format, api_to_automation_format


def test_extract_flights_basic():
    """Test basic flight extraction from text"""
    sample_text = """
    IndiGo
    6E 123
    10:00
    12:30
    ₹ 3500
    """
    
    result = extract_flights_from_card_text(sample_text)
    
    assert result["airline"] == "IndiGo"
    assert result["flight_number"] == "6E 123"
    assert result["departure"] == "10:00"
    assert result["arrival"] == "12:30"
    assert "3500" in result["price"]


def test_validate_flight_data_valid():
    """Test validation with valid flight data"""
    valid_flight = {
        "airline": "IndiGo",
        "flight_number": "6E 123",
        "departure": "10:00",
        "arrival": "12:30",
        "price": "₹ 3500"
    }
    
    assert validate_flight_data(valid_flight) == True


def test_validate_flight_data_invalid():
    """Test validation with invalid flight data"""
    invalid_flight = {
        "airline": "N/A",
        "flight_number": "N/A",
        "departure": "N/A",
        "arrival": "N/A",
        "price": "N/A"
    }
    
    assert validate_flight_data(invalid_flight) == False


def test_create_flight_id():
    """Test flight ID generation for deduplication"""
    flight = {
        "airline": "IndiGo",
        "departure": "10:00",
        "price": "₹ 3500"
    }
    
    flight_id = create_flight_id(flight)
    assert flight_id == "IndiGo_10:00_₹ 3500"


def test_deduplicate_flights():
    """Test flight deduplication"""
    flights = [
        {"airline": "IndiGo", "departure": "10:00", "price": "₹ 3500"},
        {"airline": "IndiGo", "departure": "10:00", "price": "₹ 3500"},  # Duplicate
        {"airline": "Air India", "departure": "11:00", "price": "₹ 4000"}
    ]
    
    unique = deduplicate_flights(flights)
    assert len(unique) == 2


def test_automation_to_api_format():
    """Test format conversion from automation to API"""
    automation_data = {
        "search_metadata": {
            "origin": "Bangalore",
            "destination": "Delhi",
            "search_datetime_utc": "2025-11-08T10:00:00Z",
            "total_flights_found": 1
        },
        "flights": [
            {
                "airline": "IndiGo",
                "search_datetime_utc": "2025-11-08T10:00:00Z"
            }
        ]
    }
    
    api_format = automation_to_api_format(automation_data)
    
    assert isinstance(api_format, list)
    assert len(api_format) == 1
    assert "searchdatetime" in api_format[0]
    assert "search_datetime_utc" not in api_format[0]


def test_api_to_automation_format():
    """Test format conversion from API to automation"""
    api_data = [
        {
            "airline": "IndiGo",
            "searchdatetime": "2025-11-08T10:00:00Z"
        }
    ]
    
    automation_format = api_to_automation_format(api_data, "Bangalore", "Delhi")
    
    assert isinstance(automation_format, dict)
    assert "search_metadata" in automation_format
    assert "flights" in automation_format
    assert automation_format["flights"][0]["search_datetime_utc"] == "2025-11-08T10:00:00Z"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
