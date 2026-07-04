"""Apply microsite copy punctuation rules (no em dashes or semicolons in prose)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "frontend" / "index.html"
MAIN_JS = ROOT / "frontend" / "js" / "main.js"

INDEX_REPLACEMENTS: list[tuple[str, str]] = [
    ('Team BWC — Hult Investment Challenge Post-Mortem', 'Team BWC: Hult Investment Challenge Post-Mortem'),
    (
        'on the closed trading universe — confidence signals, not trade signals.',
        'on the closed trading universe. Confidence signals, not trade signals.',
    ),
    (
        'title="End-of-simulation snapshot; filed memo targeted ~1.0 average portfolio beta"',
        'title="End-of-simulation snapshot. Filed memo targeted ~1.0 average portfolio beta"',
    ),
    (
        'Half the desk has already graduated; what lasted was tighter process discipline, cleaner logs, and a shared risk vocabulary we still use in compliance and risk roles.',
        'Half the desk has already graduated. What lasted was tighter process discipline, cleaner logs, and a shared risk vocabulary we still use in compliance and risk roles.',
    ),
    (
        'Filed memo is the narrative authority; this page is the scan path.',
        'Filed memo is the narrative authority. This page is the scan path.',
    ),
    (
        '(2004, 2017) — efficiency as an evolutionary process, not a static binary. In a three-month simulation, noise can win a round; over longer horizons, re-evaluation and discipline compound. We tried; the regime labels, charter override, and audit layer record where we adapted and where we did not.',
        '(2004, 2017): efficiency as an evolutionary process, not a static binary. In a three-month simulation, noise can win a round. Over longer horizons, re-evaluation and discipline compound. We tried. The regime labels, charter override, and audit layer record where we adapted and where we did not.',
    ),
    (
        'Section 5 charter override — portfolio last in class with twelve days left — then emergency triage, hedges, and lower exposure; desk trough',
        'Section 5 charter override (portfolio last in class with twelve days left), then emergency triage, hedges, and lower exposure. Desk trough',
    ),
    (
        'Ceasefire window: SPY snapped back; we rebuilt equity exposure too carefully and gave back relative performance.',
        'Ceasefire window: SPY snapped back. We rebuilt equity exposure too carefully and gave back relative performance.',
    ),
    (
        '2026-05-01 engineering snapshot; no live trading, no Appwrite sync. Committee memo phase calendar differs from marks-book NAV dates; this site follows the Excel PERFORMANCE TIMELINE (sheet008).',
        '2026-05-01 engineering snapshot. No live trading, no Appwrite sync. Committee memo phase calendar differs from marks-book NAV dates. This site follows the Excel PERFORMANCE TIMELINE (sheet008).',
    ),
    ('PDF for review; PPTX if you need to edit slides.', 'PDF for review. PPTX if you need to edit slides.'),
    (
        'CHL-0200 program rules, grading frame, and desk window — before the narrative and marks.',
        'CHL-0200 program rules, grading frame, and desk window, before the narrative and marks.',
    ),
    (
        'across US equities and ETFs — deployed in real time through a simulated brokerage, with the same order, margin, and short mechanics as a live desk.',
        'across US equities and ETFs, deployed in real time through a simulated brokerage, with the same order, margin, and short mechanics as a live desk.',
    ),
    (
        'The test is whether process discipline holds under constraint — not whether conviction does.',
        'The test is whether process discipline holds under constraint, not whether conviction does.',
    ),
    ('StockTrak trading period; headline marks frozen at close', 'StockTrak trading period. Headline marks frozen at close'),
    ('Static engineering snapshot; no live sync', 'Static engineering snapshot. No live sync'),
    (
        'Headline cards, ratio wall, and desk-only charts — faculty-scored marks from the 11 Apr 2026 close.',
        'Headline cards, ratio wall, and desk-only charts. Faculty-scored marks from the 11 Apr 2026 close.',
    ),
    ('Memo target ~10% p.a.; ann.', 'Memo target ~10% p.a. Ann.'),
    ('-11.72%</span> — <span', '-11.72%</span>, <span'),
    ('Negative expectancy; detail in post-mortem modal.', 'Negative expectancy. Detail in post-mortem modal.'),
    (
        'Excel close, 11 Apr 2026 — the numbers faculty scored. Headline <span class="text-mono">-4.37%</span> total; trough drawdown',
        'Excel close, 11 Apr 2026, the numbers faculty scored. Headline <span class="text-mono">-4.37%</span> total. Trough drawdown',
    ),
    (
        'the course never asked for Calmar, M2, or a full ratio wall; we built it anyway.',
        'the course never asked for Calmar, M2, or a full ratio wall. We built it anyway.',
    ),
    ('Labels match the grading sheet; read the cards above first.', 'Labels match the grading sheet. Read the cards above first.'),
    ('<!-- RESEARCH (Python audit + charts — not filed) -->', '<!-- RESEARCH (Python audit + charts, not filed) -->'),
    (
        'Backtest and stress-test on the closed trading universe — not the graded desk book.',
        'Backtest and stress-test on the closed trading universe, not the graded desk book.',
    ),
    (
        'Confidence signals, not trade signals — audit overlay only; never pair these returns with desk marks row-by-row.',
        'Confidence signals, not trade signals. Audit overlay only. Never pair these returns with desk marks row-by-row.',
    ),
    (
        'tickers we actually held/traded — audits behavior, not a new research universe.',
        'tickers we actually held/traded. Audits behavior, not a new research universe.',
    ),
    (
        'terminal-first CLI dashboard — fast review, not a flashy web UI.',
        'terminal-first CLI dashboard for fast review, not a flashy web UI.',
    ),
    ('Signals suppressed; min-variance + cash buffer', 'Signals suppressed. Min-variance + cash buffer'),
    (
        'Python backtest and forward-cast stress test on the closed trading universe — not the graded Excel book.',
        'Python backtest and forward-cast stress test on the closed trading universe, not the graded Excel book.',
    ),
    (
        'Model-weighted backtest exposure; not comparable to desk terminal beta at crisis de-risk.',
        'Model-weighted backtest exposure. Not comparable to desk terminal beta at crisis de-risk.',
    ),
    (
        '<code>project</code>, <code>project-dashboard</code>, <code>project-bootstrap</code>; doctor, backtest, dashboard entrypoints',
        '<code>project</code>, <code>project-dashboard</code>, <code>project-bootstrap</code>, plus doctor, backtest, and dashboard entrypoints',
    ),
    (
        'Snapshots, signals, alerts, scraped data (historical; frozen at archive)',
        'Snapshots, signals, alerts, scraped data (historical, frozen at archive)',
    ),
    (
        'Manim loops for ingest, limits, and module topology — swipe on mobile, grid on desktop. Muted autoplay in view only.',
        'Manim loops for ingest, limits, and module topology. Swipe on mobile, grid on desktop. Muted autoplay in view only.',
    ),
    (
        'We are not re-litigating grades here. Process and logs scored high; headline return did not.',
        'We are not re-litigating grades here. Process and logs scored high. Headline return did not.',
    ),
    ('At the Apr 2 trough only — desk', 'At the Apr 2 trough only: desk'),
    (
        'That is the preservation story; it does not vindicate negative Sharpe, Sortino, or expectancy on the term.',
        'That is the preservation story. It does not vindicate negative Sharpe, Sortino, or expectancy on the term.',
    ),
    (
        'Eight-person schedules clashed; full desk dry-runs were rare; some oral defense answers reflected that gap.',
        'Eight-person schedules clashed. Full desk dry-runs were rare. Some oral defense answers reflected that gap.',
    ),
    (
        'Not every member carried the same quant load; the lead owned validator design and integration.',
        'Not every member carried the same quant load. The lead owned validator design and integration.',
    ),
    (
        'reproducible records, not P&amp;L: the discipline we took into compliance and risk internships.',
        'reproducible records, not P&amp;L. The discipline we took into compliance and risk internships.',
    ),
    (
        'PSQ/SH cost <span class="text-mono">-$19,205</span> on the Apr 2 tariff rally; AA/CENX (+$17,169) and lower exposure at the trough did more protecting than inverse ETFs.',
        'PSQ/SH cost <span class="text-mono">-$19,205</span> on the Apr 2 tariff rally. AA/CENX (+$17,169) and lower exposure at the trough did more protecting than inverse ETFs.',
    ),
    (
        'SH/PSQ behave like short futures, not convex puts — next desk would size 1–2% NAV in OTM SPY puts instead, and still pre-write a ceasefire re-risk playbook.',
        'SH/PSQ behave like short futures, not convex puts. Next desk would size 1–2% NAV in OTM SPY puts instead, and still pre-write a ceasefire re-risk playbook.',
    ),
    (
        'Python checked our story; it did not trade the book.',
        'Python checked our story. It did not trade the book.',
    ),
    (
        'or a 15-minute walkthrough of what we filed vs what we built — email',
        'or a 15-minute walkthrough of what we filed vs what we built. Email',
    ),
    (
        'Operate inside constraints set in advance — not negotiated after the fact.',
        'Operate inside constraints set in advance, not negotiated after the fact.',
    ),
    (
        'real-time pricing, executed orders, margin, and shorts — settled in paper capital, not real currency.',
        'real-time pricing, executed orders, margin, and shorts, settled in paper capital, not real currency.',
    ),
    (
        'The Investment Policy Statement — risk tolerance, eligible instruments, operating limits — was issued by the instructor before trading opened.',
        'The Investment Policy Statement (risk tolerance, eligible instruments, operating limits) was issued by the instructor before trading opened.',
    ),
    (
        'Legible to someone who reads a stock chart as green-up / red-down — yet rigorous enough to grade on Sharpe and risk-adjusted return by semester end.',
        'Legible to someone who reads a stock chart as green-up / red-down, yet rigorous enough to grade on Sharpe and risk-adjusted return by semester end.',
    ),
    (
        'US equities and ETFs in practice; Treasuries, margin, and shorts permitted under the IPS',
        'US equities and ETFs in practice. Treasuries, margin, and shorts permitted under the IPS',
    ),
    (
        '<span class="text-mono">$10</span> commission per trade; 300-trade semester ceiling',
        '<span class="text-mono">$10</span> commission per trade. 300-trade semester ceiling',
    ),
    (
        'Eight teams, identical rules; five-person team cap removed this run',
        'Eight teams, identical rules. Five-person team cap removed this run',
    ),
    (
        'Final report and client presentation in plain language — not finance jargon',
        'Final report and client presentation in plain language, not finance jargon',
    ),
    (
        'Grading weighted process and logs heavily; headline return still missed.',
        'Grading weighted process and logs heavily. Headline return still missed.',
    ),
    (
        'Seven closed round-trips in the Excel export; only two were winners.',
        'Seven closed round-trips in the Excel export. Only two were winners.',
    ),
    (
        'Terminal beta 0.63 after a Crisis swing from ~1.0 target; AA/CENX metals (+$17,169) buffered trough downside vs SPY; inverse ETFs were a net drag, not protection.',
        'Terminal beta 0.63 after a Crisis swing from ~1.0 target. AA/CENX metals (+$17,169) buffered trough downside vs SPY. Inverse ETFs were a net drag, not protection.',
    ),
    (
        'we invoked Section 5 — emergency triage, not a calm risk dial-down.',
        'we invoked Section 5: emergency triage, not a calm risk dial-down.',
    ),
    (
        'while we were still <span class="text-mono">-4.8%</span>; we added equity slowly',
        'while we were still <span class="text-mono">-4.8%</span>. We added equity slowly',
    ),
    (
        'not inverse hedges; we re-risked too slowly after the bounce.',
        'not inverse hedges. We re-risked too slowly after the bounce.',
    ),
    (
        'Eight operators split execution, IPS compliance, and journal discipline — with a Python overlay as a confidence check in the diary, not a trade signal.',
        'Eight operators split execution, IPS compliance, and journal discipline, with a Python overlay as a confidence check in the diary, not a trade signal.',
    ),
    (
        'The brief did not ask us to invent the mandate — it asked us to run inside it and prove we did.',
        'The brief did not ask us to invent the mandate. It asked us to run inside it and prove we did.',
    ),
    (
        'Rationale for every open and close — win or loss — plus bi-weekly logs translating diary entries into trade-level justification.',
        'Rationale for every open and close, win or loss, plus bi-weekly logs translating diary entries into trade-level justification.',
    ),
    (
        'What the deliverables list required — expressed through sleeves, screens, and memo sections, not a single quant model.',
        'What the deliverables list required, expressed through sleeves, screens, and memo sections, not a single quant model.',
    ),
    (
        'Committee-facing lens on contested names — narrative risk, not a separate book.',
        'Committee-facing lens on contested names: narrative risk, not a separate book.',
    ),
    (
        'after volatile weeks — cited in diaries, never wired to live execution.',
        'after volatile weeks. Cited in diaries, never wired to live execution.',
    ),
    (
        'only names we actually held or traded — behaviour audit, not a fresh research universe.',
        'only names we actually held or traded. Behaviour audit, not a fresh research universe.',
    ),
    (
        'Grouped for scan — full depth in',
        'Grouped for scan. Full depth in',
    ),
    (
        'Macro mood labels — used to flag when trades did not match the labeled environment.',
        'Macro mood labels, used to flag when trades did not match the labeled environment.',
    ),
    (
        'committee review — not live trade instructions.',
        'committee review, not live trade instructions.',
    ),
    (
        'Stops and trailing stops on extended names; trend confirmation before adds.',
        'Stops and trailing stops on extended names, with trend confirmation before adds.',
    ),
    (
        'Screens and pitches informed debate; execution still ran through StockTrak and IPS.',
        'Screens and pitches informed debate. Execution still ran through StockTrak and IPS.',
    ),
    (
        'Ingest → validate → attribute → chart. Terminal-first CLI surfaces; no live signal feed to StockTrak.',
        'Ingest → validate → attribute → chart. Terminal-first CLI surfaces. No live signal feed to StockTrak.',
    ),
]

MAIN_JS_REPLACEMENTS: list[tuple[str, str]] = [
    (
        "title: 'End-of-simulation snapshot; filed memo targeted ~1.0 average portfolio beta'",
        "title: 'End-of-simulation snapshot. Filed memo targeted ~1.0 average portfolio beta'",
    ),
    (
        "title: 'TWR^(365/68)−1; 68-day window — context only, not investable'",
        "title: 'TWR^(365/68)−1 on a 68-day window. Context only, not investable'",
    ),
    (
        "${data.word_count ? `${data.word_count.toLocaleString()} words filed` : 'Committee memo'} — pull quotes below; full HTM is authoritative.",
        "${data.word_count ? `${data.word_count.toLocaleString()} words filed` : 'Committee memo'}. Pull quotes below. Full HTM is authoritative.",
    ),
    ("return '—'", "return 'n/a'"),
    ('/* file:// or HEAD blocked — fall through */', '/* file:// or HEAD blocked: fall through */'),
]


def apply(path: Path, pairs: list[tuple[str, str]]) -> int:
    text = path.read_text(encoding='utf-8')
    n = 0
    for old, new in pairs:
        c = text.count(old)
        if c:
            text = text.replace(old, new)
            n += c
    path.write_text(text, encoding='utf-8')
    return n


def main() -> int:
    ni = apply(INDEX, INDEX_REPLACEMENTS)
    nm = apply(MAIN_JS, MAIN_JS_REPLACEMENTS)
    print(f'index.html: {ni} replacements')
    print(f'main.js: {nm} replacements')
    remaining = INDEX.read_text(encoding='utf-8').count('\u2014')
    if remaining:
        print(f'WARNING: {remaining} em dashes remain in index.html', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
