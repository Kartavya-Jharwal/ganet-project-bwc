$env:PYTHONDONTWRITEBYTECODE="1"
function project { doppler run -- uv run python quant_monitor/cli.py @args }
