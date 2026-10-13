# IA et Energie

Prevoir l'écosystème de l'IA dans le domaine de l'énergie et environnement dans un premier temps et sociétal, puis dans les domaines de la santé et de l'éducation par exemple dans un second temps. Tout ca en prévision de 2029.

Trouver des indicateurs, chiffres, etc...
Comparer

De la créativité, mais de la vérité surtout !

# Idées de points a aborder :
- L'impact de l'IA sur la consommation énergétique
- L'impact de l'IA sur la production d'énergie
- L'impact de l'IA sur les énergies renouvelables
- L'impact de l'IA sur la consommation d'eau
- Les fautes d'orthographe et de grammaire sont très couteux et peuvent être évités grâce à l'IA
- L'impact de l'IA sur la démocratie et la société
- L'impact de l'IA sur la santé
- L'impact de l'IA sur l'éducation (l'école de demain)
- L'impact de l'IA sur la sécurité et la cybersécurité
- L'IA et le quantique
- L'IA et la robotique
- L'IA sur les energies fossiles et métaux rares
- L'IA et la pollution
- L'IA et la biodiversité

Pensez pour un ministre, pas des injenieur mais des journalistes, des politiques, des citoyens. Il faut vulgariser et rendre accessible les informations.


Consignes intra : 
Les étudiants mènent une veille scientifique rigoureuse à partir de sources institutionnelles de référence (IEA, Shift Project, GHG Protocol, Open Power System Data, World Bank Climate). Ils étudient les scaling laws les lois d’échelle qui décrivent comment la consommation énergétique de l’IA évolue avec la demande et les caractéristiques des systèmes. Ils construisent un notebook Jupyter qui applique ces lois pour projeter l’évolution des limites : consommation électrique à l’entraînement et en inférence, besoins en eau et ressources, capacité de production, émissions GES. Ils bâtissent trois scénarios chiffrés pessimiste, normal, optimiste et formulent trois recommandations actionnables, fiables et stratégiques, défendables face à des journalistes avertis.

# Angles complémentaires

Ordres de grandeur cités de mémoire : à vérifier et sourcer pendant la veille.

1. **Le mur est un mardi de décembre à 19 h.** On raisonne en TWh par an, mais le réseau casse sur la puissance à la pointe. La France est très thermosensible (de l'ordre de 2,4 GW de plus par degré en moins l'hiver, selon RTE). À calculer : puissance appelée par les data centers à la pointe hivernale, comparée à la marge du réseau.
2. **Qui débranche-t-on en premier ?** Lors d'un délestage, il y a un ordre de priorité. Un data center passe-t-il avant ou après le TGV, l'hôpital, le chauffage d'un quartier ? Décision politique que personne n'a prise publiquement.
3. **Le data center comme amortisseur du réseau.** Un entraînement de modèle peut se mettre en pause. Une étude de Duke University (2025) estime que le réseau américain pourrait absorber des dizaines de GW de nouvelle charge si elle acceptait de s'effacer moins de 1 % du temps. Recommandation possible : conditionner le raccordement à une obligation d'effacement.
4. **Le plafond humain a sauté.** La demande était bornée par l'attention de 8 milliards d'humains. Avec les agents, des machines interrogent des machines, et un modèle « qui raisonne » consomme 10 à 100 fois plus de tokens par tâche. Les gains d'efficacité sont absorbés par l'usage (effet rebond).
5. **L'électron qui manquera ailleurs.** Chaque TWh décarboné donné à l'IA n'ira pas aux voitures électriques, aux pompes à chaleur ou à l'industrie. À l'inverse, l'emplacement du calcul pèse plus que le modèle : l'intensité carbone du kWh varie d'un facteur 10 à 20 entre la France et la Pologne.
6. **Deux ans contre dix ans.** Un data center se construit en 18 à 24 mois, une ligne haute tension en 7 à 10 ans, un réacteur en 10 à 15 ans. Les gros transformateurs ont des délais de livraison de plusieurs années. SMR et fusion n'arriveront pas avant 2029.
7. **On pilote à l'aveugle.** Les estimations de consommation par requête varient d'un facteur 10 faute de données publiées. La comptabilité carbone « market-based » (certificats verts) affiche des émissions très inférieures à la réalité du réseau local. Recommandation possible : obligation de transparence.

En réserve :
- Chaleur fatale : un data center est un radiateur de 100 MW qu'on pourrait brancher sur un réseau de chaleur.
- Carbone de fabrication des puces (Scope 3).
- Arbitrage eau contre électricité dans le refroidissement.

