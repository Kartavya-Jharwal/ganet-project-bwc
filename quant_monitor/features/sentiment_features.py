"""Sentiment feature engineering — FinBERT scoring, sentiment MAs.

Processes news headlines through FinBERT, computes:
- Raw sentiment scores per headline per ticker
- Sentiment MA: 3h, 24h, 72h
- Sentiment momentum: 3h_sentiment - 72h_sentiment
- Entity extraction for held tickers
- SEC 8-K classification
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class SentimentFeatureEngine:
    """Compute sentiment features from news text using FinBERT."""

    def __init__(self) -> None:
        """Lazy-load FinBERT model and tokenizer to save memory."""
        self._model = None
        self._tokenizer = None
        self._sentence_model = None

    def _ensure_model_loaded(self) -> None:
        """Load FinBERT on first use."""
        if self._model is None:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            from quant_monitor.config import cfg

            model_name = cfg.sentiment.get("finbert_model", "ProsusAI/finbert")
            logger.info("Loading FinBERT model: %s", model_name)
            self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self._model.eval()
            logger.info("FinBERT model loaded successfully")

    def _ensure_sentence_model_loaded(self) -> None:
        """Load sentence-transformers for deduplication on first use."""
        if self._sentence_model is None:
            from sentence_transformers import SentenceTransformer

            self._sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Sentence transformer loaded for deduplication")

    def score_headlines(self, headlines: list[str]) -> list[dict]:
        """Score a batch of headlines through FinBERT.

        Returns list of {text, positive, negative, neutral, label, score}.
        """
        import torch

        self._ensure_model_loaded()

        results = []
        batch_size = 16

        # Resolve label indices from model config (not hardcoded - avoids wrong order)
        id2label = {k: v.lower() for k, v in self._model.config.id2label.items()}
        label2idx = {v: k for k, v in id2label.items()}
        pos_idx = label2idx.get("positive", 0)
        neg_idx = label2idx.get("negative", 1)

        for i in range(0, len(headlines), batch_size):
            batch = headlines[i : i + batch_size]
            inputs = self._tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            with torch.no_grad():
                outputs = self._model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

            for j, text in enumerate(batch):
                prob_list = probs[j].tolist()
                argmax_idx = probs[j].argmax().item()
                label = id2label[argmax_idx]
                p_pos = prob_list[pos_idx]
                p_neg = prob_list[neg_idx]
                score = p_pos - p_neg  # range [-1, +1]
                results.append(
                    {
                        "text": text,
                        "positive": round(p_pos, 4),
                        "negative": round(p_neg, 4),
                        "neutral": round(prob_list[3 - pos_idx - neg_idx], 4),
                        "label": label,
                        "score": round(score, 4),
                    }
                )
        return results

    def compute_sentiment_ma(
        self, scored_df: pd.DataFrame, windows: list[int] | None = None
    ) -> pd.DataFrame:
        """Compute rolling sentiment MAs over time windows (in hours)."""
        from quant_monitor.config import cfg

        if windows is None:
            windows = cfg.sentiment.get("sentiment_ma_windows", [3, 24, 72])

        result = scored_df.copy()
        for w in windows:
            col_name = f"ma_{w}h"
            result[col_name] = result["score"].rolling(window=w, min_periods=1).mean()
        return result

    def sentiment_momentum(self, scored_df: pd.DataFrame) -> pd.Series:
        """3h sentiment - 72h sentiment. Rapid negative shift = review trigger."""
        from quant_monitor.config import cfg

        windows = cfg.sentiment.get("sentiment_ma_windows", [3, 24, 72])
        short_window = windows[0]   # 3 hours
        long_window = windows[-1]   # 72 hours

        short_ma = scored_df["score"].rolling(window=short_window, min_periods=1).mean()
        long_ma = scored_df["score"].rolling(window=long_window, min_periods=1).mean()
        return (short_ma - long_ma).rename("sentiment_momentum")

    def deduplicate_news(
        self, headlines: list[str], threshold: float = 0.85
    ) -> list[str]:
        """Deduplicate headlines via cosine similarity (sentence-transformers)."""
        if len(headlines) <= 1:
            return headlines

        self._ensure_sentence_model_loaded()

        embeddings = self._sentence_model.encode(headlines, convert_to_numpy=True)

        # Normalize for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # avoid div by zero
        normalized = embeddings / norms

        # Greedy deduplication: keep first, skip similar ones
        keep = [0]
        for i in range(1, len(headlines)):
            similarities = normalized[i] @ normalized[keep].T
            if np.atleast_1d(similarities).max() < threshold:
                keep.append(i)

        return [headlines[i] for i in keep]
