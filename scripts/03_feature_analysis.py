#!/usr/bin/env python3 -u
"""
Usage:
    python -u scripts/03_feature_analysis.py

Phase 4 — Analyse exploratoire & feature engineering avancé.
Produit data/processed/features_final.parquet prêt pour la modélisation (Phase 5).
"""

import sys
import warnings

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from scipy.cluster import hierarchy
from scipy.spatial.distance import squareform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.feature_selection import mutual_info_regression
from sklearn.linear_model import BayesianRidge
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.preprocessing import MinMaxScaler

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
ANALYSIS = Path(__file__).resolve().parent.parent / "data" / "analysis"
ANALYSIS.mkdir(parents=True, exist_ok=True)

# Familles politiques et leurs colonnes cibles
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

# Colonnes exclues de l'analyse features (identifiants, cibles, comptages bruts)
EXCLURE = set(
    ["CODGEO", "annee", "lib_commune", "DEP", "REG"]
    + CIBLES
    + FAMILLES
    + [
        "inscrits", "abstentions", "votants", "blancs", "nuls", "exprimes",
        "nb_associations", "INCONNU",
        "NAISD17", "DECESD17", "NAISD22", "DECESD22",
    ]
)

# Features revenus pour imputation MICE
FEATURES_REVENUS = ["D121", "D921", "RD21", "PACT21", "PPEN21", "PPSOC21", "PIMP21", "MED21", "TP6021"]

# Features-clés imposées par la littérature (Piketty, Michelat & Simon, Siegfried)
FEATURES_LITTERATURE = [
    "taux_chomage", "MED21", "pct_sans_diplome", "pct_diplome_sup",
    "pct_immigres", "pct_cadres", "pct_ouvriers", "taux_abstention",
    "TP6021", "crim_violences", "crim_atteintes_biens", "densite_associative",
    "pct_emploi_indus", "pct_proprietaires", "pct_hlm",
]


def _priorite_feature(name: str) -> int:
    """Score de priorité dans un cluster colinéaire. Plus bas = plus interprétable."""
    if name.startswith(("taux_", "pct_", "solde_")):
        return 1
    if name.startswith("log1p_"):
        return 2
    if any(name.startswith(p) for p in ["MED", "TP60", "D12", "D92", "RD2", "PACT",
                                          "PPEN", "PPSOC", "PIMP", "crim_", "densite_"]):
        return 3
    return 4  # Colonnes brutes P_* / C_*


# ===========================================================================
# Préparation
# ===========================================================================

def preparer_cibles(df: pd.DataFrame) -> pd.DataFrame:
    """Calcule les pct_ par famille politique si absents (bug potentiel Phase 3)."""
    for fam in FAMILLES:
        pct_col = f"pct_{fam}"
        if pct_col not in df.columns and fam in df.columns and "exprimes" in df.columns:
            df[pct_col] = (df[fam] / df["exprimes"].replace(0, np.nan) * 100).round(2)
    manquantes = [c for c in CIBLES if c not in df.columns]
    if manquantes:
        print(f"  ATTENTION: cibles manquantes après calcul: {manquantes}")
    return df


# ===========================================================================
# Étape 1 — Audit des features
# ===========================================================================

def audit_features(df: pd.DataFrame, features: list) -> pd.DataFrame:
    print("=== Étape 1 — Audit des features ===")
    rows = []
    for feat in features:
        col = df[feat]
        nan_total = col.isna().mean() * 100
        nan_2017 = df.loc[df["annee"].astype(str) == "2017", feat].isna().mean() * 100
        nan_2022 = df.loc[df["annee"].astype(str) == "2022", feat].isna().mean() * 100
        zero_pct = (col == 0).mean() * 100
        valeurs = col.dropna()
        skew = float(stats.skew(valeurs)) if len(valeurs) > 2 else 0.0

        if nan_total > 50:
            statut = "inutilisable"
        elif abs(skew) > 2:
            statut = "à_transformer"
        else:
            statut = "ok"

        rows.append({
            "feature": feat,
            "mean": col.mean(),
            "std": col.std(),
            "min": col.min(),
            "max": col.max(),
            "skewness": round(skew, 3),
            "nan_pct": round(nan_total, 1),
            "nan_pct_2017": round(nan_2017, 1),
            "nan_pct_2022": round(nan_2022, 1),
            "zero_pct": round(zero_pct, 1),
            "statut": statut,
        })

    audit = pd.DataFrame(rows).set_index("feature")
    audit.to_csv(ANALYSIS / "audit_features.csv")
    print(f"  -> {ANALYSIS / 'audit_features.csv'}")

    inutilisables = audit[audit["statut"] == "inutilisable"].index.tolist()
    a_transformer = audit[audit["statut"] == "à_transformer"].index.tolist()

    print(f"  {len(features)} features analysées")
    if inutilisables:
        print(f"  Inutilisables (>50% NaN): {inutilisables}")
    else:
        print("  Aucune feature inutilisable")
    print(f"  À transformer (|skewness|>2): {len(a_transformer)} features")
    for f in a_transformer[:10]:
        print(f"    - {f} (skew={audit.loc[f, 'skewness']:.2f})")
    if len(a_transformer) > 10:
        print(f"    ... et {len(a_transformer) - 10} autres")
    print()

    return audit


# ===========================================================================
# Étape 2 — Corrélations
# ===========================================================================

def analyse_correlations(df: pd.DataFrame, features: list, cibles: list) -> None:
    print("=== Étape 2 — Corrélations ===")

    cols_dispo = [f for f in features + cibles if f in df.columns]
    corr_all = df[cols_dispo].corr()
    corr_targets = corr_all.loc[
        [f for f in features if f in corr_all.index],
        [c for c in cibles if c in corr_all.columns],
    ]
    corr_targets.to_csv(ANALYSIS / "correlations_targets.csv")
    print(f"  -> {ANALYSIS / 'correlations_targets.csv'}")

    # Top 5 features par cible
    for cible in cibles:
        if cible not in corr_targets.columns:
            continue
        top = corr_targets[cible].abs().nlargest(5)
        print(f"  {cible}:")
        for feat, _ in top.items():
            r = corr_targets.loc[feat, cible]
            print(f"    {feat}: r={r:.3f}")

    print()

    # Heatmap features × cibles
    n_features = len(corr_targets)
    fig_h = max(8, n_features * 0.2)
    plt.figure(figsize=(10, fig_h))
    sns.heatmap(
        corr_targets,
        center=0, cmap="RdBu_r", vmin=-1, vmax=1,
        linewidths=0.3, cbar_kws={"shrink": 0.6},
        yticklabels=True,
    )
    plt.title("Corrélations Pearson : features × familles politiques")
    plt.tight_layout()
    plt.savefig(ANALYSIS / "correlation_heatmap.png", dpi=120)
    plt.close()
    print(f"  -> {ANALYSIS / 'correlation_heatmap.png'}")

    # Heatmap features × features
    corr_ff = df[[f for f in features if f in df.columns]].corr()
    n = len(corr_ff)
    fig_size = max(10, n * 0.22)
    plt.figure(figsize=(fig_size, fig_size))
    sns.heatmap(
        corr_ff,
        center=0, cmap="RdBu_r", vmin=-1, vmax=1,
        linewidths=0.2, cbar_kws={"shrink": 0.5},
        xticklabels=True, yticklabels=True,
    )
    plt.title("Corrélations Pearson inter-features")
    plt.tight_layout()
    plt.savefig(ANALYSIS / "correlation_features.png", dpi=100)
    plt.close()
    print(f"  -> {ANALYSIS / 'correlation_features.png'}\n")


# ===========================================================================
# Étape 3 — Colinéarité
# ===========================================================================

def analyse_colinearite(df: pd.DataFrame, features: list) -> list:
    print("=== Étape 3 — Colinéarité ===")

    feats_dispo = [f for f in features if f in df.columns]
    corr_mat = df[feats_dispo].corr().fillna(0).abs()

    # Distance = 1 - |r|, clustering par linkage average
    dist_full = 1 - corr_mat.values
    np.fill_diagonal(dist_full, 0)
    np.clip(dist_full, 0, 1, out=dist_full)
    condensed = squareform(dist_full, checks=False)
    linkage = hierarchy.average(condensed)

    # Dendrogram
    n = len(feats_dispo)
    plt.figure(figsize=(max(14, n * 0.32), 8))
    hierarchy.dendrogram(
        linkage,
        labels=feats_dispo,
        leaf_rotation=90,
        leaf_font_size=max(5, min(9, 350 // n)),
        color_threshold=0.15,
    )
    plt.axhline(y=0.15, color="red", linestyle="--", linewidth=1.2, label="|r|=0.85")
    plt.title("Dendrogramme de colinéarité (linkage average, distance = 1-|r|)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(ANALYSIS / "dendrogram.png", dpi=120)
    plt.close()
    print(f"  -> {ANALYSIS / 'dendrogram.png'}")

    # Clusters au seuil distance < 0.15 (|r| > 0.85)
    labels = hierarchy.fcluster(linkage, t=0.15, criterion="distance")
    clusters = pd.Series(labels, index=feats_dispo)

    retenues = []
    nb_eliminees = 0
    for cluster_id in sorted(clusters.unique()):
        membres = clusters[clusters == cluster_id].index.tolist()
        if len(membres) == 1:
            retenues.append(membres[0])
        else:
            membres_tries = sorted(membres, key=_priorite_feature)
            gagnant = membres_tries[0]
            retenues.append(gagnant)
            nb_eliminees += len(membres) - 1
            print(f"  Cluster {cluster_id}: garde '{gagnant}', élimine {membres_tries[1:]}")

    print(f"  {clusters.nunique()} clusters, {nb_eliminees} features éliminées pour colinéarité")
    print(f"  {len(retenues)} features retenues\n")
    return retenues


# ===========================================================================
# Étape 4 — Imputation
# ===========================================================================

def imputer(df: pd.DataFrame) -> pd.DataFrame:
    print("=== Étape 4 — Imputation ===")
    df = df.copy()

    def _mediane_dep(serie, dep_serie, annee_serie):
        mediane = serie.groupby([dep_serie, annee_serie]).transform("median")
        return mediane.fillna(serie.median())

    # TP6021 (~20% NaN) — médiane départementale
    if "TP6021" in df.columns:
        n_nan = int(df["TP6021"].isna().sum())
        if n_nan > 0:
            df["TP6021"] = df["TP6021"].fillna(
                _mediane_dep(df["TP6021"], df["DEP"], df["annee"])
            )
            print(f"  TP6021: {n_nan} valeurs imputées (médiane départementale)")
        else:
            print("  TP6021: aucun NaN")

    # crim_stupefiants (~13% NaN) — médiane départementale
    if "crim_stupefiants" in df.columns:
        n_nan = int(df["crim_stupefiants"].isna().sum())
        if n_nan > 0:
            df["crim_stupefiants"] = df["crim_stupefiants"].fillna(
                _mediane_dep(df["crim_stupefiants"], df["DEP"], df["annee"])
            )
            print(f"  crim_stupefiants: {n_nan} valeurs imputées (médiane départementale)")
        else:
            print("  crim_stupefiants: aucun NaN")

    # Revenus (~3% NaN) — MICE avec fallback médiane départementale
    cols_revenus = [c for c in FEATURES_REVENUS if c in df.columns]
    cols_avec_nan = [c for c in cols_revenus if df[c].isna().any()]

    if cols_avec_nan:
        n_nan_avant = {c: int(df[c].isna().sum()) for c in cols_avec_nan}
        try:
            imp_mice = IterativeImputer(
                estimator=BayesianRidge(),
                max_iter=10,
                random_state=42,
                verbose=0,
            )
            df[cols_revenus] = imp_mice.fit_transform(df[cols_revenus])
            print(f"  Revenus (MICE): imputé {list(n_nan_avant.keys())}")
            for col, n in n_nan_avant.items():
                print(f"    {col}: {n} valeurs imputées")
        except Exception as e:
            print(f"  MICE échoué ({e}), fallback médiane départementale")
            for col in cols_avec_nan:
                n_nan = int(df[col].isna().sum())
                df[col] = df[col].fillna(
                    _mediane_dep(df[col], df["DEP"], df["annee"])
                )
                print(f"    {col}: {n_nan} valeurs imputées")
    else:
        print("  Revenus: aucun NaN")

    # Vérification complétude sur colonnes numériques
    cols_num = df.select_dtypes(include="number").columns
    restants = df[cols_num].isna().sum()
    restants = restants[restants > 0]
    if len(restants) == 0:
        print("  Complétude 100% sur toutes les features numériques")
    else:
        print(f"  NaN résiduels:\n{restants.to_string()}")
    print()

    return df


# ===========================================================================
# Étape 5 — Feature engineering avancé
# ===========================================================================

def _valider_composite(
    df: pd.DataFrame, nom: str, composants: list, cibles: list
) -> bool:
    """Retourne True si le composite apporte un gain MI moyen > 5% vs ses composants."""
    composants_dispo = [c for c in composants if c in df.columns]
    if not composants_dispo:
        return False

    gains = []
    for cible in cibles:
        if cible not in df.columns:
            continue
        mask = df[nom].notna() & df[cible].notna()
        if mask.sum() < 100:
            continue
        X_comp = df.loc[mask, [nom]]
        y = df.loc[mask, cible].values

        mi_comp = mutual_info_regression(X_comp, y, random_state=42)[0]
        mi_base = max(
            mutual_info_regression(df.loc[mask, [c]], y, random_state=42)[0]
            for c in composants_dispo
        )
        if mi_base > 0:
            gains.append((mi_comp - mi_base) / mi_base)

    gain_moyen = float(np.mean(gains)) if gains else 0.0
    print(f"    gain MI moyen = {gain_moyen:+.1%} vs composants", end="")
    return gain_moyen > 0.05


def feature_engineering_avance(df: pd.DataFrame, cibles: list) -> pd.DataFrame:
    print("=== Étape 5 — Feature engineering avancé ===")
    df = df.copy()
    scaler = MinMaxScaler()
    composites_retenus = []

    # 1. Indice de précarité (Piketty, Michelat & Simon)
    comps = ["taux_chomage", "TP6021", "pct_sans_diplome"]
    if all(c in df.columns for c in comps):
        normalized = scaler.fit_transform(df[comps].fillna(0))
        df["indice_precarite"] = normalized.mean(axis=1)
        print(f"  indice_precarite = mean(normalize({comps}))")
        if _valider_composite(df, "indice_precarite", comps, cibles):
            composites_retenus.append("indice_precarite")
            print(" -> RETENU")
        else:
            df.drop(columns=["indice_precarite"], inplace=True)
            print(" -> ÉCARTÉ")

    # 2. Tension emploi — proxy désindustrialisation (Piketty)
    comps = ["taux_chomage", "pct_emploi_indus"]
    if all(c in df.columns for c in comps):
        df["tension_emploi"] = df["taux_chomage"] * df["pct_emploi_indus"]
        print(f"  tension_emploi = taux_chomage × pct_emploi_indus")
        if _valider_composite(df, "tension_emploi", comps, cibles):
            composites_retenus.append("tension_emploi")
            print(" -> RETENU")
        else:
            df.drop(columns=["tension_emploi"], inplace=True)
            print(" -> ÉCARTÉ")

    # 3. Densité de services — proxy enclavement (Siegfried)
    cols_bpe = [c for c in df.columns if "BPE" in c.upper() or c.startswith("NB_")]
    if cols_bpe and "P_POP" in df.columns:
        df["densite_services"] = (
            df[cols_bpe].sum(axis=1) / df["P_POP"].replace(0, np.nan) * 1000
        )
        print(f"  densite_services = sum({cols_bpe[:2]}...) / P_POP × 1000")
        if _valider_composite(df, "densite_services", cols_bpe, cibles):
            composites_retenus.append("densite_services")
            print(" -> RETENU")
        else:
            df.drop(columns=["densite_services"], inplace=True)
            print(" -> ÉCARTÉ")
    else:
        print("  densite_services: pas de colonnes BPE disponibles → ignoré")

    # 4. Pression associative relative
    comps = ["densite_associative", "taux_chomage"]
    if all(c in df.columns for c in comps):
        df["pression_associative_rel"] = (
            df["densite_associative"] / (df["taux_chomage"] + 1)
        )
        print(f"  pression_associative_rel = densite_associative / (taux_chomage + 1)")
        if _valider_composite(df, "pression_associative_rel", comps, cibles):
            composites_retenus.append("pression_associative_rel")
            print(" -> RETENU")
        else:
            df.drop(columns=["pression_associative_rel"], inplace=True)
            print(" -> ÉCARTÉ")

    print(f"\n  {len(composites_retenus)} composites retenus: {composites_retenus}\n")
    return df


# ===========================================================================
# Étape 6 — Transformations log(1+x)
# ===========================================================================

def transformer(
    df: pd.DataFrame, audit: pd.DataFrame, features: list
) -> tuple:
    print("=== Étape 6 — Transformations log(1+x) ===")
    df = df.copy()
    features_actualisees = list(features)

    # Candidats : skewness > 2, non bornés [0,100], min >= 0
    a_transformer = [
        f for f in audit[audit["statut"] == "à_transformer"].index.tolist()
        if f in features
        and not f.startswith(("taux_", "pct_", "solde_"))
        and f in df.columns
        and df[f].min() >= 0
    ]

    nb_transformees = 0
    for feat in a_transformer:
        skew_avant = float(stats.skew(df[feat].dropna()))
        new_col = f"log1p_{feat}"
        df[new_col] = np.log1p(df[feat])
        skew_apres = float(stats.skew(df[new_col].dropna()))

        if abs(skew_apres) < abs(skew_avant) * 0.7:
            features_actualisees = [
                new_col if f == feat else f for f in features_actualisees
            ]
            df.drop(columns=[feat], inplace=True)
            nb_transformees += 1
            print(f"  {feat} → {new_col}  (skew {skew_avant:.2f} → {skew_apres:.2f})")
        else:
            df.drop(columns=[new_col], inplace=True)
            print(f"  {feat}: ignoré (gain insuffisant, skew={skew_avant:.2f})")

    print(f"  {nb_transformees} features transformées\n")
    return df, features_actualisees


# ===========================================================================
# Étape 7 — Sélection finale
# ===========================================================================

def selection_finale(
    df: pd.DataFrame, features: list, cibles: list
) -> pd.DataFrame:
    print("=== Étape 7 — Sélection finale ===")

    feats_dispo = [f for f in features if f in df.columns]
    cibles_dispo = [c for c in cibles if c in df.columns]

    # Filtre statistique : MI moyen vs toutes les cibles
    X = df[feats_dispo].fillna(0).values
    mi_par_cible = {}
    for cible in cibles_dispo:
        y = df[cible].fillna(df[cible].median()).values
        mi_par_cible[cible] = mutual_info_regression(X, y, random_state=42)

    mi_moyen = {}
    for i, feat in enumerate(feats_dispo):
        scores = [mi_par_cible[c][i] for c in cibles_dispo]
        mi_moyen[feat] = float(np.mean(scores))

    seuil_mi = 0.01
    exclues_stat = [f for f, mi in mi_moyen.items() if mi < seuil_mi]

    # Forcer la présence des features-clés de la littérature
    litt_dispo = [f for f in FEATURES_LITTERATURE if f in df.columns]
    exclues_stat = [f for f in exclues_stat if f not in litt_dispo]

    if exclues_stat:
        print(f"  Exclues (MI < {seuil_mi}): {exclues_stat}")

    features_finales = [f for f in feats_dispo if f not in exclues_stat]

    print(f"  {len(feats_dispo)} features → {len(features_finales)} retenues")
    print(f"  Liste finale:\n    " + "\n    ".join(sorted(features_finales)))

    # Sauvegarder
    identifiants = ["CODGEO", "annee", "lib_commune", "DEP", "REG"]
    auxiliaires = ["taux_abstention", "taux_blancs_nuls"]
    cols_finales = (
        [c for c in identifiants if c in df.columns]
        + [c for c in cibles if c in df.columns]
        + features_finales
        + [c for c in auxiliaires if c in df.columns and c not in features_finales]
    )
    # Dédupliquer en conservant l'ordre
    seen = set()
    cols_finales = [c for c in cols_finales if not (c in seen or seen.add(c))]

    output = df[cols_finales].copy()
    output_path = PROCESSED / "features_final.parquet"
    output.to_parquet(output_path, index=False)
    size_mb = output_path.stat().st_size / 1e6

    nan_final = output[features_finales].isna().sum().sum()
    print(f"\n  Sauvegardé : {output_path}")
    print(f"  Shape : {output.shape[0]} lignes × {output.shape[1]} colonnes ({size_mb:.1f} Mo)")
    print(f"  NaN features finales : {nan_final}")
    print()

    return output


# ===========================================================================
# Main
# ===========================================================================

def main():
    print("Phase 4 — Analyse exploratoire & feature engineering avancé")
    print(f"Source : {PROCESSED / 'table_analytique.parquet'}")
    print(f"Cible  : {PROCESSED / 'features_final.parquet'}\n")

    # Chargement
    print("Chargement de la table analytique...")
    df = pd.read_parquet(PROCESSED / "table_analytique.parquet")
    print(f"  {df.shape[0]} lignes × {df.shape[1]} colonnes\n")

    # Calcul des cibles si absentes (Phase 3 bug potentiel)
    df = preparer_cibles(df)

    # Déterminer les features candidates : numériques, hors exclusions
    toutes = set(df.columns)
    features = sorted([
        c for c in toutes
        if c not in EXCLURE
        and pd.api.types.is_numeric_dtype(df[c])
    ])
    print(f"  {len(features)} features numériques candidates\n")

    # Étape 1 — Audit
    audit = audit_features(df, features)
    features = [f for f in features if audit.loc[f, "statut"] != "inutilisable"]

    # Étape 2 — Corrélations
    analyse_correlations(df, features, CIBLES)

    # Étape 3 — Colinéarité
    features = analyse_colinearite(df, features)

    # Étape 4 — Imputation
    df = imputer(df)

    # Étape 5 — Feature engineering avancé
    df = feature_engineering_avance(df, CIBLES)
    composites = [
        c for c in [
            "indice_precarite", "tension_emploi",
            "densite_services", "pression_associative_rel",
        ]
        if c in df.columns
    ]
    features = features + composites

    # Étape 6 — Transformations
    df, features = transformer(df, audit, features)

    # Étape 7 — Sélection finale
    selection_finale(df, features, CIBLES)

    print("=" * 60)
    print("Phase 4 terminée.")
    print(f"Rapport : {ANALYSIS}/")
    print(f"Output  : {PROCESSED / 'features_final.parquet'}")


if __name__ == "__main__":
    main()
