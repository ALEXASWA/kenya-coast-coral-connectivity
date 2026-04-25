#!/usr/bin/env python3
"""
03_priority_mpa_ranking.py
==========================
Rank all Kenya coast reef patches and identify the top-10 candidates for
Marine Protected Area (MPA) designation using three complementary criteria:

  1. Source strength    – larval-export capacity (out-degree + PageRank)
  2. Stepping-stone     – network-bridging importance (betweenness centrality)
  3. Influential hub    – connection to well-connected reefs
                          (eigenvector + closeness centrality)

Usage
-----
    python scripts/03_priority_mpa_ranking.py [--data PATH] [--top N]
                                               [--w-source W]
                                               [--w-stepping W]
                                               [--w-hub W]

Examples
--------
    # Default equal weights, top-10
    python scripts/03_priority_mpa_ranking.py

    # Emphasise source strength, top-5
    python scripts/03_priority_mpa_ranking.py --w-source 2.0 --top 5

Output
------
plots/conservation/
    mpa_priority_ranking.png
    role_scores_heatmap.png
    top10_composite_bar.png
priority_reefs.csv  ← full ranking table
"""

import sys
import argparse
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from src.data_loader  import load_connectivity_csv
from src.conservation import composite_mpa_score, top_priority_reefs
from src.visualization import plot_network

OUTDIR = ROOT / "plots" / "conservation"
OUTDIR.mkdir(parents=True, exist_ok=True)


def parse_args():
    p = argparse.ArgumentParser(
        description="Rank Kenya reef patches for MPA prioritisation."
    )
    p.add_argument("--data",       default=str(ROOT / "data" / "kenya_coral_connectivity.csv"))
    p.add_argument("--top",        type=int,   default=10, help="Number of priority reefs")
    p.add_argument("--w-source",   type=float, default=1.0, help="Weight for source criterion")
    p.add_argument("--w-stepping", type=float, default=1.0, help="Weight for stepping-stone")
    p.add_argument("--w-hub",      type=float, default=1.0, help="Weight for hub criterion")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------

def plot_role_scores_heatmap(df_scores: pd.DataFrame,
                              save_path: str | None = None) -> plt.Figure:
    """Grouped bar chart showing all three role scores per reef patch."""
    try:
        import seaborn as sns
        _seaborn = True
    except ImportError:
        _seaborn = False

    cols = ["source_score", "stepping_stone_score", "hub_score"]
    fig, ax = plt.subplots(figsize=(14, 6))

    if _seaborn:
        df_melt = df_scores[cols].reset_index().melt(
            id_vars="reef_patch", var_name="criterion", value_name="score"
        )
        sns.barplot(data=df_melt, x="reef_patch", y="score",
                    hue="criterion", ax=ax, palette=["#2196F3", "#FF9800", "#4CAF50"])
    else:
        x = np.arange(len(df_scores))
        w = 0.25
        ax.bar(x - w, df_scores["source_score"],       width=w, label="Source",        color="#2196F3")
        ax.bar(x,     df_scores["stepping_stone_score"], width=w, label="Stepping-stone", color="#FF9800")
        ax.bar(x + w, df_scores["hub_score"],           width=w, label="Hub",            color="#4CAF50")
        ax.set_xticks(x)
        ax.set_xticklabels(df_scores.index, rotation=45, ha="right", fontsize=8)
        ax.legend(fontsize=9)

    ax.set_xlabel("Reef Patch", fontsize=11)
    ax.set_ylabel("Normalised Score [0–1]", fontsize=11)
    ax.set_title("MPA Conservation Role Scores by Reef Patch", fontsize=14, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_mpa_priority_network(G, top_df: pd.DataFrame,
                               title: str = "Top-10 Priority Reefs for MPAs",
                               save_path: str | None = None) -> plt.Figure:
    """Network plot highlighting the top-priority reef patches."""
    import networkx as nx

    priority_nodes = set(top_df.index)
    # Colour nodes: top-10 in gold, others in grey
    node_color_dict = {
        n: 1.0 if n in priority_nodes else 0.0
        for n in G.nodes()
    }
    fig = plot_network(
        G,
        node_size_metric=dict(G.out_degree(weight="weight")),
        node_color_metric=node_color_dict,
        title=title,
        layout="spring",
        cmap="RdYlGn",
        save_path=save_path,
    )
    return fig


def plot_top_composite_bar(top_df: pd.DataFrame,
                            save_path: str | None = None) -> plt.Figure:
    """Stacked bar chart of composite score components for top-N reefs."""
    cols = ["source_score", "stepping_stone_score", "hub_score"]
    colors = ["#2196F3", "#FF9800", "#4CAF50"]
    labels = ["Source strength", "Stepping-stone", "Hub influence"]

    fig, ax = plt.subplots(figsize=(12, 6))
    bottom = np.zeros(len(top_df))

    for col, color, label in zip(cols, colors, labels):
        vals = top_df[col].values
        ax.bar(range(len(top_df)), vals, bottom=bottom,
               color=color, label=label, edgecolor="white", linewidth=0.8)
        bottom += vals

    ax.set_xticks(range(len(top_df)))
    ax.set_xticklabels(
        [f"#{r}  {n}" for r, n in zip(top_df["priority_rank"], top_df.index)],
        rotation=45, ha="right", fontsize=9,
    )
    ax.set_ylabel("Normalised Score (stacked)", fontsize=11)
    ax.set_title(
        f"Top-{len(top_df)} Priority Reef Patches for MPA Designation",
        fontsize=14, fontweight="bold",
    )
    ax.legend(loc="upper right", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    print("=" * 65)
    print("  KENYA COAST CORAL REEFS – MPA PRIORITY RANKING")
    print("=" * 65)

    # Load connectivity
    print(f"\nLoading data from: {args.data}")
    _, G = load_connectivity_csv(args.data)
    print(f"Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Compute scores
    print("\nComputing conservation role scores …")
    df_all = composite_mpa_score(
        G,
        w_source=args.w_source,
        w_stepping=args.w_stepping,
        w_hub=args.w_hub,
    )

    top_df = top_priority_reefs(
        G, n=args.top,
        w_source=args.w_source,
        w_stepping=args.w_stepping,
        w_hub=args.w_hub,
    )

    # Print results
    print(f"\n── Top-{args.top} Priority Reefs for MPA Designation ────────────────")
    pd.set_option("display.float_format", "{:.4f}".format)
    print(top_df.to_string())

    print("\n── Full Ranking ──────────────────────────────────────────────────")
    print(df_all.to_string())

    # Save full ranking
    out_csv = ROOT / "priority_reefs.csv"
    df_all.to_csv(out_csv)
    print(f"\nFull ranking saved to: {out_csv}")

    # Plots
    print("\nGenerating conservation plots …")

    plot_role_scores_heatmap(
        df_all,
        save_path=str(OUTDIR / "role_scores_heatmap.png"),
    )
    print(f"  Saved: {OUTDIR / 'role_scores_heatmap.png'}")

    plot_top_composite_bar(
        top_df,
        save_path=str(OUTDIR / "top10_composite_bar.png"),
    )
    print(f"  Saved: {OUTDIR / 'top10_composite_bar.png'}")

    plot_mpa_priority_network(
        G, top_df,
        title=f"Top-{args.top} Priority Reefs for MPA Designation\n(green = priority, size = out-degree)",
        save_path=str(OUTDIR / "mpa_priority_ranking.png"),
    )
    print(f"  Saved: {OUTDIR / 'mpa_priority_ranking.png'}")

    print("\nDone.  All conservation plots in:", OUTDIR)


if __name__ == "__main__":
    main()
