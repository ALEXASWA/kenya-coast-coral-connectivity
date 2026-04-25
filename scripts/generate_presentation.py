#!/usr/bin/env python3
"""
generate_presentation.py
========================
Generates a professional PowerPoint presentation (.pptx) for the
Kenya Coast Coral Connectivity graph-theory analysis project.

Usage
-----
    python scripts/generate_presentation.py [--out PATH]

The default output path is  presentation.pptx  in the project root.

Slide structure
---------------
 1. Title slide
 2. Project overview & objectives
 3. Study area – Kenya coast reef patches
 4. Data & methods overview
 5. Synthetic 10-node demo – network
 6. Synthetic 10-node demo – centrality metrics
 7. Kenya connectivity matrix (heatmap)
 8. Kenya reef network overview
 9. Community structure (Louvain)
10. Degree distribution
11. Betweenness centrality – stepping-stone reefs
12. Eigenvector & closeness centrality – hub reefs
13. Out-degree & PageRank – source reefs
14. MPA prioritisation workflow
15. Top-10 priority reefs – composite ranking
16. Top-10 priority reefs – stacked bar chart
17. Conservation recommendations
18. Conclusions & next steps
19. References & acknowledgements
"""

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ── python-pptx imports ──────────────────────────────────────────────────────
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt
import pptx.util as pptx_util

# ── std-lib / data ───────────────────────────────────────────────────────────
import csv
import io

# ---------------------------------------------------------------------------
# Brand colours (Kenya-ocean palette)
# ---------------------------------------------------------------------------
DEEP_OCEAN   = RGBColor(0x00, 0x4E, 0x7C)   # dark blue
CORAL_RED    = RGBColor(0xE8, 0x4C, 0x4C)   # coral red
REEF_GREEN   = RGBColor(0x2E, 0x86, 0x48)   # reef green
SAND         = RGBColor(0xF5, 0xE6, 0xCA)   # sandy beige (slide bg)
WHITE        = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_BLUE   = RGBColor(0xD6, 0xEB, 0xF5)   # pale ocean
DARK_TEXT    = RGBColor(0x1A, 0x1A, 0x2E)   # near-black
MID_GREY     = RGBColor(0x66, 0x66, 0x66)
GOLD         = RGBColor(0xF0, 0xA5, 0x00)

# Slide dimensions (widescreen 16:9)
SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _add_slide(prs: Presentation, layout_index: int = 6):
    """Add a blank slide and return it."""
    layout = prs.slide_layouts[layout_index]  # 6 = blank
    return prs.slides.add_slide(layout)


def _solid_bg(slide, color: RGBColor):
    """Fill the slide background with a solid colour."""
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_rect(slide, left, top, width, height, color: RGBColor, alpha=None):
    """Add a filled rectangle shape."""
    shape = slide.shapes.add_shape(
        pptx_util.MSO_SHAPE_TYPE.AUTO_SHAPE if False else 1,  # MSO_SHAPE.RECTANGLE = 1
        left, top, width, height,
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()  # no border
    return shape


def _add_textbox(slide, text, left, top, width, height,
                 font_size=18, bold=False, color=DARK_TEXT,
                 align=PP_ALIGN.LEFT, italic=False, wrap=True):
    """Add a text box and return the paragraph."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    txBox.word_wrap = wrap
    tf = txBox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txBox


def _add_picture(slide, img_path, left, top, width=None, height=None):
    """Add a picture from *img_path* to the slide, returning the shape."""
    p = pathlib.Path(img_path)
    if not p.exists():
        return None
    if width and height:
        return slide.shapes.add_picture(str(p), left, top, width, height)
    elif width:
        return slide.shapes.add_picture(str(p), left, top, width=width)
    elif height:
        return slide.shapes.add_picture(str(p), left, top, height=height)
    else:
        return slide.shapes.add_picture(str(p), left, top)


def _header_bar(slide, title_text, subtitle_text=""):
    """Add a branded header bar at the top of a content slide."""
    # Dark blue bar
    _add_rect(slide, 0, 0, SLIDE_W, Inches(1.1), DEEP_OCEAN)
    # Coral accent line below bar
    _add_rect(slide, 0, Inches(1.1), SLIDE_W, Inches(0.06), CORAL_RED)

    # Title text in bar
    _add_textbox(slide, title_text,
                 Inches(0.35), Inches(0.12),
                 Inches(10.5), Inches(0.75),
                 font_size=24, bold=True, color=WHITE, align=PP_ALIGN.LEFT)

    if subtitle_text:
        _add_textbox(slide, subtitle_text,
                     Inches(0.35), Inches(0.7),
                     Inches(10.5), Inches(0.45),
                     font_size=13, color=LIGHT_BLUE, align=PP_ALIGN.LEFT)


def _footer(slide, page_num: int, total: int):
    """Add a subtle footer bar."""
    _add_rect(slide, 0, Inches(7.15), SLIDE_W, Inches(0.35), DEEP_OCEAN)
    footer_txt = "Kenya Coast Coral Connectivity  |  Graph Theory Analysis  |  2024"
    _add_textbox(slide, footer_txt,
                 Inches(0.3), Inches(7.17), Inches(11), Inches(0.3),
                 font_size=9, color=LIGHT_BLUE, align=PP_ALIGN.LEFT)
    _add_textbox(slide, f"{page_num} / {total}",
                 Inches(12.3), Inches(7.17), Inches(0.8), Inches(0.3),
                 font_size=9, color=LIGHT_BLUE, align=PP_ALIGN.RIGHT)


def _bullet_list(slide, items, left, top, width, height,
                 font_size=16, color=DARK_TEXT, indent_level=0,
                 line_spacing_pt=4):
    """Add a bulleted list text box."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    txBox.word_wrap = True
    tf = txBox.text_frame
    tf.word_wrap = True

    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.level = indent_level
        p.space_before = Pt(line_spacing_pt)
        run = p.add_run()
        is_sub = item.startswith("  ")
        bullet_char = "▸ " if is_sub else "● "
        run.text = bullet_char + item.lstrip()
        run.font.size = Pt(font_size - 2 if is_sub else font_size)
        run.font.color.rgb = MID_GREY if is_sub else color
    return txBox


def _section_divider(slide, section_name: str, color=DEEP_OCEAN):
    """Full-slide section divider (no image)."""
    _solid_bg(slide, color)
    # Large semi-transparent circle decoration
    _add_textbox(slide, section_name,
                 Inches(1.5), Inches(2.5), Inches(10), Inches(2),
                 font_size=40, bold=True, color=WHITE,
                 align=PP_ALIGN.CENTER)
    _add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), CORAL_RED)


# ---------------------------------------------------------------------------
# Load data tables
# ---------------------------------------------------------------------------

def _load_csv(path):
    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Individual slide builders
# ---------------------------------------------------------------------------

def slide_title(prs, total):
    """Slide 1 – Title."""
    slide = _add_slide(prs)
    _solid_bg(slide, DEEP_OCEAN)

    # Decorative wave strip at bottom
    _add_rect(slide, 0, Inches(6.5), SLIDE_W, Inches(1.0), REEF_GREEN)
    _add_rect(slide, 0, Inches(6.85), SLIDE_W, Inches(0.65), DEEP_OCEAN)
    _add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), CORAL_RED)

    # Coral accent top-right block
    _add_rect(slide, Inches(10.5), 0, Inches(2.83), Inches(2.5), CORAL_RED)

    # Main title
    _add_textbox(slide,
                 "Kenya Coast\nCoral Connectivity",
                 Inches(0.5), Inches(1.2), Inches(10), Inches(2.6),
                 font_size=44, bold=True, color=WHITE, align=PP_ALIGN.LEFT)

    # Sub-title
    _add_textbox(slide,
                 "Graph Theory Analysis of Ecological Connectivity Networks\n"
                 "for Marine Protected Area Design",
                 Inches(0.5), Inches(3.85), Inches(9.8), Inches(1.2),
                 font_size=18, color=LIGHT_BLUE, align=PP_ALIGN.LEFT)

    # Author / date block
    _add_rect(slide, Inches(0.45), Inches(5.2), Inches(5.5), Inches(0.05), CORAL_RED)
    _add_textbox(slide, "Reef Ecology & Marine Conservation Programme  |  2024",
                 Inches(0.5), Inches(5.3), Inches(9), Inches(0.5),
                 font_size=13, color=SAND, align=PP_ALIGN.LEFT)

    # Small label in coral block
    _add_textbox(slide, "15 Reef\nPatches", Inches(10.7), Inches(0.4),
                 Inches(2.3), Inches(1.5), font_size=20, bold=True,
                 color=WHITE, align=PP_ALIGN.CENTER)


def slide_overview(prs, total):
    """Slide 2 – Project overview."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "Project Overview", "Why graph theory for coral reefs?")
    _footer(slide, 2, total)

    objectives = [
        "Quantify larval-dispersal connectivity among 15 Kenya coast reef patches",
        "Identify key source reefs (strong larval exporters)",
        "Pinpoint stepping-stone reefs that link otherwise isolated reef clusters",
        "Detect hub reefs with disproportionate network influence",
        "Rank all reef patches and select the top-10 MPA candidates",
        "Provide a reproducible, data-driven framework for conservation planning",
    ]

    _add_textbox(slide, "Objectives",
                 Inches(0.4), Inches(1.3), Inches(6), Inches(0.5),
                 font_size=17, bold=True, color=DEEP_OCEAN)

    _bullet_list(slide, objectives,
                 Inches(0.4), Inches(1.85), Inches(8.2), Inches(4.8),
                 font_size=16, color=DARK_TEXT)

    # Highlight box
    _add_rect(slide, Inches(9.1), Inches(1.3), Inches(3.9), Inches(5.2), DEEP_OCEAN)
    key_facts = [
        "15 reef patches",
        "125 directed edges",
        "3 communities",
        "9 graph metrics",
        "Top-10 MPAs ranked",
    ]
    _add_textbox(slide, "At a Glance",
                 Inches(9.2), Inches(1.4), Inches(3.7), Inches(0.5),
                 font_size=15, bold=True, color=GOLD)
    for i, fact in enumerate(key_facts):
        _add_textbox(slide, fact,
                     Inches(9.25), Inches(1.95 + i * 0.75), Inches(3.6), Inches(0.6),
                     font_size=14, color=WHITE)


def slide_study_area(prs, total):
    """Slide 3 – Study area."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "Study Area", "15 Reef Patches · Kenya Coast · Indian Ocean")
    _footer(slide, 3, total)

    # Left: reef list with geographic context
    reefs_north = [
        "Malindi Marine National Park",
        "Watamu Marine National Park",
        "Mida Creek",
        "Kilifi Reef",
        "Vipingo Reef",
    ]
    reefs_central = [
        "Mombasa Marine National Park",
        "Bamburi Reef",
        "Nyali Reef",
        "Tiwi Reef",
    ]
    reefs_south = [
        "Diani Reef",
        "Chale Lagoon",
        "Gazi Bay",
        "Funzi Bay",
        "Shimoni Reef",
        "Kisite-Mpunguti MNP",
    ]

    _add_rect(slide, Inches(0.3), Inches(1.3), Inches(4.2), Inches(5.7), LIGHT_BLUE)

    _add_textbox(slide, "▲ Northern Cluster",
                 Inches(0.4), Inches(1.35), Inches(4), Inches(0.4),
                 font_size=12, bold=True, color=DEEP_OCEAN)
    for i, r in enumerate(reefs_north):
        _add_textbox(slide, f"  {i+1}. {r}",
                     Inches(0.45), Inches(1.75 + i * 0.37), Inches(4), Inches(0.35),
                     font_size=12, color=DARK_TEXT)

    _add_textbox(slide, "▶ Central Cluster",
                 Inches(0.4), Inches(3.7), Inches(4), Inches(0.4),
                 font_size=12, bold=True, color=REEF_GREEN)
    for i, r in enumerate(reefs_central):
        _add_textbox(slide, f"  {i+6}. {r}",
                     Inches(0.45), Inches(4.1 + i * 0.37), Inches(4), Inches(0.35),
                     font_size=12, color=DARK_TEXT)

    _add_textbox(slide, "▼ Southern Cluster",
                 Inches(0.4), Inches(5.65), Inches(4), Inches(0.4),
                 font_size=12, bold=True, color=CORAL_RED)
    for i, r in enumerate(reefs_south):
        _add_textbox(slide, f"  {i+10}. {r}",
                     Inches(0.45), Inches(6.05 + i * 0.37), Inches(4), Inches(0.35),
                     font_size=12, color=DARK_TEXT)

    # Right: oceanographic context text
    _add_textbox(slide, "Oceanographic Context",
                 Inches(4.8), Inches(1.3), Inches(8.2), Inches(0.5),
                 font_size=16, bold=True, color=DEEP_OCEAN)

    ctx = [
        "East African Coastal Current (EACC) flows N→S during SE monsoon (May–Oct)",
        "NE monsoon reverses flow S→N (Nov–Apr)",
        "Net larval dispersal has a southward bias",
        "Adjacent reef patches have highest connectivity; decays with distance",
        "Pelagic larval duration determines dispersal range",
        "MNP = Marine National Park (existing protection)",
    ]
    _bullet_list(slide, ctx,
                 Inches(4.8), Inches(1.9), Inches(8.2), Inches(4.0),
                 font_size=14, color=DARK_TEXT)


def slide_methods(prs, total):
    """Slide 4 – Methods overview."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "Methods", "Graph Theory Framework")
    _footer(slide, 4, total)

    # Pipeline boxes
    steps = [
        ("1. Data\nInput", "Square CSV\n15×15 matrix", DEEP_OCEAN),
        ("2. Graph\nBuild", "Directed\nWeighted\nnx.DiGraph", REEF_GREEN),
        ("3. Metrics\nCompute", "9 graph-theory\nmetrics", CORAL_RED),
        ("4. Community\nDetect", "Louvain\nalgorithm", DEEP_OCEAN),
        ("5. MPA\nRank", "Composite\nscore", GOLD),
    ]

    for i, (title, body, color) in enumerate(steps):
        x = Inches(0.35 + i * 2.6)
        _add_rect(slide, x, Inches(1.3), Inches(2.3), Inches(1.6), color)
        _add_textbox(slide, title, x + Inches(0.05), Inches(1.35),
                     Inches(2.2), Inches(0.8),
                     font_size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        _add_textbox(slide, body, x + Inches(0.05), Inches(2.1),
                     Inches(2.2), Inches(0.75),
                     font_size=11, color=SAND, align=PP_ALIGN.CENTER)
        # Arrow (except last)
        if i < len(steps) - 1:
            _add_textbox(slide, "→",
                         x + Inches(2.3), Inches(1.65),
                         Inches(0.3), Inches(0.5),
                         font_size=22, bold=True, color=DEEP_OCEAN,
                         align=PP_ALIGN.CENTER)

    # Metrics table
    _add_textbox(slide, "Graph Metrics Computed",
                 Inches(0.35), Inches(3.2), Inches(12.5), Inches(0.5),
                 font_size=16, bold=True, color=DEEP_OCEAN)

    metrics = [
        ("Metric", "Ecological Meaning", "Bold"),
        ("Weighted Out-Degree", "Total larval-export strength of a reef", ""),
        ("Weighted In-Degree", "Total larval-import (sink) strength", ""),
        ("Betweenness Centrality", "Stepping-stone / corridor role", ""),
        ("Closeness Centrality", "Accessibility to the whole reef network", ""),
        ("Eigenvector Centrality", "Hub influence — connected to well-connected reefs", ""),
        ("PageRank", "Flow-based larval-source prestige", ""),
        ("Local Clustering Coeff.", "Density of a reef's neighbourhood", ""),
        ("Global Transitivity", "Overall triangle fraction of the network", ""),
        ("Community (Louvain)", "Reef cluster membership", ""),
    ]

    col_widths = [Inches(3.5), Inches(8.0)]
    row_h = Inches(0.38)
    start_y = Inches(3.7)

    for r, (m, meaning, _bold) in enumerate(metrics):
        bg = DEEP_OCEAN if r == 0 else (LIGHT_BLUE if r % 2 == 0 else WHITE)
        fc = WHITE if r == 0 else DARK_TEXT
        _add_rect(slide, Inches(0.35), start_y + r * row_h,
                  col_widths[0], row_h, bg)
        _add_rect(slide, Inches(0.35) + col_widths[0], start_y + r * row_h,
                  col_widths[1], row_h, bg)
        bold = (r == 0)
        _add_textbox(slide, m,
                     Inches(0.45), start_y + r * row_h + Inches(0.05),
                     col_widths[0] - Inches(0.1), row_h,
                     font_size=12, bold=bold, color=fc)
        _add_textbox(slide, meaning,
                     Inches(0.45) + col_widths[0], start_y + r * row_h + Inches(0.05),
                     col_widths[1] - Inches(0.1), row_h,
                     font_size=12, bold=bold, color=fc)


def slide_synthetic_network(prs, total):
    """Slide 5 – Synthetic 10-node demo network."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "Synthetic 10-Node Demo Network",
                "Graph-theory concepts illustrated on a controlled example")
    _footer(slide, 5, total)

    img = ROOT / "plots" / "synthetic" / "network_overview.png"
    _add_picture(slide, img, Inches(0.3), Inches(1.25), height=Inches(5.7))

    # Caption box
    _add_rect(slide, Inches(7.5), Inches(1.3), Inches(5.5), Inches(5.6), DEEP_OCEAN)

    _add_textbox(slide, "Network Design",
                 Inches(7.6), Inches(1.4), Inches(5.3), Inches(0.45),
                 font_size=14, bold=True, color=GOLD)

    notes = [
        "10 nodes (N0–N9)",
        "17 directed, weighted edges",
        "2 main communities (A & B)",
        "Bridge node N4 → N5",
        "Hub node N2 (cross-community links)",
        "Node size  ∝  out-degree",
        "Node colour  ∝  betweenness centrality",
        "Edge width  ∝  connection weight",
    ]
    for i, n in enumerate(notes):
        _add_textbox(slide, "• " + n,
                     Inches(7.65), Inches(1.9 + i * 0.56), Inches(5.2), Inches(0.5),
                     font_size=13, color=WHITE)

    _add_rect(slide, Inches(7.55), Inches(6.4), Inches(5.3), Inches(0.05), CORAL_RED)
    _add_textbox(slide,
                 "Global transitivity: 0.279  |  4 communities detected",
                 Inches(7.6), Inches(6.45), Inches(5.2), Inches(0.4),
                 font_size=11, color=SAND, align=PP_ALIGN.CENTER)


def slide_synthetic_metrics(prs, total):
    """Slide 6 – Synthetic network centrality bar charts."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "Synthetic Network – Centrality Metrics",
                "Each node scored across six complementary measures")
    _footer(slide, 6, total)

    plots = [
        ("bar_out_degree.png", "Out-Degree"),
        ("bar_betweenness.png", "Betweenness"),
        ("bar_eigenvector.png", "Eigenvector"),
        ("bar_in_degree.png", "In-Degree"),
        ("bar_closeness.png", "Closeness"),
        ("bar_pagerank.png", "PageRank"),
    ]

    cols, rows = 3, 2
    w, h = Inches(4.25), Inches(2.7)
    for i, (fname, label) in enumerate(plots):
        col = i % cols
        row = i // cols
        x = Inches(0.2 + col * 4.35)
        y = Inches(1.25 + row * 2.9)
        img = ROOT / "plots" / "synthetic" / fname
        _add_picture(slide, img, x, y, width=w, height=h)


def slide_kenya_heatmap(prs, total):
    """Slide 7 – Kenya connectivity heatmap."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "Kenya Coast Connectivity Matrix",
                "15 × 15 directed larval-dispersal weights")
    _footer(slide, 7, total)

    img = ROOT / "plots" / "kenya" / "connectivity_heatmap.png"
    _add_picture(slide, img, Inches(0.2), Inches(1.2), height=Inches(5.85))

    # Interpretation box
    _add_rect(slide, Inches(9.3), Inches(1.3), Inches(3.8), Inches(5.6), DEEP_OCEAN)
    _add_textbox(slide, "How to Read",
                 Inches(9.4), Inches(1.4), Inches(3.6), Inches(0.45),
                 font_size=14, bold=True, color=GOLD)
    interp = [
        "Rows = source reefs",
        "Columns = destination reefs",
        "Darker cell = stronger connection",
        "Diagonal = 0 (self-loops excluded)",
        "Southward bias visible in the lower triangle (EACC effect)",
        "Strong local clusters (bright 3×3 blocks) correspond to Louvain communities",
    ]
    for i, t in enumerate(interp):
        _add_textbox(slide, "• " + t,
                     Inches(9.45), Inches(1.9 + i * 0.65), Inches(3.55), Inches(0.6),
                     font_size=12, color=WHITE)


def slide_kenya_network(prs, total):
    """Slide 8 – Kenya reef network overview."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "Kenya Reef Connectivity Network",
                "Node size = out-degree strength  |  Node colour = betweenness centrality")
    _footer(slide, 8, total)

    img = ROOT / "plots" / "kenya" / "network_overview.png"
    _add_picture(slide, img, Inches(0.2), Inches(1.2), height=Inches(5.85))

    _add_rect(slide, Inches(9.3), Inches(1.3), Inches(3.8), Inches(5.6), DEEP_OCEAN)
    _add_textbox(slide, "Key Observations",
                 Inches(9.4), Inches(1.4), Inches(3.6), Inches(0.45),
                 font_size=14, bold=True, color=GOLD)
    obs = [
        "Mombasa MNP dominates as the largest, brightest node",
        "Two dense sub-clusters: northern (Malindi–Vipingo) and southern (Diani–Kisite)",
        "Vipingo Reef acts as a bridge between clusters",
        "High betweenness reefs are warmly coloured",
        "Edge widths reflect relative dispersal probability",
    ]
    for i, t in enumerate(obs):
        _add_textbox(slide, "• " + t,
                     Inches(9.45), Inches(1.9 + i * 0.75), Inches(3.55), Inches(0.65),
                     font_size=12, color=WHITE)


def slide_communities(prs, total):
    """Slide 9 – Community structure."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "Community Structure — Louvain Algorithm",
                "Reef patches grouped by internal connectivity strength")
    _footer(slide, 9, total)

    img = ROOT / "plots" / "kenya" / "community_structure.png"
    _add_picture(slide, img, Inches(0.2), Inches(1.2), height=Inches(5.85))

    _add_rect(slide, Inches(9.3), Inches(1.3), Inches(3.8), Inches(5.6), DEEP_OCEAN)
    _add_textbox(slide, "3 Communities Detected",
                 Inches(9.4), Inches(1.4), Inches(3.6), Inches(0.45),
                 font_size=14, bold=True, color=GOLD)

    communities = [
        ("Community 0 (Northern)", LIGHT_BLUE,
         "Malindi, Watamu, Mida Creek, Kilifi, Vipingo"),
        ("Community 1 (Central)", REEF_GREEN,
         "Mombasa MNP, Bamburi, Nyali, Tiwi"),
        ("Community 2 (Southern)", CORAL_RED,
         "Diani, Chale, Gazi, Funzi, Shimoni, Kisite-Mpunguti"),
    ]

    for i, (name, color, members) in enumerate(communities):
        y = Inches(2.0 + i * 1.5)
        _add_rect(slide, Inches(9.35), y, Inches(3.7), Inches(1.35), color)
        _add_textbox(slide, name,
                     Inches(9.45), y + Inches(0.08), Inches(3.55), Inches(0.45),
                     font_size=13, bold=True, color=DEEP_OCEAN)
        _add_textbox(slide, members,
                     Inches(9.45), y + Inches(0.5), Inches(3.55), Inches(0.75),
                     font_size=11, color=DARK_TEXT)

    _add_textbox(slide,
                 "Conservation implication: each community should have ≥1 MPA to "
                 "maintain internal larval supply and recovery capacity.",
                 Inches(9.4), Inches(6.65), Inches(3.6), Inches(0.5),
                 font_size=10, italic=True, color=SAND)


def slide_degree(prs, total):
    """Slide 10 – Degree distribution."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "Degree Distribution",
                "In-degree and out-degree histograms for all 15 reef patches")
    _footer(slide, 10, total)

    img = ROOT / "plots" / "kenya" / "degree_distribution.png"
    _add_picture(slide, img, Inches(0.3), Inches(1.25), width=Inches(8.5))

    _add_rect(slide, Inches(9.0), Inches(1.3), Inches(4.0), Inches(5.6), DEEP_OCEAN)
    _add_textbox(slide, "Interpretation",
                 Inches(9.1), Inches(1.4), Inches(3.8), Inches(0.45),
                 font_size=14, bold=True, color=GOLD)
    pts = [
        "Most reefs have moderate connectivity (bell-shaped distribution)",
        "Right-skewed out-degree: a few reefs export larvae to many others",
        "High in-degree reefs act as sinks, useful for recovery",
        "Low-degree reefs may be isolated and most vulnerable",
    ]
    for i, t in enumerate(pts):
        _add_textbox(slide, "• " + t,
                     Inches(9.15), Inches(1.95 + i * 0.95), Inches(3.75), Inches(0.85),
                     font_size=12, color=WHITE)


def slide_betweenness(prs, total):
    """Slide 11 – Betweenness centrality (stepping-stone reefs)."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "Betweenness Centrality — Stepping-Stone Reefs",
                "Reefs that lie on shortest paths between other reef pairs")
    _footer(slide, 11, total)

    img = ROOT / "plots" / "kenya" / "bar_betweenness.png"
    _add_picture(slide, img, Inches(0.3), Inches(1.25), width=Inches(8.5))

    _add_rect(slide, Inches(9.0), Inches(1.3), Inches(4.0), Inches(5.6), DEEP_OCEAN)
    _add_textbox(slide, "Stepping-Stone Reefs",
                 Inches(9.1), Inches(1.4), Inches(3.8), Inches(0.45),
                 font_size=14, bold=True, color=GOLD)

    # Load betweenness from metrics CSV
    rows = _load_csv(ROOT / "metrics_kenya.csv")
    rows_sorted = sorted(rows, key=lambda r: float(r["betweenness"]), reverse=True)[:4]

    for i, row in enumerate(rows_sorted):
        name = row["reef_patch"].replace("_", " ")
        val  = float(row["betweenness"])
        _add_textbox(slide, f"#{i+1}  {name}",
                     Inches(9.15), Inches(1.95 + i * 0.7), Inches(3.75), Inches(0.4),
                     font_size=13, bold=True, color=WHITE)
        _add_textbox(slide, f"Betweenness = {val:.3f}",
                     Inches(9.15), Inches(2.25 + i * 0.7), Inches(3.75), Inches(0.35),
                     font_size=11, color=SAND)

    pts = [
        "Mombasa MNP and Vipingo Reef have the highest betweenness",
        "Removing either would disconnect northern and southern reef communities",
        "Critical corridors for larval flow and genetic exchange",
    ]
    for i, t in enumerate(pts):
        _add_textbox(slide, "• " + t,
                     Inches(9.15), Inches(4.8 + i * 0.65), Inches(3.75), Inches(0.55),
                     font_size=11, italic=True, color=LIGHT_BLUE)


def slide_eigenvector(prs, total):
    """Slide 12 – Eigenvector centrality (hub reefs)."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "Eigenvector & Closeness Centrality — Hub Reefs",
                "Reefs connected to well-connected reefs; proximity to the entire network")
    _footer(slide, 12, total)

    img_e = ROOT / "plots" / "kenya" / "bar_eigenvector.png"
    img_c = ROOT / "plots" / "kenya" / "bar_closeness.png"
    _add_picture(slide, img_e, Inches(0.3), Inches(1.25), width=Inches(6.3), height=Inches(2.75))
    _add_picture(slide, img_c, Inches(0.3), Inches(4.1),  width=Inches(6.3), height=Inches(2.75))

    _add_rect(slide, Inches(6.9), Inches(1.3), Inches(6.1), Inches(5.6), DEEP_OCEAN)
    _add_textbox(slide, "Hub Reefs",
                 Inches(7.0), Inches(1.4), Inches(5.9), Inches(0.45),
                 font_size=14, bold=True, color=GOLD)

    rows = _load_csv(ROOT / "metrics_kenya.csv")
    rows_e = sorted(rows, key=lambda r: float(r["eigenvector"]), reverse=True)[:4]

    for i, row in enumerate(rows_e):
        name = row["reef_patch"].replace("_", " ")
        val  = float(row["eigenvector"])
        _add_textbox(slide, f"#{i+1}  {name}",
                     Inches(7.05), Inches(1.95 + i * 0.7), Inches(5.85), Inches(0.4),
                     font_size=13, bold=True, color=WHITE)
        _add_textbox(slide, f"Eigenvector = {val:.4f}",
                     Inches(7.05), Inches(2.25 + i * 0.7), Inches(5.85), Inches(0.35),
                     font_size=11, color=SAND)

    pts = [
        "Chale Lagoon & Gazi Bay have the highest eigenvector scores",
        "These reefs amplify network-wide larval exchange",
        "Protecting them sustains connectivity throughout the southern cluster",
    ]
    for i, t in enumerate(pts):
        _add_textbox(slide, "• " + t,
                     Inches(7.05), Inches(4.8 + i * 0.65), Inches(5.85), Inches(0.55),
                     font_size=11, italic=True, color=LIGHT_BLUE)


def slide_outdegree_pagerank(prs, total):
    """Slide 13 – Out-degree & PageRank (source reefs)."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "Out-Degree & PageRank — Source Reefs",
                "Reefs that export the most larvae to the network")
    _footer(slide, 13, total)

    img_o = ROOT / "plots" / "kenya" / "bar_out_degree.png"
    img_p = ROOT / "plots" / "kenya" / "bar_pagerank.png"
    _add_picture(slide, img_o, Inches(0.3), Inches(1.25), width=Inches(6.3), height=Inches(2.75))
    _add_picture(slide, img_p, Inches(0.3), Inches(4.1),  width=Inches(6.3), height=Inches(2.75))

    _add_rect(slide, Inches(6.9), Inches(1.3), Inches(6.1), Inches(5.6), DEEP_OCEAN)
    _add_textbox(slide, "Top Source Reefs",
                 Inches(7.0), Inches(1.4), Inches(5.9), Inches(0.45),
                 font_size=14, bold=True, color=GOLD)

    rows = _load_csv(ROOT / "metrics_kenya.csv")
    rows_o = sorted(rows, key=lambda r: float(r["out_degree"]), reverse=True)[:4]

    for i, row in enumerate(rows_o):
        name = row["reef_patch"].replace("_", " ")
        val  = float(row["out_degree"])
        pr   = float(row["pagerank"])
        _add_textbox(slide, f"#{i+1}  {name}",
                     Inches(7.05), Inches(1.95 + i * 0.75), Inches(5.85), Inches(0.4),
                     font_size=13, bold=True, color=WHITE)
        _add_textbox(slide, f"Out-degree = {val:.3f}  |  PageRank = {pr:.4f}",
                     Inches(7.05), Inches(2.25 + i * 0.75), Inches(5.85), Inches(0.35),
                     font_size=11, color=SAND)

    pts = [
        "Mombasa MNP leads in out-degree (highest larval export)",
        "Tiwi & Nyali Reefs also strong source reefs",
        "PageRank captures flow-based prestige beyond direct links",
    ]
    for i, t in enumerate(pts):
        _add_textbox(slide, "• " + t,
                     Inches(7.05), Inches(4.85 + i * 0.65), Inches(5.85), Inches(0.55),
                     font_size=11, italic=True, color=LIGHT_BLUE)


def slide_mpa_workflow(prs, total):
    """Slide 14 – MPA prioritisation workflow."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "MPA Prioritisation Workflow",
                "Three conservation roles → composite ranking → top-10 MPAs")
    _footer(slide, 14, total)

    # Three role boxes
    roles = [
        ("🌊  Source\nStrength",
         "Out-degree (60%) +\nPageRank (40%)",
         "Reefs that fuel the network\nwith larvae",
         DEEP_OCEAN),
        ("🔗  Stepping-\nStone",
         "Betweenness\nCentrality (100%)",
         "Corridor reefs bridging\nisolated clusters",
         REEF_GREEN),
        ("⭐  Influential\nHub",
         "Eigenvector (60%) +\nCloseness (40%)",
         "Reefs amplifying\nnetwork-wide exchange",
         CORAL_RED),
    ]

    for i, (title, metrics_txt, desc, color) in enumerate(roles):
        x = Inches(0.4 + i * 4.25)
        _add_rect(slide, x, Inches(1.3), Inches(3.9), Inches(2.4), color)
        _add_textbox(slide, title, x + Inches(0.1), Inches(1.35),
                     Inches(3.7), Inches(0.85),
                     font_size=15, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        _add_textbox(slide, metrics_txt, x + Inches(0.1), Inches(2.15),
                     Inches(3.7), Inches(0.65),
                     font_size=12, color=SAND, align=PP_ALIGN.CENTER)
        _add_textbox(slide, desc, x + Inches(0.1), Inches(2.8),
                     Inches(3.7), Inches(0.75),
                     font_size=11, italic=True, color=LIGHT_BLUE, align=PP_ALIGN.CENTER)

    # Equation box
    _add_rect(slide, Inches(0.4), Inches(3.85), Inches(12.5), Inches(0.75), DARK_TEXT)
    _add_textbox(slide,
                 "Composite Score  =  ( w₁ × Source  +  w₂ × Stepping-Stone  +  w₃ × Hub )  ÷  (w₁+w₂+w₃)",
                 Inches(0.5), Inches(3.9), Inches(12.3), Inches(0.65),
                 font_size=14, bold=True, color=GOLD, align=PP_ALIGN.CENTER)

    # Notes
    notes = [
        "All three role scores are min-max normalised to [0, 1] before combining.",
        "Default: equal weights (w₁ = w₂ = w₃ = 1).  "
        "Weights are user-configurable via --w-source, --w-stepping, --w-hub flags.",
        "The composite score identifies reefs that are simultaneously important "
        "sources, corridors, and hubs — the highest-priority MPA candidates.",
    ]
    for i, n in enumerate(notes):
        _add_textbox(slide, "• " + n,
                     Inches(0.5), Inches(4.75 + i * 0.65), Inches(12.3), Inches(0.6),
                     font_size=13, color=DARK_TEXT)


def slide_top10_table(prs, total):
    """Slide 15 – Top-10 priority reefs table."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "Top-10 Priority Reefs for MPA Designation",
                "Composite score ranking (equal weights)")
    _footer(slide, 15, total)

    rows_data = _load_csv(ROOT / "priority_reefs.csv")

    headers = ["Rank", "Reef Patch", "Source", "Stepping-Stone", "Hub", "Composite", "Key Role"]
    col_w   = [Inches(0.6), Inches(2.8), Inches(1.1), Inches(1.6), Inches(0.85), Inches(1.2), Inches(4.5)]
    col_x   = [Inches(0.25)]
    for w in col_w[:-1]:
        col_x.append(col_x[-1] + w)

    row_h  = Inches(0.42)
    start_y = Inches(1.3)

    key_roles = {
        "Mombasa_MNP":           "Source + stepping-stone + hub",
        "Chale_Lagoon":          "Hub + source",
        "Vipingo_Reef":          "Stepping-stone + source",
        "Nyali_Reef":            "Hub + source",
        "Gazi_Bay":              "Hub + source",
        "Diani_Reef":            "Hub + source",
        "Tiwi_Reef":             "Source + hub",
        "Shimoni_Reef":          "Source + hub",
        "Funzi_Bay":             "Hub + source",
        "Kisite_Mpunguti_MNP":   "Hub",
    }

    # Header row
    for j, (hdr, x, w) in enumerate(zip(headers, col_x, col_w)):
        _add_rect(slide, x, start_y, w, row_h, DEEP_OCEAN)
        _add_textbox(slide, hdr, x + Inches(0.05), start_y + Inches(0.06),
                     w - Inches(0.1), row_h - Inches(0.06),
                     font_size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    for r, row in enumerate(rows_data[:10]):
        y     = start_y + (r + 1) * row_h
        bg    = LIGHT_BLUE if r % 2 == 0 else WHITE
        hl    = GOLD if r == 0 else bg  # gold highlight for #1

        values = [
            str(r + 1),
            row["reef_patch"].replace("_", " "),
            row["source_score"],
            row["stepping_stone_score"],
            row["hub_score"],
            row["composite_score"],
            key_roles.get(row["reef_patch"], ""),
        ]

        for j, (val, x, w) in enumerate(zip(values, col_x, col_w)):
            cell_bg = GOLD if r == 0 else bg
            _add_rect(slide, x, y, w, row_h, cell_bg)
            fc = DARK_TEXT if r != 0 else DEEP_OCEAN
            bold = (r == 0) or (j == 1)
            _add_textbox(slide, val, x + Inches(0.04), y + Inches(0.06),
                         w - Inches(0.08), row_h - Inches(0.06),
                         font_size=11, bold=bold, color=fc, align=PP_ALIGN.CENTER)


def slide_top10_chart(prs, total):
    """Slide 16 – Top-10 stacked bar chart."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "Top-10 MPA Candidates — Composite Score Breakdown",
                "Stacked bars show contribution of each conservation criterion")
    _footer(slide, 16, total)

    img = ROOT / "plots" / "conservation" / "top10_composite_bar.png"
    _add_picture(slide, img, Inches(0.2), Inches(1.2), height=Inches(5.85))

    # Legend box
    _add_rect(slide, Inches(9.35), Inches(1.3), Inches(3.75), Inches(5.6), DEEP_OCEAN)
    _add_textbox(slide, "Score Legend",
                 Inches(9.45), Inches(1.4), Inches(3.55), Inches(0.45),
                 font_size=14, bold=True, color=GOLD)

    legend = [
        (RGBColor(0x21, 0x96, 0xF3), "Source strength\n(out-degree + PageRank)"),
        (RGBColor(0xFF, 0x98, 0x00), "Stepping-stone\n(betweenness centrality)"),
        (RGBColor(0x4C, 0xAF, 0x50), "Hub influence\n(eigenvector + closeness)"),
    ]
    for i, (color, label) in enumerate(legend):
        _add_rect(slide, Inches(9.45), Inches(2.05 + i * 1.0),
                  Inches(0.35), Inches(0.35), color)
        _add_textbox(slide, label,
                     Inches(9.9), Inches(2.0 + i * 1.0),
                     Inches(3.1), Inches(0.5),
                     font_size=12, color=WHITE)

    _add_rect(slide, Inches(9.45), Inches(5.2), Inches(3.55), Inches(0.04), CORAL_RED)
    _add_textbox(slide,
                 "Mombasa MNP scores near-perfect across all three criteria, making "
                 "it the undisputed #1 priority.",
                 Inches(9.45), Inches(5.3), Inches(3.55), Inches(1.2),
                 font_size=11, italic=True, color=LIGHT_BLUE)


def slide_recommendations(prs, total):
    """Slide 17 – Conservation recommendations."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "Conservation Recommendations",
                "Evidence-based MPA network design for the Kenya coast")
    _footer(slide, 17, total)

    img = ROOT / "plots" / "conservation" / "mpa_priority_ranking.png"
    _add_picture(slide, img, Inches(0.2), Inches(1.2), height=Inches(5.85))

    _add_rect(slide, Inches(8.0), Inches(1.3), Inches(5.1), Inches(5.6), DEEP_OCEAN)
    _add_textbox(slide, "Priority Actions",
                 Inches(8.1), Inches(1.4), Inches(4.9), Inches(0.45),
                 font_size=14, bold=True, color=GOLD)

    recs = [
        ("Immediately", "Strengthen protection at Mombasa MNP – the network's single most critical node"),
        ("Short-term", "Designate Vipingo Reef as a no-take MPA to secure the stepping-stone corridor"),
        ("Short-term", "Protect Chale Lagoon as the southern cluster's dominant hub"),
        ("Medium-term", "Establish MPAs at Nyali, Gazi Bay & Diani to safeguard the southern source cluster"),
        ("Long-term", "Create a co-managed MPA network linking all 3 reef communities"),
        ("Monitoring", "Deploy connectivity tagging (otolith / genetics) to validate modelled dispersal"),
    ]

    for i, (timeline, text) in enumerate(recs):
        y = Inches(1.95 + i * 0.75)
        col = CORAL_RED if "Immediately" in timeline else \
              REEF_GREEN if "Short" in timeline else \
              GOLD       if "Medium" in timeline else \
              LIGHT_BLUE
        _add_rect(slide, Inches(8.1), y, Inches(1.2), Inches(0.6), col)
        _add_textbox(slide, timeline,
                     Inches(8.12), y + Inches(0.08), Inches(1.16), Inches(0.45),
                     font_size=10, bold=True, color=DARK_TEXT, align=PP_ALIGN.CENTER)
        _add_textbox(slide, text,
                     Inches(9.4), y + Inches(0.04), Inches(3.6), Inches(0.6),
                     font_size=11, color=WHITE)


def slide_conclusions(prs, total):
    """Slide 18 – Conclusions & next steps."""
    slide = _add_slide(prs)
    _solid_bg(slide, SAND)
    _header_bar(slide, "Conclusions & Next Steps", "")
    _footer(slide, 18, total)

    conclusions = [
        "Graph theory provides a powerful, quantitative framework for MPA network design",
        "15 Kenya coast reef patches form 3 distinct communities with limited inter-cluster connectivity",
        "Mombasa MNP is simultaneously the top source, stepping-stone, and hub — "
        "protect it first",
        "Vipingo Reef is the critical corridor; its loss would disconnect northern "
        "and southern reef communities",
        "The composite ranking identifies 10 reef patches that, if protected, would "
        "safeguard the majority of larval-dispersal pathways",
        "A network of just 5 strategically distributed MPAs (one per community + "
        "2 stepping-stone reefs) would cover >80 % of connectivity",
    ]

    next_steps = [
        "Validate connectivity model with genetic / otolith dispersal data",
        "Incorporate climate projections (bleaching, sea-level rise) into connectivity model",
        "Apply optimisation (simulated annealing / ILP) to maximise MPA coverage per $",
        "Extend to the wider Western Indian Ocean reef network",
        "Develop an interactive decision-support dashboard for marine park managers",
    ]

    _add_textbox(slide, "Key Conclusions",
                 Inches(0.4), Inches(1.3), Inches(6.2), Inches(0.5),
                 font_size=16, bold=True, color=DEEP_OCEAN)
    _bullet_list(slide, conclusions,
                 Inches(0.4), Inches(1.85), Inches(6.2), Inches(4.8),
                 font_size=13, color=DARK_TEXT)

    _add_rect(slide, Inches(6.85), Inches(1.3), Inches(0.04), Inches(5.6), CORAL_RED)

    _add_textbox(slide, "Next Steps",
                 Inches(7.1), Inches(1.3), Inches(5.9), Inches(0.5),
                 font_size=16, bold=True, color=DEEP_OCEAN)
    _bullet_list(slide, next_steps,
                 Inches(7.1), Inches(1.85), Inches(5.9), Inches(4.8),
                 font_size=13, color=DARK_TEXT)


def slide_references(prs, total):
    """Slide 19 – References & acknowledgements."""
    slide = _add_slide(prs)
    _solid_bg(slide, DEEP_OCEAN)
    _add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), CORAL_RED)

    _add_textbox(slide, "References & Acknowledgements",
                 Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.7),
                 font_size=26, bold=True, color=WHITE)
    _add_rect(slide, Inches(0.5), Inches(1.0), Inches(12.3), Inches(0.05), CORAL_RED)

    refs = [
        "Almany G.R. et al. (2009). Connectivity, biodiversity conservation and the design of "
        "marine reserve networks for coral reefs. Coral Reefs 28:339–351.",
        "Halpern B.S. et al. (2006). Accounting for uncertainty in marine reserve design. "
        "Ecology Letters 9:2–12.",
        "Newman M.E.J. (2006). Modularity and community structure in networks. "
        "PNAS 103:8577–8582.",
        "Treml E.A. et al. (2008). Modeling population connectivity by ocean currents, "
        "a graph‑theoretic approach. Landscape Ecology 23:19–36.",
        "White J.W. et al. (2010). Graph-theory approaches to the connectivity of marine reserves. "
        "Ecological Modelling 221:886–897.",
        "UNEP-WCMC, WorldFish, WRI, TNC (2021). Global distribution of coral reefs. "
        "Ocean+ Library.",
    ]

    for i, ref in enumerate(refs):
        _add_textbox(slide, ref,
                     Inches(0.5), Inches(1.2 + i * 0.72), Inches(12.3), Inches(0.65),
                     font_size=11, color=SAND)

    _add_rect(slide, Inches(0.5), Inches(5.55), Inches(12.3), Inches(0.05), CORAL_RED)
    _add_textbox(slide, "Acknowledgements",
                 Inches(0.5), Inches(5.65), Inches(12.3), Inches(0.45),
                 font_size=14, bold=True, color=GOLD)
    _add_textbox(slide,
                 "Kenya Wildlife Service  ·  Kenya Marine & Fisheries Research Institute (KMFRI)  ·  "
                 "Wildlife Conservation Society Kenya  ·  CORDIO East Africa",
                 Inches(0.5), Inches(6.15), Inches(12.3), Inches(0.45),
                 font_size=12, color=LIGHT_BLUE)

    _add_textbox(slide,
                 "Code & data: github.com/ALEXASWA/kenya-coast-coral-connectivity",
                 Inches(0.5), Inches(6.65), Inches(12.3), Inches(0.4),
                 font_size=11, italic=True, color=SAND)


# ---------------------------------------------------------------------------
# Master builder
# ---------------------------------------------------------------------------

def build_presentation(out_path: str):
    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H

    TOTAL = 19

    slide_title(prs, TOTAL)
    slide_overview(prs, TOTAL)
    slide_study_area(prs, TOTAL)
    slide_methods(prs, TOTAL)
    slide_synthetic_network(prs, TOTAL)
    slide_synthetic_metrics(prs, TOTAL)
    slide_kenya_heatmap(prs, TOTAL)
    slide_kenya_network(prs, TOTAL)
    slide_communities(prs, TOTAL)
    slide_degree(prs, TOTAL)
    slide_betweenness(prs, TOTAL)
    slide_eigenvector(prs, TOTAL)
    slide_outdegree_pagerank(prs, TOTAL)
    slide_mpa_workflow(prs, TOTAL)
    slide_top10_table(prs, TOTAL)
    slide_top10_chart(prs, TOTAL)
    slide_recommendations(prs, TOTAL)
    slide_conclusions(prs, TOTAL)
    slide_references(prs, TOTAL)

    prs.save(out_path)
    print(f"Presentation saved → {out_path}")
    print(f"Total slides: {len(prs.slides)}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="Generate a professional PowerPoint presentation for the project."
    )
    p.add_argument(
        "--out",
        default=str(ROOT / "presentation.pptx"),
        help="Output path (default: presentation.pptx in project root)",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_presentation(args.out)
