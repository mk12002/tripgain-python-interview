"""
Automation helper functions for browser interactions
"""
import time
from datetime import datetime, timedelta


def set_date_input(page, journey_date_str: str = None, days_from_today: int = 7):
    """
    Enhanced date setting with multiple strategies for Angular/dynamic sites.
    Can accept either a specific date string (YYYY-MM-DD) or days from today.
    
    Args:
        page: Playwright page object
        journey_date_str: Optional date string in YYYY-MM-DD format
        days_from_today: Number of days from today (default: 7)
    
    Returns:
        bool: True if date was set successfully, False otherwise
    """
    # Import here to avoid circular dependencies
    try:
        from app.utils.selectors import find_input_by_keywords
    except ImportError:
        from .selectors import find_input_by_keywords
    
    # Determine target date
    if journey_date_str:
        try:
            target_date = datetime.strptime(journey_date_str, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid date format: {journey_date_str}. Expected YYYY-MM-DD.")
            return False
    else:
        target_date = (datetime.now() + timedelta(days=days_from_today)).date()

    # Strategy 1: Try direct input field
    date_keywords = ["date", "journey", "travel", "depart", "departure", "when"]
    date_input = find_input_by_keywords(page, date_keywords)

    if date_input:
        try:
            # Make input visible and editable
            page.evaluate("""(el) => {
                el.removeAttribute('readonly');
                el.removeAttribute('disabled');
                el.style.display = 'block';
            }""", date_input)

            date_input.click()
            time.sleep(0.5)

            # Clear and set value
            date_input.fill("")
            formats_to_try = [
                target_date.strftime("%d-%m-%Y"),
                target_date.strftime("%d/%m/%Y"),
                target_date.strftime("%Y-%m-%d"),
                target_date.strftime("%d %b %Y"),
            ]

            for fmt in formats_to_try:
                page.evaluate("""(el, val) => {
                    el.value = val;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new Event('blur', { bubbles: true }));
                }""", date_input, fmt)
                time.sleep(0.3)

            # Press Enter to close potential pickers
            date_input.press("Enter")
            print(f"Date set to: {target_date.strftime('%Y-%m-%d')}")
            return True
        except Exception as e:
            print(f"Date input strategy 1 failed: {e}")

    # Strategy 2: Look for datepicker widget and click future date
    try:
        print("Date input Strategy 1 failed, trying Strategy 2 (widget click)...")
        # Try to find and click a date picker trigger
        date_triggers = [
            "button[aria-label*='date']",
            "input[placeholder*='date']",
            ".datepicker-trigger",
            "[class*='calendar']",
            "[class*='date-picker']"
        ]

        for trigger in date_triggers:
            if page.locator(trigger).count() > 0:
                page.locator(trigger).first.click(timeout=3000)
                time.sleep(1)

                # Try to click a future date in calendar
                future_day = str(target_date.day)
                day_selectors = [
                    f"td[data-day='{future_day}']:not(.disabled)",
                    f".day:has-text('{future_day}'):not(.disabled)",
                    f"button:has-text('{future_day}')",
                ]

                for sel in day_selectors:
                    try:
                        if page.locator(sel).count() > 0:
                            page.locator(sel).first.click(timeout=2000)
                            print(f"Date clicked in calendar widget: {target_date}")
                            return True
                    except:
                        continue
    except Exception as e:
        print(f"Date picker widget strategy failed: {e}")

    return False


def wait_for_flight_results(page, timeout=30000):
    """
    Wait for flight results by monitoring network activity and DOM changes.
    
    Args:
        page: Playwright page object
        timeout: Maximum time to wait in milliseconds (default: 30000)
    
    Returns:
        bool: True if results detected, False otherwise
    """
    try:
        # Strategy 1: Wait for network idle (API calls complete)
        page.wait_for_load_state("networkidle", timeout=timeout)
        time.sleep(2)

        # Strategy 2: Wait for specific result indicators
        result_indicators = [
            "[class*='flight']",
            "[class*='result']",
            "[data-flight]",
            ".card",
            "article",
            "[role='listitem']"
        ]

        for indicator in result_indicators:
            try:
                if page.locator(indicator).count() > 0:
                    # Wait for at least 1 item to appear
                    page.wait_for_function(
                        f"document.querySelectorAll('{indicator}').length >= 1",
                        timeout=10000
                    )
                    return True
            except Exception:
                continue

        # Strategy 3: Wait for price text to appear (fallback)
        page.wait_for_function(
            "document.body.innerText.includes('₹') || document.body.innerText.includes('Rs')",
            timeout=15000
        )
        return True
    except Exception as e:
        print(f"Wait for results warning: {e}")
        return False


def log_page_state(page, stage: str):
    """
    Log page state for debugging purposes.
    
    Args:
        page: Playwright page object
        stage: Description of current stage (e.g., "after_origin_fill")
    """
    try:
        url = page.url
        title = page.title()
        print(f"[{stage}] URL: {url}")
        print(f"[{stage}] Title: {title}")
        
        # Check for common error keywords
        body_text = page.locator("body").inner_text().lower()
        error_keywords = ["error", "invalid", "not found", "failed"]
        for keyword in error_keywords:
            if keyword in body_text:
                print(f"[{stage}] WARNING: Found '{keyword}' in page content")
    except Exception as e:
        print(f"[{stage}] Could not log page state: {e}")
