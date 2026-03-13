"""Technical analysis model — MA crossovers, RSI, MACD, Bollinger, volume.

Produces a signal score ∈ [-1.0, +1.0].
Volume confirmation required for high-confidence signals.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TechnicalModel:
    """Technical analysis signal generator."""

    def score(self, ohlcv: pd.DataFrame, ma_matrix: pd.DataFrame) -> float:
        """Generate technical signal score for a single ticker.

        Components:
        - MA crossover matrix (EMA9/21, SMA50/200)   weight 0.30
        - RSI divergence                              weight 0.20
        - MACD histogram direction                    weight 0.20
        - Bollinger Band position                     weight 0.15
        - Volume confirmation multiplier              weight 0.15

        Returns: signal ∈ [-1.0, +1.0]
        """
        close = ohlcv["close"]

        # ── Component 1: MA Crossover (0.30) ────────────────────────────────
        ma_signal = 0.0
        if "ema_9" in ma_matrix.columns and "ema_21" in ma_matrix.columns:
            ema9 = ma_matrix["ema_9"].iloc[-1]
            ema21 = ma_matrix["ema_21"].iloc[-1]
            if not (np.isnan(ema9) or np.isnan(ema21)):
                ma_signal += 0.5 if ema9 > ema21 else -0.5
        if "sma_50" in ma_matrix.columns and "sma_200" in ma_matrix.columns:
            sma50 = ma_matrix["sma_50"].iloc[-1]
            sma200 = ma_matrix["sma_200"].iloc[-1]
            if not (np.isnan(sma50) or np.isnan(sma200)):
                ma_signal += 0.5 if sma50 > sma200 else -0.5
        ma_signal = max(-1.0, min(1.0, ma_signal))

        # ── Component 2: RSI (0.20) ─────────────────────────────────────────
        rsi_signal = 0.0
        try:
            period = 14
            delta = close.diff()
            gain = delta.clip(lower=0).rolling(period).mean()
            loss = (-delta.clip(upper=0)).rolling(period).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            rsi_val = rsi.iloc[-1]
            if not np.isnan(rsi_val):
                if rsi_val > 70:
                    rsi_signal = -min((rsi_val - 70) / 30, 1.0)
                elif rsi_val < 30:
                    rsi_signal = min((30 - rsi_val) / 30, 1.0)
                else:
                    rsi_signal = (rsi_val - 50) / 20
        except Exception:
            rsi_signal = 0.0

        # ── Component 3: MACD histogram (0.20) ──────────────────────────────
        macd_signal = 0.0
        try:
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            histogram = macd_line - signal_line
            h_now = histogram.iloc[-1]
            h_prev = histogram.iloc[-2] if len(histogram) > 1 else h_now
            if not (np.isnan(h_now) or np.isnan(h_prev)):
                if h_now > 0 and h_now >= h_prev:
                    macd_signal = 1.0
                elif h_now > 0 and h_now < h_prev:
                    macd_signal = 0.3
                elif h_now < 0 and h_now <= h_prev:
                    macd_signal = -1.0
                else:
                    macd_signal = -0.3
        except Exception:
            macd_signal = 0.0

        # ── Component 4: Bollinger Bands (0.15) ─────────────────────────────
        bb_signal = 0.0
        try:
            bb_period = 20
            bb_std = 2
            mid = close.rolling(bb_period).mean()
            std = close.rolling(bb_period).std()
            upper = mid + bb_std * std
            lower = mid - bb_std * std
            price = close.iloc[-1]
            u = upper.iloc[-1]
            l = lower.iloc[-1]
            band_width = u - l
            if not np.isnan(band_width) and band_width > 0:
                if (u - price) / band_width < 0.05:
                    bb_signal = -0.5
                elif (price - l) / band_width < 0.05:
                    bb_signal = 0.5
        except Exception:
            bb_signal = 0.0

        # ── Component 5: Volume confirmation (0.15) ─────────────────────────
        volume_factor = 0.75
        try:
            vol = ohlcv["volume"]
            avg_vol = vol.rolling(20).mean().iloc[-1]
            cur_vol = vol.iloc[-1]
            if not np.isnan(avg_vol) and avg_vol > 0:
                ratio = cur_vol / avg_vol
                if ratio > 1.5:
                    volume_factor = 1.0
                elif ratio < 0.5:
                    volume_factor = 0.5
        except Exception:
            volume_factor = 0.75

        # ── Weighted combination ─────────────────────────────────────────────
        raw = (
            ma_signal * 0.30 + rsi_signal * 0.20 + macd_signal * 0.20 + bb_signal * 0.15
        ) * volume_factor + bb_signal * 0.15 * (1 - volume_factor)
        # Simpler: weighted sum, volume scales the non-bb components
        raw = (
            ma_signal * 0.30 + rsi_signal * 0.20 + macd_signal * 0.20 + bb_signal * 0.15
        ) * volume_factor
        return float(max(-1.0, min(1.0, raw)))

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
                results[ticker] = 0.0
        return results
