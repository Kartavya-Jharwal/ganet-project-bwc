"""Walk-forward backtesting engine.

No simple backtests — walk-forward only (avoids lookahead bias).
- Training window: 252 days (1 year)
- Test window: 21 days (1 month)
- Roll forward: 21 days at a time

Models tested independently then compared:
1. Technical only
2. Fundamental only
3. Sentiment only
4. Fused (static equal weights)
5. Fused (dynamic regime weights) ← expected winner
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


class WalkForwardEngine:
    """Walk-forward backtesting with configurable train/test windows."""

    def __init__(
        self,
        train_window: int = 252,
        test_window: int = 21,
        step_size: int = 21,
    ) -> None:
        self.train_window = train_window
        self.test_window = test_window
        self.step_size = step_size

    def run(self, data: pd.DataFrame, model_name: str) -> dict:
        """Run walk-forward backtest for a single model configuration.

        Returns: dict of aggregated metrics across all test windows.
        """
        # TODO Phase 8
        raise NotImplementedError

    def compare_models(self, data: pd.DataFrame) -> pd.DataFrame:
        """Run all 5 model configs and return comparative metrics table."""
        # TODO Phase 8
        raise NotImplementedError
