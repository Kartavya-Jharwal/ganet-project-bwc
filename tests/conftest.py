"""Shared test fixtures — mock data, sample OHLCV, config overrides."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def sample_tickers():
    """Subset of portfolio tickers for fast tests."""
    return ["SPY", "TSM", "PLTR", "AMZN", "IONQ"]


@pytest.fixture
def config_path():
    """Path to the real config.toml for integration tests."""
    return Path(__file__).parent.parent / "quant_monitor" / "config.toml"


@pytest.fixture
def mock_env():
    """Mock environment variables (simulates Doppler injection)."""
    env_vars = {
        "ALPACA_API_KEY": "test_alpaca_key",
        "ALPACA_SECRET_KEY": "test_alpaca_secret",
        "FRED_API_KEY": "test_fred_key",
        "TELEGRAM_BOT_TOKEN": "test_telegram_token",
        "TELEGRAM_CHAT_ID": "test_chat_id",
        "APPWRITE_ENDPOINT": "https://cloud.appwrite.io/v1",
        "APPWRITE_PROJECT_ID": "test_project",
        "APPWRITE_API_KEY": "test_appwrite_key",
        "ZYTE_API_KEY": "test_zyte_key",
        "SEC_EDGAR_USER_AGENT": "TestBot/1.0",
    }
    with patch.dict("os.environ", env_vars):
        yield env_vars
