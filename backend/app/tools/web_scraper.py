import requests
from bs4 import BeautifulSoup

class WebScraperError(Exception):
    pass

def scrape_website(url: str) -> dict:
    """
    Scrapes the text content from a given URL.
    Returns:
        dict: {"content": str} or {"error": str}
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        text = soup.get_text(separator=' ', strip=True)
        return {"content": text}
    except requests.RequestException as e:
        return {"error": f"Error scraping website: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}