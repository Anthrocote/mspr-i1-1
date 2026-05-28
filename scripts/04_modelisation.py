#!/usr/bin/env python3 -u
"""
Usage:
    python -u scripts/04_modelisation.py

Phase 5 — Modélisation prédictive et prospective.
Entrée  : data/processed/features_final.parquet  (Phase 4)
           data/processed/table_analytique.parquet (fallback)
Sorties : models/best_model.pkl
          data/processed/predictions_test.parquet
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

from sklearn.base import clone
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split
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

TEST_SIZE    = 0.2
RANDOM_STATE = 42


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

    print(f"  {df.shape[0]} lignes x {df.shape[1]} colonnes")

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
# Étape 2 — Préparation des matrices (données mélangées)
# ===========================================================================

def preparer_donnees(df: pd.DataFrame, features: list) -> tuple:
    print(f"=== Étape 2 — Préparation (mélange aléatoire, split {int((1-TEST_SIZE)*100)}/{int(TEST_SIZE*100)}) ===")

    feats_dispo = [f for f in features if f in df.columns]

    # Mélange aléatoire de toutes les lignes (2017 + 2022 mélangés)
    df_shuffle = df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

    mediane = df_shuffle[feats_dispo].median()
    X = df_shuffle[feats_dispo].fillna(mediane).values
    Y = df_shuffle[CIBLES].fillna(0).values

    idx = np.arange(len(X))
    idx_train, idx_test = train_test_split(idx, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    X_train, X_test = X[idx_train], X[idx_test]
    Y_train, Y_test = Y[idx_train], Y[idx_test]
    df_test = df_shuffle.iloc[idx_test]

    print(f"  {len(df_shuffle)} lignes melangees  (train={len(idx_train)}, test={len(idx_test)})")
    print(f"  {len(feats_dispo)} features, {len(CIBLES)} cibles\n")
    return X, Y, X_train, X_test, Y_train, Y_test, df_test, feats_dispo, df_shuffle


# ===========================================================================
# Étape 3 — Cross-validation k-fold
# ===========================================================================

def _definir_modeles() -> dict:
    return {
        "Ridge": Pipeline([
            ("scaler", StandardScaler()),
            ("reg", MultiOutputRegressor(Ridge(alpha=1.0))),
        ]),
        "Random Forest": RandomForestRegressor(
            n_estimators=200, random_state=RANDOM_STATE, n_jobs=-1
        ),
        "Gradient Boosting": MultiOutputRegressor(
            HistGradientBoostingRegressor(random_state=RANDOM_STATE, max_iter=100)
        ),
    }


def evaluer_modeles(
    X_train: np.ndarray,
    X_test: np.ndarray,
    Y_train: np.ndarray,
    Y_test: np.ndarray,
) -> tuple:
    print(f"=== Étape 3 — Évaluation split 80/20 ===")

    modeles = _definir_modeles()

    lignes = []
    meilleur_nom  = None
    meilleur_r2   = -np.inf
    meilleur_pred = None

    for nom, modele in modeles.items():
        print(f"  {nom}...")
        m = clone(modele)
        m.fit(X_train, Y_train)
        pred = m.predict(X_test)

        r2_par_fam = []
        for i, fam in enumerate(FAMILLES):
            r2  = r2_score(Y_test[:, i], pred[:, i])
            mae = mean_absolute_error(Y_test[:, i], pred[:, i])
            r2_par_fam.append(r2)
            lignes.append({"modele": nom, "famille": fam, "r2": round(r2, 4), "mae": round(mae, 4)})

        r2_moy = float(np.mean(r2_par_fam))
        print(f"    R² moyen = {r2_moy:.4f}")

        if r2_moy > meilleur_r2:
            meilleur_r2   = r2_moy
            meilleur_nom  = nom
            meilleur_pred = pred.copy()

    comparaison = pd.DataFrame(lignes)
    comparaison.to_csv(ANALYSIS / "model_comparison.csv", index=False)
    print(f"  -> {ANALYSIS / 'model_comparison.csv'}")

    resume = comparaison.groupby("modele")[["r2", "mae"]].mean().round(4)
    print(f"\n  Resume (moyenne sur {len(FAMILLES)} familles) :")
    print(resume.to_string())
    print(f"\n  Meilleur modele : {meilleur_nom} (R²={meilleur_r2:.4f})\n")

    return comparaison, meilleur_nom, meilleur_pred


# ===========================================================================
# Étape 4 — Entraînement final sur toutes les données
# ===========================================================================

def entrainer_modele_final(nom: str, X: np.ndarray, Y: np.ndarray):
    print(f"=== Étape 4 — Entraînement final ({nom} sur 100% des données) ===")
    modele = _definir_modeles()[nom]
    modele.fit(X, Y)
    joblib.dump(modele, MODELS / "best_model.pkl")
    print(f"  -> {MODELS / 'best_model.pkl'}\n")
    return modele


# ===========================================================================
# Étape 5 — Sauvegarde des prédictions OOF
# ===========================================================================

def sauvegarder_predictions_test(
    df_test: pd.DataFrame,
    Y_test: np.ndarray,
    pred_test: np.ndarray,
) -> pd.DataFrame:
    print("=== Étape 5 — Sauvegarde des prédictions (jeu de test) ===")

    pred_df = df_test[["CODGEO", "annee", "DEP", "lib_commune"]].copy().reset_index(drop=True)
    for i, fam in enumerate(FAMILLES):
        pred_df[f"reel_{fam}"]   = Y_test[:, i]
        pred_df[f"predit_{fam}"] = pred_test[:, i].round(4)

    pred_df.to_parquet(PROCESSED / "predictions_test.parquet", index=False)
    print(f"  -> {PROCESSED / 'predictions_test.parquet'}\n")
    return pred_df


# ===========================================================================
# Étape 6 — Feature importance
# ===========================================================================

def calculer_importance(
    modele_final,
    X_train: np.ndarray,
    X_test: np.ndarray,
    Y_train: np.ndarray,
    Y_test: np.ndarray,
    features: list,
) -> None:
    print("=== Étape 6 — Feature importance ===")

    # Clone entraîné sur le train, évalué sur le test (même split 70/30)
    modele_imp = clone(modele_final)
    modele_imp.fit(X_train, Y_train)
    X_imp, Y_imp = X_test, Y_test

    result = permutation_importance(
        modele_imp, X_imp, Y_imp,
        n_repeats=10, random_state=RANDOM_STATE, n_jobs=-1,
    )

    imp_df = pd.DataFrame({
        "feature":    features,
        "importance": result.importances_mean,
    }).sort_values("importance", ascending=False)
    imp_df.to_csv(ANALYSIS / "feature_importance.csv", index=False)
    print(f"  -> {ANALYSIS / 'feature_importance.csv'}")

    top20 = imp_df.head(20)
    plt.figure(figsize=(10, 7))
    sns.barplot(data=top20, x="importance", y="feature", palette="viridis")
    plt.title(f"Top 20 features — Permutation importance")
    plt.xlabel("Importance moyenne (permutation, holdout 20%)")
    plt.tight_layout()
    plt.savefig(ANALYSIS / "feature_importance.png", dpi=120)
    plt.close()
    print(f"  -> {ANALYSIS / 'feature_importance.png'}\n")


# ===========================================================================
# Étape 7 — Projection temporelle (T+1 / T+2 / T+3)
# ===========================================================================

def projeter_indicateurs(
    df: pd.DataFrame,
    features: list,
    modele_final,
) -> pd.DataFrame:
    print("=== Étape 7 — Projection temporelle (T+1 / T+2 / T+3) ===")

    mediane_globale = df[features].median()
    annee = df["annee"].astype(str)

    meta22 = (
        df[annee == "2022"][["CODGEO", "DEP", "lib_commune"]]
        .drop_duplicates("CODGEO")
        .set_index("CODGEO")
    )
    df17 = (
        df[annee == "2017"].drop_duplicates("CODGEO")
        .set_index("CODGEO")[features].fillna(mediane_globale)
    )
    df22 = (
        df[annee == "2022"].drop_duplicates("CODGEO")
        .set_index("CODGEO")[features].fillna(mediane_globale)
    )

    communes_communes = df17.index.intersection(df22.index)
    delta = (df22.loc[communes_communes] - df17.loc[communes_communes]) / 5
    communes_only22  = df22.index.difference(communes_communes)

    resultats = []
    for horizon, an_proj in enumerate([2023, 2024, 2025], start=1):
        X_proj = df22.loc[communes_communes] + delta * horizon
        pred   = modele_final.predict(X_proj.values)
        bloc   = pd.DataFrame(
            pred,
            columns=[f"pct_pred_{f}" for f in FAMILLES],
            index=communes_communes,
        )
        bloc["annee_projetee"] = an_proj
        resultats.append(bloc)

        if len(communes_only22) > 0:
            pred_only  = modele_final.predict(df22.loc[communes_only22].values)
            bloc_only  = pd.DataFrame(
                pred_only,
                columns=[f"pct_pred_{f}" for f in FAMILLES],
                index=communes_only22,
            )
            bloc_only["annee_projetee"] = an_proj
            resultats.append(bloc_only)

    prospectives = (
        pd.concat(resultats)
        .reset_index()
        .rename(columns={"index": "CODGEO"})
    )
    prospectives["DEP"]          = prospectives["CODGEO"].map(meta22["DEP"])
    prospectives["lib_commune"]  = prospectives["CODGEO"].map(meta22["lib_commune"])
    pred_cols = [f"pct_pred_{f}" for f in FAMILLES]
    prospectives[pred_cols] = prospectives[pred_cols].round(4)

    prospectives.to_parquet(PROCESSED / "prospectives.parquet", index=False)
    print(f"  {len(prospectives)} lignes ({prospectives['CODGEO'].nunique()} communes x 3 ans)")
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

    # --- 8a. Scatter OOF réel vs prédit ---
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    axes = axes.flatten()
    for i, fam in enumerate(FAMILLES):
        ax     = axes[i]
        reel   = pred_df[f"reel_{fam}"]
        predit = pred_df[f"predit_{fam}"]
        ax.scatter(reel, predit, alpha=0.2, s=6, color="steelblue")
        lim = [min(reel.min(), predit.min()) - 1, max(reel.max(), predit.max()) + 1]
        ax.plot(lim, lim, "r--", linewidth=1)
        r2 = r2_score(reel, predit)
        ax.set_title(f"{fam}\nR²={r2:.3f}", fontsize=9)
        ax.set_xlabel("Reel (%)")
        ax.set_ylabel("Predit (%)")
    axes[-1].set_visible(False)
    fig.suptitle(f"Reel vs Predit — Split {int((1-TEST_SIZE)*100)}/{int(TEST_SIZE*100)} (jeu de test)", fontsize=13)
    plt.tight_layout()
    plt.savefig(ANALYSIS / "scatter_reel_vs_predit.png", dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  -> {ANALYSIS / 'scatter_reel_vs_predit.png'}")

    # --- 8b. Courbes de tendance nationales ---
    annee = df["annee"].astype(str)
    mediane_hist = {}
    for an in ["2017", "2022"]:
        mask = annee == an
        for fam in FAMILLES:
            col = f"pct_{fam}"
            if col in df.columns:
                mediane_hist.setdefault(fam, {})[int(an)] = df.loc[mask, col].median()

    mediane_proj = (
        prospectives
        .groupby("annee_projetee")[[f"pct_pred_{f}" for f in FAMILLES]]
        .median()
    )

    couleurs = plt.cm.tab10(np.linspace(0, 1, 7))
    fig, ax = plt.subplots(figsize=(12, 6))
    for i, fam in enumerate(FAMILLES):
        annees_h = sorted(mediane_hist.get(fam, {}).keys())
        vals_h   = [mediane_hist[fam][a] for a in annees_h]
        annees_p = mediane_proj.index.tolist()
        vals_p   = mediane_proj[f"pct_pred_{fam}"].tolist()

        ax.plot(annees_h, vals_h, "o-", color=couleurs[i], linewidth=2, markersize=6)
        ax.plot(annees_p, vals_p, "--", color=couleurs[i], linewidth=1.5, alpha=0.7,
                label=fam.replace("_", " "))
        if annees_h and annees_p:
            ax.plot([annees_h[-1], annees_p[0]], [vals_h[-1], vals_p[0]],
                    "--", color=couleurs[i], linewidth=1.5, alpha=0.7)

    ax.axvline(x=2022.5, color="gray", linestyle=":", linewidth=1, label="-> projections")
    ax.set_xlabel("Annee")
    ax.set_ylabel("% median national")
    ax.set_title("Tendances electorales nationales — Mediane communale (2017-2025)")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(ANALYSIS / "tendances_familles.png", dpi=120)
    plt.close()
    print(f"  -> {ANALYSIS / 'tendances_familles.png'}")

    # --- 8c. Heatmap prospective par département ---
    familles_polarisees = ["droite_nationale", "gauche_radicale"]
    fig, axes = plt.subplots(1, 2, figsize=(18, 10))
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
            linewidths=0.2, cbar_kws={"label": "% median", "shrink": 0.7},
        )
        ax.set_title(f"{fam.replace('_', ' ')} — par departement", fontsize=10)
        ax.set_xlabel("Annee projetee")
        ax.set_ylabel("Departement")
        ax.tick_params(axis="y", labelsize=6)

    plt.suptitle("Tendances prospectives 2023-2025 par departement", fontsize=12)
    plt.tight_layout()
    plt.savefig(ANALYSIS / "tendances_par_dep.png", dpi=120)
    plt.close()
    print(f"  -> {ANALYSIS / 'tendances_par_dep.png'}\n")


# ===========================================================================
# Main
# ===========================================================================

def main():
    print("Phase 5 — Modelisation predictive et prospective")
    print(f"Analyse : {ANALYSIS}")
    print(f"Modeles : {MODELS}\n")

    df, features = charger_donnees()

    X, Y, X_train, X_test, Y_train, Y_test, df_test, feats_dispo, df_shuffle = preparer_donnees(df, features)

    comparaison, meilleur_nom, meilleur_pred = evaluer_modeles(X_train, X_test, Y_train, Y_test)

    modele_final = entrainer_modele_final(meilleur_nom, X, Y)

    pred_df = sauvegarder_predictions_test(df_test, Y_test, meilleur_pred)

    calculer_importance(modele_final, X_train, X_test, Y_train, Y_test, feats_dispo)

    prospectives = projeter_indicateurs(df, feats_dispo, modele_final)

    visualiser(df, pred_df, prospectives)

    print("=" * 60)
    print("Phase 5 terminee.")
    print(f"  Meilleur modele : {meilleur_nom}")
    print(f"  Modele sauvegarde : {MODELS / 'best_model.pkl'}")
    print(f"  Prospectives : {PROCESSED / 'prospectives.parquet'}")
    print(f"  Visualisations : {ANALYSIS}/")


if __name__ == "__main__":
    main()
