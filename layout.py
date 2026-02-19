"""
layout.py
=========
Structure de l'interface Dash.

Corrections & nouveautés :
- Source INSEE : html.Div en bas à droite du container (hors figure Plotly)
- Éditeur budget avec renommer / supprimer / créer catégories et sous-catégories
- Bouton sauvegarde CSV dans l'en-tête
- Onglets Immobilier / Investissement avec contenu descriptif détaillé
"""

from dash import html, dcc, dash_table

from config import (
    COLORS, INITIAL_DATA, TABLE_COLS,
    TABLE_STYLE_CELL, TABLE_STYLE_HEADER, TABLE_STYLE_DATA_COND,
    TAB_STYLE, TAB_SELECTED, LABEL_STYLE, VALUE_STYLE, card, CURRENT_YEAR,
)
from figures import (
    build_pdf_figure, build_projection_figure, build_total_figure,
    build_sankey_figure, _DEFAULT_BUDGET, _CATEGORY_COLORS,
)

_CATEGORY_COLOR_MAP = _CATEGORY_COLORS

# ─── Index HTML ───────────────────────────────────────────────────────────────
INDEX_STRING = """<!DOCTYPE html>
<html lang="fr">
<head>
    {%metas%}
    <title>Projection Patrimoniale</title>
    {%favicon%}
    {%css%}
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { box-sizing: border-box; }
        html, body {
            margin: 0; padding: 0; background: #080c14;
            font-family: 'Syne', sans-serif; overflow-x: hidden; color: #F1F5F9;
        }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: #080c14; }
        ::-webkit-scrollbar-thumb { background: #1e2d40; border-radius: 4px; }
        input[type=number]::-webkit-inner-spin-button,
        input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
        .rc-slider-track { background: #3B82F6 !important; }
        .rc-slider-handle {
            border-color: #3B82F6 !important; background: #3B82F6 !important;
            box-shadow: 0 0 0 4px rgba(59,130,246,0.25) !important;
        }
        .rc-slider-rail { background: #1e2d40 !important; }
        .dash-tab { transition: color 0.2s ease; }
        .dash-tab:hover { color: #94A3B8 !important; }
        @keyframes fadeUp {
            from { opacity: 0; transform: translateY(8px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        #tab-content { animation: fadeUp 0.25s ease; }
        body::before {
            content: ''; position: fixed; top: 0; left: 0; right: 0; height: 1px;
            background: linear-gradient(90deg, transparent, #3B82F6, #F59E0B, transparent);
            z-index: 9999;
        }
        .btn-budget {
            background: none; border: 1px solid #1e2d40; border-radius: 4px;
            color: #64748B; cursor: pointer; font-size: 10px; padding: 2px 6px;
            font-family: 'DM Mono', monospace; transition: all 0.15s; line-height: 1.4;
        }
        .btn-budget:hover { border-color: #3B82F6; color: #3B82F6; }
        .btn-budget.danger:hover { border-color: #EF4444; color: #EF4444; }
        .btn-save {
            background: rgba(59,130,246,0.12); border: 1px solid rgba(59,130,246,0.35);
            border-radius: 6px; color: #3B82F6; cursor: pointer; font-size: 11px;
            padding: 6px 16px; font-family: 'Syne', sans-serif; font-weight: 600;
            letter-spacing: 0.06em; transition: all 0.2s;
        }
        .btn-save:hover { background: rgba(59,130,246,0.22); border-color: #3B82F6; }
        .btn-add {
            background: rgba(16,185,129,0.08); border: 1px dashed rgba(16,185,129,0.3);
            border-radius: 6px; color: #10B981; cursor: pointer; font-size: 10px;
            padding: 5px 12px; font-family: 'DM Mono', monospace; width: 100%;
            transition: all 0.2s; margin-top: 4px; display: block;
        }
        .btn-add:hover { background: rgba(16,185,129,0.18); border-color: #10B981; }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>"""


# ─── Helper slider ────────────────────────────────────────────────────────────

def _slider(sid, mn, mx, step, val, marks_dict, label, width="260px"):
    return html.Div([
        html.Div(label, style={**LABEL_STYLE, "marginBottom": "4px"}),
        dcc.Slider(
            id=sid, min=mn, max=mx, step=step, value=val,
            marks={k: {"label": str(v), "style": {"color": COLORS["text_muted"],
                                                   "fontSize": "9px",
                                                   "fontFamily": "DM Mono, monospace"}}
                   for k, v in marks_dict.items()},
            tooltip={"placement": "top", "always_visible": True},
        ),
    ], style={"width": width})


# ─── Feature card (onglets À venir) ───────────────────────────────────────────

def _feature_item(title, desc, color):
    return html.Div(
        style={
            "padding": "14px 16px",
            "backgroundColor": COLORS["bg_surface"],
            "borderRadius": "10px",
            "border": f"1px solid {COLORS['border']}",
            "borderLeft": f"3px solid {color}",
        },
        children=[
            html.Div(title, style={
                "color": COLORS["text_primary"], "fontSize": "13px",
                "fontWeight": "600", "fontFamily": "Syne, sans-serif", "marginBottom": "4px",
            }),
            html.Div(desc, style={
                "color": COLORS["text_muted"], "fontSize": "11px",
                "fontFamily": "DM Mono, monospace", "lineHeight": "1.5",
            }),
        ],
    )


# ─── Onglet Salaire ────────────────────────────────────────────────────────────

def _tab_salaire():
    return html.Div([

        # ── LIGNE HAUTE ──────────────────────────────────────────────────────
        html.Div(
            style={"display": "flex", "gap": "16px",
                   "marginBottom": "16px", "alignItems": "stretch"},
            children=[

                # Colonne gauche : tableau + KPI
                html.Div(
                    style={"display": "flex", "flexDirection": "column",
                           "gap": "14px", "width": "34%"},
                    children=[
                        html.Div(style=card({"minHeight": "240px"}), children=[
                            html.Div("Historique salarial", style=LABEL_STYLE),
                            dash_table.DataTable(
                                id="table-salary",
                                data=INITIAL_DATA, columns=TABLE_COLS,
                                editable=True, row_deletable=True,
                                style_table={"height": "200px", "overflowY": "auto"},
                                style_cell=TABLE_STYLE_CELL,
                                style_header=TABLE_STYLE_HEADER,
                                style_data_conditional=TABLE_STYLE_DATA_COND,
                            ),
                        ]),
                        html.Div(style=card({
                            "flex": "1", "display": "flex", "flexDirection": "column",
                            "justifyContent": "center",
                            "borderLeft": f"3px solid {COLORS['accent']}",
                            "paddingLeft": "22px",
                        }), children=[
                            html.Div("Taux de croissance moyen", style=LABEL_STYLE),
                            html.Div(id="mean-growth-display", style={
                                **VALUE_STYLE, "fontSize": "38px",
                                "color": COLORS["accent"], "lineHeight": "1",
                            }),
                            html.Div("calculé sur votre historique", style={
                                "color": COLORS["text_muted"], "fontSize": "10px",
                                "marginTop": "8px", "fontFamily": "DM Mono, monospace",
                                "letterSpacing": "0.05em",
                            }),
                        ]),
                    ],
                ),

                # Colonne droite : graphique PDF + source INSEE sous le container
                html.Div(style=card({"width": "66%", "paddingBottom": "8px"}), children=[
                    html.Div("Position relative dans la distribution nationale",
                             style=LABEL_STYLE),
                    dcc.Graph(
                        id="graph-pdf", figure=build_pdf_figure(),
                        style={"height": "calc(33vh + 60px)"},
                        config={"displayModeBar": False},
                    ),
                    # Source en bas à droite du container — hors figure Plotly
                    html.Div(
                        "Source : INSEE · Salaires nets annuels · France métropolitaine · 2021",
                        style={
                            "textAlign": "right",
                            "color": COLORS["text_muted"],
                            "fontSize": "9px",
                            "fontFamily": "DM Mono, monospace",
                            "letterSpacing": "0.04em",
                            "marginTop": "2px",
                        },
                    ),
                ]),
            ],
        ),

        # ── PROJECTION ────────────────────────────────────────────────────────
        html.Div(style=card({"marginBottom": "16px"}), children=[
            html.Div(
                style={"display": "flex", "justifyContent": "space-between",
                       "alignItems": "flex-end", "marginBottom": "16px",
                       "flexWrap": "wrap", "gap": "14px"},
                children=[
                    html.Div("Projection salariale", style=LABEL_STYLE),
                    html.Div(
                        style={"display": "flex", "gap": "24px",
                               "alignItems": "flex-end", "flexWrap": "wrap"},
                        children=[
                            _slider("slider-growth", -5, 15, 0.5, 3,
                                    {i: f"{i}%" for i in range(-5, 16, 5)},
                                    "Taux annuel projeté", "280px"),
                            _slider("slider-horizon", 1, 40, 1, 20,
                                    {i: str(i) for i in [1, 10, 20, 30, 40]},
                                    "Horizon (années)", "240px"),
                            _slider("slider-confidence", 0, 30, 1, 5,
                                    {i: f"±{i}%" for i in [0, 10, 20, 30]},
                                    "Intervalle de confiance (%/an)", "240px"),
                        ],
                    ),
                ],
            ),
            dcc.Graph(
                id="graph-projection", figure=build_projection_figure(None, 3, 20),
                style={"height": "300px"}, config={"displayModeBar": False},
            ),
        ]),

        # ── FLUX BUDGÉTAIRE ───────────────────────────────────────────────────
        html.Div(style=card({"marginBottom": "16px"}), children=[

            dcc.Store(id="budget-store", data=_DEFAULT_BUDGET),

            # En-tête
            html.Div(
                style={"display": "flex", "justifyContent": "space-between",
                       "alignItems": "flex-end", "marginBottom": "16px",
                       "flexWrap": "wrap", "gap": "12px"},
                children=[
                    html.Div([
                        html.Div("Flux budgétaire mensuel", style=LABEL_STYLE),
                        html.Div(
                            "Éditez les catégories à gauche · Le diagramme se met à jour en temps réel",
                            style={"color": COLORS["text_muted"], "fontSize": "10px",
                                   "fontFamily": "DM Mono, monospace"},
                        ),
                    ]),
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "10px"},
                        children=[
                            html.Div("Salaire net mensuel (€)",
                                     style={**LABEL_STYLE, "marginBottom": "0"}),
                            dcc.Input(
                                id="input-monthly-salary",
                                type="number", placeholder="ex : 2 800", debounce=True,
                                style={
                                    "backgroundColor": COLORS["bg_surface"],
                                    "color": COLORS["text_secondary"],
                                    "border": f"1px solid {COLORS['border']}",
                                    "borderRadius": "6px", "padding": "7px 14px",
                                    "fontFamily": "DM Mono, monospace",
                                    "fontSize": "13px", "width": "150px", "outline": "none",
                                },
                            ),
                        ],
                    ),
                ],
            ),

            # Éditeur (dynamique via callback) + Sankey
            html.Div(
                style={"display": "flex", "gap": "16px", "alignItems": "flex-start"},
                children=[
                    html.Div(id="budget-editor-container", style={"width": "32%"}),
                    html.Div(style={"flex": "1"}, children=[
                        dcc.Graph(
                            id="graph-sankey", figure=build_sankey_figure(2800),
                            style={"height": "420px"}, config={"displayModeBar": False},
                        ),
                    ]),
                ],
            ),

            html.Div(id="budget-total-indicator", style={
                "marginTop": "10px", "textAlign": "right",
                "fontFamily": "DM Mono, monospace", "fontSize": "11px",
                "color": COLORS["text_muted"],
            }),
        ]),
    ])


# ─── Onglet Immobilier ────────────────────────────────────────────────────────

def _tab_immobilier():
    color = "#F59E0B"
    features = [
        ("Inventaire de biens",
         "Ajoutez vos propriétés (résidence principale, investissements locatifs) avec "
         "leur valeur d'acquisition, date d'achat et valeur estimée actuelle."),
        ("Simulation de crédit",
         "Renseignez votre emprunt (capital, taux, durée) pour visualiser l'amortissement, "
         "le coût total des intérêts et le capital restant dû année par année."),
        ("Revenus locatifs",
         "Suivez vos loyers mensuels, charges déductibles et taux d'occupation "
         "pour calculer la rentabilité nette de chaque bien."),
        ("Évolution du parc immobilier",
         "Projection de la valeur de vos biens avec hypothèses de revalorisation "
         "annuelle personnalisables par zone géographique."),
        ("Analyse fiscale",
         "Estimation de l'imposition sur revenus fonciers, plus-values immobilières "
         "et impact de la fiscalité sur votre rendement net après impôts."),
    ]
    return html.Div([html.Div(style=card({"minHeight": "50vh"}), children=[
        html.Div(style={"display": "flex", "gap": "20px", "alignItems": "flex-start",
                        "marginBottom": "28px"}, children=[
            html.Div(style={"flex": "1"}, children=[
                html.Div("Module Immobilier", style={
                    **VALUE_STYLE, "color": color, "marginBottom": "8px",
                }),
                html.Div(
                    "Centralisez et analysez votre patrimoine immobilier. Suivez vos biens, "
                    "crédits et revenus locatifs pour piloter votre stratégie avec précision.",
                    style={"color": COLORS["text_secondary"], "fontSize": "13px",
                           "fontFamily": "DM Mono, monospace", "lineHeight": "1.7",
                           "maxWidth": "600px"},
                ),
            ]),
            html.Div("À venir", style={
                "backgroundColor": "rgba(245,158,11,0.12)",
                "border": "1px solid rgba(245,158,11,0.3)",
                "borderRadius": "20px", "padding": "4px 14px",
                "color": color, "fontSize": "10px",
                "fontFamily": "DM Mono, monospace", "fontWeight": "600",
                "letterSpacing": "0.08em", "whiteSpace": "nowrap", "alignSelf": "flex-start",
            }),
        ]),
        html.Div(
            style={"display": "grid",
                   "gridTemplateColumns": "repeat(auto-fill, minmax(340px, 1fr))",
                   "gap": "12px"},
            children=[_feature_item(t, d, color) for t, d in features],
        ),
    ])])


# ─── Onglet Investissement ────────────────────────────────────────────────────

def _tab_investissement():
    color = "#10B981"
    features = [
        ("Portefeuilles & lignes",
         "Enregistrez vos portefeuilles (PEA, CTO, assurance-vie) avec le détail "
         "de chaque position : ticker, quantité, PRU et valeur de marché actuelle."),
        ("Performance & rendement",
         "Calcul automatique de la performance globale et par ligne (TWR, MWR), "
         "dividendes perçus et comparaison avec des indices de référence (CAC40, S&P500…)."),
        ("Allocation d'actifs",
         "Visualisez votre répartition géographique, sectorielle et par classe d'actifs. "
         "Identifiez les déséquilibres et opportunités de rééquilibrage."),
        ("Simulation d'investissement",
         "Projetez l'impact d'apports réguliers (DCA) ou ponctuels sur votre capital "
         "à long terme, avec hypothèses de rendement annuel personnalisables."),
        ("Analyse du risque",
         "Indicateurs de volatilité, corrélation entre actifs, Value-at-Risk et "
         "résistance aux scénarios de stress (krach, hausse des taux, inflation)."),
        ("Fiscalité des plus-values",
         "Estimation du PFU (30%) ou option barème progressif selon votre tranche "
         "marginale, avec simulation de l'abattement pour durée de détention."),
    ]
    return html.Div([html.Div(style=card({"minHeight": "50vh"}), children=[
        html.Div(style={"display": "flex", "gap": "20px", "alignItems": "flex-start",
                        "marginBottom": "28px"}, children=[
            html.Div(style={"flex": "1"}, children=[
                html.Div("Module Investissement", style={
                    **VALUE_STYLE, "color": color, "marginBottom": "8px",
                }),
                html.Div(
                    "Gérez et optimisez vos portefeuilles financiers. De la saisie des "
                    "positions à la simulation long terme, maîtrisez chaque dimension "
                    "de votre stratégie d'investissement.",
                    style={"color": COLORS["text_secondary"], "fontSize": "13px",
                           "fontFamily": "DM Mono, monospace", "lineHeight": "1.7",
                           "maxWidth": "600px"},
                ),
            ]),
            html.Div("À venir", style={
                "backgroundColor": "rgba(16,185,129,0.10)",
                "border": "1px solid rgba(16,185,129,0.3)",
                "borderRadius": "20px", "padding": "4px 14px",
                "color": color, "fontSize": "10px",
                "fontFamily": "DM Mono, monospace", "fontWeight": "600",
                "letterSpacing": "0.08em", "whiteSpace": "nowrap", "alignSelf": "flex-start",
            }),
        ]),
        html.Div(
            style={"display": "grid",
                   "gridTemplateColumns": "repeat(auto-fill, minmax(340px, 1fr))",
                   "gap": "12px"},
            children=[_feature_item(t, d, color) for t, d in features],
        ),
    ])])


# ─── Layout principal ──────────────────────────────────────────────────────────

def build_layout():
    return html.Div(
        style={"minHeight": "100vh", "backgroundColor": COLORS["bg_app"],
               "padding": "28px 32px", "boxSizing": "border-box"},
        children=[
            # ── Stores globaux (persistants à travers les onglets) ────────────
            # Initialisés au démarrage depuis le fichier de sauvegarde (app.py).
            # salary-store : list de dicts [{Salaire, Date de début, Date de fin}]
            # app-budget-store : dict {catégorie: {sous-poste: montant_euros}}
            dcc.Store(id="salary-store"),
            dcc.Store(id="app-budget-store"),

            # En-tête avec bouton sauvegarde
            html.Div(
                style={"marginBottom": "28px",
                       "borderBottom": f"1px solid {COLORS['border']}",
                       "paddingBottom": "18px", "display": "flex",
                       "justifyContent": "space-between", "alignItems": "center"},
                children=[
                    html.Div(style={"display": "flex", "alignItems": "baseline", "gap": "16px"},
                             children=[
                                 html.H1("PATRIMOINE", style={
                                     "color": COLORS["text_primary"],
                                     "fontFamily": "Syne, sans-serif", "fontWeight": "800",
                                     "fontSize": "24px", "letterSpacing": "0.18em", "margin": "0",
                                 }),
                                 html.Span("Projection financière personnelle", style={
                                     "color": COLORS["text_muted"],
                                     "fontFamily": "DM Mono, monospace",
                                     "fontSize": "11px", "letterSpacing": "0.06em",
                                 }),
                             ]),
                    html.Div(style={"display": "flex", "alignItems": "center", "gap": "12px"},
                             children=[
                                 html.Div(id="save-feedback", style={
                                     "fontFamily": "DM Mono, monospace", "fontSize": "10px",
                                     "color": COLORS["text_muted"],
                                 }),
                                 html.Button("💾  Sauvegarder", id="btn-save",
                                             className="btn-save", n_clicks=0),
                             ]),
                ],
            ),

            # Onglets
            dcc.Tabs(
                id="tabs-main", value="salaire",
                children=[
                    dcc.Tab(label="Salaire",        value="salaire",    style=TAB_STYLE, selected_style=TAB_SELECTED),
                    dcc.Tab(label="Immobilier",     value="immobilier", style=TAB_STYLE, selected_style=TAB_SELECTED),
                    dcc.Tab(label="Investissement", value="boursier",   style=TAB_STYLE, selected_style=TAB_SELECTED),
                ],
                style={"borderBottom": f"1px solid {COLORS['border']}",
                       "marginBottom": "22px", "backgroundColor": "transparent"},
            ),

            html.Div(id="tab-content"),

            # Bandeau total
            html.Div(style=card({
                "marginTop": "16px", "backgroundColor": COLORS["bg_card_alt"],
                "borderLeft": f"3px solid {COLORS['secondary']}",
            }), children=[
                html.Div(style={"display": "flex", "justifyContent": "space-between",
                                "alignItems": "center", "marginBottom": "12px"}, children=[
                    html.Div("Cumul patrimoine total", style=LABEL_STYLE),
                    html.Div("Salaire · Immobilier · Investissements", style={
                        "color": COLORS["text_muted"], "fontSize": "9px",
                        "fontFamily": "DM Mono, monospace", "letterSpacing": "0.08em",
                    }),
                ]),
                dcc.Graph(id="graph-total", figure=build_total_figure(),
                          style={"height": "200px"}, config={"displayModeBar": False}),
            ]),
        ],
    )


# ─── Sélecteur d'onglet ───────────────────────────────────────────────────────

def get_tab_content(tab: str):
    if tab == "salaire":
        return _tab_salaire()
    if tab == "immobilier":
        return _tab_immobilier()
    return _tab_investissement()