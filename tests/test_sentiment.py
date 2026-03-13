"""Tests for sentiment features and model — Phase 4."""

from __future__ import annotations

import numpy as np
import pandas as pd


class TestSentimentFeatureEngine:
    """Tests for quant_monitor/features/sentiment_features.py"""

    def test_score_headlines_returns_list_of_dicts(self):
        """score_headlines must return list of dicts with required keys."""
        from quant_monitor.features.sentiment_features import SentimentFeatureEngine

        engine = SentimentFeatureEngine()
        headlines = [
            "Apple reports record quarterly earnings beating estimates",
            "Markets crash as recession fears mount globally",
            "Federal Reserve holds interest rates steady",
        ]
        results = engine.score_headlines(headlines)
        assert isinstance(results, list)
        assert len(results) == 3
        for item in results:
            assert "text" in item
            assert "label" in item
            assert "score" in item
            assert item["label"] in ("positive", "negative", "neutral")
            assert -1.0 <= item["score"] <= 1.0

    def test_positive_headline_scored_positive(self):
        """Clearly positive headline should get positive score."""
        from quant_monitor.features.sentiment_features import SentimentFeatureEngine

        engine = SentimentFeatureEngine()
        # FinBERT is trained on formal financial news — use financial phrasing
        results = engine.score_headlines(
            ["The quarterly results beat analyst expectations, revenue up 30 percent year over year"]
        )
        assert results[0]["label"] == "positive" or results[0]["score"] > 0

    def test_negative_headline_scored_negative(self):
        """Clearly negative headline should get negative score."""
        from quant_monitor.features.sentiment_features import SentimentFeatureEngine

        engine = SentimentFeatureEngine()
        results = engine.score_headlines(
            ["Revenue fell sharply as demand collapsed and margins compressed significantly"]
        )
        assert results[0]["label"] == "negative" or results[0]["score"] < 0

    def test_deduplicate_news_removes_similar(self):
        """Deduplicate should remove near-duplicate headlines."""
        from quant_monitor.features.sentiment_features import SentimentFeatureEngine

        engine = SentimentFeatureEngine()
        headlines = [
            "Apple beats quarterly earnings expectations",
            "Apple Q4 earnings beat analyst expectations",  # near-duplicate
            "Federal Reserve raises interest rates by 25 basis points",
        ]
        unique = engine.deduplicate_news(headlines, threshold=0.70)
        assert len(unique) < len(headlines), "Should remove at least one duplicate"
        assert len(unique) >= 2, "Should keep at least 2 distinct headlines"

    def test_sentiment_momentum(self):
        """Sentiment momentum = short-term MA minus long-term MA."""
        from quant_monitor.features.sentiment_features import SentimentFeatureEngine

        engine = SentimentFeatureEngine()
        # Create a DataFrame with scores that shift from positive to negative
        n = 100
        timestamps = pd.date_range("2026-01-01", periods=n, freq="h")
        scores = np.concatenate([np.full(70, 0.5), np.full(30, -0.5)])  # shift at index 70
        scored_df = pd.DataFrame({"timestamp": timestamps, "score": scores}).set_index("timestamp")

        momentum = engine.sentiment_momentum(scored_df)
        # At the end, short-term MA should be more negative than long-term → negative momentum
        assert momentum.iloc[-1] < 0, "Momentum should be negative after sentiment drops"


class TestSentimentModel:
    """Tests for quant_monitor/models/sentiment.py"""

    def test_score_returns_float_in_range(self):
        """score() must return float in [-1.0, +1.0]."""
        from quant_monitor.models.sentiment import SentimentModel

        model = SentimentModel()
        features = pd.DataFrame({
            "score": [0.8, 0.6, -0.3, 0.2, -0.1],
            "momentum": [0.1, 0.05, -0.2, 0.0, -0.05],
            "ma_3h": [0.7, 0.65, -0.1, 0.3, 0.0],
            "ma_24h": [0.5, 0.4, 0.1, 0.2, 0.1],
            "ma_72h": [0.3, 0.3, 0.2, 0.15, 0.15],
        })
        score = model.score(features)
        assert isinstance(score, float)
        assert -1.0 <= score <= 1.0

    def test_score_all_returns_dict(self):
        """score_all() returns {ticker: float}."""
        from quant_monitor.models.sentiment import SentimentModel

        model = SentimentModel()
        sentiment_df = pd.DataFrame({
            "ticker": ["AAPL", "AAPL", "MSFT", "MSFT"],
            "score": [0.5, 0.3, -0.2, -0.4],
            "momentum": [0.1, 0.05, -0.1, -0.15],
            "ma_3h": [0.4, 0.35, -0.15, -0.3],
            "ma_24h": [0.3, 0.25, -0.1, -0.2],
            "ma_72h": [0.2, 0.2, 0.0, -0.05],
        })
        result = model.score_all(sentiment_df)
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert "MSFT" in result
        for v in result.values():
            assert -1.0 <= v <= 1.0
