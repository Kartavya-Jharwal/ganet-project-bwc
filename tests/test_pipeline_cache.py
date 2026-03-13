"""Unit tests for DataPipeline cache correctness."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import patch


class _FakeCache:
    def __init__(self) -> None:
        self.store: dict[str, object] = {}
        self.set_calls: list[tuple[str, object, int | None]] = []

    def get(self, key: str):
        return self.store.get(key)

    def set(self, key: str, value: object, ttl: int | None = None) -> None:
        self.store[key] = value
        self.set_calls.append((key, value, ttl))


class _FakeMassive:
    def __init__(self) -> None:
        self.is_available = True
        self.calls: list[tuple[tuple[str, ...], tuple[int, ...], tuple[int, ...]]] = []

    def get_ma_matrix(self, tickers: list[str], sma_periods: list[int], ema_periods: list[int]):
        self.calls.append((tuple(tickers), tuple(sma_periods), tuple(ema_periods)))
        ticker = tickers[0]
        return {
            ticker: {
                "sma": {p: float(p) for p in sma_periods},
                "ema": {p: float(p) for p in ema_periods},
            }
        }


class _FakeFred:
    def __init__(self, payload: dict[str, float | None]) -> None:
        self.payload = payload

    def get_macro_snapshot(self) -> dict[str, float | None]:
        return self.payload


def _build_pipeline_for_test():
    from quant_monitor.data.pipeline import DataPipeline

    with patch("quant_monitor.data.pipeline.create_appwrite_client", return_value=object()):
        return DataPipeline()


def test_ma_cache_key_includes_periods():
    pipeline = _build_pipeline_for_test()
    fake_cache = _FakeCache()
    cast(Any, pipeline)._cache = fake_cache
    cast(Any, pipeline)._massive = _FakeMassive()

    pipeline.fetch_moving_averages(["SPY"], sma_periods=[5, 10], ema_periods=[12], use_cache=True)
    pipeline.fetch_moving_averages(["SPY"], sma_periods=[50, 200], ema_periods=[26], use_cache=True)

    keys = [call[0] for call in fake_cache.set_calls]
    assert len(keys) == 2
    assert keys[0] != keys[1]
    assert "sma[5,10]" in keys[0]
    assert "sma[50,200]" in keys[1]


def test_macro_all_none_snapshot_is_not_cached():
    pipeline = _build_pipeline_for_test()
    fake_cache = _FakeCache()
    cast(Any, pipeline)._cache = fake_cache
    cast(Any, pipeline)._fred = _FakeFred(
        {
            "vix": None,
            "dxy": None,
            "yield_10y": None,
            "yield_2y": None,
            "yield_10y_2y_spread": None,
        }
    )

    macro = pipeline.fetch_macro(use_cache=True)
    assert macro["vix"] is None
    assert fake_cache.set_calls == []


def test_macro_numeric_snapshot_is_cached():
    pipeline = _build_pipeline_for_test()
    fake_cache = _FakeCache()
    cast(Any, pipeline)._cache = fake_cache
    cast(Any, pipeline)._fred = _FakeFred(
        {
            "vix": 21.3,
            "dxy": 104.2,
            "yield_10y": 4.11,
            "yield_2y": 4.40,
            "yield_10y_2y_spread": -0.29,
        }
    )

    _ = pipeline.fetch_macro(use_cache=True)
    assert len(fake_cache.set_calls) == 1
    key, _, _ = cast(tuple[str, object, int | None], fake_cache.set_calls[0])
    assert key == "macro_snapshot"
