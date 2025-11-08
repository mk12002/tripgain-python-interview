"""
Selectors module for finding elements on web pages
"""

def find_input_by_keywords(page, keywords):
    """
    Iterate through inputs on the page and return the first input element
    whose id/name/placeholder/aria-label/textContent contains any keyword.
    Returns a Playwright element handle or None.
    """
    inputs = page.query_selector_all("input, textarea")
    for el in inputs:
        try:
            attrs = {}
            for attr in ("id", "name", "placeholder", "aria-label", "type", "value"):
                try:
                    attrs[attr] = el.get_attribute(attr) or ""
                except:
                    attrs[attr] = ""
            # also try a short visible label text if available via nearest label
            label_text = ""
            try:
                lbl = page.evaluate(
                    "(el) => { const l = el.closest('label'); return l ? l.innerText : ''; }",
                    el,
                ) or ""
                label_text = lbl
            except:
                label_text = ""
            hay = " ".join([attrs[a].lower() for a in attrs]) + " " + label_text.lower()
            for kw in keywords:
                if kw.lower() in hay:
                    return el
        except:
            continue
    return None


def click_search_button(page):
    """
    Find and click the search button using multiple strategies
    """
    # Try many button finds
    buttons = page.query_selector_all("button, input[type=button], input[type=submit]")
    for b in buttons:
        try:
            txt = (b.inner_text() or b.get_attribute("value") or "").strip().lower()
            if "search" in txt or "find" in txt:
                b.scroll_into_view_if_needed()
                b.click(timeout=8000)
                return True
        except:
            continue
    # fallback: try click a button with common ids
    for sel in ("#searchBtn", "#btnSearch", "button.search", "button[aria-label*='Search']"):
        try:
            if page.locator(sel).count() > 0:
                page.locator(sel).first.click(timeout=8000)
                return True
        except:
            continue
    return False


# Common selector patterns for flight cards
FLIGHT_CARD_SELECTORS = [
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
