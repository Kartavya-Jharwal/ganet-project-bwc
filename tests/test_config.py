"""Tests for config loading."""

from __future__ import annotations

from pathlib import Path


def test_config_toml_exists():
    """Verify config.toml is present and parseable."""
    import tomllib

    config_path = Path(__file__).parent.parent / "quant_monitor" / "config.toml"
    assert config_path.exists(), "config.toml not found"

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    assert "project" in data
    assert "holdings" in data
    assert len(data["holdings"]) == 15, f"Expected 15 holdings, got {len(data['holdings'])}"


def test_config_loader(mock_env):
    """Verify config.py loads TOML + env vars correctly."""
    from quant_monitor.config import load_config

    cfg = load_config()

    assert cfg.benchmark == "SPY"
    assert len(cfg.tickers) == 15
    assert cfg.initial_capital == 1_000_000
    assert cfg.secrets.ALPACA_API_KEY == "test_alpaca_key"
    assert "SPY" in cfg.holdings
    assert cfg.holdings["SPY"]["qty"] == 295


def test_all_holdings_have_required_fields():
    """Every holding must have name, type, qty, price_paid, sector."""
    import tomllib

    config_path = Path(__file__).parent.parent / "quant_monitor" / "config.toml"
    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    required = {"name", "type", "qty", "price_paid", "sector"}
    for ticker, holding in data["holdings"].items():
        missing = required - set(holding.keys())
        assert not missing, f"{ticker} missing fields: {missing}"
