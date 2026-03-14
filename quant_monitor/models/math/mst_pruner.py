"""Phase 16: Minimum Spanning Tree (MST) Pruning."""

import logging
from typing import Any

import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)


class MSTPruner:
    def __init__(self, partial_corr_matrix: np.ndarray, tickers: list[str]):
        """
        Args:
            partial_corr_matrix: Symmetrical numpy array of partial correlations.
            tickers: List of string tickers.
        """
        self.partial_corr_matrix = partial_corr_matrix
        self.tickers = tickers

    def process_mst(self) -> dict[str, Any]:
        """Compute MST and evaluate Centrality Risk."""
        logger.info("Executing Kruskal MST Pruning on Correlation topology.")

        # Distance Metric
        rho = np.clip(self.partial_corr_matrix, -1.0, 1.0)
        dist_matrix = np.sqrt(0.5 * (1 - rho))
        np.fill_diagonal(dist_matrix, 0.0)

        G = nx.Graph()
        num_assets = len(self.tickers)

        for i in range(num_assets):
            G.add_node(self.tickers[i])
            for j in range(i + 1, num_assets):
                G.add_edge(self.tickers[i], self.tickers[j], weight=dist_matrix[i, j])

        # Kruskals Algorithm
        mst = nx.minimum_spanning_tree(G)

        # Centrality Diagnostics
        degrees = dict(mst.degree())

        warnings = []
        alpha_flags = []

        for node, degree in degrees.items():
            if degree > 4:
                warnings.append({"ticker": node, "degree": degree, "flag": "Prune Warning (Hub)"})
            elif degree == 1:
                alpha_flags.append(
                    {"ticker": node, "degree": degree, "flag": "Alpha Flag (Leaf/Island)"}
                )

        # Phase 21 Export: Generate Interactive D3 Visualization via PyVis
        try:
            import os

            from pyvis.network import Network

            # Ensure docs directory exists
            os.makedirs("docs", exist_ok=True)

            net = Network(
                height="600px", width="100%", bgcolor="#0d0d0d", font_color="white", notebook=False
            )
            # Add nodes with centrality-based scaling
            for node in mst.nodes():
                deg = degrees.get(node, 1)
                color = "#ff4757" if deg > 4 else ("#2ed573" if deg == 1 else "#a4b0be")
                net.add_node(
                    node, label=node, size=deg * 10, color=color, title=f"Degree Centrality: {deg}"
                )

            for u, v, data in mst.edges(data=True):
                w = max(1, 5 - (data["weight"] * 10))  # Invert distance for thickness
                net.add_edge(u, v, value=w, title=f"Dist: {data['weight']:.2f}")

            net.force_atlas_2based()
            net.save_graph("docs/interactive_mst.html")
            logger.info(
                "Successfully exported Interactive MST visualization to docs/interactive_mst.html"
            )
        except ImportError:
            logger.warning("PyVis not installed. Skipping D3 Export.")
        except Exception as e:
            logger.warning(f"Failed to generate PyVis interactive map: {e}")

        logger.info(
            f"MST Processed. Found {len(warnings)} hubs and {len(alpha_flags)} isolated alpha nodes."
        )

        return {
            "mst_edges": [
                {"source": u, "target": v, "weight": d["weight"]}
                for u, v, d in mst.edges(data=True)
            ],
            "prune_warnings": warnings,
            "alpha_flags": alpha_flags,
            "degrees": degrees,
        }
