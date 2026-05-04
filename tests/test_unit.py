"""
Tests unitaires pour les fonctions pures de 02_clean_transform.py.
"""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def _charger_module():
    path = Path(__file__).parent.parent / "scripts" / "02_clean_transform.py"
    spec = importlib.util.spec_from_file_location("clean_transform", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def ct():
    return _charger_module()


# ---------------------------------------------------------------------------
# _normalize_name
# ---------------------------------------------------------------------------

def test_normalize_name_supprime_accents(ct):
    assert ct._normalize_name("Mélenchon") == "MELENCHON"
    assert ct._normalize_name("Éric") == "ERIC"
    assert ct._normalize_name("Châteauneuf") == "CHATEAUNEUF"
    assert ct._normalize_name("Ségolène") == "SEGOLENE"


def test_normalize_name_upper_et_strip(ct):
    assert ct._normalize_name("  dupont  ") == "DUPONT"
    assert ct._normalize_name("jean-marie") == "JEAN-MARIE"


def test_normalize_name_conserve_tirets_et_espaces(ct):
    assert ct._normalize_name("Le Pen") == "LE PEN"
    assert ct._normalize_name("Saint-Josse") == "SAINT-JOSSE"
    assert ct._normalize_name("Dupont-Aignan") == "DUPONT-AIGNAN"


# ---------------------------------------------------------------------------
# CANDIDAT_FAMILLE
# ---------------------------------------------------------------------------

def test_candidat_famille_sept_familles(ct):
    familles = set(ct.CANDIDAT_FAMILLE.values())
    assert familles == {
        "gauche_radicale",
        "social_democratie",
        "ecologisme",
        "liberalisme_centre",
        "droite_conservatrice",
        "souverainisme",
        "droite_nationale",
    }


def test_candidat_famille_candidats_connus(ct):
    assert ct.CANDIDAT_FAMILLE[("MELENCHON", "JEAN-LUC")] == "gauche_radicale"
    assert ct.CANDIDAT_FAMILLE[("MACRON", "EMMANUEL")] == "liberalisme_centre"
    assert ct.CANDIDAT_FAMILLE[("LE PEN", "MARINE")] == "droite_nationale"
    assert ct.CANDIDAT_FAMILLE[("JADOT", "YANNICK")] == "ecologisme"
    assert ct.CANDIDAT_FAMILLE[("ZEMMOUR", "ERIC")] == "droite_nationale"
    assert ct.CANDIDAT_FAMILLE[("DUPONT-AIGNAN", "NICOLAS")] == "souverainisme"


def test_candidat_famille_mapping_via_normalize(ct):
    # Vérifier que _normalize_name + lookup fonctionne pour des noms accentués
    nom = ct._normalize_name("Mélenchon")
    prenom = ct._normalize_name("Jean-Luc")
    assert ct.CANDIDAT_FAMILLE[(nom, prenom)] == "gauche_radicale"


# ---------------------------------------------------------------------------
# build_cog_mapping
# ---------------------------------------------------------------------------

def test_cog_mapping_resout_chaine(ct):
    """A->B->C doit être résolu en A->C et B->C."""
    mvt = pd.DataFrame({
        "MOD": [31, 31],
        "DATE_EFF": ["2017-01-01", "2018-01-01"],
        "TYPECOM_AV": ["COM", "COM"],
        "TYPECOM_AP": ["COM", "COM"],
        "COM_AV": ["11001", "11002"],
        "COM_AP": ["11002", "11003"],
    })
    mapping = ct.build_cog_mapping(mvt)
    assert mapping["11001"] == "11003"
    assert mapping["11002"] == "11003"


def test_cog_mapping_exclut_avant_2016(ct):
    mvt = pd.DataFrame({
        "MOD": [31],
        "DATE_EFF": ["2015-12-31"],
        "TYPECOM_AV": ["COM"],
        "TYPECOM_AP": ["COM"],
        "COM_AV": ["11001"],
        "COM_AP": ["11002"],
    })
    mapping = ct.build_cog_mapping(mvt)
    assert "11001" not in mapping


def test_cog_mapping_exclut_mod_non_fusion(ct):
    mvt = pd.DataFrame({
        "MOD": [10],
        "DATE_EFF": ["2017-01-01"],
        "TYPECOM_AV": ["COM"],
        "TYPECOM_AP": ["COM"],
        "COM_AV": ["11001"],
        "COM_AP": ["11002"],
    })
    mapping = ct.build_cog_mapping(mvt)
    assert len(mapping) == 0


def test_cog_mapping_fusion_simple(ct):
    mvt = pd.DataFrame({
        "MOD": [31],
        "DATE_EFF": ["2020-01-01"],
        "TYPECOM_AV": ["COM"],
        "TYPECOM_AP": ["COM"],
        "COM_AV": ["01001"],
        "COM_AP": ["01002"],
    })
    mapping = ct.build_cog_mapping(mvt)
    assert mapping["01001"] == "01002"
    assert "01002" not in mapping


# ---------------------------------------------------------------------------
# harmonize_codgeo
# ---------------------------------------------------------------------------

def test_harmonize_exclut_zz(ct):
    df = pd.DataFrame({"CODGEO": ["01001", "ZZ999", "75001"]})
    result = ct.harmonize_codgeo(df, "CODGEO", {})
    assert "ZZ999" not in result["CODGEO"].values
    assert len(result) == 2


def test_harmonize_exclut_outre_mer(ct):
    df = pd.DataFrame({"CODGEO": ["01001", "97100", "75001"]})
    result = ct.harmonize_codgeo(df, "CODGEO", {})
    assert "97100" not in result["CODGEO"].values
    assert len(result) == 2


def test_harmonize_applique_remapping(ct):
    df = pd.DataFrame({"CODGEO": ["11001", "75001"]})
    result = ct.harmonize_codgeo(df, "CODGEO", {"11001": "11999"})
    assert "11999" in result["CODGEO"].values
    assert "11001" not in result["CODGEO"].values


def test_harmonize_conserve_lignes_normales(ct):
    df = pd.DataFrame({"CODGEO": ["01001", "75056", "13055"], "val": [1, 2, 3]})
    result = ct.harmonize_codgeo(df, "CODGEO", {})
    assert len(result) == 3


# ---------------------------------------------------------------------------
# clean_revenue_cols
# ---------------------------------------------------------------------------

def test_clean_revenue_secret_stat_en_nan(ct):
    df = pd.DataFrame({"CODGEO": ["01001"], "MED21": ["s"], "D121": ["18500"]})
    result = ct.clean_revenue_cols(df)
    assert pd.isna(result["MED21"].iloc[0])
    assert result["D121"].iloc[0] == pytest.approx(18500.0)


def test_clean_revenue_virgule_decimale(ct):
    df = pd.DataFrame({"CODGEO": ["01001"], "MED21": ["21500,50"]})
    result = ct.clean_revenue_cols(df)
    assert result["MED21"].iloc[0] == pytest.approx(21500.50, rel=1e-3)


def test_clean_revenue_codgeo_non_touche(ct):
    df = pd.DataFrame({"CODGEO": ["01001"], "MED21": ["20000"]})
    result = ct.clean_revenue_cols(df)
    # CODGEO ne doit pas être casté en float
    assert result["CODGEO"].iloc[0] == "01001"
