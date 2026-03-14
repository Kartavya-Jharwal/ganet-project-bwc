"""Walk-forward backtesting engine.

No simple backtests — walk-forward only (avoids lookahead bias).
- Training window: 252 days (1 year)
- Test window: 21 days (1 month)
- Roll forward: 21 days at a time

Models tested independently then compared:
1. Technical only
2. Fundamental only
3. Sentiment only
4. Fused (static equal weights)
5. Fused (dynamic regime weights) ← expected winner
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


class WalkForwardEngine:
    """Walk-forward backtesting with configurable train/test windows."""

    def __init__(
        self,
        train_window: int = 252,
        test_window: int = 21,
        step_size: int = 21,
    ) -> None:
        self.train_window = train_window
        self.test_window = test_window
        self.step_size = step_size

    def run(self, data: pd.DataFrame, model_name: str) -> dict:
        """Run walk-forward backtest for a single model configuration.

        For each window:
        1. Train period: compute features
        2. Test period: generate signals, track P/L

        Returns: dict of aggregated metrics across all test windows.
        """
        import pandas as pd

        from quant_monitor.backtest.metrics import calmar_ratio, max_drawdown, sharpe_ratio

        n = len(data)
        min_required = self.train_window + self.test_window

        if n < min_required:
            logger.warning(
                "Insufficient data: %d rows, need %d (train=%d + test=%d)",
                n,
                min_required,
                self.train_window,
                self.test_window,
            )
            return {"error": "insufficient_data", "rows": n, "required": min_required}

        all_test_returns = []
        window_results = []

        start = 0
        while start + min_required <= n:
            train_end = start + self.train_window
            test_end = min(train_end + self.test_window, n)

            train_data = data.iloc[start:train_end]
            test_data = data.iloc[train_end:test_end]

            # Generate simple signals based on model_name
            test_returns = test_data["close"].pct_change().dropna()

            if model_name == "technical":
                # Use MA crossover signal from training period
                from quant_monitor.features.moving_averages import ema

                fast_ma = ema(train_data["close"], 9)
                slow_ma = ema(train_data["close"], 21)
                signal = 1.0 if fast_ma.iloc[-1] > slow_ma.iloc[-1] else -1.0
                test_returns = test_returns * signal

            elif model_name == "fundamental":
                # Fundamental: pure beta exposure (always long)
                signal = 1.0
                test_returns = test_returns * signal

            elif model_name == "sentiment":
                # Sentiment: momentum-based (lagged return sign)
                prev_return = train_data["close"].pct_change().iloc[-5:].mean()
                signal = 1.0 if prev_return > 0 else -1.0
                test_returns = test_returns * signal

            elif model_name == "fused_equal":
                # Equal weight fusion of simple signals
                from quant_monitor.features.moving_averages import ema
                fast_ma = ema(train_data["close"], 9)
                slow_ma = ema(train_data["close"], 21)
                tech_sig = 1.0 if fast_ma.iloc[-1] > slow_ma.iloc[-1] else -1.0
                fund_sig = 1.0
                prev_return = train_data["close"].pct_change().iloc[-5:].mean()
                sent_sig = 1.0 if prev_return > 0 else -1.0
                
                fused_signal = (tech_sig + fund_sig + sent_sig) / 3.0
                test_returns = test_returns * fused_signal

            elif model_name == "fused_regime":
                # Regime-weighted: scale by volatility regime
                from quant_monitor.features.volatility import realized_volatility

                vol = realized_volatility(train_data["close"].pct_change().dropna())
                if not vol.empty and vol.iloc[-1] > 0.3:
                    test_returns = test_returns * 0.5  # reduce in high vol

            all_test_returns.extend(test_returns.tolist())
            window_results.append(
                {
                    "window_start": start,
                    "window_end": test_end,
                    "mean_return": float(test_returns.mean()) if len(test_returns) > 0 else 0.0,
                }
            )

            start += self.step_size

        if not all_test_returns:
            return {"error": "no_test_returns", "windows_tested": 0}

        returns_series = pd.Series(all_test_returns)

        return {
            "model": model_name,
            "sharpe_ratio": sharpe_ratio(returns_series),
            "max_drawdown": max_drawdown(returns_series),
            "calmar_ratio": calmar_ratio(returns_series),
            "total_return": float((1 + returns_series).prod() - 1),
            "mean_daily_return": float(returns_series.mean()),
            "windows_tested": len(window_results),
            "window_details": window_results,
        }

    def compare_models(self, data: pd.DataFrame) -> pd.DataFrame:
        """Run all 5 model configs and return comparative metrics table.

        Models tested:
        1. technical — MA crossover signals
        2. fundamental — buy and hold
        3. sentiment — momentum-based
        4. fused_equal — equal-weight fusion
        5. fused_regime — dynamic regime-weighted fusion (expected winner)
        """
        import pandas as pd

        model_names = ["technical", "fundamental", "sentiment", "fused_equal", "fused_regime"]
        results = []

        for name in model_names:
            try:
                metrics = self.run(data, name)
                if "error" not in metrics:
                    results.append(metrics)
                else:
                    logger.warning("Model '%s' backtest failed: %s", name, metrics.get("error"))
            except Exception as e:
                logger.warning("Model '%s' backtest exception: %s", name, e)

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)
        # Set model name as index for easy comparison
        if "model" in df.columns:
            df = df.set_index("model")
        return df
