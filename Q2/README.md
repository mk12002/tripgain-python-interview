# Q2 — Flight Search API (FastAPI + Playwright)

Short instructions to run the API that lives under `app`.

## Requirements

- Python 3.10+ (or a compatible 3.x)
- Install project dependencies (see `requirements.txt` in the repository root)
- Playwright browsers installed (used by the scraper)

## Quick start (Windows, cmd.exe)

1. Open a `cmd.exe` prompt and change to the Q2 folder:

    cd /d tripgain-python-interview\Q2

2. (Optional) Create and activate a virtual environment:

    python -m venv venv
    venv\Scripts\activate

3. Install dependencies (run from the repository root or adjust path to `requirements.txt`):

    pip install -r ..\requirements.txt

4. Install Playwright browsers (required for Playwright to run):

    python -m playwright install

5. Run the API using Uvicorn (from the `Q2` folder):

    uvicorn app.api.flight_search_api:app --reload

   By default Uvicorn will serve on http://127.0.0.1:8000

6. Try the API or the interactive docs:

   - API endpoint example (replace params as needed):

       http://127.0.0.1:8000/flight-search?origin=Bangalore&destination=Delhi&journey_date=2025-10-18

   - Interactive OpenAPI docs:

       http://127.0.0.1:8000/docs

## Notes & Troubleshooting

- Ensure you run the `uvicorn` command from the `Q2` folder so Python can import `app` correctly (`app` is the package under `Q2`).
- If Playwright raises errors about missing browsers, re-run `python -m playwright install`.
- If the scraper fails to load the target site, check Playwright/Chromium networking and whether the site requires additional headers or authentication.

## Minimal contract

- Input: query parameters `origin`, `destination`, `journey_date` (YYYY-MM-DD)
- Output: JSON with `search_metadata` and `flights` (see API response at `/docs`)

That's it — you can now run the API locally and use `/docs` to explore the endpoints.
