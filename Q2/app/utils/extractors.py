"""
Data extraction module for parsing flight information
"""
import re

try:
    from app.config import KNOWN_AIRLINES
except ImportError:
    from ..config import KNOWN_AIRLINES


def extract_flights_from_card_text(text):
    """
    Enhanced extraction with known airline matching and improved regex patterns.
    Parse flight card text and extract airline, flight number, times, and price.
    """
    airline = "N/A"
    flight_number = "N/A"
    departure = "N/A"
    arrival = "N/A"
    price = "N/A"
    
    # Strategy 1: Try to match known airlines first
    for known_airline in KNOWN_AIRLINES:
        if known_airline.lower() in text.lower():
            airline = known_airline
            break
    
    # Strategy 2: Heuristic airline extraction if not found
    if airline == "N/A":
        lines = text.split("\n")
        for line in lines[:5]:
            line_clean = line.strip()
            if 3 < len(line_clean) < 30 and not re.search(r"\d", line_clean):
                if line_clean not in ("Departure", "Arrival", "Price", "Duration"):
                    airline = line_clean
                    break
    
    # Extract flight number (improved regex)
    flight_match = re.search(r"\b([A-Z0-9]{1,3}[\s\-]?\d{3,5})\b", text)
    if flight_match:
        flight_number = flight_match.group(1)
    
    # Extract times
    time_pattern = r"\b([01]?[0-9]|2[0-3]):[0-5][0-9]\b"
    times = re.findall(time_pattern, text)
    if len(times) >= 2:
        departure = times[0]
        arrival = times[1]
    elif len(times) == 1:
        departure = times[0]
    
    # Extract price with currency symbol
    price = "N/A"
    price_match = re.search(r"(?:₹|Rs\.?|INR)\s*([\d,]+)", text, re.IGNORECASE)
    if not price_match:
        price_match = re.search(r"\b(\d{3,5})\b", text)
    if price_match:
        price_value = price_match.group(1)
        price = f"₹ {price_value}"
    
    return {
        "airline": airline,
        "flight_number": flight_number,
        "departure": departure,
        "arrival": arrival,
        "price": price
    }


def find_flight_cards_by_selectors(page, selector_patterns):
    """
    Find flight cards using multiple selector strategies
    """
    flight_cards = []
    
    for pattern in selector_patterns:
        try:
            count = page.locator(pattern).count()
            if count > 0:
                print(f"Found {count} elements with selector: {pattern}")
                for i in range(count):
                    try:
                        element = page.locator(pattern).nth(i)
                        text = element.inner_text()
                        # Only consider elements with time and price patterns
                        if re.search(r"\d{1,2}:\d{2}", text) and (
                            re.search(r"₹|Rs", text, re.IGNORECASE) or 
                            re.search(r"\d{3,}", text)
                        ):
                            flight_cards.append(element)
                    except:
                        continue
                if flight_cards:
                    break
        except Exception as e:
            continue
    
    return flight_cards


def find_flight_cards_heuristic(page):
    """
    Heuristic search for flight data when specific selectors don't work
    """
    flight_cards = []
    all_divs = page.query_selector_all("div, article, li, section")
    
    for div in all_divs:
        try:
            text = div.inner_text()
            # Must have time pattern and price/number pattern
            has_time = bool(re.search(r"\b([01]?[0-9]|2[0-3]):[0-5][0-9]\b", text))
            has_price = bool(re.search(r"(?:₹|Rs\.?|INR)\s*[\d,]+", text, re.IGNORECASE))
            
            if has_time and has_price:
                # Check it's not too large (likely a container)
                text_length = len(text)
                if 50 < text_length < 1000:  # Reasonable size for a flight card
                    flight_cards.append(div)
        except:
            continue
    
    return flight_cards
