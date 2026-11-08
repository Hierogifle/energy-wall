import pandas as pd
import pytest

from energywall import report as R
from energywall import sources as S


def test_registre_une_ligne_par_source():
    assert len(R.registre()) == len(S.raw_sources())
    assert "interet" in R.registre().columns


def test_crosstab_total_coherent():
    ct = R.acteur_x_lecture()
    assert ct.loc["total", "total"] == len(S.raw_sources())


def test_biais_comptes():
    n = sum(len(s["biais"]) for s in S.raw_sources())
    assert len(R.biais_long()) == n
    assert R.biais_par_sens().sum() == n
    assert R.biais_sens_x_grandeur().loc["total", "total"] == n


def test_bloquees_et_nt():
    attendu = {
        s["id"] for s in S.raw_sources() if s["statut_lecture"] in R.BLOQUEES
    }
    assert attendu  # le registre contient bien des sources bloquées
    assert set(R.sources_bloquees()["id"]) == attendu
    assert set(R.BLOQUEES) == {"pdf_illisible", "paywall", "non_trouve"}
    assert {"kaplan_2020", "hoffmann_2022"} <= set(R.relations_nt()["source"])
    assert {"C_train_2024", "N_act"} <= set(R.params_nt())


def test_bornes_par_statut_somme_100():
    b = R.bornes_par_statut()
    assert b["n"].sum() == len(S.load_params())
    assert abs(b["part_%"].sum() - 100) < 1e-9


def test_params_tout_h_sont_tout_h():
    df = S.load_params()
    # s_train n'est plus tout H : bornes 0,20/0,40 sourcées D (IEA-4E 2025, p. 29)
    assert "s_train" not in R.params_tout_h() and "g_Ctrain_2035" in R.params_tout_h()
    assert "E_DC0" not in R.params_tout_h()
    for p in R.params_tout_h():
        assert (df[df["param"] == p]["statut"] == "H").all()


@pytest.fixture
def mini_params(monkeypatch):
    # a : H H V ; b : H H D ; c : V V V
    lignes = [("a", "H"), ("a", "H"), ("a", "V"), ("b", "H"), ("b", "H"), ("b", "D"),
              ("c", "V"), ("c", "V"), ("c", "V")]
    df = pd.DataFrame(lignes, columns=["param", "statut"])
    monkeypatch.setattr(S, "load_params", lambda: df)


def test_part_h_valeurs_litterales(mini_params):
    p = R.part_h(["a", "b"])  # 6 bornes : 4 H, 1 V, 1 D
    assert p["H"] == pytest.approx(100 * 4 / 6)
    assert p["V"] == pytest.approx(100 / 6)
    assert p["D"] == pytest.approx(100 / 6)
    assert p["S"] == 0
    assert R.part_h(["c"])["H"] == 0


def test_part_h_garde(mini_params):
    with pytest.raises(ValueError, match="vide"):
        R.part_h([])
    with pytest.raises(ValueError, match="inconnus"):
        R.part_h(["a", "zzz"])


def test_tracabilite_index():
    t = R.tracabilite()
    assert len(t) == len(S.load_params())
    assert (t.loc[("s_train", "central"), "justification"]).strip()
    assert t["source_ids"].map(lambda x: isinstance(x, str)).all()
