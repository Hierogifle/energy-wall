# Energy Wall : veille scientifique et technologique

Cette partie du dépôt regroupe notre veille sur la consommation énergétique de l'intelligence artificielle. L'idée est simple : avant de modéliser quoi que ce soit dans le notebook, on voulait savoir ce que disent vraiment les sources sérieuses, où sont les incertitudes, et quels chiffres on a le droit d'utiliser sans tordre la réalité.

Le document suit les quatre angles du sujet donné par La Plateforme_ : la trajectoire de la demande, les obstacles, les innovations et les impacts. On a essayé de bien séparer trois choses qui se mélangent souvent dans les articles grand public : les chiffres publiés, les projections faites par des organismes reconnus, et les hypothèses que nous testons nous-mêmes dans le notebook.

Petite précision avant de commencer. L'histoire du train bloqué en 2029 qui sert de point de départ au projet est un scénario narratif imposé par le sujet. Ce n'est pas une prévision, et on ne la présente jamais comme telle.

Dernière mise à jour : novembre 2026.


## Ce qu'il faut retenir

On parle souvent du « cloud » comme de quelque chose d'immatériel. En pratique, chaque modèle d'IA tourne sur des puces, dans des serveurs, installés dans des centres de données branchés sur un réseau électrique. Plus les usages se développent, plus la question change de nature : il ne s'agit plus seulement de savoir ce que l'IA sait faire, mais combien d'énergie elle demande pour le faire, et avec quelles conséquences.

Le scénario le plus crédible n'est pas une grande panne mondiale. Ce qu'on voit déjà apparaître, ce sont des tensions locales : des raccordements au réseau qui prennent des années, des prix de l'électricité qui montent dans certaines zones, des équipements difficiles à obtenir, et parfois des conflits autour de l'eau.


## 1. La trajectoire : pourquoi la demande accélère

Le deep learning, puis les grands modèles de langage et l'IA générative, ont fait exploser les besoins en calcul. Pour bien comprendre d'où vient la consommation, il faut distinguer trois postes.

L'entraînement, c'est la phase où on construit le modèle. Elle coûte cher mais elle a lieu une fois (ou quelques fois). L'inférence, c'est chaque fois que le modèle répond à une demande. Le fonctionnement du centre de données lui-même s'ajoute à tout ça : refroidissement, alimentation électrique, réseau, stockage. Un modèle entraîné une seule fois peut ensuite être sollicité des millions de fois par jour, et c'est pour ça qu'à grande échelle l'inférence devient un poste qu'on ne peut plus ignorer.

Côté chiffres, la référence la plus solide reste l'Agence internationale de l'énergie. Elle estime que les centres de données ont consommé environ 415 TWh dans le monde en 2024, ce qui représente à peu près 1,5 % de l'électricité mondiale. Dans son scénario central, on monte à près de 945 TWh en 2030 puis autour de 1 200 TWh en 2035 [1]. Attention, ces chiffres concernent l'ensemble des centres de données et pas uniquement l'IA.

La croissance n'est pas la même partout. Aux États-Unis, le Lawrence Berkeley National Laboratory chiffre la consommation des centres de données à 176 TWh en 2023, et donne une fourchette très large pour 2028, entre 325 et 580 TWh [4]. L'écart entre les deux bornes montre bien à quel point les projections restent incertaines. De son côté, The Shift Project insiste sur un point qu'on retrouve dans toute la littérature : les gains d'efficacité ne font pas baisser automatiquement la consommation totale, parce que les usages augmentent plus vite [3].


## 2. Les obstacles : le mur n'est pas seulement électrique

Quand on parle de « mur énergétique », on imagine surtout un manque d'électricité. En réalité, les blocages sont aussi industriels.

Les puces et les serveurs d'abord. Les accélérateurs dédiés à l'IA progressent vite, mais ils consomment beaucoup, demandent énormément de mémoire, et les composants ne sont pas toujours disponibles. Une puce plus efficace par opération ne veut pas dire qu'on consommera moins au total.

Le réseau électrique ensuite. Raccorder un grand site dépend de ce que le réseau local peut absorber : transformateurs, lignes, postes, et des délais d'investissement qui se comptent en années. Les centres de données pèsent peu à l'échelle mondiale, mais ils peuvent créer une forte pression sur un territoire précis [1].

Le refroidissement aussi. Plus on met de puissance dans une baie, plus il y a de chaleur à évacuer. Le refroidissement liquide aide, mais il a un coût, il demande de la maintenance, et il pose la question de l'eau disponible.

Il y a aussi tout ce qui se passe avant la mise en service : fabrication des semi-conducteurs, construction des bâtiments, câblage, métaux, batteries, équipements électriques. Tout ça a une empreinte qui n'apparaît pas sur le compteur.

Enfin, les données manquent. La consommation réelle des modèles propriétaires, le nombre de requêtes traitées ou le mix électrique exact d'un site sont rarement publics en entier. Dans nos résultats, on préfère donc afficher clairement les incertitudes plutôt que de donner une fausse précision.


## 3. Les scaling laws : ce qu'elles disent et ce qu'elles ne disent pas

Les travaux de Kaplan et de ses collègues ont montré qu'il existe une relation empirique assez régulière entre la performance d'un modèle (mesurée par sa loss), sa taille, la quantité de données et le calcul utilisé [5]. Deux ans plus tard, l'équipe d'Hoffmann (le papier dit « Chinchilla ») a montré qu'à budget de calcul fixé, la façon de répartir ce budget entre la taille du modèle et le volume de données change beaucoup le résultat [6].

Ces lois expliquent bien pourquoi l'industrie a cherché à augmenter le calcul, et comment elle peut mieux l'utiliser. En revanche, elles ne donnent pas directement des TWh. Pour passer d'un nombre d'opérations (FLOPs) à une consommation d'énergie, il faut connaître le rendement du matériel (FLOPs par watt), le taux d'utilisation des machines, la durée des calculs, le PUE du centre de données et le volume réel d'usages. Prendre l'exposant d'une scaling law et l'appliquer à la consommation électrique mondiale serait tout simplement faux.

C'est pour cette raison que le notebook est découpé en deux modules indépendants. Le premier est pédagogique : il illustre le calcul nécessaire à l'entraînement en s'inspirant des scaling laws. Le second estime la demande électrique à partir d'hypothèses annuelles écrites noir sur blanc, et on compare ses résultats à la référence AIE pour 2030.


## 4. Les innovations : ce qui peut infléchir la courbe

Le levier le plus rapide, c'est souvent de demander moins de calcul pour rendre le même service. On peut utiliser des petits modèles spécialisés au lieu d'un énorme modèle généraliste, compresser les modèles par quantification ou distillation, limiter la longueur des réponses, mettre en cache les réponses fréquentes, ou envoyer les demandes simples vers un modèle plus léger. Des puces plus adaptées, des serveurs mieux utilisés et un refroidissement plus efficace améliorent aussi le rendement global. Mais pour être honnête, toutes ces solutions doivent être comparées à qualité de service équivalente et sur tout le cycle de vie, sinon on compare des choses qui ne se comparent pas.

Côté énergie, plusieurs pistes se complètent : bien choisir l'emplacement des nouveaux sites, décaler certains calculs vers les heures où le réseau est moins chargé, signer des contrats d'électricité bas carbone, récupérer la chaleur produite. La géothermie et le nucléaire de nouvelle génération reviennent souvent dans les discussions, mais leur disponibilité industrielle et leurs délais de déploiement varient beaucoup d'un site à l'autre. Ce ne sont pas des solutions immédiates qui marchent partout.

Un exemple concret pour illustrer le décalage entre efficacité et consommation : Google annonce que la demande électrique de ses centres de données a augmenté de 27 % en 2024, alors que les émissions liées à cette énergie auraient baissé de 12 % [9]. C'est intéressant, mais ça reste un chiffre communiqué par une entreprise sur son propre cas. Ça ne prouve pas que la consommation baisse en général.


## 5. Les impacts : regarder plus loin que le compteur

L'impact sur le climat dépend de l'électricité réellement consommée, mais aussi de la façon dont elle est produite, à cet endroit et à ce moment. Pour les émissions liées au fonctionnement, on utilise une approximation simple et transparente :

```
émissions (tCO2e) = énergie consommée (MWh) x facteur d'émission (tCO2e/MWh)
```

Une analyse complète irait plus loin en ajoutant la fabrication des serveurs et des bâtiments, les groupes électrogènes de secours et toute la chaîne d'approvisionnement. Dans tous les cas, il faut dire quelles conventions de calcul on a retenues.

Pour l'eau, les chiffres varient énormément selon la technologie de refroidissement, la saison et le lieu. Deux confusions reviennent souvent : mélanger l'eau prélevée et l'eau réellement consommée, et oublier de distinguer l'eau utilisée sur le site de celle qui sert à produire l'électricité.

Quant aux matériaux, on parle beaucoup des terres rares, mais le cuivre, l'aluminium, l'acier et les semi-conducteurs pèsent au moins autant dans l'empreinte de fabrication.


## 6. Trois scénarios exploratoires pour 2030 et 2035

Les chiffres de cette section sont des simulations faites pour le projet. Ce ne sont pas des prévisions officielles. On part tous du même point, les 415 TWh de 2024 publiés par l'AIE, et on applique un taux de croissance constant :

```
E(t) = 415 x (1 + g)^(t - 2024)
```

Le taux constant n'a pas pour but de reproduire le modèle de l'AIE. Il sert juste à rendre les trois scénarios comparables entre eux.

| Scénario | Croissance par an | 2030 (TWh) | 2035 (TWh) | Ce que ça représente |
| --- | --- | --- | --- | --- |
| Pessimiste | 18 % | 1 120 | 2 563 | Les usages s'envolent et la demande absorbe tous les gains d'efficacité |
| Central | 15 % | 960 | 1 931 | Croissance soutenue, proche de la référence AIE 2030 (environ 945 TWh) |
| Optimiste | 8 % | 659 | 968 | La sobriété et l'efficacité freinent nettement la hausse |

Les valeurs sont arrondies. La colonne 2035 est volontairement une extrapolation mécanique. L'AIE, dans son scénario central, projette environ 1 200 TWh en 2035 [1], soit bien moins que notre scénario central. Cet écart est justement ce qu'on veut montrer : garder le même taux de croissance pendant onze ans ne donne pas une projection crédible. Pour la soutenance, la référence principale reste donc le scénario publié par l'AIE, et nos trois scénarios servent à mesurer à quel point le résultat dépend des hypothèses.


## 7. Trois recommandations pour un décideur

Rendre les impacts mesurables. On propose un reporting commun pour les grands centres de données, avec la consommation annuelle, la demande de pointe, le PUE, l'eau utilisée, les émissions calculées selon une méthode publiée, et le lieu de raccordement. L'Union européenne a déjà posé un cadre de déclaration qu'il faudrait renforcer [8].

Tenir compte du territoire avant d'autoriser un nouveau site. Avant de donner le feu vert, il faudrait évaluer ce que le réseau peut supporter, les besoins en eau, les délais, les émissions et les conflits d'usage possibles. Il faudrait aussi regarder les possibilités de flexibilité, au lieu de raisonner uniquement en puissance installée.

Financer l'efficacité qu'on peut vérifier plutôt que la course à la capacité. Concrètement, cela passerait par des appels à projets qui comparent le coût énergétique par tâche réellement utile, à qualité égale, avec publication des résultats. Les petits modèles, la quantification, le matériel performant, la mutualisation et le pilotage intelligent entrent tous dans ce cadre.


## 8. Les limites de cette veille

On évite de reprendre telle quelle la phrase qui circule partout selon laquelle « une requête ChatGPT consomme dix fois plus qu'une recherche Google ». Le ratio dépend énormément du modèle, de la longueur de la réponse et de la méthode de mesure. Une prépublication récente donne une médiane de 0,34 Wh par requête pour le cas étudié [7], mais ce n'est pas une valeur qu'on peut généraliser, d'autant que l'article n'a pas encore été relu par des pairs.

On fait attention à ne pas confondre la consommation de tous les centres de données avec celle qui vient spécifiquement de l'IA. La plupart des chiffres disponibles portent sur le premier périmètre.

On ne présente pas la simulation de 2029 comme une panne réellement annoncée. C'est la fiction de départ du projet.

Pour chaque source, on indique l'année de publication et on précise s'il s'agit d'une mesure, d'une projection, d'une extrapolation de notre part ou d'un chiffre communiqué par une entreprise.


## Sources

Les références sont aussi disponibles dans `references.bib` (BibTeX) et `Energy_Wall_Sources.ris` (import Zotero).

[1] Agence internationale de l'énergie (2025). *Energy and AI : Energy demand from AI*. https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai

[2] Agence internationale de l'énergie (2025). *Energy and AI : Energy supply for AI*. https://www.iea.org/reports/energy-and-ai/energy-supply-for-ai

[3] The Shift Project (2025). *Intelligence artificielle, données, calculs : quelles infrastructures dans un monde décarboné ?* https://theshiftproject.org/publications/intelligence-artificielle-centres-de-donnees-rapport-final/

[4] Shehabi, A. et al. (2024). *2024 United States Data Center Energy Usage Report*. Lawrence Berkeley National Laboratory. https://energyanalysis.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report

[5] Kaplan, J. et al. (2020). *Scaling Laws for Neural Language Models*. arXiv:2001.08361. https://arxiv.org/abs/2001.08361

[6] Hoffmann, J. et al. (2022). *Training Compute-Optimal Large Language Models*. arXiv:2203.15556. https://arxiv.org/abs/2203.15556

[7] Oviedo et al. (2025). *Energy Use of AI Inference: Efficiency Pathways and Test-Time Compute*. Prépublication, arXiv:2509.20241. https://arxiv.org/abs/2509.20241

[8] Règlement délégué (UE) 2024/1364 de la Commission du 14 mars 2024 relatif aux centres de données. https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj

[9] Google (2025). *Environmental Report 2025* (données publiées par l'entreprise). https://sustainability.google/reports/google-2025-environmental-report/
