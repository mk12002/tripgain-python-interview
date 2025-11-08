"""
Main entry point for the Flight Search Application
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.flight_search_api import app
import uvicorn


def main():
    """
    Start the FastAPI application server
    """
    print("="*60)
    print("Flight Search API Server")
    print("="*60)
    print("\nStarting server at http://127.0.0.1:8000")
    print("API Documentation available at: http://127.0.0.1:8000/docs")
    print("="*60)
    
    uvicorn.run(
        "app.api.flight_search_api:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    main()
