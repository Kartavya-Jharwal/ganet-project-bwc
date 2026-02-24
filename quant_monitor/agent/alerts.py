"""Telegram bot alert dispatcher.

Alert types and priorities:
| Alert             | Trigger                              | Priority |
|-------------------|--------------------------------------|----------|
| REBALANCE         | Position drift >2% + confidence >0.65| High     |
| RISK_BREACH       | Position >10% or sector >25%         | Critical |
| MACRO_SHIFT       | Regime change detected               | High     |
| KILL_SWITCH       | Position down >15% intraday          | Critical |
| EARNINGS_UPCOMING | Earnings within 3 trading days       | Medium   |
| SENTIMENT_SPIKE   | Rapid negative sentiment shift       | Medium   |
| FEED_STALE        | Data source stale >30 min            | Low      |
"""

from __future__ import annotations

import logging
from enum import StrEnum

logger = logging.getLogger(__name__)


class AlertPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertType(StrEnum):
    REBALANCE = "REBALANCE"
    RISK_BREACH = "RISK_BREACH"
    MACRO_SHIFT = "MACRO_SHIFT"
    KILL_SWITCH = "KILL_SWITCH"
    EARNINGS_UPCOMING = "EARNINGS_UPCOMING"
    SENTIMENT_SPIKE = "SENTIMENT_SPIKE"
    FEED_STALE = "FEED_STALE"


class AlertDispatcher:
    """Sends formatted alerts to Telegram."""

    def __init__(self) -> None:
        # TODO Phase 10: Initialize telegram bot from cfg.secrets
        pass

    async def send_alert(
        self,
        alert_type: AlertType,
        priority: AlertPriority,
        message: str,
        ticker: str | None = None,
    ) -> bool:
        """Send an alert to the configured Telegram chat.

        Respects cooldown period to avoid spam.
        Returns True if sent, False if suppressed by cooldown.
        """
        # TODO Phase 10
        raise NotImplementedError

    def format_rebalance_alert(self, trades: list[dict]) -> str:
        """Format a rebalancing recommendation into a readable message."""
        # TODO Phase 10
        raise NotImplementedError

    def format_kill_switch_alert(self, position: dict) -> str:
        """Format a kill switch alert with position details."""
        # TODO Phase 10
        raise NotImplementedError
