"""
Configuration constants for the flight search application
"""
import json
import os

# Default search parameters
DEFAULT_ORIGIN = "Bangalore"
DEFAULT_DESTINATION = "Delhi"

# Timeout settings (in milliseconds)
DEFAULT_TIMEOUT = 60000  # Page default timeout
RESULT_WAIT_TIMEOUT = 45000  # Wait for flight results
NETWORK_IDLE_TIMEOUT = 30000  # Wait for network idle state

# Scraping settings
DEFAULT_DAYS_FROM_TODAY = 7  # Default travel date offset
HEADLESS_MODE = True  # Run browser in headless mode for API
SLOW_MO = 50  # Milliseconds to slow down Playwright operations

# Target website
TARGET_URL = "https://www.budgetticket.in"

# Known airlines for flight detection - loaded from JSON
def _load_airlines():
    """Load airline list from JSON file."""
    try:
        config_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(config_dir, "static", "airline_list.json")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Combine both Indian and international airlines
            return data.get("indian_airlines", []) + data.get("international_airlines", [])
    except Exception as e:
        print(f"Warning: Could not load airline_list.json: {e}")
        # Fallback list
        return [
            "IndiGo", "Air India", "SpiceJet", "Vistara", "GoAir", "Go First",
            "AirAsia India", "Air India Express", "Alliance Air", "TruJet",
            "Akasa Air", "Star Air"
        ]

KNOWN_AIRLINES = _load_airlines()
