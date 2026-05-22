"""Regression tests for the discretionary journal CSV loader."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
JOURNAL = REPO / "tests" / "test_data" / "journal_transaction_history.csv"


@pytest.mark.skipif(not JOURNAL.is_file(), reason="journal file not present")
def test_journal_parser_produces_buys_and_sells():
    from quant_monitor.data.journal_trade_csv import is_journal_trade_csv, parse_journal_trade_csv

    assert is_journal_trade_csv(JOURNAL)
    df = parse_journal_trade_csv(JOURNAL)
    assert not df.empty
    assert set(df["action"].unique()) <= {"BUY", "SELL"}
    xlu_add = df[(df["symbol"] == "XLU") & (df["date"] == "2026-04-08") & (df["action"] == "BUY")]
    assert len(xlu_add) == 1
    assert int(xlu_add.iloc[0]["qty"]) == 400
