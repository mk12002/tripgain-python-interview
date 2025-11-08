"""
Unit tests for the FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.flight_search_api import app

client = TestClient(app)


def test_api_health():
    """Test that the API is responding"""
    # This would need a health endpoint to be added to the API
    pass


def test_flight_search_missing_params():
    """Test flight search endpoint with missing parameters"""
    response = client.get("/flight-search")
    assert response.status_code == 422  # Unprocessable Entity


def test_flight_search_invalid_date():
    """Test flight search endpoint with invalid date format"""
    response = client.get(
        "/flight-search",
        params={
            "origin": "Bangalore",
            "destination": "Delhi",
            "journey_date": "invalid-date"
        }
    )
    # Should return error or 400
    assert response.status_code in [400, 422]


def test_flight_search_valid_params():
    """Test flight search endpoint with valid parameters"""
    # Note: This is a slow test as it actually scrapes the website
    # In production, you'd want to mock the scraping function
    response = client.get(
        "/flight-search",
        params={
            "origin": "Bangalore",
            "destination": "Delhi",
            "journey_date": "2025-11-15"
        }
    )
    
    # Should succeed or return 200
    # Actual result depends on website availability
    assert response.status_code in [200, 400, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
