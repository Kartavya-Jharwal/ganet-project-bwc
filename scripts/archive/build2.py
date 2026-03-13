import re

with open("task_phases_6_10.md", encoding="utf-8") as f:
    text = f.read()

m10_1 = re.findall(r"### Task 10.1.*?```python\n(.*?)```.*?```python\n(.*?)```", text, re.DOTALL)
m10_2 = re.findall(r"### Task 10.2.*?```python\n(.*?)```", text, re.DOTALL)
m10_3 = re.findall(
    r"### Task 10.3.*?```python\n(.*?)```.*?```python\n(.*?)```.*?```python\n(.*?)```",
    text,
    re.DOTALL,
)
m10_4 = re.findall(r"### Task 10.4.*?```python\n(.*?)```", text, re.DOTALL)
m10_5 = re.findall(r"### Task 10.5.*?```python\n(.*?)```", text, re.DOTALL)

with open("quant_monitor/agent/alerts.py", "w", encoding="utf-8") as f:
    f.write(
        '"""Multi-channel alert dispatcher (Telegram + ntfy).\n\nAlert types and priorities:\n| Alert             | Trigger                              | Priority |\n|-------------------|--------------------------------------|----------|\n| REBALANCE         | Position drift >2% + confidence >0.65| High     |\n| RISK_BREACH       | Position >10% or sector >25%         | Critical |\n| MACRO_SHIFT       | Regime change detected               | High     |\n| KILL_SWITCH       | Position down >15% intraday          | Critical |\n| EARNINGS_UPCOMING | Earnings within 3 trading days       | Medium   |\n| SENTIMENT_SPIKE   | Rapid negative sentiment shift       | Medium   |\n| FEED_STALE        | Data source stale >30 min            | Low      |\n\nChannels:\n- Telegram Bot API — rich HTML-formatted messages\n- ntfy.sh — simple HTTP-based pub-sub (push to UUID topic, no auth needed)\n  Subscribe: ntfy.sh/<NTFY_TOPIC> or via ntfy mobile/desktop app\n"""\n\n'
    )
    f.write(
        "from __future__ import annotations\n\nimport logging\nimport re\nfrom enum import StrEnum\nfrom datetime import datetime, timedelta, timezone\nimport httpx\nfrom telegram import Bot\n\n"
    )
    f.write("logger = logging.getLogger(__name__)\n\n")
    f.write(
        'class AlertPriority(StrEnum):\n    LOW = "LOW"\n    MEDIUM = "MEDIUM"\n    HIGH = "HIGH"\n    CRITICAL = "CRITICAL"\n\n'
    )
    f.write(
        'class AlertType(StrEnum):\n    REBALANCE = "REBALANCE"\n    RISK_BREACH = "RISK_BREACH"\n    MACRO_SHIFT = "MACRO_SHIFT"\n    KILL_SWITCH = "KILL_SWITCH"\n    EARNINGS_UPCOMING = "EARNINGS_UPCOMING"\n    SENTIMENT_SPIKE = "SENTIMENT_SPIKE"\n    FEED_STALE = "FEED_STALE"\n\n'
    )
    f.write("class AlertDispatcher:\n")
    f.write('    """Sends formatted alerts to Telegram and ntfy."""\n\n')

    f.write("    " + m10_1[0][1].replace("\n", "\n    ") + "\n\n")
    f.write("    " + m10_2[0].replace("\n", "\n    ") + "\n\n")

    f.write("    " + m10_3[0][0].replace("\n", "\n    ") + "\n\n")
    f.write("    " + m10_3[0][1].replace("\n", "\n    ") + "\n\n")
    f.write("    " + m10_3[0][2].replace("\n", "\n    ") + "\n\n")

    f.write("    " + m10_4[0].replace("\n", "\n    ") + "\n\n")
    f.write("    " + m10_5[0].replace("\n", "\n    ") + "\n\n")
