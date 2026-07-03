"""Extract excel metrics and report excerpts for the one-page microsite."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
FRONTEND = ROOT / "frontend"
DATA_DIR = FRONTEND / "data"
_EXCEL_FILES = FRONTEND / "deliverables/source/BWC_Excel_model_files"
SHEET005 = _EXCEL_FILES / "sheet005.htm"
SHEET008 = _EXCEL_FILES / "sheet008.htm"
SHEET009 = _EXCEL_FILES / "sheet009.htm"
SHEET011 = _EXCEL_FILES / "sheet011.htm"
SHEET013 = _EXCEL_FILES / "sheet013.htm"
REPORT_HTM = FRONTEND / "deliverables/source/Investment-CHL-Team-5-BWC-1 (1).htm"

_INITIAL_CAPITAL = 1_000_000.0

# Simulation phases (Hult desk narrative)
_DESK_PHASES = [
    {"id": "ph1", "label": "Ph 1 Foundation", "start": "2026-02-02", "end": "2026-02-25"},
    {"id": "ph2", "label": "Ph 2 Growth Pivot", "start": "2026-02-25", "end": "2026-03-23"},
    {"id": "ph3", "label": "Ph 3 Crisis", "start": "2026-03-23", "end": "2026-04-02"},
    {"id": "ph4", "label": "Ph 4 Ceasefire", "start": "2026-04-02", "end": "2026-04-11"},
]

_ADVANCED_RATIO_SPECS = [
    ("Sharpe Ratio", "sharpe", "RISK_ADJ"),
    ("Sortino Ratio", "sortino", "RISK_ADJ"),
    ("Calmar Ratio", "calmar", "RISK_ADJ"),
    ("Omega Ratio", "omega", "RISK_ADJ"),
    ("Information Ratio", "information_ratio", "RISK_ADJ"),
    ("Treynor Ratio", "treynor", "RISK_ADJ"),
    ("M² (Modigliani)", "m2", "RISK_ADJ"),
    ("Jensen's Alpha", "jensen_alpha", "RISK_ADJ"),
    ("Beta", "beta", "RISK_ADJ"),
    ("Profit Factor", "profit_factor", "TRADES"),
    ("Win Rate", "win_rate", "TRADES"),
    ("Avg Win ($)", "avg_win", "TRADES"),
    ("Avg Loss ($)", "avg_loss", "TRADES"),
    ("Expectancy ($)", "expectancy", "TRADES"),
]


def parse_sheet009_annualized() -> dict[str, str]:
    """Annualised desk return from GAIN ANALYSIS (sheet009)."""
    text = SHEET009.read_text(encoding="windows-1252", errors="replace")
    out: dict[str, str] = {}
    m = re.search(
        r"Annualised\s+Return \(68-day sim\)</td>\s*<td[^>]*>([^<]+)</td>",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        out["annualized_return"] = m.group(1).strip()
    m_bmk = re.search(
        r"Benchmark\s+Annualised \(SPX\)</td>\s*<td[^>]*>([^<]+)</td>",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if m_bmk:
        out["benchmark_annualized_return"] = m_bmk.group(1).strip()
    return out


def parse_excel_metrics() -> dict:
    text = SHEET005.read_text(encoding="windows-1252", errors="replace")
    metrics: dict[str, str] = {}

    patterns = [
        r"class=xl467>([^<]+)</td>\s*<td[^>]*></td>\s*<td[^>]*></td>\s*<td[^>]*></td>\s*<td[^>]*></td>\s*<td colspan=4 class=xl47\d>([^<]+)</td>",
        r"class=xl467>([^<]+)</td>\s*<td colspan=4 class=xl47\d>([^<]+)</td>",
        r"class=xl479>([^<]+)</td>\s*<td[^>]*></td>\s*<td colspan=3 class=xl48\d>([^<]+)</td>",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text):
            label = re.sub(r"&amp;", "&", m.group(1)).strip()
            val = m.group(2).strip()
            if label and val:
                metrics[label] = val

    gain_analysis = parse_sheet009_annualized()
    if gain_analysis.get("annualized_return"):
        metrics["Annualised Return (68-day sim)"] = gain_analysis["annualized_return"]

    key_specs = [
        ("Initial Capital", "initial_capital", "CAPITAL"),
        ("Final Portfolio Value", "final_value", "CAPITAL"),
        ("Portfolio Total Return", "total_return", "RETURNS"),
        ("Annualised Return (68-day sim)", "annualized_return", "RETURNS"),
        ("Benchmark Return (S&P 500)", "benchmark_return", "RETURNS"),
        ("Excess Return vs Benchmark", "excess_return", "RETURNS"),
        ("P&L Dollar Amount", "pnl", "RETURNS"),
        ("Sharpe Ratio", "sharpe", "RISK"),
        ("Portfolio Beta", "beta", "RISK"),
        ("Jensen's Alpha", "jensen_alpha", "RISK"),
        ("Total Trades Executed", "trades_executed", "ACTIVITY"),
        ("Trades Remaining (Capacity)", "trades_remaining", "ACTIVITY"),
        ("Cash Balance", "cash", "CAPITAL"),
        ("Total Dividends Received", "dividends", "INCOME"),
        ("Total Commissions Paid", "commissions", "INCOME"),
        ("Buying Power", "buying_power", "CAPITAL"),
        ("Net Income (Cash Flows)", "net_income", "INCOME"),
    ]

    grid = []
    for label, key, group in key_specs:
        if label in metrics:
            grid.append(
                {
                    "key": key,
                    "label": label,
                    "value": metrics[label],
                    "group": group,
                }
            )

    advanced = parse_sheet013_ratios()
    advanced_grid = []
    for label, key, group in _ADVANCED_RATIO_SPECS:
        if label not in advanced:
            continue
        value = advanced[label]
        if key == "jensen_alpha" and "Jensen's Alpha" in metrics:
            value = metrics["Jensen's Alpha"]
        elif key == "sharpe" and "Sharpe Ratio" in metrics:
            value = metrics["Sharpe Ratio"]
        elif key == "beta" and "Portfolio Beta" in metrics:
            value = metrics["Portfolio Beta"]
        advanced_grid.append(
            {"key": key, "label": label, "value": value, "group": group}
        )

    return {
        "source": "Final Excel model.htm (sheet005 — Hult simulation desk)",
        "trading_start": metrics.get("Trading Start Date"),
        "trading_end": metrics.get("Trading End Date"),
        "filed_mandate_target_return": "~10% p.a.",
        "filed_mandate_beta_target": "~1.0 average",
        "gain_analysis": gain_analysis,
        "grid": grid,
        "advanced_grid": advanced_grid,
        "all": metrics,
    }


def _parse_pct(value: str) -> float:
    return float(value.replace("%", "").replace(",", "").strip())


def _parse_money(value: str) -> float:
    cleaned = value.replace("$", "").replace(",", "").strip()
    if not cleaned or cleaned == "—":
        return 0.0
    return float(cleaned)


def parse_sheet011_timeline() -> dict:
    """NAV milestones from sheet008 PERFORMANCE TIMELINE (Feb 02 - Apr 11 2026)."""
    text = SHEET008.read_text(encoding="windows-1252", errors="replace")
    start = text.find("NAV TIMELINE")
    chunk = text[start : start + 80_000] if start >= 0 else text

    row_re = re.compile(
        r"<td class=xl(?:256|254|329)[^>]*>(\d{4}-\d{2}-\d{2})</td>\s*"
        r"<td class=xl\d+[^>]*>([^<]*)</td>\s*"
        r"<td[^>]*>\$([\d,]+)</td>\s*"
        r"<td[^>]*>\$([\d,]+)</td>\s*"
        r"<td[^>]*>\$([\d,]+)</td>\s*"
        r"<td[^>]*>([-\d.]+%)</td>\s*"
        r"<td[^>]*>([-\d.]+%)</td>",
        re.DOTALL,
    )

    milestones: list[dict] = []
    for m in row_re.finditer(chunk):
        event = re.sub(r"\s+", " ", m.group(2)).strip()
        milestones.append(
            {
                "date": m.group(1),
                "event": event,
                "portfolio_nav": _parse_money(m.group(3)),
                "spy_nav": _parse_money(m.group(4)),
                "portfolio_return_pct": _parse_pct(m.group(6)),
                "spy_return_pct": _parse_pct(m.group(7)),
            }
        )

    if not milestones:
        raise ValueError("No NAV milestones parsed from sheet008")

    ms = pd.DataFrame(milestones)
    ms["date"] = pd.to_datetime(ms["date"])
    ms = ms.sort_values("date").drop_duplicates("date", keep="last")

    trading_start = ms["date"].iloc[0]
    trading_end = ms["date"].iloc[-1]
    bdays = pd.bdate_range(trading_start, trading_end)

    port_nav = np.interp(
        bdays.astype(np.int64),
        ms["date"].astype(np.int64),
        ms["portfolio_nav"].astype(float),
    )
    port_ret = np.interp(
        bdays.astype(np.int64),
        ms["date"].astype(np.int64),
        ms["portfolio_return_pct"].astype(float),
    )
    spy_ret_raw = np.interp(
        bdays.astype(np.int64),
        ms["date"].astype(np.int64),
        ms["spy_return_pct"].astype(float),
    )

    # Align terminal SPY return with sheet005 official benchmark (-2.29%)
    terminal_spy = float(spy_ret_raw[-1])
    benchmark_target = -2.29
    spy_scale = benchmark_target / terminal_spy if terminal_spy else 1.0
    spy_ret = spy_ret_raw * spy_scale

    port_nav_series = port_nav.tolist()
    port_ret_series = port_ret.tolist()
    spy_ret_series = spy_ret.tolist()
    daily_port = pd.Series(port_nav_series, index=bdays).pct_change().fillna(0.0)

    peak_nav = float(ms["portfolio_nav"].max())
    trough_row = ms.loc[ms["portfolio_nav"].idxmin()]
    max_dd_pct = (trough_row["portfolio_nav"] / peak_nav - 1.0) * 100.0

    return {
        "source": "Final Excel model.htm (sheet008 — performance timeline)",
        "trading_start": trading_start.strftime("%m/%d/%Y %I:%M %p"),
        "trading_end": trading_end.strftime("%m/%d/%Y %I:%M %p"),
        "initial_capital": _INITIAL_CAPITAL,
        "final_portfolio_value": float(ms["portfolio_nav"].iloc[-1]),
        "portfolio_return_pct": float(ms["portfolio_return_pct"].iloc[-1]),
        "benchmark_return_pct": benchmark_target,
        "milestones": [
            {
                **row,
                "date": row["date"].strftime("%Y-%m-%d"),
            }
            for row in ms.to_dict(orient="records")
        ],
        "phases": _DESK_PHASES,
        "annotations": {
            "start": {
                "date": ms["date"].iloc[0].strftime("%Y-%m-%d"),
                "label": "$1,000,000 start",
            },
            "trough": {
                "date": trough_row["date"].strftime("%Y-%m-%d"),
                "portfolio_return_pct": float(trough_row["portfolio_return_pct"]),
                "spy_return_pct": float(trough_row["spy_return_pct"]),
                "max_drawdown_pct": round(max_dd_pct, 2),
            },
            "close": {
                "date": ms["date"].iloc[-1].strftime("%Y-%m-%d"),
                "portfolio_nav": float(ms["portfolio_nav"].iloc[-1]),
                "portfolio_return_pct": float(ms["portfolio_return_pct"].iloc[-1]),
                "spy_return_pct": benchmark_target,
            },
        },
        "series": {
            "dates": [d.strftime("%Y-%m-%d") for d in bdays],
            "portfolio_nav": [round(v, 2) for v in port_nav_series],
            "portfolio_return_pct": [round(v, 4) for v in port_ret_series],
            "spy_return_pct": [round(v, 4) for v in spy_ret_series],
            "daily_returns": [round(v, 8) for v in daily_port.tolist()],
        },
    }


def parse_sheet013_ratios() -> dict[str, str]:
    """Advanced ratios table from sheet013 (risk-adjusted suite only)."""
    text = SHEET013.read_text(encoding="windows-1252", errors="replace")
    text = re.sub(r"\s+", " ", text)
    start = text.find("RISK-ADJUSTED PERFORMANCE RATIOS")
    end = text.find("MAXIMUM DRAWDOWN", start)
    chunk = text[start : end] if start >= 0 and end > start else text[:30_000]

    allowed = {label for label, _, _ in _ADVANCED_RATIO_SPECS}
    ratios: dict[str, str] = {}
    row_re = re.compile(
        r"<td[^>]*class=xl3\d{2}[^>]*border-top:none[^>]*>([^<]+)</td>\s*"
        r"<td[^>]*>[^<]*</td>\s*"
        r"<td[^>]*class=xl3\d{2}[^>]*border-top:none[^>]*>([^<]+)</td>",
    )
    for m in row_re.finditer(chunk):
        name = re.sub(r"\s+", " ", m.group(1)).strip()
        val = m.group(2).strip()
        if name in allowed and name not in ratios:
            ratios[name] = val
    return ratios


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in ("script", "style"):
            self.skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self.skip = False

    def handle_data(self, data: str) -> None:
        if not self.skip:
            t = data.strip()
            if t:
                self.parts.append(t + " ")


def parse_report_excerpts() -> dict:
    htm = REPORT_HTM.read_text(encoding="windows-1252", errors="replace")
    ext = TextExtractor()
    ext.feed(htm)
    blob = re.sub(r"\s+", " ", "".join(ext.parts))

    # Curated anchors (substring match)
    curated = [
        (
            "executive",
            "EXECUTIVE SUMMARY",
            "Team 5's in the CHL-0200 Investment Challenge underperformed the benchmark",
        ),
        (
            "conclusion",
            "KEY CONCLUSION",
            "The key conclusion is straightforward: the portfolio's risk architecture was defensible",
        ),
        (
            "hedge-success",
            "CRISIS HEDGE",
            "The Team created a low-beta portfolio to invest in a market environment",
        ),
        (
            "recovery-failure",
            "RECOVERY GAP",
            "However, one of the main flaws in Team 5's investment strategy is that their portfolio underperformed during the recovery",
        ),
        (
            "post-mortem-frame",
            "POST-MORTEM FRAME",
            "A professional post-mortem therefore should not ask only",
        ),
        (
            "strategy-rationale",
            "STRATEGY RATIONALE",
            "Introduction: Strategy Choice and Rationale When the CHL-0200 Investment Challenge came along",
        ),
        (
            "mandate-target",
            "FILED MANDATE",
            "the team established a mandate to invest with a moderate",
        ),
        (
            "sharpe-caveat",
            "SHARPE CAVEAT",
            "The portfolio's Sharpe ratio finished at the bottom of the cohort",
        ),
        (
            "behavioral",
            "BEHAVIORAL DRAG",
            "behavioral drag",
        ),
        (
            "implementation",
            "IMPLEMENTATION",
            "Implementation Blueprint",
        ),
    ]

    excerpts = []
    for section_id, kicker, needle in curated:
        idx = blob.find(needle.replace("'", "\u2019")) if "'" in needle else blob.find(needle)
        if idx < 0:
            idx = blob.find(needle)
        if idx < 0:
            continue
        chunk = blob[idx : idx + 900]
        # end at sentence boundary
        end = chunk.rfind(". ")
        if end > 200:
            chunk = chunk[: end + 1]
        excerpts.append(
            {
                "id": section_id,
                "kicker": kicker,
                "text": chunk.strip(),
                "full_report_href": "./report.html",
            }
        )

    return {
        "source": "Investment-CHL-Team-5-BWC-1 (1).htm",
        "word_count": 2616,
        "excerpts": excerpts,
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    excel_path = DATA_DIR / "excel-metrics.json"
    timeline_path = DATA_DIR / "desk-timeline.json"
    report_path = DATA_DIR / "report-excerpts.json"
    excel_path.write_text(
        json.dumps(parse_excel_metrics(), indent=2), encoding="utf-8"
    )
    timeline_path.write_text(
        json.dumps(parse_sheet011_timeline(), indent=2), encoding="utf-8"
    )
    report_path.write_text(
        json.dumps(parse_report_excerpts(), indent=2), encoding="utf-8"
    )
    print(f"Wrote {excel_path}")
    print(f"Wrote {timeline_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
