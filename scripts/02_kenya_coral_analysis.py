#!/usr/bin/env python3
"""
02_kenya_coral_analysis.py
==========================
Full graph-theory analysis of the Kenya coast coral reef connectivity
network using real (or realistically synthesised) larval-dispersal data.

The script loads  data/kenya_coral_connectivity.csv, builds a directed
weighted graph, computes all metrics, and saves publication-quality plots
to  plots/kenya/.

Usage
-----
    python scripts/02_kenya_coral_analysis.py [--data PATH_TO_CSV]

If no --data argument is given, the default  data/kenya_coral_connectivity.csv
is used.

Output
------
plots/kenya/
    network_overview.png
    connectivity_heatmap.png
    community_structure.png
    bar_<metric>.png   (7 bar charts)
    degree_distribution.png
metrics_kenya.csv       ← full node-metric table
"""

import sys
import argparse
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")

from src.data_loader    import load_connectivity_csv
from src.graph_metrics  import summary_dataframe, community_detection, clustering_metrics
from src.visualization  import (
    plot_network,
    plot_connectivity_heatmap,
    plot_metric_bars,
    plot_community_network,
    plot_degree_distribution,
)

OUTDIR = ROOT / "plots" / "kenya"
OUTDIR.mkdir(parents=True, exist_ok=True)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Graph-theory analysis of Kenya coast coral connectivity."
    )
    parser.add_argument(
        "--data",
        default=str(ROOT / "data" / "kenya_coral_connectivity.csv"),
        help="Path to connectivity matrix CSV (default: data/kenya_coral_connectivity.csv)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 65)
    print("  KENYA COAST CORAL CONNECTIVITY – FULL GRAPH ANALYSIS")
    print("=" * 65)

    # -----------------------------------------------------------------------
    # 1.  Load data
    # -----------------------------------------------------------------------
    print(f"\nLoading connectivity matrix from: {args.data}")
    df_conn, G = load_connectivity_csv(args.data)
    print(f"Reef patches : {G.number_of_nodes()}")
    print(f"Directed edges (non-zero connections): {G.number_of_edges()}")

    # -----------------------------------------------------------------------
    # 2.  Compute metrics
    # -----------------------------------------------------------------------
    print("\nComputing graph-theory metrics …")
    df_metrics = summary_dataframe(G)

    clust = clustering_metrics(G)
    partition = community_detection(G)
    n_comm = len(set(partition.values()))

    print("\n── Node-level metrics ──────────────────────────────────────────")
    pd.set_option("display.float_format", "{:.4f}".format)
    pd.set_option("display.max_rows", 30)
    print(df_metrics.to_string())

    print(f"\nGlobal transitivity: {clust['global_transitivity']:.4f}")
    print(f"Communities detected: {n_comm}")
    for comm_id in sorted(set(partition.values())):
        members = [n for n, c in partition.items() if c == comm_id]
        print(f"  Community {comm_id}: {', '.join(members)}")

    # Save metrics CSV
    metrics_path = ROOT / "metrics_kenya.csv"
    df_metrics.to_csv(metrics_path)
    print(f"\nMetrics saved to: {metrics_path}")

    # -----------------------------------------------------------------------
    # 3.  Plots
    # -----------------------------------------------------------------------
    print("\nGenerating plots …")

    # 3a.  Connectivity heatmap
    plot_connectivity_heatmap(
        df_conn,
        title="Kenya Coast Coral Connectivity Matrix",
        save_path=str(OUTDIR / "connectivity_heatmap.png"),
    )
    print(f"  Saved: {OUTDIR / 'connectivity_heatmap.png'}")

    # 3b.  Network overview (size = out-degree, colour = betweenness)
    plot_network(
        G,
        node_size_metric=dict(G.out_degree(weight="weight")),
        title=(
            "Kenya Coast Coral Connectivity Network\n"
            "(node size = out-degree strength, colour = betweenness centrality)"
        ),
        layout="spring",
        save_path=str(OUTDIR / "network_overview.png"),
    )
    print(f"  Saved: {OUTDIR / 'network_overview.png'}")

    # 3c.  Community structure
    plot_community_network(
        G, partition,
        title="Kenya Coast – Community Structure (Louvain)",
        layout="spring",
        save_path=str(OUTDIR / "community_structure.png"),
    )
    print(f"  Saved: {OUTDIR / 'community_structure.png'}")

    # 3d.  Metric bar charts
    for metric in ["out_degree", "in_degree", "betweenness",
                   "closeness", "eigenvector", "pagerank", "local_clustering"]:
        plot_metric_bars(
            df_metrics, metric,
            title=f"Kenya Coast – {metric.replace('_', ' ').title()}",
            save_path=str(OUTDIR / f"bar_{metric}.png"),
        )
        print(f"  Saved: {OUTDIR / f'bar_{metric}.png'}")

    # 3e.  Degree distribution
    plot_degree_distribution(
        G,
        title="Kenya Coast – Degree Distribution",
        save_path=str(OUTDIR / "degree_distribution.png"),
    )
    print(f"  Saved: {OUTDIR / 'degree_distribution.png'}")

    print("\nDone.  All Kenya plots in:", OUTDIR)


if __name__ == "__main__":
    main()
