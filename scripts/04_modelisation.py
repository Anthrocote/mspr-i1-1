#!/usr/bin/env python3 -u
"""
Usage:
    python -u scripts/04_modelisation.py

Phase 5 — Modélisation prédictive et prospective.
Entrée  : data/processed/features_final.parquet  (Phase 4)
           data/processed/table_analytique.parquet (fallback)
Sorties : models/best_model.pkl
          data/processed/predictions_2022.parquet
          data/processed/prospectives.parquet
          data/analysis/model_comparison.csv
          data/analysis/feature_importance.csv
          data/analysis/feature_importance.png
          data/analysis/scatter_reel_vs_predit.png
          data/analysis/tendances_familles.png
          data/analysis/tendances_par_dep.png
"""

import sys
import warnings

import joblib
import numpy as np
import pandas as pd
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
ANALYSIS  = Path(__file__).resolve().parent.parent / "data" / "analysis"
MODELS    = Path(__file__).resolve().parent.parent / "models"
ANALYSIS.mkdir(parents=True, exist_ok=True)
MODELS.mkdir(parents=True, exist_ok=True)

FAMILLES = [
    "gauche_radicale",
    "social_democratie",
    "ecologisme",
    "liberalisme_centre",
    "droite_conservatrice",
    "souverainisme",
    "droite_nationale",
]
CIBLES = [f"pct_{f}" for f in FAMILLES]

EXCLUS = {
    "CODGEO", "annee", "lib_commune", "DEP", "REG",
    "taux_abstention", "taux_blancs_nuls",
    "inscrits", "abstentions", "votants", "blancs", "nuls", "exprimes",
    "nb_associations", "INCONNU",
    "NAISD17", "DECESD17", "NAISD22", "DECESD22",
} | set(CIBLES) | set(FAMILLES)


# ===========================================================================
# Étape 1 — Chargement
# ===========================================================================

def charger_donnees() -> tuple[pd.DataFrame, list]:
    print("=== Étape 1 — Chargement ===")

    chemin = PROCESSED / "features_final.parquet"
    if chemin.exists():
        df = pd.read_parquet(chemin)
        print(f"  Source : features_final.parquet")
    else:
        chemin = PROCESSED / "table_analytique.parquet"
        print(f"  ATTENTION : features_final.parquet absent, fallback sur table_analytique.parquet")
        df = pd.read_parquet(chemin)

    print(f"  {df.shape[0]} lignes × {df.shape[1]} colonnes")

    # Recalcul des cibles si absentes
    for fam in FAMILLES:
        pct_col = f"pct_{fam}"
        if pct_col not in df.columns and fam in df.columns and "exprimes" in df.columns:
            df[pct_col] = (df[fam] / df["exprimes"].replace(0, np.nan) * 100).round(2)

    manquantes = [c for c in CIBLES if c not in df.columns]
    if manquantes:
        raise ValueError(f"Cibles manquantes : {manquantes}")

    features = sorted([
        c for c in df.columns
        if c not in EXCLUS
        and pd.api.types.is_numeric_dtype(df[c])
        and df[c].notna().mean() > 0.5
    ])
    print(f"  {len(features)} features candidates\n")
    return df, features


# ===========================================================================
# Étape 2 — Split temporel
# ===========================================================================

def preparer_split(df: pd.DataFrame, features: list) -> tuple:
    print("=== Étape 2 — Split temporel (train=2017 / test=2022) ===")

    annee = df["annee"].astype(str)
    mask_train = annee == "2017"
    mask_test  = annee == "2022"

    feats_dispo = [f for f in features if f in df.columns]
    X = df[feats_dispo].fillna(df[feats_dispo].median())

    X_train = X[mask_train].values
    X_test  = X[mask_test].values
    y_train = df.loc[mask_train, CIBLES].fillna(0).values
    y_test  = df.loc[mask_test,  CIBLES].fillna(0).values

    print(f"  Train (2017) : {X_train.shape[0]} communes")
    print(f"  Test  (2022) : {X_test.shape[0]} communes")
    print(f"  Features     : {len(feats_dispo)}\n")

    return X_train, X_test, y_train, y_test, df[mask_test], feats_dispo


# ===========================================================================
# Étape 3 — Entraînement des modèles
# ===========================================================================

def entrainer_modeles(X_train: np.ndarray, y_train: np.ndarray) -> dict:
    print("=== Étape 3 — Entraînement des modèles ===")

    modeles = {
        "Ridge": Pipeline([
            ("scaler", StandardScaler()),
            ("reg", MultiOutputRegressor(Ridge(alpha=1.0))),
        ]),
        "Random Forest": RandomForestRegressor(
            n_estimators=200, random_state=42, n_jobs=-1
        ),
        "Gradient Boosting": MultiOutputRegressor(
            HistGradientBoostingRegressor(random_state=42, max_iter=100),
            n_jobs=-1,
        ),
    }

    fitte = {}
    for nom, modele in modeles.items():
        print(f"  Entraînement {nom}...")
        modele.fit(X_train, y_train)
        fitte[nom] = modele
        print(f"    OK")

    print()
    return fitte


# ===========================================================================
# Étape 4 — Évaluation
# ===========================================================================

def evaluer_modeles(
    modeles: dict,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> tuple[pd.DataFrame, str]:
    print("=== Étape 4 — Évaluation ===")

    lignes = []
    for nom, modele in modeles.items():
        y_pred = modele.predict(X_test)
        for i, fam in enumerate(FAMILLES):
            r2  = r2_score(y_test[:, i], y_pred[:, i])
            mae = mean_absolute_error(y_test[:, i], y_pred[:, i])
            lignes.append({"modele": nom, "famille": fam, "r2": round(r2, 4), "mae": round(mae, 4)})

    comparaison = pd.DataFrame(lignes)
    comparaison.to_csv(ANALYSIS / "model_comparison.csv", index=False)
    print(f"  -> {ANALYSIS / 'model_comparison.csv'}")

    # Résumé par modèle
    resume = comparaison.groupby("modele")[["r2", "mae"]].mean().round(4)
    print("\n  Résumé par modèle (moyenne sur 7 familles) :")
    print(resume.to_string())

    meilleur = resume["r2"].idxmax()
    print(f"\n  Meilleur modèle : {meilleur} (R²={resume.loc[meilleur, 'r2']:.4f})\n")
    return comparaison, meilleur


# ===========================================================================
# Étape 5 — Sauvegarde du meilleur modèle
# ===========================================================================

def sauvegarder_modele(
    modeles: dict,
    meilleur: str,
    X_test: np.ndarray,
    y_test: np.ndarray,
    df_test: pd.DataFrame,
) -> None:
    print("=== Étape 5 — Sauvegarde ===")

    modele = modeles[meilleur]
    joblib.dump(modele, MODELS / "best_model.pkl")
    print(f"  -> {MODELS / 'best_model.pkl'}")

    y_pred = modele.predict(X_test)
    pred_df = df_test[["CODGEO", "DEP", "lib_commune"]].copy().reset_index(drop=True)
    for i, fam in enumerate(FAMILLES):
        pred_df[f"reel_{fam}"]   = y_test[:, i]
        pred_df[f"predit_{fam}"] = y_pred[:, i].round(4)

    pred_df.to_parquet(PROCESSED / "predictions_2022.parquet", index=False)
    print(f"  -> {PROCESSED / 'predictions_2022.parquet'}\n")


# ===========================================================================
# Étape 6 — Feature importance
# ===========================================================================

def calculer_importance(
    modeles: dict,
    meilleur: str,
    X_test: np.ndarray,
    y_test: np.ndarray,
    features: list,
) -> None:
    print("=== Étape 6 — Feature importance ===")

    modele = modeles[meilleur]

    # Permutation importance (fonctionne avec tous les estimateurs)
    result = permutation_importance(
        modele, X_test, y_test,
        n_repeats=10, random_state=42, n_jobs=-1,
    )
    importances = result.importances_mean

    imp_df = pd.DataFrame({
        "feature":    features,
        "importance": importances,
    }).sort_values("importance", ascending=False)
    imp_df.to_csv(ANALYSIS / "feature_importance.csv", index=False)
    print(f"  -> {ANALYSIS / 'feature_importance.csv'}")

    top20 = imp_df.head(20)
    plt.figure(figsize=(10, 7))
    sns.barplot(data=top20, x="importance", y="feature", palette="viridis")
    plt.title(f"Top 20 features — Permutation importance ({meilleur})")
    plt.xlabel("Importance moyenne (permutation)")
    plt.tight_layout()
    plt.savefig(ANALYSIS / "feature_importance.png", dpi=120)
    plt.close()
    print(f"  -> {ANALYSIS / 'feature_importance.png'}\n")


# ===========================================================================
# Étape 7 — Projection temporelle
# ===========================================================================

def projeter_indicateurs(
    df: pd.DataFrame,
    features: list,
    modele,
) -> pd.DataFrame:
    print("=== Étape 7 — Projection temporelle (T+1 / T+2 / T+3) ===")

    mediane_globale = df[features].median()
    annee = df["annee"].astype(str)

    # Dédupliquer par CODGEO (garder la première occurrence) pour avoir des scalaires
    meta22 = (
        df[annee == "2022"][["CODGEO", "DEP", "lib_commune"]]
        .drop_duplicates("CODGEO")
        .set_index("CODGEO")
    )

    df17 = (
        df[annee == "2017"]
        .drop_duplicates("CODGEO")
        .set_index("CODGEO")[features]
        .fillna(mediane_globale)
    )
    df22 = (
        df[annee == "2022"]
        .drop_duplicates("CODGEO")
        .set_index("CODGEO")[features]
        .fillna(mediane_globale)
    )

    # Communes présentes dans les deux scrutins
    communes_communes = df17.index.intersection(df22.index)
    delta = (df22.loc[communes_communes] - df17.loc[communes_communes]) / 5

    # Communes seulement en 2022 : tendance nulle (delta=0)
    communes_only22 = df22.index.difference(communes_communes)

    resultats = []
    for horizon, an_proj in enumerate([2023, 2024, 2025], start=1):
        # --- Communes avec les deux millésimes ---
        X_proj = df22.loc[communes_communes] + delta * horizon
        pred = modele.predict(X_proj.values)
        bloc = pd.DataFrame(pred, columns=[f"pct_pred_{f}" for f in FAMILLES], index=communes_communes)
        bloc["annee_projetee"] = an_proj
        resultats.append(bloc)

        # --- Communes uniquement en 2022 ---
        if len(communes_only22) > 0:
            X_only = df22.loc[communes_only22]
            pred_only = modele.predict(X_only.values)
            bloc_only = pd.DataFrame(pred_only, columns=[f"pct_pred_{f}" for f in FAMILLES], index=communes_only22)
            bloc_only["annee_projetee"] = an_proj
            resultats.append(bloc_only)

    prospectives = pd.concat(resultats).reset_index().rename(columns={"index": "CODGEO"})
    prospectives["DEP"] = prospectives["CODGEO"].map(meta22["DEP"])
    prospectives["lib_commune"] = prospectives["CODGEO"].map(meta22["lib_commune"])
    # Arrondir les prédictions
    pred_cols = [f"pct_pred_{f}" for f in FAMILLES]
    prospectives[pred_cols] = prospectives[pred_cols].round(4)

    prospectives.to_parquet(PROCESSED / "prospectives.parquet", index=False)
    print(f"  {len(prospectives)} lignes ({prospectives['CODGEO'].nunique()} communes × 3 ans)")
    print(f"  -> {PROCESSED / 'prospectives.parquet'}\n")
    return prospectives


# ===========================================================================
# Étape 8 — Visualisations
# ===========================================================================

def visualiser(
    df: pd.DataFrame,
    pred_df: pd.DataFrame,
    prospectives: pd.DataFrame,
) -> None:
    print("=== Étape 8 — Visualisations ===")

    # --- 8a. Scatter réel vs prédit ---
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    axes = axes.flatten()
    for i, fam in enumerate(FAMILLES):
        ax = axes[i]
        reel   = pred_df[f"reel_{fam}"]
        predit = pred_df[f"predit_{fam}"]
        ax.scatter(reel, predit, alpha=0.3, s=8, color="steelblue")
        lim = [min(reel.min(), predit.min()) - 1, max(reel.max(), predit.max()) + 1]
        ax.plot(lim, lim, "r--", linewidth=1)
        r2 = r2_score(reel, predit)
        ax.set_title(f"{fam}\nR²={r2:.3f}", fontsize=9)
        ax.set_xlabel("Réel (%)")
        ax.set_ylabel("Prédit (%)")
    axes[-1].set_visible(False)
    fig.suptitle("Réel vs Prédit — Jeu de test 2022", fontsize=13, y=1.01)
    plt.tight_layout()
    plt.savefig(ANALYSIS / "scatter_reel_vs_predit.png", dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  -> {ANALYSIS / 'scatter_reel_vs_predit.png'}")

    # --- 8b. Courbes de tendance nationales ---
    annee = df["annee"].astype(str)

    # Médiane nationale par famille pour 2017 et 2022
    mediane_historique = {}
    for an in ["2017", "2022"]:
        mask = annee == an
        for fam in FAMILLES:
            col = f"pct_{fam}"
            if col in df.columns:
                mediane_historique.setdefault(fam, {})[int(an)] = df.loc[mask, col].median()

    # Médiane nationale prospective
    mediane_prospective = (
        prospectives.groupby("annee_projetee")[
            [f"pct_pred_{f}" for f in FAMILLES]
        ].median()
    )

    couleurs = plt.cm.tab10(np.linspace(0, 1, 7))
    fig, ax = plt.subplots(figsize=(12, 6))
    for i, fam in enumerate(FAMILLES):
        annees_hist = sorted(mediane_historique.get(fam, {}).keys())
        vals_hist   = [mediane_historique[fam][a] for a in annees_hist]
        annees_proj = mediane_prospective.index.tolist()
        vals_proj   = mediane_prospective[f"pct_pred_{fam}"].tolist()

        toutes_annees = annees_hist + annees_proj
        toutes_vals   = vals_hist + vals_proj

        ax.plot(annees_hist, vals_hist, "o-", color=couleurs[i], linewidth=2, markersize=6)
        ax.plot(annees_proj, vals_proj, "--", color=couleurs[i], linewidth=1.5, alpha=0.7,
                label=fam.replace("_", " "))
        # Pont entre 2022 et 2023
        if annees_hist and annees_proj:
            ax.plot([annees_hist[-1], annees_proj[0]],
                    [vals_hist[-1], vals_proj[0]],
                    "--", color=couleurs[i], linewidth=1.5, alpha=0.7)

    ax.axvline(x=2022.5, color="gray", linestyle=":", linewidth=1, label="→ projections")
    ax.set_xlabel("Année")
    ax.set_ylabel("% médian national")
    ax.set_title("Tendances électorales nationales — Médiane communale (2017-2025)")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(ANALYSIS / "tendances_familles.png", dpi=120)
    plt.close()
    print(f"  -> {ANALYSIS / 'tendances_familles.png'}")

    # --- 8c. Heatmap prospective par département ---
    familles_polarisees = ["droite_nationale", "gauche_radicale"]
    n_fam = len(familles_polarisees)
    fig, axes = plt.subplots(1, n_fam, figsize=(18, 10))

    for ax, fam in zip(axes, familles_polarisees):
        col = f"pct_pred_{fam}"
        pivot = (
            prospectives[prospectives["DEP"].notna()]
            .groupby(["DEP", "annee_projetee"])[col]
            .median()
            .unstack("annee_projetee")
        )
        sns.heatmap(
            pivot, ax=ax, cmap="RdYlBu_r", annot=False,
            fmt=".1f", linewidths=0.2,
            cbar_kws={"label": "% médian", "shrink": 0.7},
        )
        ax.set_title(f"{fam.replace('_', ' ')} — par département", fontsize=10)
        ax.set_xlabel("Année projetée")
        ax.set_ylabel("Département")
        ax.tick_params(axis="y", labelsize=6)

    plt.suptitle("Tendances prospectives 2023-2025 par département", fontsize=12)
    plt.tight_layout()
    plt.savefig(ANALYSIS / "tendances_par_dep.png", dpi=120)
    plt.close()
    print(f"  -> {ANALYSIS / 'tendances_par_dep.png'}\n")


# ===========================================================================
# Main
# ===========================================================================

def main():
    print("Phase 5 — Modélisation prédictive et prospective")
    print(f"Analyse : {ANALYSIS}")
    print(f"Modèles : {MODELS}\n")

    df, features = charger_donnees()

    X_train, X_test, y_train, y_test, df_test, feats_dispo = preparer_split(df, features)

    modeles = entrainer_modeles(X_train, y_train)

    comparaison, meilleur = evaluer_modeles(modeles, X_test, y_test)

    sauvegarder_modele(modeles, meilleur, X_test, y_test, df_test)

    calculer_importance(modeles, meilleur, X_test, y_test, feats_dispo)

    pred_df = pd.read_parquet(PROCESSED / "predictions_2022.parquet")

    prospectives = projeter_indicateurs(df, feats_dispo, modeles[meilleur])

    visualiser(df, pred_df, prospectives)

    print("=" * 60)
    print("Phase 5 terminée.")
    print(f"  Meilleur modèle : {meilleur}")
    print(f"  Modèle sauvegardé : {MODELS / 'best_model.pkl'}")
    print(f"  Prospectives : {PROCESSED / 'prospectives.parquet'}")
    print(f"  Visualisations : {ANALYSIS}/")


if __name__ == "__main__":
    main()
