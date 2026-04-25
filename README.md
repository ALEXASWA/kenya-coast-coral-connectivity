# Kenya Coast Coral Connectivity

Graph-theory analysis of ecological connectivity networks for reef patches along the Kenyan coast.
The project demonstrates methods on a small synthetic directed weighted network, then applies them
to a real-world larval-dispersal connectivity matrix covering **15 reef patches** from Malindi in the
north to Kisite-Mpunguti in the south.

---

## Table of Contents

1. [Project overview](#project-overview)
2. [Repository structure](#repository-structure)
3. [Quick start](#quick-start)
4. [Loading your own CSV connectivity data](#loading-your-own-csv-connectivity-data)
5. [Metrics computed](#metrics-computed)
6. [Conservation workflow – MPA ranking](#conservation-workflow--mpa-ranking)
7. [Sample outputs](#sample-outputs)
8. [Reproducing results](#reproducing-results)
9. [Dependencies](#dependencies)

---

## Project overview

Coral reefs along the Kenya coast are ecologically and economically vital, yet increasingly threatened
by climate change, overfishing, and coastal development.  Understanding **network connectivity** between
reef patches – how larvae move among reefs via ocean currents – is essential for designing effective
Marine Protected Area (MPA) networks.

This project provides:

* A **modular Python library** (`src/`) for graph-theory analysis of any directed weighted connectivity matrix
* A **10-node synthetic example** demonstrating every metric before touching real data
* A **Kenya coast connectivity dataset** (`data/kenya_coral_connectivity.csv`) with 15 reef patches
* **Three runnable scripts** covering: synthetic demo → full Kenya analysis → MPA priority ranking
* A **Jupyter notebook** combining all analyses in a single narrative document
* **Sample plots** in `plots/` generated from the scripts

---

## Repository structure

```
kenya-coast-coral-connectivity/
├── README.md
├── requirements.txt                  ← Python dependencies
│
├── data/
│   ├── kenya_coral_connectivity.csv  ← 15×15 Kenya reef connectivity matrix
│   └── synthetic_10node.csv          ← 10-node synthetic example matrix
│
├── src/                              ← Reusable Python modules
│   ├── __init__.py
│   ├── data_loader.py                ← Load CSV → NetworkX DiGraph
│   ├── graph_metrics.py              ← Degree, centrality, clustering, communities
│   ├── visualization.py              ← Network plots, heatmaps, bar charts
│   └── conservation.py              ← MPA scoring and ranking
│
├── scripts/
│   ├── 01_synthetic_network.py       ← Demo on synthetic 10-node graph
│   ├── 02_kenya_coral_analysis.py    ← Full Kenya coast analysis
│   └── 03_priority_mpa_ranking.py   ← Identify top-10 MPA candidates
│
├── notebooks/
│   └── kenya_coral_connectivity_analysis.ipynb  ← Interactive notebook
│
├── plots/                            ← Generated sample plots
│   ├── synthetic/
│   ├── kenya/
│   └── conservation/
│
├── metrics_kenya.csv                 ← Node-level metrics for all reef patches
└── priority_reefs.csv                ← Full MPA priority ranking
```

---

## Quick start

### 1. Clone and install dependencies

```bash
git clone https://github.com/ALEXASWA/kenya-coast-coral-connectivity.git
cd kenya-coast-coral-connectivity
pip install -r requirements.txt
```

### 2. Run the synthetic demonstration

```bash
python scripts/01_synthetic_network.py
```

Computes all metrics on a 10-node synthetic graph and saves plots to `plots/synthetic/`.

### 3. Run the full Kenya coast analysis

```bash
python scripts/02_kenya_coral_analysis.py
```

Loads `data/kenya_coral_connectivity.csv`, computes all graph-theory metrics, and saves
plots to `plots/kenya/` plus a `metrics_kenya.csv` table.

### 4. Identify priority reefs for MPAs

```bash
python scripts/03_priority_mpa_ranking.py
```

Ranks all 15 reef patches and prints the top-10 MPA candidates.  Saves plots to
`plots/conservation/` and the full ranking to `priority_reefs.csv`.

**Optional flags:**

```bash
# Emphasise source-strength criterion, top-5 reefs
python scripts/03_priority_mpa_ranking.py --w-source 2.0 --top 5

# Use a custom connectivity CSV
python scripts/03_priority_mpa_ranking.py --data /path/to/your_matrix.csv
```

### 5. Explore the notebook

```bash
jupyter lab notebooks/kenya_coral_connectivity_analysis.ipynb
```

---

## Loading your own CSV connectivity data

Prepare your connectivity matrix as a **square CSV** with the same node names as both row and column
headers.  Cell `[i, j]` is the edge weight from reef `i` (source) to reef `j` (destination).
Zero or missing values mean no connection.

```
,Reef_A,Reef_B,Reef_C
Reef_A,0,0.5,0.1
Reef_B,0,0,0.3
Reef_C,0.2,0,0
```

Then run:

```python
from src.data_loader import load_connectivity_csv
df, G = load_connectivity_csv("path/to/your_matrix.csv")
```

Or pass it directly to any script:

```bash
python scripts/02_kenya_coral_analysis.py --data path/to/your_matrix.csv
python scripts/03_priority_mpa_ranking.py --data path/to/your_matrix.csv
```

---

## Metrics computed

| Metric | Function | Ecological interpretation |
|---|---|---|
| **Weighted out-degree** | `degree_metrics()` | Total larval-export strength |
| **Weighted in-degree** | `degree_metrics()` | Total larval-import strength |
| **Betweenness centrality** | `centrality_metrics()` | Stepping-stone / corridor role |
| **Closeness centrality** | `centrality_metrics()` | Accessibility to the whole network |
| **Eigenvector centrality** | `centrality_metrics()` | Hub influence (connection to well-connected reefs) |
| **PageRank** | `centrality_metrics()` | Flow-based larval-source prestige |
| **Local clustering coeff.** | `clustering_metrics()` | Local neighbourhood density |
| **Global transitivity** | `clustering_metrics()` | Overall triangle fraction |
| **Community membership** | `community_detection()` | Reef clusters (Louvain algorithm) |

All functions are in `src/graph_metrics.py` and accept any `nx.DiGraph`.

---

## Conservation workflow – MPA ranking

`src/conservation.py` implements a three-criterion composite scoring system:

| Role | Score | Metrics used |
|---|---|---|
| **Source strength** | `source_strength_score()` | Out-degree (60 %) + PageRank (40 %) |
| **Stepping-stone** | `stepping_stone_score()` | Betweenness centrality |
| **Hub influence** | `influential_hub_score()` | Eigenvector centrality (60 %) + Closeness (40 %) |

Each score is min-max normalised to [0, 1].  The composite score is a weighted average of the
three role scores (equal weights by default).

```python
from src.conservation import top_priority_reefs
top10 = top_priority_reefs(G, n=10, w_source=1.0, w_stepping=1.0, w_hub=1.0)
```

### Top-10 priority reefs (default equal weights)

| Rank | Reef patch | Composite score | Key roles |
|---|---|---|---|
| 1 | Mombasa_MNP | 0.98 | Source + stepping-stone + hub |
| 2 | Chale_Lagoon | 0.70 | Hub + source |
| 3 | Vipingo_Reef | 0.62 | Stepping-stone + source |
| 4 | Nyali_Reef | 0.61 | Hub + source |
| 5 | Gazi_Bay | 0.61 | Hub + source |
| 6 | Diani_Reef | 0.61 | Hub + source |
| 7 | Tiwi_Reef | 0.58 | Source + hub |
| 8 | Shimoni_Reef | 0.57 | Source + hub |
| 9 | Funzi_Bay | 0.52 | Hub + source |
| 10 | Kisite_Mpunguti_MNP | 0.42 | Hub |

---

## Sample outputs

### Kenya coast connectivity heatmap
`plots/kenya/connectivity_heatmap.png`

### Kenya coast network (betweenness centrality coloured)
`plots/kenya/network_overview.png`

### Community structure (Louvain)
`plots/kenya/community_structure.png`

### Top-10 MPA priority reefs (stacked bar)
`plots/conservation/top10_composite_bar.png`

---

## Generating the PowerPoint presentation

```bash
python scripts/generate_presentation.py
```

This produces `presentation.pptx` in the project root — a 19-slide widescreen (16:9) deck with:

| Slide | Content |
|---|---|
| 1 | Title slide |
| 2 | Project overview & objectives |
| 3 | Study area – Kenya reef patches |
| 4 | Methods & graph-metric definitions |
| 5–6 | Synthetic 10-node demonstration |
| 7–8 | Kenya connectivity heatmap & network |
| 9 | Louvain community structure |
| 10 | Degree distribution |
| 11–13 | Betweenness, eigenvector, out-degree & PageRank |
| 14 | MPA prioritisation workflow |
| 15–16 | Top-10 priority reefs table & bar chart |
| 17 | Conservation recommendations |
| 18 | Conclusions & next steps |
| 19 | References & acknowledgements |

Save to a custom path:
```bash
python scripts/generate_presentation.py --out /path/to/output.pptx
```

---

## Reproducing results

```bash
# Full pipeline in order
python scripts/01_synthetic_network.py   # synthetic demo
python scripts/02_kenya_coral_analysis.py  # Kenya metrics + plots
python scripts/03_priority_mpa_ranking.py  # MPA ranking
python scripts/generate_presentation.py   # generate PowerPoint deck
```

Or open the notebook for an interactive, narrated walkthrough:

```bash
jupyter lab notebooks/kenya_coral_connectivity_analysis.ipynb
```

---

## Dependencies

See `requirements.txt`.  Key packages:

| Package | Purpose |
|---|---|
| `networkx` | Graph construction and all centrality metrics |
| `python-louvain` | Louvain community detection |
| `numpy` / `pandas` | Numerical computation and DataFrames |
| `matplotlib` / `seaborn` | Plotting |
| `scipy` | Sparse linear algebra (eigenvector centrality) |
| `python-pptx` | PowerPoint presentation generation |
| `notebook` / `jupyterlab` | Interactive notebook environment |


Install with:
```bash
pip install -r requirements.txt
```
