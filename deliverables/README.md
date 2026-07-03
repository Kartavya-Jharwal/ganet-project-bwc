# Team BWC deliverables

**Project Ganet** · **Adaptive Efficiency** archive · sunset `2026-04-10` valuation · `2026-05-01` reporting · Hult Investment Challenge (Team 5)

This folder is the **grading authority** for the program: client post-mortem, charter, trading records, and committee materials. The **`quant_monitor/`** package is a supplementary audit overlay, not the whole investment story.

Faculty grades and peer feedback are **already incorporated** here. If the public site or engineering docs disagree with these files, **this folder wins**.

`frontend/deliverables/source/` mirrors `source/` for GitHub Pages downloads. Chronological order is applied by `scripts/sync_deliverables_manual.py` (charter → deployment → case work → trading logs → close artifacts).

## Files (`source/`)

| File | Description |
|------|-------------|
| `Investment_Team_Charter_Team_5 (1).docx` | Team charter |
| `Initial Portfolio Depoyment.docx` | Opening book deployment memo |
| `Strategy Synopsis.docx` | Strategy summary |
| `(Case Study) Apple Annual Reports.docx` | Apple case study source |
| `(Case Study) Apple Anuual StockPitch.pptx` | Apple stock pitch deck |
| `(Case) BlackRock Top Down Analysis.pdf` | BlackRock macro case |
| `AI Advice strategies.docx` | AI-assisted strategy notes |
| `Trading_Log-1_Team_5.xlsx` … `Trading_Log-5_Team_5.xlsx` | Periodic trading logs |
| `Trading_Log-5_Team_5.csv` · `Trading_Log-5_Team_5 (4).2.csv` | Final log exports |
| `ESG X RAY Mid Simulation.pdf` | Mid-simulation ESG review |
| `Investment-CHL-Team-5-BWC-1-memo.docx` | Investment memo |
| `Investment-CHL-Team-5-BWC-1 (1).docx` | Written investment deliverable |
| `Final Excel model.xlsx` | Committee Excel model |
| `BWC_Institutional_Tearsheet.pdf` | Desk tearsheet |
| `Different format-transaction history.csv` | Alternate journal export |
| `Client_Post_Mortem_Investment_Challenge-Team-5-BWC_CH200.pdf` | Client-facing post-mortem (main narrative) |
| `Client_Post_Mortem_Investment_Challenge-Team-5-BWC_CH200.pptx` | Editable deck source |

**Web mirror:** [post-mortem PDF](../frontend/assets/post-mortem.pdf) · [download table](../frontend/deliverables/index.html) · [live site](../frontend/index.html) · [engineering docs](../frontend/docs/)

## Reproducible quant audit (code)

- Trade fixture for tests: `tests/test_data/journal_transaction_history.csv`
- Engine: `quant_monitor/` · guide: [REVIEWERS.md](../REVIEWERS.md)
