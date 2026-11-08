"""Monte Carlo et tornado : dispersion induite par les plages [low ; high] de params.yaml.

Les quantiles décrivent la dispersion induite par des plages choisies (en majorité H), pas une
probabilité : on parle de « part des tirages ». Tirages indépendants, sans corrélation.
Éventail conditionnel à E_DC0 et CI_ref constants ; hors périmètre : g_cap, forme du modèle.
Le calcul est celui du noyau `model.project_batch` (aucune formule recopiée ici).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from energywall import model as M
from energywall import sources as S

SORTIES = ("E_dem", "CO2_Mt", "W_hm3")


def mc_config() -> dict:
    mc = S.raw_params().get("monte_carlo")
    if mc is None:
        raise KeyError("section 'monte_carlo' absente de data/params.yaml")
    err: list[str] = []
    S._check_monte_carlo(mc, err)
    if err:
        raise S.ValidationError("; ".join(err))
    return mc


def _bornes() -> pd.DataFrame:
    """Index = paramètre, colonnes low / central / high."""
    return S.load_params().pivot(index="param", columns="borne", values="valeur").astype(float)


def _tires_tous() -> list[str]:
    """Clés des jeux de scénarios, constantes comprises."""
    return list(S.raw_params()["scenarios"]["jeux"]["normal"])


def params_tires() -> list[str]:
    return _tires_tous()


def _variables() -> list[str]:
    b = _bornes()
    return [p for p in _tires_tous() if b.loc[p, "low"] != b.loc[p, "high"]]


def tirages(n: int | None = None, graine: int | None = None, loi: str | None = None):
    cfg = mc_config()
    n = cfg["n_tirages"] if n is None else n
    graine = cfg["graine"] if graine is None else graine
    loi = cfg["loi"] if loi is None else loi
    if loi not in S.LOIS_MC:
        raise ValueError(f"loi inconnue '{loi}' (attendu : {S.LOIS_MC})")
    rng = np.random.default_rng(graine)
    b = _bornes()
    cols = {}
    for p in _tires_tous():
        lo, c, hi = b.loc[p, ["low", "central", "high"]]
        if lo == hi:
            cols[p] = np.full(n, lo)  # constante : aucun tirage
        elif loi == "triangulaire":
            cols[p] = rng.triangular(lo, c, hi, n)
        else:
            cols[p] = rng.uniform(lo, hi, n)
    return pd.DataFrame(cols)


def simulate(n: int | None = None, graine: int | None = None, loi: str | None = None) -> dict:
    par = tirages(n, graine, loi)
    sortie = M.project_batch({k: par[k].to_numpy() for k in par})
    res: dict = {"params": par}
    for s in SORTIES:
        res[s] = pd.DataFrame(sortie[s], columns=pd.Index(M.ANNEES, name="annee"))
    return res


def quantiles(res: dict, sortie: str) -> pd.DataFrame:
    qs = mc_config()["quantiles"]
    q = res[sortie].quantile(qs)
    q.index = qs
    return q.T


def parts_vs_iea(res: dict, annee: int = M.ANNEE1) -> dict:
    """Part des tirages sous la cible optimiste / entre optimiste et pessimiste / au-dessus."""
    e = res["E_dem"][annee].to_numpy()
    opt, pes = M.cible_iea("optimiste", annee), M.cible_iea("pessimiste", annee)
    return {
        "sous_optimiste": float(np.mean(e < opt)),
        "entre": float(np.mean((e >= opt) & (e <= pes))),
        "au_dessus_pessimiste": float(np.mean(e > pes)),
    }


def tornado(sortie: str = "E_dem", annee: int = M.ANNEE1) -> pd.DataFrame:
    """Un paramètre à la fois autour du scénario normal ; trié par amplitude décroissante."""
    base = M.scenario_params("normal")
    b = _bornes()
    h = mc_config()["pas_elasticite"]
    noms = _variables()
    # Une ligne par évaluation : (param, variante, valeur) ; un seul appel du noyau.
    lignes = [("", "base", None)]
    for p in noms:
        c = base[p]
        lignes += [(p, "low", b.loc[p, "low"]), (p, "high", b.loc[p, "high"]),
                   (p, "haut", c * (1 + h)), (p, "bas", c * (1 - h))]
    jeux = {k: np.full(len(lignes), v) for k, v in base.items()}
    for i, (p, _, v) in enumerate(lignes):
        if p:
            jeux[p][i] = v
    y = pd.Series(M.project_batch(jeux)[sortie][:, M.ANNEES.index(annee)])
    y_c = float(y[0])
    rows = []
    for i, p in enumerate(noms):
        y_lo, y_hi, y_up, y_dn = (float(y[1 + 4 * i + k]) for k in range(4))
        rows.append(
            {
                "param": p,
                "y_low": y_lo,
                "y_central": y_c,
                "y_high": y_hi,
                "amplitude": abs(y_hi - y_lo),
                "elasticite": (y_up - y_dn) / (2 * h * y_c),
            }
        )
    df = pd.DataFrame(rows, columns=["param", "y_low", "y_central", "y_high", "amplitude",
                                     "elasticite"])
    return df.sort_values("amplitude", ascending=False, kind="stable").reset_index(drop=True)


def spearman(res: dict, sortie: str = "E_dem", annee: int = M.ANNEE1) -> pd.Series:
    """Corrélation de rang (globale) entre chaque paramètre tiré non constant et la sortie."""
    y = res[sortie][annee].to_numpy()
    rho = {p: float(stats.spearmanr(res["params"][p], y).statistic) for p in _variables()}
    s = pd.Series(rho, name="rho")
    return s.reindex(s.abs().sort_values(ascending=False, kind="stable").index)
