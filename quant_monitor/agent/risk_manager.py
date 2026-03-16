"""Risk manager — position limits, beta targets, kill switch.

Validates proposed trades against charter constraints and dynamic risk params.
Adjusts limits based on current macro regime.

| Macro Regime | Max Position | Max Sector | Target Beta |
|-------------|-------------|-----------|------------|
| RISK_ON     | 10%         | 25%       | 0.50       |
| TRANSITION  | 8%          | 20%       | 0.35       |
| CRISIS      | 5%          | 15%       | 0.20       |
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class RiskManager:
    """Validates trades and monitors portfolio risk constraints."""

    def validate_trades(
        self,
        proposed_trades: list[dict],
        current_positions: dict,
        regime: str,
    ) -> list[dict]:
        """Validate proposed trades against risk limits.

        Returns the same list with 'rejected_reason' field added to failing trades.
        Passing trades have rejected_reason = None.
        """
        from quant_monitor.config import cfg

        params = cfg.risk_params.get(regime, cfg.risk_params.get("RISK_ON", {}))
        max_position = params.get("max_position", 0.10)

        validated = []
        for trade in proposed_trades:
            trade = dict(trade)
            ticker = trade.get("ticker", "UNKNOWN")
            target_weight = trade.get("target_weight", 0.0)

            if target_weight > max_position:
                trade["rejected_reason"] = (
                    f"{ticker}: target weight {target_weight:.1%} exceeds {regime} max {max_position:.0%}"
                )
            else:
                trade["rejected_reason"] = None

            validated.append(trade)

        passed = sum(1 for t in validated if not t.get("rejected_reason"))
        rejected = len(validated) - passed
        if rejected:
            logger.warning("Rejected %d/%d trades in %s regime", rejected, len(validated), regime)

        return validated

    def check_kill_switch(self, positions: dict, current_prices: dict) -> list[dict]:
        """Check if any position is down >15% intraday.

        Returns list of positions triggering the kill switch.
        Each dict has: ticker, open_price, current_price, drawdown_pct.
        """
        from quant_monitor.config import cfg

        threshold = cfg.signal_thresholds.get("kill_switch_drawdown", 0.15)
        kills = []

        for ticker, pos in positions.items():
            open_price = pos.get("open_price", pos.get("avg_cost", 0))
            current = current_prices.get(ticker)
            if open_price and current and open_price > 0:
                drawdown = (open_price - current) / open_price
                if drawdown > threshold:
                    kills.append(
                        {
                            "ticker": ticker,
                            "open_price": open_price,
                            "current_price": current,
                            "drawdown_pct": round(drawdown, 4),
                        }
                    )
                    logger.critical(
                        "KILL SWITCH: %s down %.1f%% intraday (open=%.2f, now=%.2f)",
                        ticker,
                        drawdown * 100,
                        open_price,
                        current,
                    )
        return kills

    def check_position_limits(self, weights: dict[str, float], regime: str) -> list[str]:
        """Check for position and sector limit breaches.

        Returns list of violation description strings.
        Uses regime-dependent limits from cfg.risk_params.
        """
        from quant_monitor.config import cfg
        from quant_monitor.models.fundamental import SECTOR_PEERS

        params = cfg.risk_params.get(regime, cfg.risk_params.get("RISK_ON", {}))
        max_position = params.get("max_position", 0.10)
        max_sector = params.get("max_sector", 0.25)

        violations = []

        # Check individual position limits
        for ticker, weight in weights.items():
            if weight > max_position:
                violations.append(
                    f"POSITION_BREACH: {ticker} at {weight:.1%} exceeds {regime} max {max_position:.0%}"
                )

        # Check sector concentration
        ticker_to_peer_group = {t: k for k, v in SECTOR_PEERS.items() for t in v}
        sector_weights: dict[str, float] = {}
        for ticker, weight in weights.items():
            sector = ticker_to_peer_group.get(ticker, "Unknown")
            sector_weights[sector] = sector_weights.get(sector, 0.0) + weight

        for sector, total in sector_weights.items():
            if total > max_sector:
                violations.append(
                    f"SECTOR_BREACH: {sector} at {total:.1%} exceeds {regime} max {max_sector:.0%}"
                )

        return violations

    def compute_portfolio_beta(self, weights: dict[str, float], betas: dict[str, float]) -> float:
        """Compute weighted portfolio beta.

        β_portfolio = Σ(w_i × β_i) for all positions.
        """
        total_beta = 0.0
        for ticker, weight in weights.items():
            beta = betas.get(ticker, 1.0)  # default to market beta
            total_beta += weight * beta
        return total_beta
