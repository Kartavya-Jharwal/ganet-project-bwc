"""Multi-channel alert dispatcher (Telegram + ntfy).

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

Channels:
- Telegram Bot API — rich HTML-formatted messages
- ntfy.sh — simple HTTP-based pub-sub (push to UUID topic, no auth needed)
  Subscribe: ntfy.sh/<NTFY_TOPIC> or via ntfy mobile/desktop app
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from enum import StrEnum

import httpx

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
    """Sends formatted alerts to Telegram and ntfy."""
    def __init__(self) -> None:
        from quant_monitor.config import cfg
        self._last_alert_times: dict[str, datetime] = {}
        self._enabled = True
        self._cooldown_minutes = cfg.project.get("alert_cooldown_minutes", 60)
        self._telegram_token = cfg.secrets.TELEGRAM_BOT_TOKEN
        self._chat_id = cfg.secrets.TELEGRAM_CHAT_ID
        if self._telegram_token:
            from telegram import Bot
            self._bot = Bot(token=self._telegram_token)
        else:
            self._bot = None
        if self._telegram_token and not self._chat_id:
            logger.warning("TELEGRAM_CHAT_ID missing. Telegram alerts disabled.")
        self._ntfy_topic = getattr(cfg.secrets, "NTFY_TOPIC", None)
        self._ntfy_base_url = "https://ntfy.sh"
        if not self._ntfy_topic:
            logger.warning("NTFY_TOPIC secret not found. ntfy alerts disabled.")
        """Sends formatted alerts to Telegram and ntfy.sh."""

    def _is_on_cooldown(
        self,
        alert_type: AlertType,
        ticker: str | None = None,
        priority: AlertPriority = AlertPriority.MEDIUM,
    ) -> bool:
        """Check if an alert is suppressed by cooldown.

        CRITICAL alerts always bypass cooldown.
        """
        if priority == AlertPriority.CRITICAL:
            return False

        key = f"{alert_type}:{ticker or 'PORTFOLIO'}"
        last_sent = self._last_alert_times.get(key)
        if last_sent is None:
            return False

        elapsed = datetime.utcnow() - last_sent
        return elapsed < timedelta(minutes=self._cooldown_minutes)

    def _record_alert(self, alert_type: AlertType, ticker: str | None = None) -> None:
        """Record that an alert was sent (for cooldown tracking)."""
        key = f"{alert_type}:{ticker or 'PORTFOLIO'}"
        self._last_alert_times[key] = datetime.utcnow()

    async def send_alert(
        self,
        alert_type: AlertType,
        priority: AlertPriority,
        message: str,
        ticker: str | None = None,
    ) -> bool:
        """Send an alert to ALL configured channels (Telegram + ntfy).

        Respects cooldown period to avoid spam.
        Returns True if sent to at least one channel, False if suppressed/errored.
        """
        if not self._enabled:
            logger.debug("Alerts disabled — suppressing %s", alert_type)
            return False

        if self._is_on_cooldown(alert_type, ticker, priority):
            logger.debug("Alert on cooldown: %s for %s", alert_type, ticker)
            return False

        # Format with priority prefix
        priority_emoji = {
            AlertPriority.LOW: "[INFO]",
            AlertPriority.MEDIUM: "⚠️",
            AlertPriority.HIGH: "🔔",
            AlertPriority.CRITICAL: "🚨",
        }
        prefix = priority_emoji.get(priority, "")
        full_message = f"{prefix} [{priority}] {alert_type}\n\n{message}"

        sent = False

        # --- Channel 1: Telegram ---
        if self._bot and self._chat_id:
            try:
                await self._bot.send_message(
                    chat_id=self._chat_id,
                    text=full_message,
                    parse_mode="HTML",
                )
                logger.info("Telegram alert sent: %s for %s", alert_type, ticker or "PORTFOLIO")
                sent = True
            except Exception as e:
                logger.error("Failed to send Telegram alert: %s", e)

        # --- Channel 2: ntfy.sh ---
        if self._ntfy_topic:
            try:
                url = f"{self._ntfy_base_url}/{self._ntfy_topic}"
                plain_text = self._strip_html(full_message)
                title = f"QPM: {alert_type}" + (f" — {ticker}" if ticker else "")

                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        url,
                        content=plain_text,
                        headers={
                            "Title": title,
                            "Priority": self._ntfy_priority(priority),
                            "Tags": ",".join(
                                filter(None, [alert_type.lower(), ticker, priority.lower()])
                            ),
                        },
                    )
                if resp.status_code == 200:
                    logger.info("ntfy alert sent: %s for %s", alert_type, ticker or "PORTFOLIO")
                    sent = True
                else:
                    logger.warning("ntfy returned %d: %s", resp.status_code, resp.text[:200])
            except Exception as e:
                logger.error("Failed to send ntfy alert: %s", e)

        # --- Fallback: log-only ---
        if not sent:
            logger.info("ALERT (log-only): %s", full_message)

        # Record for cooldown only when we actually sent to at least one channel.
        if sent:
            self._record_alert(alert_type, ticker)

        # --- Persist to Appwrite ---
        try:
            from quant_monitor.data.appwrite_client import create_appwrite_client

            aw = create_appwrite_client()
            aw.write_alert(
                alert_type=str(alert_type),
                message=self._strip_html(full_message),
                severity=str(priority),
                ticker=ticker,
                dispatched=sent,
            )
        except Exception as e:
            logger.warning("Failed to persist alert to Appwrite: %s", e)

        return sent

    @staticmethod
    def _strip_html(text: str) -> str:
        """Strip HTML tags for plain-text channels (ntfy)."""
        return re.sub(r"<[^>]+>", "", text)

    @staticmethod
    def _ntfy_priority(priority: AlertPriority) -> str:
        """Map AlertPriority to ntfy priority header value (1-5)."""
        return {
            AlertPriority.LOW: "2",
            AlertPriority.MEDIUM: "3",
            AlertPriority.HIGH: "4",
            AlertPriority.CRITICAL: "5",
        }.get(priority, "3")

    def format_rebalance_alert(self, trades: list[dict]) -> str:
        """Format a rebalancing recommendation into a readable message."""
        lines = ["<b>📊 Rebalance Recommendation</b>\n"]

        for trade in trades:
            ticker = trade.get("ticker", "???")
            action = trade.get("action", "???")
            current = trade.get("current_weight", 0)
            target = trade.get("target_weight", 0)
            delta = trade.get("delta", 0)

            arrow = "⬆️" if action == "BUY" else "⬇️"
            lines.append(
                f"{arrow} <b>{ticker}</b>: {action} ({current:.1%} → {target:.1%}, Δ{delta:+.1%})"
            )

        return "\n".join(lines)

    def format_kill_switch_alert(self, position: dict) -> str:
        """Format a kill switch alert with position details."""
        ticker = position.get("ticker", "???")
        open_price = position.get("open_price", 0)
        current = position.get("current_price", 0)
        drawdown = position.get("drawdown_pct", 0)

        return (
            f"🚨 <b>KILL SWITCH TRIGGERED</b>\n\n"
            f"<b>{ticker}</b> is down <b>{drawdown * 100:.1f}%</b> intraday!\n"
            f"Open: ${open_price:.2f} → Current: ${current:.2f}\n\n"
            f"<i>Immediate review recommended.</i>"
        )
    def format_macro_shift_alert(self, old_regime: str, new_regime: str, macro_data: dict) -> str:
        """Format a macro regime change alert."""
        vix = macro_data.get("vix", "N/A")
        spread = macro_data.get("yield_10y_2y_spread", "N/A")
        return (
            f"🔄 <b>Macro Regime Change</b>\n\n"
            f"{old_regime} → <b>{new_regime}</b>\n"
            f"VIX: {vix} | Yield Spread: {spread}\n\n"
            f"<i>Model weights have been adjusted.</i>"
        )

    def format_sentiment_spike_alert(self, ticker: str, momentum: float, headline: str | None = None) -> str:
        """Format a sentiment spike alert."""
        direction = "negative" if momentum < 0 else "positive"
        msg = (
            f"📰 <b>Sentiment Spike: {ticker}</b>\n\n"
            f"Sentiment momentum: <b>{momentum:+.3f}</b> ({direction})\n"
        )
        if headline:
            msg += f"Top headline: <i>{headline}</i>\n"
        return msg

    def format_feed_stale_alert(self, feed_name: str, last_update: str) -> str:
        """Format a stale data feed alert."""
        return (
            f"[INFO] <b>Data Feed Stale</b>\n\n"
            f"<b>{feed_name}</b> last updated: {last_update}\n"
            f"<i>Data may be outdated.</i>"
        )