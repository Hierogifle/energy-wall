"""Registre des sources, paramètres tracés par borne et validation."""

from __future__ import annotations

import datetime as dt
import itertools
import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
SOURCES_PATH = ROOT / "data" / "sources.yaml"
PARAMS_PATH = ROOT / "data" / "params.yaml"

BORNES = ("low", "central", "high")
STATUTS = ("V", "S", "D", "H")
TYPES_ACTEUR = (
    "agence_publique",
    "gestionnaire_reseau",
    "statistique_publique",
    "entreprise_tech",
    "academique_revu",
    "preprint",
    "think_tank_ong",
    "presse",
    "agregateur",
)
STATUTS_LECTURE = ("lu_source", "relais", "pdf_illisible", "paywall", "non_trouve")
METHODES = ("mesure", "declaratif", "modelisation", "estimation_secondaire")
SENS = ("sous-estimation", "surestimation", "indetermine")
CHAMPS_SOURCE = (
    "id",
    "titre",
    "organisation",
    "type_acteur",
    "type_acteur_qualifie",
    "url",
    "url_relais",
    "statut_lecture",
    "date_publication",
    "date_consultation",
    "version",
    "periode_donnees",
    "licence",
    "perimetre",
    "methode",
    "interet",
    "biais",
    "utilise_pour",
)
# Champs dont la valeur peut être null (clé obligatoire, valeur facultative).
CHAMPS_NULLABLES = ("url_relais", "version")
LOIS_MC = ("triangulaire", "uniforme")
STATUTS_OBS = ("V", "S", "D")
# Bornes structurelles de la config backtest.
FENETRE_MIN = 3
ANNEE_TEST_MIN, ANNEE_TEST_MAX = 2025, 2035
ANNEES_PREMIERES_MIN, ANNEES_PREMIERES_MAX = 1, 11
TAUX_MIN, TAUX_MAX = -1, 10  # taux annuel, intervalle ouvert
_TRIMESTRE_RE = re.compile(r"\d{4}Q[1-4]")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
A_QUALIFIER = "a_qualifier"
# Inconnue déclarée : mot « NT » isolé ou « non trouvé » dans un texte (insensible à la casse).
_NT_RE = re.compile(r"(?<![A-Za-z])NT(?![A-Za-z])|non trouv", re.IGNORECASE)


def a_inconnue(texte: Any) -> bool:
    return bool(_NT_RE.search(str(texte or "")))


class ValidationError(Exception):
    """Une ou plusieurs règles de validation violées (message = liste complète)."""


def _read_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def raw_sources() -> list[dict]:
    return _read_yaml(SOURCES_PATH)["sources"]


def raw_params() -> dict:
    return _read_yaml(PARAMS_PATH)


def load_sources(raw: list[dict] | None = None) -> pd.DataFrame:
    raw = raw_sources() if raw is None else raw
    return pd.DataFrame(raw)


def load_params(raw: dict | None = None) -> pd.DataFrame:
    """Une ligne par paramètre x borne."""
    raw = raw_params() if raw is None else raw
    rows = []
    for name, p in raw["params"].items():
        for borne in BORNES:
            b = p.get(borne) or {}
            rows.append(
                {
                    "param": name,
                    "borne": borne,
                    "unite": p.get("unite"),
                    "description": p.get("description"),
                    "valeur": b.get("valeur"),
                    "statut": b.get("statut"),
                    "source_ids": list(b.get("source_ids") or []),
                    "justification": b.get("justification") or "",
                }
            )
    return pd.DataFrame(rows)


def _as_date(v: Any) -> dt.date | None:
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    if isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        try:
            return dt.date.fromisoformat(v)
        except ValueError:
            return None
    return None


def _vide(v: Any) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


def _check_sources(sources: list[dict], err: list[str]) -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    today = dt.date.today()
    for i, s in enumerate(sources):
        sid = s.get("id", f"#{i}")
        for champ in CHAMPS_SOURCE:
            if champ not in s:
                err.append(f"source {sid}: champ obligatoire manquant '{champ}'")
            elif champ not in CHAMPS_NULLABLES and (
                s[champ] is None or (isinstance(s[champ], str) and not s[champ].strip())
            ):
                err.append(f"source {sid}: champ obligatoire vide '{champ}'")
        if "type_acteur_qualifie" in s and not isinstance(s["type_acteur_qualifie"], bool):
            err.append(f"source {sid}: type_acteur_qualifie doit être un booléen")
        if "id" in s:
            if s["id"] in by_id:
                err.append(f"source {sid}: id en double")
            by_id[s["id"]] = s
        for champ, enum in (
            ("type_acteur", TYPES_ACTEUR),
            ("statut_lecture", STATUTS_LECTURE),
            ("methode", METHODES),
        ):
            if s.get(champ) is not None and s[champ] not in enum:
                err.append(f"source {sid}: {champ} inconnu '{s[champ]}' (attendu : {enum})")
        biais = s.get("biais")
        if "biais" in s:
            if not isinstance(biais, list) or not biais:
                err.append(f"source {sid}: biais vide (liste non vide requise)")
            else:
                for j, b in enumerate(biais):
                    if not isinstance(b, dict):
                        err.append(f"source {sid}: biais[{j}] n'est pas un dictionnaire")
                        continue
                    for champ in ("description", "sens", "grandeur"):
                        if _vide(b.get(champ)):
                            err.append(f"source {sid}: biais[{j}] sans '{champ}'")
                    if b.get("sens") not in (None, *SENS):
                        err.append(f"source {sid}: biais[{j}] sens inconnu '{b['sens']}'")
        if "date_consultation" in s and s["date_consultation"] is not None:
            d = _as_date(s["date_consultation"])
            if d is None:
                err.append(f"source {sid}: date_consultation illisible '{s['date_consultation']}'")
            elif d > today:
                err.append(f"source {sid}: date_consultation future ({d} > {today})")
        dp = s.get("date_publication")
        if "date_publication" in s and _vide(dp):
            err.append(f"source {sid}: date_publication vide (utiliser 'inconnue')")
        if "licence" in s and _vide(s["licence"]):
            err.append(f"source {sid}: licence vide (utiliser 'inconnue')")
    return by_id


def _check_params(raw: dict, by_id: dict[str, dict], err: list[str]) -> dict[str, set[str]]:
    params = raw["params"]
    cites: dict[str, set[str]] = {}  # source_id -> params qui la citent
    for name, p in params.items():
        if _vide(p.get("unite")):
            err.append(f"param {name}: unité manquante")
        if _vide(p.get("description")):
            err.append(f"param {name}: description manquante")
        vals = {}
        for borne in BORNES:
            b = p.get(borne)
            if not isinstance(b, dict):
                err.append(f"param {name}: borne '{borne}' manquante")
                continue
            tag = f"param {name}.{borne}"
            v = b.get("valeur")
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                err.append(f"{tag}: valeur numérique manquante")
            else:
                vals[borne] = v
            st = b.get("statut")
            if st not in STATUTS:
                err.append(f"{tag}: statut inconnu '{st}' (attendu : {STATUTS})")
            ids = b.get("source_ids")
            if not isinstance(ids, list):
                err.append(f"{tag}: source_ids doit être une liste")
                ids = []
            if st in ("H", "D") and _vide(b.get("justification")):
                err.append(f"{tag}: statut {st} sans justification")
            if st in ("V", "S", "D") and not ids:
                err.append(f"{tag}: statut {st} sans source_ids")
            for sid in ids:
                src = by_id.get(sid)
                if src is None:
                    err.append(f"{tag}: source '{sid}' absente du registre")
                    continue
                cites.setdefault(sid, set()).add(name)
                lecture = src.get("statut_lecture")
                if st == "V" and lecture != "lu_source":
                    err.append(f"{tag}: statut V mais la source '{sid}' est '{lecture}' (lu_source requis)")
                if st == "S" and lecture not in ("relais", "lu_source"):
                    err.append(f"{tag}: statut S mais la source '{sid}' est '{lecture}' (relais ou lu_source requis)")
        if len(vals) == 3 and not (vals["low"] <= vals["central"] <= vals["high"]):
            err.append(f"param {name}: ordre low <= central <= high violé ({vals})")
    # Trajectoires décroissantes : g_X_2035 <= g_X_2025, borne par borne.
    for name in params:
        m = re.fullmatch(r"(g_.+)_2035", name)
        if not m or f"{m.group(1)}_2025" not in params:
            continue
        for borne in BORNES:
            try:
                v35 = params[name][borne]["valeur"]
                v25 = params[f"{m.group(1)}_2025"][borne]["valeur"]
            except (KeyError, TypeError):
                continue
            if isinstance(v35, (int, float)) and isinstance(v25, (int, float)) and v35 > v25:
                err.append(f"{name}.{borne}: {v35} > {m.group(1)}_2025.{borne} = {v25} (croissance non décroissante)")
    return cites


def _check_scenarios(raw: dict, err: list[str]) -> None:
    params = raw["params"]
    sc = raw.get("scenarios") or {}
    sens = sc.get("sens") or {}
    for name, jeu in (sc.get("jeux") or {}).items():
        for p, borne in (jeu or {}).items():
            if p not in params:
                err.append(f"scénario {name}: paramètre inconnu '{p}'")
            if borne not in BORNES:
                err.append(f"scénario {name}.{p}: borne inconnue '{borne}'")
            if p not in sens or _vide(sens[p]):
                err.append(f"scénario {name}.{p}: sens non écrit dans scenarios.sens")
    for p in sens:
        if p not in params:
            err.append(f"scenarios.sens: paramètre inconnu '{p}'")


def _check_cibles(raw: dict, by_id: dict[str, dict], err: list[str]) -> None:
    for i, c in enumerate(raw.get("cibles_iea") or []):
        tag = f"cibles_iea[{i}]"
        if c.get("statut") not in STATUTS:
            err.append(f"{tag}: statut inconnu '{c.get('statut')}'")
        if not c.get("source_ids"):
            err.append(f"{tag}: source_ids manquant")
        for sid in c.get("source_ids") or []:
            src = by_id.get(sid)
            if src is None:
                err.append(f"{tag}: source '{sid}' absente du registre")
            elif c.get("statut") == "V" and src.get("statut_lecture") != "lu_source":
                err.append(f"{tag}: statut V mais la source '{sid}' n'est pas lu_source")


def _entier(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _nombre(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _check_monte_carlo(mc: Any, err: list[str]) -> None:
    if not isinstance(mc, dict):
        err.append("monte_carlo: doit être un dictionnaire")
        return
    for cle in ("n_tirages", "graine", "loi", "quantiles", "pas_elasticite"):
        if cle not in mc:
            err.append(f"monte_carlo: clé manquante '{cle}'")
    if "n_tirages" in mc and not (_entier(mc["n_tirages"]) and mc["n_tirages"] > 0):
        err.append(f"monte_carlo.n_tirages: entier > 0 requis ({mc['n_tirages']!r})")
    if "graine" in mc and not _entier(mc["graine"]):
        err.append(f"monte_carlo.graine: entier requis ({mc['graine']!r})")
    if "loi" in mc and mc["loi"] not in LOIS_MC:
        err.append(f"monte_carlo.loi: inconnue '{mc['loi']}' (attendu : {LOIS_MC})")
    if "pas_elasticite" in mc and not (
        _nombre(mc["pas_elasticite"]) and 0 < mc["pas_elasticite"] < 1
    ):
        err.append(f"monte_carlo.pas_elasticite: dans ]0 ; 1[ requis ({mc['pas_elasticite']!r})")
    if "quantiles" in mc:
        q = mc["quantiles"]
        if not (isinstance(q, list) and q and all(_nombre(x) and 0 < x < 1 for x in q)):
            err.append(f"monte_carlo.quantiles: liste non vide de nombres dans ]0 ; 1[ ({q!r})")
        elif any(b <= a for a, b in itertools.pairwise(q)):
            err.append(f"monte_carlo.quantiles: strictement croissants requis ({q})")


def _check_miracle(mi: Any, by_id: dict[str, dict], err: list[str]) -> None:
    if not isinstance(mi, dict):
        err.append("miracle: doit être un dictionnaire")
        return
    br = mi.get("bracket_T_d")
    if not (isinstance(br, list) and len(br) == 2 and all(_nombre(x) and x > 0 for x in br)
            and br[0] < br[1]):
        err.append(f"miracle.bracket_T_d: [bas, haut] strictement croissant et > 0 requis ({br!r})")
    pe = mi.get("pointe_epoch")
    if not isinstance(pe, dict):
        err.append("miracle.pointe_epoch: dictionnaire low/high requis")
        return
    vals = {}
    for borne in ("low", "high"):
        x = pe.get(borne)
        tag = f"miracle.pointe_epoch.{borne}"
        if not isinstance(x, dict):
            err.append(f"{tag}: manquant")
            continue
        if not (_nombre(x.get("valeur")) and x["valeur"] > 0):
            err.append(f"{tag}: valeur > 0 requise ({x.get('valeur')!r})")
        else:
            vals[borne] = x["valeur"]
        if x.get("statut") not in STATUTS:
            err.append(f"{tag}: statut inconnu '{x.get('statut')}' (attendu : {STATUTS})")
        ids = x.get("source_ids")
        if not isinstance(ids, list) or not ids:
            if x.get("statut") != "H":
                err.append(f"{tag}: source_ids manquant")
        else:
            err.extend(f"{tag}: source '{i}' absente du registre" for i in ids if i not in by_id)
        if x.get("statut") in ("H", "D") and _vide(x.get("justification")):
            err.append(f"{tag}: statut {x['statut']} sans justification")
    if len(vals) == 2 and vals["low"] >= vals["high"]:
        err.append(f"miracle.pointe_epoch: low < high requis ({vals})")


def _check_refs_obs(tag: str, o: dict, by_id: dict[str, dict], err: list[str]) -> None:
    """Statut, sources, édition (séries IEA) et année d'une observation (niveau ou taux)."""
    st = o.get("statut")
    if st not in STATUTS_OBS:
        err.append(f"{tag}: statut inconnu '{st}' (attendu : {STATUTS_OBS})")
    ids = o.get("source_ids")
    if not isinstance(ids, list) or not ids:
        err.append(f"{tag}: source_ids manquant")
        ids = []
    for sid in ids:
        src = by_id.get(sid)
        if src is None:
            err.append(f"{tag}: source '{sid}' absente du registre")
        elif st == "V" and src.get("statut_lecture") != "lu_source":
            err.append(f"{tag}: statut V mais la source '{sid}' n'est pas lu_source")
    if st == "D" and _vide(o.get("justification")):
        err.append(f"{tag}: statut D sans justification")
    if str(o.get("serie", "")).startswith("iea") and _vide(o.get("edition")):
        err.append(f"{tag}: edition obligatoire pour une série IEA")
    if _vide(o.get("serie")):
        err.append(f"{tag}: serie manquante")


def _check_annee(tag: str, champ: str, v: Any, err: list[str]) -> None:
    if not _entier(v):
        err.append(f"{tag}: {champ} doit être un entier ({v!r})")
    elif v > dt.date.today().year:
        err.append(f"{tag}: {champ} {v} postérieure à l'année de consultation")


def _check_observations(obs: Any, by_id: dict[str, dict], err: list[str]) -> None:
    if not isinstance(obs, dict):
        err.append("observations: doit être un dictionnaire")
        return
    for cle in ("niveaux", "taux"):
        if not isinstance(obs.get(cle), list) or not obs.get(cle):
            err.append(f"observations: liste non vide requise '{cle}'")
    for i, o in enumerate(obs.get("niveaux") or []):
        tag = f"observations.niveaux[{i}]"
        if not isinstance(o, dict):
            err.append(f"{tag}: doit être un dictionnaire")
            continue
        _check_refs_obs(tag, o, by_id, err)
        _check_annee(tag, "annee", o.get("annee"), err)
        if not _nombre(o.get("valeur")):
            err.append(f"{tag}: valeur numérique requise ({o.get('valeur')!r})")
        if _vide(o.get("unite")):
            err.append(f"{tag}: unité manquante")
    for i, o in enumerate(obs.get("taux") or []):
        tag = f"observations.taux[{i}]"
        if not isinstance(o, dict):
            err.append(f"{tag}: doit être un dictionnaire")
            continue
        _check_refs_obs(tag, o, by_id, err)
        _check_annee(tag, "debut", o.get("debut"), err)
        _check_annee(tag, "fin", o.get("fin"), err)
        if _entier(o.get("debut")) and _entier(o.get("fin")) and o["debut"] >= o["fin"]:
            err.append(f"{tag}: debut doit précéder fin ({o['debut']} >= {o['fin']})")
        v = o.get("valeur")
        if not (_nombre(v) and TAUX_MIN < v < TAUX_MAX):
            err.append(f"{tag}: taux dans ]{TAUX_MIN} ; {TAUX_MAX}[ requis ({v!r})")


def _check_backtest(bt: Any, err: list[str]) -> None:
    if not isinstance(bt, dict):
        err.append("backtest: doit être un dictionnaire")
        return
    for cle in (
        "cso_fichier", "cso_date_telechargement", "cso_sha256", "cso_edition", "origine_debut",
        "horizons", "fenetre", "fenetre_ci", "annee_test", "annees_premieres",
    ):  # fmt: skip
        if cle not in bt:
            err.append(f"backtest: clé manquante '{cle}'")
    for cle in ("cso_fichier", "cso_edition"):
        if cle in bt and (not isinstance(bt[cle], str) or _vide(bt[cle])):
            err.append(f"backtest.{cle}: texte non vide requis ({bt[cle]!r})")
    if "cso_date_telechargement" in bt:
        d = _as_date(bt["cso_date_telechargement"])
        if d is None:
            err.append(f"backtest.cso_date_telechargement: date illisible ({bt['cso_date_telechargement']!r})")
        elif d > dt.date.today():
            err.append(f"backtest.cso_date_telechargement: date future ({d})")
    if "cso_sha256" in bt and not (
        isinstance(bt["cso_sha256"], str) and _SHA256_RE.fullmatch(bt["cso_sha256"])
    ):
        err.append(f"backtest.cso_sha256: 64 caractères hexadécimaux minuscules requis ({bt['cso_sha256']!r})")
    if "origine_debut" in bt and not (
        isinstance(bt["origine_debut"], str) and _TRIMESTRE_RE.fullmatch(bt["origine_debut"])
    ):
        err.append(f"backtest.origine_debut: format AAAAQn requis ({bt['origine_debut']!r})")
    if "horizons" in bt:
        h = bt["horizons"]
        if not (isinstance(h, list) and h and all(_entier(x) and x > 0 for x in h)):
            err.append(f"backtest.horizons: liste non vide d'entiers > 0 requise ({h!r})")
    for cle in ("fenetre", "fenetre_ci"):
        if cle in bt and not (_entier(bt[cle]) and bt[cle] >= FENETRE_MIN):
            err.append(f"backtest.{cle}: entier >= {FENETRE_MIN} requis ({bt[cle]!r})")
    for cle, lo, hi in (
        ("annee_test", ANNEE_TEST_MIN, ANNEE_TEST_MAX),
        ("annees_premieres", ANNEES_PREMIERES_MIN, ANNEES_PREMIERES_MAX),
    ):
        if cle in bt and not (_entier(bt[cle]) and lo <= bt[cle] <= hi):
            err.append(f"backtest.{cle}: entier dans [{lo} ; {hi}] requis ({bt[cle]!r})")


def validate(sources: list[dict] | None = None, params: dict | None = None) -> None:
    """Lève ValidationError (liste complète des violations) ; sinon None."""
    sources = raw_sources() if sources is None else sources
    params = raw_params() if params is None else params
    err: list[str] = []
    by_id = _check_sources(sources, err)
    cites = _check_params(params, by_id, err)
    _check_scenarios(params, err)
    _check_cibles(params, by_id, err)
    if "monte_carlo" in params:
        _check_monte_carlo(params["monte_carlo"], err)
    if "miracle" in params:
        _check_miracle(params["miracle"], by_id, err)
    if "observations" in params:
        _check_observations(params["observations"], by_id, err)
    if "backtest" in params:
        _check_backtest(params["backtest"], err)
    # Réciprocité utilise_pour <-> source_ids des bornes.
    noms = set(params["params"])
    for sid, s in by_id.items():
        decl = set(s.get("utilise_pour") or [])
        for p in sorted(decl - noms):
            err.append(f"source {sid}: utilise_pour cite le paramètre inconnu '{p}'")
        for p in sorted((decl & noms) - cites.get(sid, set())):
            err.append(f"source {sid}: utilise_pour '{p}' mais aucune borne de {p} ne la cite")
        for p in sorted(cites.get(sid, set()) - decl):
            err.append(f"source {sid}: citée par {p} mais absente de utilise_pour")
    if err:
        raise ValidationError(f"{len(err)} violation(s) :\n- " + "\n- ".join(err))


def qualification_report(sources: list[dict] | None = None, params: dict | None = None) -> dict:
    """Décompte des zones non qualifiées et des bornes par statut."""
    sources = raw_sources() if sources is None else sources
    dfp = load_params(params)
    biais = [(s["id"], b) for s in sources for b in s.get("biais") or []]
    interets_nt = sorted(s["id"] for s in sources if a_inconnue(s.get("interet")))
    return {
        "n_sources": len(sources),
        "n_biais": len(biais),
        "n_biais_a_qualifier": sum(isinstance(b, dict) and b.get("description") == A_QUALIFIER for _, b in biais),
        "n_sens_indetermine": sum(b.get("sens") == "indetermine" for _, b in biais),
        "n_interet_a_qualifier": sum(
            str(s.get("interet", "")).startswith(A_QUALIFIER) for s in sources
        ),
        "n_interet_nt": len(interets_nt),
        "sources_interet_nt": interets_nt,
        "n_biais_nt": sum(a_inconnue(b.get("description")) for _, b in biais if isinstance(b, dict)),
        "n_type_acteur_non_qualifie": sum(s.get("type_acteur_qualifie") is False for s in sources),
        "sources_sens_indetermine": sorted(
            {sid for sid, b in biais if b.get("sens") == "indetermine"}
        ),
        "sources_non_lues": sorted(
            s["id"] for s in sources if s.get("statut_lecture") != "lu_source"
        ),
        "n_bornes": len(dfp),
        "bornes_par_statut": dfp["statut"].value_counts().to_dict(),
    }
