"""
Smoke tests : vérifient que le pipeline ne plante pas sur des données synthétiques.
Aucune donnée réelle n'est requise.
"""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def _charger_module(filename: str, name: str):
    path = Path(__file__).parent.parent / "scripts" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Helpers : génération de données synthétiques
# ---------------------------------------------------------------------------

N_COMMUNES = 60
ANNEES = ["2017", "2022"]

CANDIDATS_PAR_AN = {
    "2017": [
        ("MELENCHON", "JEAN-LUC", 800),
        ("HAMON", "BENOIT", 200),
        ("MACRON", "EMMANUEL", 1000),
        ("FILLON", "FRANCOIS", 700),
        ("LE PEN", "MARINE", 900),
        ("DUPONT-AIGNAN", "NICOLAS", 150),
    ],
    "2022": [
        ("MELENCHON", "JEAN-LUC", 900),
        ("HIDALGO", "ANNE", 100),
        ("MACRON", "EMMANUEL", 950),
        ("PECRESSE", "VALERIE", 600),
        ("LE PEN", "MARINE", 950),
        ("ZEMMOUR", "ERIC", 350),
    ],
}


def _make_general(n: int) -> pd.DataFrame:
    rows = []
    for an in ANNEES:
        for i in range(n):
            rows.append({
                "id_election": f"{an}-PP-01",
                "code_commune": f"0{i+1:04d}",
                "inscrits": 5000,
                "abstentions": 1000,
                "votants": 4000,
                "blancs": 100,
                "nuls": 50,
                "exprimes": 3850,
            })
    return pd.DataFrame(rows)


def _make_candidats(n: int) -> pd.DataFrame:
    rows = []
    for an in ANNEES:
        for i in range(n):
            code = f"0{i+1:04d}"
            for nom, prenom, voix in CANDIDATS_PAR_AN[an]:
                rows.append({
                    "id_election": f"{an}-PP-01",
                    "code_commune": code,
                    "nom": nom,
                    "prenom": prenom,
                    "voix": voix,
                })
    return pd.DataFrame(rows)


def _make_table_minimale(n: int) -> pd.DataFrame:
    """Table analytique avec les colonnes minimales pour compute_features."""
    rng = np.random.default_rng(0)
    rows = []
    for an in ANNEES:
        for i in range(n):
            rows.append({
                "CODGEO": f"0{i+1:04d}",
                "annee": an,
                "inscrits":    5000.0,
                "abstentions": 1000.0,
                "votants":     4000.0,
                "blancs":      100.0,
                "nuls":        50.0,
                "exprimes":    3850.0,
                "gauche_radicale":      800.0,
                "social_democratie":    200.0,
                "ecologisme":           0.0,
                "liberalisme_centre":   1000.0,
                "droite_conservatrice": 700.0,
                "souverainisme":        150.0,
                "droite_nationale":     900.0 + float(rng.integers(0, 100)),
                "P_POP":          float(rng.integers(2000, 20000)),
                "P_POP1564":      float(rng.integers(1000, 12000)),
                "P_ACT1564":      float(rng.integers(500, 8000)),
                "P_CHOM1564":     float(rng.integers(50, 1200)),
                "P_ACTOCC1564":   float(rng.integers(400, 7000)),
                "P_NSCOL15P":     float(rng.integers(500, 6000)),
                "P_NSCOL15P_DIPLMIN": float(rng.integers(100, 2000)),
                "P_LOG":          float(rng.integers(800, 9000)),
                "P_LOGVAC":       float(rng.integers(30, 800)),
                "P_RP":           float(rng.integers(700, 8000)),
                "P_RP_PROP":      float(rng.integers(300, 5000)),
                "P_RP_LOCHLMV":   float(rng.integers(30, 1500)),
                "nb_associations": float(rng.integers(5, 150)),
            })
    return pd.DataFrame(rows)


def _make_features_final(n: int) -> pd.DataFrame:
    """features_final.parquet synthétique pour la Phase 5."""
    rng = np.random.default_rng(42)
    rows = []
    for an in ANNEES:
        for i in range(n):
            pcts = rng.dirichlet(np.ones(7)) * 100
            rows.append({
                "CODGEO": f"0{i+1:04d}",
                "annee": an,
                "DEP": f"{(i % 95) + 1:02d}",
                "lib_commune": f"Commune {i+1}",
                "pct_gauche_radicale":      pcts[0],
                "pct_social_democratie":    pcts[1],
                "pct_ecologisme":           pcts[2],
                "pct_liberalisme_centre":   pcts[3],
                "pct_droite_conservatrice": pcts[4],
                "pct_souverainisme":        pcts[5],
                "pct_droite_nationale":     pcts[6],
                "taux_chomage":       float(rng.uniform(5, 20)),
                "pct_diplome_sup":    float(rng.uniform(10, 40)),
                "pct_sans_diplome":   float(rng.uniform(10, 35)),
                "revenu_median":      float(rng.uniform(18000, 35000)),
                "pct_immigres":       float(rng.uniform(1, 20)),
                "densite_associative": float(rng.uniform(5, 30)),
                "pct_cadres":         float(rng.uniform(5, 30)),
                "pct_ouvriers":       float(rng.uniform(10, 40)),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Smoke tests Phase 3
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ct():
    return _charger_module("02_clean_transform.py", "clean_transform")


def test_aggregate_elections_familles_presentes(ct):
    general   = _make_general(10)
    candidats = _make_candidats(10)

    elections = ct.aggregate_elections(general, candidats, cog_map={})

    for col in ["gauche_radicale", "liberalisme_centre", "droite_nationale", "social_democratie"]:
        assert col in elections.columns, f"Colonne manquante : {col}"

    assert set(elections["annee"].unique()) == {"2017", "2022"}
    assert elections["CODGEO"].nunique() == 10


def test_aggregate_elections_zero_inconnu(ct):
    """Tous les candidats du jeu de test doivent être mappés."""
    general   = _make_general(5)
    candidats = _make_candidats(5)

    elections = ct.aggregate_elections(general, candidats, cog_map={})

    if "INCONNU" in elections.columns:
        assert elections["INCONNU"].sum() == 0


def test_aggregate_elections_deux_annees(ct):
    general   = _make_general(20)
    candidats = _make_candidats(20)

    elections = ct.aggregate_elections(general, candidats, cog_map={})

    assert len(elections) == 40  # 20 communes × 2 années


def test_compute_features_colonnes_cles(ct):
    table  = _make_table_minimale(20)
    result = ct.compute_features(table)

    assert "taux_abstention" in result.columns
    assert "taux_chomage" in result.columns
    assert "pct_sans_diplome" in result.columns
    assert "densite_associative" in result.columns
    assert "pct_gauche_radicale" in result.columns
    assert "pct_droite_nationale" in result.columns


def test_compute_features_taux_abstention_borne(ct):
    table  = _make_table_minimale(20)
    result = ct.compute_features(table)

    vals = result["taux_abstention"].dropna()
    assert (vals >= 0).all() and (vals <= 100).all()


def test_compute_features_somme_pct_familles_approx_100(ct):
    table  = _make_table_minimale(20)
    result = ct.compute_features(table)

    familles_pct = [
        f"pct_{f}" for f in [
            "gauche_radicale", "social_democratie", "ecologisme",
            "liberalisme_centre", "droite_conservatrice", "souverainisme", "droite_nationale",
        ]
        if f"pct_{f}" in result.columns
    ]
    if familles_pct:
        total = result[familles_pct].sum(axis=1)
        assert (total.abs() - 100).abs().median() < 5  # tolérance ±5 pp


# ---------------------------------------------------------------------------
# Smoke test Phase 5 — pipeline complet
# ---------------------------------------------------------------------------

def test_phase5_pipeline_complet(tmp_path):
    mod = _charger_module("04_modelisation.py", "modelisation_smoke")

    # Injecter les chemins temporaires
    processed = tmp_path / "processed"
    analysis  = tmp_path / "analysis"
    models    = tmp_path / "models"
    processed.mkdir()
    analysis.mkdir()
    models.mkdir()

    mod.PROCESSED = processed
    mod.ANALYSIS  = analysis
    mod.MODELS    = models

    # Écrire les données synthétiques
    df = _make_features_final(N_COMMUNES)
    df.to_parquet(processed / "features_final.parquet", index=False)

    # Exécution du pipeline
    df_loaded, features = mod.charger_donnees()
    X, Y, X_train, X_test, Y_train, Y_test, df_test, feats_dispo, df_shuffle = mod.preparer_donnees(df_loaded, features)
    comparaison, meilleur_nom, meilleur_pred = mod.evaluer_modeles(X_train, X_test, Y_train, Y_test)
    modele_final = mod.entrainer_modele_final(meilleur_nom, X, Y)
    pred_df = mod.sauvegarder_predictions_test(df_test, Y_test, meilleur_pred)
    mod.calculer_importance(modele_final, X_train, X_test, Y_train, Y_test, feats_dispo)
    prospectives = mod.projeter_indicateurs(df_loaded, feats_dispo, modele_final)
    mod.visualiser(df_loaded, pred_df, prospectives)

    # Vérifications : fichiers générés
    assert (models    / "best_model.pkl").exists(),               "Modèle non sauvegardé"
    assert (analysis  / "model_comparison.csv").exists()
    assert (analysis  / "feature_importance.csv").exists()
    assert (analysis  / "feature_importance.png").exists()
    assert (processed / "predictions_test.parquet").exists()
    assert (processed / "prospectives.parquet").exists()
    assert (analysis  / "scatter_reel_vs_predit.png").exists()
    assert (analysis  / "tendances_familles.png").exists()
    assert (analysis  / "tendances_par_dep.png").exists()

    # Vérifications : structure du model_comparison
    assert comparaison.shape[0] == 3 * 7  # 3 modèles × 7 familles
    assert set(comparaison["modele"].unique()) == {"Ridge", "Random Forest", "Gradient Boosting"}

    # Vérifications : prospectives
    assert set(prospectives["annee_projetee"].unique()) == {2023, 2024, 2025}
    assert prospectives["CODGEO"].nunique() == N_COMMUNES

    # Vérifications : prédictions test
    pred_loaded = pd.read_parquet(processed / "predictions_test.parquet")
    assert len(pred_loaded) == len(Y_test)
    assert f"reel_gauche_radicale"   in pred_loaded.columns
    assert f"predit_droite_nationale" in pred_loaded.columns
