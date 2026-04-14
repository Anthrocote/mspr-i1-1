#!/usr/bin/env python3 -u
"""
Usage:
    python -u scripts/02_clean_transform.py
"""

import sys
import warnings

import numpy as np
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

STAGING = Path(__file__).resolve().parent.parent / "data" / "staging"
PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

# Mapping des 61 candidats aux présidentielles T1 (2002-2022) vers 7 familles politiques.
#
# Fondement théorique : les familles dérivent des clivages de Rokkan (1967) et
# Seiler (1980), augmentés du clivage matérialisme/post-matérialisme (Inglehart, 1977) :
#   - gauche_radicale     : clivage de classe (travailleurs), anti-système
#   - social_democratie   : clivage de classe (travailleurs modérés), réformisme
#   - ecologisme          : post-matérialisme, transition écologique
#   - liberalisme_centre  : synthèse libérale, pro-européen
#   - droite_conservatrice: classe (possédants) + Église/État, ordre et tradition
#   - souverainisme       : centre/périphérie, euroscepticisme
#   - droite_nationale    : classe + identité, immigration, sécurité
#
# Cas limites :
#   - Chévènement (2002) : souverainiste de gauche, classé social-démocratie (programme
#     centré sur la République sociale). Discutable, pourrait aller en souverainisme.
#   - Lassalle (2017, 2022) : anti-centralisation, pro-ruralité → souverainisme.
#   - Macron (2017) : libéralisme économique + progressisme social → centre, pas droite.
#   - Cheminade (2012, 2017) : hors axe classique, classé souverainisme par défaut.
#
# Clé = (NOM upper sans accents, PRENOM upper sans accents)
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

# Mapping indicateurs criminalité -> 3 grandes catégories
CRIME_CATEGORIES = {
    "Coups et blessures volontaires": "violences",
    "Coups et blessures volontaires intrafamiliaux": "violences",
    "Autres coups et blessures volontaires": "violences",
    "Violences sexuelles": "violences",
    "Vols avec armes": "atteintes_biens",
    "Vols violents sans arme": "atteintes_biens",
    "Vols sans violence contre des personnes": "atteintes_biens",
    "Vols dans les véhicules": "atteintes_biens",
    "Vols d'accessoires sur véhicules": "atteintes_biens",
    "Vols de véhicules": "atteintes_biens",
    "Cambriolages de logement": "atteintes_biens",
    "Destructions et dégradations volontaires": "atteintes_biens",
    "Escroqueries": "atteintes_biens",
    "Trafic de stupéfiants": "stupefiants",
    "Usage de stupéfiants": "stupefiants",
    "Usage de stupéfiants (AFD)": "stupefiants",
}

# Mapping années élections -> années criminalité à moyenner
CRIME_ANNEES = {
    "2017": [2016, 2017],
    "2022": [2021, 2022],
}


def _normalize_name(s):
    """Normalise un nom/prénom pour le matching : upper, sans accents."""
    import unicodedata

    s = str(s).upper().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s


def build_cog_mapping(mvt):
    """
    Construit un dictionnaire old_code -> new_code pour les fusions communales.
    MOD 31/32/33/34 = fusions/absorptions.
    On ne garde que les mouvements après 2016-01-01 (géographie pré-2017).
    """
    fusions = mvt[
        (mvt["MOD"].isin([31, 32, 33, 34]))
        & (mvt["DATE_EFF"] >= "2016-01-01")
        & (mvt["TYPECOM_AV"] == "COM")
        & (mvt["TYPECOM_AP"] == "COM")
        & (mvt["COM_AV"] != mvt["COM_AP"])
    ][["COM_AV", "COM_AP"]].drop_duplicates()

    mapping = dict(zip(fusions["COM_AV"], fusions["COM_AP"]))

    # Résoudre les chaînes (A -> B -> C)
    changed = True
    while changed:
        changed = False
        for k, v in list(mapping.items()):
            if v in mapping and mapping[v] != v:
                mapping[k] = mapping[v]
                changed = True

    return mapping


def harmonize_codgeo(df, col, cog_map):
    """Applique le mapping COG et exclut ZZ* et outre-mer."""
    df = df.copy()
    df[col] = df[col].astype(str).str.strip()
    # Exclure consulats (ZZ*) et outre-mer (97*)
    mask = ~df[col].str.startswith("ZZ") & ~df[col].str.startswith("97")
    df = df[mask].copy()
    # Appliquer les fusions
    df[col] = df[col].map(lambda x: cog_map.get(x, x))
    return df


def clean_revenue_cols(dc):
    """Convertit les colonnes str avec secret stat 's' et virgule décimale."""
    str_cols = [
        c for c in dc.columns if pd.api.types.is_string_dtype(dc[c]) and c != "CODGEO"
    ]
    for col in str_cols:
        dc[col] = dc[col].replace("s", np.nan)
        dc[col] = dc[col].astype(str).str.replace(",", ".", regex=False)
        dc[col] = pd.to_numeric(dc[col], errors="coerce")
    return dc


def clean_rna(rna):
    """Déduplique, nettoie les codes commune, exclut dates aberrantes."""
    rna = rna.copy()
    n_before = len(rna)

    # Nettoyer les codes commune (.0 artefact float->str)
    rna["adrs_codeinsee"] = (
        rna["adrs_codeinsee"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(5)
    )

    # Exclure codes invalides
    rna = rna[rna["adrs_codeinsee"].str.len() == 5]
    rna = rna[~rna["adrs_codeinsee"].isin(["00nan", "00NaN", "nan00"])]
    rna = rna.dropna(subset=["adrs_codeinsee"])

    # Exclure dates aberrantes
    rna = rna[rna["date_creat"] != "0001-01-01"]
    rna = rna[rna["date_creat"] <= "2025-12-31"]

    # Dédupliquer
    rna = rna.drop_duplicates()

    print(
        f"  RNA nettoyage: {n_before} -> {len(rna)} ({n_before - len(rna)} supprimées)"
    )
    return rna


def aggregate_elections(general, candidats, cog_map):
    """
    Agrège BV par commune et mappe les candidats aux 7 familles politiques.
    Retourne un DataFrame avec une ligne par commune x scrutin.
    """
    general = harmonize_codgeo(general, "code_commune", cog_map)
    candidats = harmonize_codgeo(candidats, "code_commune", cog_map)
    general = general[general["inscrits"] > 0]

    general["annee"] = general["id_election"].str[:4]
    candidats["annee"] = candidats["id_election"].str[:4]

    gen_agg = (
        general.groupby(["annee", "code_commune"])
        .agg(
            {
                "inscrits": "sum",
                "abstentions": "sum",
                "votants": "sum",
                "blancs": "sum",
                "nuls": "sum",
                "exprimes": "sum",
            }
        )
        .reset_index()
    )
    gen_agg["nuls"] = gen_agg["nuls"].clip(lower=0)

    candidats["nom_norm"] = candidats["nom"].apply(_normalize_name)
    candidats["prenom_norm"] = candidats["prenom"].apply(_normalize_name)
    candidats["famille"] = candidats.apply(
        lambda r: CANDIDAT_FAMILLE.get((r["nom_norm"], r["prenom_norm"]), "INCONNU"),
        axis=1,
    )

    inconnus = candidats[candidats["famille"] == "INCONNU"][
        ["nom", "prenom"]
    ].drop_duplicates()
    if len(inconnus) > 0:
        print(
            f"  ATTENTION: {len(inconnus)} candidats non mappés: {inconnus.values.tolist()}"
        )

    fam_voix = (
        candidats.groupby(["annee", "code_commune", "famille"])["voix"]
        .sum()
        .reset_index()
    )
    fam_pivot = fam_voix.pivot_table(
        index=["annee", "code_commune"],
        columns="famille",
        values="voix",
        fill_value=0,
    ).reset_index()
    fam_pivot.columns.name = None

    elections = gen_agg.merge(fam_pivot, on=["annee", "code_commune"], how="left")

    elections = elections.rename(columns={"code_commune": "CODGEO"})

    familles = [c for c in elections.columns if c in set(CANDIDAT_FAMILLE.values())]
    for f in familles:
        elections[f] = elections[f].fillna(0)

    print(
        f"  Élections agrégé: {elections.shape[0]} lignes, {elections['CODGEO'].nunique()} communes, années: {sorted(elections['annee'].unique())}"
    )
    return elections


def aggregate_immigration(img, cog_map):
    """Calcule pct_immigres par commune."""
    img = harmonize_codgeo(img, "CODGEO", cog_map)
    agg = img.groupby(["CODGEO", "IMMI"])["NB"].sum().reset_index()
    total = agg.groupby("CODGEO")["NB"].sum().rename("total")
    immigres = agg[agg["IMMI"] == 1].groupby("CODGEO")["NB"].sum().rename("nb_immigres")
    immigration = pd.DataFrame({"total": total, "nb_immigres": immigres}).fillna(0)
    immigration["pct_immigres"] = (
        immigration["nb_immigres"] / immigration["total"] * 100
    ).round(2)
    immigration = immigration[immigration["total"] > 0][["pct_immigres"]].reset_index()
    print(
        f"  Immigration agrégé: {len(immigration)} communes, pct_immigres médiane={immigration['pct_immigres'].median():.1f}%"
    )
    return immigration


def aggregate_rna(rna, cog_map):
    """
    Compte les associations actives à 2 dates cibles (2017-04-23 et 2022-04-10,
    dates des T1 présidentiels) et calcule la densité associative.
    """
    rna = harmonize_codgeo(rna, "adrs_codeinsee", cog_map)
    rna = rna.rename(columns={"adrs_codeinsee": "CODGEO"})

    results = []
    for annee, date_cible in [("2017", "2017-04-23"), ("2022", "2022-04-10")]:
        actives = rna[
            (rna["date_creat"] <= date_cible)
            & ((rna["date_disso"] > date_cible) | (rna["date_disso"] == "0001-01-01"))
        ]
        counts = (
            actives.groupby("CODGEO").size().rename("nb_associations").reset_index()
        )
        counts["annee"] = annee
        results.append(counts)

    rna = pd.concat(results, ignore_index=True)
    print(f"  RNA agrégé: {rna.shape[0]} lignes (commune x année)")
    return rna


def aggregate_crimes(comm, dep, cog_map, ref_communes):
    """
    Agrège la criminalité en 3 grandes catégories, applique le fallback
    départemental pour les communes sous secret statistique.
    """
    comm = harmonize_codgeo(comm, "CODGEO_2024", cog_map)
    comm = comm.rename(columns={"CODGEO_2024": "CODGEO"})

    # Mapper indicateurs -> catégories
    comm["categorie"] = comm["indicateur"].map(CRIME_CATEGORIES)

    # Table des départements par commune (pour le fallback)
    dep_lookup = ref_communes[ref_communes["TYPECOM"] == "COM"][["COM", "DEP"]].copy()
    dep_lookup = dep_lookup.rename(columns={"COM": "CODGEO"})

    results = []
    for scrutin, annees in CRIME_ANNEES.items():
        sub = comm[comm["annee"].isin(annees)].copy()

        # Communes diffusées : agréger par catégorie et moyenner sur les 2 années
        diff = sub[sub["est_diffuse"] == "diff"]
        comm_agg = (
            diff.groupby(["CODGEO", "categorie"])["taux_pour_mille"]
            .mean()
            .reset_index()
        )
        comm_pivot = comm_agg.pivot_table(
            index="CODGEO",
            columns="categorie",
            values="taux_pour_mille",
        ).reset_index()
        comm_pivot.columns.name = None

        # Fallback départemental
        dep_sub = dep[dep["annee"].isin(annees)].copy()
        dep_sub["categorie"] = dep_sub["indicateur"].map(CRIME_CATEGORIES)
        # Convertir taux_pour_mille str (virgule) -> float
        dep_sub["taux_pour_mille"] = (
            dep_sub["taux_pour_mille"]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )
        dep_agg = (
            dep_sub.groupby(["Code_departement", "categorie"])["taux_pour_mille"]
            .mean()
            .reset_index()
        )
        dep_pivot = dep_agg.pivot_table(
            index="Code_departement",
            columns="categorie",
            values="taux_pour_mille",
        ).reset_index()
        dep_pivot.columns.name = None

        # Joindre le département aux communes pour fallback
        all_communes = dep_lookup.merge(
            dep_pivot, left_on="DEP", right_on="Code_departement", how="left"
        )
        all_communes = all_communes.drop(columns=["DEP", "Code_departement"])

        # Utiliser les données communales quand disponibles, sinon fallback
        cats = [
            c
            for c in ["violences", "atteintes_biens", "stupefiants"]
            if c in comm_pivot.columns
        ]
        merged = all_communes.set_index("CODGEO")
        if len(comm_pivot) > 0:
            comm_idx = comm_pivot.set_index("CODGEO")
            for cat in cats:
                if cat in comm_idx.columns and cat in merged.columns:
                    # Ne remplacer que là où la donnée communale existe (non NaN)
                    comm_vals = comm_idx[cat].dropna()
                    common_idx = comm_vals.index.intersection(merged.index)
                    if len(common_idx) > 0:
                        merged.loc[common_idx, cat] = comm_vals.loc[common_idx]

        merged = merged.reset_index()
        # Renommer les colonnes pour inclure le préfixe crim_
        for cat in cats:
            if cat in merged.columns:
                merged = merged.rename(columns={cat: f"crim_{cat}"})

        merged["annee"] = scrutin
        results.append(merged)

    crimes = pd.concat(results, ignore_index=True)
    print(f"  Criminalité agrégé: {crimes.shape[0]} lignes (commune x scrutin)")
    return crimes


def build_analytical_table(
    elections, dc, crimes, immigration, rna, ref_communes, ref_densite, cog_map
):
    """
    Assemble la table analytique (commune x scrutin x features).
    Filtre communes >= 2 000 hab, France métropolitaine.
    """
    elections = elections[elections["annee"].isin(["2017", "2022"])].copy()

    dc = harmonize_codgeo(dc, "CODGEO", cog_map)
    dc = clean_revenue_cols(dc)

    # Séparer DC en 2 versions : une pour 2022 (P22/C22) et une pour 2017 (P16/C16)
    common_cols = [
        c for c in dc.columns if not c.startswith(("P22_", "C22_", "P16_", "C16_"))
    ]
    p22_cols = [c for c in dc.columns if c.startswith(("P22_", "C22_"))]
    p16_cols = [c for c in dc.columns if c.startswith(("P16_", "C16_"))]

    dc_2022 = dc[common_cols + p22_cols].copy()
    rename_22 = {}
    for c in p22_cols:
        new_name = c.replace("P22_", "P_").replace("C22_", "C_")
        rename_22[c] = new_name
    dc_2022 = dc_2022.rename(columns=rename_22)
    dc_2022["annee"] = "2022"

    # Version 2017 : colonnes P16/C16 renommées
    # Attention aux différences de nommage entre millésimes :
    #   - CSP P16 : C16_ACTOCC1564_CS1..CS6  ->  P22 utilise C22_ACTOCC1564_STAT_GSEC11..16
    #   - Diplômes P16 : SUP (1 niveau)      ->  P22 utilise SUP2, SUP34, SUP5 (3 niveaux)
    #   - Statut marital P16 : NONMARIEE      ->  P22 utilise CELIBATAIRE
    dc_2017 = dc[common_cols + p16_cols].copy()
    rename_16 = {}
    for c in p16_cols:
        new_name = c.replace("P16_", "P_").replace("C16_", "C_")
        new_name = new_name.replace("_NONMARIEE", "_CELIBATAIRE")
        # CSP : C16_ACTOCC1564_CS1 -> C_ACTOCC1564_STAT_GSEC11 (ajouter _STAT_ et GSEC1x)
        for i in range(1, 7):
            new_name = new_name.replace(
                f"_ACTOCC1564_CS{i}", f"_ACTOCC1564_STAT_GSEC1{i}"
            )
        rename_16[c] = new_name
    dc_2017 = dc_2017.rename(columns=rename_16)
    dc_2017["annee"] = "2017"

    dc_stacked = pd.concat([dc_2022, dc_2017], ignore_index=True)

    # Forcer le typage numérique de toutes les colonnes revenues/common
    # (elles peuvent rester str après le concat si le parquet les avait en object)
    for col in dc_stacked.columns:
        if col in ("CODGEO", "annee"):
            continue
        if pd.api.types.is_string_dtype(dc_stacked[col]):
            dc_stacked[col] = pd.to_numeric(
                dc_stacked[col].astype(str).str.replace(",", ".", regex=False),
                errors="coerce",
            )

    print(f"  DC empilé: {dc_stacked.shape[0]} lignes x {dc_stacked.shape[1]} colonnes")

    # Jointure principale : Élections (base) <- DC <- Criminalité <- Immigration <- RNA
    table = elections.merge(dc_stacked, on=["CODGEO", "annee"], how="left")
    print(f"  Après jointure DC: {table.shape}")

    table = table.merge(crimes, on=["CODGEO", "annee"], how="left")
    print(f"  Après jointure Criminalité: {table.shape}")

    table = table.merge(immigration, on="CODGEO", how="left")
    print(f"  Après jointure Immigration: {table.shape}")

    table = table.merge(rna, on=["CODGEO", "annee"], how="left")
    print(f"  Après jointure RNA: {table.shape}")

    ref_densite = harmonize_codgeo(ref_densite, "CODGEO", cog_map)
    table = table.merge(ref_densite, on="CODGEO", how="left")
    print(f"  Après jointure densité: {table.shape}")

    communes_info = ref_communes[ref_communes["TYPECOM"] == "COM"][
        ["COM", "DEP", "REG", "LIBELLE"]
    ].copy()
    communes_info = communes_info.rename(
        columns={"COM": "CODGEO", "LIBELLE": "lib_commune"}
    )
    communes_info = harmonize_codgeo(communes_info, "CODGEO", cog_map)
    communes_info = communes_info.drop_duplicates(subset="CODGEO", keep="first")
    table = table.merge(communes_info, on="CODGEO", how="left")
    print(f"  Après jointure ref communes: {table.shape}")

    # Filtre : communes >= 2 000 hab, France métropolitaine.
    # Seuil de 2 000 hab : en-dessous, le secret statistique rend les données Filosofi
    # (revenus, pauvreté) et criminalité largement inutilisables (87% de secret sur TP6021,
    # 46% sur la criminalité). Le modèle ne serait pas fiable sur ces communes.
    n_before = len(table)
    table = table[table["P_POP"].notna() & (table["P_POP"] >= 2000)]
    table = table[~table["DEP"].astype(str).str.startswith("97")]
    print(f"  Filtre >= 2000 hab métro: {n_before} -> {len(table)}")

    return table


def compute_features(table):
    """Calcule les ratios et indicateurs dérivés."""
    t = table.copy()

    # Participation
    t["taux_abstention"] = (t["abstentions"] / t["inscrits"] * 100).round(2)
    t["taux_blancs_nuls"] = (
        (t["blancs"].fillna(0) + t["nuls"]) / t["votants"] * 100
    ).round(2)

    # Parts par famille politique (% des exprimés)
    familles = [
        c for c in t.columns if c.startswith("F") and "_" in c and c[1].isdigit()
    ]
    for f in familles:
        t[f"pct_{f}"] = (t[f] / t["exprimes"] * 100).round(2)

    # Emploi / chômage
    t["taux_chomage"] = (t["P_CHOM1564"] / t["P_ACT1564"] * 100).round(2)
    t["taux_activite"] = (t["P_ACT1564"] / t["P_POP1564"] * 100).round(2)

    # Diplômes
    # P22 a SUP2 + SUP34 + SUP5 (3 niveaux). P16 a SUP (1 seul niveau).
    # On utilise la somme des 3 quand disponible, sinon SUP seul.
    has_sup_detail = (
        t.get("P_NSCOL15P_SUP2", pd.Series(dtype=float)).notna()
        & t.get("P_NSCOL15P_SUP34", pd.Series(dtype=float)).notna()
        & t.get("P_NSCOL15P_SUP5", pd.Series(dtype=float)).notna()
    )
    t["_sup_total"] = np.nan
    if "P_NSCOL15P_SUP2" in t.columns:
        t.loc[has_sup_detail, "_sup_total"] = (
            t.loc[has_sup_detail, "P_NSCOL15P_SUP2"]
            + t.loc[has_sup_detail, "P_NSCOL15P_SUP34"]
            + t.loc[has_sup_detail, "P_NSCOL15P_SUP5"]
        )
    if "P_NSCOL15P_SUP" in t.columns:
        mask_sup_only = t["_sup_total"].isna() & t["P_NSCOL15P_SUP"].notna()
        t.loc[mask_sup_only, "_sup_total"] = t.loc[mask_sup_only, "P_NSCOL15P_SUP"]
    t["pct_diplome_sup"] = (t["_sup_total"] / t["P_NSCOL15P"] * 100).round(2)
    t = t.drop(columns=["_sup_total"])
    t["pct_sans_diplome"] = (t["P_NSCOL15P_DIPLMIN"] / t["P_NSCOL15P"] * 100).round(2)

    # CSP
    if "C_ACTOCC1564_STAT_GSEC13" in t.columns:
        t["pct_cadres"] = (
            t["C_ACTOCC1564_STAT_GSEC13"] / t["P_ACTOCC1564"] * 100
        ).round(2)
    if "C_ACTOCC1564_STAT_GSEC16" in t.columns:
        t["pct_ouvriers"] = (
            t["C_ACTOCC1564_STAT_GSEC16"] / t["P_ACTOCC1564"] * 100
        ).round(2)

    # Logement
    t["taux_logements_vacants"] = (t["P_LOGVAC"] / t["P_LOG"] * 100).round(2)
    t["pct_proprietaires"] = (t["P_RP_PROP"] / t["P_RP"] * 100).round(2)
    t["pct_hlm"] = (t["P_RP_LOCHLMV"] / t["P_RP"] * 100).round(2)

    # Ménages
    if "C_MEN" in t.columns:
        t["pct_menages_seuls"] = (t["C_MENPSEUL"] / t["C_MEN"] * 100).round(2)
        t["pct_familles_mono"] = (t["C_MENFAMMONO"] / t["C_MEN"] * 100).round(2)

    # Densité associative (associations / 1000 hab)
    t["densite_associative"] = (
        t["nb_associations"].fillna(0) / t["P_POP"] * 1000
    ).round(2)

    # Solde naturel (pour l'année correspondante)
    # 2017 -> NAISD17/DECESD17, 2022 -> NAISD22/DECESD22
    t["solde_naturel"] = np.nan
    if "NAISD17" in t.columns:
        mask17 = t["annee"] == "2017"
        t.loc[mask17, "solde_naturel"] = (
            (t.loc[mask17, "NAISD17"] - t.loc[mask17, "DECESD17"])
            / t.loc[mask17, "P_POP"]
            * 1000
        ).round(2)
    if "NAISD22" in t.columns:
        mask22 = t["annee"] == "2022"
        t.loc[mask22, "solde_naturel"] = (
            (t.loc[mask22, "NAISD22"] - t.loc[mask22, "DECESD22"])
            / t.loc[mask22, "P_POP"]
            * 1000
        ).round(2)

    # Secteurs d'emploi (% de l'emploi total)
    for sector, col in [
        ("agri", "C_EMPLT_AGRI"),
        ("indus", "C_EMPLT_INDUS"),
        ("const", "C_EMPLT_CONST"),
        ("services", "C_EMPLT_CTS"),
        ("public", "C_EMPLT_APESAS"),
    ]:
        if col in t.columns:
            t[f"pct_emploi_{sector}"] = (t[col] / t["P_EMPLT"] * 100).round(2)

    if "RD21" in t.columns:
        t["RD21"] = pd.to_numeric(t["RD21"], errors="coerce")

    print(f"  Features calculées: {t.shape[1]} colonnes total")
    return t


def validate(table):
    """Vérifie la cohérence de la table analytique finale."""
    print("\n=== VALIDATION ===")
    print(f"Shape: {table.shape}")
    print(f"Communes uniques: {table['CODGEO'].nunique()}")
    print(f"Années: {sorted(table['annee'].unique())}")
    print(f"Lignes par année: {table.groupby('annee').size().to_dict()}")

    # Vérifier que les % par famille somment à ~100%
    fam_pct = [c for c in table.columns if c.startswith("pct_F")]
    if fam_pct:
        total_pct = table[fam_pct].sum(axis=1)
        print(
            f"\nSomme % familles: min={total_pct.min():.1f}, "
            f"median={total_pct.median():.1f}, max={total_pct.max():.1f}"
        )

    # Taux de complétude des features clés
    print("\nComplétude des features clés:")
    key_features = [
        "taux_abstention",
        "taux_chomage",
        "pct_diplome_sup",
        "pct_sans_diplome",
        "pct_cadres",
        "pct_ouvriers",
        "MED21",
        "TP6021",
        "D121",
        "D921",
        "RD21",
        "PIMP21",
        "PACT21",
        "PPEN21",
        "PPSOC21",
        "pct_immigres",
        "crim_violences",
        "crim_atteintes_biens",
        "crim_stupefiants",
        "densite_associative",
    ]
    for feat in key_features:
        if feat in table.columns:
            pct_ok = table[feat].notna().sum() / len(table) * 100
            print(f"  {feat}: {pct_ok:.1f}% complet")

    # Vérifier que les colonnes numériques sont bien numériques (pas str)
    str_cols = [
        c
        for c in table.columns
        if pd.api.types.is_string_dtype(table[c])
        and c not in ("CODGEO", "annee", "lib_commune")
    ]
    if str_cols:
        print(f"\nATTENTION: {len(str_cols)} colonnes encore en str: {str_cols}")
    else:
        print("\nTypes: toutes les colonnes numériques sont bien en float/int")

    # Distributions aberrantes
    print("\nDistributions (min / median / max):")
    dist_features = [
        "taux_abstention",
        "taux_chomage",
        "pct_immigres",
        "MED21",
        "pct_diplome_sup",
        "pct_cadres",
        "pct_ouvriers",
        "RD21",
    ]
    for feat in dist_features:
        if feat in table.columns and table[feat].notna().any():
            vals = pd.to_numeric(table[feat], errors="coerce").dropna()
            if len(vals) > 0:
                print(
                    f"  {feat}: {vals.min():.1f} / {vals.median():.1f} / {vals.max():.1f}"
                )


def main():
    print("Phase 3 — Nettoyage et transformation")
    print(f"Source: {STAGING}")
    print(f"Cible: {PROCESSED}\n")

    # Charger les données staging
    print("Chargement des données staging...")
    general = pd.read_parquet(STAGING / "elections_general_pres_t1.parquet")
    candidats = pd.read_parquet(STAGING / "elections_candidats_pres_t1.parquet")
    dc = pd.read_parquet(STAGING / "dossier_complet_extract.parquet")
    crimes_comm = pd.read_parquet(STAGING / "criminalite.parquet")
    crimes_dep = pd.read_parquet(STAGING / "criminalite_dep.parquet")
    img = pd.read_parquet(STAGING / "immigres.parquet")
    rna = pd.read_parquet(STAGING / "rna.parquet")
    ref_communes = pd.read_parquet(STAGING / "ref_communes.parquet")
    ref_densite = pd.read_parquet(STAGING / "ref_densite.parquet")
    mvt = pd.read_parquet(STAGING / "ref_mvt_communes.parquet")
    print("  OK\n")

    print("Harmonisation COG...")
    cog_map = build_cog_mapping(mvt)
    print(f"  {len(cog_map)} communes à remapper\n")

    print("Nettoyage RNA...")
    rna = clean_rna(rna)
    print()

    print("Agrégation Élections...")
    elections = aggregate_elections(general, candidats, cog_map)
    print()

    print("Agrégation Immigration...")
    immigration = aggregate_immigration(img, cog_map)
    print()

    print("Agrégation RNA...")
    rna = aggregate_rna(rna, cog_map)
    print()

    print("Aggrégation Criminalité...")
    crimes = aggregate_crimes(crimes_comm, crimes_dep, cog_map, ref_communes)
    print()

    print("Jointure et filtre...")
    table = build_analytical_table(
        elections, dc, crimes, immigration, rna, ref_communes, ref_densite, cog_map
    )
    print()

    print("Feature engineering...")
    table = compute_features(table)
    print()

    validate(table)

    output_path = PROCESSED / "table_analytique.parquet"
    table.to_parquet(output_path, index=False)
    size_mb = output_path.stat().st_size / 1e6
    print(f"\n=== Sauvegardé: {output_path} ({size_mb:.1f} Mo) ===")
    print(f"    {table.shape[0]} lignes x {table.shape[1]} colonnes")


if __name__ == "__main__":
    main()
