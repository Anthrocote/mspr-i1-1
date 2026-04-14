<div align="center">

# Electio-Analytics

**Prédire les tendances électorales communales à partir de données socio-économiques**

<br/>

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/licence-usage%20%C3%A9ducatif-green.svg)]()
[![Données](https://img.shields.io/badge/données-INSEE%20%7C%20data.gouv.fr-orange.svg)]()

</div>

---

## Présentation

POC de data science qui analyse les déterminants socio-économiques du vote en France. Le pipeline construit une table analytique de **5 429 communes** (≥ 2 000 hab., France métropolitaine) sur les **présidentielles T1 2017 et 2022**, en croisant résultats électoraux, recensement, criminalité, immigration et vie associative.

## Fonctionnalités

- **Téléchargement automatisé** - 23 datasets depuis data.gouv.fr, INSEE et sources directes
- **Extraction intelligente** - Sélection des colonnes pertinentes, préférence Parquet sur CSV
- **Harmonisation géographique** - Gestion des fusions communales via le COG INSEE
- **7 familles politiques** - Classification des 61 candidats (2002-2022) selon les clivages de Rokkan/Seiler
- **Fallback statistique** - Imputation départementale pour les données sous secret statistique
- **Feature engineering** - Taux de chômage, diplômes, CSP, logement, démographie, criminalité, associations

## Démarrage rapide

**1. Installer les dépendances**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Télécharger les données brutes**

```bash
python -u scripts/00_download.py
```

> Télécharge ~5 Go de données dans `data/raw/`. Idempotent : les fichiers déjà présents sont vérifiés par hash SHA256.

**3. Extraire les colonnes pertinentes**

```bash
python -u scripts/01_extract_columns.py
```

> Produit 13 fichiers Parquet dans `data/staging/` (~67 Mo).

**4. Construire la table analytique**

```bash
python -u scripts/02_clean_transform.py
```

> Produit `data/processed/table_analytique.parquet` (10 608 lignes × 150 colonnes, ~7 Mo).

## Scripts

| Script | Entrée | Sortie | Description |
|--------|--------|--------|-------------|
| `00_download.py` | URLs configurées | `data/raw/` | Téléchargement avec manifest et reprise sur erreur |
| `01_extract_columns.py` | `data/raw/` | `data/staging/` | Sélection des colonnes, filtrage par scrutin |
| `02_clean_transform.py` | `data/staging/` | `data/processed/` | Nettoyage, agrégation, jointure, feature engineering |

## Sources de données

| Source | Contenu | Fournisseur |
|--------|---------|-------------|
| Élections agrégées | Résultats par bureau de vote (2002-2022) | Etalab / data.gouv.fr |
| Dossier Complet RP | Population, diplômes, CSP, logement, revenus (~1 976 variables) | INSEE |
| Criminalité SSMSI | 16 indicateurs communaux et départementaux | Ministère de l'Intérieur |
| Immigration RP | Immigrés et étrangers par commune | INSEE |
| RNA | Répertoire National des Associations | data.gouv.fr |
| Référentiels COG | Communes, départements, fusions, densité | INSEE |

## Configuration requise

| Élément | Minimum |
|---------|---------|
| Python | 3.10+ |
| Espace disque | ~6 Go (données brutes + staging + processed) |
| RAM | ~4 Go (chargement du Dossier Complet) |
| Réseau | Connexion internet pour le téléchargement initial |
