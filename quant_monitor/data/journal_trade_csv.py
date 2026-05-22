"""Parse the course journal / Excel-style trade CSV into the unified trade-log schema.

Only rows with Action Open, Close, or Adjust are material; No Action rows are ignored
(no dividends, no journal snapshots). Duplicate glitch rows (#VALUE!, pasted blocks) are skipped.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

_JOURNAL_SIGNATURE = "Date (YYYY-MM-DD)"


def is_journal_trade_csv(path: Path) -> bool:
    """Heuristic: first line matches the journal export header."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            line = f.readline()
    except OSError:
        return False
    return _JOURNAL_SIGNATURE in line and "Open / Close / Adjust" in line


def _parse_money_cell(raw: str) -> float | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or "#VALUE!" in s.upper() or s.startswith("-----"):
        return None
    s = s.replace('"', "").replace("$", "").replace(",", "")
    s = re.sub(r"\s+", "", s)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _price_per_unit(raw: str) -> float:
    n = _parse_money_cell(raw)
    return float(n) if n is not None else 0.0


def _parse_row_date(cell: str) -> pd.Timestamp | None:
    s = (cell or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return pd.Timestamp(datetime.strptime(s, fmt))
        except ValueError:
            continue
    return None


def parse_journal_trade_csv(csv_path: Path) -> pd.DataFrame:
    """Return a DataFrame with columns matching ``PortfolioHistoryEngine.get_trade_log``."""
    records: list[dict] = []
    seen: set[tuple] = set()
    seq: dict[pd.Timestamp, int] = defaultdict(int)

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            next(reader)  # header
        except StopIteration:
            return pd.DataFrame()

        for raw_row in reader:
            if not raw_row or all(not (c or "").strip() for c in raw_row):
                continue
            row = list(raw_row)
            if len(row) > 13:
                row = [*row[:12], ",".join(row[12:])]
            while len(row) < 13:
                row.append("")

            date_ts = _parse_row_date(row[0])
            if date_ts is None:
                continue

            act = (row[1] or "").strip()
            sym = (row[2] or "").strip().upper()
            if not sym or sym == "-----" or "EMEREGENCY" in (row[3] or "").upper():
                continue

            try:
                qty = int(float(str(row[5]).strip().replace(",", "")))
            except ValueError:
                continue

            price = _price_per_unit(row[6])
            gross = _parse_money_cell(row[8])
            net_abs = _parse_money_cell(row[10])
            if net_abs is None:
                continue

            net_abs = abs(float(net_abs))
            if act == "No Action":
                continue

            if "#VALUE!" in str(raw_row):
                continue

            if act == "Open":
                engine_action = "BUY"
                amount = -net_abs
            elif act == "Close":
                engine_action = "SELL"
                amount = net_abs
            elif act == "Adjust":
                if gross is not None and gross < 0:
                    engine_action = "SELL"
                    amount = net_abs
                elif gross is not None and gross > 0:
                    engine_action = "BUY"
                    amount = -net_abs
                elif gross is not None and gross == 0:
                    continue
                else:
                    continue
            else:
                continue

            seq[date_ts.normalize()] += 1
            n = seq[date_ts.normalize()]
            dt = date_ts + pd.Timedelta(minutes=min(n, 1439))

            dedupe_key = (dt.normalize(), sym, engine_action, qty, round(price, 6), round(amount, 2))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            records.append(
                {
                    "date": dt.normalize(),
                    "datetime": dt,
                    "symbol": sym,
                    "action": engine_action,
                    "qty": abs(qty),
                    "price": price,
                    "amount": amount,
                }
            )

    df = pd.DataFrame(records)
    if df.empty:
        return df
    return df.sort_values("datetime").reset_index(drop=True)
