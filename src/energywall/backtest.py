"""CSO + backtest 2020-2025 : confrontation du modèle aux seules données observées.

Lectures retenues :
- CSO = Irlande, quelques sites dominants, périmètre détecté et révisable ; il ne dit rien du
  monde, il est un témoin de dynamique. La décélération +31 % -> +10 % est « compatible avec une
  contrainte d'offre (réseau), non prouvée par ces données ».
- Les origines des pseudo-prévisions se chevauchent (erreurs autocorrélées) : n surestime
  l'information, 11 années ne désignent pas de meilleure méthode. Aucune méthode n'est « validée ».
- Backtest d_CI : la forme rétro-appliquée (b) est DANS l'échantillon (d_CI central dérivé des
  mêmes points), elle ne valide pas la forme ; « dans_plage » est en partie acquis par construction
  (plage H large) ; seul (a) est hors échantillon, sur 1 à 5 points.
- Les séries IEA viennent de deux éditions, non homogènes.
- Les quantiles MC sont des « parts des tirages », jamais des probabilités.
Le modèle n'est pas modifié ni recalé : le point 2025 est une comparaison fixée à l'avance.
Aucune valeur numérique ici : tout vient de data/ (le CSV figé, params.yaml).
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

import numpy as np
import pandas as pd

from energywall import incertitude as I
from energywall import model as M
from energywall import sources as S

TRIMESTRES_PAR_AN = 4  # structurel, pas un paramètre
METHODES = ("glissante", "croissante", "naive")
CODE_DC, CODE_TOTAL = "10", "-"  # codes C03907V04659 de la table MEC02
ORDRE_STATUT = ("D", "S", "V")  # du plus faible au plus fort


def bt_config() -> dict:
    bt = S.raw_params().get("backtest")
    if bt is None:
        raise KeyError("section 'backtest' absente de data/params.yaml")
    err: list[str] = []
    S._check_backtest(bt, err)
    if err:
        raise S.ValidationError("; ".join(err))
    return bt


def _section_obs() -> dict:
    obs = S.raw_params().get("observations")
    if obs is None:
        raise KeyError("section 'observations' absente de data/params.yaml")
    return obs


def observations(serie: str | None = None) -> pd.DataFrame:
    """Niveaux observés (colonnes du yaml), filtrés sur une série si demandé."""
    df = pd.DataFrame(_section_obs()["niveaux"])
    if serie is not None:
        df = df[df["serie"] == serie]
        if df.empty:
            raise KeyError(f"série d'observations inconnue '{serie}'")
    return df.reset_index(drop=True)


def _niveau_obs(serie: str, annee: int) -> float:
    df = observations(serie)
    ligne = df[df["annee"] == annee]
    if ligne.empty:
        raise KeyError(f"pas d'observation {serie} pour {annee}")
    return float(ligne["valeur"].iloc[0])


def _taux_obs(serie: str, debut: int, fin: int) -> float:
    for t in _section_obs()["taux"]:
        if t["serie"] == serie and t["debut"] == debut and t["fin"] == fin:
            return float(t["valeur"])
    raise KeyError(f"pas de taux observé {serie} {debut}-{fin}")


def _annee_trim(label: str) -> int:
    return int(label.split("Q")[0])


def _q_trim(label: str) -> int:
    return int(label.split("Q")[1])


# --- CSO -------------------------------------------------------------------------------------


def cso_trimestriel(chemin: Path | str | None = None, sha256: str | None = None) -> pd.DataFrame:
    """Une ligne par trimestre (DC et total métré, GWh) ; fichier figé, lu hors ligne."""
    cfg = bt_config()
    chemin = S.ROOT / cfg["cso_fichier"] if chemin is None else Path(chemin)
    sha256 = cfg["cso_sha256"] if sha256 is None else sha256
    if not chemin.is_file():
        raise FileNotFoundError(f"fichier CSO figé absent : {chemin}")
    octets = chemin.read_bytes()
    h = hashlib.sha256(octets).hexdigest()
    if h != sha256:
        raise ValueError(f"sha256 du fichier CSO différent : {h} (attendu {sha256})")
    brut = pd.read_csv(io.BytesIO(octets), dtype={"C03907V04659": str})
    manque = {"TLIST(Q1)", "C03907V04659", "VALUE"} - set(brut.columns)
    if manque:
        raise ValueError(f"CSV CSO : colonne(s) manquante(s) {sorted(manque)}")
    tab = brut.pivot(index="TLIST(Q1)", columns="C03907V04659", values="VALUE")
    absents = {CODE_DC, CODE_TOTAL} - set(tab.columns)
    if absents:
        raise ValueError(f"CSV CSO : code(s) C03907V04659 absent(s) {sorted(absents)}")
    tab = tab.rename(columns={CODE_DC: "dc_gwh", CODE_TOTAL: "total_gwh"})
    tab = tab[["dc_gwh", "total_gwh"]].sort_index()
    if tab.isna().any().any():
        raise ValueError("CSV CSO incomplet : trimestre sans valeur DC ou total")
    out = tab.rename_axis("trimestre").reset_index()
    out["annee"] = out["trimestre"].map(_annee_trim)
    out["q"] = out["trimestre"].map(_q_trim)
    out["part"] = out["dc_gwh"] / out["total_gwh"]
    return out[["trimestre", "annee", "q", "dc_gwh", "total_gwh", "part"]]


def cso_annuel() -> pd.DataFrame:
    """Somme des 4 trimestres (écart d'arrondi de 1 GWh avec la Table 1 du CSO, documenté)."""
    tri = cso_trimestriel()
    a = tri.groupby("annee")[["dc_gwh", "total_gwh"]].sum()
    a["part"] = a["dc_gwh"] / a["total_gwh"]
    a["croissance"] = a["dc_gwh"].pct_change()
    return a.reset_index()


def _serie_dc(cfg: dict | None = None) -> pd.Series:
    """Série DC (GWh) indexée par trimestre, après les contrôles qui exigent le CSV."""
    cfg = bt_config() if cfg is None else cfg
    tri = cso_trimestriel()
    serie = tri.set_index("trimestre")["dc_gwh"].astype(float)
    if cfg["annee_test"] != int(tri["annee"].iloc[-1]):
        raise ValueError(
            f"annee_test {cfg['annee_test']} != dernière année du CSO {tri['annee'].iloc[-1]}"
        )
    return serie


def _controler_origines(serie: pd.Series, cfg: dict) -> int:
    """Position de la première origine ; erreur explicite si la config est inapplicable."""
    if cfg["origine_debut"] not in serie.index:
        raise ValueError(f"origine_debut {cfg['origine_debut']} absente de la série")
    pos0 = serie.index.get_loc(cfg["origine_debut"])
    if _debut_fenetre(pos0, cfg["fenetre"]) < 0:
        raise ValueError("origine_debut - fenetre + 1 précède le premier trimestre")
    for h in cfg["horizons"]:
        if pos0 + h > len(serie) - 1:
            raise ValueError(f"aucune origine pour l'horizon {h}")
    return pos0


# --- pseudo-prévisions (rolling origin) -------------------------------------------------------


def _jusqua(serie: pd.Series, origine: str) -> pd.Series:
    """Historique connu à l'origine : points <= origine (garde anti-fuite)."""
    return serie.iloc[: serie.index.get_loc(origine) + 1]


def _debut_fenetre(pos: int, fenetre: int) -> int:
    """Position du premier point de la fenêtre glissante (`fenetre` points, origine incluse)."""
    return pos - fenetre + 1


def _ajuster(hist: pd.Series, methode: str, fenetre: int | None) -> tuple[float, float]:
    """OLS log-linéaire (ordonnée, pente) en fonction de la position dans `hist`."""
    pos = len(hist) - 1
    if methode == "glissante":
        debut = _debut_fenetre(pos, fenetre)
    elif methode == "croissante":
        debut = 0
    else:
        raise ValueError(f"méthode de régression inconnue '{methode}'")
    if debut < 0:
        raise ValueError("historique plus court que la fenêtre")
    pente, ord_ = np.polyfit(np.arange(debut, pos + 1), np.log(hist.to_numpy()[debut:]), 1)
    return float(ord_), float(pente)


def _naive(y_o: float, y_prec: float, h: int) -> float:
    """y_o * (y_o / y_{o-4})^(h/4) : h en TRIMESTRES."""
    return float(y_o * (y_o / y_prec) ** (h / TRIMESTRES_PAR_AN))


def prevoir(
    serie: pd.Series, origine: str, h: int, methode: str, fenetre: int | None = None
) -> float:
    """Prévision à h trimestres depuis `origine`, sans aucune donnée postérieure à l'origine."""
    if methode not in METHODES:
        raise ValueError(f"méthode inconnue '{methode}' (attendu : {METHODES})")
    hist = _jusqua(serie, origine)
    pos = len(hist) - 1
    if methode == "naive":
        if pos < TRIMESTRES_PAR_AN:
            raise ValueError("historique trop court pour la méthode naïve")
        return _naive(hist.iloc[pos], hist.iloc[pos - TRIMESTRES_PAR_AN], h)
    fenetre = bt_config()["fenetre"] if fenetre is None else fenetre
    ord_, pente = _ajuster(hist, methode, fenetre)
    # ŷ = exp(OLS) estime la médiane : biais de Jensen négligé.
    return float(np.exp(ord_ + pente * (pos + h)))


def pseudo_previsions(serie: pd.Series | None = None) -> pd.DataFrame:
    """Méthode, h, origine, cible, y_prevu, y_obs, erreur (relative : y_prevu / y_obs - 1)."""
    cfg = bt_config()
    serie = _serie_dc(cfg) if serie is None else serie
    pos0 = _controler_origines(serie, cfg)
    lignes = []
    for methode in METHODES:
        for h in cfg["horizons"]:
            for pos in range(pos0, len(serie) - h):
                o = serie.index[pos]
                y_prevu = prevoir(serie, o, h, methode, cfg["fenetre"])
                y_obs = float(serie.iloc[pos + h])
                lignes.append(
                    {
                        "methode": methode, "h": h, "origine": o,
                        "cible": serie.index[pos + h], "y_prevu": y_prevu, "y_obs": y_obs,
                        "erreur": y_prevu / y_obs - 1,
                    }
                )  # fmt: skip
    return pd.DataFrame(lignes)


def scores(pp: pd.DataFrame) -> pd.DataFrame:
    """Par (méthode, h) : n, MAPE, biais moyen signé. Les origines se chevauchent."""
    g = pp.groupby(["methode", "h"], sort=False)["erreur"]
    out = pd.DataFrame({"n": g.size(), "mape": g.agg(lambda e: float(np.abs(e).mean())),
                        "biais": g.mean()})  # fmt: skip
    return out.reset_index()


def derive_taux(serie: pd.Series | None = None) -> pd.DataFrame:
    """Par origine : taux annuel implicite exp(4b) - 1 (glissante, croissante) et réalisé."""
    cfg = bt_config()
    serie = _serie_dc(cfg) if serie is None else serie
    pos0 = _controler_origines(serie, cfg)
    lignes = []
    for pos in range(pos0, len(serie)):
        o = serie.index[pos]
        hist = _jusqua(serie, o)
        ligne = {"origine": o}
        for methode in ("glissante", "croissante"):
            pente = _ajuster(hist, methode, cfg["fenetre"])[1]
            ligne[methode] = float(np.exp(TRIMESTRES_PAR_AN * pente) - 1)
        ligne["realise"] = float(serie.iloc[pos] / serie.iloc[pos - TRIMESTRES_PAR_AN] - 1)
        lignes.append(ligne)
    return pd.DataFrame(lignes)


def residus_trimestre(serie: pd.Series | None = None) -> pd.Series:
    """Résidu log moyen par trimestre civil de la régression croissante sur toute la série."""
    serie = _serie_dc() if serie is None else serie
    ord_, pente = _ajuster(serie, "croissante", None)
    res = np.log(serie.to_numpy()) - (ord_ + pente * np.arange(len(serie)))
    q = serie.index.map(_q_trim)
    return pd.Series(res, index=q).groupby(level=0).mean().rename("residu_moyen")


# --- d_CI (Ember) -----------------------------------------------------------------------------


def _ajuster_ci(serie: pd.Series, origine: int, fenetre: int) -> tuple[float, float]:
    annees = np.arange(origine - fenetre + 1, origine + 1)
    pente, ord_ = np.polyfit(annees, np.log(serie.loc[annees].to_numpy()), 1)
    return float(ord_), float(pente)


def d_hat(serie_annuelle: pd.Series, origine: int, fenetre: int) -> float:
    """d̂ = 1 - exp(b), OLS log-linéaire sur les `fenetre` points annuels origine-fenetre+1..origine."""
    return float(1 - np.exp(_ajuster_ci(serie_annuelle, origine, fenetre)[1]))


def _param(nom: str, borne: str) -> float:
    return float(S.load_params().set_index(["param", "borne"]).loc[(nom, borne), "valeur"])


def ci_modele(annee: int, d: float) -> float:
    """CI_ref (1 - d)^(t - annee_ref_CI), même forme que model.project_batch (testée contre lui)."""
    return _param("CI_ref", "central") * (1 - d) ** (annee - _param("annee_ref_CI", "central"))


def backtest_ci() -> dict:
    """(a) d̂ glissant, hors échantillon ; (b) forme du modèle rétro-appliquée (dans l'échantillon)."""
    cfg = bt_config()
    obs = observations("ember_ci_monde")
    ci = obs.set_index("annee")["valeur"].astype(float).sort_index()
    fen = cfg["fenetre_ci"]
    o_min, o_max = _annee_trim(cfg["origine_debut"]), cfg["annee_test"] - 1
    if o_min - fen + 1 < ci.index.min() or cfg["annee_test"] not in ci.index:
        raise ValueError("série Ember insuffisante pour fenetre_ci / annee_test")
    low, high = _param("d_CI", "low"), _param("d_CI", "high")
    glissant, erreurs = [], []
    for o in range(o_min, o_max + 1):
        d = d_hat(ci, o, fen)
        glissant.append({"origine": o, "d_hat": d, "dans_plage": bool(low <= d <= high)})
        ord_, pente = _ajuster_ci(ci, o, fen)
        for t in range(o + 1, cfg["annee_test"] + 1):
            prevu = float(np.exp(ord_ + pente * t))
            erreurs.append({"origine": o, "annee": t, "ci_prevu": prevu, "ci_obs": ci[t],
                            "erreur": prevu / ci[t] - 1})  # fmt: skip
    forme = []
    for borne in S.BORNES:
        d = _param("d_CI", borne)
        for t, obs_t in ci.items():
            mod = ci_modele(t, d)
            forme.append({"annee": t, "borne": borne, "d": d, "ci_mod": mod, "ci_obs": obs_t,
                          "erreur": mod / obs_t - 1})  # fmt: skip
    return {
        "glissant": pd.DataFrame(glissant),
        "erreurs": pd.DataFrame(erreurs),
        "forme_modele": pd.DataFrame(forme),
    }


# --- modèle global ----------------------------------------------------------------------------


def taux_moyen(e, k: int):
    """Taux annuel moyen 2024 -> 2024 + k d'une trajectoire E (Series ou DataFrame par année)."""
    return (e[M.ANNEE0 + k] / e[M.ANNEE0]) ** (1 / k) - 1


def taux_modele(res: dict | None = None) -> pd.DataFrame:
    """Taux 2024 -> annee_test et 2024 -> 2024 + annees_premieres : scénarios et quantiles MC."""
    cfg = bt_config()
    res = I.simulate() if res is None else res
    k_test, k_prem = cfg["annee_test"] - M.ANNEE0, cfg["annees_premieres"]
    scen = M.run_scenarios()["E_dem"]
    lignes = [
        {"ligne": s, "type": "scenario", "taux_test": taux_moyen(scen.loc[s], k_test),
         "taux_premieres": taux_moyen(scen.loc[s], k_prem)}
        for s in M.SCENARIOS
    ]  # fmt: skip
    e = res["E_dem"]
    qs = I.mc_config()["quantiles"]
    q_test = taux_moyen(e, k_test).quantile(qs)
    q_prem = taux_moyen(e, k_prem).quantile(qs)
    lignes += [
        {"ligne": f"q{q:g}", "type": "mc", "taux_test": float(q_test[q]),
         "taux_premieres": float(q_prem[q])}
        for q in qs
    ]  # fmt: skip
    return pd.DataFrame(lignes)


def point_2025(res: dict | None = None) -> dict:
    """Point `annee_test` : taux M.ANNEE0 -> annee_test PRINCIPAL, puis niveau.

    Les observations (taux IEA [V], niveau IEA [S]) sont lues dans `observations`. Si le taux
    observé est hors de [plus petit ; plus grand] quantile de la config MC, `hors_intervalle` est
    vrai (« non reproduit par le modèle ») ; aucun ajustement. Parts = parts des tirages.
    """
    cfg = bt_config()
    res = I.simulate() if res is None else res
    an, k = cfg["annee_test"], cfg["annee_test"] - M.ANNEE0
    taux_obs = _taux_obs("iea_monde", M.ANNEE0, an)
    niv_obs = _niveau_obs("iea_monde", an)
    scen = M.run_scenarios()["E_dem"]
    qs = I.mc_config()["quantiles"]
    e = res["E_dem"]
    taux_mc = taux_moyen(e, k)
    q_taux, q_niv = taux_mc.quantile(qs), e[an].quantile(qs)
    bas, haut = float(q_taux[min(qs)]), float(q_taux[max(qs)])
    return {
        "annee": an,
        "taux_observe": taux_obs,
        "niveau_observe": niv_obs,
        "taux_scenarios": {s: float(taux_moyen(scen.loc[s], k)) for s in M.SCENARIOS},
        "niveaux_scenarios": {s: float(scen.loc[(s, an)]) for s in M.SCENARIOS},
        "taux_quantiles": q_taux,
        "niveaux_quantiles": q_niv,
        "intervalle_taux": (bas, haut),
        "hors_intervalle": bool(taux_obs < bas or taux_obs > haut),
        "ecart_taux": float(taux_obs - bas) if taux_obs < bas
        else float(taux_obs - haut) if taux_obs > haut else 0.0,
        "part_taux_ge": float(np.mean(taux_mc >= taux_obs)),
        "ecart_niveau_scenarios": {
            s: float(scen.loc[(s, an)] / niv_obs - 1) for s in M.SCENARIOS
        },
        "ecart_niveau_quantiles": q_niv / niv_obs - 1,
        "part_niveau_le": float(np.mean(e[an] <= niv_obs)),
        "part_niveau_ge": float(np.mean(e[an] >= niv_obs)),
    }


def _statut_effectif(statuts: list[str]) -> str:
    return min(statuts, key=ORDRE_STATUT.index)


def taux_observes() -> pd.DataFrame:
    """Taux observés ou dérivés, avec zone, période, édition et statut effectif. Aucune cible."""
    sources = {s["id"]: s for s in S.raw_sources()}
    lignes = []
    for t in _section_obs()["taux"]:
        lignes.append(
            {
                "serie": t["serie"], "zone": t["perimetre"].split(",")[0], "debut": t["debut"],
                "fin": t["fin"], "taux": float(t["valeur"]), "edition": t["edition"],
                "statut": t["statut"], "statut_effectif": t["statut"],
                "source_ids": list(t["source_ids"]),
                "formule": "valeur publiée",
            }
        )  # fmt: skip
    # LBNL : taux annuel moyen entre les deux niveaux observés (statut D, effectif = plus faible).
    lb = observations("lbnl_us").sort_values("annee")
    d0, d1 = lb.iloc[0], lb.iloc[-1]
    ids = sorted({i for x in lb["source_ids"] for i in x})
    lignes.append(
        {
            "serie": "lbnl_us", "zone": d0["perimetre"].split(",")[0], "debut": int(d0["annee"]),
            "fin": int(d1["annee"]),
            "taux": float((d1["valeur"] / d0["valeur"]) ** (1 / (d1["annee"] - d0["annee"])) - 1),
            "edition": sources[ids[0]]["titre"], "statut": "D",
            "statut_effectif": _statut_effectif(list(lb["statut"])), "source_ids": ids,
            "formule": "(v_fin / v_debut)^(1 / (fin - debut)) - 1",
        }
    )  # fmt: skip
    # CSO : mêmes périodes que les taux IEA, plus l'année précédant l'ancrage.
    cfg, annuel = bt_config(), cso_annuel().set_index("annee")["dc_gwh"]
    periodes = [(t["debut"], t["fin"]) for t in _section_obs()["taux"]]
    periodes.insert(1, (M.ANNEE0 - 1, M.ANNEE0))
    lu = sources["cso_irlande"]["statut_lecture"] == "lu_source"
    for debut, fin in periodes:
        lignes.append(
            {
                "serie": "cso_dc", "zone": "Irlande", "debut": debut, "fin": fin,
                "taux": float((annuel[fin] / annuel[debut]) ** (1 / (fin - debut)) - 1),
                "edition": cfg["cso_edition"], "statut": "D",
                "statut_effectif": "V" if lu else "S", "source_ids": ["cso_irlande"],
                "formule": "(v_fin / v_debut)^(1 / (fin - debut)) - 1",
            }
        )  # fmt: skip
    return pd.DataFrame(lignes)
