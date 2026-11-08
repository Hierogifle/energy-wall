"""Modèle structurel déterministe type Kaya : TWh, CO2e, eau, 2024-2035, pas annuel.

Aucune valeur de paramètre ici : tout vient de data/params.yaml via sources.load_params().
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from energywall import sources as S

ANNEE0 = 2024
ANNEE1 = 2035
ANNEES = list(range(ANNEE0, ANNEE1 + 1))
KT_PAR_MT = 1000.0  # 1 TWh x 1 g/kWh = 1 kt ; /1000 -> Mt
J_PAR_TWH = 3.6e15  # 1 TWh = 3,6e15 J
HM3_PAR_TWH_L_KWH = 1.0  # 1 TWh x 1 L/kWh = 1e9 L = 1 hm3
SCENARIOS = ("pessimiste", "normal", "optimiste")
COLONNES = ["E_conv", "E_train", "E_inf", "E_dem", "PUE", "CI", "CO2_Mt", "W_hm3"]


class CibleInatteignable(Exception):
    """La cible est hors de [E_dem(borne basse), E_dem(borne haute)] du bracket."""

    def __init__(self, cible: float, e_bas: float, e_haut: float):
        super().__init__(
            f"cible {cible:.6g} TWh hors de l'intervalle atteignable [{e_bas:.6g} ; {e_haut:.6g}]"
        )
        self.cible, self.e_bas, self.e_haut = cible, e_bas, e_haut


def _table() -> pd.DataFrame:
    return S.load_params().set_index(["param", "borne"])["valeur"].astype(float)


def scenario_params(nom: str) -> dict[str, float]:
    jeu = S.raw_params()["scenarios"]["jeux"].get(nom)
    if jeu is None:
        raise KeyError(f"scénario inconnu '{nom}'")
    t = _table()
    return {p: float(t[(p, borne)]) for p, borne in jeu.items()}


def trajectoire(g_2025, g_2035) -> np.ndarray:
    """Facteur cumulé F(t), t = 2024..2035 ; taux log linéaire décroissant par étape.

    Scalaires -> (12,) ; vecteurs (N,) -> (N, 12).
    """
    r = np.linspace(np.log(g_2025), np.log(g_2035), len(ANNEES) - 1, axis=-1)
    zero = np.zeros(r.shape[:-1] + (1,))
    return np.exp(np.concatenate([zero, np.cumsum(r, axis=-1)], axis=-1))


def co2_mt(e_twh, ci_g_kwh):
    return e_twh * ci_g_kwh / KT_PAR_MT


def eau_hm3(e_twh, pue, wue_site, ewif):
    # Eau sur site sur l'énergie IT (E/PUE) + eau hors site sur l'énergie électrique.
    return (e_twh / pue * wue_site + e_twh * ewif) * HM3_PAR_TWH_L_KWH


def project_batch(p: dict) -> dict[str, np.ndarray]:
    """Noyau vectorisé : p[nom] scalaire ou vecteur (N,) -> chaque sortie en forme (N, 12)."""
    q = {k: np.atleast_1d(np.asarray(v, dtype=float))[:, None] for k, v in p.items()}  # (N, 1)
    n = np.arange(len(ANNEES), dtype=float)  # (12,)
    pue = q["PUE_2024"] + (q["PUE_2035"] - q["PUE_2024"]) * n / (len(ANNEES) - 1)
    ratio_pue = pue / q["PUE_2024"]
    f_hw = 2.0 ** (n / q["T_d_parc"])
    e_ia = q["E_DC0"] * q["s_AI"]
    e_conv = q["E_DC0"] * (1 - q["s_AI"]) * (1 + q["g_conv"]) ** n * ratio_pue
    f_train = trajectoire(q["g_Ctrain_2025"][:, 0], q["g_Ctrain_2035"][:, 0])
    f_tok = trajectoire(q["g_tok_2025"][:, 0], q["g_tok_2035"][:, 0])
    e_train = e_ia * q["s_train"] * f_train / f_hw * ratio_pue
    e_inf = e_ia * (1 - q["s_train"]) * f_tok * q["g_fpt_net"] ** n / f_hw * ratio_pue
    e_dem = e_conv + e_train + e_inf
    ci = q["CI_ref"] * (1 - q["d_CI"]) ** (np.array(ANNEES) - q["annee_ref_CI"])
    return {
        "E_conv": e_conv,
        "E_train": e_train,
        "E_inf": e_inf,
        "E_dem": e_dem,
        "PUE": pue,
        "CI": ci,
        "CO2_Mt": co2_mt(e_dem, ci),
        "W_hm3": eau_hm3(e_dem, pue, q["WUE_site"], q["EWIF"]),
    }


def project(p: dict[str, float]) -> pd.DataFrame:
    out = project_batch(p)
    return pd.DataFrame(
        {k: out[k][0] for k in COLONNES}, index=pd.Index(ANNEES, name="annee")
    )


def run_scenarios() -> pd.DataFrame:
    """MultiIndex (scenario, annee)."""
    return pd.concat({s: project(scenario_params(s)) for s in SCENARIOS}, names=["scenario"])


def cible_iea(scenario: str, annee: int = ANNEE1) -> float:
    for c in S.raw_params()["cibles_iea"]:
        if c["scenario"] == scenario and c["annee"] == annee:
            return float(c["valeur"])
    raise KeyError(f"pas de cible IEA {annee} pour '{scenario}'")


def implied_param(
    scenario: str,
    cible_2035: float,
    param: str = "g_tok_2025",
    bracket: tuple[float, float] = (1.0, 10.0),
    rtol: float = 1e-6,
) -> tuple[float, bool]:
    """Diagnostic : valeur de `param` qui donne E_dem(2035) = cible ; (valeur, dans_plage)."""
    base = scenario_params(scenario)
    if param not in base:
        raise ValueError(f"paramètre inconnu '{param}' (attendu : {sorted(base)})")

    def f(x: float) -> float:
        return float(project({**base, param: x}).loc[ANNEE1, "E_dem"])

    e_bas, e_haut = f(bracket[0]), f(bracket[1])
    if not e_haut > e_bas:
        raise ValueError(
            f"E_dem(2035) non croissante en '{param}' sur {bracket} : {e_bas:.6g} -> {e_haut:.6g}"
        )
    if not (e_bas <= cible_2035 <= e_haut):
        raise CibleInatteignable(cible_2035, e_bas, e_haut)
    x = brentq(lambda v: f(v) - cible_2035, *bracket, rtol=rtol, xtol=1e-12)
    t = _table()
    return float(x), bool(t[(param, "low")] <= x <= t[(param, "high")])


def wall_stress(scenario: str) -> pd.DataFrame:
    """E_cap et E_wall = max(0, E_dem - E_cap) pour chaque borne de g_cap (hors scénarios)."""
    e_dem = project(scenario_params(scenario))["E_dem"]
    out = {"E_dem": e_dem}
    for borne in S.BORNES:
        out[f"E_cap_{borne}"] = pd.Series(e_cap(scenario, borne), index=e_dem.index)
        out[f"E_wall_{borne}"] = (e_dem - out[f"E_cap_{borne}"]).clip(lower=0.0)
    return pd.DataFrame(out)


def co2_incorpore_mt(e_twh, r_s3, ci_ref):
    """Carbone incorporé du matériel IT (Mt) ; intensité incorporée r_s3 x CI_ref constante."""
    return r_s3 * e_twh * ci_ref / KT_PAR_MT


def carbone_incorpore(scenario: str) -> pd.DataFrame:
    """Sous-ensemble du scope 3, ordre de grandeur, à part : jamais additionné à CO2_Mt.

    Par borne de r_s3 : CO2_incorpore_Mt, intensité incorporée (g/kWh) et ratio effectif
    s3/s2(t) = r_s3 x CI_ref / CI(t). r_s3 est hors scénarios (scenarios.jeux) et hors MC.
    """
    p = scenario_params(scenario)
    t = _table()
    d = project(p)
    out = {"E_dem": d["E_dem"], "CI": d["CI"], "CO2_Mt": d["CO2_Mt"]}
    for borne in S.BORNES:
        r = t[("r_s3", borne)]
        out[f"CO2_incorpore_Mt_{borne}"] = co2_incorpore_mt(d["E_dem"], r, p["CI_ref"])
        out[f"intensite_incorporee_g_kwh_{borne}"] = pd.Series(r * p["CI_ref"], index=d.index)
        out[f"ratio_effectif_{borne}"] = r * p["CI_ref"] / d["CI"]
    return pd.DataFrame(out)


CRITERES = ("2035", "trajectoire")
STATUTS_MIRACLE = ("ok", "sous_plancher", "non_contraignant")
ZONES = ("plus_rapide_que_la_pointe", "le_parc_suit_la_pointe", "plausible")


def _miracle_cfg() -> dict:
    return S.raw_params()["miracle"]


def _zone(t_star: float) -> str:
    pe = _miracle_cfg()["pointe_epoch"]
    if t_star < pe["low"]["valeur"]:
        return ZONES[0]
    return ZONES[1] if t_star <= pe["high"]["valeur"] else ZONES[2]


def e_cap(scenario: str, borne: str) -> np.ndarray:
    """Trajectoire E_cap(t) = E_DC0 (1 + g_cap)^n pour une borne de g_cap."""
    p = scenario_params(scenario)
    n = np.arange(len(ANNEES), dtype=float)
    return p["E_DC0"] * (1 + _table()[("g_cap", borne)]) ** n


def t_d_max_admissible(scenario: str, cible, critere: str = "2035") -> dict:
    """T_d_parc maximal tel que E_dem respecte `cible` (niveau constant ou trajectoire C(t)).

    E_dem(t > 2024) est strictement croissant en T_d_parc : on cherche le plus grand T qui
    tient la cible. Critère "2035" : E_dem(2035) <= C(2035) ; "trajectoire" : E_dem(t) <= C(t)
    pour t = 2025..2035. Hypothèse conditionnelle : seul T_d_parc bouge (E_conv inchangé).
    """
    if critere not in CRITERES:
        raise ValueError(f"critère inconnu '{critere}' (attendu : {CRITERES})")
    base = scenario_params(scenario)
    c = np.broadcast_to(np.asarray(cible, dtype=float), (len(ANNEES),))

    def exces(t_d: float) -> np.ndarray:
        return project({**base, "T_d_parc": t_d})["E_dem"].to_numpy() - c

    def g(t_d: float) -> float:
        e = exces(t_d)
        return float(e[-1] if critere == "2035" else e[1:].max())

    bas, haut = _miracle_cfg()["bracket_T_d"]
    g_bas, g_haut = g(bas), g(haut)
    if np.isnan(g_bas) or np.isnan(g_haut):
        raise ValueError(f"t_d_max_admissible : g(T_d) NaN aux bornes {(bas, haut)} ({scenario})")
    if g_bas > 0:
        t_star, statut = None, "sous_plancher"
    elif g_haut <= 0:
        t_star, statut = None, "non_contraignant"
    else:
        t_star, statut = float(brentq(g, bas, haut, rtol=1e-10, xtol=1e-12)), "ok"
    return {
        "T_star": t_star,
        "statut": statut,
        "T_d_parc": base["T_d_parc"],
        "deja_tenue": statut == "non_contraignant"
        or (t_star is not None and base["T_d_parc"] <= t_star),
        "zone": None if t_star is None else _zone(t_star),
        "max_E_wall": None if t_star is None else float(max(0.0, exces(t_star).max())),
    }


def miracle_table() -> pd.DataFrame:
    """3 scénarios x cibles (borne basse IEA 2035 ; E_cap par borne de g_cap) x 2 critères."""
    plancher = min(float(c["valeur"]) for c in S.raw_params()["cibles_iea"] if c["annee"] == ANNEE1)
    rows = []
    for s in SCENARIOS:
        cibles = {"IEA bas 2035": plancher} | {f"E_cap g_cap {b}": e_cap(s, b) for b in S.BORNES}
        for nom, cible in cibles.items():
            for critere in CRITERES:
                rows.append({"scenario": s, "cible": nom, "critere": critere}
                            | t_d_max_admissible(s, cible, critere))
    return pd.DataFrame(rows)


def bottom_up_check() -> dict:
    """E_bu = (C_train + 2 N_act Tokens)/eff_eff x PUE_2024 vs E_DC0 x s_AI (affiché, non utilisé)."""
    t = _table()

    def e_bu(c, n, tok, eff, pue):
        return (c + 2 * n * tok) / eff * pue / J_PAR_TWH

    def v(nom, borne):
        return t[(nom, borne)]

    central = e_bu(*(v(k, "central") for k in ("C_train_2024", "N_act", "Tokens_2024", "eff_eff", "PUE_2024")))
    # Bornes croisées : tout au plus bas / tout au plus haut (eff_eff inversé).
    bas = e_bu(v("C_train_2024", "low"), v("N_act", "low"), v("Tokens_2024", "low"),
               v("eff_eff", "high"), v("PUE_2024", "low"))
    haut = e_bu(v("C_train_2024", "high"), v("N_act", "high"), v("Tokens_2024", "high"),
                v("eff_eff", "low"), v("PUE_2024", "high"))
    ref = v("E_DC0", "central") * v("s_AI", "central")
    return {
        "E_bu": float(central),
        "E_bu_min": float(bas),
        "E_bu_max": float(haut),
        "E_ref": float(ref),
        "ratio": float(central / ref),
        "ratio_min": float(bas / ref),
        "ratio_max": float(haut / ref),
    }
