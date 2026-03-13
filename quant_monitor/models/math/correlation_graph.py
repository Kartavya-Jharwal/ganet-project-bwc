
"""Phase 13: Weighted Correlation Graph using Sparse Inverse Covariance ($L_1$ penalty)."""

from __future__ import annotations

import logging
import duckdb
import numpy as np
import pandas as pd
from sklearn.covariance import GraphicalLassoCV
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, List
import json

from quant_monitor.data.appwrite_client import create_appwrite_client, COLLECTIONS

logger = logging.getLogger(__name__)

class CorrelationGraphBuilder:
    def __init__(self, db_path: str = "portfolio.duckdb"):
        self.db_path = db_path

    def _extract_returns(self) -> pd.DataFrame:
        """Extract pivoted returns spanning ~252 days from DuckDB."""
        logger.info("Extracting prices for Correlation Graph...")
        # Since we might be lacking data initially, we do not strictly enforce 252 days in the query.
        conn = duckdb.connect(self.db_path, read_only=True)
        try:
            # Get latest 252 available trading days per ticker
            query = """
                SELECT timestamp::DATE as date, ticker, close
                FROM eod_price_matrix
                WHERE timestamp >= CURRENT_DATE - INTERVAL 365 DAY
            """
            df = conn.execute(query).df()
        except duckdb.CatalogException:
            # table might not exist if duckdb sync hasnt run
            return pd.DataFrame()
        finally:
            conn.close()

        if df.empty:
            return df
            
        pivoted = df.pivot_table(index="date", columns="ticker", values="close")
        pivoted = pivoted.ffill().bfill()
        returns = np.log(pivoted / pivoted.shift(1)).dropna(how="all")
        # limit to last 252 rows
        returns = returns.tail(252)
        
        # Drop columns with all NaNs
        returns = returns.dropna(axis=1, how="all")
        # Fill any remaining NaNs with 0 (edge case where ticker was unlisted)
        returns = returns.fillna(0.0)
        return returns

    def build_graph(self) -> dict[str, Any]:
        """Compute the sparse inverse covariance matrix."""
        returns = self._extract_returns()
        if returns.empty or len(returns.columns) < 2:
            logger.warning("Not enough data to calculate GraphicalLassoCV.")
            return {}

        tickers = list(returns.columns)
        
        # 1. StandardScaler Processing
        scaler = StandardScaler()
        scaled_returns = scaler.fit_transform(returns)
        
        # Neutralize extreme outliers (cap to +/- 5 standard deviations) to prevent earnings gap noise
        np.clip(scaled_returns, -5.0, 5.0, out=scaled_returns)

        # 2. GraphicalLasso CV Loop
        logger.info(f"Running GraphicalLassoCV on {len(tickers)} assets over {len(returns)} days...")
        # Reduce verbosity, use 5-fold CV
        model = GraphicalLassoCV(cv=5, max_iter=2000, verbose=False, n_jobs=1)
        try:
            model.fit(scaled_returns)
        except Exception as e:
             logger.error(f"GraphicalLassoCV failed to converge: {e}")
             return {}

        # The precision matrix is the inverse of covariance
        precision = model.precision_
        
        # Convert precision to partial correlation matrix
        d = np.diag(precision)
        d_inv_sqrt = np.diag(1.0 / np.sqrt(np.clip(d, a_min=1e-12, a_max=None)))
        partial_corr = - (d_inv_sqrt @ precision @ d_inv_sqrt)
        np.fill_diagonal(partial_corr, 1.0) # diagonal is 1

        # 3. Thresholding (e.g. drop edges where |rho| < 0.2)
        threshold = 0.2
        edges = []
        for i in range(len(tickers)):
            for j in range(i + 1, len(tickers)):
                rho = partial_corr[i, j]
                if abs(rho) > threshold:
                    edges.append({
                        "source": tickers[i],
                        "target": tickers[j],
                        "weight": float(rho)
                    })

        logger.info(f"Generated {len(edges)} significant topological edges.")
        
        # State Output: Pushing to Appwrite and local DuckDB
        result = {
            "tickers": tickers,
            "edges": edges,
            "covariance": model.covariance_.tolist(),
            "precision": model.precision_.tolist()
        }
        
        try:
            from datetime import datetime
            
            # Push Appwrite
            aw = create_appwrite_client()
            aw.write_document(
                COLLECTIONS.get("correlations_cache", "correlations_cache"),
                {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "nodes": json.dumps(tickers),
                    "edges": json.dumps(edges)
                }
            )
            
            # Write DuckDB explicitly as well
            conn = duckdb.connect(self.db_path, read_only=False)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS correlations_cache (
                    timestamp TIMESTAMP,
                    nodes VARCHAR,
                    edges VARCHAR
                )
            """)
            conn.execute(
                "INSERT INTO correlations_cache VALUES (CURRENT_TIMESTAMP, ?, ?)",
                (json.dumps(tickers), json.dumps(edges))
            )
            conn.close()
            logger.info("Successfully pushed topology to Appwrite and DuckDB.")
        except Exception as e:
            logger.warning(f"Failed to push topology state to Appwrite/DuckDB: {e}")
        
        return result

