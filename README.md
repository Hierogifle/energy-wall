# Energy Wall — L'IA face au mur énergétique

> « Je me suis aperçu que quelque chose clochait non parce que j'ai remarqué une anomalie dans le monde réel, mais parce que je n'arrivais plus à faire fonctionner Google Maps. »
> — Alexandre Lacroix, avril 2025

Projet M2 — La Plateforme_ · Veille scientifique, modélisation prédictive, recommandations exécutives.

**Équipe :** Romuald · Emile · Olivier

---

## Sommaire

- [Contexte](#contexte)
- [Mission](#mission)
- [Espace collaboratif](#espace-collaboratif)
- [Consignes](#consignes)
- [Livrables](#livrables)
- [Organisation](#organisation)
- [Ressources](#ressources)
- [Veille scientifique et technologique](#veille-scientifique-et-technologique)

---

## Contexte

**Décembre 2029.** Le train s'arrête en pleine campagne : panne d'électricité, encore une. Nous faisons partie de l'équipe d'experts qui accompagne le ministre des nouvelles technologies et le PDG de la SNCF à une conférence sur le développement de l'intelligence artificielle et des réseaux de données souverains.

Dans le wagon-bar, des journalistes débattent des risques de défaillance de l'infrastructure énergétique liés à la révolution de l'IA :

- Ne pouvait-on pas prévoir ces pannes et anticiper ces coupures ?
- L'explosion de la demande ne s'accompagne pas de décisions efficaces.
- L'IA peut-elle résoudre elle-même ce problème de surconsommation ?
- Les ressources s'épuisent et les émissions de CO₂ explosent.

Le ministre nous interpelle : la présentation prévue n'est plus tenable, il faut tout revoir.

## Mission

Rédiger une présentation qui montre :

| # | Angle | Contenu attendu |
|---|-------|-----------------|
| 01 | **Trajectoire** | Comment on en est arrivé là : historique de la consommation énergétique de l'IA, grandes étapes, ruptures. |
| 02 | **Obstacles** | Les verrous technologiques non franchis : limites GPU, réseau électrique, refroidissement, approvisionnement. |
| 03 | **Innovations** | Les pistes secourables à court et moyen terme : efficacité des modèles, nouveaux hardware, énergies alternatives, optimisations. |
| 04 | **Impact** | Émissions GES en équivalent CO₂, consommation d'eau, de terres rares et de ressources naturelles. |

Le tout avec des **recommandations fiables et actionnables** et un **storytelling cohérent** avec les tendances de croissance de la consommation énergétique.

### À qui on parle

Un ministre, des journalistes, des politiques, des citoyens — pas des ingénieurs. Il faut **vulgariser** et rendre l'information accessible, sans rien céder sur l'exactitude.

> De la créativité, mais de la vérité surtout.

---

## Espace collaboratif

Tout ce qui se rédige à plusieurs vit dans des outils d'édition simultanée, pour éviter les conflits Git. Le dépôt ne reçoit que les versions stabilisées.

<!-- Remplacer chaque « à ajouter » par le lien de partage, au format [Ouvrir](https://...) -->

| Ressource | Outil | Usage | Lien |
|-----------|-------|-------|------|
| Dossier partagé | Google Drive | Point d'entrée : tous les fichiers du projet | _à ajouter_ |
| Notes de veille | Google Docs | Fiches de lecture, synthèses par source | [Ouvrir](https://docs.google.com/document/d/1MF5ped0LZJSc-OqI5AN7feZNNlYaf4JgXuTF5Zp4Aus/edit?usp=sharing) |
| Sources et indicateurs | Google Sheets | Bibliographie, chiffres clés avec leur source et leur date | _à ajouter_ |
| Notebook de travail | Google Colab | Calculs et graphiques en édition partagée | _à ajouter_ |
| Présentation | Google Slides | Diaporama final | _à ajouter_ |

**Règle de partage :** ce qui est en cours de rédaction reste dans le Drive ; ce qui est validé est exporté dans le dépôt (notebook `.ipynb`, présentation en PDF, veille dans ce README).

---

## Consignes

### Veille

Mener une veille rigoureuse à partir de sources institutionnelles de référence et d'articles peer-reviewed. Pas de blog LinkedIn. Chaque chiffre avancé doit pouvoir être rattaché à une source.

### Lois d'échelle (scaling laws)

Les lois d'échelle décrivent comment les performances et les besoins d'un modèle évoluent avec sa taille, ses données et le compute. C'est l'outil de projection du projet.

| Étape | Ce qu'il faut faire |
|-------|---------------------|
| **Étudier** | Kaplan et al., Hoffmann et al. (Chinchilla) et travaux associés. Comprendre les relations du type loss ∝ compute^α. |
| **Appliquer** | Partir des caractéristiques connues des systèmes actuels (GPT-4, Gemini, Claude…). |
| **Projeter** | Extrapoler : si la demande croît de X % par an, quelle énergie en 2027, 2030, 2035 ? |

### Limites à projeter

- Consommation électrique en fonction du volume de données, à l'entraînement et en inférence
- Consommation d'eau et autres ressources nécessaires au fonctionnement
- Capacité de production
- Émissions de gaz à effet de serre

### 3 scénarios chiffrés

| Scénario | Hypothèse |
|----------|-----------|
| **Pessimiste** | Rien ne change, la demande explose, les murs énergétiques sont atteints. |
| **Normal** | La tendance actuelle se poursuit, avec des ajustements incrémentaux. |
| **Optimiste** | Innovations majeures et politiques efficaces, découplage. |

### 3 recommandations

Chaque recommandation doit être :

- **Actionnable** — une décision prenable, pas un vœu pieux.
- **Fiable** — appuyée sur la veille et les calculs.
- **Stratégique** — pensée pour un ministre, pas pour un ingénieur.

Aucune recommandation qui ne tienne pas face à un journaliste sceptique.

### Pistes de sujets

Premier temps : énergie, environnement, société. Second temps : santé, éducation.

- Impact de l'IA sur la consommation et la production d'énergie
- IA et énergies renouvelables
- IA et consommation d'eau
- IA, énergies fossiles et métaux rares
- IA, pollution et biodiversité
- IA, démocratie et société
- IA et santé
- IA et éducation (l'école de demain)
- IA, sécurité et cybersécurité
- IA et quantique, IA et robotique
- Coût des erreurs évitables grâce à l'IA (orthographe, grammaire)

---

## Livrables

**1. Une présentation** (PDF, PowerPoint ou Google Slides)

- [ ] Trajectoire, obstacles, innovations, impact
- [ ] Storytelling cohérent avec les tendances
- [ ] Data visualisations convaincantes
- [ ] 3 scénarios et 3 recommandations

**2. Un dépôt GitHub public `Energy-wall`**

- [ ] README : contexte du projet et veille scientifique complète
- [ ] Notebook Jupyter : calculs préparatoires et data visualisations, reproductibles
- [ ] Présentation finale
- [ ] Dépôt propre et documenté

### Compétences visées

- Concevoir et structurer une veille technologique et réglementaire
- Synthétiser les données issues de la veille pour en faire une restitution
- Recommander des solutions innovantes basées sur les résultats de la veille
- Gestion de projet et collaboration
- Présentation des résultats et recommandations
- Analyse de données
- Modélisation prédictive
- Data visualisation et storytelling

---

## Organisation

### Phases

| Phase | Objet | Détail |
|-------|-------|--------|
| 1 | **Veille scientifique** | Lecture des sources de référence, prise de notes structurée, bibliographie solide. |
| 2 | **Collecte et modélisation** | Récupération des données chiffrées, application des lois d'échelle, notebook reproductible. |
| 3 | **Scénarios et recommandations** | Construction des 3 scénarios chiffrés, formulation des 3 recommandations. |
| 4 | **Storytelling et livrable** | Mise en forme de la présentation, data viz exécutive, répétition devant un public critique. |

L'ordre n'est pas figé ; l'important est de tenir les quatre phases.

### Premiers pas

- [x] Constituer l'équipe
- [x] Créer le dépôt avec un README structuré
- [ ] Démarrer la veille (IEA et Shift Project en priorité)
- [ ] Identifier **3 métriques clés** suivies tout au long du projet
- [ ] Fixer le point d'étape hebdomadaire

### Travailler dans le dépôt

Chacun a sa branche : `Romuald`, `Emile`, `Olivier`. `main` est la base commune.

```bash
git checkout Romuald          # se placer sur sa branche
git pull origin main          # récupérer la base à jour avant de commencer
# ... travail, commits ...
git push                      # pousser sa branche
```

L'intégration dans `main` passe par une pull request relue par un autre membre.

Les notebooks fusionnent mal : éviter de modifier le même `.ipynb` à plusieurs en parallèle (travailler dans Colab, ou un notebook par personne) et vider les sorties avant de committer.

### Arborescence

```
energy-wall/
├── README.md          # contexte, consignes, veille
├── documents/         # sujet et support de kick-off
├── notebooks/         # (à venir) calculs et data visualisations
├── data/              # (à venir) jeux de données utilisés
└── presentation/      # (à venir) diaporama final
```

---

## Ressources

### Documents du projet

- [Sujet — Energy Wall (PDF)](documents/Energy%20wall.pdf)
- [Support de kick-off (PDF)](documents/KickOff_EnergyWall.pdf)
- [Notes de kick-off](documents/Kick-off.md)

### Sources de référence

| Source | Ce qu'on y trouve | Lien |
|--------|-------------------|------|
| **Agence Internationale de l'Énergie (IEA)** | Données et rapports sur l'énergie, les data centers, l'IA et les scénarios de transition énergétique | [iea.org](https://www.iea.org) |
| **The Shift Project** | Rapport « Intelligence artificielle, données, calculs : quelles infrastructures dans un monde décarboné ? » | [Rapport final](https://theshiftproject.org/publications/intelligence-artificielle-centres-de-donnees-rapport-final/) |
| **GHG Protocol** | Cadre méthodologique de référence pour le calcul des émissions de GES (Scopes 1, 2, 3) | [ghgprotocol.org](https://ghgprotocol.org) |
| **Open Power System Data** | Jeux de données open source sur la production et la consommation d'électricité, renouvelables et indicateurs de marché | [open-power-system-data.org](https://open-power-system-data.org) |
| **World Bank Climate Change Knowledge Portal** | Données climatiques et indicateurs de vulnérabilité, pour relier énergie, climat et impact | [Portail](https://climateknowledgeportal.worldbank.org) · [GitHub](https://github.com/worldbank/climateknowledgeportal) |

### Lois d'échelle

- Kaplan et al. (2020), *Scaling Laws for Neural Language Models* — [arXiv:2001.08361](https://arxiv.org/abs/2001.08361)
- Hoffmann et al. (2022), *Training Compute-Optimal Large Language Models* (Chinchilla) — [arXiv:2203.15556](https://arxiv.org/abs/2203.15556)

### Ordres de grandeur de départ

Chiffres donnés au kick-off comme point de départ des projections. **À vérifier et sourcer précisément pendant la veille avant toute réutilisation.**

| Indicateur | Ordre de grandeur |
|------------|-------------------|
| Part des data centers dans l'électricité mondiale | ~2 %, pourrait doubler d'ici 2030 (IEA) |
| Requête LLM vs recherche classique | ~10 fois plus énergivore |
| Entraînement d'un LLM | GPT-3 ≈ 1 300 MWh ; modèles frontier en croissance exponentielle |
| Eau de refroidissement d'un gros data center IA | Plusieurs millions de litres par an |

---

## Veille scientifique et technologique

_Section à compléter au fil du projet — c'est un livrable évalué._

### Métriques clés suivies

1. _à définir_
2. _à définir_
3. _à définir_

### Synthèse par angle

#### 01 · Trajectoire

#### 02 · Obstacles

#### 03 · Innovations

#### 04 · Impact

### Scénarios

### Recommandations

### Bibliographie
