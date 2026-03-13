"""Macro regime model — VIX, yield curve, DXY, 10Y yield signals.

Produces a signal score ∈ [-1.0, +1.0] as portfolio-level adjustment.
Triggers regime classification that shifts fusion weights.

| Signal        | Threshold         | Portfolio Impact                           |
|---------------|-------------------|--------------------------------------------|
| VIX           | > 25              | Risk-off: reduce beta, increase defensives |
| Yield curve   | Inverting          | Recession signal: shift defensive          |
| DXY           | Spiking            | Headwind for TSM (FX), AMZN international  |
| 10Y yield     | Rising >20bps/week | Headwind for PLTR/IONQ high-multiple names |
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class MacroModel:
    """Macro regime signal generator and classifier."""

    def score(self, macro_snapshot: dict) -> float:
        macro_snapshot = {k: (v if v is not None else 0.0) for k, v in macro_snapshot.items()}

        """Generate macro signal (portfolio-level, not per-ticker).

        Returns: signal ∈ [-1.0, +1.0] where:
            -1.0 = extreme risk-off
            +1.0 = extreme risk-on
        """
        from quant_monitor.config import cfg

        thresholds = cfg.macro_thresholds
        signals = []

        # 1. VIX signal
        vix = macro_snapshot.get("vix")
        if vix is None:
            vix = 20.0
        vix_threshold = thresholds["vix_risk_off"]  # 25.0
        if vix < 15:
            signals.append(1.0)
        elif vix < vix_threshold:
            signals.append(1.0 - (vix - 15) / (vix_threshold - 15))
        elif vix < 35:
            signals.append(-(vix - vix_threshold) / (35 - vix_threshold))
        else:
            signals.append(-1.0)

        # 2. Yield curve
        spread = macro_snapshot.get("yield_10y_2y_spread", 0.5)
        if spread > 1.0:
            signals.append(1.0)
        elif spread > 0 or spread > -1.0:
            signals.append(spread / 1.0)
        else:
            signals.append(-1.0)

        # 3. DXY spike
        dxy_change = abs(macro_snapshot.get("dxy_weekly_change_pct", 0.0))
        dxy_spike = thresholds["dxy_spike_weekly_pct"]  # 2.0
        if dxy_change < dxy_spike * 0.5:
            signals.append(0.5)
        elif dxy_change < dxy_spike:
            signals.append(0.0)
        else:
            signals.append(-min(dxy_change / dxy_spike, 2.0) / 2.0)

        # 4. 10Y yield spike
        yield_change = abs(macro_snapshot.get("ten_year_yield_weekly_bps", 0.0))
        yield_spike = thresholds["ten_year_yield_spike_bps"]  # 20.0
        if yield_change < yield_spike * 0.5:
            signals.append(0.3)
        elif yield_change < yield_spike:
            signals.append(0.0)
        else:
            signals.append(-min(yield_change / yield_spike, 2.0) / 2.0)

        avg = sum(signals) / len(signals)
        return float(max(-1.0, min(1.0, avg)))

    def classify_regime(self, macro_snapshot: dict) -> str:
        macro_snapshot = {k: (v if v is not None else 0.0) for k, v in macro_snapshot.items()}

        """Classify current macro regime: RISK_ON | TRANSITION | CRISIS."""
        from quant_monitor.config import cfg

        thresholds = cfg.macro_thresholds

        vix = macro_snapshot.get("vix", 20.0)
        spread = macro_snapshot.get("yield_10y_2y_spread", 0.5)
        dxy_change = abs(macro_snapshot.get("dxy_weekly_change_pct", 0.0))
        yield_change = abs(macro_snapshot.get("ten_year_yield_weekly_bps", 0.0))

        crisis_signals = 0
        if vix > 30:
            crisis_signals += 2
        elif vix > thresholds["vix_risk_off"]:
            crisis_signals += 1

        if spread < thresholds["yield_curve_inversion"]:
            crisis_signals += 1

        if dxy_change > thresholds["dxy_spike_weekly_pct"]:
            crisis_signals += 1

        if yield_change > thresholds["ten_year_yield_spike_bps"]:
            crisis_signals += 1

        if crisis_signals >= 3:
            return "CRISIS"
        elif crisis_signals >= 1:
            return "TRANSITION"
        else:
            return "RISK_ON"

    def per_ticker_impact(self, macro_snapshot: dict, ticker: str, sector: str) -> float:
        macro_snapshot = {k: (v if v is not None else 0.0) for k, v in macro_snapshot.items()}

        """Compute macro headwind/tailwind for a specific ticker.

        E.g., rising DXY → negative for TSM (ADR FX risk).
        """
        from quant_monitor.config import cfg

        thresholds = cfg.macro_thresholds
        impact = 0.0

        dxy_change = macro_snapshot.get("dxy_weekly_change_pct", 0.0)
        yield_bps = macro_snapshot.get("ten_year_yield_weekly_bps", 0.0)
        vix = macro_snapshot.get("vix", 20.0)

        # DXY sensitivity: ADRs and international revenue companies
        dxy_sensitive = {"TSM", "AMZN", "GOOGL"}
        if ticker in dxy_sensitive and abs(dxy_change) > thresholds["dxy_spike_weekly_pct"]:
            impact -= 0.3 * (dxy_change / thresholds["dxy_spike_weekly_pct"])

        # Rate sensitivity: high-multiple growth names hurt by rising yields
        rate_sensitive = {"PLTR", "IONQ", "AMZN", "GOOGL"}
        if ticker in rate_sensitive and yield_bps > thresholds["ten_year_yield_spike_bps"]:
            impact -= 0.3 * (yield_bps / thresholds["ten_year_yield_spike_bps"])

        # Defensive tickers benefit from risk-off
        defensive = {"WMT", "XLP", "PG", "JNJ", "XLU"}
        if ticker in defensive and vix > thresholds["vix_risk_off"]:
            impact += 0.2

        # Financials benefit from rising rates
        if ticker == "JPM" and yield_bps > 0:
            impact += 0.15 * min(yield_bps / thresholds["ten_year_yield_spike_bps"], 1.0)

        return float(max(-1.0, min(1.0, impact)))
