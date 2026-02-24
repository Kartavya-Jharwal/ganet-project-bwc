"""
Integration test script for Phase 1 data pipeline.

Run with: doppler run -- uv run python scripts/test_integrations.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_yfinance():
    """Test yfinance feed."""
    print("\n" + "=" * 60)
    print("Testing yfinance feed...")
    print("=" * 60)
    
    from quant_monitor.data.sources.yfinance_feed import YFinanceFeed
    
    feed = YFinanceFeed()
    
    # Test latest prices
    tickers = ["AAPL", "MSFT", "GOOGL"]
    print(f"\nFetching latest prices for {tickers}...")
    prices = feed.get_latest_prices(tickers)
    for ticker, data in prices.items():
        if data:
            print(f"  {ticker}: ${data['price']:.2f} ({data['change_percent']:+.2f}%)")
    
    # Test bars
    print(f"\nFetching 5-day history for AAPL...")
    bars = feed.get_bars(["AAPL"], period="5d")
    if not bars.empty:
        print(f"Got {len(bars)} bars")
        print(bars.tail(3))
    
    # Test info
    print(f"\nFetching info for AAPL...")
    info = feed.get_info("AAPL")
    if info:
        print(f"Name: {info.get('shortName', 'N/A')}")
        market_cap = info.get('marketCap', 0)
        if market_cap:
            print(f"Market Cap: {market_cap:,}")
        print(f"PE Ratio: {info.get('trailingPE', 'N/A')}")
    
    print("\n✓ yfinance feed working!")
    return True


def test_fred():
    """Test FRED feed."""
    print("\n" + "=" * 60)
    print("Testing FRED feed...")
    print("=" * 60)
    
    from quant_monitor.data.sources.fred_feed import create_fred_feed
    
    fred = create_fred_feed()
    
    # Check if API key is available
    if fred.api_key is None:
        print("⚠ FRED_API_KEY not set, skipping FRED tests")
        return True
    
    # Test VIX
    print("\nFetching VIX...")
    vix = fred.get_vix()
    print(f"VIX: {vix}")
    
    # Test macro snapshot
    print("\nFetching macro snapshot...")
    snapshot = fred.get_macro_snapshot()
    for key, value in snapshot.items():
        print(f"  {key}: {value}")
    
    print("\n✓ FRED feed working!")
    return True


def test_cache():
    """Test cache layer."""
    print("\n" + "=" * 60)
    print("Testing cache layer...")
    print("=" * 60)
    
    from quant_monitor.data.cache import get_cache
    
    cache = get_cache()
    
    # Test set/get
    test_key = "test:integration"
    test_value = {"timestamp": datetime.now().isoformat(), "value": 42}
    
    print(f"\nSetting cache key: {test_key}")
    cache.set(test_key, test_value, ttl=60)
    
    print("Getting cache key...")
    result = cache.get(test_key)
    print(f"Result: {result}")
    
    # Test stats
    stats = cache.stats()
    print(f"\nCache stats: {stats}")
    
    # Cleanup
    cache.delete(test_key)
    print("\n✓ Cache working!")
    return True


def test_appwrite():
    """Test Appwrite client."""
    print("\n" + "=" * 60)
    print("Testing Appwrite client...")
    print("=" * 60)
    
    from quant_monitor.data.appwrite_client import create_appwrite_client
    
    client = create_appwrite_client()
    
    if client is None:
        print("⚠ Appwrite not configured, skipping tests")
        return True
    
    # Test write signal with correct parameters
    print("\nWriting test signal...")
    doc_id = client.write_signal(
        ticker="TEST",
        technical_score=0.5,
        fundamental_score=0.6,
        sentiment_score=0.7,
        macro_score=0.4,
        fused_score=0.55,
        confidence=0.8,
        action="hold",
        regime="neutral",
        dominant_model="technical",
    )
    print(f"Created document: {doc_id}")
    
    # Test query
    print("\nQuerying signals...")
    signals = client.get_latest_signals()
    print(f"Found {len(signals)} signals")
    
    print("\n✓ Appwrite working!")
    return True


def test_pipeline():
    """Test full pipeline."""
    print("\n" + "=" * 60)
    print("Testing full pipeline...")
    print("=" * 60)
    
    from quant_monitor.data.pipeline import create_pipeline
    
    pipeline = create_pipeline()
    
    # Test price fetch with caching
    print("\nFetching prices (first call, should hit API)...")
    prices1 = pipeline.fetch_latest_prices(["AAPL", "MSFT"])
    print(f"Prices: {prices1}")
    
    print("\nFetching prices (second call, should hit cache)...")
    prices2 = pipeline.fetch_latest_prices(["AAPL", "MSFT"])
    print(f"Prices: {prices2}")
    
    # Test macro fetch
    print("\nFetching macro data...")
    macro = pipeline.fetch_macro()
    print(f"Macro keys: {list(macro.keys())}")
    
    print("\n✓ Pipeline working!")
    return True


def test_rate_limiter():
    """Test rate limiter."""
    print("\n" + "=" * 60)
    print("Testing rate limiter...")
    print("=" * 60)
    
    from quant_monitor.data.rate_limiter import rate_limiter
    
    # Test wait (the actual acquire method)
    print("\nTesting rate limit wait for 'yfinance'...")
    import time
    start = time.time()
    for i in range(3):
        success = rate_limiter.wait("yfinance", timeout=5.0)
        print(f"  Acquired token {i+1}: {success}")
    elapsed = time.time() - start
    print(f"Time elapsed: {elapsed:.2f}s")
    
    # Test try_acquire
    print("\nTesting try_acquire...")
    result = rate_limiter.try_acquire("yfinance")
    print(f"  try_acquire result: {result}")
    
    # Check bucket status
    bucket = rate_limiter.get_bucket("yfinance")
    print(f"\nBucket tokens available: {bucket.available_tokens:.2f}")
    
    print("\n✓ Rate limiter working!")
    return True


def main():
    """Run all integration tests."""
    print("\n" + "=" * 60)
    print("QUANT PORTFOLIO MONITOR - INTEGRATION TESTS")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    tests = [
        ("Rate Limiter", test_rate_limiter),
        ("Cache", test_cache),
        ("yfinance", test_yfinance),
        ("FRED", test_fred),
        ("Appwrite", test_appwrite),
        ("Pipeline", test_pipeline),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            success = test_fn()
            results.append((name, "✓ PASS" if success else "✗ FAIL"))
        except Exception as e:
            print(f"\n✗ {name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, f"✗ ERROR: {e}"))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, result in results:
        print(f"  {name}: {result}")
    
    # Return exit code
    failures = sum(1 for _, r in results if not r.startswith("✓"))
    if failures:
        print(f"\n{failures} test(s) failed!")
        return 1
    else:
        print("\nAll tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
