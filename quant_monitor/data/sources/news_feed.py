"""News feeds via Google RSS and other sources.

Aggregates news from multiple RSS sources for sentiment analysis.
Uses feedparser for robust RSS/Atom parsing.
"""

from __future__ import annotations

import logging
import re
import urllib.parse
from datetime import UTC, datetime, timedelta
from typing import Any

import feedparser
import httpx

from quant_monitor.data.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

# Google News RSS base URL
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"

# Financial news RSS feeds
FINANCIAL_RSS_FEEDS = {
    "yahoo_finance": "https://finance.yahoo.com/news/rssindex",
    "marketwatch": "https://www.marketwatch.com/rss/topstories",
    "cnbc": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "reuters_business": "https://news.google.com/rss/search?q=site:reuters.com+business",
    "bloomberg": "https://news.google.com/rss/search?q=site:bloomberg.com+markets",
}

# Sector-specific keywords for filtering
SECTOR_KEYWORDS = {
    "tech": ["AI", "artificial intelligence", "semiconductor", "chip", "GPU", "data center"],
    "defense": ["defense", "military", "aerospace", "pentagon", "contracting"],
    "finance": ["banking", "fed", "interest rate", "treasury", "financial"],
    "consumer": ["retail", "consumer", "spending", "inflation", "walmart"],
    "healthcare": ["pharma", "biotech", "FDA", "drug", "healthcare"],
    "energy": ["oil", "gas", "energy", "renewable", "EV", "battery"],
}


class NewsFeed:
    """News aggregator from multiple RSS sources."""

    def __init__(self) -> None:
        """Initialize news feed."""
        self._client = httpx.Client(
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; QuantMonitor/1.0)",
            },
            timeout=30.0,
            follow_redirects=True,
        )

    def __del__(self):
        """Close HTTP client."""
        if hasattr(self, "_client"):
            self._client.close()

    def _parse_feed(self, url: str) -> list[dict[str, Any]]:
        """Parse an RSS/Atom feed URL.
        
        Args:
            url: Feed URL
            
        Returns:
            List of article dicts
        """
        try:
            response = self._client.get(url)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
            
            articles = []
            for entry in feed.entries:
                # Parse publication date
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6], tzinfo=UTC)
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6], tzinfo=UTC)
                
                articles.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "published": published,
                    "source": feed.feed.get("title", ""),
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error parsing feed {url}: {e}")
            return []

    @rate_limiter.rate_limited("google_rss")
    def search_google_news(
        self,
        query: str,
        when: str = "7d",
        language: str = "en",
    ) -> list[dict[str, Any]]:
        """Search Google News RSS.
        
        Args:
            query: Search query (can include ticker, company name, keywords)
            when: Time range (1h, 1d, 7d, 1m)
            language: Language code
            
        Returns:
            List of news article dicts
        """
        params = {
            "q": query,
            "hl": f"{language}-US",
            "gl": "US",
            "ceid": "US:en",
        }
        
        # Add time filter
        if when:
            params["q"] = f"{query} when:{when}"
        
        url = f"{GOOGLE_NEWS_RSS}?{urllib.parse.urlencode(params)}"
        return self._parse_feed(url)

    def get_ticker_news(
        self,
        ticker: str,
        company_name: str | None = None,
        limit: int = 20,
        since_days: int = 7,
    ) -> list[dict[str, Any]]:
        """Get news for a specific ticker/company.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Full company name (improves search quality)
            limit: Max articles to return
            since_days: Only include articles from last N days
            
        Returns:
            List of news articles sorted by date
        """
        # Build search query
        query_parts = [f"${ticker}"]
        if company_name:
            # Add company name without common suffixes
            clean_name = re.sub(r"\s+(Inc\.?|Corp\.?|Ltd\.?|Co\.?|LLC|PLC)$", "", company_name, flags=re.I)
            query_parts.append(f'"{clean_name}"')
        
        query = " OR ".join(query_parts)
        
        # Map days to Google time format
        if since_days <= 1:
            when = "1d"
        elif since_days <= 7:
            when = "7d"
        else:
            when = "1m"
        
        articles = self.search_google_news(query, when=when)
        
        # Filter by date and limit
        cutoff = datetime.now(UTC) - timedelta(days=since_days)
        filtered = []
        for article in articles:
            if article["published"] and article["published"] < cutoff:
                continue
            filtered.append(article)
            if len(filtered) >= limit:
                break
        
        logger.info(f"Found {len(filtered)} news articles for {ticker}")
        return filtered

    def get_portfolio_news(
        self,
        holdings: dict[str, dict[str, Any]],
        limit_per_ticker: int = 5,
        since_days: int = 3,
    ) -> dict[str, list[dict[str, Any]]]:
        """Get news for all portfolio holdings.
        
        Args:
            holdings: Dict mapping ticker -> holding info (with 'name' key)
            limit_per_ticker: Max articles per ticker
            since_days: Look back period
            
        Returns:
            Dict mapping ticker -> list of articles
        """
        results = {}
        for ticker, info in holdings.items():
            company_name = info.get("name")
            articles = self.get_ticker_news(
                ticker,
                company_name=company_name,
                limit=limit_per_ticker,
                since_days=since_days,
            )
            results[ticker] = articles
        return results

    @rate_limiter.rate_limited("google_rss")
    def get_sector_news(
        self,
        sector: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get news for a market sector.
        
        Args:
            sector: Sector name (tech, defense, finance, consumer, healthcare, energy)
            limit: Max articles to return
            
        Returns:
            List of news articles
        """
        keywords = SECTOR_KEYWORDS.get(sector.lower(), [])
        if not keywords:
            logger.warning(f"Unknown sector: {sector}")
            return []
        
        query = " OR ".join(f'"{kw}"' for kw in keywords[:5])
        articles = self.search_google_news(f"stock market ({query})", when="7d")
        
        return articles[:limit]

    @rate_limiter.rate_limited("google_rss")
    def get_market_news(self, limit: int = 30) -> list[dict[str, Any]]:
        """Get general market news.
        
        Args:
            limit: Max articles to return
            
        Returns:
            List of market news articles
        """
        queries = [
            "stock market today",
            "S&P 500",
            "federal reserve interest rates",
        ]
        
        all_articles = []
        for query in queries:
            articles = self.search_google_news(query, when="1d")
            all_articles.extend(articles)
        
        # Deduplicate by title
        seen_titles = set()
        unique = []
        for article in all_articles:
            title_key = article["title"].lower()[:50]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique.append(article)
        
        # Sort by date
        unique.sort(key=lambda x: x["published"] or datetime.min.replace(tzinfo=UTC), reverse=True)
        
        return unique[:limit]

    def get_financial_feed(
        self,
        feed_name: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get articles from a specific financial news feed.
        
        Args:
            feed_name: Feed identifier (yahoo_finance, marketwatch, cnbc, etc.)
            limit: Max articles to return
            
        Returns:
            List of news articles
        """
        url = FINANCIAL_RSS_FEEDS.get(feed_name)
        if not url:
            logger.warning(f"Unknown feed: {feed_name}")
            return []
        
        articles = self._parse_feed(url)
        return articles[:limit]

    def get_all_financial_news(self, limit_per_feed: int = 10) -> list[dict[str, Any]]:
        """Aggregate news from all financial feeds.
        
        Args:
            limit_per_feed: Max articles per feed
            
        Returns:
            Combined and deduplicated list of articles
        """
        all_articles = []
        
        for feed_name in FINANCIAL_RSS_FEEDS:
            articles = self.get_financial_feed(feed_name, limit_per_feed)
            all_articles.extend(articles)
        
        # Deduplicate
        seen = set()
        unique = []
        for article in all_articles:
            key = article["link"]
            if key not in seen:
                seen.add(key)
                unique.append(article)
        
        # Sort by date
        unique.sort(key=lambda x: x["published"] or datetime.min.replace(tzinfo=UTC), reverse=True)
        
        return unique

    def extract_tickers_from_text(self, text: str) -> list[str]:
        """Extract stock ticker symbols from text.
        
        Args:
            text: Text to search (title, summary, etc.)
            
        Returns:
            List of potential ticker symbols
        """
        # Match $TICKER or standalone uppercase 1-5 letter words
        patterns = [
            r"\$([A-Z]{1,5})\b",  # $AAPL format
            r"\b([A-Z]{2,5})\b(?:\s+(?:stock|shares|Inc|Corp))",  # AAPL stock
        ]
        
        tickers = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            tickers.update(matches)
        
        return list(tickers)


def create_news_feed() -> NewsFeed:
    """Factory function to create a NewsFeed instance.
    
    Returns:
        Configured NewsFeed instance
    """
    return NewsFeed()


# Module-level convenience instance
_feed: NewsFeed | None = None


def get_news_feed() -> NewsFeed:
    """Get or create the global NewsFeed instance."""
    global _feed
    if _feed is None:
        _feed = create_news_feed()
    return _feed
