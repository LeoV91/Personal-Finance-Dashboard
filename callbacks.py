"""
callbacks.py
============
Tous les callbacks Dash.

Fonctionnalités :
- Mise à jour projection salariale (PDF, courbe, KPI)
- Gestion budget : store JSON, éditeur dynamique (renommer, supprimer, créer)
- Sauvegarde / chargement CSV (données salariales + budget)
"""

import json
import csv
import os
import pandas as pd
from datetime import datetime
from dash import callback, Output, Input, State, html, ALL, ctx, no_update, dcc

from config import COLORS, CURRENT_YEAR, LABEL_STYLE, VALUE_STYLE
from figures import (
    build_pdf_figure, build_projection_figure, build_sankey_figure,
    _DEFAULT_BUDGET, get_cat_color, _COLOR_CYCLE,
)
from layout import get_tab_content

# ─── Chemin du fichier de sauvegarde ──────────────────────────────────────────
SAVE_PATH = os.path.join(os.path.dirname(__file__), "patrimoine_save.json")


# ─── Parsers ──────────────────────────────────────────────────────────────────

DATE_FORMATS = ("%d/%m/%Y", "%m/%Y", "%Y", "%Y-%m-%d")


def _parse_row(row: dict) -> dict | None:
    sal_raw  = row.get("Salaire")
    date_raw = row.get("Date de début")
    if not sal_raw or not date_raw:
        return None
    try:
        sal = float(sal_raw)
    except (TypeError, ValueError):
        return None
    if sal <= 0:
        return None
    for fmt in DATE_FORMATS:
        try:
            return {"Salaire": sal, "Date": datetime.strptime(str(date_raw).strip(), fmt)}
        except ValueError:
            continue
    return None


def _parse_table(rows: list) -> pd.DataFrame | None:
    valid = [r for row in rows if (r := _parse_row(row)) is not None]
    if not valid:
        return None
    return pd.DataFrame(valid).sort_values("Date").reset_index(drop=True)


def _mean_growth_rate(salaries: list) -> float | None:
    if len(salaries) < 2 or salaries[0] <= 0:
        return None
    n = len(salaries) - 1
    return (salaries[-1] / salaries[0]) ** (1 / n) - 1


# ─── Rendu éditeur budget ──────────────────────────────────────────────────────

def _render_editor(budget: dict) -> html.Div:
    """Génère le panneau d'édition gauche du budget depuis le store."""
    cat_blocks = []

    for cat, subcats in budget.items():
        color = get_cat_color(cat)

        sub_rows = []
        for sub, pct in subcats.items():
            sub_rows.append(html.Div(
                style={"display": "flex", "alignItems": "center",
                       "gap": "5px", "marginBottom": "4px"},
                children=[
                    dcc.Input(
                        id={"type": "subcat-name", "cat": cat, "sub": sub},
                        value=sub, debounce=True,
                        style={
                            "flex": "1", "background": "none", "border": "none",
                            "borderBottom": f"1px solid {COLORS['border']}",
                            "color": COLORS["text_muted"], "fontSize": "10px",
                            "fontFamily": "DM Mono, monospace",
                            "padding": "1px 4px", "outline": "none",
                        },
                    ),
                    dcc.Input(
                        id={"type": "budget-input", "cat": cat, "sub": sub},
                        type="number", value=pct, min=0, debounce=True,
                        style={
                            "width": "72px", "backgroundColor": COLORS["bg_app"],
                            "color": COLORS["text_secondary"],
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "4px", "padding": "2px 5px",
                            "fontFamily": "DM Mono, monospace", "fontSize": "11px",
                            "textAlign": "right",
                        },
                    ),
                    html.Span("€", style={"color": COLORS["text_muted"],
                                          "fontSize": "10px",
                                          "fontFamily": "DM Mono, monospace"}),
                    html.Button("✕",
                                id={"type": "del-subcat", "cat": cat, "sub": sub},
                                className="btn-budget danger", n_clicks=0,
                                title=f"Supprimer {sub}"),
                ],
            ))

        # Bouton ajouter sous-poste
        sub_rows.append(html.Button(
            "+ sous-poste",
            id={"type": "add-subcat", "cat": cat},
            className="btn-add", n_clicks=0,
        ))

        cat_blocks.append(html.Div(
            style={
                "backgroundColor": COLORS["bg_surface"],
                "borderRadius": "8px", "padding": "10px 12px",
                "border": f"1px solid {COLORS['border']}",
                "borderLeft": f"3px solid {color}",
            },
            children=[
                html.Div(style={"display": "flex", "alignItems": "center",
                                "gap": "6px", "marginBottom": "8px"}, children=[
                    dcc.Input(
                        id={"type": "cat-name", "cat": cat},
                        value=cat, debounce=True,
                        style={
                            "flex": "1", "background": "none", "border": "none",
                            "color": color, "fontSize": "10px", "fontWeight": "700",
                            "fontFamily": "Syne, sans-serif", "letterSpacing": "0.08em",
                            "textTransform": "uppercase", "outline": "none", "padding": "0",
                        },
                    ),
                    html.Button("✕",
                                id={"type": "del-cat", "cat": cat},
                                className="btn-budget danger", n_clicks=0,
                                title=f"Supprimer {cat}"),
                ]),
                *sub_rows,
            ],
        ))

    # Bouton ajouter catégorie
    cat_blocks.append(html.Button(
        "+ nouvelle catégorie",
        id="add-cat-btn",
        className="btn-add", n_clicks=0,
        style={"marginTop": "6px"},
    ))

    return html.Div(
        children=cat_blocks,
        style={"display": "flex", "flexDirection": "column",
               "gap": "6px", "maxHeight": "420px", "overflowY": "auto"},
    )


# ─── Chargement initial depuis fichier ────────────────────────────────────────

def load_saved_data() -> tuple[list, dict]:
    """Charge les données sauvegardées. Retourne (salary_rows, budget)."""
    if not os.path.exists(SAVE_PATH):
        return [], _DEFAULT_BUDGET
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        salary_rows = data.get("salary", [])
        budget      = data.get("budget", _DEFAULT_BUDGET)
        return salary_rows, budget
    except Exception:
        return [], _DEFAULT_BUDGET


# ─── CALLBACKS ────────────────────────────────────────────────────────────────

@callback(Output("tab-content", "children"), Input("tabs-main", "value"))
def render_tab(tab: str):
    return get_tab_content(tab)


# ── Restauration au chargement / refresh ──────────────────────────────────────
# Déclenché à chaque chargement de page (URL initiale).
# Injecte les données des stores globaux dans le DataTable et le budget-store local.
@callback(
    Output("table-salary",  "data",  allow_duplicate=True),
    Output("budget-store",  "data",  allow_duplicate=True),
    Input("salary-store",       "data"),
    Input("app-budget-store",   "data"),
    prevent_initial_call="initial_duplicate",
)
def restore_on_load(saved_salary, saved_budget):
    from config import INITIAL_DATA, N_ROWS
    from figures import _DEFAULT_BUDGET as _DB

    # Historique salarial
    rows = list(saved_salary) if saved_salary else list(INITIAL_DATA)
    while len(rows) < N_ROWS:
        rows.append({"Salaire": None, "Date de début": None, "Date de fin": None})

    # Budget
    budget = saved_budget if saved_budget else _DB

    return rows, budget


# ── Projection + PDF + KPI ────────────────────────────────────────────────────
@callback(
    Output("mean-growth-display", "children"),
    Output("graph-pdf",           "figure"),
    Output("graph-projection",    "figure"),
    Input("table-salary",      "data"),
    Input("slider-growth",     "value"),
    Input("slider-horizon",    "value"),
    Input("slider-confidence", "value"),
)
def update_salary_tab(rows, growth_pct, horizon, confidence_pct):
    past_df = _parse_table(rows) if rows else None

    if past_df is not None and len(past_df) >= 2:
        mgr = _mean_growth_rate(past_df["Salaire"].tolist())
        color = COLORS["accent"] if (mgr or 0) >= 0 else COLORS["secondary"]
        mean_display = html.Span(
            f"{mgr * 100:+.2f} %" if mgr is not None else "—",
            style={"color": color},
        )
    else:
        mean_display = html.Span("—", style={"color": COLORS["text_muted"]})

    last_salary = (
        float(past_df["Salaire"].iloc[-1])
        if past_df is not None and len(past_df) > 0 else None
    )
    return (
        mean_display,
        build_pdf_figure(last_salary),
        build_projection_figure(past_df, growth_pct, horizon, CURRENT_YEAR,
                                confidence_pct=float(confidence_pct or 5)),
    )


# ── Budget store : CRUD complet ───────────────────────────────────────────────
@callback(
    Output("budget-store", "data", allow_duplicate=True),
    # Renommer catégorie
    Input({"type": "cat-name",   "cat": ALL}, "value"),
    State({"type": "cat-name",   "cat": ALL}, "id"),
    # Supprimer catégorie
    Input({"type": "del-cat",    "cat": ALL}, "n_clicks"),
    State({"type": "del-cat",    "cat": ALL}, "id"),
    # Renommer sous-poste
    Input({"type": "subcat-name","cat": ALL, "sub": ALL}, "value"),
    State({"type": "subcat-name","cat": ALL, "sub": ALL}, "id"),
    # Supprimer sous-poste
    Input({"type": "del-subcat", "cat": ALL, "sub": ALL}, "n_clicks"),
    State({"type": "del-subcat", "cat": ALL, "sub": ALL}, "id"),
    # Modifier valeur %
    Input({"type": "budget-input","cat": ALL, "sub": ALL}, "value"),
    State({"type": "budget-input","cat": ALL, "sub": ALL}, "id"),
    # Ajouter sous-poste
    Input({"type": "add-subcat", "cat": ALL}, "n_clicks"),
    State({"type": "add-subcat", "cat": ALL}, "id"),
    # Ajouter catégorie
    Input("add-cat-btn", "n_clicks"),
    State("budget-store", "data"),
    prevent_initial_call=True,
)
def update_budget_store(
    cat_names, cat_name_ids,
    del_cat_clicks, del_cat_ids,
    sub_names, sub_name_ids,
    del_sub_clicks, del_sub_ids,
    pct_values, pct_ids,
    add_sub_clicks, add_sub_ids,
    add_cat_clicks,
    budget,
):
    triggered = ctx.triggered_id
    if budget is None:
        budget = _DEFAULT_BUDGET.copy()

    # ── Supprimer catégorie ──────────────────────────────────────────────
    if isinstance(triggered, dict) and triggered.get("type") == "del-cat":
        cat = triggered["cat"]
        budget = {k: v for k, v in budget.items() if k != cat}
        return budget

    # ── Supprimer sous-poste ─────────────────────────────────────────────
    if isinstance(triggered, dict) and triggered.get("type") == "del-subcat":
        cat = triggered["cat"]
        sub = triggered["sub"]
        if cat in budget:
            budget[cat] = {k: v for k, v in budget[cat].items() if k != sub}
            if not budget[cat]:
                del budget[cat]
        return budget

    # ── Ajouter sous-poste ───────────────────────────────────────────────
    if isinstance(triggered, dict) and triggered.get("type") == "add-subcat":
        cat = triggered["cat"]
        if cat in budget:
            i = 1
            new_name = f"Nouveau poste {i}"
            while new_name in budget[cat]:
                i += 1
                new_name = f"Nouveau poste {i}"
            budget[cat][new_name] = 0
        return budget

    # ── Ajouter catégorie ────────────────────────────────────────────────
    if triggered == "add-cat-btn":
        i = 1
        new_name = f"Catégorie {i}"
        while new_name in budget:
            i += 1
            new_name = f"Catégorie {i}"
        budget[new_name] = {"Nouveau poste": 0}
        return budget

    # ── Renommer catégorie ───────────────────────────────────────────────
    if isinstance(triggered, dict) and triggered.get("type") == "cat-name":
        old_cat = triggered["cat"]
        # Trouver la nouvelle valeur
        for id_d, val in zip(cat_name_ids, cat_names):
            if id_d["cat"] == old_cat and val and val != old_cat:
                new_budget = {}
                for k, v in budget.items():
                    new_budget[val if k == old_cat else k] = v
                return new_budget
        return budget

    # ── Renommer sous-poste ──────────────────────────────────────────────
    if isinstance(triggered, dict) and triggered.get("type") == "subcat-name":
        cat = triggered["cat"]
        old_sub = triggered["sub"]
        for id_d, val in zip(sub_name_ids, sub_names):
            if id_d["cat"] == cat and id_d["sub"] == old_sub and val and val != old_sub:
                if cat in budget:
                    new_subs = {}
                    for k, v in budget[cat].items():
                        new_subs[val if k == old_sub else k] = v
                    budget[cat] = new_subs
                return budget
        return budget

    # ── Modifier montant (€) ─────────────────────────────────────────────
    if isinstance(triggered, dict) and triggered.get("type") == "budget-input":
        for id_d, val in zip(pct_ids, pct_values):
            cat = id_d["cat"]
            sub = id_d["sub"]
            if cat in budget and sub in budget[cat]:
                budget[cat][sub] = float(val) if val is not None else 0.0
        return budget

    return budget


# ── Rendu éditeur + Sankey ────────────────────────────────────────────────────
@callback(
    Output("budget-editor-container", "children"),
    Output("graph-sankey",            "figure"),
    Output("budget-total-indicator",  "children"),
    Input("budget-store",          "data"),
    Input("input-monthly-salary",  "value"),
    Input("table-salary",          "data"),
)
def render_budget_ui(budget, monthly_salary, salary_rows):
    if budget is None:
        budget = _DEFAULT_BUDGET

    # Salaire mensuel
    if monthly_salary and float(monthly_salary) > 0:
        sal = float(monthly_salary)
    else:
        past_df = _parse_table(salary_rows) if salary_rows else None
        sal = float(past_df["Salaire"].iloc[-1]) / 12 if (
            past_df is not None and len(past_df) > 0
        ) else 2_800.0

    editor  = _render_editor(budget)
    fig     = build_sankey_figure(sal, budget)

    # Indicateur — tout en euros
    total_eur = sum(a for subs in budget.values() for a in subs.values())
    remaining = sal - total_eur
    ind_color = (COLORS["success"] if abs(remaining) < 1
                 else COLORS["secondary"] if remaining > 0 else COLORS["danger"])
    indicator = html.Span([
        html.Span(f"Total alloué : {total_eur:,.0f} € / {sal:,.0f} € — ",
                  style={"color": COLORS["text_muted"]}),
        html.Span(
            "Budget équilibré ✓" if abs(remaining) < 1 else f"Solde : {remaining:+,.0f} €",
            style={"color": ind_color, "fontWeight": "600"},
        ),
    ])
    return editor, fig, indicator


# ── Sauvegarde JSON ───────────────────────────────────────────────────────────
# Met à jour le fichier ET les stores globaux afin que le prochain refresh
# retrouve immédiatement les données sans relancer le serveur.
@callback(
    Output("save-feedback",    "children"),
    Output("salary-store",     "data"),
    Output("app-budget-store", "data"),
    Input("btn-save",     "n_clicks"),
    State("table-salary", "data"),
    State("budget-store", "data"),
    prevent_initial_call=True,
)
def save_data(n_clicks, salary_rows, budget):
    if not n_clicks:
        return no_update, no_update, no_update
    try:
        salary_rows = salary_rows or []
        budget      = budget or _DEFAULT_BUDGET
        payload = {
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "salary":   salary_rows,
            "budget":   budget,
        }
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        ts = datetime.now().strftime("%H:%M:%S")
        feedback = html.Span(f"✓ Sauvegardé à {ts}", style={"color": COLORS["success"]})
        return feedback, salary_rows, budget
    except Exception as e:
        return html.Span(f"✗ Erreur : {e}", style={"color": COLORS["danger"]}), no_update, no_update