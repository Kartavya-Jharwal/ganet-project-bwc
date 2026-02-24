# Development Guide

This guide covers setting up your development environment, running the system locally, and contributing to the codebase.

---

## Prerequisites

### Required

- **Python 3.11+** — [Download](https://www.python.org/downloads/)
- **uv** — Package manager ([Installation](https://github.com/astral-sh/uv#installation))
  ```powershell
  # Windows
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  
  # macOS/Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Doppler CLI** — Secrets management ([Installation](https://docs.doppler.com/docs/install-cli))
  ```powershell
  # Windows
  winget install doppler
  
  # macOS
  brew install dopplerhq/cli/doppler
  ```
- **Git** — Version control

### Optional (for full workflow)

- **GitHub CLI** (`gh`) — For repo operations
- **Heroku CLI** — For deployment debugging

---

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/Kartavya-Jharwal/quant-portfolio-monitor.git
cd quant-portfolio-monitor
```

### 2. Install Dependencies

```bash
uv sync
```

This creates `.venv/` and installs all 188 dependencies from the lockfile.

### 3. Configure Doppler

```bash
doppler login
doppler setup  # Select project: quant-monitor, config: dev
```

### 4. Verify Installation

```bash
# Check package imports
uv run python -c "import quant_monitor; print('OK')"

# Check config loads
uv run python -c "from quant_monitor.config import cfg; print(cfg.tickers)"

# Run main (should exit cleanly)
doppler run -- uv run python -m quant_monitor.main
```

---

## Development Workflow

### Running Commands

Always use `uv run` to execute Python commands within the virtual environment:

```bash
# Without secrets
uv run python -m quant_monitor.main

# With Doppler secrets
doppler run -- uv run python -m quant_monitor.main

# Run Streamlit dashboard
doppler run -- uv run streamlit run quant_monitor/dashboard/app.py
```

### Adding Dependencies

```bash
# Add a runtime dependency
uv add package-name

# Add a dev dependency
uv add --group dev package-name

# Update lockfile after manual pyproject.toml edits
uv lock
uv sync
```

### Running Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_config.py -v

# With coverage
uv run pytest tests/ --cov=quant_monitor --cov-report=html
```

### Linting & Formatting

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check . --fix

# Format code
uv run ruff format .

# Check formatting (CI mode)
uv run ruff format --check .

# Type checking
uv run mypy quant_monitor/ --ignore-missing-imports
```

### Pre-commit Hooks

```bash
# Install hooks (one-time)
uv run pre-commit install

# Run manually on all files
uv run pre-commit run --all-files
```

---

## Project Structure

```
quant_monitor/
├── __init__.py           # Package version
├── main.py               # APScheduler entry point
├── config.py             # TOML + env loader
├── config.toml           # Static configuration
│
├── data/                 # Layer 1: Data Pipeline
│   ├── pipeline.py       # Orchestrator with failover
│   ├── cache.py          # diskcache wrapper
│   ├── appwrite_client.py
│   └── sources/
│       ├── alpaca_feed.py
│       └── fred_feed.py
│
├── features/             # Layer 2: Feature Engineering
│   ├── moving_averages.py
│   ├── volatility.py
│   └── sentiment_features.py
│
├── models/               # Layer 3: Analysis Models
│   ├── technical.py
│   ├── fundamental.py
│   ├── sentiment.py
│   └── macro.py
│
├── agent/                # Layers 4-5: Fusion + Orchestrator
│   ├── fusion.py         # Signal fusion engine
│   ├── optimizer.py      # Black-Litterman + MVO
│   ├── risk_manager.py   # Position limits, kill switch
│   └── alerts.py         # Telegram dispatcher
│
├── backtest/             # Validation
│   ├── engine.py         # Walk-forward backtester
│   └── metrics.py        # Sharpe, Calmar, etc.
│
├── dashboard/            # UI
│   └── app.py            # Streamlit app
│
└── spiders/              # Scrapy (deploys to Zyte)
    ├── items.py
    ├── pipelines.py
    ├── sec_edgar_spider.py
    ├── google_rss_spider.py
    └── yfinance_spider.py
```

---

## Configuration

### config.toml

All non-secret, version-controlled configuration:

```toml
[project]
name = "Quant Portfolio Monitor"
initial_capital = 1_000_000
benchmark = "SPY"

[holdings.SPY]
name = "SPDR S&P 500 ETF"
qty = 295
price_paid = 684.89
sector = "Broad Market"

[cache_ttl]
price_realtime = 60
news = 1800

[regime_weights.CRISIS]
technical = 0.10
fundamental = 0.10
sentiment = 0.20
macro = 0.60
```

### Doppler Secrets

Secrets injected via environment variables:

| Variable | Description |
|----------|-------------|
| `ALPACA_API_KEY` | Alpaca Markets API key |
| `ALPACA_SECRET_KEY` | Alpaca Markets secret |
| `FRED_API_KEY` | Federal Reserve API key |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat/group ID |
| `APPWRITE_ENDPOINT` | Appwrite Cloud endpoint |
| `APPWRITE_PROJECT_ID` | Appwrite project ID |
| `APPWRITE_API_KEY` | Appwrite API key |
| `ZYTE_API_KEY` | Zyte/Scrapy Cloud API key |

### Accessing Config in Code

```python
from quant_monitor.config import cfg

# Static config
tickers = cfg.tickers                    # ['SPY', 'TSM', ...]
benchmark = cfg.benchmark                 # 'SPY'
cache_ttl = cfg.cache_ttl['price_realtime']  # 60

# Holdings
spy_qty = cfg.holdings['SPY']['qty']      # 295

# Secrets (from Doppler via env)
api_key = cfg.secrets.ALPACA_API_KEY
```

---

## Testing

### Test Organization

```
tests/
├── conftest.py           # Shared fixtures
├── test_config.py        # Config loading tests
├── test_data/
│   └── test_pipeline.py
├── test_features/
│   └── test_moving_averages.py
└── test_models/
    └── test_technical.py
```

### Fixtures

```python
# tests/conftest.py
@pytest.fixture
def mock_env():
    """Mock environment variables (simulates Doppler injection)."""
    env_vars = {
        "ALPACA_API_KEY": "test_key",
        # ...
    }
    with patch.dict("os.environ", env_vars):
        yield env_vars

@pytest.fixture
def sample_ohlcv():
    """Sample OHLCV DataFrame for testing."""
    return pd.DataFrame({
        'open': [...],
        'high': [...],
        # ...
    })
```

### Writing Tests

```python
def test_ema_calculation(sample_ohlcv):
    """EMA should match pandas ewm calculation."""
    from quant_monitor.features.moving_averages import ema
    
    result = ema(sample_ohlcv['close'], period=9)
    expected = sample_ohlcv['close'].ewm(span=9, adjust=False).mean()
    
    pd.testing.assert_series_equal(result, expected)
```

---

## Deployment

### Local Development

```bash
# Start dashboard
doppler run -- uv run streamlit run quant_monitor/dashboard/app.py

# Start worker (signal loop)
doppler run -- uv run python -m quant_monitor.main
```

### Heroku

Automatic deployment via GitHub Actions on push to `main`.

Manual deployment:
```bash
# Generate requirements.txt for Heroku
uv pip compile pyproject.toml -o requirements.txt

# Push to Heroku
git push heroku main

# Check logs
heroku logs --tail
```

### Scrapy Cloud (Zyte)

```bash
# Install Zyte CLI
pip install shub

# Login
shub login

# Deploy spiders
shub deploy
```

---

## Documentation

### Building Docs

```bash
# Live preview
uv run mkdocs serve -f docs/mkdocs.yml

# Build static site
uv run mkdocs build -f docs/mkdocs.yml
```

### Adding Documentation

1. Create Markdown file in `docs/`
2. Add to `nav` section in `docs/mkdocs.yml`
3. Commit and push — GitHub Actions deploys to Pages

---

## Troubleshooting

### uv sync hangs on torch

torch is 108MB. First sync is slow. Solutions:
1. Set `UV_CACHE_DIR` to local drive (avoids cross-drive copies)
2. Wait — subsequent syncs use cache

### Doppler not found

```bash
# Verify installation
doppler --version

# Re-authenticate
doppler login
doppler setup
```

### Import errors after uv sync

```bash
# Force reinstall
uv sync --reinstall

# Or recreate venv
rm -rf .venv
uv sync
```

### Tests fail with missing secrets

Tests should mock secrets, not require Doppler:
```python
@pytest.fixture
def mock_env():
    with patch.dict("os.environ", {"ALPACA_API_KEY": "test"}):
        yield
```

---

## Code Style

- **Line length:** 100 characters
- **Quotes:** Double quotes for strings
- **Imports:** Sorted by ruff (isort rules)
- **Type hints:** Required for all public functions
- **Docstrings:** Google style

```python
def compute_signal(
    prices: pd.DataFrame,
    regime: str,
    threshold: float = 0.35,
) -> dict[str, float]:
    """Compute trading signal for all tickers.
    
    Args:
        prices: OHLCV DataFrame with MultiIndex (ticker, date)
        regime: Current volatility regime name
        threshold: Minimum signal magnitude to trigger action
        
    Returns:
        Dictionary mapping ticker to signal score in [-1, 1]
        
    Raises:
        ValueError: If regime is not recognized
    """
```

---

*Last updated: February 24, 2026*
