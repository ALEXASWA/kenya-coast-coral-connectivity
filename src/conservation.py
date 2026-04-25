"""
conservation.py
===============
Rank reef patches along the Kenya coast for marine conservation prioritisation
and identify the top-10 candidates for Marine Protected Area (MPA) designation.

Three complementary roles are scored and combined:

1. **Source strength** – reefs that export many larvae to other reefs are
   critical nurseries.  Measured by weighted out-degree and PageRank.

2. **Stepping-stone importance** – reefs that connect otherwise isolated
   sections of the network are irreplaceable corridors.  Measured by
   betweenness centrality.

3. **Influential hub** – reefs that are well-connected to other well-connected
   reefs amplify network-wide larval exchange.  Measured by eigenvector
   centrality and closeness centrality.

The three role scores are min-max normalised to [0, 1] and combined into a
single composite score using user-defined weights (default: equal weighting).

Public API
----------
source_strength_score(G)       -> dict[str, float]
stepping_stone_score(G)        -> dict[str, float]
influential_hub_score(G)       -> dict[str, float]
composite_mpa_score(G, ...)    -> pd.DataFrame
top_priority_reefs(G, n=10, .) -> pd.DataFrame
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import networkx as nx

from src.graph_metrics import centrality_metrics, degree_metrics


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _minmax_normalise(d: dict) -> dict[str, float]:
    """Min-max normalise values in a dictionary to [0, 1]."""
    vals = np.array(list(d.values()), dtype=float)
    lo, hi = vals.min(), vals.max()
    if hi == lo:
        return {k: 0.5 for k in d}
    return {k: float((v - lo) / (hi - lo)) for k, v in d.items()}


# ---------------------------------------------------------------------------
# Role scores
# ---------------------------------------------------------------------------

def source_strength_score(G: nx.DiGraph) -> dict[str, float]:
    """Score each reef patch by its larval-export (source) strength.

    Combines weighted out-degree (direct export capacity) and PageRank
    (flow-based importance as a source in the network).

    Parameters
    ----------
    G : nx.DiGraph

    Returns
    -------
    dict  {node: score in [0, 1]}
    """
    out_deg  = dict(G.out_degree(weight="weight"))
    pagerank = nx.pagerank(G, weight="weight", alpha=0.85)

    norm_out = _minmax_normalise(out_deg)
    norm_pr  = _minmax_normalise(pagerank)

    nodes = list(G.nodes())
    combined = {n: 0.6 * norm_out.get(n, 0) + 0.4 * norm_pr.get(n, 0)
                for n in nodes}
    return _minmax_normalise(combined)


def stepping_stone_score(G: nx.DiGraph) -> dict[str, float]:
    """Score each reef patch by its stepping-stone (corridor) importance.

    Uses betweenness centrality: how often a node appears on shortest paths
    between all other node pairs, indicating bridging roles.

    Parameters
    ----------
    G : nx.DiGraph

    Returns
    -------
    dict  {node: score in [0, 1]}
    """
    # Ensure distance attribute is present
    for u, v, data in G.edges(data=True):
        w = data.get("weight", 1.0)
        data["distance"] = 1.0 / w if w > 0 else float("inf")

    betweenness = nx.betweenness_centrality(G, weight="distance", normalized=True)
    return _minmax_normalise(betweenness)


def influential_hub_score(G: nx.DiGraph) -> dict[str, float]:
    """Score each reef patch by its hub influence in the network.

    Combines eigenvector centrality (connection to well-connected reefs) and
    closeness centrality (proximity to all other reefs).

    Parameters
    ----------
    G : nx.DiGraph

    Returns
    -------
    dict  {node: score in [0, 1]}
    """
    try:
        eigen = nx.eigenvector_centrality_numpy(G, weight="weight")
    except Exception:
        try:
            eigen = nx.eigenvector_centrality(G, weight="weight",
                                               max_iter=1000, tol=1e-6)
        except Exception:
            eigen = {n: 0.0 for n in G.nodes()}

    # Ensure distance attribute is present
    for u, v, data in G.edges(data=True):
        w = data.get("weight", 1.0)
        data["distance"] = 1.0 / w if w > 0 else float("inf")

    closeness = nx.closeness_centrality(G.to_undirected(), distance="distance")

    norm_e = _minmax_normalise(eigen)
    norm_c = _minmax_normalise(closeness)

    nodes = list(G.nodes())
    combined = {n: 0.6 * norm_e.get(n, 0) + 0.4 * norm_c.get(n, 0)
                for n in nodes}
    return _minmax_normalise(combined)


# ---------------------------------------------------------------------------
# Composite scoring
# ---------------------------------------------------------------------------

def composite_mpa_score(
    G: nx.DiGraph,
    w_source: float = 1.0,
    w_stepping: float = 1.0,
    w_hub: float = 1.0,
) -> pd.DataFrame:
    """Compute composite MPA priority scores for all reef patches.

    Parameters
    ----------
    G           : Directed connectivity graph.
    w_source    : Weight for source-strength score (default 1.0).
    w_stepping  : Weight for stepping-stone score (default 1.0).
    w_hub       : Weight for hub-influence score (default 1.0).

    Returns
    -------
    pd.DataFrame
        One row per reef patch, columns:
        source_score, stepping_stone_score, hub_score, composite_score.
        Sorted by composite_score descending.
    """
    src   = source_strength_score(G)
    step  = stepping_stone_score(G)
    hub   = influential_hub_score(G)

    total_w = w_source + w_stepping + w_hub
    nodes = list(G.nodes())

    records = []
    for n in nodes:
        s  = src.get(n, 0.0)
        st = step.get(n, 0.0)
        h  = hub.get(n, 0.0)
        composite = (w_source * s + w_stepping * st + w_hub * h) / total_w
        records.append({
            "reef_patch":          n,
            "source_score":        round(s,  4),
            "stepping_stone_score": round(st, 4),
            "hub_score":           round(h,  4),
            "composite_score":     round(composite, 4),
        })

    df = pd.DataFrame(records).set_index("reef_patch")
    df = df.sort_values("composite_score", ascending=False)
    return df


def top_priority_reefs(
    G: nx.DiGraph,
    n: int = 10,
    w_source: float = 1.0,
    w_stepping: float = 1.0,
    w_hub: float = 1.0,
) -> pd.DataFrame:
    """Identify the top-N reef patches recommended for MPA designation.

    Parameters
    ----------
    G          : Directed connectivity graph.
    n          : Number of priority reefs to return (default 10).
    w_source   : Weight for source-strength criterion.
    w_stepping : Weight for stepping-stone criterion.
    w_hub      : Weight for hub-influence criterion.

    Returns
    -------
    pd.DataFrame  – top-N rows from composite_mpa_score, with an added
    'priority_rank' column (1 = most important).
    """
    df = composite_mpa_score(G, w_source=w_source,
                              w_stepping=w_stepping, w_hub=w_hub)
    top = df.head(n).copy()
    top.insert(0, "priority_rank", range(1, len(top) + 1))
    return top
