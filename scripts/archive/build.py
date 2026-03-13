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
    f.write(m10_1[0][0] + "\n\n")
    f.write("from __future__ import annotations\n")
    f.write("import logging\n")
    f.write("from enum import StrEnum\n")
    f.write("from datetime import datetime, timedelta, timezone\n")
    f.write("import asyncio\n")  # Might need asyncio if using async
    f.write("\nlogger = logging.getLogger(__name__)\n\n")
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
