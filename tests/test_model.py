import numpy as np
import pytest

from energywall import model as M
from energywall import sources as S

NEUTRE = {
    "E_DC0": 415.0, "s_AI": 0.15, "s_train": 0.35, "PUE_2024": 1.4, "PUE_2035": 1.4,
    "g_conv": 0.0, "g_Ctrain_2025": 1.0, "g_Ctrain_2035": 1.0,
    "g_tok_2025": 1.0, "g_tok_2035": 1.0, "g_fpt_net": 1.0, "T_d_parc": 1e12,
    "CI_ref": 458.0, "annee_ref_CI": 2025.0, "d_CI": 0.015, "WUE_site": 1.0, "EWIF": 1.6,
}


def _aleatoire(rng):
    p = dict(NEUTRE)
    p.update(
        s_AI=rng.uniform(0.02, 0.4), s_train=rng.uniform(0.1, 0.7),
        PUE_2024=rng.uniform(1.1, 1.8), PUE_2035=rng.uniform(1.1, 1.8),
        g_conv=rng.uniform(0, 0.1), g_Ctrain_2025=rng.uniform(1.2, 3),
        g_Ctrain_2035=rng.uniform(1.0, 1.2), g_tok_2025=rng.uniform(1.2, 3),
        g_tok_2035=rng.uniform(1.0, 1.2), g_fpt_net=rng.uniform(0.9, 1.1),
        T_d_parc=rng.uniform(1.5, 5),
    )
    return p


def test_edem_2024_egal_edc0_scenarios_et_aleatoire():
    rng = np.random.default_rng(0)
    jeux = [M.scenario_params(s) for s in M.SCENARIOS] + [_aleatoire(rng) for _ in range(20)]
    for p in jeux:
        assert M.project(p).loc[2024, "E_dem"] == pytest.approx(p["E_DC0"], rel=1e-9)


def test_croissances_neutres_donnent_edc0_constant():
    df = M.project(NEUTRE)
    assert df["E_dem"].to_numpy() == pytest.approx(415.0, rel=1e-9)


def test_loi_fermee_poste_isole():
    # Seule l'inférence croît : E_inf(t) = E_DC0 s_AI (1-s_train) g^n ; autres postes constants.
    p = {**NEUTRE, "g_tok_2025": 1.5, "g_tok_2035": 1.5}
    df = M.project(p)
    n = np.arange(12)
    attendu = 415 * 0.15 * 0.65 * 1.5**n
    assert df["E_inf"].to_numpy() == pytest.approx(attendu, rel=1e-9)
    assert df["E_conv"].to_numpy() == pytest.approx(415 * 0.85, rel=1e-9)
    assert df["E_train"].to_numpy() == pytest.approx(415 * 0.15 * 0.35, rel=1e-9)
    # Efficacité du parc seule : E_train / 2^(n/T)
    q = {**NEUTRE, "T_d_parc": 3.0}
    assert M.project(q)["E_train"].to_numpy() == pytest.approx(
        415 * 0.15 * 0.35 / 2 ** (n / 3.0), rel=1e-9
    )


def test_trajectoire_constante_et_decroissante():
    n = np.arange(12)
    assert M.trajectoire(1.7, 1.7) == pytest.approx(1.7**n, rel=1e-9)
    F = M.trajectoire(2.0, 1.2)
    assert F[0] == 1.0 and F[1] == pytest.approx(2.0)
    taux = F[1:] / F[:-1]
    assert np.all(np.diff(taux) < 0)
    assert taux[-1] == pytest.approx(1.2)


def test_co2_415_twh_458():
    assert M.co2_mt(415.0, 458.0) == pytest.approx(190.07, abs=0.005)


def test_eau_unite():
    assert M.eau_hm3(1.0, 1.0, 0.0, 1.0) == pytest.approx(1.0)
    assert M.eau_hm3(1.0, 2.0, 1.0, 0.0) == pytest.approx(0.5)  # E/PUE


def test_co2_et_eau_coherents_dans_project():
    p = M.scenario_params("normal")
    df = M.project(p)
    assert df.loc[2025, "CI"] == pytest.approx(p["CI_ref"])
    assert df.loc[2035, "CO2_Mt"] == pytest.approx(df.loc[2035, "E_dem"] * df.loc[2035, "CI"] / 1000)


def test_valeurs_reelles_dans_40_pct_des_cibles_iea():
    df = M.run_scenarios()
    for s in M.SCENARIOS:
        e = df.loc[(s, 2035), "E_dem"]
        cible = M.cible_iea(s)
        assert abs(e / cible - 1) < 0.40, (s, e, cible)


def test_ordre_des_scenarios():
    df = M.run_scenarios()
    for a in range(2026, 2036):
        o, n, p = (df.loc[(s, a), "E_dem"] for s in ("optimiste", "normal", "pessimiste"))
        assert o < n < p, a


def test_implied_param_atteint_la_cible():
    p = M.scenario_params("normal")
    cible = 1100.0
    x, _ = M.implied_param("normal", cible)
    e = M.project({**p, "g_tok_2025": x}).loc[2035, "E_dem"]
    assert e == pytest.approx(cible, rel=1e-6)


def test_implied_param_drapeau_hors_plage():
    t = S.load_params().set_index(["param", "borne"])["valeur"]
    x, ok = M.implied_param("normal", 1200.0)  # nécessite g_tok_2025 > high de la plage
    assert ok == (t[("g_tok_2025", "low")] <= x <= t[("g_tok_2025", "high")])
    x_bas, ok_bas = M.implied_param("normal", 600.0)
    assert x_bas < t[("g_tok_2025", "low")] and ok_bas is False
    _, ok_c = M.implied_param("normal", float(M.project(M.scenario_params("normal")).loc[2035, "E_dem"]))
    assert ok_c is True


def test_implied_param_cible_inatteignable():
    with pytest.raises(M.CibleInatteignable) as ei:
        M.implied_param("normal", 1e9)
    assert ei.value.e_bas < ei.value.e_haut < 1e9
    with pytest.raises(M.CibleInatteignable):
        M.implied_param("normal", 1.0)


@pytest.mark.parametrize("s", M.SCENARIOS)
def test_mur_positif_nul_en_2024(s):
    w = M.wall_stress(s)
    cols = [c for c in w.columns if c.startswith("E_wall_")]
    assert len(cols) == 3
    assert (w[cols] >= 0).all().all()
    assert (w.loc[2024, cols] == 0).all()
    for b in S.BORNES:
        assert w.loc[2024, f"E_cap_{b}"] == pytest.approx(415.0)
        assert (w[f"E_wall_{b}"] == (w["E_dem"] - w[f"E_cap_{b}"]).clip(lower=0)).all()


@pytest.mark.parametrize("s", M.SCENARIOS)
def test_forme_index_et_finitude(s):
    df = M.project(M.scenario_params(s))
    assert len(df) == 12
    assert list(df.index) == list(range(2024, 2036))
    assert df.index.dtype.kind == "i"
    assert np.isfinite(df.to_numpy()).all()
    assert list(df.columns) == M.COLONNES


def test_run_scenarios_multiindex():
    df = M.run_scenarios()
    assert len(df) == 36
    assert np.isfinite(df.to_numpy()).all()


def test_scenario_inconnu():
    with pytest.raises(KeyError):
        M.scenario_params("zzz")


def test_bottom_up():
    r = M.bottom_up_check()
    assert r["E_bu_min"] < r["E_bu"] < r["E_bu_max"]
    assert r["ratio"] == pytest.approx(r["E_bu"] / (415 * 0.15))
    # (5e26 + 2*1e11*1e16)/3e11 J x 1,4 / 3,6e15 J/TWh
    assert r["E_bu"] == pytest.approx((5e26 + 2e27) / 3e11 * 1.4 / 3.6e15)


def test_params_bottom_up_dans_registre_et_validation():
    S.validate()
    df = S.load_params()
    for nom in ("C_train_2024", "N_act", "Tokens_2024", "eff_eff"):
        assert (df[df.param == nom].statut == "H").all()


def test_ratio_pue_applique_aux_trois_postes():
    # PUE variable 1,4 -> 1,8 ; croissances neutres ; attendu en forme fermée indépendante.
    p = {**NEUTRE, "PUE_2035": 1.8}
    df = M.project(p)
    n = np.arange(12)
    ratio = (1.4 + 0.4 * n / 11) / 1.4
    assert df["E_conv"].to_numpy() == pytest.approx(415 * 0.85 * ratio, rel=1e-9)
    assert df["E_train"].to_numpy() == pytest.approx(415 * 0.15 * 0.35 * ratio, rel=1e-9)
    assert df["E_inf"].to_numpy() == pytest.approx(415 * 0.15 * 0.65 * ratio, rel=1e-9)
    assert df.loc[2035, "E_dem"] == pytest.approx(415 * 1.8 / 1.4, rel=1e-9)


def test_co2_valeurs_en_dur():
    # CI(2030) = 458 x 0,985^5 ; CI(2035) = 458 x 0,985^10 (annee_ref_CI = 2025), calcul à la main.
    df = M.project(NEUTRE)
    assert df.loc[2030, "CI"] == pytest.approx(424.665, abs=1e-3)
    assert df.loc[2035, "CI"] == pytest.approx(393.757, abs=1e-3)
    assert df.loc[2035, "CO2_Mt"] == pytest.approx(415 * 393.757 / 1000, abs=1e-3)


def test_eau_dans_project_forme_fermee():
    # 2035 : E = 415 x 1,8/1,4 ; W = E/1,8 x 1,0 + E x 1,6 = 415/1,4 + 415 x 1,8/1,4 x 1,6
    df = M.project({**NEUTRE, "PUE_2035": 1.8})
    assert df.loc[2035, "W_hm3"] == pytest.approx(1150.143, abs=1e-3)
    assert df.loc[2024, "W_hm3"] == pytest.approx(415 / 1.4 + 415 * 1.6, rel=1e-9)


def test_implied_param_parametre_inconnu():
    with pytest.raises(ValueError, match="inconnu"):
        M.implied_param("normal", 1000.0, param="zzz")


def test_implied_param_monotonie_verifiee():
    # Bracket inversé : E_dem(borne haute) < E_dem(borne basse) -> erreur explicite
    with pytest.raises(ValueError, match="croissante"):
        M.implied_param("normal", 1000.0, bracket=(10.0, 1.0))


# Garde de refactor (L-08) : sorties 2035 figées, relevées avant le passage au noyau vectorisé.
# Seul endroit où des valeurs de sortie sont figées ; à mettre à jour seulement si le modèle change.
FIGE_2035 = {
    "pessimiste": (2154.830257425733, 938.662246370476, 10081.29048127947),
    "normal": (978.7909277103267, 385.4053315791133, 2349.098226504784),
    "optimiste": (510.5705593385353, 172.4402284138213, 701.1835681582552),
}


@pytest.mark.parametrize("scenario", list(FIGE_2035))
def test_non_regression_2035(scenario):
    r = M.project(M.scenario_params(scenario)).loc[2035]
    obtenu = (r["E_dem"], r["CO2_Mt"], r["W_hm3"])
    assert obtenu == pytest.approx(FIGE_2035[scenario], rel=1e-6)


# --- Stress test « miracle » (L2) ---
def _e2035(scenario, t_d):
    return M.project({**M.scenario_params(scenario), "T_d_parc": t_d}).loc[2035, "E_dem"]


@pytest.mark.parametrize("scenario", M.SCENARIOS)
def test_edem_croissant_en_t_d_parc(scenario):
    p = M.scenario_params(scenario)
    e = np.array([M.project({**p, "T_d_parc": t})["E_dem"].to_numpy() for t in (0.5, 1, 2, 5, 50)])
    assert (np.diff(e[:, 1:], axis=0) > 0).all()


@pytest.mark.parametrize("scenario", M.SCENARIOS)
def test_t_d_max_2035_atteint_la_cible(scenario):
    cible = M.cible_iea("optimiste")
    r = M.t_d_max_admissible(scenario, cible, "2035")
    assert r["statut"] == "ok"
    assert _e2035(scenario, r["T_star"]) == pytest.approx(cible, rel=1e-6)
    assert r["max_E_wall"] >= 0


def test_t_d_max_chiffres_de_controle():
    cible = M.cible_iea("optimiste")
    att = {"pessimiste": 1.63, "normal": 2.21, "optimiste": 3.51}
    for s, v in att.items():
        assert M.t_d_max_admissible(s, cible, "2035")["T_star"] == pytest.approx(v, abs=0.01)


@pytest.mark.parametrize("scenario", M.SCENARIOS)
@pytest.mark.parametrize("borne", S.BORNES)
def test_t_d_max_trajectoire(scenario, borne):
    c = M.e_cap(scenario, borne)
    r35 = M.t_d_max_admissible(scenario, c, "2035")
    rtr = M.t_d_max_admissible(scenario, c, "trajectoire")
    assert rtr["statut"] == r35["statut"] == "ok"
    e = M.project({**M.scenario_params(scenario), "T_d_parc": rtr["T_star"]})["E_dem"].to_numpy()
    assert (e - c)[1:].max() == pytest.approx(0.0, abs=1e-5)
    assert rtr["T_star"] <= r35["T_star"] + 1e-9


def test_t_d_max_cas_limites():
    bas, haut = S.raw_params()["miracle"]["bracket_T_d"]
    r = M.t_d_max_admissible("normal", _e2035("normal", bas) - 1.0, "2035")
    assert (r["statut"], r["T_star"], r["zone"], r["deja_tenue"]) == ("sous_plancher", None, None, False)
    r = M.t_d_max_admissible("normal", _e2035("normal", haut) + 1.0, "2035")
    assert (r["statut"], r["T_star"], r["deja_tenue"]) == ("non_contraignant", None, True)


def test_t_d_max_deja_tenue_cas_ok():
    cible = M.cible_iea("optimiste")
    r = M.t_d_max_admissible("optimiste", cible, "2035")
    assert r["statut"] == "ok"
    assert r["T_d_parc"] <= r["T_star"]
    assert r["deja_tenue"] is True
    r = M.t_d_max_admissible("pessimiste", cible, "2035")
    assert r["T_d_parc"] > r["T_star"]
    assert r["deja_tenue"] is False


def test_t_d_max_nan_leve_valueerror():
    with pytest.raises(ValueError, match="NaN"):
        M.t_d_max_admissible("normal", float("nan"), "2035")


def test_wall_stress_utilise_e_cap():
    w = M.wall_stress("normal")
    for b in S.BORNES:
        assert np.array_equal(w[f"E_cap_{b}"].to_numpy(), M.e_cap("normal", b))


def test_t_d_max_critere_inconnu():
    with pytest.raises(ValueError, match="critère"):
        M.t_d_max_admissible("normal", 700.0, "zzz")


def test_zones_pointe_epoch():
    pe = S.raw_params()["miracle"]["pointe_epoch"]
    lo, hi = pe["low"]["valeur"], pe["high"]["valeur"]
    assert M._zone(lo - 0.01) == "plus_rapide_que_la_pointe"
    assert M._zone(lo) == M._zone(hi) == "le_parc_suit_la_pointe"
    assert M._zone(hi + 0.01) == "plausible"


def test_miracle_table_forme():
    t = M.miracle_table()
    assert len(t) == len(M.SCENARIOS) * (1 + len(S.BORNES)) * len(M.CRITERES)
    assert set(t["statut"]) <= set(M.STATUTS_MIRACLE)
    assert not t["statut"].eq("ok").eq(t["T_star"].isna()).any()


def test_miracle_ne_modifie_pas_les_scenarios():
    avant = M.run_scenarios()
    M.miracle_table()
    assert M.run_scenarios().equals(avant)
    for s, (e35, _, _) in FIGE_2035.items():
        assert _e2035(s, M.scenario_params(s)["T_d_parc"]) == pytest.approx(e35, rel=1e-6)


def test_validate_miracle_bracket_invalide():
    p = S.raw_params()
    p = {**p, "miracle": {**p["miracle"], "bracket_T_d": [0, 100]}}
    with pytest.raises(S.ValidationError, match="bracket_T_d"):
        S.validate(params=p)
