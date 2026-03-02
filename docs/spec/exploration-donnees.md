# Exploration preliminaire des donnees disponibles

## 1. Donnees electorales

**Source principale** : Ministere de l'Interieur via data.gouv.fr

| Scrutin | Annees disponibles |
|---|---|
| Presidentielles | 2002, 2007, 2012, 2017, 2022 |
| Legislatives | 2002, 2007, 2012, 2017, 2022, 2024 (+ Sciences Po 1958-2012) |
| Municipales | 2008, 2014, 2020 |
| Europeennes | 1999, 2004, 2009, 2014, 2019, 2024 |
| Regionales | 2004, 2010, 2015, 2021 |
| Departementales | 2015, 2021 |

**Granularite** : du bureau de vote au national (bureau de vote > commune > circonscription > departement > region > national).

**Formats** : CSV (principal), XLSX, GeoJSON (contours geographiques).

**Point cle** : un referentiel de "nuances politiques" est maintenu par le Ministere, permettant de regrouper les candidats par tendance (gauche, droite, centre, extreme...) plutot que par parti. C'est essentiel pour la variable cible du modele.

---

## 2. Donnees de securite

**Source principale** : SSMSI (Service statistique ministeriel de la securite interieure)

**Dataset cle** : Bases communale et departementale des principaux indicateurs de crimes et delits.

| Niveau | Disponibilite | Periode |
|---|---|---|
| Departemental | Complet | 2016-2024 |
| Communal | Restreint (communes > 5 faits sur 3 ans) | 2016-2024 |
| Archive (107 categories) | Departemental | 2012-2021 |

**Formats** : CSV, Parquet, XLSX.

**Limitation importante** : les donnees communales ne couvrent pas les petites communes (seuil de 5 faits constates sur 3 annees consecutives). Pour un POC departemental, les donnees departementales sont completes.

---

## 3. Donnees d'emploi

**Sources principales** : INSEE, France Travail (ex-Pole Emploi), DARES

| Type de donnee | Granularite la plus fine | Periode |
|---|---|---|
| Taux de chomage localise | Zone d'emploi, departement | 1954-2024 |
| Demandeurs d'emploi (DEFM) | Zone d'emploi | Series mensuelles continues |
| Emploi au lieu de travail | Commune | 2011-2022 |
| Caracteristiques de l'emploi | Commune | 2011-2022 |
| Creations d'entreprises | Commune | 2012-2024 |
| Effectifs salaries (FLORES) | Commune | Annuel |

**Formats** : CSV (dominant), XLS, Parquet.

**Point cle** : les donnees France Travail sont souvent a la maille zone d'emploi ou departement. Les donnees communales viennent principalement de l'INSEE (recensement, SIRENE).

---

## 4. Donnees INSEE (demographie, pauvrete, entreprises)

### Population / demographie

| Dataset | Granularite | Periode |
|---|---|---|
| Recensement (CSP, diplomes, emploi, logement) | IRIS (~2000 hab) | 2020-2021 |
| Serie historique du recensement | Commune | 1968-2022 |
| Populations municipales | Commune | 1968-2023 |

### Pauvrete / revenus

| Dataset | Granularite | Periode |
|---|---|---|
| Filosofi (revenus, pauvrete, niveaux de vie) | IRIS | 2015-2022 |
| Donnees carroyees (revenus) | Carreau 200m | 2010-2019 |
| Indicateurs de pauvrete communale | Commune | 2021 |

### Entreprises

| Dataset | Granularite | Periode |
|---|---|---|
| Base SIRENE | Etablissement | 1973-present |
| Creations d'entreprises | Commune | Annuel |
| Effectifs salaries (FLORES) | Commune | Annuel |

### Vie associative

Pas de dataset INSEE dedie. Deux alternatives :
- **Base SIRENE** : filtrer par forme juridique "association loi 1901" pour compter les associations par commune
- **Repertoire National des Associations (RNA)** : maintenu par le Ministere de l'Interieur, disponible sur data.gouv.fr

### Autres datasets utiles

- **Base Permanente des Equipements (BPE)** : commerce, sport, sante, enseignement par commune
- **Bureaux de vote et adresses des electeurs** : permet de croiser resultats electoraux avec caracteristiques sociodemographiques

---

## 5. Synthese : matrice de disponibilite par granularite

| Indicateur | Bureau de vote | Commune | Departement | Periode exploitable |
|---|---|---|---|---|
| Resultats electoraux | Oui | Oui | Oui | 2002-2024 |
| Population / demographie | Non | Oui | Oui | 1968-2023 |
| Revenus / pauvrete | Non | Oui (Filosofi) | Oui | 2015-2022 |
| Securite | Non | Partiel (seuil) | Oui | 2016-2024 |
| Emploi (recensement) | Non | Oui | Oui | 2011-2022 |
| Chomage (France Travail) | Non | Non | Oui | 1954-2024 |
| Entreprises (SIRENE) | Non | Oui | Oui | 1973-present |
| Creations d'entreprises | Non | Oui | Oui | 2012-2024 |
| Vie associative (RNA/SIRENE) | Non | Oui | Oui | Variable |
| Equipements (BPE) | Non | Oui | Oui | Annuel |

---

## 6. Recommandation preliminaire

### Echelle geographique : le departement

Le **departement** est le meilleur compromis pour le POC :
- C'est la seule echelle ou **tous les indicateurs** sont disponibles sans restriction (securite incluse).
- En utilisant les **communes du departement comme unites d'observation**, on multiplie les points de donnees pour l'apprentissage (un departement moyen = 300-500 communes).
- Les resultats electoraux sont disponibles a la commune, ce qui permet la jointure.

A la maille communale, les donnees de securite sont partielles (seuil de 5 faits) et le chomage n'est pas disponible directement (seulement via le recensement INSEE). Si on travaille au niveau departemental avec subdivision communale, on contourne ces limitations en utilisant les indicateurs departementaux de securite/chomage comme constantes pour toutes les communes du departement.

### Periode : 2012-2024

La fenetre 2012-2024 offre le meilleur equilibre :
- **Elections couvertes** : presidentielles 2012/2017/2022, legislatives 2012/2017/2022/2024, municipales 2014/2020, europeennes 2014/2019/2024
- **Indicateurs disponibles** : tous les indicateurs cles sont couverts sur cette periode
- Avant 2012, les donnees de securite communale et de revenus Filosofi ne sont pas disponibles

### Points d'attention

- **Alignement temporel** : a definir (indicateurs N-1 pour scrutin N)
- **Donnees de securite communales** : incompletes pour les petites communes, possibilite d'utiliser le taux departemental en fallback
- **Vie associative** : necessite un traitement specifique (extraction SIRENE ou RNA)
