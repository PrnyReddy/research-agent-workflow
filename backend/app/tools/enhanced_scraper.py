import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional
from urllib.parse import urlparse
import time

class EnhancedWebScraper:
    """
    Enhanced web scraper with better error handling, content cleaning, and metadata extraction.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common web artifacts
        text = re.sub(r'cookie|privacy|terms|conditions', '', text, flags=re.IGNORECASE)
        
        # Remove navigation elements
        text = re.sub(r'menu|navigation|sidebar|footer|header', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, str]:
        """Extract metadata from the webpage."""
        metadata = {
            "title": "",
            "description": "",
            "keywords": "",
            "author": "",
            "url": url
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata["title"] = title_tag.get_text().strip()
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            metadata["description"] = meta_desc.get('content', '').strip()
        
        # Extract keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            metadata["keywords"] = meta_keywords.get('content', '').strip()
        
        # Extract author
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author:
            metadata["author"] = meta_author.get('content', '').strip()
        
        return metadata
    
    def extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from the webpage."""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Try to find main content areas
        main_selectors = [
            'main',
            '[role="main"]',
            '.main-content',
            '.content',
            '#content',
            'article',
            '.post-content',
            '.entry-content'
        ]
        
        main_content = ""
        for selector in main_selectors:
            element = soup.select_one(selector)
            if element:
                main_content = element.get_text()
                break
        
        # If no main content found, get body text
        if not main_content:
            main_content = soup.get_text()
        
        return self.clean_text(main_content)
    
    def scrape_website(self, url: str, timeout: int = 15) -> Dict[str, any]:
        """
        Enhanced website scraping with better error handling and content extraction.
        
        Args:
            url: The URL to scrape
            timeout: Request timeout in seconds
            
        Returns:
            Dict containing scraped content and metadata
        """
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme:
                url = f"https://{url}"
            
            # Make request with timeout and retry
            for attempt in range(2):
                try:
                    response = self.session.get(url, timeout=timeout)
                    response.raise_for_status()
                    break
                except requests.RequestException as e:
                    if attempt == 1:  # Last attempt
                        return {"error": f"Failed to fetch URL after retries: {str(e)}"}
                    time.sleep(1)  # Wait before retry
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content and metadata
            content = self.extract_main_content(soup)
            metadata = self.extract_metadata(soup, url)
            
            # Limit content length to avoid token limits
            if len(content) > 8000:
                content = content[:8000] + "... [Content truncated]"
            return {
                "content": content,
                "metadata": metadata,
                "url": url,
                "status": "success",
                "content_length": len(content)
            }
            
        except requests.RequestException as e:
            return {"error": f"Request error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

# Global instance
enhanced_scraper = EnhancedWebScraper()

def scrape_website_enhanced(url: str) -> Dict[str, any]:
    """
    Enhanced website scraping function for use with LangChain tools.
    
    Args:
        url: The URL to scrape
        
    Returns:
        Dict containing scraped content and metadata
    """
    return enhanced_scraper.scrape_website(url) 