"""
visualization.py
================
Plotting utilities for the Kenya coast coral connectivity project.

All functions accept a matplotlib Axes (or None to create a new figure) and
return the Figure so that callers can save or display it.

Public API
----------
plot_network(G, metrics, ...)      -> plt.Figure
plot_connectivity_heatmap(df, ...) -> plt.Figure
plot_metric_bars(df, metric, ...)  -> plt.Figure
plot_community_network(G, partition, ...) -> plt.Figure
plot_degree_distribution(G, ...)   -> plt.Figure
"""

from __future__ import annotations

import warnings
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors

# Set the Agg (non-interactive) backend only when running outside an
# interactive environment.  In Jupyter notebooks the backend is already
# configured before this module is imported, so the guard below avoids
# overriding it.  When running as a plain script the MPLBACKEND variable or
# a prior matplotlib.use() call may also pre-select a backend.
import sys as _sys
_in_notebook = "ipykernel" in _sys.modules or "IPython" in _sys.modules
if not _in_notebook:
    matplotlib.use("Agg")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_KENYA_PALETTE = [
    "#e41a1c", "#377eb8", "#4daf4a", "#984ea3",
    "#ff7f00", "#a65628", "#f781bf", "#999999",
    "#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3",
]


def _scale(values: dict, lo: float = 200, hi: float = 2000) -> list[float]:
    """Min-max scale a dict of values to the range [lo, hi] for node sizing."""
    vals = np.array(list(values.values()), dtype=float)
    vmin, vmax = vals.min(), vals.max()
    if vmax == vmin:
        return [lo + (hi - lo) / 2] * len(vals)
    scaled = lo + (vals - vmin) / (vmax - vmin) * (hi - lo)
    return scaled.tolist()


def _node_positions(G: nx.DiGraph, layout: str = "spring") -> dict:
    """Return node positions using the requested layout algorithm."""
    if layout == "circular":
        return nx.circular_layout(G)
    elif layout == "kamada_kawai":
        try:
            return nx.kamada_kawai_layout(G, weight="weight")
        except Exception:
            return nx.spring_layout(G, seed=42)
    else:  # default: spring
        return nx.spring_layout(G, seed=42, weight="weight")


# ---------------------------------------------------------------------------
# Main plotting functions
# ---------------------------------------------------------------------------

def plot_network(
    G: nx.DiGraph,
    node_size_metric: dict | None = None,
    node_color_metric: dict | None = None,
    title: str = "Connectivity Network",
    layout: str = "spring",
    figsize: tuple[float, float] = (12, 9),
    cmap: str = "YlOrRd",
    color_label: str = "Node metric",
    save_path: str | None = None,
) -> plt.Figure:
    """Draw the directed connectivity network.

    Parameters
    ----------
    G                 : Directed graph.
    node_size_metric  : dict {node: float} used to scale node sizes.
                        Defaults to out-degree.
    node_color_metric : dict {node: float} used to colour nodes.
                        Defaults to betweenness centrality.
    title             : Plot title.
    layout            : One of 'spring', 'circular', 'kamada_kawai'.
    figsize           : (width, height) in inches.
    cmap              : Matplotlib colourmap name.
    color_label       : Label for the colour-bar (describes node_color_metric).
    save_path         : If given, the figure is saved to this path.

    Returns
    -------
    plt.Figure
    """
    if node_size_metric is None:
        node_size_metric = dict(G.out_degree(weight="weight"))
    if node_color_metric is None:
        node_color_metric = nx.betweenness_centrality(G, weight="distance",
                                                       normalized=True)
        color_label = "Betweenness centrality"

    pos = _node_positions(G, layout)
    nodes = list(G.nodes())

    sizes  = _scale(node_size_metric)
    # Reorder to match G.nodes()
    size_map  = dict(zip(node_size_metric.keys(), sizes))
    node_sizes = [size_map.get(n, 300) for n in nodes]
    node_vals  = [node_color_metric.get(n, 0.0) for n in nodes]

    edge_weights = [G[u][v].get("weight", 1.0) for u, v in G.edges()]
    max_w = max(edge_weights) if edge_weights else 1.0
    edge_widths = [0.5 + 3.5 * (w / max_w) for w in edge_weights]

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor("#f0f4f8")
    fig.patch.set_facecolor("#f0f4f8")

    norm = mcolors.Normalize(vmin=min(node_vals), vmax=max(node_vals))
    colormap = cm.get_cmap(cmap)
    node_colors = [colormap(norm(v)) for v in node_vals]

    nx.draw_networkx_edges(
        G, pos, ax=ax,
        width=edge_widths, alpha=0.55,
        edge_color="steelblue",
        arrows=True,
        arrowsize=15,
        connectionstyle="arc3,rad=0.1",
    )
    nc = nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_size=node_sizes,
        node_color=node_colors,
        alpha=0.92,
    )
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=8, font_weight="bold")

    sm = cm.ScalarMappable(cmap=colormap, norm=norm)
    sm.set_array([])
    plt.colorbar(sm, ax=ax, label=color_label, shrink=0.75)

    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.axis("off")
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_connectivity_heatmap(
    df: pd.DataFrame,
    title: str = "Connectivity Matrix",
    figsize: tuple[float, float] = (12, 10),
    cmap: str = "Blues",
    save_path: str | None = None,
) -> plt.Figure:
    """Draw a heatmap of the connectivity matrix.

    Parameters
    ----------
    df        : Square connectivity DataFrame (sources × destinations).
    title     : Plot title.
    figsize   : Figure size in inches.
    cmap      : Matplotlib colourmap.
    save_path : Optional path to save the figure.

    Returns
    -------
    plt.Figure
    """
    try:
        import seaborn as sns
        _seaborn = True
    except ImportError:
        _seaborn = False

    fig, ax = plt.subplots(figsize=figsize)

    if _seaborn:
        sns.heatmap(
            df, ax=ax, cmap=cmap, linewidths=0.3, linecolor="white",
            annot=(len(df) <= 12), fmt=".2f",
            cbar_kws={"label": "Connectivity weight"},
        )
    else:
        im = ax.imshow(df.values, cmap=cmap, aspect="auto")
        ax.set_xticks(range(len(df.columns)))
        ax.set_xticklabels(df.columns, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(df.index)))
        ax.set_yticklabels(df.index, fontsize=8)
        plt.colorbar(im, ax=ax, label="Connectivity weight")

    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Destination (sink)", fontsize=11)
    ax.set_ylabel("Source", fontsize=11)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_metric_bars(
    df: pd.DataFrame,
    metric: str,
    title: str | None = None,
    top_n: int | None = None,
    figsize: tuple[float, float] = (12, 6),
    color: str = "#2196F3",
    save_path: str | None = None,
) -> plt.Figure:
    """Bar chart for any scalar metric column in the summary DataFrame.

    Parameters
    ----------
    df       : Summary DataFrame with reef patches as index.
    metric   : Column name to plot.
    title    : Plot title (auto-generated if None).
    top_n    : Show only the top-N nodes.
    figsize  : Figure size.
    color    : Bar colour.
    save_path: Optional save path.

    Returns
    -------
    plt.Figure
    """
    series = df[metric].dropna().sort_values(ascending=False)
    if top_n is not None:
        series = series.head(top_n)

    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.bar(range(len(series)), series.values, color=color,
                  edgecolor="white", linewidth=0.8)
    ax.set_xticks(range(len(series)))
    ax.set_xticklabels(series.index, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel(metric.replace("_", " ").title(), fontsize=11)
    ax.set_title(title or f"{metric.replace('_', ' ').title()} by Reef Patch",
                 fontsize=14, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_community_network(
    G: nx.DiGraph,
    partition: dict[str, int],
    title: str = "Community Structure",
    layout: str = "spring",
    figsize: tuple[float, float] = (12, 9),
    save_path: str | None = None,
) -> plt.Figure:
    """Draw the network with nodes coloured by community membership.

    Parameters
    ----------
    G         : Directed graph.
    partition : {node: community_id} mapping.
    title     : Plot title.
    layout    : Layout algorithm.
    figsize   : Figure size.
    save_path : Optional save path.

    Returns
    -------
    plt.Figure
    """
    pos = _node_positions(G, layout)
    communities = sorted(set(partition.values()))
    color_map = {c: _KENYA_PALETTE[i % len(_KENYA_PALETTE)]
                 for i, c in enumerate(communities)}

    node_colors = [color_map[partition[n]] for n in G.nodes()]
    out_deg = dict(G.out_degree(weight="weight"))
    node_sizes = _scale(out_deg, 300, 2000)
    size_list = [node_sizes[list(G.nodes()).index(n)] for n in G.nodes()]

    edge_weights = [G[u][v].get("weight", 1.0) for u, v in G.edges()]
    max_w = max(edge_weights) if edge_weights else 1.0
    edge_widths = [0.4 + 3.0 * (w / max_w) for w in edge_weights]

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor("#f0f4f8")
    fig.patch.set_facecolor("#f0f4f8")

    nx.draw_networkx_edges(
        G, pos, ax=ax, width=edge_widths, alpha=0.45,
        edge_color="#888888", arrows=True, arrowsize=14,
        connectionstyle="arc3,rad=0.1",
    )
    nx.draw_networkx_nodes(
        G, pos, ax=ax, node_color=node_colors, node_size=size_list, alpha=0.9
    )
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=8, font_weight="bold")

    # Legend
    handles = [
        matplotlib.patches.Patch(color=color_map[c], label=f"Community {c}")
        for c in communities
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=9,
              framealpha=0.85, title="Communities")

    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.axis("off")
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_degree_distribution(
    G: nx.DiGraph,
    title: str = "Degree Distribution",
    figsize: tuple[float, float] = (10, 5),
    save_path: str | None = None,
) -> plt.Figure:
    """Plot in-degree and out-degree distributions side by side.

    Parameters
    ----------
    G         : Directed graph.
    title     : Super-title for both panels.
    figsize   : Figure size.
    save_path : Optional save path.

    Returns
    -------
    plt.Figure
    """
    in_degrees  = [d for _, d in G.in_degree(weight="weight")]
    out_degrees = [d for _, d in G.out_degree(weight="weight")]

    fig, axes = plt.subplots(1, 2, figsize=figsize)
    for ax, data, label, color in zip(
        axes,
        [in_degrees, out_degrees],
        ["Weighted In-Degree", "Weighted Out-Degree"],
        ["#2196F3", "#FF5722"],
    ):
        n_bins = max(5, len(data) // 2)
        ax.hist(data, bins=n_bins, color=color, edgecolor="white", alpha=0.85)
        ax.set_xlabel(label, fontsize=10)
        ax.set_ylabel("Count", fontsize=10)
        ax.set_title(label, fontsize=11)
        ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig
