"""Tableaux de lecture du registre et des paramètres pour le notebook."""

from __future__ import annotations

import pandas as pd

from energywall import sources as S

MARQUE_NT = "[NT]"
BLOQUEES = ("pdf_illisible", "paywall", "non_trouve")


def registre() -> pd.DataFrame:
    """Une ligne par source : origine, lecture, méthode, intérêt (conflit d'intérêts potentiel)."""
    cols = ["id", "organisation", "type_acteur", "statut_lecture", "methode", "periode_donnees",
            "perimetre", "interet"]
    return S.load_sources()[cols].set_index("id")


def acteur_x_lecture() -> pd.DataFrame:
    df = S.load_sources()
    return pd.crosstab(df["type_acteur"], df["statut_lecture"], margins=True, margins_name="total")


def biais_long() -> pd.DataFrame:
    """Une ligne par biais déclaré (source, sens, grandeur, description)."""
    rows = [
        {"source": s["id"], **{k: b.get(k) for k in ("sens", "grandeur", "description")}}
        for s in S.raw_sources()
        for b in s.get("biais") or []
    ]
    return pd.DataFrame(rows)


def biais_par_sens() -> pd.Series:
    return biais_long()["sens"].value_counts()


def biais_sens_x_grandeur() -> pd.DataFrame:
    b = biais_long()
    return pd.crosstab(b["grandeur"], b["sens"], margins=True, margins_name="total")


def sources_bloquees() -> pd.DataFrame:
    df = S.load_sources()
    return df[df["statut_lecture"].isin(BLOQUEES)][["id", "organisation", "statut_lecture"]]


def relations_nt() -> pd.DataFrame:
    """Biais ou valeurs marqués [NT] (non revérifiés)."""
    b = biais_long()
    return b[b["description"].astype(str).str.contains(MARQUE_NT, regex=False)]


def params_nt() -> list[str]:
    """Paramètres dont une justification de borne cite une relation [NT]."""
    df = S.load_params()
    return sorted(df[df["justification"].str.contains(MARQUE_NT, regex=False)]["param"].unique())


def bornes_par_statut() -> pd.DataFrame:
    """Décompte des bornes par statut, avec part (%)."""
    n = S.load_params()["statut"].value_counts().reindex(S.STATUTS, fill_value=0)
    return pd.DataFrame({"n": n, "part_%": 100 * n / n.sum()})


def params_tout_h() -> list[str]:
    df = S.load_params()
    return sorted(p for p, g in df.groupby("param") if (g["statut"] == "H").all())


def part_h(params: list[str]) -> pd.Series:
    """Part (%) des bornes par statut, restreinte aux paramètres donnés."""
    df = S.load_params()
    if not params:
        raise ValueError("part_h : liste de paramètres vide")
    inconnus = sorted(set(params) - set(df["param"]))
    if inconnus:
        raise ValueError(f"part_h : paramètres inconnus {inconnus}")
    n = df[df["param"].isin(params)]["statut"].value_counts().reindex(S.STATUTS, fill_value=0)
    return (100 * n / n.sum()).rename("part_%")


def tracabilite() -> pd.DataFrame:
    """Une ligne par paramètre x borne : valeur, statut, sources, justification."""
    df = S.load_params()
    df["source_ids"] = df["source_ids"].map(", ".join)
    df["valeur"] = df["valeur"].map(lambda v: format(v, ".6g"))  # lisible de 1e-2 à 1e26
    return df[["param", "borne", "unite", "valeur", "statut", "source_ids",
               "justification"]].set_index(
        ["param", "borne"]
    )
