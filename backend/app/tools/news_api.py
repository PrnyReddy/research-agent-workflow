import os
from newsapi import NewsApiClient
from dotenv import load_dotenv

from typing import Optional

load_dotenv()

API_KEY = os.getenv("NEWS_API_KEY")

class NewsAPIError(Exception):
    pass

def get_news_articles(query: str, num_articles: Optional[int] = 5) -> dict:
    """
    Fetches a specified number of recent news articles for a given query.
    Returns:
        dict: {"articles": list} or {"error": str}
    """
    if not API_KEY:
        return {"error": "NewsAPI key not found."}

    try:
        newsapi = NewsApiClient(api_key=API_KEY)
        top_headlines = newsapi.get_everything(
            q=query,
            language='en',
            sort_by='relevancy',
            page_size=num_articles
        )
        if top_headlines['status'] != 'ok':
            return {"error": "Failed to fetch news from NewsAPI."}
        articles = [
            {
                "title": article["title"],
                "description": article["description"],
                "url": article["url"],
                "source": article["source"]["name"],
            }
            for article in top_headlines["articles"]
        ]
        return {"articles": articles}
    except Exception as e:
        return {"error": f"NewsAPIError: {e}"}