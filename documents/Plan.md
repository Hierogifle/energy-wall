# Plan de travail — Energy Wall

Trame du projet et répartition. Les consignes de référence sont dans [KickOff_EnergyWall.pdf](KickOff_EnergyWall.pdf).

## Fil rouge

> **L'IA grandit en mois, le réseau électrique en décennies. Le mur, c'est l'endroit où les deux courbes se croisent.**

**La scène.** Mardi de décembre 2029, 19 h. Le train s'arrête en pleine campagne. Ce n'est plus un événement : les coupures tournantes sont devenues une habitude à laquelle la France s'est adaptée. Le réseau mobile fonctionne, les data centers tournent, mais le train est coupé. Cette fois, il y en a assez : le ministre demande des réponses.

**La question d'ouverture.** Pourquoi le train et pas le data center ?

## Le graphique fil rouge

Un seul graphique, qui revient à chaque partie et s'enrichit :

- **Courbe 1 — la demande de l'IA**, qui monte vite.
- **Courbe 2 — ce que le réseau peut fournir**, qui monte lentement.
- **Le croisement** : le train qui s'arrête.
- **L'écart entre les deux** : ce qu'il faut combler en urgence, et ce que cela coûte.

## Trame de la présentation

Un peu plus de 15 minutes, environ 13 diapositives. Chaque partie fait une seule chose sur le graphique et répond à l'une des répliques des journalistes du sujet.

| # | Partie | Ce qu'elle fait sur le graphique | Réplique du journaliste | Durée | Diapos |
|---|--------|----------------------------------|-------------------------|-------|--------|
| 0 | **Ouverture** | Montre le croisement : décembre 2029, 19 h | « Génial ! Ma connexion réseau mobile fonctionne encore ! » | 1 min | 1 |
| 1 | **Trajectoire** | Trace la courbe de la demande | « Ne pouvait-on pas prévoir ces pannes ? » | 2 min 30 | 2 |
| 2 | **Obstacles** | Trace la courbe du réseau | « L'explosion de la demande ne s'accompagne pas de décisions efficaces ! » | 2 min 30 | 2 |
| 3 | **Innovations** | Ce qui rapproche les deux courbes, et ce qui arrive trop tard | « L'IA peut-elle résoudre elle-même ce problème de surconsommation ? » | 2 min 30 | 2 |
| 4 | **Impact** | Ce que coûte l'écart | « Quelle plaie pour la planète ! » | 2 min 30 | 2 |
| 5 | **Scénarios** | Trois courbes de demande : l'écart se creuse, se maintient, se referme | — | 2 min | 2 |
| 6 | **Recommandations** | Trois façons de refermer l'écart | — | 1 min 30 | 1 |
| 7 | **Clôture** | Retour dans le train : lequel des trois futurs choisit-on ? | — | 30 s | 1 |

### Contenu de chaque partie

**1 — Trajectoire : la courbe de la demande**
- Historique de la consommation de l'IA
- Lois d'échelle (Kaplan, Chinchilla) : pourquoi les besoins croissent plus vite que les performances
- Bascule de l'entraînement vers l'inférence
- Les agents : la demande n'est plus bornée par le nombre d'humains
- Les usages qui tirent la demande (santé, éducation, robotique), cités sans être développés

**2 — Obstacles : la courbe du réseau**
- La pointe d'hiver à 19 h : le réseau casse sur la puissance, pas sur l'énergie annuelle
- Les délais : un data center en 2 ans, une ligne haute tension en 10, un réacteur en 15
- Transformateurs, refroidissement, approvisionnement en GPU
- L'opacité : faute de données publiées, on pilote à l'aveugle

**3 — Innovations : ce qui rapproche les courbes**
- Côté demande : efficacité des modèles et du matériel
- Côté réseau : effacement des data centers à la pointe, choix d'implantation, récupération de chaleur
- L'IA au service du réseau : prévision de la production renouvelable, pilotage
- Ce qui arrive trop tard pour 2029 : data centers en orbite, SMR, fusion, quantique

**4 — Impact : ce que coûte l'écart**
- L'écart comblé par du gaz en urgence : émissions (Scopes 1, 2, 3 selon le GHG Protocol)
- Eau de refroidissement
- Métaux et fabrication des puces
- Électricité décarbonée détournée d'autres usages (voitures électriques, pompes à chaleur, industrie)

## Règle de tri

Un sujet reste dans les 15 minutes s'il **déplace l'une des deux courbes** ou **chiffre l'écart**. Sinon, il va en diapositive de réserve (pour les questions) et dans la veille du README.

| Idée | Décision |
|------|----------|
| Consommation énergétique | Courbe de la demande — partie 1 |
| Production d'énergie, énergies renouvelables | Courbe du réseau — parties 2 et 3 |
| Consommation d'eau, énergies fossiles, métaux rares | Coût de l'écart — partie 4 |
| Pollution, biodiversité | Partie 4, en complément |
| Santé, éducation, robotique | Partie 1, comme moteurs de la demande uniquement |
| Spatial | Partie 3, une ligne dans « ce qui arrive trop tard » ; détail en réserve |
| Quantique | Partie 3, même traitement |
| Sécurité et cybersécurité | Réserve |
| Démocratie et société | Ouverture et clôture : qui décide du délestage ? |
| Ingérences politiques, désinformation | Réserve et section dédiée dans la veille du README |
| Fautes d'orthographe | Écartée |

## L'IA des deux côtés du graphique

Chaque thématique montre ce que l'IA aggrave et ce qu'elle soulage. Exemples à vérifier et sourcer :

| Thématique | Ce que l'IA aggrave | Ce que l'IA soulage |
|------------|---------------------|---------------------|
| Électricité | Demande en forte hausse, concentrée sur quelques sites | Prévision de la production renouvelable, pilotage du réseau, optimisation du refroidissement |
| Eau | Refroidissement en zones déjà sous tension | Détection de fuites, gestion des réseaux d'eau |
| Climat | Émissions directes et de fabrication | Réductions permises dans d'autres secteurs (estimations de l'IEA) |
| Ressources | Métaux, renouvellement rapide des GPU | Découverte de matériaux, recyclage |
| Spatial | Émissions des lancements, débris, chaleur difficile à évacuer dans le vide | Solaire quasi continu, ni eau ni foncier ; observation de la Terre pour le climat |
| Démocratie | Ingérences, désinformation à grande échelle, implantations décidées sans débat public | Accès à l'information, consultation citoyenne, transparence des données publiques |

Les bénéfices sont bien moins documentés que les consommations : les présenter comme des potentiels, pas comme des acquis.

## Les 3 métriques suivies

| # | Métrique | Unité | Rôle dans le fil rouge |
|---|----------|-------|------------------------|
| 1 | Électricité appelée par les data centers et l'IA | TWh/an et GW à la pointe | Les deux courbes |
| 2 | Émissions de gaz à effet de serre | MtCO₂e/an | Coût de l'écart |
| 3 | Consommation d'eau | millions de m³/an | Coût de l'écart |

Chaque scénario donne une valeur de ces trois métriques en 2027, 2030 et 2035.

## Les trois scénarios

| Scénario | Récit | Sur le graphique | Leviers à paramétrer |
|----------|-------|------------------|----------------------|
| **Pessimiste** | On ne fait rien : l'IA gagne en puissance sans règle ni régulation | L'écart se creuse | Demande forte, gains d'efficacité absorbés par l'usage, mix électrique inchangé |
| **Normal** | On agit un peu : la tendance actuelle se poursuit avec des ajustements | L'écart se maintient | Demande tendancielle, efficacité au rythme actuel, régulation partielle |
| **Optimiste** | Le développement de l'IA est aligné sur ce que le réseau et les ressources peuvent fournir | L'écart se referme | Demande pilotée, effacement, implantation choisie, transparence |

Points de vigilance :

- **Le scénario optimiste garde un coût chiffré.** « Zéro problème » ne tient pas face à un journaliste sceptique.
- **Cohérence des dates.** Les projections partent des données de 2026. Le train arrêté de 2029 est l'aboutissement de la trajectoire « on ne fait rien » ; les deux autres scénarios montrent ce qui était évitable.
- **Si les courbes ne se croisent pas.** La France exporte aujourd'hui de l'électricité : le calcul montrera peut-être que le croisement n'a lieu que localement ou à la pointe. C'est un résultat, à présenter tel quel : « voici sous quelles hypothèses le train s'arrête ».

## Répartition

### Travail de fond : un lot par personne

| Lot | Périmètre | Alimente | Sources principales | Qui |
|-----|-----------|----------|---------------------|-----|
| **A — La courbe de la demande** | Lois d'échelle, historique de consommation de l'IA, inférence et agents, leviers d'efficacité, paramétrage des scénarios | Parties 1, 3, 5 | Kaplan, Hoffmann (Chinchilla), IEA | |
| **B — La courbe du réseau** | Capacité et pointe, délais de construction et de raccordement, effacement, implantation | Parties 2, 3 | IEA, Open Power System Data, RTE | |
| **C — Le coût de l'écart** | Émissions, eau, métaux, fabrication des puces, usages concurrents de l'électricité | Partie 4 | GHG Protocol, Shift Project, World Bank Climate | |

En commun :

- Hypothèses partagées (années, unités, facteurs d'émission), fixées avant de coder
- Le graphique fil rouge
- Les trois recommandations
- Diaporama et répétition
- Section « Veille » du README : chacun rédige la partie de son lot

Notebook : chacun travaille sur son lot dans un notebook séparé, sur sa branche ; l'assemblage en un notebook final se fait en phase 3.

### À l'oral : trois blocs d'environ 5 minutes

| Bloc | Parties | Durée | Qui |
|------|---------|-------|-----|
| Les deux courbes | 1 et 2 | 5 min | |
| L'écart et ses remèdes | 3 et 4 | 5 min | |
| La scène, les scénarios, les recommandations | 0, 5, 6, 7 | 5 min | |

La même personne ouvre et referme la scène du train.

## Idées de mise en forme

- **Le compteur** : en clôture, annoncer ce que les data centers ont consommé dans le monde pendant la présentation (électricité, eau), calculé dans le notebook.
- **Une unité parlante** : convertir les chiffres en trajets de TGV ou en réacteurs plutôt qu'en TWh.
- **Tableau de bord** : les trois métriques rappelées dans un coin de chaque diapositive.
- **Un chiffre par diapositive**, sourcé en bas de page.
- **Répétition** : l'un de nous joue le journaliste sceptique.

## Étapes

**Phase 1 — Veille**
- [ ] Se répartir les lots et les blocs oraux
- [ ] Valider les 3 métriques
- [ ] Lire les sources de son lot, noter chaque chiffre avec sa source et sa date
- [ ] Fixer le point hebdomadaire

**Phase 2 — Collecte et modélisation**
- [ ] Fixer les hypothèses communes
- [ ] Récupérer les données de son lot
- [ ] Tracer une première version des deux courbes

**Phase 3 — Scénarios et recommandations**
- [ ] Paramétrer les trois scénarios
- [ ] Assembler le notebook final
- [ ] Choisir et chiffrer les trois recommandations

**Phase 4 — Storytelling et livrable**
- [ ] Diaporama
- [ ] Veille complète dans le README
- [ ] Répétition devant un public critique

## Pistes de recommandations

Trois façons de refermer l'écart, à confirmer ou écarter selon les calculs.

1. **Agir sur le croisement** : conditionner le raccordement d'un data center à une obligation d'effacement lors des pointes.
2. **Voir les courbes** : imposer la transparence — consommation d'électricité et d'eau publiée par site, émissions calculées sur le réseau local.
3. **Déplacer la demande** : orienter l'implantation vers les zones où le réseau et l'eau le permettent, avec récupération de chaleur obligatoire.
