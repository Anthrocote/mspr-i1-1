#!/usr/bin/env python3 -u
"""
Export SQL depuis table_analytique.parquet
Génère data/processed/electio_analytics.sql

Usage :
    python -u scripts/05_export_sql.py
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
STAGING = Path(__file__).resolve().parent.parent / "data" / "staging"
OUTPUT = PROCESSED / "electio_analytics.sql"

# Familles et clivages
FAMILLES_CLIVAGES = {
    "gauche_radicale": "clivage de classe (travailleurs), anti-système",
    "social_democratie": "clivage de classe (réformisme)",
    "ecologisme": "post-matérialisme, transition écologique",
    "liberalisme_centre": "synthèse libérale, pro-européen",
    "droite_conservatrice": "clivage de classe (possédants), ordre, tradition",
    "souverainisme": "centre/périphérie, euroscepticisme",
    "droite_nationale": "identitaire, immigration, sécurité",
}

# Candidats -> famille (copie de 02_clean_transform.py pour l'export)
CANDIDAT_FAMILLE = {
    ("BESANCENOT", "OLIVIER"): "gauche_radicale",
    ("LAGUILLER", "ARLETTE"): "gauche_radicale",
    ("GLUCKSTEIN", "DANIEL"): "gauche_radicale",
    ("HUE", "ROBERT"): "gauche_radicale",
    ("BUFFET", "MARIE-GEORGE"): "gauche_radicale",
    ("BOVE", "JOSE"): "gauche_radicale",
    ("SCHIVARDI", "GERARD"): "gauche_radicale",
    ("MELENCHON", "JEAN-LUC"): "gauche_radicale",
    ("ARTHAUD", "NATHALIE"): "gauche_radicale",
    ("POUTOU", "PHILIPPE"): "gauche_radicale",
    ("ROUSSEL", "FABIEN"): "gauche_radicale",
    ("JOSPIN", "LIONEL"): "social_democratie",
    ("TAUBIRA", "CHRISTIANE"): "social_democratie",
    ("CHEVENEMENT", "JEAN-PIERRE"): "social_democratie",
    ("ROYAL", "SEGOLENE"): "social_democratie",
    ("HOLLANDE", "FRANCOIS"): "social_democratie",
    ("HAMON", "BENOIT"): "social_democratie",
    ("HIDALGO", "ANNE"): "social_democratie",
    ("MAMERE", "NOEL"): "ecologisme",
    ("VOYNET", "DOMINIQUE"): "ecologisme",
    ("JOLY", "EVA"): "ecologisme",
    ("JADOT", "YANNICK"): "ecologisme",
    ("BAYROU", "FRANCOIS"): "liberalisme_centre",
    ("MACRON", "EMMANUEL"): "liberalisme_centre",
    ("CHIRAC", "JACQUES"): "droite_conservatrice",
    ("MADELIN", "ALAIN"): "droite_conservatrice",
    ("BOUTIN", "CHRISTINE"): "droite_conservatrice",
    ("SARKOZY", "NICOLAS"): "droite_conservatrice",
    ("FILLON", "FRANCOIS"): "droite_conservatrice",
    ("PECRESSE", "VALERIE"): "droite_conservatrice",
    ("SAINT-JOSSE", "JEAN"): "souverainisme",
    ("LEPAGE", "CORINNE"): "souverainisme",
    ("DE VILLIERS", "PHILIPPE"): "souverainisme",
    ("NIHOUS", "FREDERIC"): "souverainisme",
    ("DUPONT-AIGNAN", "NICOLAS"): "souverainisme",
    ("ASSELINEAU", "FRANCOIS"): "souverainisme",
    ("LASSALLE", "JEAN"): "souverainisme",
    ("CHEMINADE", "JACQUES"): "souverainisme",
    ("LE PEN", "JEAN-MARIE"): "droite_nationale",
    ("MEGRET", "BRUNO"): "droite_nationale",
    ("LE PEN", "MARINE"): "droite_nationale",
    ("ZEMMOUR", "ERIC"): "droite_nationale",
}

SCRUTINS = [
    {"id": 1, "type": "presidentielle", "tour": 1, "date": "2017-04-23"},
    {"id": 2, "type": "presidentielle", "tour": 1, "date": "2022-04-10"},
]
SCRUTIN_MAP = {"2017": 1, "2022": 2}

# Colonnes du profil socio-économique exportées dans observation
SOCIO_COLS = [
    "taux_abstention",
    "taux_blancs_nuls",
    "taux_chomage",
    "taux_activite",
    "pct_diplome_sup",
    "pct_sans_diplome",
    "pct_cadres",
    "pct_ouvriers",
    "taux_logements_vacants",
    "pct_proprietaires",
    "pct_hlm",
    "pct_menages_seuls",
    "pct_familles_mono",
    "densite_associative",
    "solde_naturel",
    "pct_emploi_agri",
    "pct_emploi_indus",
    "pct_emploi_const",
    "pct_emploi_services",
    "pct_emploi_public",
    "pct_immigres",
    "crim_violences",
    "crim_atteintes_biens",
    "crim_stupefiants",
    "MED21",
    "TP6021",
    "D121",
    "D921",
    "RD21",
    "PIMP21",
    "PACT21",
    "PPEN21",
    "PPSOC21",
]


# --------------------------------------------------------------------------- #
# Helpers SQL
# --------------------------------------------------------------------------- #


def sql_val(v):
    """Formate une valeur Python en littéral SQL."""
    if v is None:
        return "NULL"
    if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
        return "NULL"
    if isinstance(v, np.floating):
        if np.isnan(float(v)) or np.isinf(float(v)):
            return "NULL"
        return f"{float(v):.6f}"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, float):
        return f"{v:.6f}"
    # str
    return "'" + str(v).replace("'", "''") + "'"


def build_inserts(table_name, rows, chunk=500):
    """Génère des INSERT…VALUES groupés par chunks."""
    if not rows:
        return ""
    cols = "(" + ", ".join(rows[0].keys()) + ")"
    parts = []
    for i in range(0, len(rows), chunk):
        batch = rows[i : i + chunk]
        vals = ",\n    ".join(
            "(" + ", ".join(sql_val(v) for v in r.values()) + ")" for r in batch
        )
        parts.append(f"INSERT INTO {table_name} {cols} VALUES\n    {vals};")
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Schéma DDL
# --------------------------------------------------------------------------- #

DDL = """\
CREATE TABLE region (
    code    VARCHAR(3)  PRIMARY KEY,
    nom     VARCHAR(100) NOT NULL
);

CREATE TABLE departement (
    code        VARCHAR(3)   PRIMARY KEY,
    nom         VARCHAR(100) NOT NULL,
    code_region VARCHAR(3)   NOT NULL REFERENCES region(code)
);

CREATE TABLE commune (
    code             VARCHAR(5)   PRIMARY KEY,
    nom              VARCHAR(150) NOT NULL,
    population       INTEGER,
    code_departement VARCHAR(3)   NOT NULL REFERENCES departement(code)
);

CREATE TABLE scrutin (
    id    INTEGER      PRIMARY KEY,
    type  VARCHAR(50)  NOT NULL,
    tour  INTEGER      NOT NULL,
    date  DATE         NOT NULL
);

CREATE TABLE famille_politique (
    code             VARCHAR(30)  PRIMARY KEY,
    nom              VARCHAR(60)  NOT NULL,
    clivage_dominant VARCHAR(200) NOT NULL
);

CREATE TABLE candidat (
    id           INTEGER      PRIMARY KEY,
    nom          VARCHAR(100) NOT NULL,
    prenom       VARCHAR(100) NOT NULL,
    code_famille VARCHAR(30)  NOT NULL REFERENCES famille_politique(code)
);

CREATE TABLE observation (
    id                       INTEGER      PRIMARY KEY,
    code_commune             VARCHAR(5)   NOT NULL REFERENCES commune(code),
    id_scrutin               INTEGER      NOT NULL REFERENCES scrutin(id),
    -- participation
    inscrits                 INTEGER,
    votants                  INTEGER,
    abstentions              INTEGER,
    blancs                   INTEGER,
    nuls                     INTEGER,
    exprimes                 INTEGER,
    -- profil socio-économique
    taux_abstention          DECIMAL(6,2),
    taux_blancs_nuls         DECIMAL(6,2),
    taux_chomage             DECIMAL(6,2),
    taux_activite            DECIMAL(6,2),
    pct_diplome_sup          DECIMAL(6,2),
    pct_sans_diplome         DECIMAL(6,2),
    pct_cadres               DECIMAL(6,2),
    pct_ouvriers             DECIMAL(6,2),
    taux_logements_vacants   DECIMAL(6,2),
    pct_proprietaires        DECIMAL(6,2),
    pct_hlm                  DECIMAL(6,2),
    pct_menages_seuls        DECIMAL(6,2),
    pct_familles_mono        DECIMAL(6,2),
    densite_associative      DECIMAL(8,2),
    solde_naturel            DECIMAL(8,2),
    pct_emploi_agri          DECIMAL(6,2),
    pct_emploi_indus         DECIMAL(6,2),
    pct_emploi_const         DECIMAL(6,2),
    pct_emploi_services      DECIMAL(6,2),
    pct_emploi_public        DECIMAL(6,2),
    pct_immigres             DECIMAL(6,2),
    crim_violences           DECIMAL(8,4),
    crim_atteintes_biens     DECIMAL(8,4),
    crim_stupefiants         DECIMAL(8,4),
    revenu_median            DECIMAL(10,2),
    taux_pauvrete            DECIMAL(6,2),
    d1_revenu                DECIMAL(10,2),
    d9_revenu                DECIMAL(10,2),
    rapport_interdecile      DECIMAL(6,2),
    part_revenus_activite    DECIMAL(6,2),
    part_revenus_chomage     DECIMAL(6,2),
    part_revenus_retraite    DECIMAL(6,2),
    part_prestations_sociales DECIMAL(6,2),
    UNIQUE (code_commune, id_scrutin)
);

CREATE TABLE resultat (
    id_observation  INTEGER     NOT NULL REFERENCES observation(id),
    code_famille    VARCHAR(30) NOT NULL REFERENCES famille_politique(code),
    voix            INTEGER     NOT NULL DEFAULT 0,
    pourcentage     DECIMAL(6,2),
    PRIMARY KEY (id_observation, code_famille)
);
"""


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def main():
    print("Phase 5 — Export SQL")
    print(f"Source : {PROCESSED}")
    print(f"Sortie  : {OUTPUT}\n")

    # Chargement
    print("Chargement des parquets...")
    table = pd.read_parquet(PROCESSED / "table_analytique.parquet")
    regions_df = pd.read_parquet(STAGING / "ref_regions.parquet")
    depts_df = pd.read_parquet(STAGING / "ref_departements.parquet")
    print(f"  table_analytique : {table.shape[0]} lignes x {table.shape[1]} colonnes")

    # Normaliser types
    table["CODGEO"] = table["CODGEO"].astype(str).str.strip()
    table["annee"] = table["annee"].astype(str).str.strip()
    table["DEP"] = table["DEP"].astype(str).str.strip()
    # REG peut être float64 (ex: 84.0) dans la table analytique
    table["REG"] = table["REG"].dropna().apply(lambda x: str(int(float(x))))
    # Remplir les NaN laissés par dropna().apply()
    table["REG"] = table["REG"].fillna("").where(table["REG"].notna(), other=None)
    regions_df["REG"] = regions_df["REG"].apply(lambda x: str(int(x)))
    regions_df["LIBELLE"] = regions_df["LIBELLE"].astype(str).str.strip()
    depts_df["DEP"] = depts_df["DEP"].astype(str).str.strip()
    depts_df["REG"] = depts_df["REG"].apply(lambda x: str(int(x)))
    depts_df["LIBELLE"] = depts_df["LIBELLE"].astype(str).str.strip()

    # Filtrer régions/deps présents dans la table
    regs_used = table["REG"].dropna().unique()
    deps_used = table["DEP"].dropna().unique()
    regions_df = regions_df[regions_df["REG"].isin(regs_used)]
    depts_df = depts_df[depts_df["DEP"].isin(deps_used)]

    # ---- REGION ----
    region_rows = [
        {"code": r["REG"], "nom": r["LIBELLE"]} for _, r in regions_df.iterrows()
    ]
    print(f"  Régions          : {len(region_rows)}")

    # ---- DEPARTEMENT ----
    dept_rows = [
        {"code": r["DEP"], "nom": r["LIBELLE"], "code_region": r["REG"]}
        for _, r in depts_df.iterrows()
    ]
    print(f"  Départements     : {len(dept_rows)}")

    # ---- COMMUNE ----
    communes = (
        table[["CODGEO", "lib_commune", "DEP"]].drop_duplicates(subset="CODGEO").copy()
    )
    # population : prendre le max entre les deux scrutins
    pop = table.groupby("CODGEO")["P_POP"].max().rename("pop").reset_index()
    communes = communes.merge(pop, on="CODGEO", how="left")

    commune_rows = [
        {
            "code": r["CODGEO"],
            "nom": r["lib_commune"] if pd.notna(r["lib_commune"]) else "",
            "population": int(r["pop"]) if pd.notna(r["pop"]) else None,
            "code_departement": r["DEP"],
        }
        for _, r in communes.iterrows()
    ]
    print(f"  Communes         : {len(commune_rows)}")

    # ---- SCRUTIN ----
    scrutin_rows = SCRUTINS
    print(f"  Scrutins         : {len(scrutin_rows)}")

    # ---- FAMILLE_POLITIQUE ----
    famille_rows = [
        {
            "code": code,
            "nom": code.replace("_", " "),
            "clivage_dominant": clivage,
        }
        for code, clivage in FAMILLES_CLIVAGES.items()
    ]
    print(f"  Familles politiques : {len(famille_rows)}")

    # ---- CANDIDAT ----
    candidat_rows = [
        {
            "id": idx + 1,
            "nom": nom,
            "prenom": prenom,
            "code_famille": famille,
        }
        for idx, ((nom, prenom), famille) in enumerate(sorted(CANDIDAT_FAMILLE.items()))
    ]
    print(f"  Candidats        : {len(candidat_rows)}")

    # ---- OBSERVATION + RESULTAT ----
    familles = list(FAMILLES_CLIVAGES.keys())
    observation_rows = []
    resultat_rows = []

    obs_id = 1
    for _, row in table.iterrows():
        sid = SCRUTIN_MAP.get(row["annee"])
        if sid is None:
            continue

        def _int(v):
            return int(v) if pd.notna(v) else None

        def _flt(v):
            if pd.isna(v) or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
                return None
            return float(v)

        obs = {
            "id": obs_id,
            "code_commune": row["CODGEO"],
            "id_scrutin": sid,
            "inscrits": _int(row.get("inscrits")),
            "votants": _int(row.get("votants")),
            "abstentions": _int(row.get("abstentions")),
            "blancs": _int(row.get("blancs")),
            "nuls": _int(row.get("nuls")),
            "exprimes": _int(row.get("exprimes")),
            # profil socio-économique
            "taux_abstention": _flt(row.get("taux_abstention")),
            "taux_blancs_nuls": _flt(row.get("taux_blancs_nuls")),
            "taux_chomage": _flt(row.get("taux_chomage")),
            "taux_activite": _flt(row.get("taux_activite")),
            "pct_diplome_sup": _flt(row.get("pct_diplome_sup")),
            "pct_sans_diplome": _flt(row.get("pct_sans_diplome")),
            "pct_cadres": _flt(row.get("pct_cadres")),
            "pct_ouvriers": _flt(row.get("pct_ouvriers")),
            "taux_logements_vacants": _flt(row.get("taux_logements_vacants")),
            "pct_proprietaires": _flt(row.get("pct_proprietaires")),
            "pct_hlm": _flt(row.get("pct_hlm")),
            "pct_menages_seuls": _flt(row.get("pct_menages_seuls")),
            "pct_familles_mono": _flt(row.get("pct_familles_mono")),
            "densite_associative": _flt(row.get("densite_associative")),
            "solde_naturel": _flt(row.get("solde_naturel")),
            "pct_emploi_agri": _flt(row.get("pct_emploi_agri")),
            "pct_emploi_indus": _flt(row.get("pct_emploi_indus")),
            "pct_emploi_const": _flt(row.get("pct_emploi_const")),
            "pct_emploi_services": _flt(row.get("pct_emploi_services")),
            "pct_emploi_public": _flt(row.get("pct_emploi_public")),
            "pct_immigres": _flt(row.get("pct_immigres")),
            "crim_violences": _flt(row.get("crim_violences")),
            "crim_atteintes_biens": _flt(row.get("crim_atteintes_biens")),
            "crim_stupefiants": _flt(row.get("crim_stupefiants")),
            "revenu_median": _flt(row.get("MED21")),
            "taux_pauvrete": _flt(row.get("TP6021")),
            "d1_revenu": _flt(row.get("D121")),
            "d9_revenu": _flt(row.get("D921")),
            "rapport_interdecile": _flt(row.get("RD21")),
            "part_revenus_activite": _flt(row.get("PIMP21")),
            "part_revenus_chomage": _flt(row.get("PACT21")),
            "part_revenus_retraite": _flt(row.get("PPEN21")),
            "part_prestations_sociales": _flt(row.get("PPSOC21")),
        }
        observation_rows.append(obs)

        exprimes = row.get("exprimes")
        exprimes_val = float(exprimes) if pd.notna(exprimes) and exprimes > 0 else None

        for f in familles:
            voix_raw = row.get(f)
            voix = int(voix_raw) if pd.notna(voix_raw) else 0
            pct = round(voix / exprimes_val * 100, 2) if exprimes_val else None
            resultat_rows.append(
                {
                    "id_observation": obs_id,
                    "code_famille": f,
                    "voix": voix,
                    "pourcentage": pct,
                }
            )

        obs_id += 1

    print(f"  Observations     : {len(observation_rows)}")
    print(f"  Résultats        : {len(resultat_rows)}")

    # ---- Écriture SQL ----
    print(f"\nÉcriture de {OUTPUT.name}...")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(DDL)
        f.write("BEGIN;\n\n")

        for name, rows in [
            ("region", region_rows),
            ("departement", dept_rows),
            ("commune", commune_rows),
            ("scrutin", scrutin_rows),
            ("famille_politique", famille_rows),
            ("candidat", candidat_rows),
            ("observation", observation_rows),
            ("resultat", resultat_rows),
        ]:
            print(f"  Écriture {name}...")
            f.write(f"-- {name}\n")
            f.write(build_inserts(name, rows))
            f.write("\n\n")

        f.write("COMMIT;\n")

    size_kb = OUTPUT.stat().st_size / 1_000
    print(f"\nFichier généré : {OUTPUT}")
    print(f"Taille         : {size_kb:.0f} Ko")
    print("Terminé.")


if __name__ == "__main__":
    main()
