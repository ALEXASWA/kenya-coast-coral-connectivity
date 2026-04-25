"""
data_loader.py
==============
Utilities for reading connectivity matrices stored as CSV files and converting
them into NetworkX directed, weighted graphs.

CSV format expected
-------------------
A square matrix where both row and column headers are node (reef patch) names.
Rows are *sources* and columns are *destinations*.  A non-zero value at
[row i, col j] means there is a directed edge i → j with that weight.

Example (3-node system):
    ,NodeA,NodeB,NodeC
    NodeA,0,0.5,0.1
    NodeB,0,0,0.3
    NodeC,0.2,0,0

Public API
----------
load_connectivity_csv(path)          -> (pd.DataFrame, nx.DiGraph)
build_graph_from_dataframe(df)       -> nx.DiGraph
synthetic_10node_graph()             -> nx.DiGraph
"""

import pathlib
import numpy as np
import pandas as pd
import networkx as nx


# ---------------------------------------------------------------------------
# CSV loading helpers
# ---------------------------------------------------------------------------

def load_connectivity_csv(path: str | pathlib.Path) -> tuple[pd.DataFrame, nx.DiGraph]:
    """Load a connectivity matrix CSV and return both the DataFrame and a
    directed NetworkX graph.

    Parameters
    ----------
    path : str or Path
        File path to the CSV connectivity matrix.

    Returns
    -------
    df : pd.DataFrame
        The raw connectivity matrix (sources as rows, destinations as columns).
    G  : nx.DiGraph
        Directed weighted graph built from *df*.
    """
    path = pathlib.Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Connectivity matrix not found: {path}")

    df = pd.read_csv(path, index_col=0)
    # Ensure row and column labels match
    if list(df.index) != list(df.columns):
        raise ValueError(
            "Row labels and column labels of the connectivity matrix must be identical "
            "and in the same order."
        )
    G = build_graph_from_dataframe(df)
    return df, G


def build_graph_from_dataframe(df: pd.DataFrame) -> nx.DiGraph:
    """Convert a square connectivity DataFrame to a directed NetworkX graph.

    Only edges with weight > 0 are added.

    Parameters
    ----------
    df : pd.DataFrame
        Square matrix; df.loc[src, dst] is the edge weight from *src* to *dst*.

    Returns
    -------
    nx.DiGraph
    """
    G = nx.DiGraph()
    G.add_nodes_from(df.index.tolist())

    for src in df.index:
        for dst in df.columns:
            w = float(df.loc[src, dst])
            if w > 0:
                G.add_edge(src, dst, weight=w)

    return G


# ---------------------------------------------------------------------------
# Synthetic 10-node network
# ---------------------------------------------------------------------------

def synthetic_10node_graph() -> nx.DiGraph:
    """Create a small, deterministic synthetic directed weighted graph with
    10 nodes to illustrate graph-theory methods before applying them to the
    real Kenya dataset.

    Node names are 'N0' through 'N9'.  Edge weights represent hypothetical
    larval dispersal probabilities (0–1).

    Returns
    -------
    nx.DiGraph
    """
    rng = np.random.default_rng(seed=42)

    nodes = [f"N{i}" for i in range(10)]
    G = nx.DiGraph()
    G.add_nodes_from(nodes)

    # Define a hand-crafted edge list that exhibits interesting topology:
    # two loosely connected communities, a bridge node, and a hub node.
    edges = [
        # Community A (N0–N4)
        ("N0", "N1", 0.8),
        ("N1", "N2", 0.6),
        ("N2", "N0", 0.4),
        ("N0", "N3", 0.5),
        ("N3", "N4", 0.7),
        ("N4", "N0", 0.3),
        # Community B (N5–N9)
        ("N5", "N6", 0.9),
        ("N6", "N7", 0.5),
        ("N7", "N8", 0.8),
        ("N8", "N9", 0.6),
        ("N9", "N5", 0.4),
        # Bridge / stepping-stone node N4 → N5
        ("N4", "N5", 0.2),
        # Hub node N2 connects broadly
        ("N2", "N5", 0.3),
        ("N2", "N7", 0.25),
        ("N6", "N2", 0.15),
        # A few reverse edges
        ("N8", "N3", 0.1),
        ("N9", "N1", 0.2),
    ]

    for src, dst, w in edges:
        G.add_edge(src, dst, weight=w)

    return G
