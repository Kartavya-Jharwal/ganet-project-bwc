"""SEC EDGAR data feed — filings, ownership changes, and company facts.

Uses SEC EDGAR REST API with proper rate limiting (10 req/sec max).
Follow SEC's fair access policy by including User-Agent with contact info.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any

import httpx

from quant_monitor.data.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

# SEC EDGAR API endpoints
SEC_BASE_URL = "https://data.sec.gov"
SEC_SUBMISSIONS_URL = f"{SEC_BASE_URL}/submissions"
SEC_COMPANY_FACTS_URL = f"{SEC_BASE_URL}/api/xbrl/companyfacts"

# Filing types we care about
IMPORTANT_FILINGS = {
    "10-K": "Annual Report",
    "10-Q": "Quarterly Report",
    "8-K": "Current Report (material events)",
    "4": "Insider Trading",
    "13F-HR": "Institutional Holdings",
    "SC 13G": "Beneficial Ownership (>5%)",
    "SC 13D": "Beneficial Ownership (activist)",
    "DEF 14A": "Proxy Statement",
}

# Ticker to CIK mapping (populated dynamically)
_CIK_CACHE: dict[str, str] = {}


class SecEdgarFeed:
    """SEC EDGAR data feed with rate limiting."""

    def __init__(self, user_agent: str | None = None) -> None:
        """Initialize SEC EDGAR feed.
        
        Args:
            user_agent: SEC requires User-Agent header with contact info.
                        Format: "Company Name contact@email.com"
                        Reads from SEC_EDGAR_USER_AGENT env var if not provided.
        """
        self.user_agent = user_agent or os.environ.get("SEC_EDGAR_USER_AGENT")
        
        if not self.user_agent:
            logger.warning(
                "SEC_EDGAR_USER_AGENT not set. SEC API requires a User-Agent. "
                "Set it to: 'Your Name your.email@domain.com'"
            )
        
        self._client = httpx.Client(
            headers={"User-Agent": self.user_agent} if self.user_agent else {},
            timeout=30.0,
        )

    def __del__(self):
        """Close HTTP client on cleanup."""
        if hasattr(self, "_client"):
            self._client.close()

    @property
    def is_available(self) -> bool:
        """Check if SEC feed is available (has user agent)."""
        return bool(self.user_agent)

    @rate_limiter.rate_limited("sec_edgar")
    def _get(self, url: str) -> dict | list | None:
        """Make a rate-limited GET request to SEC API."""
        if not self.user_agent:
            logger.error("Cannot make SEC request without User-Agent")
            return None
            
        try:
            response = self._client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"SEC API error: {e.response.status_code} for {url}")
            return None
        except Exception as e:
            logger.error(f"SEC request failed: {e}")
            return None

    def get_cik(self, ticker: str) -> str | None:
        """Convert ticker symbol to CIK (Central Index Key).
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            10-digit CIK string (zero-padded) or None
        """
        ticker = ticker.upper()
        
        # Check cache first
        if ticker in _CIK_CACHE:
            return _CIK_CACHE[ticker]
        
        # Fetch company tickers mapping
        url = "https://www.sec.gov/files/company_tickers.json"
        data = self._get(url)
        
        if not data:
            return None
        
        # Build cache and find ticker
        for entry in data.values():
            t = entry.get("ticker", "").upper()
            cik = str(entry.get("cik_str", "")).zfill(10)
            _CIK_CACHE[t] = cik
            
        return _CIK_CACHE.get(ticker)

    @rate_limiter.rate_limited("sec_edgar")
    def get_company_submissions(self, ticker: str) -> dict[str, Any] | None:
        """Get all SEC filings for a company.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with company info and recent filings
        """
        cik = self.get_cik(ticker)
        if not cik:
            logger.error(f"Could not find CIK for {ticker}")
            return None
        
        url = f"{SEC_SUBMISSIONS_URL}/CIK{cik}.json"
        return self._get(url)

    def get_recent_filings(
        self,
        ticker: str,
        filing_types: list[str] | None = None,
        limit: int = 20,
        since_days: int = 90,
    ) -> list[dict[str, Any]]:
        """Get recent SEC filings for a company.
        
        Args:
            ticker: Stock ticker symbol
            filing_types: Filter to specific types (e.g., ["10-K", "8-K"])
            limit: Max filings to return
            since_days: Only include filings from last N days
            
        Returns:
            List of filing dicts with type, date, description, url
        """
        data = self.get_company_submissions(ticker)
        if not data or "filings" not in data:
            return []
        
        filings_data = data["filings"].get("recent", {})
        
        # Parse filings
        forms = filings_data.get("form", [])
        dates = filings_data.get("filingDate", [])
        accessions = filings_data.get("accessionNumber", [])
        primary_docs = filings_data.get("primaryDocument", [])
        descriptions = filings_data.get("primaryDocDescription", [])
        
        cutoff = datetime.now() - timedelta(days=since_days)
        cik = self.get_cik(ticker)
        
        filings = []
        for i in range(len(forms)):
            form = forms[i]
            
            # Filter by type if specified
            if filing_types and form not in filing_types:
                continue
            
            # Parse date
            try:
                date = datetime.strptime(dates[i], "%Y-%m-%d")
                if date < cutoff:
                    continue
            except (ValueError, IndexError):
                continue
            
            # Build SEC filing URL
            accession = accessions[i].replace("-", "")
            primary_doc = primary_docs[i] if i < len(primary_docs) else ""
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_doc}"
            
            filings.append({
                "form": form,
                "form_description": IMPORTANT_FILINGS.get(form, form),
                "date": dates[i],
                "description": descriptions[i] if i < len(descriptions) else "",
                "accession_number": accessions[i],
                "url": filing_url,
            })
            
            if len(filings) >= limit:
                break
        
        logger.info(f"Found {len(filings)} recent filings for {ticker}")
        return filings

    def get_insider_transactions(
        self,
        ticker: str,
        limit: int = 20,
        since_days: int = 90,
    ) -> list[dict[str, Any]]:
        """Get recent Form 4 (insider trading) filings.
        
        Args:
            ticker: Stock ticker symbol
            limit: Max transactions to return
            since_days: Only include from last N days
            
        Returns:
            List of insider transaction dicts
        """
        return self.get_recent_filings(
            ticker,
            filing_types=["4", "3", "5"],
            limit=limit,
            since_days=since_days,
        )

    def get_8k_filings(
        self,
        ticker: str,
        limit: int = 10,
        since_days: int = 30,
    ) -> list[dict[str, Any]]:
        """Get recent 8-K (material event) filings.
        
        8-Ks report significant events like:
        - Earnings announcements
        - Material agreements
        - Leadership changes
        - Mergers/acquisitions
        
        Args:
            ticker: Stock ticker symbol
            limit: Max filings to return
            since_days: Only include from last N days
            
        Returns:
            List of 8-K filing dicts
        """
        return self.get_recent_filings(
            ticker,
            filing_types=["8-K", "8-K/A"],
            limit=limit,
            since_days=since_days,
        )

    @rate_limiter.rate_limited("sec_edgar")
    def get_company_facts(self, ticker: str) -> dict[str, Any] | None:
        """Get XBRL company facts (financial data).
        
        Returns standardized financial metrics like revenue, EPS, etc.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with company facts organized by taxonomy
        """
        cik = self.get_cik(ticker)
        if not cik:
            return None
        
        url = f"{SEC_COMPANY_FACTS_URL}/CIK{cik}.json"
        return self._get(url)

    def get_financials(
        self,
        ticker: str,
        metrics: list[str] | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Get financial metrics from SEC filings.
        
        Args:
            ticker: Stock ticker symbol
            metrics: Specific metrics to fetch (e.g., ["Revenues", "NetIncomeLoss"])
                    If None, returns common metrics.
                    
        Returns:
            Dict mapping metric name -> list of values with dates
        """
        if metrics is None:
            metrics = [
                "Revenues",
                "NetIncomeLoss",
                "EarningsPerShareBasic",
                "EarningsPerShareDiluted",
                "Assets",
                "Liabilities",
                "StockholdersEquity",
                "OperatingIncomeLoss",
                "CashAndCashEquivalentsAtCarryingValue",
            ]
        
        facts = self.get_company_facts(ticker)
        if not facts:
            return {}
        
        results = {}
        
        # Navigate the facts structure
        us_gaap = facts.get("facts", {}).get("us-gaap", {})
        
        for metric in metrics:
            if metric not in us_gaap:
                continue
                
            metric_data = us_gaap[metric]
            units = metric_data.get("units", {})
            
            # Try USD first, then shares
            values = units.get("USD", units.get("USD/shares", []))
            
            # Filter to 10-K and 10-Q filings
            filtered = [
                {
                    "value": v["val"],
                    "end_date": v.get("end"),
                    "form": v.get("form"),
                    "filed": v.get("filed"),
                    "fiscal_year": v.get("fy"),
                    "fiscal_period": v.get("fp"),
                }
                for v in values
                if v.get("form") in ["10-K", "10-Q"]
            ]
            
            if filtered:
                results[metric] = sorted(filtered, key=lambda x: x["end_date"], reverse=True)
        
        return results

    def get_filings_summary(
        self,
        tickers: list[str],
        since_days: int = 30,
    ) -> dict[str, list[dict[str, Any]]]:
        """Get filing summary for multiple tickers.
        
        Args:
            tickers: List of ticker symbols
            since_days: Look back period
            
        Returns:
            Dict mapping ticker -> list of recent important filings
        """
        results = {}
        for ticker in tickers:
            filings = self.get_recent_filings(
                ticker,
                filing_types=list(IMPORTANT_FILINGS.keys()),
                limit=10,
                since_days=since_days,
            )
            results[ticker] = filings
        return results


def create_sec_feed(user_agent: str | None = None) -> SecEdgarFeed:
    """Factory function to create a SecEdgarFeed instance.
    
    Args:
        user_agent: SEC User-Agent string. Reads from env var if not provided.
        
    Returns:
        Configured SecEdgarFeed instance
    """
    return SecEdgarFeed(user_agent=user_agent)


# Module-level convenience instance
_feed: SecEdgarFeed | None = None


def get_sec_feed() -> SecEdgarFeed:
    """Get or create the global SecEdgarFeed instance."""
    global _feed
    if _feed is None:
        _feed = create_sec_feed()
    return _feed
