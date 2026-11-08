import numpy as np
import pandas as pd
import pytest

from energywall import incertitude as inc
from energywall import model as M
from energywall import sources as S

SORTIES = ("E_dem", "CO2_Mt", "W_hm3")
N_TEST = 4000  # fixe pour les tests statistiques ; la graine vient du yaml


@pytest.fixture(scope="module")
def res_tri():
    return inc.simulate(n=N_TEST, loi="triangulaire")


@pytest.fixture(scope="module")
def res_uni():
    return inc.simulate(n=N_TEST, loi="uniforme")


def _bornes():
    return S.load_params().pivot(index="param", columns="borne", values="valeur").astype(float)


# (a)(b) noyau vectorisé == project
@pytest.mark.parametrize("n", [50, 12, 1])
def test_noyau_egal_project(n):
    par = inc.tirages(n=n)
    out = M.project_batch({k: par[k].to_numpy() for k in par})
    for i in range(n):
        ref = M.project({k: float(par[k][i]) for k in par})
        for s in ("E_conv", "E_train", "E_inf", "E_dem", "PUE", "CI", "CO2_Mt", "W_hm3"):
            assert out[s].shape == (n, 12)
            np.testing.assert_allclose(out[s][i], ref[s].to_numpy(), rtol=1e-9)


def test_trajectoire_vectorielle_egale_scalaire():
    g25, g35 = np.array([1.9, 2.1, 1.7]), np.array([1.2, 1.3, 1.15])
    F = M.trajectoire(g25, g35)
    assert F.shape == (3, 12)
    for i in range(3):
        np.testing.assert_allclose(F[i], M.trajectoire(g25[i], g35[i]), rtol=1e-12)
    assert M.trajectoire(2.0, 1.3).shape == (12,)


# (c) tirages
@pytest.mark.parametrize("loi", ["triangulaire", "uniforme"])
def test_tirages_dans_les_bornes_et_constantes(loi):
    t, b = inc.tirages(n=N_TEST, loi=loi), _bornes()
    assert list(t.columns) == inc.params_tires() and len(inc.params_tires()) == 17
    assert "g_cap" not in t.columns
    for p in t:
        assert (t[p] >= b.loc[p, "low"]).all() and (t[p] <= b.loc[p, "high"]).all()
        if b.loc[p, "low"] == b.loc[p, "high"]:
            assert (t[p] == b.loc[p, "low"]).all()
    for p in ("E_DC0", "CI_ref", "annee_ref_CI"):
        assert t[p].nunique() == 1


def test_graine():
    a, b = inc.tirages(n=100, graine=7), inc.tirages(n=100, graine=7)
    c = inc.tirages(n=100, graine=8)
    pd.testing.assert_frame_equal(a, b)
    assert not a["s_AI"].equals(c["s_AI"])


def test_loi_inconnue():
    with pytest.raises(ValueError, match="loi inconnue"):
        inc.tirages(n=5, loi="normale")


@pytest.mark.parametrize("loi", ["triangulaire", "uniforme"])
def test_moyenne_empirique(loi):
    t, b = inc.tirages(n=N_TEST, loi=loi), _bornes()
    for p in inc._variables():
        lo, c, hi = b.loc[p, ["low", "central", "high"]]
        if loi == "triangulaire":
            moy = (lo + c + hi) / 3
            sig = np.sqrt((lo**2 + c**2 + hi**2 - lo * c - lo * hi - c * hi) / 18)
        else:
            moy, sig = (lo + hi) / 2, (hi - lo) / np.sqrt(12)
        assert abs(t[p].mean() - moy) <= 4 * sig / np.sqrt(N_TEST), p


# (d) trajectoires décroissantes
def test_plages_croissance_disjointes():
    b = _bornes()
    for x in ("g_Ctrain", "g_tok"):
        assert b.loc[f"{x}_2035", "high"] < b.loc[f"{x}_2025", "low"], x


@pytest.mark.parametrize("loi", ["triangulaire", "uniforme"])
def test_croissance_decroissante_dans_les_tirages(loi):
    t = inc.tirages(n=N_TEST, loi=loi)
    for x in ("g_Ctrain", "g_tok"):
        assert (t[f"{x}_2025"] >= t[f"{x}_2035"]).all()


# (e) forme et identité
def test_forme_identite_finitude(res_tri, res_uni):
    for res in (res_tri, res_uni):
        for s in SORTIES:
            df = res[s]
            assert df.shape == (N_TEST, 12)
            assert list(df.columns) == M.ANNEES and df.columns.dtype.kind == "i"
            assert np.isfinite(df.to_numpy()).all()
        np.testing.assert_allclose(res["E_dem"][2024], res["params"]["E_DC0"], rtol=1e-9)


# (f) quantiles et parts
def test_quantiles_croissants_et_mediane_entre_scenarios(res_tri, res_uni):
    d = M.run_scenarios()
    for res in (res_tri, res_uni):
        for s in SORTIES:
            q = inc.quantiles(res, s)
            assert list(q.index) == M.ANNEES
            assert list(q.columns) == S.raw_params()["monte_carlo"]["quantiles"]
            assert (np.diff(q.to_numpy(), axis=1) >= 0).all()
        med = inc.quantiles(res, "E_dem").loc[2035, 0.5]
        assert d.loc[("optimiste", 2035), "E_dem"] < med < d.loc[("pessimiste", 2035), "E_dem"]
        # quantiles strictement croissants dès 2026 ; en 2024 E_dem = E_DC0 constant (ex aequo)
        assert (np.diff(inc.quantiles(res, "E_dem").loc[2026:].to_numpy(), axis=1) > 0).all()


def test_parts_vs_iea(res_tri, res_uni):
    for res in (res_tri, res_uni):
        p = inc.parts_vs_iea(res)
        assert set(p) == {"sous_optimiste", "entre", "au_dessus_pessimiste"}
        assert all(0 <= v <= 1 for v in p.values())
        assert sum(p.values()) == pytest.approx(1.0, abs=1e-12)


# (g) tornado
def test_tornado_structure_et_central():
    t = inc.tornado()
    normal = M.run_scenarios().loc[("normal", 2035), "E_dem"]
    np.testing.assert_allclose(t["y_central"], normal, rtol=1e-9)
    assert not {"E_DC0", "CI_ref", "annee_ref_CI", "g_cap"} & set(t["param"])
    assert set(t["param"]) == set(inc._variables()) and len(t) == 14
    assert (np.diff(t["amplitude"]) <= 0).all()
    lo = t[["y_low", "y_high"]].min(axis=1)
    hi = t[["y_low", "y_high"]].max(axis=1)
    assert ((lo <= t["y_central"] + 1e-9) & (t["y_central"] <= hi + 1e-9)).all()
    assert np.isfinite(t[["y_low", "y_high", "amplitude", "elasticite"]].to_numpy()).all()


def test_tornado_sens_variable():
    t = inc.tornado().set_index("param")
    for p in ("s_train", "PUE_2024"):
        assert t.loc[p, "y_low"] > t.loc[p, "y_high"]
    assert t.loc["s_AI", "y_low"] < t.loc["s_AI", "y_high"]
    c = inc.tornado("CO2_Mt").set_index("param")
    assert c.loc["d_CI", "y_low"] > c.loc["d_CI", "y_high"]


@pytest.mark.parametrize(
    "sortie,nuls,non_nuls",
    [
        ("E_dem", ("d_CI", "WUE_site", "EWIF"), ("s_AI",)),
        ("CO2_Mt", ("WUE_site", "EWIF"), ("d_CI", "s_AI")),
        ("W_hm3", ("d_CI",), ("WUE_site", "EWIF")),
    ],
)
def test_tornado_amplitudes_nulles(sortie, nuls, non_nuls):
    t = inc.tornado(sortie).set_index("param")
    for p in nuls:
        assert t.loc[p, "amplitude"] == 0, p
        assert p in t.index  # gardé, pas supprimé
    for p in non_nuls:
        assert t.loc[p, "amplitude"] > 0, p
    assert t.index[-len(nuls) :].isin(nuls).all()


def test_tornado_annee_au_choix():
    assert inc.tornado(annee=2030)["y_central"].iloc[0] != inc.tornado()["y_central"].iloc[0]


# (h) Spearman
def test_spearman(res_tri):
    s = inc.spearman(res_tri)
    assert set(s.index) == set(inc._variables())
    assert ((s >= -1) & (s <= 1)).all()
    assert s["g_tok_2025"] > 0
    assert (np.diff(s.abs().to_numpy()) <= 0).all()


# (i) config
def test_mc_config_reelle():
    cfg = inc.mc_config()
    assert cfg["loi"] in S.LOIS_MC and cfg["n_tirages"] > 0


def test_mc_config_absente(monkeypatch):
    p = S.raw_params()
    p.pop("monte_carlo")
    monkeypatch.setattr(S, "raw_params", lambda: p)
    with pytest.raises(KeyError, match="monte_carlo"):
        inc.mc_config()


def test_mc_config_invalide(monkeypatch):
    p = S.raw_params()
    p["monte_carlo"]["n_tirages"] = 0
    monkeypatch.setattr(S, "raw_params", lambda: p)
    with pytest.raises(S.ValidationError, match="n_tirages"):
        inc.mc_config()
