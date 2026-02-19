"""
figures.py
==========
Fonctions de construction des graphiques Plotly.
La mention de source INSEE est affichée dans un html.Div
sous le graphique (layout.py), pas dans la figure Plotly.
"""

import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import PchipInterpolator

from config import COLORS, SALARY_DIST, PROPORTIONS, CURRENT_YEAR


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _build_cdf():
    x_pts = np.array([0] + list(SALARY_DIST.values()) + [SALARY_DIST["C99"] * 1.6])
    y_pts = np.array([0.0] + list(PROPORTIONS.values()) + [1.0])
    return PchipInterpolator(x_pts, y_pts)


def _base_layout(bg: str, title: str, extra: dict | None = None) -> dict:
    layout = dict(
        paper_bgcolor=bg,
        plot_bgcolor=bg,
        font=dict(color=COLORS["text_secondary"], family="DM Mono, monospace"),
        margin=dict(l=10, r=10, t=44, b=44),
        title=dict(
            text=title,
            font=dict(size=12, color=COLORS["text_label"], family="Syne, sans-serif"),
            x=0.5,
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)",
                    font=dict(color=COLORS["text_secondary"], size=10)),
    )
    if extra:
        layout.update(extra)
    return layout


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convertit #RRGGBB en rgba(r,g,b,alpha) — seul format valide pour Plotly."""
    h = hex_color.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    return f"rgba(148,163,184,{alpha})"


# ─── Palette catégories budget ─────────────────────────────────────────────────

_CATEGORY_COLORS = {
    "Logement":      "#3B82F6",
    "Alimentation":  "#10B981",
    "Transport":     "#8B5CF6",
    "Loisirs":       "#F59E0B",
    "Épargne":       "#06B6D4",
    "Santé":         "#EF4444",
    "Autre":         "#94A3B8",
}

_COLOR_CYCLE = [
    "#3B82F6", "#10B981", "#8B5CF6", "#F59E0B",
    "#06B6D4", "#EF4444", "#EC4899", "#84CC16",
    "#F97316", "#A78BFA",
]

_DEFAULT_BUDGET = {
    "Logement":     {"Loyer / crédit": 850, "Charges & énergie": 120, "Assurance habitation": 30},
    "Alimentation": {"Courses": 350, "Restaurants": 120},
    "Transport":    {"Carburant / transports": 150, "Assurance auto": 80},
    "Loisirs":      {"Sorties & culture": 80, "Abonnements": 40},
    "Épargne":      {"Épargne de précaution": 200, "Investissements": 150},
    "Santé":        {"Mutuelles": 70, "Soins": 50},
    "Autre":        {"Divers": 100},
}


def get_cat_color(cat: str, cat_colors: dict | None = None) -> str:
    if cat_colors and cat in cat_colors:
        return cat_colors[cat]
    if cat in _CATEGORY_COLORS:
        return _CATEGORY_COLORS[cat]
    return _COLOR_CYCLE[abs(hash(cat)) % len(_COLOR_CYCLE)]


# ─── Graphique PDF · Distribution salariale ───────────────────────────────────

def build_pdf_figure(salary_compare: float | None = None) -> go.Figure:
    """
    Courbe de densité des salaires nets annuels (France, INSEE 2021).
    Aucune annotation de source dans la figure — placée en html.Div dans layout.py.
    """
    cdf  = _build_cdf()
    pdf  = cdf.derivative()

    x_min  = 5_000
    x_max  = int(SALARY_DIST["C99"] * 1.35)
    x_fine = np.linspace(x_min, x_max, 2_000)
    y_pdf  = np.clip(pdf(x_fine), 0, None)

    area = np.trapezoid(y_pdf, x_fine)
    if area > 0:
        y_pdf /= area
    y_max = float(y_pdf.max())

    fig = go.Figure()

    if salary_compare is not None:
        pct  = float(np.clip(cdf(salary_compare), 0, 1))
        mask = x_fine <= salary_compare
        if mask.any():
            fig.add_trace(go.Scatter(
                x=np.concatenate([[x_fine[mask][0]], x_fine[mask], [x_fine[mask][-1]]]),
                y=np.concatenate([[0], y_pdf[mask], [0]]),
                fill="toself", fillcolor="rgba(59,130,246,0.14)",
                line=dict(width=0), showlegend=True,
                name=f"{pct * 100:.1f} % de la population",
                hoverinfo="skip",
            ))

    fig.add_trace(go.Scatter(
        x=x_fine, y=y_pdf, mode="lines",
        line=dict(color=COLORS["accent"], width=2.5),
        name="Densité estimée",
        hovertemplate="<b>%{x:,.0f} €</b><extra></extra>",
    ))

    for lbl in PROPORTIONS:
        xv = SALARY_DIST[lbl]
        yv = float(np.clip(pdf(xv), 0, None)) / (area if area > 0 else 1)
        fig.add_trace(go.Scatter(
            x=[xv], y=[yv], mode="markers+text",
            marker=dict(color=COLORS["accent"], size=6,
                        line=dict(color=COLORS["bg_card"], width=2)),
            text=[lbl], textposition="top center",
            textfont=dict(color=COLORS["text_muted"], size=8, family="DM Mono, monospace"),
            showlegend=False,
            hovertemplate=f"<b>{lbl}</b> : {xv:,} €<extra></extra>",
        ))
        fig.add_shape(type="line", x0=xv, x1=xv, y0=0, y1=yv,
                      line=dict(color=COLORS["border_glow"], dash="dot", width=1))

    if salary_compare is not None:
        pct = float(np.clip(cdf(salary_compare), 0, 1))
        fig.add_vline(x=salary_compare, line_color=COLORS["secondary"],
                      line_width=2, line_dash="solid")
        fig.add_annotation(
            x=salary_compare, y=y_max * 0.88,
            text=f"<b>{pct * 100:.1f}e percentile</b><br>{salary_compare:,.0f} €/an",
            showarrow=True, arrowhead=2,
            arrowcolor=COLORS["secondary"], arrowwidth=1.5,
            ax=70, ay=-36,
            font=dict(color=COLORS["text_primary"], size=11, family="Syne, sans-serif"),
            bgcolor=COLORS["bg_card_alt"],
            bordercolor=COLORS["secondary"], borderwidth=1.5, borderpad=8,
        )

    fig.update_layout(**_base_layout(
        COLORS["bg_card"], "Distribution des salaires nets annuels",
        extra=dict(
            xaxis=dict(
                title=dict(text="Salaire net annuel (€)",
                           font=dict(size=10, color=COLORS["text_label"])),
                range=[x_min, x_max],
                tickvals=list(SALARY_DIST.values()),
                ticktext=[f"{v // 1_000}k €" for v in SALARY_DIST.values()],
                gridcolor=COLORS["grid"], color=COLORS["text_muted"],
                zeroline=False, tickfont=dict(size=9, family="DM Mono, monospace"),
            ),
            yaxis=dict(visible=False),
            hovermode="x",
            margin=dict(l=10, r=10, t=44, b=36),
        ),
    ))
    return fig


# ─── Graphique projection temporelle ──────────────────────────────────────────

def build_projection_figure(
    past_df,
    future_growth: float,
    horizon: int,
    current_year: int = CURRENT_YEAR,
    confidence_pct: float = 5.0,
) -> go.Figure:
    fig = go.Figure()
    all_years = []

    if past_df is not None and len(past_df) > 0:
        past_years    = [d.year for d in past_df["Date"]]
        past_salaries = past_df["Salaire"].tolist()
        all_years.extend(past_years)

        fig.add_trace(go.Scatter(
            x=past_years, y=past_salaries, mode="lines+markers",
            line=dict(color=COLORS["accent"], width=2.5),
            marker=dict(size=8, color=COLORS["accent"],
                        line=dict(color=COLORS["bg_card"], width=2)),
            name="Historique",
            hovertemplate="<b>%{x}</b><br>%{y:,.0f} €<extra></extra>",
        ))

        if future_growth is not None and horizon:
            last_year   = past_years[-1]
            last_salary = past_salaries[-1]
            gr = 1 + future_growth / 100

            future_years = list(range(last_year, last_year + horizon + 1))
            n = len(future_years)
            # Taux haut et bas : growth_rate ± confidence_pct (en absolu sur le taux)
            gr_high = 1 + (future_growth + confidence_pct) / 100
            gr_low  = 1 + (future_growth - confidence_pct) / 100
            proj_values = [last_salary * (gr      ** i) for i in range(n)]
            proj_high   = [last_salary * (gr_high ** i) for i in range(n)]
            proj_low    = [last_salary * (gr_low  ** i) for i in range(n)]
            all_years.extend(future_years)

            fig.add_trace(go.Scatter(
                x=future_years + future_years[::-1],
                y=proj_high + proj_low[::-1],
                fill="toself", fillcolor="rgba(245,158,11,0.09)",
                line=dict(width=0), showlegend=True,
                name=f"Intervalle ±{confidence_pct:.0f}%/an",
                hoverinfo="skip",
            ))
            fig.add_trace(go.Scatter(
                x=future_years, y=proj_values, mode="lines",
                line=dict(color=COLORS["secondary"], width=2.5, dash="dash"),
                name=f"Projection {future_growth:+.1f}%/an",
                hovertemplate="<b>%{x}</b><br>%{y:,.0f} €<extra></extra>",
            ))

    fig.add_vline(
        x=current_year,
        line_color="rgba(255,255,255,0.10)", line_width=1.5, line_dash="dot",
        annotation_text="Aujourd'hui",
        annotation_font=dict(color=COLORS["text_muted"], size=10, family="Syne, sans-serif"),
        annotation_position="top right",
    )

    if all_years:
        x_min_yr, x_max_yr = min(all_years) - 1, max(all_years) + 1
    else:
        x_min_yr, x_max_yr = current_year - 1, current_year + horizon + 1

    fig.update_layout(**_base_layout(
        COLORS["bg_card"], "Évolution & projection salariale",
        extra=dict(
            xaxis=dict(
                title=dict(text="Année",
                           font=dict(size=10, color=COLORS["text_label"])),
                range=[x_min_yr, x_max_yr],
                tickmode="linear", dtick=max(1, (x_max_yr - x_min_yr) // 10),
                gridcolor=COLORS["grid"], color=COLORS["text_muted"],
                zeroline=False, tickfont=dict(size=9, family="DM Mono, monospace"),
            ),
            yaxis=dict(
                title=dict(text="Salaire net annuel (€)",
                           font=dict(size=10, color=COLORS["text_label"])),
                gridcolor=COLORS["grid"], color=COLORS["text_muted"],
                zeroline=False, tickformat=",.0f",
                tickfont=dict(size=9, family="DM Mono, monospace"),
            ),
            hovermode="x unified",
        ),
    ))
    return fig


# ─── Graphique Sankey · Flux budgétaire mensuel ───────────────────────────────

def build_sankey_figure(
    salary_net_monthly: float,
    budget: dict | None = None,
    cat_colors: dict | None = None,
) -> go.Figure:
    """
    salary_net_monthly : utilisé uniquement pour le nœud source (montant total affiché).
    budget             : dict {catégorie: {sous-poste: montant_euros}} — valeurs en € directement.
    """
    if budget is None:
        budget = _DEFAULT_BUDGET

    if not budget:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor=COLORS["bg_card"], plot_bgcolor=COLORS["bg_card"],
            margin=dict(l=10, r=10, t=44, b=20),
            annotations=[dict(
                text="Aucune catégorie définie",
                showarrow=False, font=dict(color=COLORS["text_muted"], size=12),
                x=0.5, y=0.5, xref="paper", yref="paper",
            )],
        )
        return fig

    nodes_labels = ["Salaire net mensuel"]
    node_colors  = [_hex_to_rgba("#3B82F6", 0.9)]

    cat_indices: dict[str, int] = {}
    for cat in budget:
        cat_indices[cat] = len(nodes_labels)
        c = get_cat_color(cat, cat_colors)
        nodes_labels.append(cat)
        node_colors.append(_hex_to_rgba(c, 0.85))

    subcat_idx: dict[str, int] = {}
    for cat, subcats in budget.items():
        for sub in subcats:
            key = f"{cat}::{sub}"
            subcat_idx[key] = len(nodes_labels)
            c = get_cat_color(cat, cat_colors)
            nodes_labels.append(sub)
            node_colors.append(_hex_to_rgba(c, 0.55))   # rgba valide — pas de hex 8 chars

    source, target, value, link_colors = [], [], [], []

    for cat, subcats in budget.items():
        # Les valeurs du budget sont désormais en euros (montants absolus)
        cat_amount = sum(subcats.values())
        c = get_cat_color(cat, cat_colors)

        source.append(0)
        target.append(cat_indices[cat])
        value.append(round(max(cat_amount, 0.01), 2))
        link_colors.append(_hex_to_rgba(c, 0.35))

        for sub, amount in subcats.items():
            source.append(cat_indices[cat])
            target.append(subcat_idx[f"{cat}::{sub}"])
            value.append(round(max(amount, 0.01), 2))
            link_colors.append(_hex_to_rgba(c, 0.20))

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=16, thickness=18,
            line=dict(color=COLORS["bg_app"], width=0.5),
            label=nodes_labels,
            color=node_colors,
            hovertemplate="<b>%{label}</b><br>%{value:,.0f} €/mois<extra></extra>",
        ),
        link=dict(
            source=source, target=target, value=value, color=link_colors,
            hovertemplate="%{source.label} → %{target.label}<br><b>%{value:,.0f} €/mois</b><extra></extra>",
        ),
    ))
    fig.update_layout(
        paper_bgcolor=COLORS["bg_card"], plot_bgcolor=COLORS["bg_card"],
        font=dict(color=COLORS["text_secondary"], family="DM Mono, monospace", size=11),
        margin=dict(l=10, r=10, t=44, b=20),
        title=dict(text="Flux budgétaire mensuel",
                   font=dict(size=12, color=COLORS["text_label"], family="Syne, sans-serif"),
                   x=0.5),
    )
    return fig


# ─── Graphique patrimoine total (placeholder) ──────────────────────────────────

def build_total_figure() -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor=COLORS["bg_card_alt"], plot_bgcolor=COLORS["bg_card_alt"],
        font=dict(color=COLORS["text_muted"]),
        margin=dict(l=10, r=10, t=10, b=40),
        xaxis=dict(gridcolor=COLORS["grid"], zeroline=False),
        yaxis=dict(gridcolor=COLORS["grid"], zeroline=False, tickformat=",.0f"),
        annotations=[dict(
            text="Renseignez les données des 3 onglets pour afficher le cumul",
            showarrow=False,
            font=dict(color=COLORS["text_muted"], size=12, family="Syne, sans-serif"),
            x=0.5, y=0.5, xref="paper", yref="paper",
        )],
    )
    return fig