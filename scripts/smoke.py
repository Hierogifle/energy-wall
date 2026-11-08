"""Smoke L-02/L-03/L-08/L20261016 : registre, paramètres, modèle, Monte Carlo + tornado, CSO + backtest.

Une ligne `OK|FAIL <invariant> <détail>` par invariant ; code 0 si tous tiennent.
`--mutation-check` : mutations en mémoire ; code 0 si chacune fait échouer un invariant.
Déterministe (graine du yaml).
"""

from __future__ import annotations

import copy
import csv
import hashlib
import itertools
import re
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import nbformat
import numpy as np
import pandas as pd

from energywall import backtest as B
from energywall import incertitude as I
from energywall import model as M
from energywall import sources as S

ROOT = Path(__file__).resolve().parents[1]


def _ids(srcs):
    return {s["id"]: s for s in srcs}


def inv_registre_valide(srcs, params):
    # E2 : le registre et les paramètres passent validate()
    try:
        S.validate(srcs, params)
    except S.ValidationError as e:
        return False, str(e).splitlines()[0]
    return True, f"{len(srcs)} sources"


def inv_biais_non_vide(srcs, params):
    # E2 : chaque source porte au moins un biais qualifié (description, sens, grandeur)
    vides = [
        s.get("id", "?")
        for s in srcs
        if not s.get("biais") or any(not (b.get("description") and b.get("sens") and b.get("grandeur")) for b in s["biais"])
    ]
    return not vides, f"sans biais : {vides}" if vides else "toutes les sources"


def inv_bornes_tracables(srcs, params):
    # E5 : chaque borne = (H justifiée) ou (source du registre), par borne
    ids = _ids(srcs)
    mal = []
    for name, p in params["params"].items():
        for b in S.BORNES:
            x = p.get(b) or {}
            if x.get("statut") == "H":
                ok = bool((x.get("justification") or "").strip())
            else:
                sid = x.get("source_ids") or []
                ok = bool(sid) and all(i in ids for i in sid)
            if not ok:
                mal.append(f"{name}.{b}")
    n = sum(len(S.BORNES) for _ in params["params"])
    return not mal, f"{n} bornes" if not mal else f"non tracables : {mal}"


def inv_v_s_lisibles(srcs, params):
    # E5 : V cite lu_source, S cite relais ou lu_source
    ids = _ids(srcs)
    mal = []
    for name, p in params["params"].items():
        for b in S.BORNES:
            x = p.get(b) or {}
            for i in x.get("source_ids") or []:
                lect = ids.get(i, {}).get("statut_lecture")
                if x.get("statut") == "V" and lect != "lu_source":
                    mal.append(f"{name}.{b}->{i}")
                if x.get("statut") == "S" and lect not in ("relais", "lu_source"):
                    mal.append(f"{name}.{b}->{i}")
    return not mal, f"incohérences : {mal}" if mal else "V/S cohérents"


def inv_rapport_non_vide(srcs, params):
    # E5 : les zones non qualifiées sont comptées et affichées (jamais masquées)
    try:
        r = S.qualification_report(srcs, params)
    except Exception as e:  # noqa: BLE001
        return False, f"rapport en échec : {e}"
    total = sum(r["bornes_par_statut"].values())
    # comptage indépendant des intérêts inconnus (NT / non trouvé) : le rapport doit les voir
    nt = sum(
        "NT" in re.findall(r"\w+", str(s.get("interet") or ""))
        or "non trouv" in str(s.get("interet") or "").lower()
        for s in srcs
    )
    ok = (
        r["n_biais"] > 0
        and r["n_sens_indetermine"] > 0
        and r["n_interet_nt"] == nt
        and total == r["n_bornes"] == 3 * len(params["params"])
    )
    return ok, (
        f"biais={r['n_biais']} sens_indetermine={r['n_sens_indetermine']} "
        f"interet_a_qualifier={r['n_interet_a_qualifier']} interet_nt={r['n_interet_nt']}/{nt} "
        f"bornes={r['bornes_par_statut']}"
    )


def inv_identite_2024(srcs, params):
    # E4 : E_dem(2024) = E_DC0 pour chaque scénario
    ecarts = {s: M.project(M.scenario_params(s)).loc[2024, "E_dem"] - M.scenario_params(s)["E_DC0"] for s in M.SCENARIOS}
    mal = {s: e for s, e in ecarts.items() if abs(e) > 1e-6}
    return not mal, f"écarts {mal}" if mal else "E_dem(2024)=E_DC0 (3 scénarios)"


def inv_croissances_neutres(srcs, params):
    # E4 : sans croissance ni gain, E(t) = E_DC0
    p = M.scenario_params("normal")
    p.update(g_conv=0.0, g_Ctrain_2025=1.0, g_Ctrain_2035=1.0, g_tok_2025=1.0, g_tok_2035=1.0,
             g_fpt_net=1.0, T_d_parc=1e12, PUE_2035=p["PUE_2024"])
    e = M.project(p)["E_dem"].to_numpy()
    return bool(np.allclose(e, p["E_DC0"], rtol=1e-9)), f"max|E-E_DC0|={abs(e - p['E_DC0']).max():.2e}"


def inv_trajectoire_decroissante(srcs, params):
    # E4 : taux annuel de g_tok de g_2025 (étape 1) à g_2035 (étape 11), strictement décroissant
    p = M.scenario_params("normal")
    F = M.trajectoire(p["g_tok_2025"], p["g_tok_2035"])
    taux = F[1:] / F[:-1]
    ok = bool(np.isclose(taux[0], p["g_tok_2025"]) and np.isclose(taux[-1], p["g_tok_2035"]) and np.all(np.diff(taux) < 0))
    return ok, f"taux {taux[0]:.3f} -> {taux[-1]:.3f}"


def inv_unites(srcs, params):
    # E4 : 415 TWh x 458 g/kWh = 190,07 Mt ; 1 TWh x 1 L/kWh = 1 hm3
    co2 = M.co2_mt(415.0, 458.0)
    eau = M.eau_hm3(1.0, 1.0, 0.0, 1.0)
    return abs(co2 - 190.07) < 0.005 and abs(eau - 1.0) < 1e-12, f"CO2={co2:.3f} Mt eau={eau:.3f} hm3"


def inv_ordre_scenarios(srcs, params):
    # E3 : pessimiste = consommation haute ; optimiste < normal < pessimiste chaque année >= 2026
    d = M.run_scenarios()
    mal = [a for a in range(2026, 2036)
           if not d.loc[("optimiste", a), "E_dem"] < d.loc[("normal", a), "E_dem"] < d.loc[("pessimiste", a), "E_dem"]]
    return not mal, f"années en désordre : {mal}" if mal else "ordre respecté 2026-2035"


def inv_forme_annuelle(srcs, params):
    # E4 : 12 lignes, index entier 2024-2035, aucune valeur non finie
    mal = []
    for s in M.SCENARIOS:
        df = M.project(M.scenario_params(s))
        if list(df.index) != list(range(2024, 2036)) or df.index.dtype.kind != "i" or not np.isfinite(df.to_numpy()).all():
            mal.append(s)
    return not mal, f"formes invalides : {mal}" if mal else "12 années entières, valeurs finies"


def inv_non_cale(srcs, params):
    # E3 (amendée) : le calage est un diagnostic ; les scénarios ne sont pas forcés sur l'IEA
    # (écart à la cible > 1 % pour au moins un scénario) et le diagnostic atteint la cible.
    d = M.run_scenarios()
    ecarts = {s: d.loc[(s, 2035), "E_dem"] / M.cible_iea(s) - 1 for s in M.SCENARIOS}
    x, _ = M.implied_param("normal", M.cible_iea("normal"))
    e = M.project({**M.scenario_params("normal"), "g_tok_2025": x}).loc[2035, "E_dem"]
    ok = max(abs(v) for v in ecarts.values()) > 0.01 and abs(e / M.cible_iea("normal") - 1) < 1e-6
    return ok, " ".join(f"{s}={v:+.1%}" for s, v in ecarts.items())


def inv_mur(srcs, params):
    # E4 / plan « mur séparé » : E_wall >= 0 et nul en 2024, pour chaque scénario x g_cap
    mal = []
    for s in M.SCENARIOS:
        w = M.wall_stress(s)
        cols = [c for c in w.columns if c.startswith("E_wall_")]
        if (w[cols] < 0).any().any() or (w.loc[2024, cols] != 0).any():
            mal.append(s)
    return not mal, f"mur invalide : {mal}" if mal else "E_wall >= 0, nul en 2024"


def inv_bottom_up(srcs, params):
    # E4 : contrôle bottom-up fini, positif, bornes ordonnées (affiché, non utilisé)
    r = M.bottom_up_check()
    ok = 0 < r["E_bu_min"] < r["E_bu"] < r["E_bu_max"] and np.isfinite(r["ratio"])
    return bool(ok), f"E_bu={r['E_bu']:.2f} TWh ratio={r['ratio']:.3f}"


def inv_pue_trois_postes(srcs, params):
    # E4 : le ratio PUE(t)/PUE_2024 s'applique à E_conv, E_train, E_inf (PUE variable, forme fermée)
    p = M.scenario_params("normal")
    p.update(g_conv=0.0, g_Ctrain_2025=1.0, g_Ctrain_2035=1.0, g_tok_2025=1.0, g_tok_2035=1.0,
             g_fpt_net=1.0, T_d_parc=1e12, PUE_2024=1.4, PUE_2035=1.8)
    df = M.project(p)
    r = 1.8 / 1.4
    e_ia = p["E_DC0"] * p["s_AI"]
    att = {"E_conv": p["E_DC0"] * (1 - p["s_AI"]) * r, "E_train": e_ia * p["s_train"] * r,
           "E_inf": e_ia * (1 - p["s_train"]) * r}
    mal = [k for k, v in att.items() if not np.isclose(df.loc[2035, k], v, rtol=1e-9)]
    return not mal, f"postes sans ratio PUE : {mal}" if mal else "ratio PUE sur 3 postes"


def inv_miracle(srcs, params):
    # L2 / E12 : T_d_max admissible. Par scénario x cible : T*_traj <= T*_2035, statuts valides,
    # E_dem(2035) croissant en T_d_parc, E_dem(2035; T*) = cible (IEA), zone cohérente avec la pointe.
    pe = params["miracle"]["pointe_epoch"]
    lo, hi = pe["low"]["valeur"], pe["high"]["valeur"]
    cible = M.cible_iea("optimiste")
    mal = []
    t = M.miracle_table()
    if not t["statut"].isin(M.STATUTS_MIRACLE).all():
        mal.append("statut invalide")
    for (s, c), g in t.groupby(["scenario", "cible"]):
        r = g.set_index("critere")["T_star"]
        if r.notna().all() and r["trajectoire"] > r["2035"] + 1e-9:
            mal.append(f"T*_traj>T*_2035 {s}/{c}")
    w = t.pivot_table(index=["scenario", "cible"], columns="critere", values="T_star")
    if not (w["trajectoire"] < w["2035"] - 1e-9).any():  # E_cap : la bosse existe
        mal.append("critère trajectoire jamais plus strict que 2035")
    for _, r in t[t["T_star"].notna()].iterrows():
        z = M.ZONES[0] if r["T_star"] < lo else M.ZONES[1] if r["T_star"] <= hi else M.ZONES[2]
        if r["zone"] != z:
            mal.append(f"zone {r['scenario']}/{r['cible']}/{r['critere']}")
    for s in M.SCENARIOS:
        p = M.scenario_params(s)
        e = [M.project({**p, "T_d_parc": x}).loc[2035, "E_dem"] for x in (1.0, 2.0, 4.0, 8.0)]
        if not all(a < b for a, b in itertools.pairwise(e)):
            mal.append(f"E_dem non croissant en T_d {s}")
        r = M.t_d_max_admissible(s, cible, "2035")
        e35 = M.project({**p, "T_d_parc": r["T_star"]}).loc[2035, "E_dem"] if r["T_star"] else None
        if e35 is None or abs(e35 / cible - 1) > 1e-6:
            mal.append(f"cible non atteinte {s}")
    return not mal, f"{len(t)} lignes" if not mal else f"miracle : {mal[:3]}"


NB_PY = ROOT / "notebooks" / "energy_wall.py"
NB_IPYNB = NB_PY.with_suffix(".ipynb")
# Littéraux tolérés dans les cellules de code : tailles de figure, transparence, marges,
# pourcentage (100), largeur d'affichage (200), colonnes (110). Toute autre valeur numérique doit
# venir de data/*.yaml. Aucune valeur ne doit coller à un paramètre du modèle (ex. 0.15, 0.35, 415).
# Faux négatifs connus : float("1.4") ou int("415") (chaînes), valeurs dans LITTERAUX_OK qui
# coïncideraient avec une valeur du modèle, constantes calculées (2 * 207.5), nombres en markdown.
LITTERAUX_OK = {0, 1, 2, 3, 5, 8, 9, 15, 100, 110, 150, 200, 0.3, 4.5}


def _charger_notebook():
    """Cellules (type, source) lues par jupytext pour le .py et le .ipynb (hors outputs)."""
    import jupytext

    def cells(path):
        nb = jupytext.read(path)
        return [(c.cell_type, c.source) for c in nb.cells]

    return cells(NB_PY), cells(NB_IPYNB)


def _litteraux_suspects(cellules):
    import ast

    mal = []
    for typ, src in cellules:
        if typ != "code":
            continue
        for n in ast.walk(ast.parse(src)):
            if (isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
                    and not isinstance(n.value, bool) and n.value not in LITTERAUX_OK):
                mal.append(n.value)
    return mal


def inv_notebook_synchronise(srcs, params):
    # Lot 04 : .py et .ipynb présents, même source de cellules (outputs ignorés)
    if not (NB_PY.exists() and NB_IPYNB.exists()):
        return False, "notebook .py ou .ipynb absent"
    py, nb = _charger_notebook()
    return py == nb, f"{len(py)} cellules .py / {len(nb)} cellules .ipynb"


def inv_notebook_sans_chiffre_en_dur(srcs, params):
    # Lot 04 : heuristique, aucun littéral numérique hors LITTERAUX_OK dans les cellules de code
    if not NB_PY.exists():
        return False, "notebook .py absent"
    mal = _litteraux_suspects(_charger_notebook()[0])
    return not mal, f"littéraux suspects : {mal}" if mal else "aucun littéral suspect"


TITRES_SECTION8 = ("## 8. CSO", "### 8.1", "### 8.2", "### 8.3", "### 8.4", "### 8.5",
                   "## 9. Limites")
LECTURE_B0 = "non reproduit par le modèle"


def _lecture_b0_pilotee(codes):
    """La phrase B0 n'apparaît que dans le corps d'un If/IfExp dont le test cite hors_intervalle
    et dont la branche else est non vide (les commentaires n'existent pas dans l'AST)."""
    import ast

    def cite_hors_intervalle(test):
        return any(isinstance(n, ast.Constant) and n.value == "hors_intervalle"
                   or isinstance(n, ast.Attribute) and n.attr == "hors_intervalle"
                   or isinstance(n, ast.Name) and n.id == "hors_intervalle"
                   for n in ast.walk(test))

    pilotees = hors = 0
    for src in codes:
        arbre = ast.parse(src)
        total = sum(1 for n in ast.walk(arbre) if isinstance(n, ast.Constant)
                    and isinstance(n.value, str) and LECTURE_B0 in n.value)
        dans = 0
        for n in ast.walk(arbre):
            if isinstance(n, (ast.If, ast.IfExp)) and cite_hors_intervalle(n.test) and n.orelse:
                corps = n.body if isinstance(n.body, list) else [n.body]
                dans += sum(1 for x in corps for m in ast.walk(x)
                            if isinstance(m, ast.Constant) and isinstance(m.value, str)
                            and LECTURE_B0 in m.value)
        pilotees += dans
        hors += total - dans
    if hors:
        return False, "phrase B0 hors d'un If piloté par hors_intervalle (avec else)"
    if not pilotees:
        return False, "lecture B0 non pilotée par hors_intervalle"
    return True, ""


def inv_notebook_section8(srcs, params):
    # L20261016-03 (B0) : section 8 présente et ordonnée avant Limites (9) ; la lecture « non
    # reproduit » n'existe que dans une cellule de code pilotée par `hors_intervalle`, jamais en
    # markdown figé ; plus de puce « à venir » CSO/backtest.
    if not NB_PY.exists():
        return False, "notebook .py absent"
    cells = _charger_notebook()[0]
    md = [s for t, s in cells if t == "markdown"]
    pos = []
    for titre in TITRES_SECTION8:
        idx = next((i for i, s in enumerate(md) if s.lstrip().startswith(titre)
                    or f"\n{titre}" in s), None)
        pos.append(idx)
    if None in pos or pos != sorted(pos):
        return False, f"sections 8.x / 9 absentes ou désordonnées : {pos}"
    if any(LECTURE_B0 in s for s in md):
        return False, "lecture B0 figée dans un markdown"
    ok_b0, detail_b0 = _lecture_b0_pilotee([s for t, s in cells if t == "code"])
    if not ok_b0:
        return False, detail_b0
    if any("Régressions CSO" in s for s in md):
        return False, "puce « à venir » CSO/backtest encore présente"
    return True, "section 8 ordonnée, lecture B0 pilotée par hors_intervalle"


TITRE_LIMITES, TITRE_CONCLUSION = "## 9. Limites", "## 10. Conclusion"
# Puces clés des Limites (plan L4) : horizon, méthode proxy, ancrage 2025, pas de recalage.
MOTS_LIMITES = ("5 ans", "proxy", "Ancrage 2025", "Pas de recalage")
RE_NUM_SECTION = re.compile(r"^\s*#+\s*\d+(\.\d+)*\.?", re.MULTILINE)
RE_ANNEE = re.compile(r"\b(?:19|20)\d{2}\b")


def _chiffres_markdown(src):
    """Chiffres restants après retrait des numéros de titre et des années à 4 chiffres."""
    return re.findall(r"\d+", RE_ANNEE.sub("", RE_NUM_SECTION.sub("", src)))


def inv_notebook_conclusion(srcs, params):
    # L20261108-04 (L4) : section 10 après Limites (9), sans chiffre en markdown, générée par du
    # code (display(Markdown)), liste « À venir » retirée, puces clés des Limites présentes.
    if not NB_PY.exists():
        return False, "notebook .py absent"
    cells = _charger_notebook()[0]
    pos = {t: next((i for i, (typ, s) in enumerate(cells)
                    if typ == "markdown" and s.lstrip().startswith(t)), None)
           for t in (TITRE_LIMITES, TITRE_CONCLUSION)}
    i9, i10 = pos[TITRE_LIMITES], pos[TITRE_CONCLUSION]
    if i9 is None or i10 is None or i9 >= i10:
        return False, f"sections 9 / 10 absentes ou désordonnées : {pos}"
    if any(typ == "markdown" and "À venir" in s for typ, s in cells):
        return False, "liste « À venir » encore présente"
    mal = [c for typ, s in cells[i10:] if typ == "markdown" for c in _chiffres_markdown(s)]
    if mal:
        return False, f"chiffres en markdown dans la section 10 : {mal[:3]}"
    codes = [s for typ, s in cells[i10:] if typ == "code"]
    if not any("display(Markdown(" in s for s in codes):
        return False, "section 10 non générée par du code"
    limites = "\n".join(s for typ, s in cells[i9:i10] if typ == "markdown")
    absents = [m for m in MOTS_LIMITES if m not in limites]
    if absents:
        return False, f"puces clés des Limites absentes : {absents}"
    return True, f"section 10 générée ({len(codes)} cellules), Limites : {len(MOTS_LIMITES)} mots-clés"


NB_TIMEOUT_S = 120  # par cellule


def _notebook_a_executer():
    """Notebook .ipynb lu en mémoire (jupytext), jamais réécrit."""
    import jupytext

    return jupytext.read(NB_IPYNB)


def inv_notebook_s_execute(srcs, params):
    # Lot 05 : le notebook s'exécute de bout en bout, en mémoire, kernel python3 du venv,
    # cwd = notebooks/ ; aucune écriture du .ipynb.
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError

    if not NB_IPYNB.exists():
        return False, "notebook .ipynb absent"
    nb = _notebook_a_executer()
    client = NotebookClient(nb, kernel_name="python3", timeout=NB_TIMEOUT_S,
                            resources={"metadata": {"path": str(NB_IPYNB.parent)}})
    try:
        client.execute()
    except CellExecutionError as e:
        # la cellule fautive est celle dont les outputs contiennent l'erreur
        for i, c in enumerate(nb.cells):
            if c.cell_type == "code" and any(o.get("output_type") == "error" for o in c.outputs):
                err = next(o for o in c.outputs if o.get("output_type") == "error")
                debut = c.source.strip().splitlines()[0][:60] if c.source.strip() else ""
                msg = f"{err.get('ename')}: {err.get('evalue', '')[:80]}"
                return False, f"cellule {i} ({debut!r}) {msg}"
        return False, f"CellExecutionError: {str(e).splitlines()[-1]}"
    return True, f"{sum(c.cell_type == 'code' for c in nb.cells)} cellules de code exécutées"


def _egaux(a, b):
    return bool(np.array_equal(a.to_numpy(), b.to_numpy()))


def inv_mc_reproductible(srcs, params):
    # E7 / D6 : même graine => mêmes tirages ; graine différente => tirages différents
    cfg = I.mc_config()
    n, g = cfg["n_tirages"], cfg["graine"]
    a, b, c = I.tirages(n, g), I.tirages(n, g), I.tirages(n, g + 1)
    ok = _egaux(a, b) and not _egaux(a, c)
    return ok, f"n={n} graine={g}"


def inv_mc_bornes(srcs, params):
    # E7 / D1-D2 : tirages dans [low ; high] pour les deux lois, constantes exactes
    cfg = I.mc_config()
    b = I._bornes()
    mal = []
    for loi in S.LOIS_MC:
        t = I.tirages(cfg["n_tirages"], cfg["graine"], loi)
        for p in t:
            lo, hi = b.loc[p, "low"], b.loc[p, "high"]
            if t[p].min() < lo or t[p].max() > hi or (lo == hi and (t[p] != lo).any()):
                mal.append(f"{loi}:{p}")
    ok_txt = f"{len(S.LOIS_MC)} lois, {len(t.columns)} paramètres"
    return not mal, f"hors bornes : {mal}" if mal else ok_txt


def inv_mc_identite_2024(srcs, params):
    # E4 / D5 : E_dem(2024) = E_DC0 pour tous les tirages ; sorties finies, forme (n, 12)
    t0 = time.perf_counter()
    res = I.simulate()
    dt_s = time.perf_counter() - t0
    n = I.mc_config()["n_tirages"]
    ok = (
        np.allclose(res["E_dem"][2024], res["params"]["E_DC0"], rtol=1e-9)
        and all(res[k].shape == (n, len(M.ANNEES)) and np.isfinite(res[k].to_numpy()).all()
                for k in I.SORTIES)
    )
    return bool(ok), f"MC {n} tirages en {dt_s:.2f} s"


def inv_mc_quantiles_croissants(srcs, params):
    # E7 : quantiles croissants à chaque année, pour les 3 sorties
    res = I.simulate()
    mal = [k for k in I.SORTIES if (np.diff(I.quantiles(res, k).to_numpy(), axis=1) < 0).any()]
    return not mal, f"désordre : {mal}" if mal else "3 sorties ordonnées"


def inv_mc_tornado(srcs, params):
    # E7 / D7 : tornado trié par amplitude, d_CI sans effet sur E_dem, central = scénario normal
    t = I.tornado().set_index("param")
    normal = M.project(M.scenario_params("normal")).loc[M.ANNEE1, "E_dem"]
    ok = (
        bool((np.diff(t["amplitude"].to_numpy()) <= 0).all())
        and t.loc["d_CI", "amplitude"] == 0
        and bool(np.allclose(t["y_central"], normal, rtol=1e-9))
    )
    return ok, f"{len(t)} paramètres, tête : {t.index[0]}"


def inv_mc_noyau_egal_project(srcs, params):
    # D5 : chaque ligne du noyau vectorisé == project(jeu), avec N = nb d'années (diffusion)
    # et N = nb de scénarios
    mal = []
    for n in (len(M.ANNEES), len(M.SCENARIOS)):
        par = I.tirages(n=n)
        out = M.project_batch({k: par[k].to_numpy() for k in par})
        for i in range(n):
            ref = M.project({k: float(par[k][i]) for k in par})
            for k in I.SORTIES:
                if not np.allclose(out[k][i], ref[k].to_numpy(), rtol=1e-9):
                    mal.append((n, i, k))
    return not mal, f"écarts : {mal[:3]}" if mal else "N = 12 et N = 3"


def _octets_cso(chemin):
    return chemin.read_bytes()


def inv_cso_sha256(srcs, params):
    # B1 / L20261016-01 : le CSV CSO figé a l'empreinte consignée dans params.yaml (backtest)
    bt = params.get("backtest") or {}
    chemin = ROOT / str(bt.get("cso_fichier", ""))
    if not chemin.is_file():
        return False, f"fichier absent : {chemin}"
    h = hashlib.sha256(_octets_cso(chemin)).hexdigest()
    return h == bt.get("cso_sha256"), f"sha256 {h[:12]}... ({bt.get('cso_edition')})"


def _serie_synth(valeurs):
    idx = [f"{2015 + i // 4}Q{i % 4 + 1}" for i in range(len(valeurs))]
    return pd.Series(np.asarray(valeurs, dtype=float), index=idx)


def _rupture(n=44, k=25, a=0.01, b=0.05):
    i = np.arange(n)
    return _serie_synth(np.exp(np.where(i < k, a * i, a * k + b * (i - k)) + 5))


def inv_cso_conforme(srcs, params):
    # B1/B4 : le CSV lu par backtest == lecture indépendante (module csv) ; valeurs [V] relues à la source
    bt = params["backtest"]
    with open(ROOT / bt["cso_fichier"], encoding="utf-8", newline="") as f:
        ref = {r["TLIST(Q1)"]: int(r["VALUE"]) for r in csv.DictReader(f)
               if r["C03907V04659"] == "10"}  # fmt: skip
    t = B.cso_trimestriel()
    a = B.cso_annuel().set_index("annee")
    ok = (
        len(t) == 44
        and t["dc_gwh"].tolist() == [ref[x] for x in t["trimestre"]]
        and ref["2015Q1"] == 291 and ref["2025Q4"] == 1991
        and a.loc[2024, "dc_gwh"] == 6974 and a.loc[2025, "dc_gwh"] == 7662
    )  # fmt: skip
    return bool(ok), f"{len(t)} trimestres, 2024={a.loc[2024, 'dc_gwh']} 2025={a.loc[2025, 'dc_gwh']} GWh"


def inv_bt_pseudo_previsions(srcs, params):
    # B4 : 108 lignes (20 origines h=4, 16 origines h=8 x 3 méthodes) ; (2024Q4, h=4) -> 2025Q4 = 1991
    pp = B.pseudo_previsions()
    n4 = int(((pp["h"] == 4) & (pp["methode"] == "naive")).sum())
    n8 = int(((pp["h"] == 8) & (pp["methode"] == "naive")).sum())
    ligne = pp[(pp["origine"] == "2024Q4") & (pp["h"] == 4)]
    ok = (len(pp) == 108 and n4 == 20 and n8 == 16 and (ligne["cible"] == "2025Q4").all()
          and (ligne["y_obs"] == 1991).all())  # fmt: skip
    return bool(ok), f"{len(pp)} lignes ({n4} origines h=4, {n8} h=8)"


def inv_bt_anti_fuite(srcs, params):
    # B4 : une valeur postérieure à l'origine ne change aucune prévision (3 méthodes)
    s = _rupture()
    o = "2021Q4"
    pos = s.index.get_loc(o)
    futur = s.copy()
    futur.iloc[pos + 1 :] = 1e9
    mal = [m for m in B.METHODES if B.prevoir(s, o, 4, m, 12) != B.prevoir(futur, o, 4, m, 12)]
    return not mal, f"fuite : {mal}" if mal else "3 méthodes sans fuite"


def inv_bt_rupture_synthetique(srcs, params):
    # B4 : série à rupture ; glissante = polyfit des 12 derniers points (origine incluse),
    # croissante = polyfit depuis 2015Q1, naïve = formule fermée avec h en trimestres
    s = _rupture()
    pos, h = 30, 4
    y = np.log(s.to_numpy())
    fen, tout = list(range(pos - 11, pos + 1)), list(range(pos + 1))
    bg, ag = np.polyfit(fen, y[fen], 1)
    bc, ac = np.polyfit(tout, y[tout], 1)
    o = s.index[pos]
    naive = s.iloc[pos] * (s.iloc[pos] / s.iloc[pos - 4]) ** (h / 4)
    obt = {"glissante": B.prevoir(s, o, h, "glissante", 12), "croissante": B.prevoir(s, o, h, "croissante"),
           "naive": B.prevoir(s, o, h, "naive")}  # fmt: skip
    att = {"glissante": np.exp(ag + bg * (pos + h)), "croissante": np.exp(ac + bc * (pos + h)),
           "naive": naive}  # fmt: skip
    mal = [m for m in att if not np.isclose(obt[m], att[m], rtol=1e-9)]
    return not mal, f"écarts : {mal}" if mal else "3 méthodes == polyfit / forme fermée"


def inv_bt_d_hat_synthetique(srcs, params):
    # B5(a) : taux constant => d̂ = d ; série non log-linéaire => polyfit sur fenetre_ci points
    d = 0.02
    ci = pd.Series({t: 500 * (1 - d) ** (t - 2010) for t in range(2010, 2026)})
    fen = params["backtest"]["fenetre_ci"]
    ok1 = abs(B.d_hat(ci, 2020, fen) - d) < 1e-9
    irr = pd.Series({2016: 100.0, 2017: 90.0, 2018: 95.0, 2019: 60.0, 2020: 70.0, 2021: 10.0})
    an = list(range(2020 - fen + 1, 2021))
    b, _ = np.polyfit(an, np.log([irr[t] for t in an]), 1)
    ok2 = bool(np.isclose(B.d_hat(irr, 2020, fen), 1 - np.exp(b), rtol=1e-9))
    return ok1 and ok2, f"d̂={B.d_hat(ci, 2020, fen):.6f} (d={d})"


def inv_bt_scenarios_inchanges(srcs, params):
    # B0 / non-régression : le modèle ne change pas (E_dem 2025 et 2035 des 3 scénarios, TWh).
    # Valeurs = instantané de run_scenarios avant le lot (backtest ne touche pas au modèle),
    # recoupées par le prototype B0 de la revue de plan (437 / 453 / 469 TWh en 2025).
    # Écart assumé au contrat smoke (valeurs figées), décidé à la main.
    att = {"pessimiste": (468.71900380133235, 2154.830257425733),
           "normal": (452.6762991549624, 978.7909277103267),
           "optimiste": (436.9893810463422, 510.5705593385353)}  # fmt: skip
    d = M.run_scenarios()["E_dem"]
    mal = [s for s, (a, b) in att.items()
           if not (np.isclose(d[(s, 2025)], a, rtol=1e-9) and np.isclose(d[(s, 2035)], b, rtol=1e-9))]
    return not mal, f"scénarios modifiés : {mal}" if mal else "E_dem 2025/2035 inchangés"


def inv_carbone_incorpore(srcs, params):
    # L3 / E13 : carbone incorporé du matériel IT, à part. Ratio effectif r_s3*CI_ref/CI(t) >= r_s3
    # après l'année de référence (strict si d_CI > 0), jamais de colonne total, CO2_Mt (scope 2)
    # inchangé, formule/unités (1 TWh x 1 g/kWh = 1 kt), borne basse D tracée à morrison_2025.
    mal = []
    r = params["params"]["r_s3"]
    if not (r["low"]["statut"] == "D" and r["low"]["source_ids"] == ["morrison_2025"]):
        mal.append("borne basse non tracée (D, morrison_2025)")
    if not np.isclose(M.co2_incorpore_mt(1.0, 1.0, 1.0), 1.0 / M.KT_PAR_MT, rtol=1e-12):
        mal.append("unité 1 TWh x 1 g/kWh != 1 kt")
    for s in M.SCENARIOS:
        t, p = M.carbone_incorpore(s), M.scenario_params(s)
        if any("total" in c.lower() for c in t.columns):
            mal.append(f"colonne total {s}")
        if not np.array_equal(t["CO2_Mt"], M.project(p)["CO2_Mt"]):
            mal.append(f"CO2_Mt scope 2 modifié {s}")
        apres = t.index > p["annee_ref_CI"]
        for b in S.BORNES:
            rb = r[b]["valeur"]
            rat = t[f"ratio_effectif_{b}"]
            if not (rat[apres] > rb).all() or not np.isclose(rat[int(p["annee_ref_CI"])], rb):
                mal.append(f"ratio effectif {s}/{b}")
            if not np.allclose(t[f"CO2_incorpore_Mt_{b}"], rat * t["CO2_Mt"], rtol=1e-9):
                mal.append(f"incorporé != ratio x CO2_Mt {s}/{b}")
    return not mal, f"carbone incorporé : {mal[:3]}" if mal else "ratio effectif >= r_s3, à part"


INVARIANTS = [
    ("E2.registre_valide", inv_registre_valide),
    ("E2.biais_non_vide", inv_biais_non_vide),
    ("E5.bornes_tracables", inv_bornes_tracables),
    ("E5.v_s_lisibles", inv_v_s_lisibles),
    ("E5.rapport_non_vide", inv_rapport_non_vide),
    ("E4.identite_2024", inv_identite_2024),
    ("E4.croissances_neutres", inv_croissances_neutres),
    ("E4.trajectoire_decroissante", inv_trajectoire_decroissante),
    ("E4.unites_co2_eau", inv_unites),
    ("E3.ordre_scenarios", inv_ordre_scenarios),
    ("E4.forme_annuelle", inv_forme_annuelle),
    ("E3.diagnostic_non_applique", inv_non_cale),
    ("E4.mur_non_negatif", inv_mur),
    ("E4.bottom_up", inv_bottom_up),
    ("E4.pue_trois_postes", inv_pue_trois_postes),
    ("L04.notebook_synchronise", inv_notebook_synchronise),
    ("L04.notebook_sans_chiffre_en_dur", inv_notebook_sans_chiffre_en_dur),
    ("L05.notebook_s_execute", inv_notebook_s_execute),
    ("B0.notebook_section8", inv_notebook_section8),
    ("L4.notebook_conclusion", inv_notebook_conclusion),
    ("E7.mc_reproductible", inv_mc_reproductible),
    ("E7.mc_bornes", inv_mc_bornes),
    ("E7.mc_identite_2024", inv_mc_identite_2024),
    ("E7.mc_quantiles_croissants", inv_mc_quantiles_croissants),
    ("E7.mc_tornado", inv_mc_tornado),
    ("E7.mc_noyau_egal_project", inv_mc_noyau_egal_project),
    ("B1.cso_sha256", inv_cso_sha256),
    ("B4.cso_conforme", inv_cso_conforme),
    ("B4.pseudo_previsions", inv_bt_pseudo_previsions),
    ("B4.anti_fuite", inv_bt_anti_fuite),
    ("B4.rupture_synthetique", inv_bt_rupture_synthetique),
    ("B5.d_hat_synthetique", inv_bt_d_hat_synthetique),
    ("B0.scenarios_inchanges", inv_bt_scenarios_inchanges),
    ("E12.miracle_t_d_max", inv_miracle),
    ("E13.carbone_incorpore", inv_carbone_incorpore),
]
LENTS = {"L05.notebook_s_execute"}  # exclus des mutations registre/modèle (coût d'exécution)


def run(srcs, params, verbose=True, lents=True):
    ok_all = True
    for nom, f in INVARIANTS:
        if not lents and nom in LENTS:
            continue
        try:
            ok, detail = f(srcs, params)
        except Exception as e:  # noqa: BLE001 - une exception vaut un invariant en échec
            ok, detail = False, f"exception {type(e).__name__}: {e}"
        ok_all &= ok
        if verbose:
            print(f"{'OK' if ok else 'FAIL'} {nom} {detail}")
    return ok_all


def _mut_source_supprimee(s, p):
    del s[0]  # iea_energy_ai_2025 : citée par E_DC0


def _mut_biais_vide(s, p):
    s[3]["biais"] = []


def _mut_h_sans_justification(s, p):
    p["params"]["s_train"]["central"]["justification"] = ""


def _mut_v_sur_paywall(s, p):
    p["params"]["E_DC0"]["low"]["source_ids"] = ["nature_2026"]


def _mut_borne_sans_source(s, p):
    p["params"]["CI_ref"]["high"]["source_ids"] = []


def _mut_borne_retiree(s, p):
    del p["params"]["EWIF"]["high"]


def _mut_rapport_masque(s, p):
    for src in s:  # tout « qualifié » artificiellement : plus de zone floue à compter
        src["interet"] = "x"
        for b in src["biais"]:
            b["sens"] = "sous-estimation"


def _mut_obs_source_absente(s, p):
    p["observations"]["niveaux"][0]["source_ids"] = ["fantome"]  # B2 : source du registre requise


def _mut_obs_edition_retiree(s, p):
    for o in p["observations"]["taux"]:
        o.pop("edition", None)  # B2 : edition obligatoire pour les séries IEA


def _mut_cso_sha256_corrompu(s, p):
    p["backtest"]["cso_sha256"] = "0" * 64  # B1 : empreinte consignée != fichier


def _mut_backtest_fenetre_invalide(s, p):
    p["backtest"]["fenetre"] = 1  # B7 : fenetre >= 3


MUTATIONS = [
    ("source_supprimee", _mut_source_supprimee),
    ("biais_vide", _mut_biais_vide),
    ("h_sans_justification", _mut_h_sans_justification),
    ("v_sur_paywall", _mut_v_sur_paywall),
    ("borne_sans_source", _mut_borne_sans_source),
    ("borne_retiree", _mut_borne_retiree),
    ("rapport_masque", _mut_rapport_masque),
    ("obs_source_absente", _mut_obs_source_absente),
    ("obs_edition_retiree", _mut_obs_edition_retiree),
    ("cso_sha256_corrompu", _mut_cso_sha256_corrompu),
    ("backtest_fenetre_invalide", _mut_backtest_fenetre_invalide),
]


@contextmanager
def _patch(cible=M, **attrs):
    old = {k: getattr(cible, k) for k in attrs}
    for k, v in attrs.items():
        setattr(cible, k, v)
    try:
        yield
    finally:
        for k, v in old.items():
            setattr(cible, k, v)


def _mod_co2_unite():
    return {"co2_mt": lambda e, ci: e * ci / 1e6}


def _mod_eau_unite():
    return {"eau_hm3": lambda e, pue, w, ew: (e / pue * w + e * ew) * 1000}


def _mod_trajectoire_plate():
    return {"trajectoire": lambda g25, g35: g25 ** np.arange(len(M.ANNEES), dtype=float)}


def _mod_scenarios_inverses():
    orig = M.scenario_params
    swap = {"pessimiste": "optimiste", "optimiste": "pessimiste", "normal": "normal"}
    return {"scenario_params": lambda nom: orig(swap[nom])}


def _mod_calage_applique():
    orig, proj = M.scenario_params, M.project

    def force(nom):
        p = orig(nom)
        lo, hi = 1.0, 10.0
        cible = M.cible_iea(nom)
        for _ in range(60):  # dichotomie : le calage est (à tort) injecté dans le scénario
            mid = (lo + hi) / 2
            if proj({**p, "g_tok_2025": mid}).loc[2035, "E_dem"] < cible:
                lo = mid
            else:
                hi = mid
        return {**p, "g_tok_2025": (lo + hi) / 2}

    return {"scenario_params": force}


def _mod_mur_non_ecrete():
    orig = M.wall_stress

    def sans_clip(nom):
        w = orig(nom)
        for b in S.BORNES:
            w[f"E_wall_{b}"] = w["E_dem"] - w[f"E_cap_{b}"]
        return w

    return {"wall_stress": sans_clip}


def _mod_identite_cassee():
    proj = M.project

    def decale(p):
        df = proj(p)
        df["E_dem"] = df["E_dem"] + 5.0
        return df

    return {"project": decale}


def _mod_pue_poste_retire():
    proj = M.project

    def sans_pue_train(p):
        df = proj(p)
        r = df["PUE"] / p["PUE_2024"]
        df["E_dem"] = df["E_dem"] - df["E_train"] + df["E_train"] / r
        df["E_train"] = df["E_train"] / r
        return df

    return {"project": sans_pue_train}


def _mc_loi_normale():
    # loi non bornée : normale centrée sur le central, écart-type = demi-plage
    def tirages(n=None, graine=None, loi=None):
        cfg = I.mc_config()
        rng = np.random.default_rng(cfg["graine"] if graine is None else graine)
        b = I._bornes()
        cols = {}
        for p in I._tires_tous():
            lo, c, hi = b.loc[p, ["low", "central", "high"]]
            cols[p] = np.full(n or cfg["n_tirages"], lo) if lo == hi else rng.normal(
                c, (hi - lo) / 2, n or cfg["n_tirages"])
        return pd.DataFrame(cols)

    return {"tirages": tirages}


def _mc_graine_ignoree():
    orig = I.tirages
    return {"tirages": lambda n=None, graine=None, loi=None: orig(n, I.mc_config()["graine"], loi)}


def _mc_tornado_non_trie():
    orig = I.tornado
    return {"tornado": lambda *a, **k: orig(*a, **k).iloc[::-1].reset_index(drop=True)}


def _mc_quantiles_inverses():
    orig = I.quantiles
    return {"quantiles": lambda res, sortie: orig(res, sortie).iloc[:, ::-1]}


def _mc_diffusion_cassee():
    orig = M.project_batch

    def casse(p):
        n = len(np.atleast_1d(p["E_DC0"]))
        out = orig({k: np.atleast_1d(v)[:1] for k, v in p.items()})  # 1re ligne diffusée à toutes
        return {k: np.repeat(v, n, axis=0) for k, v in out.items()}

    return {"project_batch": casse}


MUTATIONS_MC = [
    ("mc_loi_normale", I, _mc_loi_normale),
    ("mc_graine_ignoree", I, _mc_graine_ignoree),
    ("mc_tornado_non_trie", I, _mc_tornado_non_trie),
    ("mc_quantiles_inverses", I, _mc_quantiles_inverses),
    ("mc_diffusion_cassee", M, _mc_diffusion_cassee),
]


def _bt_filtre_total():
    # codes échangés : DC lu comme total métré (et inversement) ; détecté par les valeurs
    return {"CODE_DC": B.CODE_TOTAL, "CODE_TOTAL": B.CODE_DC}


def _bt_fuite():
    return {"_jusqua": lambda serie, origine: serie}  # la prévision voit tout le futur


def _bt_signe_d_hat():
    orig = B.d_hat
    return {"d_hat": lambda *a: -orig(*a)}


def _bt_naive_h_annees():
    return {"_naive": lambda y_o, y_prec, h: y_o * (y_o / y_prec) ** h}  # h au lieu de h / 4


def _bt_fenetre_decalee():
    return {"_debut_fenetre": lambda pos, fenetre: pos - fenetre}  # un point de trop


def _bt_origine_decalee():
    orig = B._controler_origines
    return {"_controler_origines": lambda serie, cfg: orig(serie, cfg) + 1}


MUTATIONS_BT = [
    ("bt_filtre_total", _bt_filtre_total),
    ("bt_fuite", _bt_fuite),
    ("bt_signe_d_hat", _bt_signe_d_hat),
    ("bt_naive_h_annees", _bt_naive_h_annees),
    ("bt_fenetre_decalee", _bt_fenetre_decalee),
    ("bt_origine_decalee", _bt_origine_decalee),
]


def _miracle_t_etoile_gonfle():
    orig = M.t_d_max_admissible

    def gonfle(s, cible, critere="2035"):
        r = orig(s, cible, critere)
        return {**r, "T_star": None if r["T_star"] is None else r["T_star"] * 1.05}

    return {"t_d_max_admissible": gonfle}


def _miracle_trajectoire_ignoree():
    orig = M.t_d_max_admissible
    return {"t_d_max_admissible": lambda s, c, critere="2035": orig(s, c, "2035")}


def _miracle_zones_inversees():
    orig = M._zone
    return {"_zone": lambda t: M.ZONES[::-1][M.ZONES.index(orig(t))]}


def _carbone_unite():
    return {"co2_incorpore_mt": lambda e, r, ci: r * e * ci / 1e6}


def _carbone_additionne():
    orig = M.carbone_incorpore

    def somme(s):
        t = orig(s)
        t["CO2_Mt"] = t["CO2_Mt"] + t["CO2_incorpore_Mt_central"]
        return t

    return {"carbone_incorpore": somme}


def _carbone_ratio_plat():
    orig = M.carbone_incorpore

    def plat(s):
        t = orig(s)
        for b in S.BORNES:
            t[f"ratio_effectif_{b}"] = t[f"ratio_effectif_{b}"].iloc[0]
        return t

    return {"carbone_incorpore": plat}


MUTATIONS_MODELE = [
    ("co2_unite", _mod_co2_unite),
    ("eau_unite", _mod_eau_unite),
    ("trajectoire_plate", _mod_trajectoire_plate),
    ("scenarios_inverses", _mod_scenarios_inverses),
    ("calage_applique", _mod_calage_applique),
    ("mur_non_ecrete", _mod_mur_non_ecrete),
    ("identite_cassee", _mod_identite_cassee),
    ("pue_poste_retire", _mod_pue_poste_retire),
    ("miracle_t_etoile_gonfle", _miracle_t_etoile_gonfle),
    ("miracle_trajectoire_ignoree", _miracle_trajectoire_ignoree),
    ("miracle_zones_inversees", _miracle_zones_inversees),
    ("carbone_incorpore_unite", _carbone_unite),
    ("carbone_incorpore_additionne", _carbone_additionne),
    ("carbone_incorpore_ratio_plat", _carbone_ratio_plat),
]


def _mut_nb_chiffre_en_dur(orig):
    def charge():
        py, nb = orig()
        return py + [("code", "x = 1234.5")], nb + [("code", "x = 1234.5")]

    return charge


def _mut_nb_desynchronise(orig):
    def charge():
        py, nb = orig()
        return py, nb[:-1]

    return charge


def _mut_nb_valeur_modele(orig):
    def charge():
        py, nb = orig()
        ajout = [("code", "e = 415\ns = 0.35")]
        return py + ajout, nb + ajout

    return charge


def _mut_nb_section8_absente(orig):
    def charge():
        py, nb = orig()
        # retirée des DEUX côtés : seul B0.notebook_section8 peut la tuer (synchro intacte)
        return [c for c in py if "### 8.4" not in c[1]], [c for c in nb if "### 8.4" not in c[1]]

    return charge


def _mut_nb_b0_commentaire(orig):
    def charge():
        py, nb = orig()
        ajout = [("code", f"# hors_intervalle else\nlecture = '{LECTURE_B0}'")]
        return py + ajout, nb + ajout

    return charge


def _mut_nb_b0_fige(orig):
    def charge():
        py, nb = orig()
        ajout = [("markdown", f"Taux observé : {LECTURE_B0}.")]
        return py + ajout, nb + ajout

    return charge


def _mut_nb_conclusion_chiffre(orig):
    def charge():
        py, nb = orig()
        ajout = [("markdown", "Le modèle projette 700 TWh en conclusion.")]
        return py + ajout, nb + ajout

    return charge


def _mut_nb_limites_sans_proxy(orig):
    def charge():
        def sans(cells):
            return [(t, s.replace("proxy", "") if s.lstrip().startswith(TITRE_LIMITES) else s)
                    for t, s in cells]

        py, nb = orig()
        return sans(py), sans(nb)

    return charge


MUTATIONS_NOTEBOOK = [
    ("nb_section8_absente", _mut_nb_section8_absente),
    ("nb_b0_fige", _mut_nb_b0_fige),
    ("nb_b0_commentaire", _mut_nb_b0_commentaire),
    ("nb_conclusion_chiffre", _mut_nb_conclusion_chiffre),
    ("nb_limites_sans_proxy", _mut_nb_limites_sans_proxy),
    ("nb_valeur_modele", _mut_nb_valeur_modele),
    ("nb_chiffre_en_dur", _mut_nb_chiffre_en_dur),
    ("nb_desynchronise", _mut_nb_desynchronise),
]


def _mut_nb_cellule_qui_leve(orig):
    def charge():
        nb = orig()
        nb.cells.append(nbformat.v4.new_code_cell("raise RuntimeError('mutation')"))
        return nb

    return charge


def _mut_nb_cellule_cassee(orig):
    def charge():
        nb = orig()
        c = next(c for c in nb.cells if c.cell_type == "code" and c.source.strip())
        c.source = "import module_inexistant_mutation\n" + c.source
        return nb

    return charge


MUTATIONS_NB_EXEC = [
    ("nb_cellule_qui_leve", _mut_nb_cellule_qui_leve),
    ("nb_cellule_cassee", _mut_nb_cellule_cassee),
]


def mutation_check():
    srcs, params = S.raw_sources(), S.raw_params()
    tout = True
    for nom, mut in MUTATIONS:
        s, p = copy.deepcopy(srcs), copy.deepcopy(params)
        mut(s, p)
        tue = not run(s, p, verbose=False, lents=False)
        tout &= tue
        print(f"{'OK' if tue else 'FAIL'} mutation.{nom} {'detectee' if tue else 'NON detectee'}")
    for nom, make in MUTATIONS_MODELE:
        with _patch(**make()):
            tue = not run(srcs, params, verbose=False, lents=False)
        tout &= tue
        print(f"{'OK' if tue else 'FAIL'} mutation.{nom} {'detectee' if tue else 'NON detectee'}")
    for nom, cible, make in MUTATIONS_MC:
        with _patch(cible, **make()):
            tue = not run(srcs, params, verbose=False, lents=False)
        tout &= tue
        print(f"{'OK' if tue else 'FAIL'} mutation.{nom} {'detectee' if tue else 'NON detectee'}")
    for nom, make in MUTATIONS_BT:
        with _patch(B, **make()):
            tue = not run(srcs, params, verbose=False, lents=False)
        tout &= tue
        print(f"{'OK' if tue else 'FAIL'} mutation.{nom} {'detectee' if tue else 'NON detectee'}")
    # B1 : fichier CSO altéré en mémoire (octet ajouté) => empreinte différente
    orig_octets = _octets_cso
    globals()["_octets_cso"] = lambda chemin: orig_octets(chemin) + b"\n"
    try:
        tue = not run(srcs, params, verbose=False, lents=False)
    finally:
        globals()["_octets_cso"] = orig_octets
    tout &= tue
    print(f"{'OK' if tue else 'FAIL'} mutation.cso_octets_alteres {'detectee' if tue else 'NON detectee'}")
    # B1 : un rapport qui ignorerait les intérêts NT (détecteur neutralisé) doit être détecté
    orig_nt = S.a_inconnue
    S.a_inconnue = lambda _t: False
    try:
        tue = not run(srcs, params, verbose=False, lents=False)
    finally:
        S.a_inconnue = orig_nt
    tout &= tue
    print(f"{'OK' if tue else 'FAIL'} mutation.rapport_ignore_nt {'detectee' if tue else 'NON detectee'}")
    for cible, muts in (("_charger_notebook", MUTATIONS_NOTEBOOK),
                        ("_notebook_a_executer", MUTATIONS_NB_EXEC)):
        orig = globals()[cible]
        for nom, make in muts:
            globals()[cible] = make(orig)
            try:
                tue = not run(srcs, params, verbose=False, lents=cible == "_notebook_a_executer")
            finally:
                globals()[cible] = orig
            tout &= tue
            print(f"{'OK' if tue else 'FAIL'} mutation.{nom} {'detectee' if tue else 'NON detectee'}")
    return tout


def show():
    d = M.run_scenarios()
    print("Tableau 2035 (comparaison aux bornes IEA, non calé)")
    print(f"{'scenario':<11}{'E_dem TWh':>10}{'cible':>7}{'écart %':>9}{'CO2_Mt':>9}{'W_hm3':>9}"
          f"{'g_tok_2025 impl.':>18}  drapeau")
    for s in M.SCENARIOS:
        r = d.loc[(s, 2035)]
        cible = M.cible_iea(s)
        try:
            x, ok = M.implied_param(s, cible)
            impl, flag = f"{x:.3f}", "dans la plage" if ok else "HORS PLAGE"
        except M.CibleInatteignable as e:
            impl, flag = "n/a", f"inatteignable [{e.e_bas:.0f};{e.e_haut:.0f}]"
        print(f"{s:<11}{r['E_dem']:>10.0f}{cible:>7.0f}{(r['E_dem'] / cible - 1) * 100:>+9.1f}"
              f"{r['CO2_Mt']:>9.0f}{r['W_hm3']:>9.0f}{impl:>18}  {flag}")
    b = M.bottom_up_check()
    print("Contrôle bottom-up 2024 (affiché, non utilisé)")
    print(f"E_bu = {b['E_bu']:.2f} TWh [{b['E_bu_min']:.2f} ; {b['E_bu_max']:.2f}] "
          f"vs E_DC0*s_AI = {b['E_ref']:.2f} TWh ; ratio = {b['ratio']:.3f} "
          f"[{b['ratio_min']:.4f} ; {b['ratio_max']:.2f}]")


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    if "--mutation-check" in argv:
        return 0 if mutation_check() else 1
    if "--show" in argv:
        show()
        return 0
    return 0 if run(S.raw_sources(), S.raw_params()) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
