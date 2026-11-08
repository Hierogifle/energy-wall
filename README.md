# Energy Wall : l'IA face au mur énergétique

Projet M2, La Plateforme_. Veille scientifique, modélisation prédictive et recommandations pour un ministre.

**Équipe :** Romuald Courtois, Émile Le Gouz de Saint-Seine, Olivier Bonnin

| Livrable | Où le trouver |
|----------|---------------|
| Présentation (diaporama HTML, et sa version PDF) | [presentation/index.html](presentation/index.html), [presentation/energy-wall.pdf](presentation/energy-wall.pdf) |
| Trame orale de la présentation | [presentation/trame.md](presentation/trame.md) |
| Notebook de calcul et data visualisations | [notebooks/energy_wall.ipynb](notebooks/energy_wall.ipynb) |
| Veille scientifique et technologique | [ce README, section Veille](#veille-scientifique-et-technologique) |

## Sommaire

- [Le projet](#le-projet)
- [Le dépôt](#le-dépôt)
- [Veille scientifique et technologique](#veille-scientifique-et-technologique)
  - [Ce qu'il faut retenir](#ce-quil-faut-retenir)
  - [1. Trajectoire](#1-trajectoire--comment-on-en-est-arrivé-là)
  - [2. Obstacles](#2-obstacles--ce-qui-na-pas-été-franchi)
  - [3. Innovations](#3-innovations--ce-qui-peut-aider-à-court-et-moyen-terme)
  - [4. Impacts](#4-impacts--climat-eau-métaux)
  - [5. Cadre réglementaire](#5-cadre-réglementaire)
  - [6. Modèle et scénarios](#6-modèle-et-scénarios-2024-2035)
  - [7. Recommandations](#7-trois-recommandations)
  - [8. Limites](#8-limites-de-cette-veille)
- [Sources](#sources)

---

## Le projet

**Décembre 2029.** Le train s'arrête en pleine campagne, faute d'électricité. À bord, l'équipe d'experts qui accompagne le ministre des nouvelles technologies et le PDG de la SNCF à une conférence sur l'IA et les réseaux de données souverains. Dans le wagon-bar, des journalistes accusent la révolution de l'IA. Le ministre demande une présentation qui montre :

1. comment on en est arrivé là ;
2. quels obstacles technologiques n'ont pas été franchis ;
3. quelles innovations peuvent aider à court et moyen terme ;
4. quel est l'impact environnemental (émissions en équivalent CO₂, ressources naturelles).

Il veut trois scénarios chiffrés (pessimiste, normal, optimiste) et trois recommandations actionnables, défendables face à des journalistes avertis.

Le train arrêté est une fiction imposée par le sujet. Nous ne la présentons jamais comme une prévision : nous cherchons au contraire à savoir si les données la rendent plausible, et où.

**Notre fil rouge :** l'IA grandit en mois, le réseau électrique en décennies. Un data center se construit en deux ou trois ans ; une ligne à haute tension demande quatre à huit ans dans les pays avancés (IEA, 2025).

Documents de cadrage : [sujet](documents/Energy%20wall.pdf), [support de kick-off](documents/KickOff_EnergyWall.pdf).

## Le dépôt

```
energy-wall/
├── README.md              contexte, veille, sources
├── presentation/          diaporama HTML, version PDF, trame orale
├── notebooks/             notebook exécuté (.ipynb) et sa version texte (.py)
├── src/energywall/        modèle, incertitude, backtest, registre des sources
├── data/                  paramètres (params.yaml), registre des sources (sources.yaml), données CSO
├── tests/                 tests du modèle (pytest)
├── scripts/               scripts utilitaires (figures de la présentation, vérifications)
└── documents/             sujet, kick-off, bibliographie (BibTeX et RIS pour Zotero)
```

### Relancer les calculs

Le projet utilise [uv](https://docs.astral.sh/uv/) et Python 3.12 ou plus.

```bash
uv sync
```

```bash
uv run pytest
```

```bash
uv run jupyter lab notebooks/energy_wall.ipynb
```

Chaque chiffre du notebook est calculé à partir de `data/params.yaml` et `data/sources.yaml`. Chaque paramètre porte trois bornes (basse, centrale, haute), un statut (lu à la source, relayé, dérivé ou hypothèse) et les identifiants de ses sources.

Les données des graphiques du diaporama viennent du modèle : `uv run python scripts/figures_presentation.py` régénère `presentation/data.js`.

Le notebook est versionné avec ses sorties pour que les graphiques soient lisibles sur GitHub. Sa version texte `energy_wall.py` est synchronisée avec jupytext.

---

## Veille scientifique et technologique

Avant de modéliser quoi que ce soit, nous voulions savoir ce que disent les sources sérieuses, où sont les incertitudes, et quels chiffres nous avons le droit d'utiliser. Nous séparons trois choses que les articles grand public mélangent souvent : les mesures publiées, les projections d'organismes reconnus, et les hypothèses que nous testons nous-mêmes.

Dernière mise à jour : novembre 2026.

### Ce qu'il faut retenir

- **La demande double d'ici 2030.** Les data centers ont consommé environ 415 TWh en 2024, soit 1,5 % de l'électricité mondiale. L'IEA projette environ 945 TWh en 2030 et 1 200 TWh en 2035 dans son scénario de référence, avec une fourchette de 700 à 1 700 TWh en 2035 selon les cas.
- **Le mur est local avant d'être mondial.** En Irlande, les data centers consomment environ 20 % de l'électricité ; en Virginie, 25 %. Dublin a suspendu les nouveaux raccordements jusqu'en 2030.
- **En France, le blocage vient des réservations, pas du manque d'électricité.** Au 1er novembre 2025, des data centers avaient réservé environ 14 GW de raccordement auprès de RTE, mais les sites déjà raccordés n'utilisent qu'environ 20 % de leur puissance contractuelle. RTE parle de projets « fantômes » et de saturation artificielle.
- **L'efficacité ne suffit pas.** Le matériel progresse vite, mais l'usage progresse plus vite encore. Notre modèle montre que, dans le scénario pessimiste, il faudrait doubler l'efficacité du parc tous les 1,6 an pour tenir la borne basse de l'IEA, plus vite que les meilleures puces du marché.
- **L'impact dépasse le compteur électrique.** Eau de refroidissement et de production d'électricité, fabrication des puces, cuivre, gallium raffiné à 98 % en Chine : l'IA dépend de chaînes matérielles concentrées et fragiles.

### 1. Trajectoire : comment on en est arrivé là

Le deep learning, puis les grands modèles de langage et l'IA générative, ont fait exploser les besoins en calcul. La consommation se répartit en trois postes :

- **l'entraînement**, qui construit le modèle. GPT-4 aurait demandé environ 42 GWh sur 14 semaines, la consommation quotidienne de 28 500 foyers de pays avancés pendant toute cette période (IEA, 2025) ;
- **l'inférence**, chaque fois que le modèle répond. Un modèle entraîné une fois sert ensuite des millions de requêtes par jour, et c'est ce poste qui pèse à grande échelle ;
- **le fonctionnement du site** : refroidissement, alimentation électrique, réseau, stockage. L'indicateur PUE mesure ce surcoût.

L'ordre de grandeur par tâche varie énormément. Dans les tests rapportés par l'IEA, générer du texte avec un petit modèle consomme environ 0,3 Wh, avec un modèle moyen environ 5 Wh, et une courte vidéo environ 115 Wh. Pour comparaison, recharger un téléphone demande environ 15 Wh.

**Les chiffres de référence.** L'IEA estime que les data centers ont consommé environ 415 TWh dans le monde en 2024, soit à peu près 1,5 % de l'électricité mondiale. Dans son scénario de référence, la consommation atteint environ 945 TWh en 2030 (un peu plus que la consommation totale du Japon aujourd'hui) puis environ 1 200 TWh en 2035 [1]. Ces chiffres couvrent l'ensemble des data centers, pas uniquement l'IA. Aux États-Unis, le Lawrence Berkeley National Laboratory chiffre la consommation à 176 TWh en 2023, avec une fourchette de 325 à 580 TWh pour 2028 [4]. L'écart entre ces bornes montre à quel point les projections restent incertaines.

**Les lois d'échelle.** Kaplan et ses collègues ont montré qu'il existe une relation empirique régulière entre la performance d'un modèle (sa loss), sa taille, la quantité de données et le calcul utilisé [5]. Hoffmann et ses collègues (le papier « Chinchilla ») ont ensuite montré qu'à budget de calcul fixé, il faut faire croître la taille du modèle et le volume de données au même rythme [6]. Ces lois expliquent pourquoi l'industrie a cherché à augmenter le calcul. Elles ne donnent pas des TWh pour autant : pour passer d'opérations de calcul à de l'électricité, il faut le rendement du matériel, son taux d'utilisation, le PUE du site et le volume réel d'usage. Appliquer l'exposant d'une loi d'échelle à la consommation mondiale serait faux. Notre modèle utilise donc les relations de Kaplan (environ 6 opérations par paramètre et par token à l'entraînement, 2 à l'inférence) comme contrôle de cohérence, et projette la demande avec une décomposition explicite (section 6).

**L'effet rebond.** Le Shift Project insiste sur un point que confirme toute la littérature : les gains d'efficacité ne font pas baisser la consommation totale, parce que les usages augmentent plus vite [3]. Google annonce que la demande électrique de ses data centers a augmenté de 27 % en 2024 [9] ; c'est un chiffre d'entreprise sur son propre cas, mais il va dans le même sens. En 2025, la consommation mondiale a crû d'environ 17 % selon les données relayées dans notre modèle, au-dessus de la fourchette que nous avions retenue (section 6).

### 2. Obstacles : ce qui n'a pas été franchi

**Le réseau électrique.** Construire une ligne à haute tension prend quatre à huit ans dans les pays avancés, alors qu'un data center peut être opérationnel en deux à trois ans [1]. Les délais d'attente pour les transformateurs et les câbles ont doublé en trois ans ; le carnet de commandes de transformateurs a augmenté de plus de 30 % en 2024 et leur indice de prix a été multiplié par 1,5 depuis 2020 [1]. L'IEA estime qu'environ 20 % des data centers prévus d'ici 2030 risquent d'être retardés par ces contraintes [1]. Les files d'attente de raccordement atteignent jusqu'à sept à dix ans dans certaines régions [1].

**Les territoires saturés.** Les data centers pèsent peu à l'échelle mondiale mais beaucoup sur certains territoires. En Irlande, ils consomment environ 20 % de l'électricité distribuée ; aux États-Unis, six États dépassent 10 %, et la Virginie atteint 25 % [1]. À Dublin, les nouveaux raccordements sont suspendus jusqu'en 2030 [1]. La moitié des data centers en développement aux États-Unis se construisent dans des pôles déjà existants, ce qui concentre les tensions [1].

**La France : un réseau réservé mais peu utilisé.** Le Bilan prévisionnel 2025 de RTE décrit une situation différente [10] :

- au 1er novembre 2025, environ 30 GW de capacités d'accès au réseau de transport sont réservées, dont environ 14 GW pour des data centers, 9,5 GW pour l'hydrogène et 6,5 GW pour l'industrie ;
- les data centers déjà raccordés n'utilisent à ce jour que 20 % de leur puissance contractuelle ;
- si tous les projets se réalisaient à pleine puissance, la consommation française augmenterait de 240 TWh, bien au-delà des trajectoires compatibles avec les objectifs publics ;
- RTE juge le dispositif de réservation « faiblement sélectif » : il ne distingue pas les projets matures des projets « fantômes », et donne une image de « saturation artificielle » alors que la France dispose d'un réseau capable d'accueillir rapidement de fortes consommations.

Le risque en France ne vient donc pas d'un manque de production à court terme. Il vient d'une file d'attente qui bloque des capacités au détriment d'autres projets d'électrification (industrie, hydrogène, transports).

**Les puces, la mémoire et la chaleur.** Les accélérateurs dédiés à l'IA progressent vite mais consomment beaucoup et demandent énormément de mémoire. Une puce plus efficace par opération ne fait pas baisser la consommation totale. Plus la puissance par baie augmente, plus il faut évacuer de chaleur ; le refroidissement liquide aide mais coûte cher, demande de la maintenance et pose la question de l'eau.

**L'approvisionnement.** La fabrication des semi-conducteurs, des équipements électriques et des bâtiments dépend de métaux concentrés dans quelques pays (section 4). Les turbines à gaz, qui sont avec le solaire la seule source constructible en un ou deux ans, ont elles aussi des délais de livraison de plusieurs années [2].

**L'opacité.** La consommation réelle des modèles propriétaires, le nombre de requêtes ou le mix électrique d'un site sont rarement publics. Dans nos résultats, nous affichons les incertitudes plutôt qu'une fausse précision.

### 3. Innovations : ce qui peut aider à court et moyen terme

**Demander moins de calcul pour le même service.** C'est souvent le levier le plus rapide : petits modèles spécialisés plutôt qu'un modèle généraliste, compression par quantification ou distillation, réponses plus courtes, mise en cache des réponses fréquentes, routage des demandes simples vers un modèle léger. L'IEA estime qu'un scénario de forte efficacité logicielle et matérielle réduit la consommation des data centers de 20 % en 2035 par rapport au scénario de référence [1]. Ces solutions doivent être comparées à qualité de service égale et sur tout le cycle de vie.

**Rendre les data centers flexibles.** L'IEA juge cette stratégie « encore sous-explorée ». Beaucoup de data centers disposent d'une marge de serveurs inutilisés, de groupes de secours et de batteries qu'ils pourraient mobiliser pour soulager le réseau aux heures de pointe [1]. Décaler les calculs non urgents (entraînement, traitements par lots) vers les heures creuses est techniquement possible ; l'IEA note toutefois qu'un data center d'IA coûte dix fois plus cher en capital qu'une aluminerie, ce qui rend l'arrêt de ses serveurs coûteux.

**Choisir l'emplacement.** Implanter les nouveaux sites là où le réseau et l'eau le permettent est, selon l'IEA, le moyen le plus direct de réduire les tensions locales [1]. Récupérer la chaleur produite pour un réseau de chaleur urbain transforme une perte en ressource.

**Refroidir sans évaporer.** Le refroidissement liquide direct et l'immersion des serveurs réduisent fortement la consommation d'eau sur site [1].

**Utiliser l'IA pour le système énergétique.** L'IEA estime que la diffusion large d'applications d'IA existantes (détection des fuites de méthane, optimisation du réseau, des transports, de l'industrie) pourrait réduire les émissions d'un volume équivalent à environ 5 % des émissions liées à l'énergie en 2035, bien plus que les émissions des data centers eux-mêmes [1]. Ce potentiel dépend d'une adoption qui n'a pas lieu aujourd'hui, et les effets rebond peuvent l'annuler en partie.

**Ce qui arrivera trop tard pour 2029.** Les petits réacteurs nucléaires modulaires (SMR) font l'objet d'annonces liées aux data centers à hauteur de 25 GW, presque toutes aux États-Unis, mais les premiers projets ne sont attendus qu'à la fin de la décennie [2]. La fusion, le calcul quantique et les data centers en orbite relèvent de la recherche ou de prototypes : aucun ne fournira de capacité significative d'ici 2029. Pour un décideur, ces pistes ne remplacent pas les leviers disponibles dès maintenant.

### 4. Impacts : climat, eau, métaux

**Émissions.** Les émissions liées à l'électricité consommée par les data centers passent d'environ 180 Mt CO₂e aujourd'hui à 300 Mt en 2035 dans le scénario de référence de l'IEA, et jusqu'à 500 Mt dans son cas haut [1]. Elles restent sous 1,5 % des émissions du secteur énergétique, mais figurent parmi celles qui croissent le plus vite. Entre 2024 et 2035, les énergies fossiles fournissent environ un tiers de l'électricité supplémentaire consommée par les data centers ; dans le cas haut, près de la moitié de la hausse d'ici 2030 [1]. Notre modèle calcule les émissions avec une approximation transparente :

```
émissions (t CO2e) = électricité consommée (MWh) x intensité carbone du réseau (t CO2e/MWh)
```

Nous retenons la convention « location-based » du GHG Protocol [11] : l'intensité carbone du réseau réel, et non celle des contrats d'électricité verte. La fabrication des serveurs (Scope 3) est chiffrée à part dans le notebook, sans l'additionner.

**Eau.** L'IEA estime la consommation d'eau des data centers à environ 560 milliards de litres par an aujourd'hui, et environ 1 200 milliards en 2030 dans son scénario de référence [1]. Environ deux tiers de cette eau sont consommés pour produire l'énergie, un quart pour le refroidissement sur site, le reste pour fabriquer les puces (l'eau ultra-pure). Un data center de 100 MW aux États-Unis consomme en moyenne environ 2 millions de litres par jour, l'équivalent de 6 500 foyers [1]. Deux confusions reviennent souvent : mélanger l'eau prélevée et l'eau réellement consommée, et oublier l'eau utilisée hors du site pour produire l'électricité.

**Métaux.** En 2030, la demande des nouveaux data centers pourrait représenter jusqu'à 2 % de la demande actuelle de cuivre et de silicium, plus de 3 % de celle des terres rares et 11 % de celle du gallium, soit 512 000 tonnes de cuivre [1]. Le gallium, indispensable aux puces et à l'électronique de puissance, est raffiné à 98 % en Chine, qui en a restreint l'export vers les États-Unis en décembre 2024 [1]. Le cuivre a dépassé 14 000 dollars la tonne en mai 2026, et l'offre minière mondiale pourrait accuser un déficit de 25 % en 2035 [12]. Les data centers entrent en concurrence pour ces métaux avec les réseaux électriques, les véhicules électriques et la défense.

### 5. Cadre réglementaire

- **Union européenne.** Le règlement délégué (UE) 2024/1364 impose aux data centers de plus de 500 kW de déclarer leurs indicateurs de performance énergétique et d'eau dans une base européenne commune [8].
- **France.** RTE et la CRE révisent l'accès au réseau : la délibération de la CRE du 23 juillet 2025 prévoit un recensement sectoriel des projets pour donner la priorité aux plus mûrs, et RTE ouvre des sites « fast track » déjà équipés pour accueillir de fortes consommations [10].

### 6. Modèle et scénarios 2024-2035

Le notebook projette la consommation électrique **mondiale** des data centers (IA comprise), avec ses émissions et son eau, de 2024 à 2035. Il part des 415 TWh de 2024 publiés par l'IEA.

**Méthode.** Une décomposition de type Kaya sépare la consommation conventionnelle, l'entraînement et l'inférence. Chaque poste évolue selon des taux de croissance (calcul d'entraînement, tokens servis), le gain d'efficacité du parc de puces et l'évolution du PUE. Les trois scénarios sont des jeux cohérents de bornes ; ils sont **comparés** aux bornes de l'IEA, jamais calés dessus. Le notebook ajoute :

- un **Monte Carlo** qui propage les plages d'incertitude des paramètres ;
- un **test du mur** qui confronte la demande à une capacité supposée croître de 8 à 18 % par an ;
- un **test « miracle »** : de combien le parc doit-il gagner en efficacité pour tenir une cible ?
- un **backtest** sur les données observées (CSO en Irlande, Ember) ;
- une estimation du **carbone incorporé** du matériel informatique.

**Résultats.**

| Scénario | Électricité (TWh) 2027 / 2030 / 2035 | Émissions (Mt CO₂e) 2027 / 2030 / 2035 | Eau consommée (hm³) 2027 / 2030 / 2035 |
|----------|--------------------------------------|----------------------------------------|----------------------------------------|
| Pessimiste | 647 / 1 157 / 2 155 | 294 / 517 / 939 | 2 976 / 5 353 / 10 081 |
| Normal | 558 / 772 / 979 | 248 / 328 / 385 | 1 302 / 1 821 / 2 349 |
| Optimiste | 486 / 544 / 511 | 209 / 214 / 172 | 663 / 744 / 701 |

Repères IEA pour 2035 : 1 700 TWh (cas haut), 1 200 TWh (référence), 700 TWh (cas bas). Notre scénario pessimiste dépasse le cas haut de 27 % ; nos scénarios normal et optimiste sont 18 % et 27 % sous leurs repères.

**Ce que le modèle apprend.**

- **Le mur est possible au niveau mondial.** Si la capacité ne croît que de 8 % par an, la demande la dépasse dès 2025 dans le scénario pessimiste. Même avec une capacité qui croît de 18 % par an, le scénario pessimiste la dépasse à partir de 2029.
- **L'efficacité seule ne suffit pas.** Pour tenir 700 TWh en 2035, le parc devrait doubler d'efficacité au plus tous les 1,6 an dans le scénario pessimiste, plus vite que les meilleures puces ; tous les 2,2 ans dans le scénario normal, au rythme des meilleures puces ; tous les 3,4 ans dans le scénario optimiste, ce qui est plausible.
- **La réalité roule déjà sur la voie haute.** La croissance observée entre 2024 et 2025 (environ 17 %) sort de la fourchette de nos tirages (6 à 14 %). Nous ne l'avons pas recalée : c'est un résultat.
- **L'eau est l'indicateur le plus incertain.** Le scénario pessimiste cumule une forte demande et des paramètres d'eau défavorables ; ses valeurs dépassent nettement les estimations de l'IEA et doivent se lire comme une borne haute.
- **La fabrication pèse aussi.** Le carbone incorporé du matériel informatique représente 15 à 67 Mt CO₂e en 2035 dans le scénario normal, en plus des émissions d'usage.

**Ce que le modèle ne dit pas.** Ce n'est pas une prévision : l'horizon de onze ans dépasse les cinq ans que recommande l'IEA-4E, et 71 % des bornes de paramètres tirés sont des hypothèses justifiées, pas des mesures. Les quantiles du Monte Carlo décrivent la dispersion due aux plages choisies, pas des probabilités. Le modèle est mondial et annuel : il ne dit rien de la pointe d'hiver en France, que nous documentons avec RTE (section 2).

### 7. Trois recommandations

1. **Libérer le réseau des projets fantômes.** Donner la priorité de raccordement aux projets mûrs, reprendre les capacités réservées et inutilisées, et conditionner les nouveaux raccordements à une flexibilité aux heures de pointe (report des calculs non urgents, mobilisation des batteries et groupes de secours). Appuis : RTE [10], IEA [1].
2. **Rendre les impacts mesurables.** Un reporting public et commun pour les grands data centers : consommation annuelle, puissance de pointe, PUE, eau consommée, émissions calculées sur le réseau local, lieu de raccordement. Le règlement européen 2024/1364 pose la base ; il faut le rendre public et le compléter [8].
3. **Choisir où l'on construit.** Avant d'autoriser un site, évaluer ce que le réseau et la ressource en eau locale peuvent supporter, orienter les projets vers les zones disponibles, et imposer la récupération de chaleur quand un réseau de chaleur existe à proximité. Appuis : IEA [1], RTE [10].

### 8. Limites de cette veille

- Nous ne reprenons pas la phrase qui circule partout selon laquelle « une requête ChatGPT consomme dix fois plus qu'une recherche Google ». Le ratio dépend du modèle, de la longueur de la réponse et de la méthode de mesure. Une prépublication récente donne une médiane de 0,34 Wh par requête pour le cas étudié [7], valeur qu'on ne peut pas généraliser.
- La plupart des chiffres portent sur l'ensemble des data centers, pas sur la seule IA.
- Les chiffres d'entreprises (Google, Mistral) sont signalés comme tels : ils décrivent un cas, avec une méthode choisie par l'entreprise.
- Pour chaque chiffre du modèle, `data/sources.yaml` indique s'il s'agit d'une mesure, d'une projection, d'une dérivation ou d'une hypothèse.

---

## Sources

La bibliographie est aussi disponible aux formats [BibTeX](documents/references.bib) et [RIS pour Zotero](documents/Energy_Wall_Sources.ris). Le registre complet des sources du modèle, avec leurs biais déclarés, est dans [data/sources.yaml](data/sources.yaml).

[1] Agence internationale de l'énergie (2025). *Energy and AI*. https://www.iea.org/reports/energy-and-ai

[2] Agence internationale de l'énergie (2025). *Energy and AI : Energy supply for AI*. https://www.iea.org/reports/energy-and-ai/energy-supply-for-ai

[3] The Shift Project (2025). *Intelligence artificielle, données, calculs : quelles infrastructures dans un monde décarboné ?* https://theshiftproject.org/publications/intelligence-artificielle-centres-de-donnees-rapport-final/

[4] Shehabi, A. et al. (2024). *2024 United States Data Center Energy Usage Report*. Lawrence Berkeley National Laboratory. https://energyanalysis.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report

[5] Kaplan, J. et al. (2020). *Scaling Laws for Neural Language Models*. arXiv:2001.08361. https://arxiv.org/abs/2001.08361

[6] Hoffmann, J. et al. (2022). *Training Compute-Optimal Large Language Models*. arXiv:2203.15556. https://arxiv.org/abs/2203.15556

[7] Oviedo et al. (2025). *Energy Use of AI Inference: Efficiency Pathways and Test-Time Compute*. Prépublication, arXiv:2509.20241. https://arxiv.org/abs/2509.20241

[8] Règlement délégué (UE) 2024/1364 de la Commission du 14 mars 2024 relatif aux centres de données. https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj

[9] Google (2025). *Environmental Report 2025* (données publiées par l'entreprise). https://sustainability.google/reports/google-2025-environmental-report/

[10] RTE (2025). *Bilan prévisionnel 2025-2035 : principaux résultats* et *résumé exécutif*. https://www.rte-france.com/analyses-tendances-et-prospectives/bilan-previsionnel

[11] GHG Protocol. *Scope 2 Guidance*. https://ghgprotocol.org/scope-2-guidance

[12] Agence internationale de l'énergie (2026). *Global Critical Minerals Outlook 2026*. https://www.iea.org/reports/global-critical-minerals-outlook-2026

Autres sources de départ du kick-off : [Open Power System Data](https://open-power-system-data.org), [World Bank Climate Change Knowledge Portal](https://climateknowledgeportal.worldbank.org).

---

Documents internes : [notes de kick-off de Romuald](documents/Kick-off.md) (idées de départ, hors consignes).
