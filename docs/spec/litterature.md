# Revue de littérature — Facteurs d'influence sur les tendances électorales

## Objectif

Ce document justifie scientifiquement le choix des variables retenues pour le modèle prédictif du POC Electio-Analytics. Pour chaque variable, il présente :
- Les références scientifiques attestant de son influence sur le vote
- Le mécanisme causal attendu
- La direction d'influence
- La disponibilité des données sur data.gouv.fr / INSEE

---

## 1. Cadre théorique — Sociologie électorale classique

### 1.1 Géographie électorale (Siegfried, 1913)

**Référence :** André Siegfried, *Tableau politique de la France de l'Ouest sous la Troisième République*, Armand Colin, 1913.

**Apport :** Fondateur de la géographie électorale mondiale. Siegfried construit une chaîne causale en cinq maillons : nature du sol → type d'habitat (dispersé/groupé) → structure foncière (grande/petite propriété) → rapport social au clergé et aux notables → orientation politique.

**Mécanisme causal :** La grande propriété foncière crée une dépendance économique et morale des paysans envers les notables et le clergé catholique, produisant un conservatisme politique. La petite propriété produit une autonomie et un rapport laïque au monde, favorisant le vote à gauche.

**Direction :** Grande propriété + catholicisme intégré → droite ; petite propriété + laïcité → gauche.

**Variables extractibles :** type de commune (urbain/rural), densité d'habitat, structure foncière.

**Note critique :** La formule simplifiée "granite vote à droite, calcaire vote à gauche" a été critiquée comme géodéterministe (Raymond Aron). La richesse du modèle réside dans les médiations sociales, pas dans la géologie. Colloque du centenaire : Cerisy, 2013 ; ouvrage collectif Le Digol, Voilliot et Bussi (PUR, 2019).

---

### 1.2 Déterminants sociaux du vote (Lazarsfeld et al., 1944)

**Référence :** Paul F. Lazarsfeld, Bernard Berelson, Hazel Gaudet, *The People's Choice: How the Voter Makes Up His Mind in a Presidential Campaign*, Columbia University Press, 1944.

**Apport :** École de Columbia. Construction de l'Index of Political Predisposition (IPP) combinant trois variables : statut socio-économique (CSP), religion et lieu de résidence.

**Mécanisme causal :** Le vote est déterminé par le milieu social. Un individu protestant, aisé, rural vote républicain à 74 % ; un individu catholique, pauvre, urbain vote démocrate à 83 %. Quand les affiliations pointent dans des directions contradictoires (*cross-pressure*), l'individu décide plus tard et vote moins.

**Direction :** Classe populaire + urbanité → gauche ; classe aisée + ruralité → droite.

**Variables extractibles :** CSP, densité urbaine, revenus.

---

### 1.3 Classe et religion en France (Michelat & Simon, 1977)

**Référence :** Guy Michelat et Michel Simon, *Classe, religion et comportement politique*, Presses de la FNSP / Éditions sociales, 1977.

**Confirmation récente :** "Religion, classe sociale et comportement politique : l'épreuve de l'élection singulière de 2017", *L'Année sociologique*, 2021, vol. 71, n°2, pp. 369 sq. ([HAL hal-04042251](https://hal.science/hal-04042251/)).

**Apport :** Adaptation française de Columbia. L'effet de la religion n'est pas seulement confessionnel mais lié au *niveau d'intégration religieuse* (pratique régulière vs occasionnelle vs irréligion), qui structure un système de valeurs.

**Mécanisme causal :** Intégration religieuse forte → valeurs hiérarchiques, respect de l'autorité → vote à droite. Désintégration religieuse → valeurs égalitaires, conflit de classe → vote à gauche. Les deux variables (classe et religion) interagissent : un ouvrier pratiquant vote plus à droite qu'un cadre athée.

**Direction :** Ouvrier + irréligion → gauche maximale ; cadre + catholicisme pratiquant → droite maximale.

**Variables extractibles :** CSP, pratique religieuse (difficilement mesurable par données publiques — proxy possible via indicateurs territoriaux).

**Validation :** Le modèle reste significatif en 2017 (article *L'Année sociologique* 2021), même si ses effets se combinent avec de nouveaux clivages.

---

### 1.4 Inversion du clivage éducatif (Piketty, 2018-2019)

**Références :**
- Thomas Piketty, "Brahmin Left vs Merchant Right: Rising Inequality and the Changing Structure of Political Conflict", WID.world Working Paper 2018/7. [PDF](http://piketty.pse.ens.fr/files/Piketty2018.pdf)
- Amory Gethin, Clara Martínez-Toledano, Thomas Piketty, "Brahmin Left Versus Merchant Right: Changing Political Cleavages in 21 Western Democracies, 1948-2020", *Quarterly Journal of Economics*, 2022, vol. 137, n°1, pp. 1-48. [DOI](https://academic.oup.com/qje/article/137/1/1/6383014)
- Thomas Piketty, *Capital et idéologie*, Seuil, 2019.

**Apport :** Transformation structurelle longue du clivage éducatif. Dans les années 1950-70, le vote gauche est associé aux faibles niveaux d'éducation ET de revenu. Dans les années 1990-2010, le vote gauche est associé aux hauts niveaux d'éducation mais toujours aux faibles revenus/patrimoines.

**Mécanisme causal :** Émergence d'un système de partis à élites multiples : la "gauche brahmane" (élite scolaire) vs la "droite marchande" (élite économique). Les classes populaires peu diplômées se retrouvent sans représentation politique adaptée → report vers l'abstention ou les partis populistes. En France : en 1956, les partis de gauche obtenaient 17 points de moins chez les diplômés du supérieur ; en 2012, 9 points de plus.

**Direction :** Diplôme élevé (Bac+3 et plus) → gauche/centre ; revenu/patrimoine élevé → droite ; diplôme faible + revenu faible → abstention ou vote populiste (RN).

**Variables extractibles :** niveau de diplôme, revenu médian, patrimoine immobilier, interaction diplôme × revenu.

---

### 1.5 Classes géosociales (Cagé & Piketty, 2023)

**Référence :** Julia Cagé et Thomas Piketty, *Une histoire du conflit politique. Élections et inégalités sociales en France, 1789-2022*, Seuil, 2023. Données en libre accès : [unehistoireduconflitpolitique.fr](https://www.unehistoireduconflitpolitique.fr/).

**Apport :** Numérisation inédite des données électorales et socio-économiques de 36 000 communes sur deux siècles. Introduction du concept de "classe géosociale" croisant revenu, capital immobilier et secteur économique dominant.

**Résultat clé :** Les géo-classes sociales expliquent **70 % des écarts de vote entre communes**. Depuis le début des années 1990, les différences électorales selon le revenu communal se sont accrues.

**Variables extractibles :** revenu communal, patrimoine immobilier, secteur économique dominant.

---

### 1.6 Synthèse récente

**Référence :** Frédéric Gonthier, "Bilan raisonné de la sociologie électorale en France (1951-2021)", *Revue française de science politique*, 2021, vol. 71, n°5-6, pp. 789 sq. [Cairn](https://www.cairn.info/revue-francaise-de-science-politique-2021-5-page-789.htm).

---

## 2. Facteurs économiques

### 2.1 Taux de chômage

**Références :**
- Richard Nadeau, Michael Lewis-Beck, Éric Bélanger, "Economics and Elections Revisited", *Comparative Political Studies*, 2013. [DOI](https://journals.sagepub.com/doi/abs/10.1177/0010414012463877)
- Diane Bolet, "Local labour market competition and radical right voting: Evidence from France", *European Journal of Political Research*, 2020, vol. 59, n°4. [DOI](https://onlinelibrary.wiley.com/doi/10.1111/1475-6765.12378)
- Pavlos Vasilopoulos, Haley McAvay, Sylvain Brouard, "Residential Context and Voting for the Far Right", *Political Behavior*, 2022. [DOI](https://link.springer.com/article/10.1007/s11109-021-09676-z)
- Pascal Perrineau, *La France au front*, Fayard, 2014. [HAL](https://hal.science/hal-01052605/)

**Mécanisme causal :** La frustration économique générée par le chômage produit un vote de rejet dirigé contre les partis de gouvernement (reward-punish theory) et favorise les forces populistes.

**Direction :** ↑ chômage → ↑ vote RN/extrêmes, ↓ voix pour le gouvernement sortant.

**Résultat chiffré :** Une hausse d'un point de pourcentage du taux de chômage est associée à une perte d'environ 5 % des voix du premier tour pour la coalition gouvernementale sortante (Nadeau et al., 2013, données régionales françaises 1978-1993). Aux municipales dans le Pas-de-Calais, Marine Le Pen a obtenu plus de 60 % dans certaines communes à fort chômage (Bolet, 2020).

**Données :** INSEE — taux de chômage localisé par zone d'emploi et département (1954-2024). France Travail — demandeurs d'emploi par zone. Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

### 2.2 Revenu médian et pauvreté

**Références :**
- Julia Cagé et Thomas Piketty, *Une histoire du conflit politique*, Seuil, 2023.
- Jérôme Fourquet, *L'Archipel français*, Seuil, 2019.
- Guillaume Bazot, "Structure économique et sociale des territoires et vote populiste en France", Fondapol, 2024. [Lien](https://www.fondapol.org/etude/structure-economique-et-sociale-des-territoires-et-vote-populiste-en-france/)

**Mécanisme causal :** La précarité économique engendre un sentiment d'abandon par les élites politiques. Les ménages à faible revenu se tournent vers des offres politiques de rupture.

**Direction :** ↓ revenu → ↑ vote populiste (RN en zones rurales, LFI en zones urbaines).

**Résultat clé :** Les géo-classes sociales (revenu + patrimoine + CSP communale) expliquent 70 % des écarts de vote entre communes (Cagé & Piketty, 2023).

**Données :** INSEE Filosofi — revenus, pauvreté, niveaux de vie par commune et IRIS (2015-2022). Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

### 2.3 Inégalités

**Références :**
- Cagé et Piketty (2023), op. cit.
- Ugur Polat et Ahmet Bozdogan, "Economic voting and the radical right in Europe", *Empirica*, 2026. [DOI](https://link.springer.com/article/10.1007/s10663-025-09664-0)
- Florian Dorn et al., "Economic Deprivation and Radical Voting: Evidence from Germany", ifo Institute Working Paper, 2020. [Lien](https://www.ifo.de/en/publications/2020/working-paper/economic-deprivation-and-radical-voting-evidence-germany)

**Mécanisme causal :** La perception d'injustice distributive génère une défiance envers les institutions et les élites, alimentant la radicalisation aux deux extrêmes.

**Direction :** ↑ inégalités → ↑ votes extrêmes (droite et gauche).

**Note :** La littérature utilise davantage le taux de pauvreté relative que le Gini au niveau infra-national. Le Gini départemental/régional (INSEE) est disponible mais peu exploité dans les études électorales françaises.

**Données :** INSEE Filosofi — indicateurs d'inégalités par commune. Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

### 2.4 Créations et destructions d'entreprises

**Références :**
- Michael S. Lewis-Beck, *Economics and Elections: The Major Western Democracies*, University of Michigan Press, 1988.
- Raymond Duch et Randolph Stevenson, *The Economic Vote*, Cambridge University Press, 2008. [DOI](https://www.cambridge.org/core/books/economic-vote/57D49941B6465119EA9CA9D2D8518903)

**Mécanisme causal :** Le dynamisme économique local (créations nettes) génère confiance et satisfaction → vote modéré. Les déserts économiques (destructions nettes, fermetures) alimentent la défiance → vote protestataire.

**Direction :** ↑ dynamisme → ↓ vote protestataire ; ↑ destructions → ↑ vote antisystème.

**Note :** Aucune étude académique française spécifiquement centrée sur le lien créations/destructions d'entreprises → vote n'a été identifiée. Le chômage est utilisé comme proxy. Le croisement SIRENE × données électorales constitue une piste de recherche originale.

**Données :** INSEE — créations d'entreprises par commune (2012-2024). Base SIRENE — radiations. Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

### 2.5 Emploi public vs privé

**Références :**
- Michelat et Simon (1977), op. cit.
- Luc Rouban, "Le vote des fonctionnaires à l'élection présidentielle de 2022", CEVIPOF, 2022. [HAL](https://sciencespo.hal.science/hal-03790691)
- Luc Rouban, Note CEVIPOF vote des fonctionnaires européennes/législatives 2024. [PDF](https://www.sciencespo.fr/cevipof/sites/sciencespo.fr.cevipof/files/Noteelectionseuropeennesetlegislatives_LR_votedesfonctionnaires_septembre2024_V2.pdf)

**Mécanisme causal :** Les agents publics bénéficient d'une stabilité d'emploi qui réduit leur exposition aux risques économiques et les rend historiquement moins réceptifs aux promesses de rupture.

**Direction (historique) :** Emploi public → vote gauche. **Direction (tendance récente) :** Érosion de ce lien — entre 2017 et 2022, Marine Le Pen a gagné **+9 points chez les agents publics**. En 2022, la gauche ne recueille plus que 37 % des suffrages de la Fonction Publique d'État. Le vote RN progresse dans les trois fonctions publiques, surtout dans la FPH.

**Données :** INSEE recensement — emploi par secteur (public/privé) au niveau communal (2011-2022). Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

## 3. Facteurs territoriaux et démographiques

### 3.1 Densité de population (urbain / périurbain / rural)

**Références :**
- Hervé Le Bras et Emmanuel Todd, *Le Mystère français*, Seuil, 2013.
- Christophe Guilluy, *Fractures françaises*, Flammarion, 2010 ; *La France périphérique*, Flammarion, 2014.
- Jérôme Fourquet et Sylvain Manternach, "Comprendre la géographie du vote RN en 2024", Institut Terram, 2024. [PDF](https://www.institut-terram.org/wp-content/uploads/2024/09/IT_ETUDE-00005_FOURQUET-MANTERNACH_2024-09-09_w.pdf)

**Mécanisme causal :** Le vote s'organise selon un "gradient d'urbanité" (Jacques Lévy). Les métropoles, concentrant les diplômés et les CSP+, votent pour des partis d'ouverture. Les périphéries et zones de faible densité, touchées par la désindustrialisation et la relégation spatiale, penchent vers les droites nationalistes ou l'abstention.

**Direction :** Zones denses et métropolitaines → gauche/centre ; zones périurbaines et rurales → droite/RN.

**Note critique :** Guilluy est très cité dans le débat public mais fait l'objet de critiques académiques sérieuses (absence de méthode rigoureuse, données non sourcées). À citer comme essayiste influent plutôt que chercheur au sens strict.

**Données :** INSEE — grille communale de densité, zonage en aires d'attraction des villes (AAV 2020). Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

### 3.2 Évolution démographique

**Références :**
- Guilluy (2014), op. cit.
- Bernard Schwengler, "L'ouvrier caché : le paradoxe du vote rural d'extrême droite dans la France du Nord-Est", *Revue française de science politique*, 2003, vol. 53, n°4, pp. 513-533. [Cairn](https://www.cairn.info/revue-francaise-de-science-politique-2003-4-page-513.htm)

**Mécanisme causal :** La décroissance démographique d'une commune → perte de services, de commerces, de représentation symbolique → sentiment d'abandon → vote protestataire.

**Direction :** ↓ population → ↑ vote RN / abstention.

**Données :** INSEE — série historique du recensement par commune (1968-2022), populations municipales (1968-2023). Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

### 3.3 Structure par âge

**Références :**
- CEVIPOF, Baromètre de la confiance politique (vagues annuelles depuis 2011). [Lien](https://www.sciencespo.fr/cevipof/fr/etudes-enquetes/barometre-confiance-politique/)
- IFOP, "Les jeunes et l'élection présidentielle de 2022". [Lien](https://www.ifop.com/publication/les-jeunes-et-lelection-presidentielle-de-2022/)
- Ipsos, "70 % des moins de 35 ans n'ont pas voté" (législatives 2022). [Lien](https://www.ipsos.com/fr-fr/legislatives-2022/70-des-moins-de-35-ans-nont-pas-vote)
- INSEE Première n°1929, "Vingt ans de participation électorale", 2023. [Lien](https://www.insee.fr/fr/statistiques/6658143)

**Mécanisme causal :** Les jeunes (18-35 ans), confrontés à la précarité et au sentiment d'impuissance, s'abstiennent massivement (70 % aux législatives 2022). Quand ils votent : gauche radicale (LFI) ou extrême droite selon le profil socioéconomique. Les retraités, bénéficiant de stabilité économique et d'un attachement aux institutions, participent fortement et votent droite/centre-droit.

**Direction :** Jeunes → abstention massive, si vote : gauche ou extrême droite ; retraités → forte participation, droite/centre-droit.

**Données :** INSEE recensement — structure par âge communale. Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

### 3.4 Part de propriétaires vs locataires

**Références :**
- IFOP, "La France des propriétaires, vote à droite ?", 2012. [Lien](https://www.ifop.com/publication/france-des-proprietaires-vote/)
- Violaine Girard, *Le vote FN au village*, Éditions du Croquant, 2017. Recension : [Cairn](https://shs.cairn.info/revue-projet-2018-3-page-112?lang=fr).
- "Le vote pavillonnaire existe-t-il ?", *Politix*, 2008, n°83. [Cairn](https://www.cairn.info/revue-politix-2008-3-page-23.htm)
- Andrew Hall et Jesse Yoder, "Does Homeownership Influence Political Behavior?", *Journal of Politics*, 2022, vol. 84, n°1. [DOI](https://www.journals.uchicago.edu/doi/10.1086/714932)

**Mécanisme causal :** La propriété immobilière génère un intérêt patrimonial (protection de l'investissement, fiscalité, sécurité du voisinage) → préférences conservatrices. La sélection socioéconomique (propriétaires plus âgés et aisés en moyenne) amplifie l'effet.

**Direction :** ↑ propriétaires → ↑ vote droite/centre-droit (effet net modéré après contrôle de l'âge et du revenu) ; locataires HLM → vote gauche.

**Données :** INSEE recensement — statut d'occupation du logement par commune. Filosofi. Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

### 3.5 Part de population étrangère / immigration

**Références :**
- Jérôme Fourquet, *L'Archipel français*, Seuil, 2019.
- Fourquet et Manternach, "Comprendre la géographie du vote RN en 2024", Institut Terram, 2024. [PDF](https://www.institut-terram.org/wp-content/uploads/2024/09/IT_ETUDE-00005_FOURQUET-MANTERNACH_2024-09-09_w.pdf)
- Schwengler (2003), op. cit.
- Le Bras et Todd (2013), op. cit.

**Mécanisme causal :** Le "paradoxe de la distance" : les scores les plus élevés du RN se trouvent dans des zones à faible présence immigrée (ruralité profonde, nord-est), tandis que l'Île-de-France, à forte densité de population étrangère, vote faiblement RN. Ce n'est pas la présence réelle d'immigrés qui prédit le vote RN, mais la perception de la menace combinée à des fragilités socio-économiques locales. Fourquet (2024) développe un indicateur composite IPI (Immigration, Pauvreté, Insécurité) qui explique mieux le vote RN que chaque variable prise isolément.

**Direction :** Fort taux de population étrangère → vote RN faible ; faible taux + déclin économique → vote RN fort. Relation non linéaire.

**Données :** INSEE recensement — part des immigrés et des étrangers par commune. Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

## 4. Facteurs sociaux et éducation

### 4.1 Niveau de diplôme

**Références :**
- Piketty (2018), Gethin, Martínez-Toledano et Piketty (2022), op. cit.
- INSEE Première n°1929, "Vingt ans de participation électorale", 2023. [Lien](https://www.insee.fr/fr/statistiques/6658143)
- Ipsos, "Sociologie des électorats législatives 2024". [Lien](https://www.ipsos.com/fr-fr/legislatives-2024/sociologie-des-electorats-legislatives-2024)

**Mécanisme causal :** Le clivage diplômés/non-diplômés a remplacé le clivage riche/pauvre comme structurant du vote. La massification de l'enseignement supérieur a inversé la relation : les diplômés du supérieur votent gauche/centre, les non-diplômés se tournent vers le RN ou l'abstention. Les écarts de participation selon le diplôme ont quasi doublé entre 2002 et 2022 (INSEE).

**Direction :** ↑ diplômés → ↑ gauche/centre ; ↓ diplômés → ↑ RN et abstention.

**Résultat chiffré :** Aux législatives 2024, 49 % des sans-bac votent RN contre ~15-20 % des Bac+3 et plus (Ipsos).

**Données :** INSEE recensement — niveau de diplôme par commune et IRIS. Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

### 4.2 CSP dominante

**Références :**
- Michelat et Simon (1977), op. cit.
- Nonna Mayer, "Que reste-t-il du vote de classe ? Le cas français", *Lien social et Politiques*, 2004. [HAL PDF](https://sciencespo.hal.science/hal-03462311/file/2004-mayer-que-reste-t-il-du-vote-de-classe.pdf)
- Nonna Mayer, "Les électeurs du Front national", 2017. [HAL PDF](https://sciencespo.hal.science/hal-01524034/file/2017-mayer-les-electeurs-du-front-national.pdf)
- Luc Rouban, *Les ressorts cachés du vote RN*, Presses de Sciences Po, 2024.

**Mécanisme causal :** La classe ouvrière déchristianisée votait massivement à gauche (PCF/PS). Depuis les années 1980, réalignement majeur : les ouvriers ont abandonné la gauche pour le RN, perçu comme défenseur de leurs intérêts face à la mondialisation. Les cadres et professions intellectuelles se sont déplacés vers le centre-gauche. Mayer nuance : le déterminant premier reste attitudinal (ethnocentrisme) plutôt que strictement catégoriel.

**Direction :** Ouvriers/employés → vote RN dominant ; cadres/professions intellectuelles → gauche modérée/centre ; indépendants/artisans → droite traditionnelle/RN.

**Résultat chiffré :** Aux législatives 2024, le RN atteint 57 % chez les ouvriers et 44 % chez les employés (Mayer).

**Données :** INSEE recensement — CSP par commune et IRIS. Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

### 4.3 Vie associative (capital social)

**Références :**
- Robert D. Putnam, *Making Democracy Work*, Princeton University Press, 1993.
- Mayer et Perrineau (dir.), "Les conséquences politiques du capital social : le cas français", *Revue internationale de politique comparée*, 2003, vol. 10, n°3. [Cairn](https://cairn.info/revue-internationale-de-politique-comparee-2003-3-page-381.html)
- Julien Talpin, "Les associations, rempart contre l'abstention et l'extrême droite ?", Carenews, 2022-2024.

**Mécanisme causal :** L'appartenance associative génère des réseaux de confiance interpersonnelle (bonding et bridging capital) qui augmentent la disposition à participer électoralement. L'adaptation française nuance Putnam : la simple adhésion n'accroît pas mécaniquement la participation, sauf pour le tiers le plus engagé — lequel est aussi socialement et culturellement privilégié.

**Direction :** ↑ associations → ↓ abstention (effet robuste) ; lien avec vote RN indirect et conditionnel.

**Données :** Répertoire National des Associations (RNA) sur data.gouv.fr ; base SIRENE (filtre associations loi 1901). Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

## 5. Sécurité et vote

### 5.1 Taux de criminalité / délinquance

**Références :**
- Pascal Perrineau et Nonna Mayer, "Pourquoi votent-ils pour le Front national ?", 1990. [HAL PDF](https://sciencespo.hal.science/hal-01315813/file/1990-mayer-perrineau-vote-fn.pdf)
- Pascal Perrineau, *Cette France de gauche qui vote FN*, Seuil, 2017.
- Luc Rouban, "La cité de la peur : l'insécurité et le choix politique", CEVIPOF, Note Baromètre vague 15, mars 2024. [PDF](https://www.sciencespo.fr/cevipof/sites/sciencespo.fr.cevipof/files/NoteBaroV15_LR_citedelapeur_mars2024.pdf)

**Mécanisme causal :** Face à une criminalité perçue ou réelle, les individus cherchent une offre politique sécuritaire. Perrineau a établi dès 1990 une corrélation géographique entre zones de forte délinquance et vote FN. Rouban (2024) nuance : l'insécurité ne produit pas mécaniquement un vote d'extrême droite. Ce qui agit, c'est l'interprétation culturelle de l'insécurité (liée à la question migratoire), non la criminalité brute.

**Direction :** ↑ délinquance → ↑ vote RN dans certaines configurations (corrélation géographique établie mais effet direct statistiquement modeste). L'effet est médiatisé par les attitudes culturelles.

**Données :** SSMSI — bases communale et départementale des indicateurs de crimes et délits (2016-2024). Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

### 5.2 Perception vs réalité de l'insécurité

**Références :**
- Sebastian Roché, *Le sentiment d'insécurité*, PUF, 1993.
- Laurent Mucchielli, *Violences et insécurité. Fantasmes et réalités dans le débat français*, La Découverte, 2002.
- Rouban (2024), op. cit.

**Tension théorique :** Roché (1993) établit un ancrage empirique réel du sentiment d'insécurité dans les taux de délinquance locaux. Mucchielli (2002) soutient la thèse inverse : le sentiment est largement construit médiatiquement, déconnecté des chiffres réels. Rouban (2024) apporte la synthèse : le déterminant principal du sentiment d'insécurité n'est pas la classe sociale ou la précarité, mais le **niveau de libéralisme culturel** (attitudes vis-à-vis de l'immigration).

**Direction :** Sentiment d'insécurité → vote RN, mais médiatisé par le rejet de l'immigration et l'ethnocentrisme. Corrélation faible entre taux objectifs de criminalité et vote RN au niveau individuel.

**Implication pour le modèle :** Les données objectives de criminalité sont une variable utile mais dont le pouvoir prédictif direct est limité. Son interaction avec d'autres variables (immigration, diplôme) est plus informative.

**Données :** SSMSI/Interstats — données départementales. Disponible sur [data.gouv.fr](https://www.data.gouv.fr). Les données de sentiment d'insécurité ne sont pas disponibles en open data à granularité fine (enquêtes CEVIPOF).

---

## 6. L'abstention comme variable

### 6.1 Facteurs socio-économiques de l'abstention

**Référence :** Céline Braconnier et Jean-Yves Dormagen, *La démocratie de l'abstention. Aux origines de la démobilisation électorale en milieux populaires*, Folio/Gallimard, 2007. [HAL](https://sciencespo.hal.science/hal-01045084/document)

**Mécanisme causal :** Trente ans de chômage de masse, de précarité et de ghettoïsation des quartiers populaires dissolvent les identités politiques. La probabilité de voter croît linéairement avec l'âge, le diplôme et la stabilité professionnelle. Exemple : une retraitée diplômée de 65-70 ans avait 98 % de chances d'avoir voté en 2012 ; une ouvrière non diplômée de 18-24 ans présentait 33 % de probabilité d'abstention.

**Direction :** Jeunesse + précarité + faible diplôme → abstention forte.

---

### 6.2 Abstention aux scrutins précédents

**Référence :** Céline Braconnier, "Une démocratie de l'abstention", *Hérodote*, 2014/3, n°154. [Cairn](https://www.cairn.info/revue-herodote-2014-3-page-42.htm)

**Mécanisme causal :** La participation électorale est devenue largement intermittente. L'abstention répétée constitue un signal de désaffiliation politique et un prédicteur fort de l'abstention future. Elle corrèle aussi avec le vote protestataire lors des épisodes de (re)mobilisation.

**Direction :** Abstention passée répétée → abstention future ; (re)mobilisation → vote protestataire.

**Données :** Résultats électoraux par bureau de vote sur [data.gouv.fr](https://www.data.gouv.fr) (Ministère de l'Intérieur).

---

## 7. Variables non conventionnelles (exploratoires)

### 7.1 Prix de l'immobilier / effet patrimoine

**Références :**
- Jacques Capdevielle et Élisabeth Dupoirier, *France de gauche, vote à droite*, Presses de Sciences Po, 1981.
- Éric Kerrouche et al., "La persistance de l'effet patrimoine lors des élections présidentielles françaises", *Revue française de science politique*, 2011, vol. 61, n°4. [Cairn](https://www.cairn.info/revue-francaise-de-science-politique-2011-4-page-659.htm)

**Mécanisme causal :** La possession de patrimoine immobilier accroît significativement la probabilité de voter à droite. Les actifs risqués (résidence secondaire, valeurs mobilières, immobilier locatif) sont les prédicteurs les plus puissants du vote droite entre 1988 et 2007. La hausse des prix génère pour les locataires une frustration (exclusion du marché) pouvant orienter vers des votes protestataires.

**Direction :** Propriétaires enrichis par la hausse → droite ; locataires exclus du marché → frustration → gauche/protestataire.

**Données :** DVF (Demandes de Valeurs Foncières) sur [data.gouv.fr](https://www.data.gouv.fr/datasets/demandes-de-valeurs-foncieres) — transactions immobilières géolocalisées depuis 2014.

---

### 7.2 Accès aux services publics

**Références :** Littérature territoriale, rapports parlementaires, analyses Le Monde. Pas d'étude académique peer-reviewed identifiée spécifiquement.

**Mécanisme causal :** La fermeture progressive d'écoles, de maternités, de services de santé et d'administration génère un sentiment d'abandon dans les territoires concernés, se traduisant par un renforcement du vote protestataire.

**Direction :** ↓ services publics → ↑ sentiment d'abandon → ↑ vote protestataire.

**Données :** INSEE — Base Permanente des Équipements (BPE), 229 types d'équipements par commune et IRIS. Mise à jour annuelle. [Lien](https://www.insee.fr/fr/metadonnees/source/serie/s1161). Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

### 7.3 Mobilité / temps de trajet domicile-travail

**Références :**
- CREST/INSEE, "Les déterminants de la mobilisation des Gilets jaunes", Document de Travail 2019-06. [PDF](https://crest.science/RePEc/wpstorage/2019-06.pdf)
- Publication dans *Revue économique*, 2020/1. [Cairn](https://shs.cairn.info/revue-economique-2020-1-page-109?lang=fr)

**Mécanisme causal :** Corrélation forte entre la mobilisation Gilets jaunes et les variables de mobilité : distances de navettage et ralentissement des routes secondaires à 80 km/h. La dépendance automobile des zones rurales et périurbaines crée une vulnérabilité aux chocs de prix de l'énergie, source de frustration sociale se traduisant en vote antisystème.

**Direction :** ↑ dépendance automobile + ↑ temps trajet → ↑ frustration → ↑ vote protestataire.

**Données :** INSEE recensement — fichiers flux de mobilité domicile-travail. [Lien](https://www.insee.fr/fr/information/2383337). Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

### 7.4 Dépenses publiques locales

**Référence :** Yann Le Lann et Pauline Rameau, "Dépenses visibles et perspectives de réélection dans un scrutin à deux tours : le cas des élections municipales françaises", *Revue d'économie politique*, 2011/3, vol. 121. [Cairn](https://cairn.info/revue-d-economie-politique-2011-3-page-435.htm)

**Mécanisme causal :** Les dépenses d'investissement et d'équipement, plus visibles que les dépenses de fonctionnement, ont un impact positif sur les perspectives de réélection des sortants.

**Direction :** ↑ investissement local visible → ↑ prime au sortant.

**Données :** DGCL — comptes de gestion des collectivités locales. Disponible sur [collectivites-locales.gouv.fr](https://www.collectivites-locales.gouv.fr) et [data.gouv.fr](https://www.data.gouv.fr).

---

### 7.5 Logement social (part HLM)

**Références :** Littérature OFCE/INED sur la ségrégation résidentielle. [OFCE](https://www.ofce.sciences-po.fr/blog/10285-2/)

**Mécanisme causal :** La concentration de logements sociaux génère une ségrégation spatiale des populations précaires, produisant historiquement un vote de gauche/extrême gauche (PCF, banlieues rouges). Évolution récente vers vote protestataire (RN) ou abstention dans certains quartiers.

**Direction :** Forte concentration HLM → historiquement gauche ; évolution vers protestataire/abstention.

**Données :** RPLS (Répertoire du Parc Locatif Social) — données communales et IRIS. Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

### 7.6 Évolution du tissu commercial

**Références :** Rapports parlementaires sur la désertification commerciale, analyses IFOP.

**Mécanisme causal :** La fermeture de commerces dans les centres-villes moyens et bourgs ruraux génère un sentiment de déclin et d'abandon, se traduisant par un vote protestataire amplifié.

**Direction :** ↓ commerces → ↑ sentiment de déclin → ↑ vote protestataire.

**Données :** SIRENE (INSEE) — créations et radiations d'établissements par commune. BPE — gammes d'équipements commerciaux. Disponible sur [data.gouv.fr](https://www.data.gouv.fr).

---

## 8. Synthèse : variables retenues et justification

### Variables à fort appui scientifique (prioritaires)

| Variable | Références clés | Direction | Données |
|---|---|---|---|
| Niveau de diplôme | Piketty (2018), Gethin et al. (2022), Ipsos (2024) | ↑ diplôme → gauche/centre ; ↓ diplôme → RN | INSEE recensement |
| CSP dominante | Michelat & Simon (1977), Mayer (2004, 2017), Rouban (2024) | Ouvriers → RN ; cadres → gauche/centre | INSEE recensement |
| Taux de chômage | Nadeau et al. (2013), Bolet (2020), Vasilopoulos et al. (2022) | ↑ chômage → ↑ vote protestataire | INSEE, France Travail |
| Revenu médian / pauvreté | Cagé & Piketty (2023), Fourquet (2019) | ↓ revenu → ↑ vote populiste | INSEE Filosofi |
| Densité de population | Le Bras & Todd (2013), Guilluy (2014) | Urbain → gauche ; rural → droite/RN | INSEE recensement |
| Structure par âge | CEVIPOF, IFOP (2022), Ipsos (2022) | Jeunes → abstention ; retraités → droite | INSEE recensement |
| Taux de participation (scrutins précédents) | Braconnier & Dormagen (2007), Braconnier (2014) | ↑ abstention passée → ↑ abstention future / vote protestataire | data.gouv.fr élections |

### Variables à appui scientifique modéré (secondaires)

| Variable | Références clés | Direction | Données |
|---|---|---|---|
| Taux de criminalité | Perrineau (1990), Rouban (2024) | Effet médiatisé par les attitudes culturelles | SSMSI |
| Part de propriétaires | IFOP (2012), Girard (2017), Hall & Yoder (2022) | Propriétaires → droite (effet modéré) | INSEE recensement |
| Part population étrangère | Fourquet (2019), Schwengler (2003) | Relation non linéaire (paradoxe de la distance) | INSEE recensement |
| Emploi public vs privé | Michelat & Simon (1977), Rouban (2022) | Historiquement gauche, érosion depuis 2012 | INSEE recensement |
| Vie associative | Putnam (1993), Mayer & Perrineau (2003) | ↑ associations → ↓ abstention | RNA, SIRENE |

### Variables exploratoires (à valider par l'analyse)

| Variable | Références clés | Direction | Données |
|---|---|---|---|
| Prix immobilier | Capdevielle & Dupoirier (1981), Kerrouche (2011) | Propriétaires enrichis → droite ; locataires exclus → protestataire | DVF |
| Accès aux services publics | Rapports parlementaires, presse | ↓ services → ↑ vote protestataire | BPE INSEE |
| Mobilité domicile-travail | CREST (2019) | ↑ dépendance auto → ↑ frustration → protestataire | INSEE navettes |
| Dépenses publiques locales | Le Lann & Rameau (2011) | ↑ investissement → prime au sortant | DGCL |
| Part logement social | Littérature OFCE | Historiquement gauche ; évolution | RPLS |
| Tissu commercial | Rapports, presse | ↓ commerces → ↑ protestataire | SIRENE |
| Créations/destructions entreprises | Lewis-Beck (1988), Duch & Stevenson (2008) | Dynamisme → modéré ; déclin → protestataire | SIRENE, INSEE |
| Inégalités | Dorn et al. (2020), Polat & Bozdogan (2026) | ↑ inégalités → ↑ votes extrêmes | INSEE Filosofi |

---

## 9. Références bibliographiques

### Ouvrages fondamentaux

- Braconnier C. et Dormagen J.-Y., *La démocratie de l'abstention*, Folio/Gallimard, 2007.
- Cagé J. et Piketty T., *Une histoire du conflit politique*, Seuil, 2023.
- Capdevielle J. et Dupoirier É., *France de gauche, vote à droite*, Presses de Sciences Po, 1981.
- Fourquet J., *L'Archipel français*, Seuil, 2019.
- Guilluy C., *La France périphérique*, Flammarion, 2014.
- Lazarsfeld P., Berelson B. et Gaudet H., *The People's Choice*, Columbia University Press, 1944.
- Le Bras H. et Todd E., *Le Mystère français*, Seuil, 2013.
- Lewis-Beck M., *Economics and Elections*, University of Michigan Press, 1988.
- Michelat G. et Simon M., *Classe, religion et comportement politique*, FNSP/Éditions sociales, 1977.
- Mucchielli L., *Violences et insécurité*, La Découverte, 2002.
- Perrineau P., *La France au front*, Fayard, 2014.
- Piketty T., *Capital et idéologie*, Seuil, 2019.
- Putnam R., *Making Democracy Work*, Princeton University Press, 1993.
- Roché S., *Le sentiment d'insécurité*, PUF, 1993.
- Rouban L., *Les ressorts cachés du vote RN*, Presses de Sciences Po, 2024.
- Siegfried A., *Tableau politique de la France de l'Ouest*, Armand Colin, 1913.

### Articles académiques

- Bolet D., "Local labour market competition and radical right voting: Evidence from France", *European Journal of Political Research*, 2020.
- Gethin A., Martínez-Toledano C. et Piketty T., "Brahmin Left Versus Merchant Right", *Quarterly Journal of Economics*, 2022.
- Gonthier F., "Bilan raisonné de la sociologie électorale en France (1951-2021)", *RFSP*, 2021.
- Kerrouche É. et al., "La persistance de l'effet patrimoine", *RFSP*, 2011.
- Le Lann Y. et Rameau P., "Dépenses visibles et perspectives de réélection", *Revue d'économie politique*, 2011.
- Mayer N., "Que reste-t-il du vote de classe ?", *Lien social et Politiques*, 2004.
- Nadeau R., Lewis-Beck M. et Bélanger É., "Economics and Elections Revisited", *Comparative Political Studies*, 2013.
- Schwengler B., "L'ouvrier caché", *RFSP*, 2003.
- Vasilopoulos P. et al., "Residential Context and Voting for the Far Right", *Political Behavior*, 2022.

### Notes et rapports institutionnels

- Bazot G., "Structure économique et sociale des territoires et vote populiste en France", Fondapol, 2024.
- CREST/INSEE, "Les déterminants de la mobilisation des Gilets jaunes", Document de Travail 2019-06.
- Fourquet J. et Manternach S., "Comprendre la géographie du vote RN en 2024", Institut Terram, 2024.
- Rouban L., "Le vote des fonctionnaires à l'élection présidentielle de 2022", CEVIPOF, 2022.
- Rouban L., "La cité de la peur : l'insécurité et le choix politique", CEVIPOF, mars 2024.

### Enquêtes et données post-électorales

- CEVIPOF, Baromètre de la confiance politique (vagues annuelles depuis 2011).
- IFOP, "Les jeunes et l'élection présidentielle de 2022".
- INSEE Première n°1929, "Vingt ans de participation électorale", 2023.
- Ipsos, "Sociologie des électorats législatives 2024".
