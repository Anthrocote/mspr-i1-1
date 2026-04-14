#!/usr/bin/env python3 -u
"""
Usage:
    python -u scripts/01_extract_columns.py
"""

import sys
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
STAGING = Path(__file__).resolve().parent.parent / "data" / "staging"
STAGING.mkdir(parents=True, exist_ok=True)


def extract_elections_general():
    print("=== Élections general_results ===")
    cols = [
        "id_election",
        "code_commune",
        "libelle_commune",
        "code_bv",
        "inscrits",
        "abstentions",
        "votants",
        "blancs",
        "nuls",
        "exprimes",
    ]
    df = pd.read_parquet(RAW / "elections" / "general_results.parquet", columns=cols)
    df = df[df["id_election"].str.contains("pres_t1")]
    print(
        f"  {df.shape[0]} lignes, {df['code_commune'].nunique()} communes, elections: {sorted(df['id_election'].unique())}"
    )
    df.to_parquet(STAGING / "elections_general_pres_t1.parquet", index=False)
    print(f"  -> {STAGING / 'elections_general_pres_t1.parquet'}")


# Élections (candidats_results)
def extract_elections_candidats():
    print("=== Élections candidats_results ===")
    cols = [
        "id_election",
        "code_commune",
        "code_bv",
        "voix",
        "nom",
        "prenom",
        "nuance",
    ]
    df = pd.read_parquet(RAW / "elections" / "candidats_results.parquet", columns=cols)
    df = df[df["id_election"].str.contains("pres_t1")]
    print(f"  {df.shape[0]} lignes, {df['code_commune'].nunique()} communes")
    df.to_parquet(STAGING / "elections_candidats_pres_t1.parquet", index=False)
    print(f"  -> {STAGING / 'elections_candidats_pres_t1.parquet'}")


# Dossier Complet
def extract_dossier_complet():
    print("=== Dossier Complet ===")

    # Colonnes P22/C22 retenues
    cols_p22_c22 = [
        "CODGEO",
        # Population / âge
        "P22_POP",
        "P22_POP0014",
        "P22_POP1529",
        "P22_POP3044",
        "P22_POP4559",
        "P22_POP6074",
        "P22_POP7589",
        "P22_POP90P",
        # Diplômes
        "P22_NSCOL15P",
        "P22_NSCOL15P_DIPLMIN",
        "P22_NSCOL15P_BEPC",
        "P22_NSCOL15P_CAPBEP",
        "P22_NSCOL15P_BAC",
        "P22_NSCOL15P_SUP2",
        "P22_NSCOL15P_SUP34",
        "P22_NSCOL15P_SUP5",
        # Emploi / chômage / CSP
        "P22_POP1564",
        "P22_ACT1564",
        "P22_ACTOCC1564",
        "P22_CHOM1564",
        "P22_INACT1564",
        "P22_RETR1564",
        "P22_ETUD1564",
        "P22_EMPLT",
        "C22_ACTOCC1564_STAT_GSEC11",
        "C22_ACTOCC1564_STAT_GSEC12",
        "C22_ACTOCC1564_STAT_GSEC13",
        "C22_ACTOCC1564_STAT_GSEC14",
        "C22_ACTOCC1564_STAT_GSEC15",
        "C22_ACTOCC1564_STAT_GSEC16",
        "C22_EMPLT_AGRI",
        "C22_EMPLT_INDUS",
        "C22_EMPLT_CONST",
        "C22_EMPLT_CTS",
        "C22_EMPLT_APESAS",
        "P22_ACTOCC15P_VOITURE",
        "P22_ACTOCC15P_COMMUN",
        # Logement
        "P22_LOG",
        "P22_RP",
        "P22_LOGVAC",
        "P22_RSECOCC",
        "P22_MAISON",
        "P22_APPART",
        "P22_RP_PROP",
        "P22_RP_LOC",
        "P22_RP_LOCHLMV",
        "P22_RP_VOIT1P",
        # Familles / ménages
        "C22_MEN",
        "C22_MENPSEUL",
        "C22_MENCOUPSENF",
        "C22_MENCOUPAENF",
        "C22_MENFAMMONO",
        "P22_POP15P_MARIEE",
        "P22_POP15P_CELIBATAIRE",
        # Revenus / pauvreté
        "NBMENFISC21",
        "MED21",
        "PIMP21",
        "TP6021",
        "D121",
        "D921",
        "RD21",
        "PACT21",
        "PPEN21",
        "PPSOC21",
        # Salaires
        "SNEMM_23",
        # Naissances / décès
        "NAISD17",
        "DECESD17",
        "NAISD22",
        "DECESD22",
        # Établissements
        "ETTOT24",
        "ETPOQ24",
        "ETPPRESPUB24",
        "ETPNPRESPUB24",
    ]

    # Colonnes BPE (toutes)
    # On les detectera dynamiquement
    all_cols = pd.read_csv(
        RAW / "recensement" / "dossier_complet" / "dossier_complet.csv",
        sep=";",
        nrows=0,
    ).columns.tolist()
    bpe_cols = [c for c in all_cols if c.startswith("BPE_")]

    # Equivalents P16/C16
    # Le nommage change entre millésimes, on les liste explicitement
    cols_p16_c16 = [
        # Population / âge
        "P16_POP",
        "P16_POP0014",
        "P16_POP1529",
        "P16_POP3044",
        "P16_POP4559",
        "P16_POP6074",
        "P16_POP7589",
        "P16_POP90P",
        # Diplômes (grille simplifiée : pas de BEPC, SUP non découpe)
        "P16_NSCOL15P",
        "P16_NSCOL15P_DIPLMIN",
        "P16_NSCOL15P_CAPBEP",
        "P16_NSCOL15P_BAC",
        "P16_NSCOL15P_SUP",
        # Emploi / chômage / CSP (CS1..CS6 au lieu de GSEC)
        "P16_POP1564",
        "P16_ACT1564",
        "P16_ACTOCC1564",
        "P16_CHOM1564",
        "P16_INACT1564",
        "P16_RETR1564",
        "P16_ETUD1564",
        "P16_EMPLT",
        "C16_ACTOCC1564_CS1",
        "C16_ACTOCC1564_CS2",
        "C16_ACTOCC1564_CS3",
        "C16_ACTOCC1564_CS4",
        "C16_ACTOCC1564_CS5",
        "C16_ACTOCC1564_CS6",
        "C16_EMPLT_AGRI",
        "C16_EMPLT_INDUS",
        "C16_EMPLT_CONST",
        "C16_EMPLT_CTS",
        "C16_EMPLT_APESAS",
        "P16_ACTOCC15P_VOITURE",
        "P16_ACTOCC15P_COMMUN",
        # Logement
        "P16_LOG",
        "P16_RP",
        "P16_LOGVAC",
        "P16_RSECOCC",
        "P16_MAISON",
        "P16_APPART",
        "P16_RP_PROP",
        "P16_RP_LOC",
        "P16_RP_LOCHLMV",
        "P16_RP_VOIT1P",
        # Familles / ménages
        "C16_MEN",
        "C16_MENPSEUL",
        "C16_MENCOUPSENF",
        "C16_MENCOUPAENF",
        "C16_MENFAMMONO",
        "P16_POP15P_MARIEE",
        "P16_POP15P_NONMARIEE",
    ]
    # Ne garder que celles qui existent
    cols_p16_c16 = [c for c in cols_p16_c16 if c in all_cols]

    final_cols = cols_p22_c22 + bpe_cols + cols_p16_c16
    final_cols = [c for c in final_cols if c in all_cols]
    missing = [c for c in cols_p22_c22 if c not in all_cols and c != "CODGEO"]
    if missing:
        print(f"  ATTENTION colonnes absentes: {missing}")

    print(f"  Chargement de {len(final_cols)} colonnes sur {len(all_cols)}...")
    df = pd.read_csv(
        RAW / "recensement" / "dossier_complet" / "dossier_complet.csv",
        sep=";",
        usecols=final_cols,
        low_memory=False,
    )
    print(f"  {df.shape[0]} lignes x {df.shape[1]} colonnes")
    df.to_parquet(STAGING / "dossier_complet_extract.parquet", index=False)
    print(f"  -> {STAGING / 'dossier_complet_extract.parquet'}")


# Criminalité
def extract_crimes():
    print("=== Criminalité ===")
    cols = [
        "CODGEO_2024",
        "annee",
        "indicateur",
        "nombre",
        "taux_pour_mille",
        "est_diffuse",
    ]
    df = pd.read_parquet(
        RAW
        / "criminalite"
        / "donnee-comm-data.gouv-parquet-2024-geographie2024-produit-le2025-03-14.parquet",
        columns=cols,
    )
    # Garder les années pertinentes pour scrutins 2017 et 2022
    df = df[df["annee"].isin([2016, 2017, 2021, 2022])]
    print(f"  {df.shape[0]} lignes, {df['CODGEO_2024'].nunique()} communes")
    df.to_parquet(STAGING / "criminalite.parquet", index=False)
    print(f"  -> {STAGING / 'criminalite.parquet'}")

    # Fallback départemental
    dep_files = sorted(RAW.glob("criminalite/donnee-dep-*.csv"))
    if dep_files:
        dep = pd.read_csv(dep_files[0], sep=";", low_memory=False)
        print(f"  Fallback départemental: {dep.shape[0]} lignes")
        dep.to_parquet(STAGING / "criminalite_dep.parquet", index=False)
        print(f"  -> {STAGING / 'criminalite_dep.parquet'}")


# Immigration
def extract_immigration():
    print("=== Immigration ===")

    # IMG1A
    img = pd.read_csv(
        RAW / "recensement" / "TD_IMG1A_2022_csv" / "TD_IMG1A_2022.csv",
        sep=";",
        low_memory=False,
    )
    img = img[["CODGEO", "IMMI", "NB"]]
    print(f"  IMG1A: {img.shape[0]} lignes")
    img.to_parquet(STAGING / "immigres.parquet", index=False)
    print(f"  -> {STAGING / 'immigres.parquet'}")

    # NAT1
    nat = pd.read_csv(
        RAW / "recensement" / "TD_NAT1_2022_csv" / "TD_NAT1_2022.csv",
        sep=";",
        low_memory=False,
    )
    nat = nat[["CODGEO", "INATC", "NB"]]
    print(f"  NAT1: {nat.shape[0]} lignes")
    nat.to_parquet(STAGING / "etrangers.parquet", index=False)
    print(f"  -> {STAGING / 'etrangers.parquet'}")


# RNA (Associations)
def extract_rna():
    print("=== RNA ===")
    # Prendre le snapshot waldec le plus récent
    waldec_dirs = sorted(RAW.glob("associations/rna_waldec_*"))
    waldec_dirs = [d for d in waldec_dirs if d.is_dir()]
    if not waldec_dirs:
        print("  ERREUR: aucun dossier rna_waldec trouvé")
        return
    latest = waldec_dirs[-1]
    print(f"  Snapshot: {latest.name}")

    dfs = []
    csv_files = sorted(latest.glob("*.csv"))
    for f in csv_files:
        df = pd.read_csv(
            f,
            sep=";",
            usecols=["adrs_codeinsee", "date_creat", "date_disso"],
            low_memory=False,
        )
        dfs.append(df)
    rna = pd.concat(dfs, ignore_index=True)
    # Forcer adrs_codeinsee en string (types mixtes dans les CSV)
    rna["adrs_codeinsee"] = rna["adrs_codeinsee"].astype(str).str.zfill(5)
    print(f"  {rna.shape[0]} associations, {rna['adrs_codeinsee'].nunique()} communes")
    rna.to_parquet(STAGING / "rna.parquet", index=False)
    print(f"  -> {STAGING / 'rna.parquet'}")


# Référentiels
def extract_referentiels():
    print("=== Référentiels ===")

    # Communes
    comm = pd.read_csv(RAW / "referentiels" / "v_commune_2025.csv")
    comm = comm[["COM", "DEP", "REG", "LIBELLE", "TYPECOM"]]
    comm.to_parquet(STAGING / "ref_communes.parquet", index=False)
    print(f"  Communes: {comm.shape[0]} lignes -> ref_communes.parquet")

    # Départements
    dept = pd.read_csv(RAW / "referentiels" / "v_departement_2025.csv")
    dept = dept[["DEP", "REG", "LIBELLE"]]
    dept.to_parquet(STAGING / "ref_departements.parquet", index=False)
    print(f"  Départements: {dept.shape[0]} lignes -> ref_departements.parquet")

    # Régions
    reg = pd.read_csv(RAW / "referentiels" / "v_region_2025.csv")
    reg = reg[["REG", "LIBELLE"]]
    reg.to_parquet(STAGING / "ref_regions.parquet", index=False)
    print(f"  Régions: {reg.shape[0]} lignes -> ref_regions.parquet")

    # Mouvements communes
    mvt = pd.read_csv(RAW / "referentiels" / "v_mvt_commune_2025.csv")
    mvt.to_parquet(STAGING / "ref_mvt_communes.parquet", index=False)
    print(f"  Mouvements: {mvt.shape[0]} lignes -> ref_mvt_communes.parquet")

    # Grille densité, header row 4 (codes), data from row 5
    gd = pd.read_excel(
        RAW / "referentiels" / "fichier_diffusion_2025.xlsx", header=None, skiprows=4
    )
    header = gd.iloc[0].tolist()
    gd = gd.iloc[1:].copy()
    gd.columns = header
    gd = gd[["CODGEO", "DENS", "DENS7"]].copy()
    gd = gd.dropna(subset=["CODGEO"])
    gd.to_parquet(STAGING / "ref_densite.parquet", index=False)
    print(f"  Densité: {gd.shape[0]} lignes -> ref_densite.parquet")


if __name__ == "__main__":
    print(f"Extraction vers {STAGING}\n")
    extract_elections_general()
    print()
    extract_elections_candidats()
    print()
    extract_dossier_complet()
    print()
    extract_crimes()
    print()
    extract_immigration()
    print()
    extract_rna()
    print()
    extract_referentiels()
    print("\n=== Terminé ===")
    total_size = sum(f.stat().st_size for f in STAGING.glob("*.parquet"))
    nb_files = len(list(STAGING.glob("*.parquet")))
    print(f"{nb_files} fichiers parquet, {total_size / 1e6:.1f} Mo total")
