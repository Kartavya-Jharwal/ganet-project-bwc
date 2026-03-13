# Quant Portfolio Monitor — Granular Task List

> **Purpose:** Step-by-step implementation roadmap for AI coding assistants.
> Each task is self-contained with exact file paths, function signatures, config values,
> expected inputs/outputs, forbidden patterns, and acceptance criteria.
>
> **CRITICAL RULES FOR AI MODELS:**
> 1. DO NOT change function signatures — they are already defined in the stub files.
> 2. DO NOT rename files or move files — the project structure is final.
> 3. DO NOT add new dependencies unless explicitly stated in the task.
> 4. ALWAYS use `from quant_monitor.config import cfg` to read config values.
> 5. ALWAYS run `doppler run -- uv run pytest` after each task to verify no regressions.
> 6. ALWAYS read the existing file FIRST before editing — the stubs contain exact signatures.
> 7. Config values are in `quant_monitor/config.toml` — NEVER hardcode them.
> 8. Secrets come from Doppler via `os.environ` — NEVER hardcode API keys.
> 9. All functions that raise `NotImplementedError` must be replaced with real logic.
> 10. Type hints are ALREADY in the stubs — preserve them exactly.

---

## TABLE OF CONTENTS

- [Phase 0: Housekeeping (Fix Existing Issues)](#phase-0-housekeeping)
- [Phase 2: Feature Engineering](#phase-2-feature-engineering)
- [Phase 3: Technical + Macro Models](#phase-3-technical--macro-models)
- [Phase 4: Sentiment Model + Features](#phase-4-sentiment-model--features)
- [Phase 5: Fundamental Model](#phase-5-fundamental-model)

> Phase 1 is COMPLETE. All data feeds, cache, rate limiter, pipeline, and Appwrite client
> are implemented and tested. 9 integration tests pass. Do NOT touch Phase 1 files unless
> a task explicitly says to.

---

## Phase 0: Housekeeping

These tasks fix known issues in the existing codebase before new feature work begins.

---

### Task 0.1 — Add `httpx` to production dependencies

**File:** `pyproject.toml`
**Problem:** `quant_monitor/data/sources/sec_feed.py` imports `httpx` but it is not listed in
`pyproject.toml` dependencies. It works today only because it's a transitive dependency of
another package, which could break on update.

**What to do:**
1. Open `pyproject.toml`
2. In the `[project] dependencies` list, add `"httpx>=0.27.0",` right after the `"feedparser>=6.0.0",` line
3. Run `uv sync` to update the lockfile

**Acceptance criteria:**
- `uv run python -c "import httpx; print(httpx.__version__)"` prints a version ≥ 0.27.0
- No other dependency changes occur

---

### Task 0.2 — Move `yfinance` from dev to production dependencies

**File:** `pyproject.toml`
**Problem:** `yfinance` is listed under `[dependency-groups] dev` but is imported in production
code (`quant_monitor/data/sources/yfinance_feed.py` and `quant_monitor/data/pipeline.py`).

**What to do:**
1. Open `pyproject.toml`
2. Add `"yfinance>=0.2.36",` to the `[project] dependencies` list (after the data sources block)
3. Remove `"yfinance>=0.2.36",` from the `[dependency-groups] dev` list
4. Run `uv sync`

**Acceptance criteria:**
- `uv run python -c "import yfinance; print(yfinance.__version__)"` works without `--group dev`
- The `[dependency-groups] dev` list no longer contains yfinance

---

### Task 0.3 — Add Massive secrets to `config.py` Secrets dataclass

**File:** `quant_monitor/config.py`
**Problem:** The `Secrets` dataclass has fields for Alpaca, FRED, Telegram, Appwrite, Zyte,
and SEC EDGAR, but is MISSING fields for the 5 Massive/Polygon secrets that are already in Doppler.

**What to do:**
1. Open `quant_monitor/config.py`
2. In the `Secrets` dataclass, add these 5 fields (after `SEC_EDGAR_USER_AGENT`):

```python
MASSIVE_API_KEY: str = ""
MASSIVE_S3_ENDPOINT: str = ""
MASSIVE_S3_ACCESS_KEY_ID: str = ""
MASSIVE_S3_SECRET_ACCESS_KEY: str = ""
MASSIVE_S3_BUCKET: str = ""
```

3. DO NOT change any existing fields
4. DO NOT change the `from_env()` method — it already dynamically reads all fields

**Acceptance criteria:**
- `doppler run -- uv run python -c "from quant_monitor.config import cfg; print(cfg.secrets.MASSIVE_API_KEY[:8])"` prints `EmrWNo9n`
- All 5 new fields are accessible on `cfg.secrets`
- Existing tests still pass: `doppler run -- uv run pytest tests/test_config.py`

---

### Task 0.4 — Remove unused `duckdb` dependency

**File:** `pyproject.toml`
**Problem:** `duckdb>=1.0.0` is listed in dependencies but is NEVER imported anywhere in the
codebase. The original plan mentioned DuckDB but the implementation uses Appwrite instead.

**What to do:**
1. Open `pyproject.toml`
2. Remove the line `"duckdb>=1.0.0",`
3. Run `uv sync`

**Acceptance criteria:**
- `grep -r "duckdb" quant_monitor/` returns zero matches
- `uv sync` completes without errors
- All existing tests pass

---

### Task 0.5 — Add Phase 2 unit test file skeleton

**File to CREATE:** `tests/test_features.py`

**What to do:**
Create a new test file with test stubs for Phase 2 features. These tests will be filled in
as each Phase 2 task is completed.

```python
"""Tests for feature engineering — Phase 2."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


class TestMovingAverages:
    """Tests for quant_monitor/features/moving_averages.py"""

    def test_ema_matches_pandas_ewm(self):
        """EMA output must match pandas ewm(span=period).mean() within 1e-10."""
        from quant_monitor.features.moving_averages import ema

        series = pd.Series(np.random.randn(100).cumsum() + 100)
        result = ema(series, period=9)
        expected = series.ewm(span=9, adjust=False).mean()
        pd.testing.assert_series_equal(result, expected, atol=1e-10)

    def test_sma_matches_pandas_rolling(self):
        """SMA output must match pandas rolling(period).mean()."""
        from quant_monitor.features.moving_averages import sma

        series = pd.Series(np.random.randn(100).cumsum() + 100)
        result = sma(series, period=50)
        expected = series.rolling(window=50).mean()
        pd.testing.assert_series_equal(result, expected, atol=1e-10)

    def test_kama_returns_series_of_same_length(self):
        """KAMA output length must match input length."""
        from quant_monitor.features.moving_averages import kama

        series = pd.Series(np.random.randn(200).cumsum() + 100)
        result = kama(series, period=10, fast_sc=2, slow_sc=30)
        assert len(result) == len(series)
        assert isinstance(result, pd.Series)

    def test_kama_adapts_to_volatility(self):
        """KAMA should be closer to price in trending markets, smoother in choppy."""
        from quant_monitor.features.moving_averages import kama

        # Trending series
        trending = pd.Series(np.arange(200, dtype=float))
        kama_trending = kama(trending, period=10)
        # In a perfect trend, KAMA should closely track price
        # Check last 50 values: mean absolute error should be small
        mae_trending = (trending.iloc[-50:] - kama_trending.iloc[-50:]).abs().mean()

        # Choppy series
        choppy = pd.Series(np.random.randn(200).cumsum())
        kama_choppy = kama(choppy, period=10)
        # KAMA should be smoother than raw price in choppy market
        # Check that KAMA has lower volatility than raw series
        vol_raw = choppy.diff().std()
        vol_kama = kama_choppy.diff().dropna().std()
        assert vol_kama < vol_raw, "KAMA should smooth out noise"

    def test_vwap_requires_ohlcv_columns(self):
        """VWAP must work with DataFrame containing open/high/low/close/volume."""
        from quant_monitor.features.moving_averages import vwap

        ohlcv = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [105, 106, 107],
            "low": [99, 100, 101],
            "close": [103, 104, 105],
            "volume": [1000, 1500, 1200],
        })
        result = vwap(ohlcv)
        assert isinstance(result, pd.Series)
        assert len(result) == 3

    def test_hma_lower_lag_than_sma(self):
        """HMA should have lower lag than SMA of same period on a trending series."""
        from quant_monitor.features.moving_averages import hma, sma

        # Create a series that starts trending suddenly
        flat = np.full(50, 100.0)
        trend = np.linspace(100, 150, 50)
        series = pd.Series(np.concatenate([flat, trend]))

        hma_result = hma(series, period=16)
        sma_result = sma(series, period=16)

        # After the trend starts (index 50), HMA should respond faster
        # Check at index 60: HMA should be closer to actual price than SMA
        assert hma_result.iloc[65] > sma_result.iloc[65], (
            "HMA should have less lag than SMA on a trending series"
        )

    def test_compute_ma_matrix_returns_all_columns(self):
        """compute_ma_matrix must return DataFrame with all 8 MA columns."""
        from quant_monitor.features.moving_averages import compute_ma_matrix

        np.random.seed(42)
        n = 300  # need enough data for SMA 200
        ohlcv = pd.DataFrame({
            "open": np.random.randn(n).cumsum() + 100,
            "high": np.random.randn(n).cumsum() + 102,
            "low": np.random.randn(n).cumsum() + 98,
            "close": np.random.randn(n).cumsum() + 100,
            "volume": np.random.randint(1000, 10000, n),
        })
        result = compute_ma_matrix(ohlcv)
        expected_columns = {"ema_9", "ema_21", "sma_50", "sma_200", "kama_10", "vwap", "mvwap_20", "hma_16"}
        assert expected_columns.issubset(set(result.columns)), (
            f"Missing columns: {expected_columns - set(result.columns)}"
        )


class TestVolatility:
    """Tests for quant_monitor/features/volatility.py"""

    def test_realized_vol_annualized(self):
        """Realized vol should be annualized (multiply by sqrt(252))."""
        from quant_monitor.features.volatility import realized_volatility

        np.random.seed(42)
        daily_returns = pd.Series(np.random.randn(100) * 0.01)  # ~1% daily vol
        result = realized_volatility(daily_returns, window=20)
        # Last value should be roughly 0.01 * sqrt(252) ≈ 0.159
        assert 0.05 < result.iloc[-1] < 0.5, f"Annualized vol {result.iloc[-1]} out of range"

    def test_vol_percentile_range(self):
        """Volatility percentile must be in [0, 1] range."""
        from quant_monitor.features.volatility import volatility_percentile

        np.random.seed(42)
        vol_series = pd.Series(np.random.rand(300) * 0.3)
        result = volatility_percentile(vol_series, lookback=252)
        valid = result.dropna()
        assert (valid >= 0).all() and (valid <= 1).all(), "Percentile must be in [0,1]"

    def test_hurst_trending_series(self):
        """Hurst exponent > 0.6 for a strongly trending series."""
        from quant_monitor.features.volatility import hurst_exponent

        # Pure trending: cumulative sum with positive drift
        np.random.seed(42)
        trending = pd.Series(np.arange(500, dtype=float) + np.random.randn(500) * 0.1)
        h = hurst_exponent(trending)
        assert h > 0.55, f"Hurst {h} should be > 0.55 for trending series"

    def test_hurst_mean_reverting_series(self):
        """Hurst exponent < 0.45 for mean-reverting (anti-persistent) series."""
        from quant_monitor.features.volatility import hurst_exponent

        np.random.seed(42)
        # Mean-reverting: alternating +1/-1 with small noise
        n = 500
        mean_rev = pd.Series(np.cumsum([(-1)**i + np.random.randn()*0.01 for i in range(n)]))
        h = hurst_exponent(mean_rev)
        assert h < 0.45, f"Hurst {h} should be < 0.45 for mean-reverting series"

    def test_classify_regime_crisis(self):
        """VIX > 30 → CRISIS regardless of other inputs."""
        from quant_monitor.features.volatility import classify_regime, VolRegime

        result = classify_regime(
            realized_vol=0.2,
            vol_percentile=0.5,
            hurst=0.5,
            vix=35.0,
            vix_crisis_threshold=30.0,
        )
        assert result == VolRegime.CRISIS

    def test_classify_regime_low_vol_trend(self):
        """Low vol + high Hurst → LOW_VOL_TREND."""
        from quant_monitor.features.volatility import classify_regime, VolRegime

        result = classify_regime(
            realized_vol=0.10,
            vol_percentile=0.25,
            hurst=0.7,
            vix=15.0,
        )
        assert result == VolRegime.LOW_VOL_TREND

    def test_classify_regime_high_vol_range(self):
        """High vol + low Hurst → HIGH_VOL_RANGE."""
        from quant_monitor.features.volatility import classify_regime, VolRegime

        result = classify_regime(
            realized_vol=0.35,
            vol_percentile=0.85,
            hurst=0.35,
            vix=25.0,
        )
        assert result == VolRegime.HIGH_VOL_RANGE
```

**Acceptance criteria:**
- File exists at `tests/test_features.py`
- `uv run pytest tests/test_features.py --collect-only` collects all tests (they will fail until Phase 2 is done)

---

## Phase 2: Feature Engineering

> **Prerequisites:** All Phase 0 tasks must be complete first.
> **Config reference:** All numeric parameters come from `quant_monitor/config.toml`
> under sections `[moving_averages]` and `[volatility]`.

---

### Task 2.1 — Implement `ema()` in moving_averages.py

**File:** `quant_monitor/features/moving_averages.py`
**Function:** `ema(series: pd.Series, period: int) -> pd.Series`

**What to do:**
Replace the `raise NotImplementedError` with a real implementation.

**Implementation (exact logic):**
```python
def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    import pandas as pd
    return series.ewm(span=period, adjust=False).mean()
```

**Key details:**
- Use `adjust=False` for standard EMA (recursive formula, not weighted average)
- Return a `pd.Series` of the SAME length as input (first values will be warm-up)
- Do NOT drop NaN rows — pandas handles the warm-up automatically

**Acceptance criteria:**
- `pytest tests/test_features.py::TestMovingAverages::test_ema_matches_pandas_ewm` passes
- Output matches `series.ewm(span=period, adjust=False).mean()` within 1e-10

---

### Task 2.2 — Implement `sma()` in moving_averages.py

**File:** `quant_monitor/features/moving_averages.py`
**Function:** `sma(series: pd.Series, period: int) -> pd.Series`

**Implementation (exact logic):**
```python
def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=period).mean()
```

**Key details:**
- First `period - 1` values will be NaN — this is correct behavior, do NOT fill them
- Return type is `pd.Series`

**Acceptance criteria:**
- `pytest tests/test_features.py::TestMovingAverages::test_sma_matches_pandas_rolling` passes

---

### Task 2.3 — Implement `kama()` in moving_averages.py

**File:** `quant_monitor/features/moving_averages.py`
**Function:** `kama(series: pd.Series, period: int = 10, fast_sc: int = 2, slow_sc: int = 30) -> pd.Series`

**Implementation logic (Kaufman Adaptive Moving Average):**
1. Compute `direction = abs(series - series.shift(period))` — price change over period
2. Compute `volatility = series.diff().abs().rolling(period).sum()` — sum of absolute daily changes
3. Compute `er = direction / volatility` — Efficiency Ratio (0 = choppy, 1 = trending)
4. Compute `fast_alpha = 2 / (fast_sc + 1)` and `slow_alpha = 2 / (slow_sc + 1)`
5. Compute `sc = (er * (fast_alpha - slow_alpha) + slow_alpha) ** 2` — smoothing constant
6. Initialize KAMA at `series.iloc[period - 1]`
7. Loop from `period` to end: `kama[i] = kama[i-1] + sc[i] * (series[i] - kama[i-1])`
8. Return as pd.Series (indices before `period - 1` are NaN)

```python
def kama(series: pd.Series, period: int = 10, fast_sc: int = 2, slow_sc: int = 30) -> pd.Series:
    """Kaufman Adaptive Moving Average — adjusts speed based on volatility."""
    import numpy as np
    import pandas as pd

    direction = (series - series.shift(period)).abs()
    volatility = series.diff().abs().rolling(window=period).sum()

    # Efficiency ratio: 0 = pure noise, 1 = pure trend
    er = direction / volatility
    er = er.fillna(0)

    fast_alpha = 2.0 / (fast_sc + 1)
    slow_alpha = 2.0 / (slow_sc + 1)
    sc = (er * (fast_alpha - slow_alpha) + slow_alpha) ** 2

    kama_values = np.full(len(series), np.nan)
    # First valid KAMA value
    first_valid = period - 1
    if first_valid < len(series):
        kama_values[first_valid] = series.iloc[first_valid]

    for i in range(first_valid + 1, len(series)):
        kama_values[i] = kama_values[i - 1] + sc.iloc[i] * (series.iloc[i] - kama_values[i - 1])

    return pd.Series(kama_values, index=series.index, name="kama")
```

**Acceptance criteria:**
- `pytest tests/test_features.py::TestMovingAverages::test_kama_returns_series_of_same_length` passes
- `pytest tests/test_features.py::TestMovingAverages::test_kama_adapts_to_volatility` passes
- Return type is `pd.Series` with same length and index as input

---

### Task 2.4 — Implement `vwap()` in moving_averages.py

**File:** `quant_monitor/features/moving_averages.py`
**Function:** `vwap(ohlcv: pd.DataFrame) -> pd.Series`

**Implementation logic (Session-anchored VWAP):**
1. Compute `typical_price = (ohlcv["high"] + ohlcv["low"] + ohlcv["close"]) / 3`
2. Compute `vwap = (typical_price * ohlcv["volume"]).cumsum() / ohlcv["volume"].cumsum()`
3. Return as pd.Series

**IMPORTANT:** The input DataFrame MUST have lowercase column names: `open`, `high`, `low`, `close`, `volume`. The pipeline already normalizes these.

```python
def vwap(ohlcv: pd.DataFrame) -> pd.Series:
    """Session-anchored Volume-Weighted Average Price."""
    typical_price = (ohlcv["high"] + ohlcv["low"] + ohlcv["close"]) / 3
    cumulative_tp_vol = (typical_price * ohlcv["volume"]).cumsum()
    cumulative_vol = ohlcv["volume"].cumsum()
    return (cumulative_tp_vol / cumulative_vol).rename("vwap")
```

**Acceptance criteria:**
- `pytest tests/test_features.py::TestMovingAverages::test_vwap_requires_ohlcv_columns` passes
- Returns `pd.Series` with same length as input
- No division-by-zero errors (volume is always > 0 in real data)

---

### Task 2.5 — Implement `mvwap()` in moving_averages.py

**File:** `quant_monitor/features/moving_averages.py`
**Function:** `mvwap(ohlcv: pd.DataFrame, period: int = 20) -> pd.Series`

**Implementation logic (Moving VWAP):**
1. Compute `typical_price = (ohlcv["high"] + ohlcv["low"] + ohlcv["close"]) / 3`
2. Compute rolling numerator: `(typical_price * ohlcv["volume"]).rolling(period).sum()`
3. Compute rolling denominator: `ohlcv["volume"].rolling(period).sum()`
4. Return `numerator / denominator`

```python
def mvwap(ohlcv: pd.DataFrame, period: int = 20) -> pd.Series:
    """Moving VWAP — N-day rolling VWAP. Institutional price reference."""
    typical_price = (ohlcv["high"] + ohlcv["low"] + ohlcv["close"]) / 3
    tp_vol = (typical_price * ohlcv["volume"]).rolling(window=period).sum()
    vol_sum = ohlcv["volume"].rolling(window=period).sum()
    return (tp_vol / vol_sum).rename("mvwap")
```

**Acceptance criteria:**
- Returns `pd.Series` of same length as input
- First `period - 1` values are NaN
- Subsequent values are between the min and max of typical price

---

### Task 2.6 — Implement `hma()` in moving_averages.py

**File:** `quant_monitor/features/moving_averages.py`
**Function:** `hma(series: pd.Series, period: int = 16) -> pd.Series`

**Implementation logic (Hull Moving Average):**
HMA reduces lag. Formula:
1. Compute `wma_half = series.rolling(period // 2).apply(lambda x: np.average(x, weights=np.arange(1, len(x) + 1)))` — WMA with half period
2. Compute `wma_full = series.rolling(period).apply(lambda x: np.average(x, weights=np.arange(1, len(x) + 1)))` — WMA with full period
3. Compute `diff = 2 * wma_half - wma_full`
4. Compute `sqrt_period = int(np.sqrt(period))`
5. Return `diff.rolling(sqrt_period).apply(lambda x: np.average(x, weights=np.arange(1, len(x) + 1)))` — WMA of diff with sqrt(period)

```python
def hma(series: pd.Series, period: int = 16) -> pd.Series:
    """Hull Moving Average — low-lag responsive trend signal."""
    import numpy as np

    def weighted_ma(s: pd.Series, w: int) -> pd.Series:
        weights = np.arange(1, w + 1, dtype=float)
        return s.rolling(window=w).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )

    half_period = period // 2
    sqrt_period = int(np.sqrt(period))

    wma_half = weighted_ma(series, half_period)
    wma_full = weighted_ma(series, period)
    diff = 2 * wma_half - wma_full
    return weighted_ma(diff, sqrt_period).rename("hma")
```

**Acceptance criteria:**
- `pytest tests/test_features.py::TestMovingAverages::test_hma_lower_lag_than_sma` passes
- Returns `pd.Series` of same length as input
- On trending data, HMA responds faster than SMA of same period

---

### Task 2.7 — Implement `compute_ma_matrix()` in moving_averages.py

**File:** `quant_monitor/features/moving_averages.py`
**Function:** `compute_ma_matrix(ohlcv: pd.DataFrame) -> pd.DataFrame`

**Implementation logic:**
Combine all MA functions from Tasks 2.1–2.6 into a single DataFrame using config periods.

```python
def compute_ma_matrix(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Compute full MA matrix for a single ticker. Returns DataFrame with all MAs as columns."""
    import pandas as pd
    from quant_monitor.config import cfg

    ma_cfg = cfg.moving_averages
    close = ohlcv["close"]

    result = pd.DataFrame(index=ohlcv.index)
    result["ema_9"] = ema(close, ma_cfg["ema_fast"])          # ema_fast = 9
    result["ema_21"] = ema(close, ma_cfg["ema_medium"])       # ema_medium = 21
    result["sma_50"] = sma(close, ma_cfg["sma_medium"])       # sma_medium = 50
    result["sma_200"] = sma(close, ma_cfg["sma_long"])        # sma_long = 200
    result["kama_10"] = kama(close, ma_cfg["kama_period"])    # kama_period = 10
    result["vwap"] = vwap(ohlcv)
    result["mvwap_20"] = mvwap(ohlcv, ma_cfg["mvwap_period"])  # mvwap_period = 20
    result["hma_16"] = hma(close, ma_cfg["hma_period"])        # hma_period = 16

    return result
```

**Config values used (from `quant_monitor/config.toml [moving_averages]`):**
| Key | Value | Description |
|-----|-------|-------------|
| ema_fast | 9 | EMA short period |
| ema_medium | 21 | EMA medium period |
| sma_medium | 50 | SMA medium period |
| sma_long | 200 | SMA long period |
| kama_period | 10 | KAMA period |
| hma_period | 16 | HMA period |
| mvwap_period | 20 | MVWAP rolling window |

**Column names in returned DataFrame MUST be:**
`ema_9`, `ema_21`, `sma_50`, `sma_200`, `kama_10`, `vwap`, `mvwap_20`, `hma_16`

**Acceptance criteria:**
- `pytest tests/test_features.py::TestMovingAverages::test_compute_ma_matrix_returns_all_columns` passes
- Input requires at least 200 rows (for SMA 200) — this is fine, pipeline fetches 1 year
- All 8 columns present in output

---

### Task 2.8 — Add `import pandas as pd` and `import numpy as np` at top of moving_averages.py

**File:** `quant_monitor/features/moving_averages.py`
**Problem:** The existing file uses `TYPE_CHECKING` import for pandas, but the implementations
need actual runtime imports.

**What to do:**
Replace:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd
```

With:
```python
import numpy as np
import pandas as pd
```

**IMPORTANT:** Do this BEFORE or AT THE SAME TIME as Tasks 2.1–2.7. The implementations
need pandas and numpy at runtime.

**Acceptance criteria:**
- No `ImportError` at runtime when importing from `quant_monitor.features.moving_averages`

---

### Task 2.9 — Implement `realized_volatility()` in volatility.py

**File:** `quant_monitor/features/volatility.py`
**Function:** `realized_volatility(returns: pd.Series, window: int = 20) -> pd.Series`

**Implementation logic:**
Rolling standard deviation of returns, annualized by multiplying by √252.

```python
def realized_volatility(returns: pd.Series, window: int = 20) -> pd.Series:
    """Annualized rolling realized volatility."""
    import numpy as np
    return returns.rolling(window=window).std() * np.sqrt(252)
```

**Input:** Daily log returns (or simple returns) as a pd.Series
**Output:** Annualized rolling vol as pd.Series (same length, first `window-1` values are NaN)

**Config value:** `cfg.volatility["realized_vol_window"]` = 20

**Acceptance criteria:**
- `pytest tests/test_features.py::TestVolatility::test_realized_vol_annualized` passes
- Output is annualized (not daily) — multiply by √252

---

### Task 2.10 — Implement `volatility_percentile()` in volatility.py

**File:** `quant_monitor/features/volatility.py`
**Function:** `volatility_percentile(vol_series: pd.Series, lookback: int = 252) -> pd.Series`

**Implementation logic:**
Percentile rank of each vol value against the trailing `lookback` window.

```python
def volatility_percentile(vol_series: pd.Series, lookback: int = 252) -> pd.Series:
    """Percentile rank of current vol vs trailing lookback period."""
    def pct_rank(window):
        """Percentile rank of last value within window."""
        return (window < window.iloc[-1]).sum() / (len(window) - 1) if len(window) > 1 else 0.5

    return vol_series.rolling(window=lookback, min_periods=2).apply(pct_rank, raw=False)
```

**Output:** Values in [0, 1] where 1.0 = highest vol in lookback period
**Config value:** `cfg.volatility["vol_percentile_lookback"]` = 252

**Acceptance criteria:**
- `pytest tests/test_features.py::TestVolatility::test_vol_percentile_range` passes
- All non-NaN values are between 0 and 1 inclusive

---

### Task 2.11 — Implement `hurst_exponent()` in volatility.py

**File:** `quant_monitor/features/volatility.py`
**Function:** `hurst_exponent(series: pd.Series, max_lag: int = 100) -> float`

**Implementation logic (R/S Analysis — Rescaled Range):**
This is one of the HARDEST parts of the project. Follow this algorithm EXACTLY:

```python
def hurst_exponent(series: pd.Series, max_lag: int = 100) -> float:
    """Compute Hurst exponent using R/S analysis.

    H > 0.6 → trending (persistent)
    H ≈ 0.5 → random walk
    H < 0.4 → mean-reverting (anti-persistent)
    """
    import numpy as np

    ts = series.dropna().values
    n = len(ts)
    if n < 20:
        return 0.5  # not enough data, assume random walk

    # Use lags from 2 to max_lag (or n//2, whichever is smaller)
    max_k = min(max_lag, n // 2)
    lags = range(2, max_k + 1)

    rs_values = []
    for lag in lags:
        # Divide series into chunks of size lag
        n_chunks = n // lag
        if n_chunks < 1:
            continue

        rs_chunk = []
        for i in range(n_chunks):
            chunk = ts[i * lag : (i + 1) * lag]
            mean_chunk = np.mean(chunk)
            deviations = chunk - mean_chunk
            cumulative_dev = np.cumsum(deviations)
            r = np.max(cumulative_dev) - np.min(cumulative_dev)  # Range
            s = np.std(chunk, ddof=1)  # Standard deviation
            if s > 0:
                rs_chunk.append(r / s)

        if rs_chunk:
            rs_values.append((lag, np.mean(rs_chunk)))

    if len(rs_values) < 2:
        return 0.5

    log_lags = np.log([v[0] for v in rs_values])
    log_rs = np.log([v[1] for v in rs_values])

    # Linear regression: log(R/S) = H * log(lag) + c
    hurst, _ = np.polyfit(log_lags, log_rs, 1)

    # Clamp to valid range
    return float(np.clip(hurst, 0.0, 1.0))
```

**Interpretation:**
| Hurst Value | Meaning | Action |
|-------------|---------|--------|
| > 0.6 | Trending (persistent) | Trend-following works |
| ≈ 0.5 | Random walk | No edge |
| < 0.4 | Mean-reverting | Mean-reversion works |

**Config values:**
- `cfg.volatility["hurst_trending_threshold"]` = 0.6
- `cfg.volatility["hurst_reverting_threshold"]` = 0.4

**Acceptance criteria:**
- `pytest tests/test_features.py::TestVolatility::test_hurst_trending_series` passes (H > 0.55)
- `pytest tests/test_features.py::TestVolatility::test_hurst_mean_reverting_series` passes (H < 0.45)
- Returns a single float (not a Series)
- Value is between 0 and 1

---

### Task 2.12 — Implement `classify_regime()` in volatility.py

**File:** `quant_monitor/features/volatility.py`
**Function:** `classify_regime(realized_vol, vol_percentile, hurst, vix, vix_crisis_threshold=30.0) -> VolRegime`

**Implementation logic (5-regime classifier):**
```python
def classify_regime(
    realized_vol: float,
    vol_percentile: float,
    hurst: float,
    vix: float,
    vix_crisis_threshold: float = 30.0,
) -> VolRegime:
    """Classify current volatility regime from multiple inputs."""
    # Rule 1: VIX above crisis threshold → CRISIS (overrides everything)
    if vix >= vix_crisis_threshold:
        return VolRegime.CRISIS

    # Rule 2: High/Low vol determined by percentile (above/below 50th percentile)
    is_high_vol = vol_percentile > 0.5

    # Rule 3: Trending/Range determined by Hurst exponent
    # H > 0.5 → trending, H <= 0.5 → range-bound
    is_trending = hurst > 0.5

    if is_high_vol and is_trending:
        return VolRegime.HIGH_VOL_TREND
    elif is_high_vol and not is_trending:
        return VolRegime.HIGH_VOL_RANGE
    elif not is_high_vol and is_trending:
        return VolRegime.LOW_VOL_TREND
    else:
        return VolRegime.LOW_VOL_RANGE
```

**Regime table:**
| Vol Percentile | Hurst | VIX < 30 | Regime |
|---------------|-------|----------|--------|
| > 0.5 | > 0.5 | Yes | HIGH_VOL_TREND |
| > 0.5 | ≤ 0.5 | Yes | HIGH_VOL_RANGE |
| ≤ 0.5 | > 0.5 | Yes | LOW_VOL_TREND |
| ≤ 0.5 | ≤ 0.5 | Yes | LOW_VOL_RANGE |
| Any | Any | No (≥30) | CRISIS |

**Acceptance criteria:**
- All 3 regime tests pass:
  - `test_classify_regime_crisis` — VIX > 30 → CRISIS
  - `test_classify_regime_low_vol_trend` — low percentile + high Hurst → LOW_VOL_TREND
  - `test_classify_regime_high_vol_range` — high percentile + low Hurst → HIGH_VOL_RANGE

---

### Task 2.13 — Add runtime imports to volatility.py

**File:** `quant_monitor/features/volatility.py`
**Problem:** Same as Task 2.8 — pandas/numpy are behind TYPE_CHECKING guard.

**What to do:**
Replace:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd
```

With:
```python
import numpy as np
import pandas as pd
```

---

### Task 2.14 — Run full Phase 2 test suite

**Not a code change.** Run this command to verify all Phase 2 tasks:

```bash
doppler run -- uv run pytest tests/test_features.py -v
```

**Expected output:** ALL tests pass (approximately 10 tests).

**If any test fails:**
1. Read the error message carefully
2. Check that the function signature matches the stub exactly
3. Check that config values are read (not hardcoded)
4. Check that pandas/numpy imports are at runtime (not behind TYPE_CHECKING)

---

## Phase 3: Technical + Macro Models

> **Prerequisites:** Phase 2 must be COMPLETE (all moving average + volatility functions working).
> **Depends on:** `quant_monitor/features/moving_averages.py` and `quant_monitor/features/volatility.py`

---

### Task 3.0 — Create Phase 3 test file

**File to CREATE:** `tests/test_models.py`

```python
"""Tests for analysis models — Phase 3 (Technical + Macro)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


class TestTechnicalModel:
    """Tests for quant_monitor/models/technical.py"""

    def _make_ohlcv(self, n: int = 300, trend: str = "up") -> pd.DataFrame:
        """Helper: generate synthetic OHLCV data."""
        np.random.seed(42)
        if trend == "up":
            close = pd.Series(np.linspace(100, 150, n) + np.random.randn(n) * 2)
        elif trend == "down":
            close = pd.Series(np.linspace(150, 100, n) + np.random.randn(n) * 2)
        else:  # sideways
            close = pd.Series(100 + np.random.randn(n) * 3)

        return pd.DataFrame({
            "open": close - np.random.rand(n) * 0.5,
            "high": close + np.random.rand(n) * 2,
            "low": close - np.random.rand(n) * 2,
            "close": close,
            "volume": np.random.randint(100_000, 1_000_000, n),
        })

    def test_score_returns_float_in_range(self):
        """score() must return a float in [-1.0, +1.0]."""
        from quant_monitor.models.technical import TechnicalModel
        from quant_monitor.features.moving_averages import compute_ma_matrix

        model = TechnicalModel()
        ohlcv = self._make_ohlcv(300, "up")
        ma_matrix = compute_ma_matrix(ohlcv)
        score = model.score(ohlcv, ma_matrix)
        assert isinstance(score, float)
        assert -1.0 <= score <= 1.0, f"Score {score} out of [-1, 1] range"

    def test_uptrend_positive_score(self):
        """Strong uptrend should produce a positive score."""
        from quant_monitor.models.technical import TechnicalModel
        from quant_monitor.features.moving_averages import compute_ma_matrix

        model = TechnicalModel()
        ohlcv = self._make_ohlcv(300, "up")
        ma_matrix = compute_ma_matrix(ohlcv)
        score = model.score(ohlcv, ma_matrix)
        assert score > 0, f"Uptrend score {score} should be positive"

    def test_downtrend_negative_score(self):
        """Strong downtrend should produce a negative score."""
        from quant_monitor.models.technical import TechnicalModel
        from quant_monitor.features.moving_averages import compute_ma_matrix

        model = TechnicalModel()
        ohlcv = self._make_ohlcv(300, "down")
        ma_matrix = compute_ma_matrix(ohlcv)
        score = model.score(ohlcv, ma_matrix)
        assert score < 0, f"Downtrend score {score} should be negative"

    def test_score_all_returns_dict(self):
        """score_all() must return {ticker: float} for all input tickers."""
        from quant_monitor.models.technical import TechnicalModel
        from quant_monitor.features.moving_averages import compute_ma_matrix

        model = TechnicalModel()
        data = {}
        for ticker in ["AAPL", "MSFT", "GOOGL"]:
            ohlcv = self._make_ohlcv(300, "up")
            data[ticker] = ohlcv
        result = model.score_all(data)
        assert isinstance(result, dict)
        assert set(result.keys()) == {"AAPL", "MSFT", "GOOGL"}
        for v in result.values():
            assert -1.0 <= v <= 1.0


class TestMacroModel:
    """Tests for quant_monitor/models/macro.py"""

    def test_score_risk_on(self):
        """Low VIX + normal yield curve → positive (risk-on) score."""
        from quant_monitor.models.macro import MacroModel

        model = MacroModel()
        snapshot = {
            "vix": 15.0,
            "yield_10y_2y_spread": 0.5,   # positive = normal
            "dxy_weekly_change_pct": 0.3,  # moderate
            "ten_year_yield_weekly_bps": 5.0,  # stable
        }
        score = model.score(snapshot)
        assert isinstance(score, float)
        assert score > 0, "Low VIX + normal curve should be risk-on (positive)"

    def test_score_risk_off(self):
        """High VIX + inverted yield curve → negative (risk-off) score."""
        from quant_monitor.models.macro import MacroModel

        model = MacroModel()
        snapshot = {
            "vix": 28.0,
            "yield_10y_2y_spread": -0.5,   # inverted
            "dxy_weekly_change_pct": 3.0,   # spiking
            "ten_year_yield_weekly_bps": 25.0,  # spiking
        }
        score = model.score(snapshot)
        assert score < 0, "High VIX + inverted curve should be risk-off (negative)"

    def test_classify_regime_risk_on(self):
        """Normal conditions → RISK_ON."""
        from quant_monitor.models.macro import MacroModel

        model = MacroModel()
        snapshot = {"vix": 14.0, "yield_10y_2y_spread": 1.0, "dxy_weekly_change_pct": 0.5, "ten_year_yield_weekly_bps": 3.0}
        regime = model.classify_regime(snapshot)
        assert regime == "RISK_ON"

    def test_classify_regime_crisis(self):
        """Extreme conditions → CRISIS."""
        from quant_monitor.models.macro import MacroModel

        model = MacroModel()
        snapshot = {"vix": 35.0, "yield_10y_2y_spread": -1.0, "dxy_weekly_change_pct": 4.0, "ten_year_yield_weekly_bps": 40.0}
        regime = model.classify_regime(snapshot)
        assert regime == "CRISIS"

    def test_per_ticker_impact_tsm(self):
        """TSM (ADR) should be negatively impacted by DXY spike."""
        from quant_monitor.models.macro import MacroModel

        model = MacroModel()
        snapshot = {"vix": 18.0, "yield_10y_2y_spread": 0.3, "dxy_weekly_change_pct": 3.5, "ten_year_yield_weekly_bps": 5.0}
        impact = model.per_ticker_impact(snapshot, "TSM", "AI Infrastructure")
        assert impact < 0, "TSM should have negative macro impact from DXY spike"

    def test_score_range(self):
        """score() must return float in [-1.0, +1.0]."""
        from quant_monitor.models.macro import MacroModel

        model = MacroModel()
        for vix in [10, 20, 30, 40]:
            for spread in [-1, 0, 1]:
                snapshot = {"vix": vix, "yield_10y_2y_spread": spread, "dxy_weekly_change_pct": 1.0, "ten_year_yield_weekly_bps": 10.0}
                score = model.score(snapshot)
                assert -1.0 <= score <= 1.0, f"Score {score} out of range for vix={vix}, spread={spread}"
```

**Acceptance criteria:**
- File exists at `tests/test_models.py`
- `uv run pytest tests/test_models.py --collect-only` collects all tests

---

### Task 3.1 — Implement `TechnicalModel.score()` in technical.py

**File:** `quant_monitor/models/technical.py`
**Method:** `TechnicalModel.score(self, ohlcv: pd.DataFrame, ma_matrix: pd.DataFrame) -> float`

**Implementation logic — 5 signal components, each in [-1, +1], then averaged:**

**Component 1: MA Crossover Matrix (weight 0.30)**
- EMA 9 > EMA 21 → +0.5; EMA 9 < EMA 21 → -0.5
- SMA 50 > SMA 200 → +0.5; SMA 50 < SMA 200 → -0.5
- Sum and clamp to [-1, 1]

**Component 2: RSI (weight 0.20)**
- RSI formula: `100 - (100 / (1 + avg_gain / avg_loss))` with 14-period lookback
- RSI > 70 → overbought → score = -(RSI - 70) / 30 (negative, capped at -1)
- RSI < 30 → oversold → score = (30 - RSI) / 30 (positive, capped at +1)
- RSI 30-70 → score = (RSI - 50) / 20 (centered on 50, mild signal)

**Component 3: MACD Histogram Direction (weight 0.20)**
- MACD = EMA(12) - EMA(26), Signal = EMA(9) of MACD, Histogram = MACD - Signal
- If histogram > 0 and increasing → +1
- If histogram > 0 and decreasing → +0.3
- If histogram < 0 and decreasing → -1
- If histogram < 0 and increasing → -0.3

**Component 4: Bollinger Band (weight 0.15)**
- BB with 20-period SMA and 2 std devs
- Price near upper band (within 5%) → -0.5 (overbought)
- Price near lower band (within 5%) → +0.5 (oversold)
- Bandwidth shrinking (squeeze) → abs score closer to 0 (uncertain)

**Component 5: Volume Confirmation (weight 0.15)**
- If current volume > 1.5x 20-day average → multiply other signals by 1.0 (confirmed)
- If current volume < 0.5x 20-day average → multiply other signals by 0.5 (unconfirmed)
- else → multiply by 0.75

**Final score:**
```
raw = (ma_signal * 0.30 + rsi_signal * 0.20 + macd_signal * 0.20 + bb_signal * 0.15 + volume_factor_applied) 
return max(-1.0, min(1.0, raw))
```

**Add runtime imports at the top of the file:**
Replace `TYPE_CHECKING` guard with real imports:
```python
import numpy as np
import pandas as pd
```

**Acceptance criteria:**
- `pytest tests/test_models.py::TestTechnicalModel::test_score_returns_float_in_range` passes
- `pytest tests/test_models.py::TestTechnicalModel::test_uptrend_positive_score` passes
- `pytest tests/test_models.py::TestTechnicalModel::test_downtrend_negative_score` passes
- Score is ALWAYS in [-1.0, +1.0] — clamp at the end

---

### Task 3.2 — Implement `TechnicalModel.score_all()` in technical.py

**File:** `quant_monitor/models/technical.py`
**Method:** `TechnicalModel.score_all(self, data: dict[str, pd.DataFrame]) -> dict[str, float]`

**Implementation:**
```python
def score_all(self, data: dict[str, pd.DataFrame]) -> dict[str, float]:
    """Score all tickers. Returns {ticker: signal_score}."""
    from quant_monitor.features.moving_averages import compute_ma_matrix

    results = {}
    for ticker, ohlcv in data.items():
        try:
            ma_matrix = compute_ma_matrix(ohlcv)
            results[ticker] = self.score(ohlcv, ma_matrix)
        except Exception as e:
            logger.warning("Technical scoring failed for %s: %s", ticker, e)
            results[ticker] = 0.0  # neutral on error
    return results
```

**Acceptance criteria:**
- `pytest tests/test_models.py::TestTechnicalModel::test_score_all_returns_dict` passes
- Every ticker gets a score (0.0 on error, not exception)

---

### Task 3.3 — Implement `MacroModel.score()` in macro.py

**File:** `quant_monitor/models/macro.py`
**Method:** `MacroModel.score(self, macro_snapshot: dict) -> float`

**Expected `macro_snapshot` dict keys (from FRED feed via pipeline):**
```python
{
    "vix": float,                       # VIX level
    "yield_10y_2y_spread": float,       # 10Y-2Y spread (negative = inverted)
    "dxy_weekly_change_pct": float,     # DXY weekly % change
    "ten_year_yield_weekly_bps": float,  # 10Y yield weekly change in bps
}
```

**Implementation logic — 4 sub-signals averaged:**

**Config thresholds (from `quant_monitor/config.toml [macro_thresholds]`):**
| Key | Value | Meaning |
|-----|-------|---------|
| vix_risk_off | 25.0 | VIX above this = risk-off signal |
| yield_curve_inversion | 0.0 | Spread below this = inverted = bearish |
| dxy_spike_weekly_pct | 2.0 | DXY weekly change above this = spiking |
| ten_year_yield_spike_bps | 20.0 | 10Y change above this = spiking |

```python
def score(self, macro_snapshot: dict) -> float:
    """Generate macro signal (portfolio-level, not per-ticker)."""
    from quant_monitor.config import cfg
    thresholds = cfg.macro_thresholds
    signals = []

    # 1. VIX signal: low VIX = risk-on (+1), high VIX = risk-off (-1)
    vix = macro_snapshot.get("vix", 20.0)
    vix_threshold = thresholds["vix_risk_off"]  # 25.0
    if vix < 15:
        signals.append(1.0)
    elif vix < vix_threshold:
        signals.append(1.0 - (vix - 15) / (vix_threshold - 15))
    elif vix < 35:
        signals.append(-(vix - vix_threshold) / (35 - vix_threshold))
    else:
        signals.append(-1.0)

    # 2. Yield curve: positive spread = healthy (+), negative = inverted (-)
    spread = macro_snapshot.get("yield_10y_2y_spread", 0.5)
    if spread > 1.0:
        signals.append(1.0)
    elif spread > 0:
        signals.append(spread / 1.0)
    elif spread > -1.0:
        signals.append(spread / 1.0)
    else:
        signals.append(-1.0)

    # 3. DXY spike: large weekly move = headwind
    dxy_change = abs(macro_snapshot.get("dxy_weekly_change_pct", 0.0))
    dxy_spike = thresholds["dxy_spike_weekly_pct"]  # 2.0
    if dxy_change < dxy_spike * 0.5:
        signals.append(0.5)  # stable = slightly positive
    elif dxy_change < dxy_spike:
        signals.append(0.0)  # moderate
    else:
        signals.append(-min(dxy_change / dxy_spike, 2.0) / 2.0)  # spiking = negative

    # 4. 10Y yield spike: rising rates = headwind for growth
    yield_change = abs(macro_snapshot.get("ten_year_yield_weekly_bps", 0.0))
    yield_spike = thresholds["ten_year_yield_spike_bps"]  # 20.0
    if yield_change < yield_spike * 0.5:
        signals.append(0.3)  # stable
    elif yield_change < yield_spike:
        signals.append(0.0)  # moderate
    else:
        signals.append(-min(yield_change / yield_spike, 2.0) / 2.0)  # spiking

    # Average all sub-signals and clamp
    avg = sum(signals) / len(signals)
    return max(-1.0, min(1.0, avg))
```

**Acceptance criteria:**
- `pytest tests/test_models.py::TestMacroModel::test_score_risk_on` passes
- `pytest tests/test_models.py::TestMacroModel::test_score_risk_off` passes
- `pytest tests/test_models.py::TestMacroModel::test_score_range` passes
- Score is ALWAYS in [-1.0, +1.0]

---

### Task 3.4 — Implement `MacroModel.classify_regime()` in macro.py

**File:** `quant_monitor/models/macro.py`
**Method:** `MacroModel.classify_regime(self, macro_snapshot: dict) -> str`

**Returns one of:** `"RISK_ON"`, `"TRANSITION"`, `"CRISIS"`

**Implementation logic:**
```python
def classify_regime(self, macro_snapshot: dict) -> str:
    """Classify current macro regime: RISK_ON | TRANSITION | CRISIS."""
    from quant_monitor.config import cfg
    thresholds = cfg.macro_thresholds

    vix = macro_snapshot.get("vix", 20.0)
    spread = macro_snapshot.get("yield_10y_2y_spread", 0.5)
    dxy_change = abs(macro_snapshot.get("dxy_weekly_change_pct", 0.0))
    yield_change = abs(macro_snapshot.get("ten_year_yield_weekly_bps", 0.0))

    crisis_signals = 0
    if vix > 30:
        crisis_signals += 2  # VIX > 30 is very strong crisis signal
    elif vix > thresholds["vix_risk_off"]:  # > 25
        crisis_signals += 1

    if spread < thresholds["yield_curve_inversion"]:  # < 0 (inverted)
        crisis_signals += 1

    if dxy_change > thresholds["dxy_spike_weekly_pct"]:  # > 2%
        crisis_signals += 1

    if yield_change > thresholds["ten_year_yield_spike_bps"]:  # > 20 bps
        crisis_signals += 1

    if crisis_signals >= 3:
        return "CRISIS"
    elif crisis_signals >= 1:
        return "TRANSITION"
    else:
        return "RISK_ON"
```

**Acceptance criteria:**
- `pytest tests/test_models.py::TestMacroModel::test_classify_regime_risk_on` passes
- `pytest tests/test_models.py::TestMacroModel::test_classify_regime_crisis` passes

---

### Task 3.5 — Implement `MacroModel.per_ticker_impact()` in macro.py

**File:** `quant_monitor/models/macro.py`
**Method:** `MacroModel.per_ticker_impact(self, macro_snapshot: dict, ticker: str, sector: str) -> float`

**Implementation logic:**
Different tickers have different sensitivity to macro factors. Returns adjustment in [-1, 1].

```python
def per_ticker_impact(self, macro_snapshot: dict, ticker: str, sector: str) -> float:
    """Compute macro headwind/tailwind for a specific ticker."""
    from quant_monitor.config import cfg
    thresholds = cfg.macro_thresholds
    impact = 0.0

    dxy_change = macro_snapshot.get("dxy_weekly_change_pct", 0.0)
    yield_bps = macro_snapshot.get("ten_year_yield_weekly_bps", 0.0)
    vix = macro_snapshot.get("vix", 20.0)

    # DXY sensitivity: ADRs and international revenue companies
    dxy_sensitive = {"TSM", "AMZN", "GOOGL"}  # FX exposure
    if ticker in dxy_sensitive and abs(dxy_change) > thresholds["dxy_spike_weekly_pct"]:
        impact -= 0.3 * (dxy_change / thresholds["dxy_spike_weekly_pct"])

    # Rate sensitivity: high-multiple growth names hurt by rising yields
    rate_sensitive = {"PLTR", "IONQ", "AMZN", "GOOGL"}
    if ticker in rate_sensitive and yield_bps > thresholds["ten_year_yield_spike_bps"]:
        impact -= 0.3 * (yield_bps / thresholds["ten_year_yield_spike_bps"])

    # Defensive tickers benefit from risk-off
    defensive = {"WMT", "XLP", "PG", "JNJ", "XLU"}
    if ticker in defensive and vix > thresholds["vix_risk_off"]:
        impact += 0.2  # defensive names get a tailwind in risk-off

    # Financials benefit from rising rates (net interest margin)
    if ticker == "JPM" and yield_bps > 0:
        impact += 0.15 * min(yield_bps / thresholds["ten_year_yield_spike_bps"], 1.0)

    return max(-1.0, min(1.0, impact))
```

**Acceptance criteria:**
- `pytest tests/test_models.py::TestMacroModel::test_per_ticker_impact_tsm` passes
- Returns float in [-1.0, +1.0]
- TSM gets negative impact from DXY spike (FX headwind)
- Defensive names (WMT, XLP, etc.) get positive impact in risk-off

---

### Task 3.6 — Run full Phase 3 test suite

```bash
doppler run -- uv run pytest tests/test_models.py -v
```

**Expected:** All ~10 tests pass.

---

## Phase 4: Sentiment Model + Features

> **Prerequisites:** Phase 3 must be COMPLETE.
> **New dependency needed:** `transformers` and `sentence-transformers` are already in pyproject.toml.
> **Model:** FinBERT = `ProsusAI/finbert` (from config.toml `[sentiment]`)
>
> **WARNING:** FinBERT requires downloading ~400MB model on first run. Ensure good internet.
> The model will be cached in `~/.cache/huggingface/` after first download.
> Use `torch` CPU mode only (PyTorch CPU variant already configured in pyproject.toml).

---

### Task 4.0 — Create Phase 4 test file

**File to CREATE:** `tests/test_sentiment.py`

```python
"""Tests for sentiment features and model — Phase 4."""

from __future__ import annotations

import pandas as pd
import numpy as np
import pytest


class TestSentimentFeatureEngine:
    """Tests for quant_monitor/features/sentiment_features.py"""

    def test_score_headlines_returns_list_of_dicts(self):
        """score_headlines must return list of dicts with required keys."""
        from quant_monitor.features.sentiment_features import SentimentFeatureEngine

        engine = SentimentFeatureEngine()
        headlines = [
            "Apple reports record quarterly earnings beating estimates",
            "Markets crash as recession fears mount globally",
            "Federal Reserve holds interest rates steady",
        ]
        results = engine.score_headlines(headlines)
        assert isinstance(results, list)
        assert len(results) == 3
        for item in results:
            assert "text" in item
            assert "label" in item
            assert "score" in item
            assert item["label"] in ("positive", "negative", "neutral")
            assert -1.0 <= item["score"] <= 1.0

    def test_positive_headline_scored_positive(self):
        """Clearly positive headline should get positive score."""
        from quant_monitor.features.sentiment_features import SentimentFeatureEngine

        engine = SentimentFeatureEngine()
        results = engine.score_headlines(["Company reports massive earnings beat and raises guidance"])
        assert results[0]["label"] == "positive" or results[0]["score"] > 0

    def test_negative_headline_scored_negative(self):
        """Clearly negative headline should get negative score."""
        from quant_monitor.features.sentiment_features import SentimentFeatureEngine

        engine = SentimentFeatureEngine()
        results = engine.score_headlines(["Company issues profit warning amid declining sales and layoffs"])
        assert results[0]["label"] == "negative" or results[0]["score"] < 0

    def test_deduplicate_news_removes_similar(self):
        """Deduplicate should remove near-duplicate headlines."""
        from quant_monitor.features.sentiment_features import SentimentFeatureEngine

        engine = SentimentFeatureEngine()
        headlines = [
            "Apple beats quarterly earnings expectations",
            "Apple Q4 earnings beat analyst expectations",  # near-duplicate
            "Federal Reserve raises interest rates by 25 basis points",
        ]
        unique = engine.deduplicate_news(headlines, threshold=0.85)
        assert len(unique) < len(headlines), "Should remove at least one duplicate"
        assert len(unique) >= 2, "Should keep at least 2 distinct headlines"

    def test_sentiment_momentum(self):
        """Sentiment momentum = short-term MA minus long-term MA."""
        from quant_monitor.features.sentiment_features import SentimentFeatureEngine

        engine = SentimentFeatureEngine()
        # Create a DataFrame with scores that shift from positive to negative
        np.random.seed(42)
        n = 100
        timestamps = pd.date_range("2026-01-01", periods=n, freq="h")
        scores = np.concatenate([np.full(70, 0.5), np.full(30, -0.5)])  # shift at index 70
        scored_df = pd.DataFrame({"timestamp": timestamps, "score": scores}).set_index("timestamp")

        momentum = engine.sentiment_momentum(scored_df)
        # At the end, short-term MA should be more negative than long-term → negative momentum
        assert momentum.iloc[-1] < 0, "Momentum should be negative after sentiment drops"


class TestSentimentModel:
    """Tests for quant_monitor/models/sentiment.py"""

    def test_score_returns_float_in_range(self):
        """score() must return float in [-1.0, +1.0]."""
        from quant_monitor.models.sentiment import SentimentModel

        model = SentimentModel()
        # Create mock sentiment features
        features = pd.DataFrame({
            "score": [0.8, 0.6, -0.3, 0.2, -0.1],
            "momentum": [0.1, 0.05, -0.2, 0.0, -0.05],
            "ma_3h": [0.7, 0.65, -0.1, 0.3, 0.0],
            "ma_24h": [0.5, 0.4, 0.1, 0.2, 0.1],
            "ma_72h": [0.3, 0.3, 0.2, 0.15, 0.15],
        })
        score = model.score(features)
        assert isinstance(score, float)
        assert -1.0 <= score <= 1.0

    def test_score_all_returns_dict(self):
        """score_all() returns {ticker: float}."""
        from quant_monitor.models.sentiment import SentimentModel

        model = SentimentModel()
        sentiment_df = pd.DataFrame({
            "ticker": ["AAPL", "AAPL", "MSFT", "MSFT"],
            "score": [0.5, 0.3, -0.2, -0.4],
            "momentum": [0.1, 0.05, -0.1, -0.15],
            "ma_3h": [0.4, 0.35, -0.15, -0.3],
            "ma_24h": [0.3, 0.25, -0.1, -0.2],
            "ma_72h": [0.2, 0.2, 0.0, -0.05],
        })
        result = model.score_all(sentiment_df)
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert "MSFT" in result
        for v in result.values():
            assert -1.0 <= v <= 1.0
```

---

### Task 4.1 — Implement `SentimentFeatureEngine.__init__()` with lazy FinBERT loading

**File:** `quant_monitor/features/sentiment_features.py`
**Method:** `SentimentFeatureEngine.__init__(self)`

**Implementation:**
```python
def __init__(self) -> None:
    """Lazy-load FinBERT model and tokenizer to save memory."""
    self._model = None
    self._tokenizer = None
    self._sentence_model = None

def _ensure_model_loaded(self) -> None:
    """Load FinBERT on first use."""
    if self._model is None:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch
        from quant_monitor.config import cfg

        model_name = cfg.sentiment.get("finbert_model", "ProsusAI/finbert")
        logger.info("Loading FinBERT model: %s", model_name)
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self._model.eval()  # inference mode
        logger.info("FinBERT model loaded successfully")

def _ensure_sentence_model_loaded(self) -> None:
    """Load sentence-transformers for deduplication on first use."""
    if self._sentence_model is None:
        from sentence_transformers import SentenceTransformer
        self._sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Sentence transformer loaded for deduplication")
```

**Key rules:**
- Model is ONLY loaded when first needed (lazy init)
- Use `cfg.sentiment["finbert_model"]` = `"ProsusAI/finbert"` from config
- Call `self._model.eval()` to disable dropout (inference mode)
- `sentence-transformers` model is separate, loaded only for deduplication

**Also add runtime imports at top of file:**
Replace `TYPE_CHECKING` guard with:
```python
import numpy as np
import pandas as pd
```

---

### Task 4.2 — Implement `SentimentFeatureEngine.score_headlines()`

**File:** `quant_monitor/features/sentiment_features.py`
**Method:** `score_headlines(self, headlines: list[str]) -> list[dict]`

**Implementation:**
```python
def score_headlines(self, headlines: list[str]) -> list[dict]:
    """Score a batch of headlines through FinBERT."""
    import torch
    self._ensure_model_loaded()

    results = []
    # Process in batches of 16 to avoid OOM
    batch_size = 16
    for i in range(0, len(headlines), batch_size):
        batch = headlines[i : i + batch_size]
        inputs = self._tokenizer(
            batch, padding=True, truncation=True, max_length=512, return_tensors="pt"
        )
        with torch.no_grad():
            outputs = self._model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

        # FinBERT label order: positive=0, negative=1, neutral=2
        labels = ["positive", "negative", "neutral"]
        for j, text in enumerate(batch):
            pos, neg, neu = probs[j].tolist()
            label = labels[probs[j].argmax().item()]
            # Score: positive=+1, negative=-1, neutral=0, weighted by probability
            score = pos - neg  # range [-1, +1]
            results.append({
                "text": text,
                "positive": round(pos, 4),
                "negative": round(neg, 4),
                "neutral": round(neu, 4),
                "label": label,
                "score": round(score, 4),
            })
    return results
```

**Key details:**
- Batch size 16 to prevent out-of-memory on CPU
- FinBERT outputs 3 classes: positive (index 0), negative (index 1), neutral (index 2)
- Score = positive_prob - negative_prob → range [-1, +1]
- Use `torch.no_grad()` for inference (saves memory)

**Acceptance criteria:**
- Test `test_score_headlines_returns_list_of_dicts` passes
- Test `test_positive_headline_scored_positive` passes
- Test `test_negative_headline_scored_negative` passes

---

### Task 4.3 — Implement `SentimentFeatureEngine.compute_sentiment_ma()`

**File:** `quant_monitor/features/sentiment_features.py`
**Method:** `compute_sentiment_ma(self, scored_df: pd.DataFrame, windows: list[int]) -> pd.DataFrame`

**Input:** `scored_df` has a DatetimeIndex (hourly/per-article timestamps) and a `score` column.
**Config:** `cfg.sentiment["sentiment_ma_windows"]` = `[3, 24, 72]` (hours)

```python
def compute_sentiment_ma(self, scored_df: pd.DataFrame, windows: list[int] | None = None) -> pd.DataFrame:
    """Compute rolling sentiment MAs over time windows (in hours)."""
    from quant_monitor.config import cfg
    if windows is None:
        windows = cfg.sentiment.get("sentiment_ma_windows", [3, 24, 72])

    result = scored_df.copy()
    for w in windows:
        col_name = f"ma_{w}h"
        result[col_name] = result["score"].rolling(window=w, min_periods=1).mean()
    return result
```

**Acceptance criteria:**
- Output DataFrame has columns `ma_3h`, `ma_24h`, `ma_72h` (for default windows)
- Values are rolling means of the `score` column

---

### Task 4.4 — Implement `SentimentFeatureEngine.sentiment_momentum()`

**File:** `quant_monitor/features/sentiment_features.py`
**Method:** `sentiment_momentum(self, scored_df: pd.DataFrame) -> pd.Series`

```python
def sentiment_momentum(self, scored_df: pd.DataFrame) -> pd.Series:
    """3h sentiment - 72h sentiment. Rapid negative shift = review trigger."""
    from quant_monitor.config import cfg
    windows = cfg.sentiment.get("sentiment_ma_windows", [3, 24, 72])

    short_window = windows[0]   # 3 hours
    long_window = windows[-1]   # 72 hours

    short_ma = scored_df["score"].rolling(window=short_window, min_periods=1).mean()
    long_ma = scored_df["score"].rolling(window=long_window, min_periods=1).mean()
    return (short_ma - long_ma).rename("sentiment_momentum")
```

**Acceptance criteria:**
- `pytest tests/test_sentiment.py::TestSentimentFeatureEngine::test_sentiment_momentum` passes
- Negative momentum = recent sentiment worse than historical

---

### Task 4.5 — Implement `SentimentFeatureEngine.deduplicate_news()`

**File:** `quant_monitor/features/sentiment_features.py`
**Method:** `deduplicate_news(self, headlines: list[str], threshold: float = 0.85) -> list[str]`

**Config:** `cfg.sentiment["similarity_dedup_threshold"]` = 0.85

```python
def deduplicate_news(self, headlines: list[str], threshold: float = 0.85) -> list[str]:
    """Deduplicate headlines via cosine similarity (sentence-transformers)."""
    if len(headlines) <= 1:
        return headlines

    self._ensure_sentence_model_loaded()
    import numpy as np

    embeddings = self._sentence_model.encode(headlines, convert_to_numpy=True)

    # Normalize for cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1  # avoid div by zero
    normalized = embeddings / norms

    # Greedy deduplication: keep first, skip similar ones
    keep = [0]
    for i in range(1, len(headlines)):
        similarities = normalized[i] @ normalized[keep].T
        if similarities.max() < threshold:
            keep.append(i)

    return [headlines[i] for i in keep]
```

**Acceptance criteria:**
- `pytest tests/test_sentiment.py::TestSentimentFeatureEngine::test_deduplicate_news_removes_similar` passes
- Near-identical headlines are removed
- Distinct headlines are preserved

---

### Task 4.6 — Implement `SentimentModel.score()` in sentiment.py

**File:** `quant_monitor/models/sentiment.py`
**Method:** `SentimentModel.score(self, sentiment_features: pd.DataFrame) -> float`

**Input DataFrame expected columns:** `score`, `momentum`, `ma_3h`, `ma_24h`, `ma_72h`

```python
def score(self, sentiment_features: pd.DataFrame) -> float:
    """Generate sentiment signal for a single ticker.

    Weighs: sentiment momentum, absolute level, 8-K classification.
    Returns: signal ∈ [-1.0, +1.0]
    """
    if sentiment_features.empty:
        return 0.0

    # Component 1: Current sentiment level (weight 0.4)
    # Use the most recent short-term MA
    current_level = 0.0
    if "ma_3h" in sentiment_features.columns:
        current_level = sentiment_features["ma_3h"].iloc[-1]
    elif "score" in sentiment_features.columns:
        current_level = sentiment_features["score"].mean()

    # Component 2: Sentiment momentum (weight 0.4)
    # Short MA - Long MA: negative = deteriorating sentiment
    momentum = 0.0
    if "momentum" in sentiment_features.columns:
        momentum = sentiment_features["momentum"].iloc[-1]
    elif "ma_3h" in sentiment_features.columns and "ma_72h" in sentiment_features.columns:
        momentum = sentiment_features["ma_3h"].iloc[-1] - sentiment_features["ma_72h"].iloc[-1]

    # Component 3: Absolute recent score (weight 0.2)
    recent_score = 0.0
    if "score" in sentiment_features.columns:
        recent_score = sentiment_features["score"].iloc[-5:].mean() if len(sentiment_features) >= 5 else sentiment_features["score"].mean()

    weighted = current_level * 0.4 + momentum * 0.4 + recent_score * 0.2
    return max(-1.0, min(1.0, weighted))
```

**Add runtime imports at top of file:**
Replace `TYPE_CHECKING` guard with:
```python
import numpy as np
import pandas as pd
```

---

### Task 4.7 — Implement `SentimentModel.score_all()` in sentiment.py

**File:** `quant_monitor/models/sentiment.py`
**Method:** `SentimentModel.score_all(self, sentiment_df: pd.DataFrame) -> dict[str, float]`

**Input:** DataFrame with a `ticker` column + sentiment feature columns.

```python
def score_all(self, sentiment_df: pd.DataFrame) -> dict[str, float]:
    """Score all tickers. Returns {ticker: signal_score}."""
    results = {}
    if "ticker" not in sentiment_df.columns:
        logger.warning("sentiment_df missing 'ticker' column")
        return results

    for ticker, group in sentiment_df.groupby("ticker"):
        try:
            results[ticker] = self.score(group)
        except Exception as e:
            logger.warning("Sentiment scoring failed for %s: %s", ticker, e)
            results[ticker] = 0.0
    return results
```

**Acceptance criteria:**
- `pytest tests/test_sentiment.py::TestSentimentModel::test_score_returns_float_in_range` passes
- `pytest tests/test_sentiment.py::TestSentimentModel::test_score_all_returns_dict` passes

---

### Task 4.8 — Run full Phase 4 test suite

```bash
doppler run -- uv run pytest tests/test_sentiment.py -v
```

**WARNING:** First run will be SLOW (~2-5 minutes) because FinBERT model needs to download.
Subsequent runs will be fast (model cached in `~/.cache/huggingface/`).

**Expected:** All 7+ tests pass.

---

## Phase 5: Fundamental Model

> **Prerequisites:** Phase 4 must be COMPLETE.
> **Data source:** yfinance fundamentals (via pipeline) — P/E, P/S, EV/EBITDA
> **No new dependencies needed.**

---

### Task 5.0 — Create Phase 5 test file

**File to CREATE:** `tests/test_fundamental.py`

```python
"""Tests for fundamental model — Phase 5."""

from __future__ import annotations

import pandas as pd
import numpy as np
import pytest


class TestFundamentalModel:
    """Tests for quant_monitor/models/fundamental.py"""

    def test_score_cheap_stock(self):
        """Stock with P/E below sector median should get positive score."""
        from quant_monitor.models.fundamental import FundamentalModel

        model = FundamentalModel()
        fundamentals = {"pe_ratio": 12.0, "ps_ratio": 1.5, "ev_ebitda": 8.0, "earnings_revision": 0.05}
        sector_data = {"pe_median": 20.0, "ps_median": 3.0, "ev_ebitda_median": 12.0}
        score = model.score(fundamentals, sector_data)
        assert isinstance(score, float)
        assert score > 0, "Cheap stock should get positive score"
        assert -1.0 <= score <= 1.0

    def test_score_expensive_stock(self):
        """Stock with P/E above sector median should get negative score."""
        from quant_monitor.models.fundamental import FundamentalModel

        model = FundamentalModel()
        fundamentals = {"pe_ratio": 40.0, "ps_ratio": 8.0, "ev_ebitda": 25.0, "earnings_revision": -0.03}
        sector_data = {"pe_median": 20.0, "ps_median": 3.0, "ev_ebitda_median": 12.0}
        score = model.score(fundamentals, sector_data)
        assert score < 0, "Expensive stock should get negative score"

    def test_score_missing_data_returns_neutral(self):
        """Missing fundamental data should return neutral (0.0)."""
        from quant_monitor.models.fundamental import FundamentalModel

        model = FundamentalModel()
        score = model.score({}, {})
        assert score == 0.0

    def test_score_all_returns_dict(self):
        """score_all returns {ticker: float} for all tickers."""
        from quant_monitor.models.fundamental import FundamentalModel

        model = FundamentalModel()
        df = pd.DataFrame({
            "ticker": ["AAPL", "AAPL", "MSFT", "MSFT"],
            "pe_ratio": [25.0, 25.0, 30.0, 30.0],
            "ps_ratio": [6.0, 6.0, 10.0, 10.0],
            "ev_ebitda": [18.0, 18.0, 22.0, 22.0],
            "earnings_revision": [0.02, 0.02, -0.01, -0.01],
            "sector": ["Tech", "Tech", "Tech", "Tech"],
            "pe_median": [20.0, 20.0, 20.0, 20.0],
            "ps_median": [5.0, 5.0, 5.0, 5.0],
            "ev_ebitda_median": [15.0, 15.0, 15.0, 15.0],
        })
        result = model.score_all(df)
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert "MSFT" in result
        for v in result.values():
            assert -1.0 <= v <= 1.0

    def test_score_range_bounds(self):
        """Score must always be in [-1, 1] regardless of extreme inputs."""
        from quant_monitor.models.fundamental import FundamentalModel

        model = FundamentalModel()
        # Extremely undervalued
        score_cheap = model.score(
            {"pe_ratio": 1.0, "ps_ratio": 0.1, "ev_ebitda": 1.0, "earnings_revision": 0.5},
            {"pe_median": 50.0, "ps_median": 20.0, "ev_ebitda_median": 30.0}
        )
        assert -1.0 <= score_cheap <= 1.0

        # Extremely overvalued
        score_expensive = model.score(
            {"pe_ratio": 500.0, "ps_ratio": 100.0, "ev_ebitda": 200.0, "earnings_revision": -0.5},
            {"pe_median": 10.0, "ps_median": 2.0, "ev_ebitda_median": 5.0}
        )
        assert -1.0 <= score_expensive <= 1.0
```

---

### Task 5.1 — Implement `FundamentalModel.score()` in fundamental.py

**File:** `quant_monitor/models/fundamental.py`
**Method:** `FundamentalModel.score(self, fundamentals: dict, sector_data: dict) -> float`

**Implementation logic — relative valuation scoring:**

```python
def score(self, fundamentals: dict, sector_data: dict) -> float:
    """Generate fundamental signal score for a single ticker.

    Compares P/E, P/S, EV/EBITDA to sector medians.
    Cheaper than sector = positive signal.
    """
    if not fundamentals or not sector_data:
        return 0.0

    signals = []

    # 1. P/E relative to sector (weight 0.35)
    pe = fundamentals.get("pe_ratio")
    pe_median = sector_data.get("pe_median")
    if pe and pe_median and pe_median > 0:
        # Negative = cheap (P/E below median), positive = expensive
        pe_signal = (pe_median - pe) / pe_median  # cheap → positive, expensive → negative
        pe_signal = max(-1.0, min(1.0, pe_signal))
        signals.append(("pe", pe_signal, 0.35))

    # 2. P/S relative to sector (weight 0.25)
    ps = fundamentals.get("ps_ratio")
    ps_median = sector_data.get("ps_median")
    if ps and ps_median and ps_median > 0:
        ps_signal = (ps_median - ps) / ps_median
        ps_signal = max(-1.0, min(1.0, ps_signal))
        signals.append(("ps", ps_signal, 0.25))

    # 3. EV/EBITDA relative to sector (weight 0.25)
    ev_ebitda = fundamentals.get("ev_ebitda")
    ev_median = sector_data.get("ev_ebitda_median")
    if ev_ebitda and ev_median and ev_median > 0:
        ev_signal = (ev_median - ev_ebitda) / ev_median
        ev_signal = max(-1.0, min(1.0, ev_signal))
        signals.append(("ev", ev_signal, 0.25))

    # 4. Earnings revision direction (weight 0.15)
    revision = fundamentals.get("earnings_revision", 0.0)
    if revision is not None:
        # revision > 0 → analysts raising estimates → bullish
        rev_signal = max(-1.0, min(1.0, revision * 5))  # scale: 0.2 revision → +1.0
        signals.append(("rev", rev_signal, 0.15))

    if not signals:
        return 0.0

    # Weighted average
    total_weight = sum(s[2] for s in signals)
    weighted_sum = sum(s[1] * s[2] for s in signals)
    return max(-1.0, min(1.0, weighted_sum / total_weight))
```

**Add runtime imports at top of file:**
Replace `TYPE_CHECKING` guard with:
```python
import numpy as np
import pandas as pd
```

**Acceptance criteria:**
- `pytest tests/test_fundamental.py::TestFundamentalModel::test_score_cheap_stock` passes
- `pytest tests/test_fundamental.py::TestFundamentalModel::test_score_expensive_stock` passes
- `pytest tests/test_fundamental.py::TestFundamentalModel::test_score_missing_data_returns_neutral` passes
- `pytest tests/test_fundamental.py::TestFundamentalModel::test_score_range_bounds` passes

---

### Task 5.2 — Implement `FundamentalModel.score_all()` in fundamental.py

**File:** `quant_monitor/models/fundamental.py`
**Method:** `FundamentalModel.score_all(self, fundamentals_df: pd.DataFrame) -> dict[str, float]`

**Input DataFrame expected columns:** `ticker`, `pe_ratio`, `ps_ratio`, `ev_ebitda`, `earnings_revision`, `sector`, `pe_median`, `ps_median`, `ev_ebitda_median`

```python
def score_all(self, fundamentals_df: pd.DataFrame) -> dict[str, float]:
    """Score all tickers. Returns {ticker: signal_score}."""
    results = {}
    if fundamentals_df.empty or "ticker" not in fundamentals_df.columns:
        return results

    for ticker, group in fundamentals_df.groupby("ticker"):
        try:
            row = group.iloc[-1]  # latest data
            fundamentals = {
                "pe_ratio": row.get("pe_ratio"),
                "ps_ratio": row.get("ps_ratio"),
                "ev_ebitda": row.get("ev_ebitda"),
                "earnings_revision": row.get("earnings_revision", 0.0),
            }
            sector_data = {
                "pe_median": row.get("pe_median"),
                "ps_median": row.get("ps_median"),
                "ev_ebitda_median": row.get("ev_ebitda_median"),
            }
            results[ticker] = self.score(fundamentals, sector_data)
        except Exception as e:
            logger.warning("Fundamental scoring failed for %s: %s", ticker, e)
            results[ticker] = 0.0
    return results
```

**Acceptance criteria:**
- `pytest tests/test_fundamental.py::TestFundamentalModel::test_score_all_returns_dict` passes

---

### Task 5.3 — Add sector classification helper to fundamental.py

**File:** `quant_monitor/models/fundamental.py`

**Add this BELOW the imports, ABOVE the class definition:**

```python
# Sector classification for the 15 portfolio holdings
# Used to group tickers for relative valuation comparison
SECTOR_MAP = {
    "SPY": "Broad Market",
    "TSM": "AI Infrastructure",
    "MU": "AI Memory",
    "PLTR": "AI Software",
    "AMZN": "E-commerce/Cloud",
    "GOOGL": "Big Tech/AI",
    "GE": "Industrial/Aerospace",
    "JPM": "Financials",
    "LMT": "Defense/Space",
    "WMT": "Defensive Retail",
    "XLP": "Staples",
    "PG": "FMCG Defensive",
    "JNJ": "Healthcare",
    "XLU": "Utilities",
    "IONQ": "Quantum/Speculative",
}

# Sector peer groups for relative valuation
SECTOR_PEERS = {
    "AI Infrastructure": ["TSM", "MU"],
    "AI Software": ["PLTR"],
    "Big Tech/AI": ["GOOGL", "AMZN"],
    "Defensive": ["WMT", "XLP", "PG", "JNJ", "XLU"],
    "Financials": ["JPM"],
    "Industrial": ["GE", "LMT"],
    "Speculative": ["IONQ"],
}
```

**Acceptance criteria:**
- `from quant_monitor.models.fundamental import SECTOR_MAP, SECTOR_PEERS` works
- All 15 portfolio tickers are in SECTOR_MAP

---

### Task 5.4 — Run full Phase 5 test suite

```bash
doppler run -- uv run pytest tests/test_fundamental.py -v
```

**Expected:** All 5 tests pass.

---

### Task 5.5 — Run FULL test suite (all phases)

```bash
doppler run -- uv run pytest tests/ -v --tb=short
```

**Expected:** All tests pass across:
- `tests/test_config.py` (3 tests from Phase 0)
- `tests/test_features.py` (~10 tests from Phase 2)
- `tests/test_models.py` (~10 tests from Phase 3)
- `tests/test_sentiment.py` (~7 tests from Phase 4)
- `tests/test_fundamental.py` (~5 tests from Phase 5)

Total: ~35 tests passing.

---

## POST-PHASE 5 — Integration Verification

### Task FINAL.1 — Integration test: Full pipeline → features → models

**File to CREATE:** `tests/test_integration_models.py`

```python
"""Integration test: data pipeline → feature engineering → model scoring.

This test requires Doppler secrets and network access.
Run with: doppler run -- uv run pytest tests/test_integration_models.py -v
"""

from __future__ import annotations

import pytest
import pandas as pd


@pytest.mark.integration
class TestFullPipeline:
    """End-to-end tests from data pull to model scoring."""

    def test_pipeline_to_technical_score(self):
        """Fetch data → compute MAs → score with technical model."""
        from quant_monitor.data.pipeline import DataPipeline
        from quant_monitor.features.moving_averages import compute_ma_matrix
        from quant_monitor.models.technical import TechnicalModel

        pipeline = DataPipeline()
        # Fetch 1 year of data for AAPL
        prices = pipeline.fetch_prices(["SPY"], period="1y")
        assert "SPY" in prices
        ohlcv = prices["SPY"]
        assert len(ohlcv) > 200, "Need > 200 rows for SMA 200"

        ma_matrix = compute_ma_matrix(ohlcv)
        assert "ema_9" in ma_matrix.columns
        assert "sma_200" in ma_matrix.columns

        model = TechnicalModel()
        score = model.score(ohlcv, ma_matrix)
        assert -1.0 <= score <= 1.0
        print(f"SPY technical score: {score:.4f}")

    def test_pipeline_to_macro_score(self):
        """Fetch FRED data → score with macro model."""
        from quant_monitor.data.pipeline import DataPipeline
        from quant_monitor.models.macro import MacroModel

        pipeline = DataPipeline()
        macro = pipeline.fetch_macro()
        assert "vix" in macro

        model = MacroModel()
        score = model.score(macro)
        assert -1.0 <= score <= 1.0

        regime = model.classify_regime(macro)
        assert regime in ("RISK_ON", "TRANSITION", "CRISIS")
        print(f"Macro score: {score:.4f}, regime: {regime}")

    def test_pipeline_to_volatility_regime(self):
        """Fetch data → compute vol features → classify regime."""
        from quant_monitor.data.pipeline import DataPipeline
        from quant_monitor.features.volatility import (
            realized_volatility,
            volatility_percentile,
            hurst_exponent,
            classify_regime,
        )

        pipeline = DataPipeline()
        prices = pipeline.fetch_prices(["SPY"], period="1y")
        ohlcv = prices["SPY"]
        returns = ohlcv["close"].pct_change().dropna()

        vol = realized_volatility(returns, window=20)
        vol_pct = volatility_percentile(vol.dropna(), lookback=252)
        hurst = hurst_exponent(ohlcv["close"])

        macro = pipeline.fetch_macro()
        vix = macro.get("vix", 20.0)

        regime = classify_regime(
            realized_vol=vol.iloc[-1],
            vol_percentile=vol_pct.iloc[-1],
            hurst=hurst,
            vix=vix,
        )
        print(f"Vol: {vol.iloc[-1]:.4f}, Percentile: {vol_pct.iloc[-1]:.2f}, "
              f"Hurst: {hurst:.3f}, VIX: {vix}, Regime: {regime}")
        assert regime in ("LOW_VOL_TREND", "HIGH_VOL_TREND", "LOW_VOL_RANGE",
                         "HIGH_VOL_RANGE", "CRISIS")
```

**Acceptance criteria:**
- `doppler run -- uv run pytest tests/test_integration_models.py -v` — all 3 tests pass
- End-to-end flow: real data → features → model scores

---

## Quick Reference: Config Values Used Across All Phases

| Config Section | Key | Value | Used In |
|---------------|-----|-------|---------|
| `[moving_averages]` | ema_fast | 9 | compute_ma_matrix |
| `[moving_averages]` | ema_medium | 21 | compute_ma_matrix |
| `[moving_averages]` | sma_medium | 50 | compute_ma_matrix |
| `[moving_averages]` | sma_long | 200 | compute_ma_matrix |
| `[moving_averages]` | kama_period | 10 | compute_ma_matrix |
| `[moving_averages]` | hma_period | 16 | compute_ma_matrix |
| `[moving_averages]` | mvwap_period | 20 | compute_ma_matrix |
| `[volatility]` | realized_vol_window | 20 | realized_volatility |
| `[volatility]` | vol_percentile_lookback | 252 | volatility_percentile |
| `[volatility]` | hurst_trending_threshold | 0.6 | classify_regime |
| `[volatility]` | hurst_reverting_threshold | 0.4 | classify_regime |
| `[volatility]` | vix_crisis_threshold | 30.0 | classify_regime |
| `[macro_thresholds]` | vix_risk_off | 25.0 | MacroModel.score |
| `[macro_thresholds]` | yield_curve_inversion | 0.0 | MacroModel.classify_regime |
| `[macro_thresholds]` | dxy_spike_weekly_pct | 2.0 | MacroModel.per_ticker_impact |
| `[macro_thresholds]` | ten_year_yield_spike_bps | 20.0 | MacroModel.per_ticker_impact |
| `[sentiment]` | finbert_model | ProsusAI/finbert | SentimentFeatureEngine |
| `[sentiment]` | sentiment_ma_windows | [3, 24, 72] | compute_sentiment_ma |
| `[sentiment]` | similarity_dedup_threshold | 0.85 | deduplicate_news |
| `[signal_thresholds]` | confidence_min | 0.65 | Phase 6 (fusion) |
| `[signal_thresholds]` | fused_score_min | 0.35 | Phase 6 (fusion) |
| `[signal_thresholds]` | drift_threshold | 0.02 | Phase 7 (optimizer) |
| `[signal_thresholds]` | kill_switch_drawdown | 0.15 | Phase 7 (risk manager) |

---

## Quick Reference: All 15 Portfolio Tickers

```
SPY, TSM, MU, PLTR, AMZN, GOOGL, GE, JPM, LMT, WMT, XLP, PG, JNJ, XLU, IONQ
```

Access via: `cfg.tickers` (returns list of strings)

---

## Quick Reference: Doppler Secrets Available

| Secret Name | Description |
|------------|-------------|
| MASSIVE_API_KEY | Polygon.io/Massive API key |
| MASSIVE_S3_ENDPOINT | Massive S3 endpoint |
| MASSIVE_S3_ACCESS_KEY_ID | Massive S3 access key |
| MASSIVE_S3_SECRET_ACCESS_KEY | Massive S3 secret |
| MASSIVE_S3_BUCKET | Massive S3 bucket name |
| FRED_API_KEY | FRED economic data API |
| SEC_EDGAR_USER_AGENT | SEC EDGAR user agent string |
| APPWRITE_ENDPOINT | Appwrite Cloud endpoint |
| APPWRITE_PROJECT_ID | Appwrite project ID |
| APPWRITE_API_KEY | Appwrite API key |
| TELEGRAM_BOT_TOKEN | Telegram bot token |
| TELEGRAM_CHAT_ID | Telegram chat ID |
| ZYTE_API_KEY | Zyte/Scrapy Cloud API key |
| ALPACA_API_KEY | (NOT_AVAILABLE — using yfinance) |
| ALPACA_SECRET_KEY | (NOT_AVAILABLE — using yfinance) |

Access via: `cfg.secrets.MASSIVE_API_KEY` etc. (after Task 0.3)
Or directly: `os.environ.get("MASSIVE_API_KEY")`

---

## Execution Order Summary

```
Phase 0 (Housekeeping):
  0.1 → 0.2 → 0.3 → 0.4 → 0.5

Phase 2 (Feature Engineering):
  2.8 → 2.13 (imports first!)
  2.1 → 2.2 → 2.3 → 2.4 → 2.5 → 2.6 → 2.7
  2.9 → 2.10 → 2.11 → 2.12
  2.14 (run tests)

Phase 3 (Technical + Macro Models):
  3.0 (tests first)
  3.1 → 3.2 (technical)
  3.3 → 3.4 → 3.5 (macro)
  3.6 (run tests)

Phase 4 (Sentiment):
  4.0 (tests first)
  4.1 → 4.2 → 4.3 → 4.4 → 4.5 (features)
  4.6 → 4.7 (model)
  4.8 (run tests)

Phase 5 (Fundamental):
  5.0 (tests first)
  5.1 → 5.2 → 5.3 (model)
  5.4 (run tests)
  5.5 (full test suite)

Final Integration:
  FINAL.1 (end-to-end test)
```

---

*Generated: February 25, 2026 | Covers Phase 0 through Phase 5*
*Phases 6-10 (Fusion, Agent, Backtest, Dashboard, Alerts) will be planned after Phase 5 completion.*
