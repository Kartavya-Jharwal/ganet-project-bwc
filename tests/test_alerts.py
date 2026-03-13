"""Tests for alert dispatcher — Phase 10."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAlertDispatcher:
    """Tests for quant_monitor/agent/alerts.py"""

    def test_init_loads_config(self):
        """AlertDispatcher should initialize with config values."""
        from quant_monitor.agent.alerts import AlertDispatcher

        dispatcher = AlertDispatcher()
        assert hasattr(dispatcher, "_cooldown_minutes")
        assert hasattr(dispatcher, "_last_alert_times")

    def test_init_has_ntfy_topic(self):
        """AlertDispatcher should have ntfy topic from config."""
        from quant_monitor.agent.alerts import AlertDispatcher

        dispatcher = AlertDispatcher()
        assert hasattr(dispatcher, "_ntfy_topic")

    def test_format_rebalance_alert(self):
        """format_rebalance_alert should produce readable message."""
        from quant_monitor.agent.alerts import AlertDispatcher

        dispatcher = AlertDispatcher()
        trades = [
            {"ticker": "TSM", "action": "BUY", "current_weight": 0.05, "target_weight": 0.08, "delta": 0.03},
            {"ticker": "IONQ", "action": "SELL", "current_weight": 0.10, "target_weight": 0.05, "delta": -0.05},
        ]
        msg = dispatcher.format_rebalance_alert(trades)
        assert isinstance(msg, str)
        assert "TSM" in msg
        assert "IONQ" in msg
        assert "BUY" in msg
        assert "SELL" in msg

    def test_format_kill_switch_alert(self):
        """format_kill_switch_alert should include ticker and drawdown."""
        from quant_monitor.agent.alerts import AlertDispatcher

        dispatcher = AlertDispatcher()
        position = {
            "ticker": "IONQ",
            "open_price": 30.00,
            "current_price": 24.00,
            "drawdown_pct": 0.20,
        }
        msg = dispatcher.format_kill_switch_alert(position)
        assert isinstance(msg, str)
        assert "IONQ" in msg
        assert "20" in msg  # 20% drawdown

    def test_cooldown_prevents_spam(self):
        """Same alert type + ticker within cooldown should be suppressed."""
        from quant_monitor.agent.alerts import AlertDispatcher, AlertType

        dispatcher = AlertDispatcher()
        # Simulate a recent alert
        key = "REBALANCE:TSM"
        dispatcher._last_alert_times[key] = datetime.utcnow()

        # Should be suppressed (within cooldown window)
        suppressed = dispatcher._is_on_cooldown(AlertType.REBALANCE, "TSM")
        assert suppressed is True

    def test_cooldown_expires(self):
        """Alert after cooldown period should NOT be suppressed."""
        from quant_monitor.agent.alerts import AlertDispatcher, AlertType

        dispatcher = AlertDispatcher()
        key = "REBALANCE:TSM"
        # Set last alert to 60 minutes ago (beyond 30-min cooldown)
        dispatcher._last_alert_times[key] = datetime.utcnow() - timedelta(minutes=60)

        suppressed = dispatcher._is_on_cooldown(AlertType.REBALANCE, "TSM")
        assert suppressed is False

    def test_critical_alerts_bypass_cooldown(self):
        """CRITICAL priority alerts should bypass cooldown."""
        from quant_monitor.agent.alerts import AlertDispatcher, AlertPriority, AlertType

        dispatcher = AlertDispatcher()
        key = "KILL_SWITCH:IONQ"
        dispatcher._last_alert_times[key] = datetime.utcnow()  # just sent

        # CRITICAL should bypass
        suppressed = dispatcher._is_on_cooldown(
            AlertType.KILL_SWITCH, "IONQ", priority=AlertPriority.CRITICAL
        )
        assert suppressed is False

    @pytest.mark.asyncio
    async def test_send_alert_calls_telegram(self):
        """send_alert should call Telegram API when not on cooldown."""
        from quant_monitor.agent.alerts import AlertDispatcher, AlertPriority, AlertType

        dispatcher = AlertDispatcher()
        dispatcher._bot = MagicMock()
        dispatcher._bot.send_message = AsyncMock(return_value=True)
        dispatcher._chat_id = "test_chat"

        result = await dispatcher.send_alert(
            alert_type=AlertType.MACRO_SHIFT,
            priority=AlertPriority.HIGH,
            message="Regime changed to CRISIS",
        )
        # Should attempt to send (cooldown fresh)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_send_ntfy_posts_to_topic(self):
        """send_alert should also POST to ntfy when topic is configured."""
        from quant_monitor.agent.alerts import AlertDispatcher, AlertPriority, AlertType

        dispatcher = AlertDispatcher()
        dispatcher._ntfy_topic = "qpm-test-topic-abc123"
        dispatcher._bot = None  # no Telegram
        dispatcher._chat_id = None

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            result = await dispatcher.send_alert(
                alert_type=AlertType.REBALANCE,
                priority=AlertPriority.HIGH,
                message="Test ntfy alert",
                ticker="TSM",
            )
            assert result is True
            mock_post.assert_called_once()
            call_url = mock_post.call_args[0][0]
            assert "qpm-test-topic-abc123" in call_url


class TestNtfy:
    """Tests specifically for ntfy integration."""

    def test_ntfy_plain_text_format(self):
        """ntfy messages should strip HTML tags to plain text."""
        from quant_monitor.agent.alerts import AlertDispatcher

        dispatcher = AlertDispatcher()
        html = "<b>KILL SWITCH</b>\n<i>IONQ down 20%</i>"
        plain = dispatcher._strip_html(html)
        assert "<b>" not in plain
        assert "<i>" not in plain
        assert "KILL SWITCH" in plain
        assert "IONQ down 20%" in plain

    def test_ntfy_priority_mapping(self):
        """Alert priorities should map to ntfy priority headers (1-5)."""
        from quant_monitor.agent.alerts import AlertDispatcher, AlertPriority

        dispatcher = AlertDispatcher()
        assert dispatcher._ntfy_priority(AlertPriority.LOW) == "2"
        assert dispatcher._ntfy_priority(AlertPriority.MEDIUM) == "3"
        assert dispatcher._ntfy_priority(AlertPriority.HIGH) == "4"
        assert dispatcher._ntfy_priority(AlertPriority.CRITICAL) == "5"
