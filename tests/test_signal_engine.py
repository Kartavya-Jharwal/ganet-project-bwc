"""Tests for the Confidence-Filtered Signal Engine."""

from quant_monitor.agent.signal_engine import (
    ConfidenceFilteredSignalEngine,
    PerformanceLedger,
    SignalRecord,
)


class TestSignalRecord:
    def test_unresolved_record(self):
        r = SignalRecord("AAPL", "2026-01-01", "BUY", 0.8, 0.9, 0.08, "technical")
        assert not r.is_resolved
        assert r.realized_return is None

    def test_resolved_accurate(self):
        r = SignalRecord("AAPL", "2026-01-01", "BUY", 0.8, 0.9, 0.08, "technical")
        r.realized_return = 0.05
        assert r.is_resolved
        assert r.is_accurate  # both positive

    def test_resolved_inaccurate(self):
        r = SignalRecord("AAPL", "2026-01-01", "BUY", 0.8, 0.9, 0.08, "technical")
        r.realized_return = -0.03
        assert r.is_resolved
        assert not r.is_accurate  # expected positive, realized negative

    def test_hold_always_accurate(self):
        r = SignalRecord("AAPL", "2026-01-01", "HOLD", 0.1, 0.5, 0.0, "technical")
        r.realized_return = -0.05
        assert r.is_accurate

    def test_to_dict(self):
        r = SignalRecord("AAPL", "2026-01-01", "BUY", 0.8, 0.9, 0.08, "technical")
        d = r.to_dict()
        assert d["ticker"] == "AAPL"
        assert d["action"] == "BUY"
        assert d["is_accurate"] is None  # unresolved


class TestPerformanceLedger:
    def test_empty_ledger(self):
        ledger = PerformanceLedger()
        assert ledger.overall_accuracy() is None
        summary = ledger.performance_summary()
        assert summary["total_signals"] == 0

    def test_record_and_resolve(self):
        ledger = PerformanceLedger()
        r = SignalRecord("AAPL", "2026-01-01", "BUY", 0.8, 0.9, 0.08, "technical")
        ledger.record_signal(r)
        ledger.resolve_signal("AAPL", 0.05)
        assert r.realized_return == 0.05

    def test_ticker_accuracy_insufficient_history(self):
        ledger = PerformanceLedger()
        r = SignalRecord("AAPL", "2026-01-01", "BUY", 0.8, 0.9, 0.08, "technical")
        ledger.record_signal(r)
        ledger.resolve_signal("AAPL", 0.05)
        assert ledger.ticker_accuracy("AAPL") is None  # < 5 signals

    def test_ticker_accuracy_sufficient_history(self):
        ledger = PerformanceLedger()
        # 5 accurate signals
        for i in range(5):
            r = SignalRecord("AAPL", f"2026-01-0{i+1}", "BUY", 0.8, 0.9, 0.08, "technical")
            ledger.record_signal(r)
            ledger.resolve_signal("AAPL", 0.05)
        acc = ledger.ticker_accuracy("AAPL")
        assert acc is not None
        assert acc == 1.0  # all accurate

    def test_model_accuracy(self):
        ledger = PerformanceLedger()
        r1 = SignalRecord("AAPL", "2026-01-01", "BUY", 0.8, 0.9, 0.08, "technical")
        r2 = SignalRecord("TSLA", "2026-01-01", "SELL", -0.8, 0.9, -0.08, "fundamental")
        ledger.record_signal(r1)
        ledger.record_signal(r2)
        ledger.resolve_signal("AAPL", 0.05)  # accurate
        ledger.resolve_signal("TSLA", 0.03)  # inaccurate (expected negative, got positive)
        model_acc = ledger.model_accuracy()
        assert model_acc["technical"] == 1.0
        assert model_acc["fundamental"] == 0.0

    def test_performance_summary(self):
        ledger = PerformanceLedger()
        r = SignalRecord("AAPL", "2026-01-01", "BUY", 0.8, 0.9, 0.08, "technical")
        ledger.record_signal(r)
        ledger.resolve_signal("AAPL", 0.05)
        summary = ledger.performance_summary()
        assert summary["total_signals"] == 1
        assert summary["resolved_signals"] == 1
        assert summary["overall_accuracy"] == 1.0


class TestConfidenceFilteredSignalEngine:
    def test_high_confidence_passes(self):
        """High confidence + strong agreement → signal passes through."""
        engine = ConfidenceFilteredSignalEngine()
        result = engine.filter_signal(
            ticker="AAPL",
            technical=0.8,
            fundamental=0.7,
            sentiment=0.9,
            macro=0.6,
            regime="LOW_VOL_TREND",
        )
        assert not result["filtered"]
        assert result["action"] in ("BUY", "TRIM_UNDERWEIGHT")

    def test_low_confidence_filtered(self):
        """Low confidence → HOLD regardless of score."""
        engine = ConfidenceFilteredSignalEngine()
        result = engine.filter_signal(
            ticker="AAPL",
            technical=1.0,
            fundamental=-1.0,
            sentiment=0.8,
            macro=-0.8,
            regime="LOW_VOL_TREND",
        )
        assert result["action"] == "HOLD"

    def test_filter_all(self):
        """Batch filtering produces results for all tickers."""
        engine = ConfidenceFilteredSignalEngine()
        results = engine.filter_all(
            technical_scores={"AAPL": 0.8, "TSLA": -0.7},
            fundamental_scores={"AAPL": 0.7, "TSLA": -0.6},
            sentiment_scores={"AAPL": 0.9, "TSLA": -0.8},
            macro_score=0.5,
            regime="LOW_VOL_TREND",
        )
        assert "AAPL" in results
        assert "TSLA" in results

    def test_resolve_updates_ledger(self):
        """Resolving signals updates the performance ledger."""
        engine = ConfidenceFilteredSignalEngine()
        engine.filter_signal("AAPL", 0.8, 0.7, 0.9, 0.6, "LOW_VOL_TREND")
        engine.resolve_signals({"AAPL": 0.05})
        summary = engine.get_performance_report()
        assert summary["resolved_signals"] == 1

    def test_performance_report_structure(self):
        """Performance report includes expected fields."""
        engine = ConfidenceFilteredSignalEngine()
        report = engine.get_performance_report()
        assert "confidence_threshold" in report
        assert "accuracy_gate" in report
        assert "total_signals" in report

    def test_signal_history_dataframe(self):
        """Signal history returns a valid DataFrame."""
        engine = ConfidenceFilteredSignalEngine()
        engine.filter_signal("AAPL", 0.8, 0.7, 0.9, 0.6, "LOW_VOL_TREND")
        df = engine.get_signal_history()
        assert len(df) == 1
        assert "ticker" in df.columns

    def test_effective_threshold_increases_with_poor_accuracy(self):
        """Effective threshold should increase for tickers with poor accuracy."""
        engine = ConfidenceFilteredSignalEngine(accuracy_gate=0.70, penalty_factor=0.15)
        # Simulate 5 resolved signals, all inaccurate
        for i in range(5):
            engine.filter_signal("BAD", 0.8, 0.7, 0.9, 0.6, "LOW_VOL_TREND", f"t{i}")
            engine.resolve_signals({"BAD": -0.05})  # wrong direction for BUY
        threshold = engine._effective_threshold("BAD")
        # Should be higher than default 0.65
        assert threshold > engine._confidence_min

    def test_effective_threshold_unchanged_with_good_accuracy(self):
        """Good accuracy should not raise the threshold."""
        engine = ConfidenceFilteredSignalEngine()
        for i in range(5):
            engine.filter_signal("GOOD", 0.8, 0.7, 0.9, 0.6, "LOW_VOL_TREND", f"t{i}")
            engine.resolve_signals({"GOOD": 0.05})  # correct direction for BUY
        threshold = engine._effective_threshold("GOOD")
        assert threshold == engine._confidence_min
