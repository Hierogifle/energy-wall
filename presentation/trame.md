# Signal rouge : trame orale

Présentation de 15 minutes, 13 diapositives, trois voix.

| Qui | Diapositives | Temps de parole |
|-----|--------------|-----------------|
| Romuald | 1, 2, 5, 6, 7, 13 | 6 min |
| Olivier | 3, 8, 9, 12 | 5 min |
| Émile | 4, 10, 11 | 4 min |

## Avant de commencer

- Ouvrir `presentation/index.html` dans un navigateur, avec une connexion internet (pour les polices). Sans internet, la présentation fonctionne, avec une police de secours.
- Flèche droite, espace ou clic : diapositive suivante. Flèche gauche : retour. `F` : plein écran.
- Version de secours : `presentation/energy-wall.pdf`.

## Le principe

Nous sommes les experts du ministre, bloqués dans le train le mardi 11 décembre 2029 à 19 h 04. L'horloge en bas à droite avance avec la présentation ; à 19 h 19, le train repart. La ligne en haut de l'écran montre où nous en sommes, de l'arrêt au départ.

Chaque partie s'ouvre sur une réplique des journalistes du sujet, en italique. Celui qui parle la lit, puis y répond.

Trois couleurs, toujours les mêmes : rouge pour le scénario pessimiste, orange pour le normal, vert pour l'optimiste. Ce sont les couleurs des signaux ferroviaires.

La chute, à la diapositive 6 : en France, le train ne s'arrête pas faute d'électricité. Il s'arrête à un signal rouge parce que la voie devant lui est réservée par des trains qui ne passent pas. C'est ce que décrit RTE.

---

## 1. Arrêt (Romuald, 30 s, 19:04)

**À dire.** Mardi 11 décembre 2029, 19 h 04. Notre train s'arrête en pleine campagne. Plus d'électricité. Nous accompagnons le ministre à une conférence sur l'IA, et dans le wagon-bar, les journalistes ont déjà trouvé le coupable.

**Attention.** C'est la fiction du sujet. Le pied de page le dit : on ne présente jamais cette panne comme une prévision.

## 2. Le wagon-bar (Romuald, 1 min, 19:05)

**À dire.** Lire deux répliques à voix haute, pas les quatre. Puis : « Le ministre nous pose une question simple : pourquoi le train s'arrête, et pas le data center ? Le train repart dans quinze minutes. On a jusque-là pour lui répondre, en quatre temps : comment on en est arrivé là, ce qui bloque, ce qui peut aider, et ce que ça coûte à la planète. »

**Transition.** « Olivier, on pouvait le voir venir ? »

## 3. Trajectoire : la demande double (Olivier, 1 min 30, 19:06)

**À dire.** On pouvait le prévoir. Depuis 2025, l'Agence internationale de l'énergie publie la courbe : 415 TWh consommés par les data centers en 2024, 1,5 % de l'électricité mondiale. 945 TWh en 2030, plus que le Japon entier aujourd'hui. Environ 1 200 en 2035, avec une fourchette de 700 à 1 700 selon les hypothèses.

Trois moteurs tirent la courbe. L'inférence : chaque fois qu'un modèle répond, il consomme, et il répond des millions de fois par jour. Les agents, qui enchaînent les requêtes sans humain derrière. Et les lois d'échelle : Kaplan en 2020, puis Chinchilla en 2022, ont montré que plus de calcul donne de meilleurs modèles. L'industrie a donc acheté du calcul.

**Chiffre clé.** 415 TWh en 2024, 945 en 2030 (IEA, *Energy and AI*, 2025).

**Question piège.** « Les lois d'échelle prédisent la consommation ? » Non. Elles relient la performance au calcul. Pour passer au kWh, il faut le rendement des puces, leur taux d'utilisation, le refroidissement et le volume d'usage. C'est ce que fait notre modèle.

**Transition.** « Émile a traduit ces chiffres en quelque chose de plus parlant. »

## 4. Trajectoire : en réacteurs (Émile, 1 min 30, 19:08)

**À dire.** 415 TWh par an, c'est une puissance moyenne de 47 GW, soit 47 réacteurs nucléaires d'un gigawatt qui tournent en continu pour les data centers du monde. Dans notre scénario normal, ils sont 80 en 2029. Dans le pessimiste, 109. Toute la France en compte 57.

Et la réalité va plus vite que nos hypothèses : en 2025, la consommation a crû de 17 %. Notre modèle prévoyait 6 à 14 %. Nous n'avons pas recalé le modèle pour coller au chiffre : on vous le montre tel quel. La réalité roule déjà sur la voie haute.

**Chiffre clé.** 47 réacteurs en 2024, 80 en 2029 (scénario normal).

**Question piège.** « Pourquoi des réacteurs d'un gigawatt ? » C'est un ordre de grandeur : les réacteurs français font de 900 à 1 650 MW. On divise la consommation annuelle par les 8 760 heures de l'année.

**Transition.** « Si la demande était prévisible, pourquoi le réseau n'a pas suivi ? Romuald. »

## 5. Obstacles : le temps (Romuald, 1 min 15, 19:09)

**À dire.** Parce que l'IA grandit en mois, et le réseau en décennies. Un data center se construit en deux ou trois ans. Une ligne à haute tension, quatre à huit ans dans les pays avancés. Dans certaines régions, attendre son raccordement prend jusqu'à dix ans. Les délais de livraison des transformateurs et des câbles ont doublé en trois ans.

Là où les data centers se concentrent, le mur est déjà là : ils consomment 20 % de l'électricité en Irlande, 25 % en Virginie. Dublin a suspendu les nouveaux raccordements jusqu'en 2030.

**Chiffre clé.** 2 à 3 ans contre 4 à 8 ans (IEA, 2025).

**Question piège.** « Et les puces, la chaleur ? » Plus une baie de serveurs est puissante, plus il faut évacuer de chaleur ; le refroidissement liquide devient obligatoire et demande de l'eau. Les puces et leurs métaux viennent de quelques pays : on y revient dans l'impact.

## 6. Obstacles : le canton occupé (Romuald, 1 min 15, 19:11)

**À dire.** Et en France ? Sur une voie ferrée, un train s'arrête au signal rouge quand le tronçon devant lui, le canton, est occupé. Notre train est arrêté. Mais regardez le canton : il est réservé par un train qui ne passe pas.

Au 1er novembre 2025, des data centers avaient réservé 14 GW de raccordement auprès de RTE. Ceux qui sont déjà branchés n'utilisent que 20 % de la puissance qu'ils ont réservée. RTE parle lui-même de projets « fantômes » et de « saturation artificielle ».

La France ne manque pas d'électricité. Des réservations bloquent la voie de l'industrie, de l'hydrogène et des transports.

**Chiffre clé.** 14 GW réservés, 20 % utilisés (RTE, Bilan prévisionnel 2025).

**Question piège.** « Alors la panne de 2029 est impossible ? » Une panne nationale par manque de production est peu probable selon RTE. Le risque en France, c'est un réseau bloqué par des réservations pendant que d'autres projets attendent. Ailleurs, en Irlande ou en Virginie, la pénurie locale existe déjà.

## 7. Innovations (Romuald, 1 min 30, 19:12)

**À dire.** Le journaliste demande si l'IA peut se sauver elle-même. En partie, avec ce qui existe déjà.

Disponible avant 2029 : des modèles plus sobres, petits, compressés, avec mise en cache ; l'IEA chiffre ce levier à 20 % de consommation en moins en 2035. Des data centers flexibles, qui décalent l'entraînement hors des heures de pointe. Construire là où le réseau et l'eau suivent, en récupérant la chaleur. Et l'IA au service du réseau : si on l'adoptait largement, elle éviterait l'équivalent de 5 % des émissions du secteur de l'énergie en 2035.

Trop tard pour 2029 : les petits réacteurs nucléaires, dont les premiers arriveront en fin de décennie, la fusion, le calcul quantique, les data centers en orbite. Ce sont des paris de recherche, pas des réponses pour ce soir.

**Chiffre clé.** −20 % en 2035 dans le cas de forte efficacité de l'IEA.

**Question piège.** « Les petits réacteurs, c'est pour bientôt ? » 25 GW sont annoncés pour les data centers, presque tous aux États-Unis, mais l'IEA n'attend les premiers projets qu'à la fin de la décennie.

**Transition.** « Reste la question de la planète. Olivier. »

## 8. Impact : les émissions (Olivier, 1 min, 19:13)

**À dire.** Si rien ne change, les émissions des data centers quintuplent d'ici 2035 : de 190 à près de 940 millions de tonnes de CO₂ dans notre scénario pessimiste. Dans le normal, 385 ; dans l'optimiste, elles baissent à 172.

Nous comptons les émissions du réseau réel où le data center se branche, pas celles de ses contrats d'électricité verte. Et fabriquer les serveurs ajoute encore 15 à 67 millions de tonnes par an en 2035.

**Chiffre clé.** 939 / 385 / 172 Mt CO₂e en 2035. Repère IEA : 300 Mt.

**Question piège.** « Les géants du numérique disent être neutres en carbone. » Ils comptent leurs contrats d'électricité verte (méthode « market-based »). Le GHG Protocol demande aussi la méthode « location-based », celle du réseau réel ; c'est celle que nous utilisons.

## 9. Impact : eau et métaux (Olivier, 1 min, 19:14)

**À dire.** L'eau et les métaux ne s'affichent pas sur le compteur. Les data centers consomment 560 milliards de litres d'eau par an, 1 200 milliards en 2030 selon l'IEA. Deux tiers servent à produire leur électricité. Un site de 100 MW boit autant que 6 500 foyers.

Côté métaux, 98 % du gallium, indispensable aux puces, est raffiné en Chine, qui en restreint l'export depuis décembre 2024. Le cuivre dépasse 14 000 dollars la tonne, et l'IEA prévoit un déficit d'offre de 25 % en 2035.

**Chiffre clé.** 560 puis 1 200 milliards de litres (IEA, 2025) ; gallium raffiné à 98 % en Chine.

**Question piège.** « Votre modèle donne 10 000 hm³ d'eau en 2035, c'est énorme. » C'est le scénario pessimiste, qui cumule forte demande et paramètres d'eau défavorables : à lire comme une borne haute. L'eau est notre indicateur le plus incertain.

**Transition.** « Alors où va-t-on ? Émile a construit le modèle. »

## 10. Aiguillage : trois voies (Émile, 1 min 45, 19:16)

**À dire.** Trois voies partent d'ici. Notre modèle sépare l'entraînement, l'inférence et le reste des data centers, et fait évoluer chaque poste selon la demande, l'efficacité des puces et le refroidissement. 284 tests le vérifient.

En rouge, rien ne change : 2 155 TWh en 2035, cinq fois 2024. En orange, la tendance actuelle : 979 TWh. En vert, l'IA alignée sur ce que le réseau et les ressources peuvent fournir : 511 TWh, la consommation baisse après 2031. Les pointillés montrent une capacité qui croîtrait de 12 % par an. Sur la voie rouge, même une capacité qui croîtrait de 18 % par an est dépassée dès 2029.

Nous le disons franchement : 71 % des bornes de nos paramètres sont des hypothèses justifiées, pas des mesures. C'est un exercice de sensibilité, pas une prévision.

**Chiffre clé.** 2 155 / 979 / 511 TWh en 2035. Repères IEA : 1 700 / 1 200 / 700.

**Question piège.** « Pourquoi votre scénario normal est sous celui de l'IEA ? » Nous n'avons pas calé nos scénarios sur l'IEA : nous les comparons. Notre normal est 18 % sous le repère de l'IEA, et la croissance réelle de 2025 suggère que nous sommes plutôt trop prudents.

## 11. Aiguillage : le test miracle (Émile, 45 s, 19:17)

**À dire.** On a posé la question à l'envers : de combien les puces devraient-elles progresser pour rester sous 700 TWh en 2035 ? Sur la voie rouge, il faudrait doubler l'efficacité de toutes les puces en service tous les 1,6 an. Les meilleures puces du marché doublent tous les 1,7 à 3 ans. Aucune ne va assez vite. L'innovation ne suffira pas sans décisions.

**Chiffre clé.** 1,6 / 2,2 / 3,4 ans, contre 1,7 à 3 ans pour les meilleures puces (Epoch AI).

**Transition.** « Les décisions, justement. Olivier. »

## 12. Trois décisions (Olivier, 1 min 30, 19:18)

**À dire.** Trois décisions pour l'aiguilleur.

Libérer la voie : raccorder d'abord les projets mûrs, reprendre la puissance réservée et inutilisée, et exiger que chaque nouveau data center s'efface aux heures de pointe. La CRE a ouvert la porte en juillet 2025 ; il faut aller au bout.

Mesurer en public : chaque grand site publie son électricité, sa pointe, son eau et ses émissions sur le réseau réel. Le règlement européen de 2024 impose déjà une déclaration ; il faut la rendre publique et complète.

Choisir où construire : autoriser un site selon ce que le réseau et l'eau locale supportent, et imposer la récupération de chaleur près d'un réseau de chaleur.

**Question piège.** « L'effacement, les opérateurs n'en voudront pas. » L'IEA le reconnaît : arrêter des serveurs coûte cher. Mais beaucoup de sites ont des serveurs en réserve, des batteries et des groupes de secours qu'ils peuvent mobiliser. En échange, ils obtiennent un raccordement plus rapide.

## 13. Départ (Romuald, 30 s, 19:19)

**À dire.** 19 h 19. Le train repart. Pendant ces quinze minutes, en 2029, les data centers du monde auront consommé environ 20 GWh. Les voies que nous posons en 2029, nous roulerons dessus en 2050. Merci.

---

## Si on vous pose la question

- **« Une requête ChatGPT consomme dix fois plus qu'une recherche Google ? »** Nous ne reprenons pas ce chiffre : il dépend du modèle, de la longueur de la réponse et de la méthode de mesure. Selon l'IEA, générer un texte va d'environ 0,3 Wh avec un petit modèle à 5 Wh avec un modèle moyen ; une courte vidéo, environ 115 Wh.
- **« Vos chiffres portent sur l'IA ou sur tous les data centers ? »** Sur tous les data centers, IA comprise. C'est le périmètre des statistiques publiques.
- **« Pourquoi pas jusqu'en 2050 ? »** L'IEA-4E déconseille de projeter au-delà de cinq ans ; nous allons déjà jusqu'à 2035 en le signalant. Au-delà, ce serait de la fiction.
- **« Combien a coûté votre propre calcul ? »** Le notebook tourne en quelques minutes sur un ordinateur portable : une consommation négligeable à côté de celle d'un entraînement de modèle.
- **« Où sont vos sources ? »** Dans le README du dépôt Energy-wall, et pour chaque paramètre du modèle dans `data/sources.yaml`, avec son statut : mesure, projection, dérivation ou hypothèse.
