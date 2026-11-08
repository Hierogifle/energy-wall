import copy
import datetime as dt
import hashlib

import pytest
import yaml

from energywall import sources as S
from energywall.sources import ValidationError, validate

MINI_SOURCES = """
sources:
  - id: src_a
    titre: A
    organisation: Org
    type_acteur: agence_publique
    type_acteur_qualifie: false
    url: https://exemple.test/a
    url_relais: null
    statut_lecture: lu_source
    date_publication: inconnue
    date_consultation: 2026-01-01
    version: null
    periode_donnees: "2024"
    licence: inconnue
    perimetre: monde
    methode: mesure
    interet: "a_qualifier : test"
    biais:
      - {description: d, sens: indetermine, grandeur: x}
    utilise_pour: [p1]
  - id: src_b
    titre: B
    organisation: Org
    type_acteur: presse
    type_acteur_qualifie: true
    url: https://exemple.test/b
    url_relais: null
    statut_lecture: relais
    date_publication: inconnue
    date_consultation: 2026-01-01
    version: null
    periode_donnees: "2024"
    licence: inconnue
    perimetre: monde
    methode: declaratif
    interet: i
    biais:
      - {description: d, sens: surestimation, grandeur: x}
    utilise_pour: [p2]
  - id: src_c
    titre: C
    organisation: Org
    type_acteur: preprint
    type_acteur_qualifie: true
    url: https://exemple.test/c
    url_relais: null
    statut_lecture: paywall
    date_publication: inconnue
    date_consultation: 2026-01-01
    version: null
    periode_donnees: "2024"
    licence: inconnue
    perimetre: monde
    methode: estimation_secondaire
    interet: i
    biais:
      - {description: d, sens: sous-estimation, grandeur: x}
    utilise_pour: []
"""

MINI_PARAMS = """
params:
  p1:
    unite: TWh
    description: d
    low: {valeur: 1, statut: V, source_ids: [src_a], justification: ""}
    central: {valeur: 2, statut: V, source_ids: [src_a], justification: ""}
    high: {valeur: 3, statut: V, source_ids: [src_a], justification: ""}
  p2:
    unite: u
    description: d
    low: {valeur: 1, statut: S, source_ids: [src_b], justification: ""}
    central: {valeur: 2, statut: H, source_ids: [], justification: choix}
    high: {valeur: 3, statut: D, source_ids: [src_b], justification: derive}
  g_x_2025:
    unite: facteur/an
    description: d
    low: {valeur: 1.5, statut: H, source_ids: [], justification: j}
    central: {valeur: 1.8, statut: H, source_ids: [], justification: j}
    high: {valeur: 2.0, statut: H, source_ids: [], justification: j}
  g_x_2035:
    unite: facteur/an
    description: d
    low: {valeur: 1.1, statut: H, source_ids: [], justification: j}
    central: {valeur: 1.2, statut: H, source_ids: [], justification: j}
    high: {valeur: 1.3, statut: H, source_ids: [], justification: j}
scenarios:
  sens: {p1: "plus haut = plus de TWh", p2: "idem"}
  jeux:
    normal: {p1: central, p2: central}
cibles_iea:
  - {annee: 2030, scenario: base, cas_iea: Base, valeur: 9, unite: TWh, statut: V, source_ids: [src_a], note: n}
"""


@pytest.fixture
def mini():
    return yaml.safe_load(MINI_SOURCES)["sources"], yaml.safe_load(MINI_PARAMS)


def expect(srcs, params, motif):
    with pytest.raises(ValidationError, match=motif):
        validate(srcs, params)


def test_mini_valide(mini):
    validate(*mini)


def test_source_referencee_absente(mini):
    s, p = mini
    p["params"]["p1"]["low"]["source_ids"] = ["inexistante"]
    expect(s, p, "absente du registre")


def test_champ_obligatoire_manquant(mini):
    s, p = mini
    del s[0]["perimetre"]
    expect(s, p, "champ obligatoire manquant 'perimetre'")


def test_biais_vide(mini):
    s, p = mini
    s[0]["biais"] = []
    expect(s, p, "biais vide")


def test_enum_inconnue_source(mini):
    s, p = mini
    s[0]["type_acteur"] = "blog"
    expect(s, p, "type_acteur inconnu")


@pytest.mark.parametrize("champ", ["interet", "perimetre", "titre", "periode_donnees"])
@pytest.mark.parametrize("vide", ["", "   "])
def test_champ_obligatoire_vide(mini, champ, vide):
    s, p = mini
    s[0][champ] = vide
    expect(s, p, f"champ obligatoire vide '{champ}'")


@pytest.mark.parametrize("mauvais", ["texte", None, 3, {"description": "d"}, {"sens": "indetermine"}])
def test_biais_element_invalide(mini, mauvais):
    s, p = mini
    s[0]["biais"] = [mauvais]
    with pytest.raises(ValidationError):
        validate(s, p)


def test_enum_inconnue_statut_lecture(mini):
    s, p = mini
    s[0]["statut_lecture"] = "vu_en_reve"
    expect(s, p, "statut_lecture inconnu")


def test_enum_inconnue_methode(mini):
    s, p = mini
    s[0]["methode"] = "intuition"
    expect(s, p, "methode inconnu")


def test_type_acteur_qualifie_booleen(mini):
    s, p = mini
    s[0]["type_acteur_qualifie"] = "oui"
    expect(s, p, "type_acteur_qualifie doit être un booléen")


def test_type_acteur_qualifie_manquant(mini):
    s, p = mini
    del s[0]["type_acteur_qualifie"]
    expect(s, p, "champ obligatoire manquant 'type_acteur_qualifie'")


def test_enum_inconnue_sens_biais(mini):
    s, p = mini
    s[0]["biais"][0]["sens"] = "grand"
    expect(s, p, "sens inconnu")


def test_enum_inconnue_statut_borne(mini):
    s, p = mini
    p["params"]["p1"]["low"]["statut"] = "X"
    expect(s, p, "statut inconnu")


def test_ordre_bornes(mini):
    s, p = mini
    p["params"]["p1"]["central"]["valeur"] = 10
    expect(s, p, "low <= central <= high")


def test_egalite_bornes_acceptee(mini):
    s, p = mini
    for b in S.BORNES:
        p["params"]["p1"][b]["valeur"] = 5
    validate(s, p)


def test_h_sans_justification(mini):
    s, p = mini
    p["params"]["p2"]["central"]["justification"] = ""
    expect(s, p, "statut H sans justification")


def test_d_sans_justification(mini):
    s, p = mini
    p["params"]["p2"]["high"]["justification"] = "  "
    expect(s, p, "statut D sans justification")


def test_v_sans_source_ids(mini):
    s, p = mini
    p["params"]["p1"]["low"]["source_ids"] = []
    expect(s, p, "statut V sans source_ids")


def test_s_sans_source_ids(mini):
    s, p = mini
    p["params"]["p2"]["low"]["source_ids"] = []
    expect(s, p, "statut S sans source_ids")


def test_v_sur_source_non_lu_source(mini):
    s, p = mini
    p["params"]["p1"]["low"]["source_ids"] = ["src_b"]  # relais
    expect(s, p, "statut V mais la source 'src_b' est 'relais'")


@pytest.mark.parametrize("lecture", ["pdf_illisible", "paywall", "non_trouve"])
def test_v_sur_source_bloquee(mini, lecture):
    s, p = mini
    s[2]["statut_lecture"] = lecture
    p["params"]["p1"]["low"]["source_ids"] = ["src_a", "src_c"]
    expect(s, p, "statut V mais la source 'src_c'")


def test_s_sur_source_paywall(mini):
    s, p = mini
    p["params"]["p2"]["low"]["source_ids"] = ["src_c"]
    expect(s, p, "statut S mais la source 'src_c'")


def test_s_accepte_lu_source(mini):
    s, p = mini
    p["params"]["p2"]["low"]["source_ids"] = ["src_b", "src_a"]
    s[0]["utilise_pour"] = ["p1", "p2"]
    validate(s, p)


def test_utilise_pour_non_reciproque_source_vers_param(mini):
    s, p = mini
    s[2]["utilise_pour"] = ["p1"]
    expect(s, p, "aucune borne de p1 ne la cite")


def test_utilise_pour_non_reciproque_param_vers_source(mini):
    s, p = mini
    s[1]["utilise_pour"] = []
    expect(s, p, "absente de utilise_pour")


def test_utilise_pour_param_inconnu(mini):
    s, p = mini
    s[2]["utilise_pour"] = ["fantome"]
    expect(s, p, "paramètre inconnu 'fantome'")


def test_scenario_param_inconnu(mini):
    s, p = mini
    p["scenarios"]["jeux"]["normal"]["fantome"] = "central"
    expect(s, p, "paramètre inconnu 'fantome'")


def test_scenario_borne_inconnue(mini):
    s, p = mini
    p["scenarios"]["jeux"]["normal"]["p1"] = "milieu"
    expect(s, p, "borne inconnue 'milieu'")


def test_scenario_sens_manquant(mini):
    s, p = mini
    del p["scenarios"]["sens"]["p2"]
    expect(s, p, "sens non écrit")


def test_date_consultation_future(mini):
    s, p = mini
    s[0]["date_consultation"] = dt.date.today() + dt.timedelta(days=1)
    expect(s, p, "date_consultation future")


def test_unite_manquante(mini):
    s, p = mini
    p["params"]["p1"]["unite"] = ""
    expect(s, p, "unité manquante")


def test_croissance_2035_superieure_a_2025(mini):
    s, p = mini
    p["params"]["g_x_2035"]["high"]["valeur"] = 2.5
    expect(s, p, "croissance non décroissante")


def test_cible_source_absente(mini):
    s, p = mini
    p["cibles_iea"][0]["source_ids"] = ["inexistante"]
    expect(s, p, "cibles_iea")


def test_toutes_violations_listees(mini):
    s, p = mini
    s[0]["biais"] = []
    p["params"]["p1"]["unite"] = ""
    with pytest.raises(ValidationError) as e:
        validate(s, p)
    assert "biais vide" in str(e.value) and "unité manquante" in str(e.value)


def test_rapport_mini(mini):
    s, p = mini
    r = S.qualification_report(s, p)
    assert r["n_sources"] == 3 and r["n_interet_a_qualifier"] == 1
    assert r["n_sens_indetermine"] == 1
    assert r["n_type_acteur_non_qualifie"] == 1
    assert sum(r["bornes_par_statut"].values()) == r["n_bornes"] == 12


def test_rapport_interet_nt(mini):
    s, p = mini
    s[1]["interet"] = "NT : financement non lu"
    s[2]["interet"] = "Non trouvé"
    s[0]["interet"] = "Organisme public ; intérêt qualifié"
    r = S.qualification_report(s, p)
    assert r["n_interet_nt"] == 2 and r["n_interet_a_qualifier"] == 0
    assert r["sources_interet_nt"] == sorted([s[1]["id"], s[2]["id"]])
    assert not S.a_inconnue("Intérêt documenté (ENT)") and S.a_inconnue("financement NT")


# --- vraies données ---

PLAN_SOURCE_IDS = [
    "iea_energy_ai_2025", "iea4e_2025", "nature_2026", "morrison_2025", "uptime", "epoch",
    "bloom", "cso_irlande", "ember_2025", "arxiv_2606_21760", "ren_2023", "google_2025",
    "kaplan_2020", "hoffmann_2022",
]  # fmt: skip
PLAN_PARAMS = [
    "E_DC0", "s_AI", "s_train", "PUE_2024", "g_conv", "g_Ctrain_2025", "g_Ctrain_2035",
    "g_tok_2025", "g_tok_2035", "g_fpt_net", "T_d_parc", "PUE_2035", "g_cap", "CI_ref",
    "d_CI", "WUE_site", "EWIF", "annee_ref_CI",
    "C_train_2024", "N_act", "Tokens_2024", "eff_eff",
    "r_s3",
]  # fmt: skip


def test_vraies_donnees_valides():
    validate()


def test_ids_du_plan_presents():
    ids = set(S.load_sources()["id"])
    assert set(PLAN_SOURCE_IDS) <= ids
    assert set(PLAN_PARAMS) == set(S.load_params()["param"])


def test_dataframes_formes():
    dfp = S.load_params()
    assert len(dfp) == 3 * len(PLAN_PARAMS)
    assert set(dfp["borne"]) == set(S.BORNES)
    assert len(S.load_sources()) >= 19


def test_chemins_independants_du_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert len(S.load_sources()) > 0 and len(S.load_params()) > 0


def test_valeurs_du_plan():
    dfp = S.load_params().set_index(["param", "borne"])
    assert dfp.loc[("E_DC0", "central"), "valeur"] == 415
    assert dfp.loc[("EWIF", "high"), "valeur"] == 3.14
    assert dfp.loc[("annee_ref_CI", "central"), "valeur"] == 2025
    assert dfp.loc[("WUE_site", "low"), "statut"] == "D"
    assert dfp.loc[("T_d_parc", "high"), "statut"] == "D"
    assert dfp.loc[("T_d_parc", "central"), "statut"] == "H"


def test_cibles_iea():
    c = {(x["annee"], x["scenario"]): x["valeur"] for x in S.raw_params()["cibles_iea"]}
    assert c == {
        (2030, "base"): 945,
        (2035, "optimiste"): 700,
        (2035, "normal"): 1200,
        (2035, "pessimiste"): 1700,
    }


def test_circularite_affichee_sur_les_croissances():
    dfp = S.load_params()
    for name in ("g_Ctrain_2025", "g_Ctrain_2035", "g_tok_2025", "g_tok_2035",
                 "g_fpt_net", "T_d_parc", "PUE_2035", "g_conv"):  # fmt: skip
        h = dfp[(dfp["param"] == name) & (dfp["statut"] == "H")]
        assert len(h) > 0
        assert h["justification"].str.contains("ce n'est pas une mesure").all(), name


def test_rapport_reel_non_vide():
    r = S.qualification_report()
    assert r["n_biais"] > 0 and r["n_sens_indetermine"] > 0
    assert sum(r["bornes_par_statut"].values()) == r["n_bornes"]
    assert r["bornes_par_statut"].get("H", 0) > 0
    assert "hoffmann_2022" in r["sources_non_lues"] and "epoch" in r["sources_non_lues"]
    assert r["n_type_acteur_non_qualifie"] == 3
    # intérêts inconnus (NT) comptés séparément de a_qualifier (B1)
    assert r["n_interet_nt"] == len(r["sources_interet_nt"]) > 0
    attendus = {"iea4e_2025", "nature_2026", "morrison_2025", "kaplan_2020",
                "iea_energy_ai_2025", "shift_project_2025"}  # fmt: skip
    assert attendus <= set(
        r["sources_interet_nt"]
    )
    assert "epoch" not in r["sources_interet_nt"] and r["n_interet_nt"] == 16 and "owid_2026" in r["sources_interet_nt"]


def test_copie_non_mutee():
    # validate ne modifie pas ses entrées
    s, p = S.raw_sources(), S.raw_params()
    s0, p0 = copy.deepcopy(s), copy.deepcopy(p)
    validate(s, p)
    assert s == s0 and p == p0


# --- section monte_carlo (L-08) ---
MC_OK = {
    "n_tirages": 100,
    "graine": 1,
    "loi": "triangulaire",
    "quantiles": [0.1, 0.5, 0.9],
    "pas_elasticite": 0.1,
}


def test_mini_sans_monte_carlo_valide(mini):
    assert "monte_carlo" not in mini[1]
    validate(*mini)


def test_monte_carlo_valide_accepte(mini):
    s, p = mini
    p["monte_carlo"] = dict(MC_OK)
    validate(s, p)


def test_monte_carlo_present_dans_vraies_donnees():
    mc = S.raw_params().get("monte_carlo")
    assert isinstance(mc, dict) and set(MC_OK) <= set(mc)


@pytest.mark.parametrize(
    "cle,val,motif",
    [
        ("n_tirages", 0, "n_tirages"),
        ("n_tirages", -5, "n_tirages"),
        ("n_tirages", 10.5, "n_tirages"),
        ("n_tirages", True, "n_tirages"),
        ("graine", 1.5, "graine"),
        ("graine", "abc", "graine"),
        ("loi", "normale", "loi"),
        ("pas_elasticite", 0, "pas_elasticite"),
        ("pas_elasticite", 1, "pas_elasticite"),
        ("pas_elasticite", 1.5, "pas_elasticite"),
        ("quantiles", [0.0, 0.5], "quantiles"),
        ("quantiles", [0.5, 1.0], "quantiles"),
        ("quantiles", [0.5, 0.5], "strictement croissants"),
        ("quantiles", [0.9, 0.1], "strictement croissants"),
        ("quantiles", [], "quantiles"),
    ],
)
def test_monte_carlo_invalide(mini, cle, val, motif):
    s, p = mini
    p["monte_carlo"] = {**MC_OK, cle: val}
    expect(s, p, motif)


def test_monte_carlo_cle_manquante(mini):
    s, p = mini
    p["monte_carlo"] = {k: v for k, v in MC_OK.items() if k != "graine"}
    expect(s, p, "clé manquante 'graine'")


# --- sections observations et backtest (L20261016-01) ---
NIVEAU_OK = {"serie": "iea_monde", "annee": 2024, "valeur": 415, "unite": "TWh", "statut": "V",
             "source_ids": ["src_a"], "edition": "Ed 2025"}
TAUX_OK = {"serie": "iea_monde", "debut": 2019, "fin": 2024, "valeur": 0.12, "statut": "V",
           "source_ids": ["src_a"], "edition": "Ed 2025"}
BT_OK = {
    "cso_fichier": "data/raw/x.csv",
    "cso_date_telechargement": dt.date(2026, 10, 16),
    "cso_sha256": "a" * 64,
    "cso_edition": "édition 2025",
    "origine_debut": "2020Q1",
    "horizons": [4, 8],
    "fenetre": 12,
    "fenetre_ci": 5,
    "annee_test": 2025,
    "annees_premieres": 3,
}


def _obs(niveau=None, taux=None):
    return {"niveaux": [{**NIVEAU_OK, **(niveau or {})}], "taux": [{**TAUX_OK, **(taux or {})}]}


def test_mini_sans_observations_ni_backtest_valide(mini):
    assert "observations" not in mini[1] and "backtest" not in mini[1]
    validate(*mini)


def test_observations_et_backtest_valides_acceptes(mini):
    s, p = mini
    p["observations"], p["backtest"] = _obs(), dict(BT_OK)
    validate(s, p)


def test_observations_et_backtest_presents_dans_vraies_donnees():
    p = S.raw_params()
    assert {"niveaux", "taux"} <= set(p["observations"])
    assert set(BT_OK) <= set(p["backtest"])


@pytest.mark.parametrize(
    "cle,modif,motif",
    [
        ("niveaux", {"statut": "X"}, "statut inconnu"),
        ("niveaux", {"statut": "H"}, "statut inconnu"),
        ("niveaux", {"source_ids": ["fantome"]}, "absente du registre"),
        ("niveaux", {"source_ids": []}, "source_ids manquant"),
        ("niveaux", {"statut": "V", "source_ids": ["src_b"]}, "n'est pas lu_source"),
        ("niveaux", {"edition": None}, "edition obligatoire"),
        ("niveaux", {"edition": " "}, "edition obligatoire"),
        ("niveaux", {"annee": 2024.5}, "annee doit être un entier"),
        ("niveaux", {"annee": "2024"}, "annee doit être un entier"),
        ("niveaux", {"annee": 9999}, "postérieure"),
        ("niveaux", {"valeur": "x"}, "valeur numérique"),
        ("niveaux", {"unite": ""}, "unité manquante"),
        ("niveaux", {"statut": "D"}, "sans justification"),
        ("taux", {"statut": "X"}, "statut inconnu"),
        ("taux", {"source_ids": ["fantome"]}, "absente du registre"),
        ("taux", {"statut": "V", "source_ids": ["src_b"]}, "n'est pas lu_source"),
        ("taux", {"edition": None}, "edition obligatoire"),
        ("taux", {"debut": 2019.5}, "debut doit être un entier"),
        ("taux", {"fin": 9999}, "postérieure"),
        ("taux", {"debut": 2024, "fin": 2019}, "debut doit précéder fin"),
        ("taux", {"valeur": -1}, "taux dans"),
        ("taux", {"valeur": 10}, "taux dans"),
        ("taux", {"valeur": 25}, "taux dans"),
        ("taux", {"valeur": None}, "taux dans"),
    ],
)
def test_observations_invalides(mini, cle, modif, motif):
    s, p = mini
    p["observations"] = _obs(**{"niveau" if cle == "niveaux" else "taux": modif})
    expect(s, p, motif)


def test_observation_non_iea_sans_edition_acceptee(mini):
    s, p = mini
    p["observations"] = _obs(niveau={"serie": "lbnl_us", "edition": None})
    validate(s, p)


def test_observations_sections_manquantes(mini):
    s, p = mini
    p["observations"] = {"niveaux": [dict(NIVEAU_OK)]}
    expect(s, p, "liste non vide requise 'taux'")


@pytest.mark.parametrize("obs", [{"taux": [dict(TAUX_OK)]}, {"niveaux": [], "taux": [dict(TAUX_OK)]}])
def test_observations_niveaux_absent_ou_vide(mini, obs):
    s, p = mini
    p["observations"] = obs
    expect(s, p, "liste non vide requise 'niveaux'")


@pytest.mark.parametrize("cle", ["niveaux", "taux"])
def test_observation_non_dictionnaire(mini, cle):
    s, p = mini
    p["observations"] = {**_obs(), cle: ["pas un dict"]}
    expect(s, p, rf"observations.{cle}\[0\]: doit être un dictionnaire")


@pytest.mark.parametrize(
    "cle,val,motif",
    [
        ("cso_fichier", "", "cso_fichier"),
        ("cso_edition", None, "cso_edition"),
        ("cso_date_telechargement", "pas une date", "date illisible"),
        ("cso_date_telechargement", dt.date(2999, 1, 1), "date future"),
        ("cso_sha256", "abc", "cso_sha256"),
        ("cso_sha256", "A" * 64, "cso_sha256"),
        ("origine_debut", "2020", "AAAAQn"),
        ("origine_debut", "2020Q5", "AAAAQn"),
        ("origine_debut", 20201, "AAAAQn"),
        ("horizons", [], "horizons"),
        ("horizons", [4, 0], "horizons"),
        ("horizons", [4.5], "horizons"),
        ("horizons", 4, "horizons"),
        ("fenetre", 2, "fenetre"),
        ("fenetre", 12.0, "fenetre"),
        ("fenetre", True, "fenetre"),
        ("fenetre_ci", 2, "fenetre_ci"),
        ("fenetre_ci", "5", "fenetre_ci"),
        ("annee_test", 2024, "annee_test"),
        ("annee_test", 2036, "annee_test"),
        ("annee_test", 2025.5, "annee_test"),
        ("annees_premieres", 0, "annees_premieres"),
        ("annees_premieres", 12, "annees_premieres"),
        ("annees_premieres", 3.5, "annees_premieres"),
    ],
)
def test_backtest_invalide(mini, cle, val, motif):
    s, p = mini
    p["backtest"] = {**BT_OK, cle: val}
    expect(s, p, motif)


def test_backtest_cle_manquante(mini):
    s, p = mini
    p["backtest"] = {k: v for k, v in BT_OK.items() if k != "cso_sha256"}
    expect(s, p, "clé manquante 'cso_sha256'")


def test_backtest_bornes_limites_acceptees(mini):
    s, p = mini
    for cle, val in (("annee_test", 2035), ("annees_premieres", 11), ("annees_premieres", 1),
                     ("fenetre", 3), ("fenetre_ci", 3)):  # fmt: skip
        p["backtest"] = {**BT_OK, cle: val}
        validate(s, p)


def test_vrai_vintage_cso_sha256():
    bt = S.raw_params()["backtest"]
    octets = (S.ROOT / bt["cso_fichier"]).read_bytes()
    assert hashlib.sha256(octets).hexdigest() == bt["cso_sha256"]


def test_nouvelles_sources_dans_le_registre_reel():
    ids = set(S.load_sources()["id"])
    assert {"iea_key_questions_2026", "owid_2026", "cso_irlande"} <= ids
    obs = S.raw_params()["observations"]
    cites = {i for o in obs["niveaux"] + obs["taux"] for i in o["source_ids"]}
    assert {"iea_key_questions_2026", "owid_2026"} <= cites


def test_observations_reelles_statuts_et_editions():
    obs = S.raw_params()["observations"]
    iea = [o for o in obs["niveaux"] + obs["taux"] if o["serie"] == "iea_monde"]
    assert iea and all(str(o["edition"]).strip() for o in iea)
    ci = [o["annee"] for o in obs["niveaux"] if o["serie"] == "ember_ci_monde"]
    assert sorted(ci) == list(range(ci[0], ci[0] + 11))


def test_rapport_compte_les_nouvelles_sources():
    r = S.qualification_report()
    assert r["n_sources"] >= 21
    assert "owid_2026" in r["sources_non_lues"] and "iea_key_questions_2026" not in r["sources_non_lues"]
    assert "cso_irlande" in r["sources_interet_nt"]  # NT conservé (financement)
    assert r["n_biais"] >= sum(len(s["biais"]) for s in S.raw_sources() if s["id"] in (
        "iea_key_questions_2026", "owid_2026"))  # fmt: skip
