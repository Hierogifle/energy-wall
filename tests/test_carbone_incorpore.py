import copy

import numpy as np
import pandas as pd
import pytest

from energywall import backtest as B
from energywall import incertitude as inc
from energywall import model as M
from energywall import sources as S


def _r(borne):
    return float(M._table()[("r_s3", borne)])


@pytest.fixture
def sans_r_s3(monkeypatch):
    """S.raw_params sans r_s3 : état « avant » le lot, pour prouver l'identité des sorties."""
    p = copy.deepcopy(S.raw_params())
    del p["params"]["r_s3"]
    monkeypatch.setattr(S, "raw_params", lambda: p)


def test_formule_et_unites():
    # 1 TWh x 1 g/kWh = 1 kt = 1/KT_PAR_MT Mt
    assert M.co2_incorpore_mt(1.0, 1.0, 1.0) == pytest.approx(1.0 / M.KT_PAR_MT)
    assert M.co2_incorpore_mt(1200.0, 0.05, 458.0) == pytest.approx(0.05 * 1200 * 458 / 1000)


@pytest.mark.parametrize("scenario", M.SCENARIOS)
def test_table_valeurs_et_ratio(scenario):
    t, p = M.carbone_incorpore(scenario), M.scenario_params(scenario)
    d = M.project(p)
    for b in S.BORNES:
        np.testing.assert_allclose(
            t[f"CO2_incorpore_Mt_{b}"], _r(b) * d["E_dem"] * p["CI_ref"] / 1000, rtol=1e-12
        )
        np.testing.assert_allclose(
            t[f"intensite_incorporee_g_kwh_{b}"], _r(b) * p["CI_ref"], rtol=1e-12
        )
        ratio = t[f"ratio_effectif_{b}"]
        # = r_s3 en année de référence, puis croissant (d_CI > 0)
        assert ratio[int(p["annee_ref_CI"])] == pytest.approx(_r(b))
        apres = ratio.loc[int(p["annee_ref_CI"]) :]
        assert p["d_CI"] > 0 and apres.is_monotonic_increasing and apres.iloc[-1] > _r(b)
        np.testing.assert_allclose(ratio, t[f"CO2_incorpore_Mt_{b}"] / t["CO2_Mt"], rtol=1e-9)


def test_bornes_ordonnees_et_aucune_colonne_total():
    assert _r("low") < _r("central") < _r("high")
    for s in M.SCENARIOS:
        t = M.carbone_incorpore(s)
        assert not any("total" in c.lower() for c in t.columns)
        np.testing.assert_array_equal(t["CO2_Mt"], M.project(M.scenario_params(s))["CO2_Mt"])


def test_validation_r_s3():
    S.validate()
    dfp = S.load_params().set_index(["param", "borne"])
    assert dfp.loc[("r_s3", "low"), "statut"] == "D"
    assert dfp.loc[("r_s3", "low"), "source_ids"] == ["morrison_2025"]
    assert "22 / (471" in dfp.loc[("r_s3", "low"), "justification"]
    raw = copy.deepcopy(S.raw_params())
    raw["params"]["r_s3"]["low"]["valeur"] = 0.9  # viole low <= central <= high
    with pytest.raises(S.ValidationError):
        S.validate(params=raw)
    raw = copy.deepcopy(S.raw_params())
    raw["params"]["r_s3"]["high"]["justification"] = ""
    with pytest.raises(S.ValidationError):
        S.validate(params=raw)


def test_r_s3_hors_scenarios_et_mc():
    assert "r_s3" in S.raw_params()["params"]
    assert all("r_s3" not in jeu for jeu in S.raw_params()["scenarios"]["jeux"].values())
    assert "r_s3" not in inc.params_tires() and "r_s3" not in inc.tirages(n=5).columns
    assert "r_s3" not in M.scenario_params("normal")


def test_scenarios_et_mc_identiques_avant_apres(monkeypatch):
    apres_sc = M.run_scenarios()
    apres_mc = inc.simulate()
    apres_b0 = B.point_2025(apres_mc)

    p = copy.deepcopy(S.raw_params())
    del p["params"]["r_s3"]  # état « avant »
    monkeypatch.setattr(S, "raw_params", lambda: p)
    avant_sc = M.run_scenarios()
    avant_mc = inc.simulate()
    avant_b0 = B.point_2025(avant_mc)

    pd.testing.assert_frame_equal(apres_sc, avant_sc, rtol=1e-9, atol=0)
    for s in inc.SORTIES:
        pd.testing.assert_frame_equal(
            inc.quantiles(apres_mc, s), inc.quantiles(avant_mc, s), rtol=1e-9, atol=0
        )
        np.testing.assert_allclose(apres_mc[s][M.ANNEE1], avant_mc[s][M.ANNEE1], rtol=1e-9)
    assert apres_b0["hors_intervalle"] == avant_b0["hors_intervalle"]
    np.testing.assert_allclose(apres_b0["intervalle_taux"], avant_b0["intervalle_taux"], rtol=1e-9)
    assert apres_b0["part_taux_ge"] == pytest.approx(avant_b0["part_taux_ge"], abs=1e-9)
    np.testing.assert_allclose(
        apres_b0["taux_quantiles"], avant_b0["taux_quantiles"], rtol=1e-9
    )


def test_carbone_incorpore_leve_keyerror_sans_r_s3(sans_r_s3):
    with pytest.raises(KeyError):
        M.carbone_incorpore("normal")


def test_carbone_incorpore_calcule_sans_mc(monkeypatch):
    def interdit(*a, **k):
        raise AssertionError("le Monte Carlo ne doit pas être appelé")

    monkeypatch.setattr(inc, "simulate", interdit)
    monkeypatch.setattr(inc, "tirages", interdit)
    t = M.carbone_incorpore("normal")
    assert np.isfinite(t["CO2_incorpore_Mt_central"]).all()
