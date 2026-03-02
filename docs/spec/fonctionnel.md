# Spécification fonctionnelle - POC Electio-Analytics

## 1. Contexte

Electio-Analytics est une startup de conseil stratégique pour campagnes électorales. Elle souhaite valider, via une preuve de concept (POC), sa capacité à prévoir les tendances électorales à moyen terme (1 à 3 ans) en croisant des résultats électoraux historiques avec des indicateurs socio-économiques.

Le POC porte sur une zone géographique unique et restreinte.

## 2. Objectif

Démontrer qu'il est possible, à partir de données publiques, d'identifier des corrélations entre indicateurs socio-économiques et tendances électorales, puis de construire un modèle prédictif capable de projeter ces tendances à moyen terme (1 à 3 ans).

**Distinction clé** : le client demande de prédire des **tendances électorales** (évolution continue de l'orientation politique), pas uniquement des **résultats de scrutins** (événements ponctuels). Les résultats électoraux sont des points de vérification de la tendance, pas la tendance elle-même.

## 3. Périmètre

### 3.1 Zone géographique

Une zone unique doit être sélectionnée parmi :
- une commune
- un arrondissement
- une circonscription législative
- un département

Le choix doit être justifié selon trois critères :
- **Disponibilité des données** : la zone doit disposer de jeux de données publics suffisants sur les indicateurs retenus et les résultats électoraux.
- **Représentativité** : la zone doit présenter une diversité suffisante pour que l'analyse ait du sens (éviter les zones trop homogènes).
- **Taille exploitable** : la volumétrie doit être suffisante pour entraîner un modèle, sans être ingérable pour un POC.

### 3.2 Indicateurs retenus

Les indicateurs suivants sont demandés par le client (liste minimale) :
- Sécurité (criminalité, délinquance)
- Emploi (taux de chômage, offres d'emploi)
- Démographie / population (densité, évolution)
- Vie économique (nombre d'entreprises, créations/radiations)
- Pauvreté (taux de pauvreté, revenus médians)
- Vie associative (nombre d'associations)

Des indicateurs supplémentaires peuvent être ajoutés si pertinents :
- Enquêtes d'opinion
- Flux de réseaux sociaux
- Dépenses publiques locales

### 3.3 Données électorales et de tendance politique

Deux types de données complémentaires :

**Résultats électoraux (ponctuels)** : résultats historiques sur la zone choisie, couvrant plusieurs scrutins (présidentielles, législatives, européennes...). Ce sont des points d'ancrage fiables de la tendance politique à un instant donné. Les élections municipales sont écartées : le choix de candidats y est souvent limité et le vote est davantage lié à la personne qu'à la tendance politique, ce qui les rend peu représentatives.

**Données de tendance continue (à explorer)** : sources permettant de mesurer l'orientation politique entre les scrutins :
- Sondages d'opinion / baromètres politiques
- Enquêtes d'opinion locales ou nationales
- Éventuellement flux de réseaux sociaux

Les résultats électoraux et les données de tendance servent conjointement à construire une vision continue de l'orientation politique, que le modèle cherchera à prédire.

## 4. Fonctionnalités

### F1 - Collecte et centralisation des données

**Description** : Collecter les jeux de données publics depuis les sources identifiées et les centraliser dans un entrepôt unique.

**Sources identifiées** :
- data.gouv.fr (élections, sécurité, emploi, INSEE)
- Autres sources publiques pertinentes

**Critères d'acceptation** :
- Les données sont téléchargées et stockées localement.
- Chaque source est identifiée et traçable (origine, date de téléchargement, périmètre).

### F2 - Nettoyage et normalisation des données (pipeline ETL)

**Description** : Mettre en place un pipeline automatisé qui extrait, transforme et charge les données dans une base structurée.

**Critères d'acceptation** :
- Le pipeline est reproductible (relançable sans intervention manuelle).
- Les données sont nettoyées (valeurs manquantes traitées, doublons supprimés, formats homogénéisés).
- Les données sont normalisées (échelles comparables entre indicateurs).
- Le schéma de base de données est clairement nommé (tables et champs).
- Un schéma de flux de données (data flow) documente le pipeline.

### F3 - Analyse exploratoire

**Description** : Produire des visualisations descriptives pour identifier les corrélations entre chaque indicateur et les tendances électorales passées.

**Critères d'acceptation** :
- Des visualisations sont produites : cartes, histogrammes, heatmaps.
- Les corrélations entre chaque indicateur et les tendances électorales sont mises en évidence.
- L'indicateur le plus corrélé aux résultats électoraux est identifié et justifié.
- Les visualisations sont compréhensibles par des non-techniciens.

### F4 - Modèle prédictif

**Description** : Construire un modèle d'apprentissage supervisé capable de prédire les tendances électorales à partir des indicateurs socio-économiques.

**Critères d'acceptation** :
- Les données sont découpées en jeu d'entraînement et jeu de test.
- Plusieurs modèles sont testés et comparés.
- L'accuracy (pouvoir prédictif) du modèle retenu est mesurée et documentée.
- La méthodologie de l'apprentissage supervisé est définie et expliquée.

### F5 - Prédictions et visualisations prospectives

**Description** : Utiliser le modèle retenu pour générer des prédictions à 1, 2 et 3 ans et les présenter visuellement.

**Critères d'acceptation** :
- Des scénarios prospectifs sont produits pour les horizons 1 an, 2 ans et 3 ans.
- Les prédictions sont illustrées par des graphiques : courbes temporelles, cartes de chaleur, diagrammes de probabilité.
- Les visualisations sont accessibles à des non-techniciens et permettent une prise de décision stratégique.

## 5. Livrables attendus

| # | Livrable | Format |
|---|----------|--------|
| 1 | Dossier de synthèse (justification zone, critères, démarche, MCD, modèles, résultats, visualisations, accuracy, réponses aux questions) | Document |
| 2 | Jeu de données nettoyé et normalisé | SQL ou NoSQL |
| 3 | Code propre et commenté | Python / Jupyter |
| 4 | Support de soutenance | Présentation |

## 6. Questions auxquelles répondre

1. Parmi les données sélectionnées, laquelle est la plus corrélée aux résultats des élections ?
2. Qu'est-ce qu'un apprentissage supervisé ? (définition)
3. Comment mesure-t-on l'accuracy du modèle ?

## 7. Retours du coach (02/03/2026)

### 7.1 Décisions actées

**Carte blanche sur les choix techniques**
Le coach a indiqué que les résultats dépendent des données collectées et traitées. Tous les choix techniques (zone géographique, type de scrutin, granularité, indicateurs) sont à notre discrétion, à condition d'être justifiés.

**Démarche itérative attendue**
Plusieurs modèles doivent être testés et comparés. Le livrable "modèles testés" du cahier des charges est explicitement attendu.

### 7.2 Incohérence identifiée dans le sujet

Le cahier des charges demande :
- **En entrée** : des indicateurs socio-économiques à un instant T (approche causale)
- **En sortie** : des courbes de tendance à T+1, T+2, T+3 ans (approche temporelle)

Ces deux exigences sont contradictoires. Un modèle causal (indicateurs → tendance) produit une prédiction sur un même instant T. Un modèle temporel (historique → projection) produit une prédiction future à partir de résultat passées, mais n'utilise pas les indicateurs socio-éco comme entrées.

La seule façon de satisfaire les deux est de combiner les modèles :
1. **Modèle temporel** : projeter les indicateurs socio-éco futurs à partir de leur historique
2. **Modèle causal** : prédire la tendance politique à partir de ces indicateurs projetés

Cette approche implique une prédiction sur une prédiction (propagation d'erreurs), ce qui dégrade la fiabilité des résultats. Cependant, c'est la démarche et sa justification qui comptent, pas la qualité brute des prédictions.

**Décision** : on combine les deux approches pour coller au plus proche du sujet. L'incohérence et ses conséquences seront présentées et justifiées au jury. Décision finale à confirmer mercredi après-midi avec tous les groupes.

## 8. Analyse de faisabilité

### 8.1 Points à éclaircir (en attente d'exploration des données)

### 8.2 Volume de données et apprentissage supervisé

### 8.3 Alignement temporel des données

Les indicateurs socio-économiques sont publiés à des rythmes variés (annuel, trimestriel, par recensement). Les élections sont des événements ponctuels. Il faut définir une convention d'alignement : par exemple, associer à chaque scrutin les indicateurs de l'année N-1. Cette convention doit être documentée et justifiée.

### 8.4 Disponibilité et granularité des données publiques

Toutes les données ne sont pas disponibles à toutes les échelles géographiques ni sur toutes les périodes :
- Les données de sécurité sont souvent à l'échelle départementale, pas communale.
- Les données INSEE au niveau communal peuvent avoir des trous pour les petites communes.
- La vie associative est peu documentée dans les jeux de données publics standards.

Le choix de la zone géographique et des indicateurs doit être fait conjointement, en vérifiant au préalable la disponibilité réelle des données.

### 8.5 Synthèse par fonctionnalité

| Fonctionnalité | Faisabilité | Risques identifiés |
|---|---|---|
| F1 - Collecte | Aucun blocage | Formats hétérogènes entre sources, nettoyage potentiellement chronophage |
| F2 - Pipeline ETL | Aucun blocage | Alignement temporel à définir, conventions de nommage à stabiliser tôt |
| F3 - Analyse exploratoire | Aucun blocage | Les corrélations trouvées sur peu de points peuvent être non significatives |
| F4 - Modèle prédictif | Faisable sous réserve | Dépend du volume de données. Risque de surapprentissage sur un petit jeu de données |
| F5 - Prédictions à 1/2/3 ans | Nécessite clarification | L'horizon temporel n'a de sens que s'il est rattaché à des scrutins réels |

## 9. Contraintes

- Les visualisations et livrables doivent être lisibles par des non-techniciens.
- Les formats de sortie doivent être compatibles avec les outils internes : SQL, CSV, notebooks Jupyter, PowerBI.
- Le pipeline ETL doit être reproductible et traçable.
- La documentation doit être suffisamment exhaustive pour servir à un appel à financement.
