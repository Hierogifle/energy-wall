import ast
import copy
import csv
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from energywall import backtest as B
from energywall import incertitude as inc
from energywall import model as M
from energywall import sources as S

CSV = S.ROOT / "data" / "raw" / "cso_MEC02.csv"
N_MC = 2000


def _labels(n=44, annee0=2015):
    return [f"{annee0 + i // 4}Q{i % 4 + 1}" for i in range(n)]


def _serie(valeurs, annee0=2015):
    return pd.Series(np.asarray(valeurs, dtype=float), index=_labels(len(valeurs), annee0))


def _croissance(r, n=44, y0=100.0):
    return _serie(y0 * (1 + r) ** np.arange(n))


@pytest.fixture(scope="module")
def pp():
    return B.pseudo_previsions()


@pytest.fixture(scope="module")
def res():
    return inc.simulate(n=N_MC)


@pytest.fixture
def params_modifies(monkeypatch):
    """Remplace S.raw_params par une copie modifiable (fonction `modifier(p)`)."""
    base = S.raw_params()

    def appliquer(modifier):
        p = copy.deepcopy(base)
        modifier(p)
        monkeypatch.setattr(S, "raw_params", lambda: p)

    return appliquer


def _csv_dc():
    with open(CSV, encoding="utf-8", newline="") as f:
        return {r["TLIST(Q1)"]: int(r["VALUE"]) for r in csv.DictReader(f)
                if r["C03907V04659"] == "10"}  # fmt: skip


# --- (b) CSO ---------------------------------------------------------------------------------


def test_cso_trimestriel_forme_et_valeurs():
    t = B.cso_trimestriel()
    assert len(t) == 44
    assert list(t.columns) == ["trimestre", "annee", "q", "dc_gwh", "total_gwh", "part"]
    assert t.set_index("trimestre").loc["2015Q1", "dc_gwh"] == 291
    assert t.set_index("trimestre").loc["2025Q4", "dc_gwh"] == 1991
    assert t["dc_gwh"].tolist() == [_csv_dc()[x] for x in t["trimestre"]]
    np.testing.assert_allclose(t["part"], t["dc_gwh"] / t["total_gwh"])
    assert t["total_gwh"].gt(t["dc_gwh"]).all()


def test_cso_annuel():
    a = B.cso_annuel().set_index("annee")
    assert len(a) == 11
    assert a.loc[2024, "dc_gwh"] == 6974 and a.loc[2025, "dc_gwh"] == 7662
    assert a.loc[2025, "croissance"] == pytest.approx(7662 / 6974 - 1)
    dc = _csv_dc()
    assert a.loc[2020, "dc_gwh"] == sum(dc[f"2020Q{q}"] for q in (1, 2, 3, 4))
    assert np.isnan(a.loc[2015, "croissance"])


def test_cso_fichier_absent(tmp_path):
    with pytest.raises(FileNotFoundError, match="absent"):
        B.cso_trimestriel(chemin=tmp_path / "nexiste_pas.csv")


def test_cso_sha256_different(tmp_path):
    f = tmp_path / "copie.csv"
    f.write_bytes(CSV.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="sha256"):
        B.cso_trimestriel(chemin=f)
    # même contenu mais empreinte attendue fausse
    with pytest.raises(ValueError, match="sha256"):
        B.cso_trimestriel(sha256="0" * 64)


def test_cso_sha256_ok_sur_copie(tmp_path):
    f = tmp_path / "copie.csv"
    f.write_bytes(CSV.read_bytes())
    assert hashlib.sha256(f.read_bytes()).hexdigest() == S.raw_params()["backtest"]["cso_sha256"]
    assert len(B.cso_trimestriel(chemin=f)) == 44


def test_cso_colonne_ou_code_manquant(tmp_path):
    brut = CSV.read_text(encoding="utf-8")
    f = tmp_path / "x.csv"
    f.write_text(brut.replace('"VALUE"', '"VAL"'), encoding="utf-8")
    sha = hashlib.sha256(f.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="colonne"):
        B.cso_trimestriel(chemin=f, sha256=sha)
    lignes = [x for x in brut.splitlines() if '"-"' not in x]
    f.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    sha = hashlib.sha256(f.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="code"):
        B.cso_trimestriel(chemin=f, sha256=sha)


def test_config_absente(params_modifies):
    params_modifies(lambda p: p.pop("backtest"))
    with pytest.raises(KeyError, match="backtest"):
        B.bt_config()
    params_modifies(lambda p: p.pop("observations"))
    with pytest.raises(KeyError, match="observations"):
        B.observations()


def test_config_inapplicable_au_csv(params_modifies):
    params_modifies(lambda p: p["backtest"].update(annee_test=2026))
    with pytest.raises(ValueError, match="annee_test"):
        B.pseudo_previsions()
    params_modifies(lambda p: p["backtest"].update(origine_debut="2015Q2"))
    with pytest.raises(ValueError, match="précède"):
        B.pseudo_previsions()
    params_modifies(lambda p: p["backtest"].update(horizons=[4, 80]))
    with pytest.raises(ValueError, match="horizon 80"):
        B.pseudo_previsions()


# --- (c) pseudo-prévisions -------------------------------------------------------------------


def _serie_a_rupture(k=25, a=0.01, b=0.05, n=44):
    """log y : pente a avant le trimestre k, pente b ensuite (continu en k)."""
    i = np.arange(n)
    return _serie(np.exp(np.where(i < k, a * i, a * k + b * (i - k)) + 5))


def test_prevoir_sur_rupture_valeurs_independantes():
    s = _serie_a_rupture()
    o, h, pos = "2022Q3", 4, 30  # 2022Q3 = position 30
    assert s.index[pos] == o
    y = np.log(s.to_numpy())
    fen = list(range(19, 31))  # 12 derniers points, origine incluse
    b, a = np.polyfit(fen, y[fen], 1)
    assert B.prevoir(s, o, h, "glissante", 12) == pytest.approx(np.exp(a + b * (pos + h)))
    tout = list(range(31))  # depuis 2015Q1
    b, a = np.polyfit(tout, y[tout], 1)
    assert B.prevoir(s, o, h, "croissante") == pytest.approx(np.exp(a + b * (pos + h)))
    # les deux régressions diffèrent bien (la rupture est visible)
    assert B.prevoir(s, o, h, "glissante", 12) != pytest.approx(B.prevoir(s, o, h, "croissante"))


def test_prevoir_fenetre_defaut_depuis_config():
    s = _serie_a_rupture()
    assert B.prevoir(s, "2022Q3", 4, "glissante") == B.prevoir(
        s, "2022Q3", 4, "glissante", S.raw_params()["backtest"]["fenetre"]
    )


def test_prevoir_methode_inconnue_et_historique_court():
    s = _croissance(0.02)
    with pytest.raises(ValueError, match="méthode"):
        B.prevoir(s, "2022Q3", 4, "magique")
    with pytest.raises(ValueError, match="fenêtre"):
        B.prevoir(s, "2015Q4", 4, "glissante", 12)
    with pytest.raises(ValueError, match="naïve"):
        B.prevoir(s, "2015Q4", 4, "naive")


def test_108_lignes_20_et_16_origines(pp):
    assert len(pp) == 108
    assert list(pp.columns) == ["methode", "h", "origine", "cible", "y_prevu", "y_obs", "erreur"]
    assert (pp.groupby(["methode", "h"]).size().loc[(slice(None), 4)] == 20).all()
    assert (pp.groupby(["methode", "h"]).size().loc[(slice(None), 8)] == 16).all()
    assert set(pp["methode"]) == {"glissante", "croissante", "naive"}
    np.testing.assert_allclose(pp["erreur"], pp["y_prevu"] / pp["y_obs"] - 1)


def test_indexation_origine_cible(pp):
    lignes = pp[(pp["origine"] == "2024Q4") & (pp["h"] == 4)]
    assert len(lignes) == 3
    assert (lignes["cible"] == "2025Q4").all()
    assert (lignes["y_obs"] == 1991).all()
    # première et dernière origine h = 8
    h8 = pp[(pp["h"] == 8) & (pp["methode"] == "naive")]
    assert h8["origine"].iloc[0] == "2020Q1" and h8["cible"].iloc[0] == "2022Q1"
    assert h8["origine"].iloc[-1] == "2023Q4" and h8["cible"].iloc[-1] == "2025Q4"
    dc = _csv_dc()
    assert (pp["y_obs"] == pp["cible"].map(dc)).all()


@pytest.mark.parametrize("h", [4, 8])
def test_naive_forme_fermee_h_en_trimestres(h):
    r = 0.03
    s = _croissance(r)
    o = "2021Q2"
    y_o = s.loc[o]
    assert B.prevoir(s, o, h, "naive") == pytest.approx(y_o * (1 + r) ** h)
    assert B.prevoir(s, o, h, "naive") != pytest.approx(y_o * (1 + r) ** (4 * h))


def test_naive_formule_sur_serie_quelconque():
    s = _serie_a_rupture()
    y_o, y_4 = s.loc["2022Q3"], s.loc["2021Q3"]
    assert B.prevoir(s, "2022Q3", 8, "naive") == pytest.approx(y_o * (y_o / y_4) ** 2)


@pytest.mark.parametrize("methode", ["glissante", "croissante", "naive"])
def test_anti_fuite(methode):
    s = _serie_a_rupture()
    o = "2021Q4"
    avant = B.prevoir(s, o, 4, methode, 12)
    pos = s.index.get_loc(o)
    futur = s.copy()
    futur.iloc[pos + 1 :] = [1e9 * (i + 1) for i in range(len(s) - pos - 1)]
    assert futur.iloc[pos] == s.iloc[pos] and futur.iloc[pos + 1] != s.iloc[pos + 1]
    assert B.prevoir(futur, o, 4, methode, 12) == avant


def test_anti_fuite_pseudo_previsions():
    s = _serie_a_rupture()
    ref = B.pseudo_previsions(s)
    modif = s.copy()
    modif.iloc[-1] = 1e9  # dernier point : ne peut être qu'une cible (h >= 1)
    mod = B.pseudo_previsions(modif)
    cible_derniere = ref["cible"] == s.index[-1]
    assert cible_derniere.any()
    assert (mod.loc[~cible_derniere, "y_prevu"] == ref.loc[~cible_derniere, "y_prevu"]).all()


def test_derive_taux_croissance_connue():
    r = 0.02
    d = B.derive_taux(_croissance(r))
    attendu = (1 + r) ** 4 - 1
    np.testing.assert_allclose(d["glissante"], attendu, rtol=1e-9)
    np.testing.assert_allclose(d["croissante"], attendu, rtol=1e-9)
    np.testing.assert_allclose(d["realise"], attendu, rtol=1e-9)


def test_derive_taux_realise_serie_reelle():
    d = B.derive_taux().set_index("origine")
    dc = _csv_dc()
    assert d.loc["2025Q4", "realise"] == pytest.approx(dc["2025Q4"] / dc["2024Q4"] - 1)
    assert d.index[0] == "2020Q1" and d.index[-1] == "2025Q4" and len(d) == 24


def test_derive_taux_glissante_vs_polyfit_rupture():
    s = _serie_a_rupture()
    d = B.derive_taux(s).set_index("origine")
    pos = 30
    y = np.log(s.to_numpy())
    fen = list(range(pos - 11, pos + 1))
    b, _ = np.polyfit(fen, y[fen], 1)
    assert d.loc[s.index[pos], "glissante"] == pytest.approx(np.exp(4 * b) - 1)


def test_scores_valeurs_independantes():
    pp_ = pd.DataFrame(
        {"methode": ["a", "a", "a", "b"], "h": [4, 4, 8, 4], "erreur": [0.1, -0.3, 0.2, -0.05]}
    )
    sc = B.scores(pp_).set_index(["methode", "h"])
    assert sc.loc[("a", 4), "n"] == 2
    assert sc.loc[("a", 4), "mape"] == pytest.approx(0.2)
    assert sc.loc[("a", 4), "biais"] == pytest.approx(-0.1)
    assert sc.loc[("b", 4), "biais"] == pytest.approx(-0.05)


def test_scores_reels_coherents(pp):
    sc = B.scores(pp)
    assert len(sc) == 6 and sc["n"].sum() == 108
    sous = pp[(pp["methode"] == "naive") & (pp["h"] == 4)]["erreur"]
    ligne = sc[(sc["methode"] == "naive") & (sc["h"] == 4)].iloc[0]
    assert ligne["mape"] == pytest.approx(sous.abs().mean())
    assert ligne["biais"] == pytest.approx(sous.mean())
    assert (sc["mape"] >= sc["biais"].abs() - 1e-12).all()


def test_residus_trimestre():
    plat = B.residus_trimestre(_croissance(0.02))
    assert list(plat.index) == [1, 2, 3, 4]
    np.testing.assert_allclose(plat, 0.0, atol=1e-9)
    i = np.arange(44)
    saison = _serie(np.exp(0.02 * i + np.where(i % 4 == 0, 0.1, 0.0)))
    r = B.residus_trimestre(saison)
    assert r.loc[1] > 0.05 and (r.loc[[2, 3, 4]] < 0).all()
    assert r.mean() == pytest.approx(0.0, abs=1e-9)  # OLS avec constante : résidus de moyenne nulle


# --- (d) d_CI --------------------------------------------------------------------------------


def _ember():
    return {o["annee"]: o["valeur"] for o in S.raw_params()["observations"]["niveaux"]
            if o["serie"] == "ember_ci_monde"}  # fmt: skip


def test_d_hat_taux_constant():
    d = 0.02
    ci = pd.Series({t: 500 * (1 - d) ** (t - 2010) for t in range(2010, 2026)})
    assert B.d_hat(ci, 2020, 5) == pytest.approx(d, abs=1e-9)
    assert B.d_hat(ci, 2025, 5) == pytest.approx(d, abs=1e-9)


def test_d_hat_serie_non_log_lineaire_et_fenetre_exacte():
    ci = pd.Series({2016: 100.0, 2017: 90.0, 2018: 95.0, 2019: 60.0, 2020: 70.0, 2021: 10.0})
    annees = [2016, 2017, 2018, 2019, 2020]  # exactement fenetre_ci = 5 points
    b, _ = np.polyfit(annees, np.log([ci[t] for t in annees]), 1)
    assert B.d_hat(ci, 2020, 5) == pytest.approx(1 - np.exp(b))
    # 2021 (futur) n'entre pas dans d̂(2020)
    ci2 = ci.copy()
    ci2[2021] = 1e6
    assert B.d_hat(ci2, 2020, 5) == B.d_hat(ci, 2020, 5)
    # fenêtre décalée d'un point : valeur différente
    annees6 = [2015, *annees]
    ci3 = ci.copy()
    ci3[2015] = 300.0
    assert B.d_hat(ci3, 2020, 5) == B.d_hat(ci, 2020, 5)
    b6, _ = np.polyfit(annees6, np.log([ci3[t] for t in annees6]), 1)
    assert 1 - np.exp(b6) != pytest.approx(B.d_hat(ci3, 2020, 5))


def test_d_hat_annee_manquante():
    with pytest.raises(KeyError):
        B.d_hat(pd.Series({2020: 1.0, 2021: 1.0}), 2021, 5)


def test_backtest_ci_glissant_valeurs_independantes():
    bt = B.backtest_ci()
    g = bt["glissant"].set_index("origine")
    assert list(g.index) == [2020, 2021, 2022, 2023, 2024]
    ci = _ember()
    p = S.raw_params()["params"]["d_CI"]
    low, high = p["low"]["valeur"], p["high"]["valeur"]
    for o in g.index:
        annees = list(range(o - 4, o + 1))
        b, a = np.polyfit(annees, np.log([ci[t] for t in annees]), 1)
        assert g.loc[o, "d_hat"] == pytest.approx(1 - np.exp(b))
        assert g.loc[o, "dans_plage"] == (low <= 1 - np.exp(b) <= high)
        e = bt["erreurs"]
        e = e[e["origine"] == o]
        assert list(e["annee"]) == list(range(o + 1, 2026))
        np.testing.assert_allclose(
            e["erreur"], [np.exp(a + b * t) / ci[t] - 1 for t in e["annee"]]
        )
    assert len(bt["erreurs"]) == 5 + 4 + 3 + 2 + 1


def test_backtest_ci_dans_plage_coherent_hors_plage(params_modifies):
    params_modifies(lambda p: p["params"]["d_CI"]["low"].update(valeur=0.012))
    g = B.backtest_ci()["glissant"]
    assert g["dans_plage"].tolist() == [d >= 0.012 for d in g["d_hat"]]
    assert not g["dans_plage"].all()


def test_forme_modele_2025_et_coherence_modele():
    f = B.backtest_ci()["forme_modele"]
    p = S.raw_params()["params"]
    f25 = f[(f["annee"] == 2025) & (f["borne"] == "central")].iloc[0]
    assert f25["erreur"] == pytest.approx(
        p["CI_ref"]["central"]["valeur"] / _ember()[2025] - 1
    )
    assert f25["erreur"] == pytest.approx(458 / 458.29 - 1)
    assert len(f) == 3 * 11 and set(f["borne"]) == {"low", "central", "high"}


def test_ci_modele_egal_sortie_du_modele_toutes_annees_et_bornes():
    for borne in ("low", "central", "high"):
        d = S.raw_params()["params"]["d_CI"][borne]["valeur"]
        ci = M.project({**M.scenario_params("normal"), "d_CI": d})["CI"]
        for t in M.ANNEES:
            assert B.ci_modele(t, d) == pytest.approx(ci[t], rel=1e-12)
    f = B.backtest_ci()["forme_modele"]
    for _, r in f.iterrows():
        assert r["ci_mod"] == B.ci_modele(r["annee"], r["d"])


# --- (e) modèle global -----------------------------------------------------------------------


def test_taux_moyen_construit():
    e = pd.Series({2024: 100.0, 2025: 110.0, 2026: 121.0, 2027: 133.1})
    assert B.taux_moyen(e, 3) == pytest.approx(0.1)
    assert B.taux_moyen(e, 1) == pytest.approx(0.1)
    e2 = pd.Series({2024: 100.0, 2025: 120.0, 2026: 100.0, 2027: 200.0})
    assert B.taux_moyen(e2, 3) == pytest.approx((200 / 100) ** (1 / 3) - 1)
    df = pd.DataFrame({2024: [100.0, 50.0], 2025: [110.0, 100.0]})
    np.testing.assert_allclose(B.taux_moyen(df, 1), [0.1, 1.0])


def test_cas_neutre_taux_nul():
    p = M.scenario_params("normal")
    p.update(g_conv=0.0, g_Ctrain_2025=1.0, g_Ctrain_2035=1.0, g_tok_2025=1.0, g_tok_2035=1.0,
             g_fpt_net=1.0, T_d_parc=1e12, PUE_2035=p["PUE_2024"])
    e = M.project(p)["E_dem"]
    assert B.taux_moyen(e, 1) == pytest.approx(0.0, abs=1e-12)
    assert B.taux_moyen(e, 3) == pytest.approx(0.0, abs=1e-12)


def test_taux_modele_valeurs_independantes(res):
    t = B.taux_modele(res).set_index("ligne")
    cfg = S.raw_params()["backtest"]
    k = cfg["annees_premieres"]
    for s in M.SCENARIOS:
        e = M.project(M.scenario_params(s))["E_dem"]
        assert t.loc[s, "taux_test"] == pytest.approx(e[2025] / e[2024] - 1)
        assert t.loc[s, "taux_premieres"] == pytest.approx((e[2024 + k] / e[2024]) ** (1 / k) - 1)
    e = res["E_dem"]
    qs = S.raw_params()["monte_carlo"]["quantiles"]
    attendu = np.quantile(e[2025] / e[2024] - 1, qs)
    np.testing.assert_allclose(t.loc[[f"q{q:g}" for q in qs], "taux_test"], attendu)
    assert t.loc[[f"q{q:g}" for q in qs], "taux_test"].is_monotonic_increasing
    assert t.loc[["optimiste", "normal", "pessimiste"], "taux_test"].is_monotonic_increasing


def test_point_2025_parts_et_quantiles(res):
    p = B.point_2025(res)
    assert p["annee"] == 2025
    for cle in ("part_taux_ge", "part_niveau_le", "part_niveau_ge"):
        assert 0.0 <= p[cle] <= 1.0
    assert p["part_niveau_le"] + p["part_niveau_ge"] >= 1.0  # l'égalité est comptée des deux côtés
    taux = (res["E_dem"][2025] / res["E_dem"][2024] - 1).to_numpy()
    assert p["part_taux_ge"] == pytest.approx(np.mean(taux >= 0.17))
    assert p["part_niveau_le"] == pytest.approx(np.mean(res["E_dem"][2025].to_numpy() <= 485))
    assert p["part_niveau_ge"] == pytest.approx(np.mean(res["E_dem"][2025].to_numpy() >= 485))
    assert p["taux_quantiles"].is_monotonic_increasing
    assert p["niveaux_quantiles"].is_monotonic_increasing
    bas, haut = p["intervalle_taux"]
    assert bas == pytest.approx(np.quantile(taux, 0.05)) and bas < haut
    d = M.run_scenarios()["E_dem"]
    for s in M.SCENARIOS:
        assert p["taux_scenarios"][s] == pytest.approx(d[(s, 2025)] / d[(s, 2024)] - 1)
        assert p["niveaux_scenarios"][s] == pytest.approx(d[(s, 2025)])
        assert p["ecart_niveau_scenarios"][s] == pytest.approx(d[(s, 2025)] / 485 - 1)


def test_point_2025_regle_b0_hors_intervalle(res):
    p = B.point_2025(res)
    bas, haut = p["intervalle_taux"]
    assert p["hors_intervalle"] == (not (bas <= p["taux_observe"] <= haut))
    if p["taux_observe"] > haut:
        assert p["ecart_taux"] == pytest.approx(p["taux_observe"] - haut)


def test_point_2025_branche_basse_b0(params_modifies, res):
    def modifier(p):
        for t in p["observations"]["taux"]:
            if (t["debut"], t["fin"]) == (2024, 2025):
                t["valeur"] = 0.01

    params_modifies(modifier)
    p = B.point_2025(res)
    bas, _ = p["intervalle_taux"]
    assert p["taux_observe"] < bas
    assert p["hors_intervalle"] is True
    assert p["ecart_taux"] == pytest.approx(0.01 - bas) and p["ecart_taux"] < 0
    assert p["part_taux_ge"] == 1.0


def test_point_2025_lit_les_observations(params_modifies, res):
    def modifier(p):
        for t in p["observations"]["taux"]:
            if (t["debut"], t["fin"]) == (2024, 2025):
                t["valeur"] = 0.095
        for o in p["observations"]["niveaux"]:
            if o["serie"] == "iea_monde" and o["annee"] == 2025:
                o["valeur"] = 450

    params_modifies(modifier)
    p = B.point_2025(res)
    assert p["taux_observe"] == 0.095 and p["niveau_observe"] == 450.0
    assert not p["hors_intervalle"] and p["ecart_taux"] == 0.0
    assert p["part_niveau_le"] == pytest.approx(np.mean(res["E_dem"][2025].to_numpy() <= 450))


def test_point_2025_observation_absente(params_modifies, res):
    params_modifies(lambda p: p["observations"].update(taux=[]))
    with pytest.raises(KeyError, match="taux observé"):
        B.point_2025(res)


def test_taux_observes():
    t = B.taux_observes()
    # 6 + 2 : taux monde 2018-2023 (IEA-4E, p. 43) et son homologue CSO
    assert len(t) == 8
    assert {"serie", "zone", "debut", "fin", "taux", "edition", "statut_effectif",
            "source_ids"} <= set(t.columns)  # fmt: skip
    assert t["edition"].str.len().gt(0).all() and t["zone"].str.len().gt(0).all()
    iea = t[t["serie"] == "iea_monde"].set_index("fin")
    assert iea.loc[2024, "taux"] == 0.12 and iea.loc[2025, "taux"] == 0.17
    ie = t[(t["serie"] == "iea_monde") & (t["fin"] == 2023)].iloc[0]
    assert ie["debut"] == 2018 and ie["taux"] == 0.105 and ie["statut_effectif"] == "D"
    assert 0.08 <= ie["taux"] <= 0.13  # ordre de grandeur attendu du taux monde 2018-2023
    lb = t[t["serie"] == "lbnl_us"].iloc[0]
    assert (lb["debut"], lb["fin"]) == (2014, 2023)
    assert lb["taux"] == pytest.approx((176 / 58) ** (1 / 9) - 1)
    assert lb["statut"] == "D" and lb["statut_effectif"] == "S"
    cso = t[t["serie"] == "cso_dc"].set_index(["debut", "fin"])
    dc = _csv_dc()
    an = {a: sum(dc[f"{a}Q{q}"] for q in (1, 2, 3, 4)) for a in range(2018, 2026)}
    assert cso.loc[(2024, 2025), "taux"] == pytest.approx(an[2025] / an[2024] - 1)
    assert cso.loc[(2023, 2024), "taux"] == pytest.approx(an[2024] / an[2023] - 1)
    assert cso.loc[(2019, 2024), "taux"] == pytest.approx((an[2024] / an[2019]) ** (1 / 5) - 1)
    assert cso.loc[(2018, 2023), "taux"] == pytest.approx((an[2023] / an[2018]) ** (1 / 5) - 1)
    assert (cso["statut"] == "D").all() and (cso["zone"] == "Irlande").all()


def test_observations_accesseur():
    df = B.observations("ember_ci_monde")
    assert len(df) == 11 and df["annee"].tolist() == list(range(2015, 2026))
    assert len(B.observations()) == 17
    with pytest.raises(KeyError):
        B.observations("inconnue")


# --- (g) aucun chiffre en dur ----------------------------------------------------------------


def test_aucun_chiffre_en_dur_hors_trimestres_par_an():
    src = Path(B.__file__).read_text(encoding="utf-8")
    arbre = ast.parse(src)
    assert B.TRIMESTRES_PAR_AN == 4
    exclus = {
        id(n.value)
        for n in ast.walk(arbre)
        if isinstance(n, ast.Assign)
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id == "TRIMESTRES_PAR_AN"
    }
    mal = [
        n.value
        for n in ast.walk(arbre)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, (int, float))
        and not isinstance(n.value, bool)
        and n.value not in (0, 1)
        and id(n) not in exclus
    ]
    assert mal == []
