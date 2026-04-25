#!/usr/bin/env python3
"""
01_synthetic_network.py
=======================
Demonstrate graph-theory analysis methods on a small (10-node) synthetic
directed weighted network before applying them to the real Kenya coast data.

Usage
-----
    python scripts/01_synthetic_network.py

Output
------
All plots are saved to  plots/synthetic/
A metrics summary is printed to the console.
"""

import sys
import pathlib
import pandas as pd

# Make the project root importable
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")

from src.data_loader    import synthetic_10node_graph
from src.graph_metrics  import summary_dataframe, community_detection, clustering_metrics
from src.visualization  import (
    plot_network,
    plot_connectivity_heatmap,
    plot_metric_bars,
    plot_community_network,
    plot_degree_distribution,
)

OUTDIR = ROOT / "plots" / "synthetic"
OUTDIR.mkdir(parents=True, exist_ok=True)


def main():
    # -----------------------------------------------------------------------
    # 1.  Build the synthetic graph
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("  SYNTHETIC 10-NODE NETWORK – GRAPH THEORY DEMONSTRATION")
    print("=" * 60)

    G = synthetic_10node_graph()
    print(f"\nGraph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # -----------------------------------------------------------------------
    # 2.  Compute all metrics and print summary
    # -----------------------------------------------------------------------
    df = summary_dataframe(G)
    print("\n── Node-level metrics ──────────────────────────────────")
    pd.set_option("display.float_format", "{:.4f}".format)
    print(df.to_string())

    clust = clustering_metrics(G)
    print(f"\nGlobal transitivity (clustering coefficient): "
          f"{clust['global_transitivity']:.4f}")

    partition = community_detection(G)
    print(f"\nCommunity assignments: {partition}")
    n_communities = len(set(partition.values()))
    print(f"Number of communities detected: {n_communities}")

    # -----------------------------------------------------------------------
    # 3.  Visualise
    # -----------------------------------------------------------------------
    print("\nGenerating plots …")

    # 3a.  Network plot sized by out-degree, coloured by betweenness
    plot_network(
        G,
        node_size_metric=dict(G.out_degree(weight="weight")),
        title="Synthetic 10-Node Network\n(size = out-degree, colour = betweenness)",
        layout="spring",
        save_path=str(OUTDIR / "network_overview.png"),
    )
    print(f"  Saved: {OUTDIR / 'network_overview.png'}")

    # 3b.  Community structure
    plot_community_network(
        G, partition,
        title="Synthetic Network – Community Structure",
        layout="spring",
        save_path=str(OUTDIR / "community_structure.png"),
    )
    print(f"  Saved: {OUTDIR / 'community_structure.png'}")

    # 3c.  Metric bar charts
    for metric in ["out_degree", "in_degree", "betweenness",
                   "closeness", "eigenvector", "pagerank", "local_clustering"]:
        plot_metric_bars(
            df, metric,
            title=f"Synthetic – {metric.replace('_', ' ').title()}",
            save_path=str(OUTDIR / f"bar_{metric}.png"),
        )
        print(f"  Saved: {OUTDIR / f'bar_{metric}.png'}")

    # 3d.  Degree distribution
    plot_degree_distribution(
        G,
        title="Synthetic 10-Node – Degree Distribution",
        save_path=str(OUTDIR / "degree_distribution.png"),
    )
    print(f"  Saved: {OUTDIR / 'degree_distribution.png'}")

    print("\nDone.  All synthetic plots in:", OUTDIR)


if __name__ == "__main__":
    main()
