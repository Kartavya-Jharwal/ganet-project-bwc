"""Phase 14: Hierarchical Risk Parity (HRP) Position Sizing."""

import logging

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform

logger = logging.getLogger(__name__)


class HRPSizer:
    def __init__(self, partial_corr_matrix: np.ndarray, tickers: list[str], variances: np.ndarray):
        """
        Args:
            partial_corr_matrix: Symmetrical numpy array of partial correlations.
            tickers: List of ticker strings.
            variances: Numpy array of asset variances (e.g., from ATR or historical).
        """
        self.partial_corr_matrix = partial_corr_matrix
        self.tickers = tickers
        self.variances = variances

    def get_quasi_diag(self, link: np.ndarray) -> list[int]:
        """Sort clustered items by distance."""
        link = link.astype(int)
        sort_ix = pd.Series([link[-1, 0], link[-1, 1]])
        num_items = link[-1, 3]
        while sort_ix.max() >= num_items:
            sort_ix.index = range(0, sort_ix.shape[0] * 2, 2)
            df0 = sort_ix[sort_ix >= num_items]
            i = df0.index
            j = df0.values - num_items
            sort_ix[i] = link[j, 0]
            df0 = pd.Series(link[j, 1], index=i + 1)
            sort_ix = pd.concat([sort_ix, df0])
            sort_ix = sort_ix.sort_index()
            sort_ix.index = range(sort_ix.shape[0])
        return sort_ix.tolist()

    def get_cluster_var(self, cov: np.ndarray, c_items: list[int]) -> float:
        """Calculate variance per cluster."""
        cov_slice = cov[np.ix_(c_items, c_items)]
        # Inverse variance portfolio weights
        iv = 1.0 / np.diag(cov_slice)
        iv /= iv.sum()
        w = iv.reshape(-1, 1)
        return float(np.dot(np.dot(w.T, cov_slice), w)[0, 0])

    def get_rec_bipart(self, cov: np.ndarray, sort_ix: list[int]) -> pd.Series:
        """Compute HRP allocations via recursive bisection."""
        w = pd.Series(1.0, index=sort_ix)
        c_items = [sort_ix]
        while len(c_items) > 0:
            c_items = [
                i[j:k]
                for i in c_items
                for j, k in ((0, len(i) // 2), (len(i) // 2, len(i)))
                if len(i) > 1
            ]
            for i in range(0, len(c_items), 2):
                c_items0 = c_items[i]
                c_items1 = c_items[i + 1]
                c_var0 = self.get_cluster_var(cov, c_items0)
                c_var1 = self.get_cluster_var(cov, c_items1)
                alpha = 1 - c_var0 / (c_var0 + c_var1)
                w[c_items0] *= alpha
                w[c_items1] *= 1 - alpha
        return w

    def allocate(self) -> dict[str, float]:
        """Compute the HRP weights."""
        logger.info(f"Computing HRP allocations for {len(self.tickers)} assets.")

        # 1. Distance Metric
        # D_i,j = sqrt(0.5 * (1 - rho_i,j))
        # Ensure partial_corr is bounded to [-1, 1] to avoid nan in sqrt
        rho = np.clip(self.partial_corr_matrix, -1.0, 1.0)
        dist_matrix = np.sqrt(0.5 * (1 - rho))

        # Zero out diagonal
        np.fill_diagonal(dist_matrix, 0.0)

        # 2. SciPy Linkage
        # Convert to condensed distance matrix for linkage
        condensed_dist = squareform(dist_matrix, checks=False)
        link = linkage(condensed_dist, method="single")

        # 3. Asset Sorting
        sort_ix = self.get_quasi_diag(link)

        # 4. Recursive Bisection using Inverse Trailing Variance
        # We need a proxy covariance matrix for the cluster var calculation.
        # Since we use inverse variance sizing, we construct a diagonal covariance
        # using the provided variances (ATR-derived).
        proxy_cov = np.diag(self.variances)

        weights = self.get_rec_bipart(proxy_cov, sort_ix)

        # 5. Sizing Output
        w_dict = {}
        for idx, weight in weights.items():
            w_dict[self.tickers[idx]] = weight

        logger.info("Successfully generated HRP weights.")
        return w_dict
