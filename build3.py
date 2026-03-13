with open('quant_monitor/agent/alerts.py', encoding='utf-8') as f:
    lines = f.readlines()
# insert init after line 48
init_lines = [
    '    def __init__(self) -> None:\n',
    '        from quant_monitor.config import cfg\n',
    '        self._last_alert_times: dict[str, datetime] = {}\n',
    '        self._cooldown_minutes = cfg.project.get("alert_cooldown_minutes", 60)\n',
    '        self._telegram_token = cfg.secrets.TELEGRAM_BOT_TOKEN\n',
    '        self._telegram_chat_id = cfg.secrets.TELEGRAM_CHAT_ID\n',
    '        if self._telegram_token:\n',
    '            from telegram import Bot\n',
    '            self._bot = Bot(token=self._telegram_token)\n',
    '        else:\n',
    '            self._bot = None\n',
    '        self._ntfy_topic = getattr(cfg.secrets, "NTFY_TOPIC", None)\n',
    '        if not self._ntfy_topic:\n',
    '            logger.warning("NTFY_TOPIC secret not found. ntfy alerts disabled.")\n'
]
del lines[50:52] 
lines = lines[:50] + init_lines + lines[50:]
with open('quant_monitor/agent/alerts.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)