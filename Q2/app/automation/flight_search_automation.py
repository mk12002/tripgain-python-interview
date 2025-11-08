# flight_search_automation_fixed.py
import json
import re
import time
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright

# Import shared helper functions, utilities, and config
try:
    from app.utils.automation_helpers import set_date_input, wait_for_flight_results
    from app.utils.selectors import find_input_by_keywords, click_search_button, FLIGHT_CARD_SELECTORS
    from app.utils.extractors import extract_flights_from_card_text, find_flight_cards_by_selectors, find_flight_cards_heuristic
    from app.utils.validators import validate_flight_data, deduplicate_flights, create_flight_id
    from app.config import DEFAULT_ORIGIN, DEFAULT_DESTINATION, TARGET_URL, DEFAULT_TIMEOUT, KNOWN_AIRLINES
except ImportError:
    # Fallback for local testing
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from app.utils.automation_helpers import set_date_input, wait_for_flight_results
    from app.utils.selectors import find_input_by_keywords, click_search_button, FLIGHT_CARD_SELECTORS
    from app.utils.extractors import extract_flights_from_card_text, find_flight_cards_by_selectors, find_flight_cards_heuristic
    from app.utils.validators import validate_flight_data, deduplicate_flights, create_flight_id
    from app.config import DEFAULT_ORIGIN, DEFAULT_DESTINATION, TARGET_URL, DEFAULT_TIMEOUT, KNOWN_AIRLINES

ORIGIN = DEFAULT_ORIGIN
DESTINATION = DEFAULT_DESTINATION

# Note: All utility functions (find_input_by_keywords, click_search_button, 
# extract_flights_from_card_text, validate_flight_data, etc.) are now 
# imported from their respective modules in app.utils

def log_page_state(page, stage):
    """Log current page state for debugging."""
    try:
        url = page.url
        title = page.title()
        print(f"\n=== Page State at {stage} ===")
        print(f"URL: {url}")
        print(f"Title: {title}")
        
        # Check for error messages
        error_texts = ["error", "invalid", "required", "please"]
        for err in error_texts:
            if page.locator(f"text=/{err}/i").count() > 0:
                print(f"⚠️  Found '{err}' on page")
    except Exception as e:
        print(f"Could not log page state: {e}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)  # Reduced slow_mo
        page = browser.new_page()
        page.set_default_timeout(60000)
        
        print("Loading BudgetTicket.in...")
        try:
            page.goto("https://www.budgetticket.in", wait_until="domcontentloaded")
        except Exception as e:
            print("Page load error:", e)
            browser.close()
            return
        
        time.sleep(2)
        
        # Close modals
        try:
            for selector in ['button[aria-label="Close"]', 'button.close', 
                           '.modal button.close', 'button[title="Close"]']:
                try:
                    if page.locator(selector).count() > 0:
                        page.locator(selector).first.click(timeout=2000)
                        time.sleep(0.3)
                except:
                    pass
        except:
            pass
        
        # Fill origin
        print("Filling origin...")
        from_input = find_input_by_keywords(page, ["from", "origin", "departure"])
        if not from_input:
            print("ERROR: Could not find 'From' input.")
            browser.close()
            return
        
        try:
            from_input.click()
            from_input.fill("")
            from_input.type(ORIGIN, delay=60)
            time.sleep(0.8)
            
            # Select from autocomplete
            try:
                page.wait_for_selector("ul[role=listbox], .autocomplete", timeout=3000)
                page.keyboard.press("ArrowDown")
                page.keyboard.press("Enter")
            except:
                page.keyboard.press("Enter")
            
            print("Origin filled.")
            time.sleep(1.0)
        except Exception as e:
            print("Failed to fill origin:", e)
            browser.close()
            return
        
        # Fill destination
        print("Filling destination...")
        to_input = find_input_by_keywords(page, ["to", "destination", "arrival"])
        if not to_input:
            print("ERROR: Could not find 'To' input.")
            browser.close()
            return
        
        try:
            to_input.click()
            to_input.fill("")
            to_input.type(DESTINATION, delay=60)
            time.sleep(0.8)
            
            try:
                page.wait_for_selector("ul[role=listbox], .autocomplete", timeout=3000)
                page.keyboard.press("ArrowDown")
                page.keyboard.press("Enter")
            except:
                page.keyboard.press("Enter")
            
            print("Destination filled.")
            time.sleep(1.0)
        except Exception as e:
            print("Failed to fill destination:", e)
            browser.close()
            return
        
        # SKIP DATE SETTING - use default date
        print("Using default date from page...")
        
        # Click search
        print("Clicking search...")
        if not click_search_button(page):
            print("ERROR: Could not locate Search button.")
            browser.close()
            return
        
        # Wait for results
        print("Waiting for results to load...")
        wait_for_flight_results(page, timeout=45000)
        time.sleep(1)

        # Take screenshot for debugging
        page.screenshot(path="results_page.png", full_page=True)

        # Enhanced extraction with multiple strategies
        all_flights = []
        search_datetime_utc = datetime.now(timezone.utc).isoformat()

        # Strategy 1: Find by common class patterns
        selector_patterns = [
            "div[class*='flight-card']",
            "div[class*='flight-result']",
            "div[class*='result-card']",
            "div[class*='ticket']",
            "li[class*='flight']",
            "article",
            ".card",
            "[data-test*='flight']",
            "[data-testid*='flight']"
        ]

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

        # Strategy 2: Heuristic search if no cards found
        if not flight_cards:
            print("Using heuristic search for flight data...")
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

        print(f"Total flight cards found: {len(flight_cards)}")

        # Note: validate_flight_data and deduplicate_flights are imported from app.utils.validators

        # Extract data from cards with validation
        all_flights = []

        for idx, card in enumerate(flight_cards):
            try:
                card_text = card.inner_text()
                
                # Skip very short cards (likely not flight data)
                if len(card_text) < 30:
                    continue
                
                parsed = extract_flights_from_card_text(card_text)
                
                # Add metadata
                parsed["origin"] = ORIGIN
                parsed["destination"] = DESTINATION
                parsed["search_datetime_utc"] = search_datetime_utc
                
                # Validate flight data
                if validate_flight_data(parsed):
                    all_flights.append(parsed)
                    print(f"Extracted flight {len(all_flights)}: {parsed.get('airline')} "
                          f"[{parsed.get('flight_number', 'N/A')}] {parsed.get('departure')} - "
                          f"{parsed.get('price')}")
            except Exception as e:
                print(f"Error extracting flight card {idx}: {e}")
                continue

        # Deduplicate flights using centralized function
        all_flights = deduplicate_flights(all_flights)

        # Save output with metadata (matches API format)
        output_data = {
            "search_metadata": {
                "origin": ORIGIN,
                "destination": DESTINATION,
                "search_datetime_utc": search_datetime_utc,
                "total_flights_found": len(all_flights)
            },
            "flights": all_flights
        }
        
        out_path = "flight_results.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"✓ Successfully saved {len(all_flights)} flights to {out_path}")
        print(f"{'='*60}")

        if len(all_flights) > 0:
            print("\nSample flights:")
            for i, flight in enumerate(all_flights[:3], 1):
                print(f"\n{i}. {flight['airline']} [{flight.get('flight_number', 'N/A')}]")
                print(f"   {flight['departure']} → {flight['arrival']}")
                print(f"   Price: {flight['price']}")
            
            # Statistics
            prices = [f.get('price', 'N/A') for f in all_flights if f.get('price') != 'N/A']
            if prices:
                print(f"\nPrice range: {min(prices)} to {max(prices)}")
        else:
            print("No structured flights found - inspect results_page.png for debugging.")
            page.screenshot(path="results_page.png")

        print("\nKeeping browser open for 5 seconds...")
        time.sleep(5)
        browser.close()

if __name__ == "__main__":
    main()
