"""
graph_metrics.py
================
Compute a comprehensive suite of graph-theory metrics on a directed weighted
NetworkX graph.

Metrics covered
---------------
* Weighted in-degree and out-degree (node-level)
* Betweenness centrality (node and edge)
* Closeness centrality
* Eigenvector centrality
* PageRank (a flow-based prestige measure useful for larval-source ranking)
* Local clustering coefficient and global transitivity
* Community detection (Louvain algorithm on the undirected projection)

All node-level metrics are returned as dictionaries {node_label: value} so
they are easy to inspect and combine into a summary DataFrame.

Public API
----------
compute_all_metrics(G)  -> dict[str, dict]
degree_metrics(G)       -> dict[str, dict]
centrality_metrics(G)   -> dict[str, dict]
clustering_metrics(G)   -> dict[str, dict]
community_detection(G)  -> dict[str, int]
summary_dataframe(G)    -> pd.DataFrame
"""

import warnings
import numpy as np
import pandas as pd
import networkx as nx

# community detection – try python-louvain first, fall back to greedy modularity
try:
    import community as community_louvain  # python-louvain package
    _LOUVAIN_AVAILABLE = True
except ImportError:
    _LOUVAIN_AVAILABLE = False


# ---------------------------------------------------------------------------
# Individual metric functions
# ---------------------------------------------------------------------------

def degree_metrics(G: nx.DiGraph) -> dict[str, dict]:
    """Return weighted in-degree and out-degree for every node.

    For an unweighted graph the weight is treated as 1.

    Parameters
    ----------
    G : nx.DiGraph

    Returns
    -------
    dict with keys:
        'in_degree'  : {node: weighted in-degree}
        'out_degree' : {node: weighted out-degree}
    """
    in_deg  = dict(G.in_degree(weight="weight"))
    out_deg = dict(G.out_degree(weight="weight"))
    return {"in_degree": in_deg, "out_degree": out_deg}


def centrality_metrics(G: nx.DiGraph) -> dict[str, dict]:
    """Compute betweenness, closeness, eigenvector centrality, and PageRank.

    Betweenness and closeness use the *distance* interpretation of weights
    (lower weight = shorter path).  For connectivity matrices where a higher
    weight represents *stronger* connection, we convert weights to distances
    via distance = 1 / weight.

    Parameters
    ----------
    G : nx.DiGraph

    Returns
    -------
    dict with keys:
        'betweenness'  : {node: betweenness centrality}
        'closeness'    : {node: closeness centrality}
        'eigenvector'  : {node: eigenvector centrality}
        'pagerank'     : {node: PageRank}
    """
    # Assign distance attribute (inverse of weight) to each edge
    for u, v, data in G.edges(data=True):
        w = data.get("weight", 1.0)
        data["distance"] = 1.0 / w if w > 0 else float("inf")

    # --- Betweenness centrality ---
    betweenness = nx.betweenness_centrality(G, weight="distance", normalized=True)

    # --- Closeness centrality ---
    # nx.closeness_centrality on DiGraph uses in-edges by default;
    # we use the undirected version of the graph to get a symmetric measure.
    closeness = nx.closeness_centrality(G.to_undirected(), distance="distance")

    # --- Eigenvector centrality ---
    try:
        eigenvector = nx.eigenvector_centrality_numpy(G, weight="weight")
    except nx.exception.NetworkXException:
        warnings.warn(
            "eigenvector_centrality_numpy failed; falling back to power-iteration.",
            RuntimeWarning,
        )
        try:
            eigenvector = nx.eigenvector_centrality(
                G, weight="weight", max_iter=1000, tol=1e-6
            )
        except nx.exception.PowerIterationFailedConvergence:
            eigenvector = {n: float("nan") for n in G.nodes()}

    # --- PageRank ---
    pagerank = nx.pagerank(G, weight="weight", alpha=0.85)

    return {
        "betweenness": betweenness,
        "closeness":   closeness,
        "eigenvector": eigenvector,
        "pagerank":    pagerank,
    }


def clustering_metrics(G: nx.DiGraph) -> dict[str, object]:
    """Compute local clustering coefficients and global transitivity.

    Uses the undirected projection of *G* to obtain the classic triangle-based
    measures, which are well-defined for both directed and undirected graphs.

    Parameters
    ----------
    G : nx.DiGraph

    Returns
    -------
    dict with keys:
        'local_clustering'  : {node: clustering coefficient}
        'global_transitivity': float
    """
    U = G.to_undirected()
    local_clust = nx.clustering(U, weight="weight")
    global_trans = nx.transitivity(U)
    return {
        "local_clustering": local_clust,
        "global_transitivity": global_trans,
    }


def community_detection(G: nx.DiGraph) -> dict[str, int]:
    """Detect communities using the Louvain algorithm (or greedy modularity as
    a fallback) on the undirected projection of *G*.

    Parameters
    ----------
    G : nx.DiGraph

    Returns
    -------
    dict  {node: community_id}
    """
    U = G.to_undirected()

    if _LOUVAIN_AVAILABLE:
        # python-louvain: best_partition returns {node: community_int}
        partition = community_louvain.best_partition(U, weight="weight", random_state=42)
    else:
        # Fallback: networkx greedy modularity communities
        communities_gen = nx.community.greedy_modularity_communities(U, weight="weight")
        partition = {}
        for comm_id, comm_nodes in enumerate(communities_gen):
            for node in comm_nodes:
                partition[node] = comm_id

    return partition


# ---------------------------------------------------------------------------
# Aggregate helpers
# ---------------------------------------------------------------------------

def compute_all_metrics(G: nx.DiGraph) -> dict[str, object]:
    """Compute and return all graph metrics in a single call.

    Parameters
    ----------
    G : nx.DiGraph

    Returns
    -------
    dict with keys:
        'in_degree', 'out_degree',
        'betweenness', 'closeness', 'eigenvector', 'pagerank',
        'local_clustering', 'global_transitivity',
        'community'
    """
    metrics = {}
    metrics.update(degree_metrics(G))
    metrics.update(centrality_metrics(G))
    clust = clustering_metrics(G)
    metrics["local_clustering"]   = clust["local_clustering"]
    metrics["global_transitivity"] = clust["global_transitivity"]
    metrics["community"] = community_detection(G)
    return metrics


def summary_dataframe(G: nx.DiGraph) -> pd.DataFrame:
    """Build a tidy DataFrame with one row per node and one column per metric.

    Parameters
    ----------
    G : nx.DiGraph

    Returns
    -------
    pd.DataFrame  indexed by node label, sorted by out_degree descending.
    """
    m = compute_all_metrics(G)

    node_metrics = {
        "in_degree":        m["in_degree"],
        "out_degree":       m["out_degree"],
        "betweenness":      m["betweenness"],
        "closeness":        m["closeness"],
        "eigenvector":      m["eigenvector"],
        "pagerank":         m["pagerank"],
        "local_clustering": m["local_clustering"],
        "community":        m["community"],
    }

    df = pd.DataFrame(node_metrics)
    df.index.name = "reef_patch"
    df = df.sort_values("out_degree", ascending=False)
    return df
