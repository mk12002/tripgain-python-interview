import os
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup
from dotenv import load_dotenv  # <-- 1. ADD THIS IMPORT

def configure_api():
    """
    Configures the Gemini API by loading the key from a .env file.
    """
    load_dotenv()  # <-- 2. ADD THIS LINE
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found. "
                         "Make sure you have a .env file in the same directory "
                         "with 'GOOGLE_API_KEY=YOUR_KEY'")
    genai.configure(api_key=api_key)

def fetch_and_clean_content(url: str) -> str:
    """
    Fetches content from a URL and cleans it to extract main text.
    
    Args:
        url: The webpage URL to scrape.

    Returns:
        The cleaned, text-only content from the webpage.
    """
    try:
        # Add headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)  # Pass headers here
        response.raise_for_status()  # Check for HTTP errors

        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # --- HTML Cleaning ---
        # Remove all script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # For Wikipedia, the main content is in <div id="mw-content-text">
        # This is a robust way to get *only* the article
        main_content = soup.find('div', id='mw-content-text')

        if not main_content:
            # Fallback if the specific ID isn't found (e.g., for BBC/CNN)
            main_content = soup.body
            # Remove common irrelevant tags
            for tag in main_content(["nav", "header", "footer", "aside"]):
                tag.decompose()

        # Get text, separated by spaces, and strip whitespace
        text = main_content.get_text(separator=" ", strip=True)
        
        # Limit the text to avoid overwhelming the API (e.g., first 50k chars)
        # This is a practical step for very long articles.
        return text[:50000]

    except requests.exceptions.RequestException as e:
        print(f"Error fetching webpage: {e}")
        return None

def create_prompt(text_content: str) -> str:
    """
    Creates the custom prompt for Gemini.
    """
    
    # This is the prompt design from Q3
    prompt = f"""
    You are an expert technology analyst. Your task is to analyze the 
    following webpage content about Artificial Intelligence and distill 
    it into a concise, structured briefing.

    Focus on the key capabilities, applications, and ethical challenges 
    presented in the text.

    Your response *must* follow this exact format:

    Summary:
    • <point 1>
    • <point 2>
    • <point 3>
    • <point 4>
    • <point 5>
    Insight:
    <single-line insight interpreting the overall theme or trend>

    ---
    Here is the text to analyze:
    {text_content}
    ---
    """
    return prompt

def get_gemini_analysis(prompt: str) -> str:
    """
    Sends the prompt to the Gemini 1.5 Flash model and gets the response.
    
    Note: User requested "2.5 Flash". As of now, the latest available 
    flash model is 'gemini-1.5-flash-latest'. This script uses that.
    """
    try:
        # Use the latest 1.5 Flash model for speed and capability
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # We only want the text, no complex chat history
        response = model.generate_content(prompt)
        
        return response.text
    
    except Exception as e:
        print(f"Error generating content from Gemini: {e}")
        return None

def save_output(content: str, filename: str = "summary_output.txt"):
    """
    Saves the provided content to a text file.
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\nSuccessfully saved output to {filename}")
    except IOError as e:
        print(f"Error saving output to file: {e}")

# --- Main execution ---
if __name__ == "__main__":
    
    # 1. Configure the API
    try:
        configure_api()
    except ValueError as e:
        print(e)
        exit(1)

    # 2. Define the source URL
    # We use the stable Wikipedia link as it's great for summarization.
    URL_TO_ANALYZE = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    
    print(f"Fetching and cleaning content from: {URL_TO_ANALYZE}")
    
    # 3. Fetch and clean
    cleaned_text = fetch_and_clean_content(URL_TO_ANALYZE)
    
    if cleaned_text:
        print("Content cleaned. Sending to Gemini for analysis...")
        
        # 4. Create the custom prompt
        analysis_prompt = create_prompt(cleaned_text)
        
        # 5. Get the analysis from Gemini
        result = get_gemini_analysis(analysis_prompt)
        
        if result:
            # 6. Print result to console (matches required format)
            print("--- Gemini Analysis Result ---")
            print(result)
            
            # 7. Save the result to the output file
            save_output(result)
        else:
            print("Could not get analysis from Gemini.")
    else:
        print("Could not fetch or clean webpage content.")