"""
Data validation module for flight information
"""


def validate_flight_data(flight_dict):
    """
    Validate that flight data has minimum required fields.
    Returns True if valid, False otherwise.
    """
    # Must have at least airline/price and one time
    has_airline = flight_dict.get("airline") != "N/A"
    has_price = flight_dict.get("price") != "N/A"
    has_time = (
        flight_dict.get("departure") != "N/A" or 
        flight_dict.get("arrival") != "N/A"
    )
    
    return has_price and has_time


def create_flight_id(flight_dict):
    """
    Create a unique identifier for deduplication.
    """
    airline = flight_dict.get("airline", "")
    departure = flight_dict.get("departure", "")
    price = flight_dict.get("price", "")
    return f"{airline}_{departure}_{price}"


def deduplicate_flights(flights):
    """
    Remove duplicate flights based on flight_id.
    Returns list of unique flights.
    """
    seen = set()
    unique_flights = []
    
    for flight in flights:
        flight_id = create_flight_id(flight)
        if flight_id not in seen:
            seen.add(flight_id)
            unique_flights.append(flight)
    
    return unique_flights


def filter_valid_cards(cards, min_length=30, max_length=5000):
    """
    Filter cards by text length to remove invalid containers.
    """
    valid_cards = []
    for card in cards:
        try:
            text = card.inner_text() if hasattr(card, 'inner_text') else str(card)
            text_length = len(text)
            if min_length < text_length < max_length:
                valid_cards.append(card)
        except:
            continue
    
    return valid_cards
