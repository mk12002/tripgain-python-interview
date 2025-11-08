import re
import time
from datetime import datetime, timezone
from typing import List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from playwright.sync_api import sync_playwright

# --- 1. Imports from your 'utils' modules ---
# Assumes the app is run from the root (where main.py is)
try:
    from app.utils.selectors import find_input_by_keywords, click_search_button, FLIGHT_CARD_SELECTORS
    from app.utils.extractors import extract_flights_from_card_text, find_flight_cards_by_selectors, find_flight_cards_heuristic
    from app.utils.validators import validate_flight_data, deduplicate_flights
    from app.utils.automation_helpers import set_date_input, wait_for_flight_results
    from app.config import TARGET_URL, DEFAULT_TIMEOUT, HEADLESS_MODE, SLOW_MO
except ImportError:
    # Fallback for local testing if needed
    from ..utils.selectors import find_input_by_keywords, click_search_button, FLIGHT_CARD_SELECTORS
    from ..utils.extractors import extract_flights_from_card_text, find_flight_cards_by_selectors, find_flight_cards_heuristic
    from ..utils.validators import validate_flight_data, deduplicate_flights
    from ..utils.automation_helpers import set_date_input, wait_for_flight_results
    from ..config import TARGET_URL, DEFAULT_TIMEOUT, HEADLESS_MODE, SLOW_MO


# --- 2. Pydantic Models for API Response ---
class Flight(BaseModel):
    airline: str
    flight_number: str
    departure: str
    arrival: str
    price: str
    origin: str
    destination: str
    search_datetime_utc: str  # Changed to match automation output


class SearchMetadata(BaseModel):
    origin: str
    destination: str
    journey_date: str
    search_datetime_utc: str
    total_flights_found: int


class FlightSearchResponse(BaseModel):
    search_metadata: SearchMetadata
    flights: List[Flight]


# --- 3. FastAPI App Initialization ---
# Note: If 'main.py' creates the app, this file should use an APIRouter
# But for a self-contained example, we create the app here.
app = FastAPI(
    title="Flight Search API",
    description="An API that scrapes flight data using Playwright.",
)


# --- 4. Core Scraper Logic (Orchestrator) ---
# Helper functions (set_date_input, wait_for_flight_results) are now imported from automation_helpers
def run_scraper(origin: str, destination: str, journey_date: str) -> List[dict]:
    """
    This function orchestrates the entire scraping process
    by calling the imported helper functions.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS_MODE, slow_mo=SLOW_MO)
        page = browser.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT)
        
        print(f"Loading BudgetTicket.in for {origin} -> {destination} on {journey_date}")
        try:
            page.goto(TARGET_URL, wait_until="domcontentloaded")
        except Exception as e:
            browser.close()
            raise HTTPException(status_code=503, detail="Scraping target site failed to load.")
        
        time.sleep(2)
        
        # Close modals
        try:
            for selector in ['button[aria-label="Close"]', 'button.close', 
                           '.modal button.close', 'button[title="Close"]']:
                try:
                    if page.locator(selector).count() > 0:
                        page.locator(selector).first.click(timeout=2000)
                        time.sleep(0.3)
                except: pass
        except: pass
        
        # --- Use imported selector functions ---
        print("Filling origin...")
        from_input = find_input_by_keywords(page, ["from", "origin", "departure"])
        if not from_input:
            browser.close()
            raise HTTPException(status_code=500, detail="Scraping failed: Could not find 'From' input.")
        
        try:
            from_input.click()
            from_input.fill("")
            from_input.type(origin, delay=60)
            time.sleep(0.8)
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            print("Origin filled.")
            time.sleep(1.0)
        except Exception as e:
            browser.close()
            raise HTTPException(status_code=500, detail=f"Scraping failed: Could not fill origin: {e}")
        
        print("Filling destination...")
        to_input = find_input_by_keywords(page, ["to", "destination", "arrival"])
        if not to_input:
            browser.close()
            raise HTTPException(status_code=500, detail="Scraping failed: Could not find 'To' input.")
        
        try:
            to_input.click()
            to_input.fill("")
            to_input.type(destination, delay=60)
            time.sleep(0.8)
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            print("Destination filled.")
            time.sleep(1.0)
        except Exception as e:
            browser.close()
            raise HTTPException(status_code=500, detail=f"Scraping failed: Could not fill destination: {e}")
        
        # -----------------------------------------------------------------
        # --- MODIFICATION: Skipping date input as requested ---
        # -----------------------------------------------------------------
        print("Skipping date input, using website default.")
        # print("Setting journey date...")
        # if not set_date_input(page, journey_date):
        #     browser.close()
        #     raise HTTPException(status_code=500, detail="Scraping failed: Could not set date.")
        
        time.sleep(1.0)

        print("Clicking search...")
        if not click_search_button(page):
            browser.close()
            raise HTTPException(status_code=500, detail="Scraping failed: Could not locate Search button.")
        
        print("Waiting for results to load...")
        wait_for_flight_results(page, timeout=45000)
        time.sleep(1)

        # --- Use imported extractor functions ---
        search_datetime = datetime.now(timezone.utc).isoformat()
        
        flight_cards = find_flight_cards_by_selectors(page, FLIGHT_CARD_SELECTORS)
        
        if not flight_cards:
            print("No cards found with primary selectors, trying heuristic search...")
            flight_cards = find_flight_cards_heuristic(page)
        
        print(f"Total flight cards found: {len(flight_cards)}")

        all_parsed_flights = []
        for idx, card in enumerate(flight_cards):
            try:
                card_text = card.inner_text()
                if len(card_text) < 30: continue
                
                parsed = extract_flights_from_card_text(card_text)
                
                parsed["origin"] = origin
                parsed["destination"] = destination
                parsed["search_datetime_utc"] = search_datetime  # Changed to match Pydantic model
                
                # --- Use imported validator function ---
                if validate_flight_data(parsed):
                    all_parsed_flights.append(parsed)
            except Exception as e:
                print(f"Error extracting flight card {idx}: {e}")
                continue
        
        # --- Use imported validator function ---
        valid_flights = deduplicate_flights(all_parsed_flights)
        
        browser.close()
        print(f"Scraping complete. Found {len(valid_flights)} unique flights.")
        return valid_flights


# --- 6. FastAPI Endpoint ---
@app.get(
    "/flight-search",
    response_model=FlightSearchResponse,
    summary="Search for flights",
    description="Runs a Playwright scraper to find flight details."
)
def search_flights(
    origin: str = Query(..., description="Departure city", example="Bangalore"),
    destination: str = Query(..., description="Arrival city", example="Delhi"),
    journey_date: str = Query(..., description="Journey date in YYYY-MM-DD format", example="2025-10-18")
):
    """
    Searches for flights by running the Playwright web scraper.
    Returns a unified response format with metadata and flight list.
    """
    try:
        datetime.strptime(journey_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Please use YYYY-MM-DD."
        )
    
    print(f"API call received for {origin} -> {destination} on {journey_date}")
    search_timestamp = datetime.now(timezone.utc).isoformat()

    try:
        flights = run_scraper(origin, destination, journey_date)
        
        if not flights:
            raise HTTPException(
                status_code=404,
                detail=f"No flights found for {origin} to {destination} on {journey_date}."
            )
        
        # Return unified response format matching automation output
        return FlightSearchResponse(
            search_metadata=SearchMetadata(
                origin=origin,
                destination=destination,
                journey_date=journey_date,
                search_datetime_utc=search_timestamp,
                total_flights_found=len(flights)
            ),
            flights=flights
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred: {e}"
        )

# --- To run this app ---
# This assumes your 'main.py' file will import 'app' from this file
# and run it with uvicorn.
#
# If this file is meant to be run directly:
# 1. Save as app/api/flight_search_api.py
# 2. Run from the *root* directory (the one containing 'main.py'):
#    uvicorn app.api.flight_search_api:app --reload