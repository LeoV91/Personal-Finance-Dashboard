"""
config.py
=========
Constantes globales : palette, données INSEE, styles CSS partagés.
"""

from datetime import datetime

# ─── Données salaires France · INSEE 2021 ─────────────────────────────────────
SALARY_DIST = {
    "D1":  14_500,
    "Q1":  19_800,
    "D5":  26_000,
    "Q3":  36_000,
    "D9":  55_000,
    "C95": 72_000,
    "C99": 110_000,
}

PROPORTIONS = {
    "D1":  0.10,
    "Q1":  0.25,
    "D5":  0.50,
    "Q3":  0.75,
    "D9":  0.90,
    "C95": 0.95,
    "C99": 0.99,
}

CURRENT_YEAR = datetime.now().year

# ─── Palette ──────────────────────────────────────────────────────────────────
COLORS = {
    "bg_app":        "#080c14",
    "bg_surface":    "#0d1117",
    "bg_card":       "#111827",
    "bg_card_alt":   "#0d1421",
    "border":        "#1e2d40",
    "border_glow":   "#1e3a5f",
    "grid":          "#151f2e",
    "accent":        "#3B82F6",
    "accent_dim":    "rgba(59,130,246,0.12)",
    "accent_glow":   "rgba(59,130,246,0.35)",
    "secondary":     "#F59E0B",
    "secondary_dim": "rgba(245,158,11,0.18)",
    "success":       "#10B981",
    "danger":        "#EF4444",
    "text_primary":  "#F1F5F9",
    "text_secondary":"#94A3B8",
    "text_muted":    "#475569",
    "text_label":    "#64748B",
}

# ─── Tableau salarial ──────────────────────────────────────────────────────────
N_ROWS = 8

INITIAL_DATA = [
    {"Salaire": 37_000, "Date de début": "01/01/2023", "Date de fin": "31/12/2023"},
    {"Salaire": 39_000, "Date de début": "01/01/2024", "Date de fin": "31/12/2024"},
    {"Salaire": 41_000, "Date de début": "01/01/2025", "Date de fin": "31/12/2025"},
]
while len(INITIAL_DATA) < N_ROWS:
    INITIAL_DATA.append({"Salaire": None, "Date de début": None, "Date de fin": None})

TABLE_COLS = [
    {"name": "Salaire (€)",   "id": "Salaire",       "editable": True, "type": "numeric"},
    {"name": "Date de début", "id": "Date de début",  "editable": True},
    {"name": "Date de fin",   "id": "Date de fin",    "editable": True},
]

# ─── Styles tableau Dash ──────────────────────────────────────────────────────
TABLE_STYLE_CELL = {
    "backgroundColor": COLORS["bg_surface"],
    "color": COLORS["text_secondary"],
    "border": f"1px solid {COLORS['border']}",
    "fontFamily": "DM Mono, monospace",
    "fontSize": "12px",
    "padding": "7px 12px",
    "textAlign": "center",
}
TABLE_STYLE_HEADER = {
    "backgroundColor": COLORS["bg_app"],
    "color": COLORS["accent"],
    "fontWeight": "600",
    "border": f"1px solid {COLORS['border']}",
    "fontSize": "10px",
    "textTransform": "uppercase",
    "letterSpacing": "0.08em",
    "fontFamily": "DM Mono, monospace",
}
TABLE_STYLE_DATA_COND = [
    {"if": {"state": "active"},
     "backgroundColor": "#0a1628",
     "border": f"1px solid {COLORS['accent']}"},
    {"if": {"row_index": "odd"},
     "backgroundColor": "#0c1520"},
]

TAB_STYLE = {
    "backgroundColor": "transparent",
    "color": COLORS["text_muted"],
    "border": "none",
    "borderBottom": "2px solid transparent",
    "padding": "12px 28px",
    "fontFamily": "Syne, sans-serif",
    "fontSize": "12px",
    "fontWeight": "600",
    "textTransform": "uppercase",
    "letterSpacing": "0.1em",
}
TAB_SELECTED = {
    **TAB_STYLE,
    "color": COLORS["text_primary"],
    "borderBottom": f"2px solid {COLORS['accent']}",
}

LABEL_STYLE = {
    "color": COLORS["text_label"],
    "fontSize": "10px",
    "fontWeight": "700",
    "textTransform": "uppercase",
    "letterSpacing": "0.1em",
    "marginBottom": "8px",
    "fontFamily": "Syne, sans-serif",
}

VALUE_STYLE = {
    "color": COLORS["text_primary"],
    "fontSize": "28px",
    "fontWeight": "700",
    "fontFamily": "Syne, sans-serif",
    "letterSpacing": "-0.02em",
}

INPUT_STYLE = {
    "backgroundColor": COLORS["bg_surface"],
    "color": COLORS["text_secondary"],
    "border": f"1px solid {COLORS['border']}",
    "borderRadius": "6px",
    "padding": "7px 14px",
    "fontFamily": "DM Mono, monospace",
    "fontSize": "13px",
    "width": "100%",
    "boxSizing": "border-box",
    "outline": "none",
}


def card(extra: dict | None = None) -> dict:
    base = {
        "backgroundColor": COLORS["bg_card"],
        "borderRadius": "14px",
        "padding": "20px",
        "boxSizing": "border-box",
        "border": f"1px solid {COLORS['border']}",
        "position": "relative",
        "overflow": "hidden",
    }
    if extra:
        base.update(extra)
    return base