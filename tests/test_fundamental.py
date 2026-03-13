"""Tests for fundamental model — Phase 5."""

from __future__ import annotations

import pandas as pd


class TestFundamentalModel:
    """Tests for quant_monitor/models/fundamental.py"""

    def test_score_cheap_stock(self):
        """Stock with P/E below sector median should get positive score."""
        from quant_monitor.models.fundamental import FundamentalModel

        model = FundamentalModel()
        fundamentals = {"pe_ratio": 12.0, "ps_ratio": 1.5, "ev_ebitda": 8.0, "earnings_revision": 0.05}
        sector_data = {"pe_median": 20.0, "ps_median": 3.0, "ev_ebitda_median": 12.0}
        score = model.score(fundamentals, sector_data)
        assert isinstance(score, float)
        assert score > 0, "Cheap stock should get positive score"
        assert -1.0 <= score <= 1.0

    def test_score_expensive_stock(self):
        """Stock with P/E above sector median should get negative score."""
        from quant_monitor.models.fundamental import FundamentalModel

        model = FundamentalModel()
        fundamentals = {"pe_ratio": 40.0, "ps_ratio": 8.0, "ev_ebitda": 25.0, "earnings_revision": -0.03}
        sector_data = {"pe_median": 20.0, "ps_median": 3.0, "ev_ebitda_median": 12.0}
        score = model.score(fundamentals, sector_data)
        assert score < 0, "Expensive stock should get negative score"

    def test_score_missing_data_returns_neutral(self):
        """Missing fundamental data should return neutral (0.0)."""
        from quant_monitor.models.fundamental import FundamentalModel

        model = FundamentalModel()
        score = model.score({}, {})
        assert score == 0.0

    def test_score_all_returns_dict(self):
        """score_all returns {ticker: float} for all tickers."""
        from quant_monitor.models.fundamental import FundamentalModel

        model = FundamentalModel()
        df = pd.DataFrame({
            "ticker": ["AAPL", "AAPL", "MSFT", "MSFT"],
            "pe_ratio": [25.0, 25.0, 30.0, 30.0],
            "ps_ratio": [6.0, 6.0, 10.0, 10.0],
            "ev_ebitda": [18.0, 18.0, 22.0, 22.0],
            "earnings_revision": [0.02, 0.02, -0.01, -0.01],
            "sector": ["Tech", "Tech", "Tech", "Tech"],
            "pe_median": [20.0, 20.0, 20.0, 20.0],
            "ps_median": [5.0, 5.0, 5.0, 5.0],
            "ev_ebitda_median": [15.0, 15.0, 15.0, 15.0],
        })
        result = model.score_all(df)
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert "MSFT" in result
        for v in result.values():
            assert -1.0 <= v <= 1.0

    def test_score_range_bounds(self):
        """Score must always be in [-1, 1] regardless of extreme inputs."""
        from quant_monitor.models.fundamental import FundamentalModel

        model = FundamentalModel()
        score_cheap = model.score(
            {"pe_ratio": 1.0, "ps_ratio": 0.1, "ev_ebitda": 1.0, "earnings_revision": 0.5},
            {"pe_median": 50.0, "ps_median": 20.0, "ev_ebitda_median": 30.0},
        )
        assert -1.0 <= score_cheap <= 1.0

        score_expensive = model.score(
            {"pe_ratio": 500.0, "ps_ratio": 100.0, "ev_ebitda": 200.0, "earnings_revision": -0.5},
            {"pe_median": 10.0, "ps_median": 2.0, "ev_ebitda_median": 5.0},
        )
        assert -1.0 <= score_expensive <= 1.0

    def test_sector_map_contains_all_tickers(self):
        """SECTOR_MAP must contain all 15 portfolio holdings."""
        from quant_monitor.models.fundamental import SECTOR_MAP

        expected = {"SPY", "TSM", "MU", "PLTR", "AMZN", "GOOGL", "GE", "JPM",
                    "LMT", "WMT", "XLP", "PG", "JNJ", "XLU", "IONQ"}
        assert expected.issubset(set(SECTOR_MAP.keys()))

    def test_sector_map_importable(self):
        """SECTOR_MAP and SECTOR_PEERS are importable."""
        from quant_monitor.models.fundamental import SECTOR_MAP, SECTOR_PEERS

        assert isinstance(SECTOR_MAP, dict)
        assert isinstance(SECTOR_PEERS, dict)
        assert len(SECTOR_MAP) >= 15
