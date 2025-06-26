import requests
from bs4 import BeautifulSoup

def scrape_website(url: str) -> str:
    """
    Scrapes the text content from a given URL.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        text = soup.get_text(separator=' ', strip=True)
        return text
    except requests.RequestException as e:
        return f"Error scraping website: {e}"