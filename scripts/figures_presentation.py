"""Exporte les données des graphiques du diaporama dans presentation/data.js.

Toutes les valeurs viennent du modèle (src/energywall) et de data/params.yaml :
le diaporama ne contient aucun chiffre de scénario écrit à la main.

    uv run python scripts/figures_presentation.py
"""

import json
from pathlib import Path

from energywall import model as M
from energywall import sources as S

SORTIE = Path(__file__).resolve().parents[1] / "presentation" / "data.js"
HEURES_PAR_AN = 8760
QUARTS_HEURE_PAR_AN = 365 * 24 * 4


def main() -> None:
    res = M.run_scenarios()
    annees = [int(a) for a in M.ANNEES]

    scenarios = {}
    for s in M.SCENARIOS:
        mur = M.wall_stress(s)
        scenarios[s] = {
            "twh": [round(float(v), 1) for v in res.loc[s, "E_dem"]],
            "co2_mt": [round(float(v), 1) for v in res.loc[s, "CO2_Mt"]],
            "eau_hm3": [round(float(v), 1) for v in res.loc[s, "W_hm3"]],
            "capacite_twh": {
                borne: [round(float(v), 1) for v in mur[f"E_cap_{borne}"]]
                for borne in S.BORNES
            },
        }

    miracle = M.miracle_table()
    sel = miracle[(miracle["critere"] == "trajectoire") & (miracle["cible"] == "IEA bas 2035")]
    t_star = {r["scenario"]: round(float(r["T_star"]), 2) for _, r in sel.iterrows()}
    pointe = S.raw_params()["miracle"]["pointe_epoch"]

    i2029 = annees.index(2029)
    twh_2029 = {s: scenarios[s]["twh"][i2029] for s in M.SCENARIOS}

    data = {
        "annees": annees,
        "scenarios": scenarios,
        "cibles_iea": [
            {"annee": c["annee"], "cas": c["cas_iea"], "twh": c["valeur"]}
            for c in S.raw_params()["cibles_iea"]
        ],
        "miracle": {
            "cible": "IEA bas 2035 (700 TWh), critère trajectoire",
            "t_star_ans": t_star,
            "pointe_epoch_ans": [pointe["low"]["valeur"], pointe["high"]["valeur"]],
        },
        "unites_parlantes": {
            "gw_moyens_2024": round(scenarios["normal"]["twh"][0] * 1000 / HEURES_PAR_AN, 1),
            "gw_moyens_2029": {
                s: round(v * 1000 / HEURES_PAR_AN, 1) for s, v in twh_2029.items()
            },
            "gwh_par_quart_heure_2029": {
                s: round(v * 1000 / QUARTS_HEURE_PAR_AN, 1) for s, v in twh_2029.items()
            },
        },
    }

    SORTIE.write_text(
        "// Généré par scripts/figures_presentation.py, ne pas modifier à la main.\n"
        f"window.ENERGY_WALL = {json.dumps(data, ensure_ascii=False, indent=1)};\n",
        encoding="utf-8",
    )
    print(f"Écrit : {SORTIE}")
    print(json.dumps(data["unites_parlantes"], indent=1))
    print(json.dumps(data["miracle"], ensure_ascii=False))


if __name__ == "__main__":
    main()
