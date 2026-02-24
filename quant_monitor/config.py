"""Configuration loader — merges TOML config with Doppler-injected env vars.

Usage:
    from quant_monitor.config import cfg

    # Static config from TOML
    tickers = list(cfg.holdings.keys())
    benchmark = cfg.project["benchmark"]

    # Secrets from Doppler (via os.environ)
    alpaca_key = cfg.secrets.ALPACA_API_KEY
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).parent / "config.toml"


@dataclass(frozen=True)
class Secrets:
    """Secrets injected by Doppler via environment variables.

    Access as cfg.secrets.ALPACA_API_KEY etc.
    Returns empty string if not set (allows dry-run without Doppler).
    """

    ALPACA_API_KEY: str = ""
    ALPACA_SECRET_KEY: str = ""
    FRED_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    APPWRITE_ENDPOINT: str = ""
    APPWRITE_PROJECT_ID: str = ""
    APPWRITE_API_KEY: str = ""
    ZYTE_API_KEY: str = ""
    SEC_EDGAR_USER_AGENT: str = ""

    @classmethod
    def from_env(cls) -> Secrets:
        """Load secrets from environment (Doppler injects these)."""
        return cls(
            **{f.name: os.environ.get(f.name, f.default) for f in cls.__dataclass_fields__.values()}
        )


@dataclass
class Config:
    """Unified configuration object combining TOML + environment secrets."""

    # Raw TOML sections
    project: dict[str, Any] = field(default_factory=dict)
    holdings: dict[str, dict[str, Any]] = field(default_factory=dict)
    cache_ttl: dict[str, int] = field(default_factory=dict)
    regime_weights: dict[str, dict[str, float]] = field(default_factory=dict)
    risk_params: dict[str, dict[str, float]] = field(default_factory=dict)
    signal_thresholds: dict[str, float] = field(default_factory=dict)
    moving_averages: dict[str, int] = field(default_factory=dict)
    volatility: dict[str, Any] = field(default_factory=dict)
    sentiment: dict[str, Any] = field(default_factory=dict)
    macro_thresholds: dict[str, float] = field(default_factory=dict)
    appwrite: dict[str, Any] = field(default_factory=dict)
    scrapy_cloud: dict[str, Any] = field(default_factory=dict)
    alerts: dict[str, Any] = field(default_factory=dict)

    # Doppler secrets
    secrets: Secrets = field(default_factory=Secrets)

    @property
    def tickers(self) -> list[str]:
        """All portfolio ticker symbols."""
        return list(self.holdings.keys())

    @property
    def initial_capital(self) -> float:
        return float(self.project.get("initial_capital", 1_000_000))

    @property
    def benchmark(self) -> str:
        return self.project.get("benchmark", "SPY")

    @property
    def valuation_date(self) -> str:
        return self.project.get("valuation_date", "2026-04-10")

    @property
    def sunset_date(self) -> str:
        return self.project.get("sunset_date", "2026-05-01")


def load_config(config_path: Path = CONFIG_PATH) -> Config:
    """Load configuration from TOML file and environment."""
    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    return Config(
        project=raw.get("project", {}),
        holdings=raw.get("holdings", {}),
        cache_ttl=raw.get("cache_ttl", {}),
        regime_weights=raw.get("regime_weights", {}),
        risk_params=raw.get("risk_params", {}),
        signal_thresholds=raw.get("signal_thresholds", {}),
        moving_averages=raw.get("moving_averages", {}),
        volatility=raw.get("volatility", {}),
        sentiment=raw.get("sentiment", {}),
        macro_thresholds=raw.get("macro_thresholds", {}),
        appwrite=raw.get("appwrite", {}),
        scrapy_cloud=raw.get("scrapy_cloud", {}),
        alerts=raw.get("alerts", {}),
        secrets=Secrets.from_env(),
    )


# Singleton — import this everywhere
cfg = load_config()
