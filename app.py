"""
app.py
======
Point d'entrée de l'application Dash.

Stratégie de persistance :
  - Deux dcc.Store globaux (salary-store, app-budget-store) sont déclarés
    dans build_layout() et donc toujours présents dans le DOM.
  - Au démarrage du process, leurs valeurs initiales sont écrasées par les
    données du fichier patrimoine_save.json s'il existe.
  - Un callback dans callbacks.py écoute ces stores pour initialiser le
    DataTable et le budget-store local à l'onglet Salaire.
  - Un refresh navigateur recharge la page et déclenche ce callback :
    les données sont restaurées sans relancer le serveur.

Arborescence
------------
├── app.py
├── config.py
├── figures.py
├── layout.py
├── callbacks.py
├── SalaryProjectionFunc.py
└── patrimoine_save.json   (créé par le bouton Sauvegarder)
"""

from dash import Dash

from config import INITIAL_DATA, N_ROWS
from figures import _DEFAULT_BUDGET
from layout import build_layout, INDEX_STRING
from callbacks import load_saved_data
import callbacks  # noqa: F401


# ─── Données à injecter (sauvegarde ou valeurs par défaut) ───────────────────
_saved_salary, _saved_budget = load_saved_data()

_init_salary = _saved_salary if _saved_salary else INITIAL_DATA
_init_budget = _saved_budget if _saved_budget else _DEFAULT_BUDGET

# Compléter l'historique salarial jusqu'à N_ROWS
_init_salary = list(_init_salary)
while len(_init_salary) < N_ROWS:
    _init_salary.append({"Salaire": None, "Date de début": None, "Date de fin": None})


# ─── Application ─────────────────────────────────────────────────────────────
app = Dash(__name__, suppress_callback_exceptions=True)
app.index_string = INDEX_STRING
app.layout = build_layout()

# Injecter dans les stores globaux (avant que le serveur commence à servir)
app.layout["salary-store"].data      = _init_salary
app.layout["app-budget-store"].data  = _init_budget


# ─── Lancement ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=8050)