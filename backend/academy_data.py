"""
BULL SAGE ACADEMY - Contenu pédagogique complet
Parcours d'apprentissage gamifié pour débutants
Conçu pour être compréhensible par un enfant de 12 ans
"""

# ============== SYSTÈME DE NIVEAUX ET XP ==============

LEVEL_THRESHOLDS = [
    {"level": 1, "title": "Nouveau Venu", "min_xp": 0, "icon": "🌱"},
    {"level": 2, "title": "Curieux", "min_xp": 100, "icon": "🔍"},
    {"level": 3, "title": "Apprenti", "min_xp": 250, "icon": "📚"},
    {"level": 4, "title": "Étudiant", "min_xp": 500, "icon": "✏️"},
    {"level": 5, "title": "Pratiquant", "min_xp": 800, "icon": "💪"},
    {"level": 6, "title": "Trader Junior", "min_xp": 1200, "icon": "📈"},
    {"level": 7, "title": "Trader", "min_xp": 1800, "icon": "💼"},
    {"level": 8, "title": "Analyste", "min_xp": 2500, "icon": "🔬"},
    {"level": 9, "title": "Expert", "min_xp": 3500, "icon": "🎯"},
    {"level": 10, "title": "Maître Trader", "min_xp": 5000, "icon": "👑"},
]

XP_REWARDS = {
    "lesson_complete": 50,
    "quiz_pass": 100,
    "quiz_perfect": 50,  # Bonus
    "quiz_first_try": 25,  # Bonus
    "daily_streak": 25,
    "module_complete": 200,
    "all_modules_complete": 1000,
}

# ============== BADGES ==============

BADGES = [
    {
        "id": "first_lesson",
        "name": "Premier Pas",
        "description": "Tu as terminé ta première leçon !",
        "icon": "🎯",
        "condition": "complete_1_lesson"
    },
    {
        "id": "curious_mind",
        "name": "Esprit Curieux",
        "description": "Tu as terminé 5 leçons",
        "icon": "🧠",
        "condition": "complete_5_lessons"
    },
    {
        "id": "bookworm",
        "name": "Dévoreur de Savoir",
        "description": "Tu as terminé 15 leçons",
        "icon": "📚",
        "condition": "complete_15_lessons"
    },
    {
        "id": "quiz_master",
        "name": "Maître du Quiz",
        "description": "Score parfait à un quiz !",
        "icon": "🏆",
        "condition": "perfect_quiz"
    },
    {
        "id": "streak_3",
        "name": "En Route",
        "description": "3 jours d'apprentissage consécutifs",
        "icon": "🔥",
        "condition": "streak_3_days"
    },
    {
        "id": "streak_7",
        "name": "Sur ta Lancée",
        "description": "7 jours d'apprentissage consécutifs",
        "icon": "⚡",
        "condition": "streak_7_days"
    },
    {
        "id": "streak_30",
        "name": "Inarrêtable",
        "description": "30 jours d'apprentissage consécutifs !",
        "icon": "💎",
        "condition": "streak_30_days"
    },
    {
        "id": "module_1_complete",
        "name": "Les Bases Maîtrisées",
        "description": "Module 1 terminé avec succès",
        "icon": "🌟",
        "condition": "complete_module_1"
    },
    {
        "id": "module_2_complete",
        "name": "Lecteur de Graphiques",
        "description": "Module 2 terminé avec succès",
        "icon": "📊",
        "condition": "complete_module_2"
    },
    {
        "id": "module_3_complete",
        "name": "Technicien",
        "description": "Module 3 terminé avec succès",
        "icon": "🔧",
        "condition": "complete_module_3"
    },
    {
        "id": "module_4_complete",
        "name": "Gestionnaire de Risque",
        "description": "Module 4 terminé avec succès",
        "icon": "🛡️",
        "condition": "complete_module_4"
    },
    {
        "id": "module_5_complete",
        "name": "Maître de Soi",
        "description": "Module 5 terminé avec succès",
        "icon": "🧘",
        "condition": "complete_module_5"
    },
    {
        "id": "module_6_complete",
        "name": "Stratège",
        "description": "Module 6 terminé avec succès",
        "icon": "♟️",
        "condition": "complete_module_6"
    },
    {
        "id": "graduate",
        "name": "Diplômé BULL SAGE",
        "description": "Tu as terminé tout le parcours !",
        "icon": "🎓",
        "condition": "complete_all_modules"
    },
    {
        "id": "high_scorer",
        "name": "Excellence",
        "description": "Moyenne de 90%+ sur tous les quiz",
        "icon": "⭐",
        "condition": "average_90_percent"
    },
]

# ============== MODULES ET LEÇONS ==============

ACADEMY_MODULES = [
    {
        "id": "module_1",
        "title": "Les Bases du Trading",
        "description": "Découvre le monde fascinant du trading ! Comme un jeu vidéo, mais avec de vraies stratégies.",
        "icon": "🌟",
        "color": "emerald",
        "order": 1,
        "estimated_time": "45 min",
        "lessons": [
            {
                "id": "lesson_1_1",
                "title": "C'est quoi le trading ?",
                "description": "Comprendre l'idée de base du trading",
                "order": 1,
                "xp_reward": 50,
                "content": """
# 🎮 C'est quoi le trading ?

Salut ! Je suis **BULL**, ton coach trading ! 🐂

Imagine que tu collectionnes des cartes Pokémon. Un jour, tu achètes une carte Pikachu rare à 5€. Quelques semaines plus tard, tout le monde veut cette carte et elle vaut maintenant 15€. Tu la revends et tu as gagné 10€ !

**C'est exactement ça, le trading !**

## 💡 Le Trading en 3 points simples

1. **Acheter** quelque chose (une crypto, une action, etc.)
2. **Attendre** que sa valeur change
3. **Vendre** pour faire un profit (ou limiter une perte)

## 🎯 L'objectif du trader

> "Acheter bas, vendre haut" - C'est la règle d'or !

C'est comme quand tu achètes des glaces pas chères en hiver pour les revendre plus cher en été. Malin, non ? 😉

## 🌍 Où ça se passe ?

Le trading se fait sur des **marchés**. Pense à un grand marché (comme celui de ta ville), mais en ligne et ouvert 24h/24 pour les cryptos !

- **Bourse** : Pour acheter des parts d'entreprises (Apple, Tesla...)
- **Crypto** : Pour acheter des monnaies numériques (Bitcoin, Ethereum...)
- **Forex** : Pour échanger des devises (Euro contre Dollar...)

## ⚠️ Attention !

Le trading peut faire **gagner** de l'argent, mais aussi en **perdre**. C'est pour ça qu'on va t'apprendre à être prudent et intelligent !

## 🧠 Retiens bien

- Le trading = acheter et vendre pour faire du profit
- Il faut être patient et stratégique
- On ne joue jamais avec l'argent dont on a besoin
""",
            },
            {
                "id": "lesson_1_2",
                "title": "Les marchés financiers",
                "description": "Découvre où se font les échanges",
                "order": 2,
                "xp_reward": 50,
                "content": """
# 🏛️ Les Marchés Financiers

Hey ! C'est encore **BULL** ! 🐂 Aujourd'hui, on explore les différents marchés.

## 🎪 Imagine un grand marché

Tu connais les marchés où on vend des fruits et légumes ? Les marchés financiers, c'est pareil, mais au lieu de tomates, on échange de l'argent, des cryptos et des parts d'entreprises !

## 📊 Les 3 grands types de marchés

### 1. 📈 La Bourse (Actions)
Quand tu achètes une **action**, tu deviens propriétaire d'un petit morceau d'une entreprise !

*Exemple : Si tu achètes une action Apple, tu possèdes une toute petite partie d'Apple. Cool, non ?*

### 2. 🪙 Les Cryptomonnaies
Ce sont des monnaies **100% numériques**, qui existent uniquement sur Internet.

*Exemple : Bitcoin, Ethereum, Solana... C'est comme de l'or digital !*

### 3. 💱 Le Forex (Devises)
C'est l'échange entre différentes monnaies du monde.

*Exemple : Échanger des Euros contre des Dollars quand tu pars en vacances aux USA.*

## ⏰ Quand sont-ils ouverts ?

| Marché | Horaires |
|--------|----------|
| Bourse | Lundi-Vendredi, heures fixes |
| Crypto | **24h/24, 7j/7** 🌙 |
| Forex | Lundi-Vendredi, presque 24h |

**Les cryptos ne dorment jamais !** C'est pour ça qu'elles sont populaires.

## 🐂 vs 🐻 : Bull et Bear

Dans le trading, on utilise deux animaux pour décrire le marché :

- 🐂 **BULL (Taureau)** = Le marché MONTE (c'est bien !)
- 🐻 **BEAR (Ours)** = Le marché DESCEND (attention !)

> C'est pour ça que je m'appelle BULL ! Je suis là quand ça monte ! 😄

## 🎯 À retenir

- Plusieurs marchés existent (Bourse, Crypto, Forex)
- Les cryptos sont ouvertes tout le temps
- Bull = marché qui monte, Bear = marché qui descend
""",
            },
            {
                "id": "lesson_1_3",
                "title": "Bitcoin et les cryptomonnaies",
                "description": "Comprendre les monnaies numériques",
                "order": 3,
                "xp_reward": 50,
                "content": """
# 🪙 Bitcoin et les Cryptomonnaies

Bienvenue ! **BULL** ici ! 🐂 Parlons de ces fameuses cryptos !

## 💎 C'est quoi une cryptomonnaie ?

Imagine de l'argent qui existe **uniquement sur Internet**, sans pièces ni billets. C'est une cryptomonnaie !

### Pourquoi "crypto" ?
Parce qu'elle est protégée par de la **cryptographie** (des codes secrets super complexes). Impossible à falsifier !

## 👑 Le Roi : Bitcoin (BTC)

**Bitcoin** est la première et la plus célèbre des cryptomonnaies.

- 📅 Créé en 2009 par Satoshi Nakamoto (personne ne sait qui c'est vraiment !)
- 💰 Quantité limitée : seulement 21 millions de Bitcoin existeront
- 🏆 C'est "l'or numérique"

## 🌟 Les autres stars

| Crypto | Symbole | À quoi ça sert ? |
|--------|---------|------------------|
| Ethereum | ETH | Applications décentralisées |
| Solana | SOL | Transactions ultra rapides |
| XRP | XRP | Transferts internationaux |

## 📱 Comment ça marche ?

1. Tu crées un **portefeuille** (wallet) - comme un compte bancaire digital
2. Tu achètes des cryptos avec des euros
3. Tu peux les garder (HODL) ou les échanger

## 🎢 Pourquoi ça monte et ça descend ?

Le prix change selon l'**offre et la demande** :

- **Beaucoup de gens veulent acheter** → Le prix MONTE 📈
- **Beaucoup de gens veulent vendre** → Le prix DESCEND 📉

*C'est comme les sneakers en édition limitée : plus elles sont demandées, plus elles sont chères !*

## ⚠️ Les risques

- Les prix peuvent changer TRÈS vite (parfois -20% en une journée !)
- Ne jamais investir l'argent dont tu as besoin
- Toujours faire ses recherches avant d'acheter

## 🧠 À retenir

- Les cryptos sont de l'argent 100% numérique
- Bitcoin est le plus connu et le plus ancien
- Les prix changent selon l'offre et la demande
- C'est volatil (ça bouge beaucoup !)
""",
            },
            {
                "id": "lesson_1_4",
                "title": "Comprendre les prix",
                "description": "Pourquoi les prix montent et descendent",
                "order": 4,
                "xp_reward": 50,
                "content": """
# 📊 Comprendre les Prix

Yo ! **BULL** au rapport ! 🐂 Aujourd'hui, on comprend pourquoi les prix bougent !

## 🎪 L'histoire de la pizza magique

Imagine une pizzeria qui fait la **meilleure pizza du monde**.

- Au début, 5 personnes la connaissent → Pizza à 10€
- Puis 100 personnes la veulent → Pizza à 15€
- Un influenceur en parle → 10 000 personnes la veulent → Pizza à 50€ !

**C'est l'offre et la demande !**

## ⚖️ Offre et Demande

### La DEMANDE (ceux qui veulent acheter)
- Plus il y a d'acheteurs → Prix MONTE 📈

### L'OFFRE (ceux qui veulent vendre)
- Plus il y a de vendeurs → Prix DESCEND 📉

## 📈 Lire un prix

Quand tu regardes un prix de crypto, tu vois :

```
Bitcoin (BTC)
$88,000 (+2.5% 24h)
```

Cela veut dire :
- 1 Bitcoin vaut 88 000 dollars
- En 24h, le prix a augmenté de 2.5%

## 🎢 La volatilité

**Volatilité** = À quel point les prix bougent vite et fort

| Actif | Volatilité |
|-------|-----------|
| Euro/Dollar | Faible 😴 |
| Actions (Apple) | Moyenne 🙂 |
| Bitcoin | Haute 🎢 |
| Petites cryptos | Très haute 🚀 |

*Plus c'est volatil, plus tu peux gagner... mais aussi perdre !*

## 📰 Ce qui fait bouger les prix

1. **Les news** - Une bonne nouvelle = prix monte
2. **Les gros investisseurs** - Les "baleines" qui achètent/vendent beaucoup
3. **L'économie mondiale** - Inflation, taux d'intérêt...
4. **Les émotions** - La peur et la cupidité des gens

## 🔴 et 🟢 : Rouge et Vert

Sur les graphiques :
- 🟢 **Vert** = Le prix monte (positif)
- 🔴 **Rouge** = Le prix descend (négatif)

## 🧠 À retenir

- Les prix bougent selon l'offre et la demande
- Plus de demande = prix monte
- Plus d'offre = prix descend
- Les cryptos sont très volatiles
- Vert = ça monte, Rouge = ça descend
""",
            },
            {
                "id": "lesson_1_5",
                "title": "Les différents types de traders",
                "description": "Découvre quel style te correspond",
                "order": 5,
                "xp_reward": 50,
                "content": """
# 👥 Les Types de Traders

Salut champion ! **BULL** ici ! 🐂 Découvrons les différents styles de trading !

## 🎮 Choisis ton personnage !

Comme dans un jeu vidéo, il y a différentes "classes" de traders :

## ⚡ Le Scalper

**Temps de jeu** : Quelques secondes à minutes

C'est le **ninja** du trading ! Il fait plein de petites opérations très rapides.

✅ Avantages :
- Gains rapides
- Pas besoin d'attendre longtemps

❌ Inconvénients :
- Très stressant
- Demande beaucoup de concentration
- Pas pour les débutants !

## 🌊 Le Day Trader

**Temps de jeu** : Quelques heures (dans la journée)

Il ouvre et ferme toutes ses positions dans la **même journée**. Il ne garde rien la nuit.

✅ Avantages :
- Pas de stress la nuit
- Résultats chaque jour

❌ Inconvénients :
- Demande du temps libre
- Doit surveiller les écrans

## 🏄 Le Swing Trader

**Temps de jeu** : Quelques jours à semaines

Il **surfe sur les vagues** du marché. Il achète et garde quelques jours.

✅ Avantages :
- Moins stressant
- Pas besoin de regarder tout le temps

❌ Inconvénients :
- Patience nécessaire
- Le marché peut changer la nuit

## 🐢 Le Holder (HODLer)

**Temps de jeu** : Mois ou années

Il achète et **garde longtemps**, peu importe les variations.

✅ Avantages :
- Très simple
- Pas de stress quotidien
- Historiquement rentable sur Bitcoin

❌ Inconvénients :
- Faut être très patient
- Voir son investissement baisser peut être dur

> **HODL** = "Hold On for Dear Life" (Tiens bon !)

## 🧪 Quel type es-tu ?

| Si tu es... | Tu devrais être... |
|------------|-------------------|
| Patient et calme | Holder 🐢 |
| Actif mais pas pressé | Swing Trader 🏄 |
| Disponible et focus | Day Trader 🌊 |
| Expert et rapide | Scalper ⚡ |

## 💡 Conseil de BULL

> Pour débuter, commence par le **Swing Trading** ou le **Holding**. C'est moins stressant et tu auras le temps d'apprendre !

## 🧠 À retenir

- Scalper = Très rapide, très risqué
- Day Trader = Dans la journée
- Swing Trader = Quelques jours (idéal pour débuter)
- Holder = Longue durée, très patient
""",
            },
        ],
        "quiz": {
            "title": "Quiz - Les Bases du Trading",
            "description": "Vérifie que tu as bien compris les bases !",
            "passing_score": 70,
            "questions": [
                {
                    "id": "q1_1",
                    "question": "C'est quoi le principe de base du trading ?",
                    "type": "multiple_choice",
                    "options": [
                        "Acheter haut, vendre bas",
                        "Acheter bas, vendre haut",
                        "Toujours acheter sans jamais vendre",
                        "Vendre sans jamais acheter"
                    ],
                    "correct_answer": 1,
                    "explanation": "Le but du trading est d'acheter quand c'est pas cher et de vendre quand ça vaut plus cher. C'est comme acheter des sneakers en soldes et les revendre plus cher !"
                },
                {
                    "id": "q1_2",
                    "question": "Quel animal représente un marché qui MONTE ?",
                    "type": "multiple_choice",
                    "options": [
                        "L'ours (Bear)",
                        "Le taureau (Bull)",
                        "Le loup",
                        "L'aigle"
                    ],
                    "correct_answer": 1,
                    "explanation": "Le taureau (Bull) représente un marché haussier car il attaque en levant ses cornes vers le haut ! 🐂📈"
                },
                {
                    "id": "q1_3",
                    "question": "Quelle est la particularité du marché des cryptomonnaies ?",
                    "type": "multiple_choice",
                    "options": [
                        "Il est fermé le week-end",
                        "Il n'est ouvert que la nuit",
                        "Il est ouvert 24h/24, 7j/7",
                        "Il ferme à midi"
                    ],
                    "correct_answer": 2,
                    "explanation": "Les cryptomonnaies ne dorment jamais ! Le marché est ouvert tout le temps, même le dimanche à 3h du matin 🌙"
                },
                {
                    "id": "q1_4",
                    "question": "Qu'est-ce qui fait monter le prix d'un actif ?",
                    "type": "multiple_choice",
                    "options": [
                        "Quand beaucoup de gens veulent le vendre",
                        "Quand personne ne s'y intéresse",
                        "Quand beaucoup de gens veulent l'acheter",
                        "Quand il pleut"
                    ],
                    "correct_answer": 2,
                    "explanation": "Plus il y a de demande (gens qui veulent acheter), plus le prix monte. C'est la loi de l'offre et la demande !"
                },
                {
                    "id": "q1_5",
                    "question": "C'est quoi un 'Holder' ?",
                    "type": "multiple_choice",
                    "options": [
                        "Quelqu'un qui achète et vend très vite",
                        "Quelqu'un qui achète et garde longtemps",
                        "Quelqu'un qui ne fait que vendre",
                        "Quelqu'un qui regarde sans jamais acheter"
                    ],
                    "correct_answer": 1,
                    "explanation": "Un Holder achète et garde son investissement pendant des mois ou des années. HODL = Hold On for Dear Life ! 🐢"
                },
                {
                    "id": "q1_6",
                    "question": "Quelle couleur représente une hausse des prix ?",
                    "type": "multiple_choice",
                    "options": [
                        "Rouge",
                        "Bleu",
                        "Vert",
                        "Jaune"
                    ],
                    "correct_answer": 2,
                    "explanation": "Le vert signifie que le prix monte (positif), le rouge signifie qu'il descend (négatif). 🟢 = bien, 🔴 = attention !"
                },
                {
                    "id": "q1_7",
                    "question": "Qu'est-ce que le Bitcoin ?",
                    "type": "multiple_choice",
                    "options": [
                        "Une banque en ligne",
                        "La première et plus connue des cryptomonnaies",
                        "Un jeu vidéo",
                        "Une application de messagerie"
                    ],
                    "correct_answer": 1,
                    "explanation": "Bitcoin est la première cryptomonnaie, créée en 2009. C'est comme l'or du monde numérique ! 👑"
                },
                {
                    "id": "q1_8",
                    "question": "Quel style de trading est recommandé pour un débutant ?",
                    "type": "multiple_choice",
                    "options": [
                        "Scalping (très rapide)",
                        "Day Trading intensif",
                        "Swing Trading ou Holding",
                        "Tous en même temps"
                    ],
                    "correct_answer": 2,
                    "explanation": "Le Swing Trading et le Holding sont moins stressants et laissent le temps d'apprendre. Pas besoin d'être devant l'écran tout le temps !"
                },
            ]
        }
    },
    {
        "id": "module_2",
        "title": "Lire les Graphiques",
        "description": "Les graphiques racontent une histoire. Apprends à la lire !",
        "icon": "📊",
        "color": "blue",
        "order": 2,
        "estimated_time": "50 min",
        "lessons": [
            {
                "id": "lesson_2_1",
                "title": "Les chandeliers japonais",
                "description": "Des bougies qui racontent l'histoire des prix",
                "order": 1,
                "xp_reward": 50,
                "content": """
# 🕯️ Les Chandeliers Japonais

Hey ! **BULL** ici ! 🐂 Aujourd'hui, on apprend à lire les "bougies" !

## 📖 Un peu d'histoire

Les chandeliers ont été inventés au Japon il y a plus de 200 ans par des marchands de riz ! Ils les utilisaient pour suivre les prix du riz. Malin, non ?

## 🕯️ Anatomie d'un chandelier

Chaque bougie représente une période de temps (1 heure, 1 jour, etc.)

```
    │  ← Mèche haute (ombre)
  ┌─┴─┐
  │   │ ← Corps (la partie épaisse)
  └─┬─┘
    │  ← Mèche basse (ombre)
```

## 🟢 Bougie Verte (Haussière)

Une bougie **verte** signifie que le prix a **monté** pendant cette période.

```
    │
  ┌─┴─┐ ← Le prix a FERMÉ ici (plus haut)
  │ 🟢│
  └─┬─┘ ← Le prix a OUVERT ici (plus bas)
    │
```

- Le bas du corps = prix d'ouverture
- Le haut du corps = prix de fermeture
- La bougie est verte car : fermeture > ouverture 📈

## 🔴 Bougie Rouge (Baissière)

Une bougie **rouge** signifie que le prix a **baissé** pendant cette période.

```
    │
  ┌─┴─┐ ← Le prix a OUVERT ici (plus haut)
  │ 🔴│
  └─┬─┘ ← Le prix a FERMÉ ici (plus bas)
    │
```

- Le haut du corps = prix d'ouverture
- Le bas du corps = prix de fermeture
- La bougie est rouge car : fermeture < ouverture 📉

## 📏 Les mèches (ombres)

Les mèches montrent jusqu'où le prix est allé pendant la période :

- **Mèche haute** = le prix maximum atteint
- **Mèche basse** = le prix minimum atteint

*Plus la mèche est longue, plus il y a eu de bataille entre acheteurs et vendeurs !*

## 🎯 Exemples concrets

| Bougie | Ce qu'elle dit |
|--------|----------------|
| 🟢 Grande verte | Les acheteurs ont dominé ! Fort mouvement haussier |
| 🔴 Grande rouge | Les vendeurs ont dominé ! Fort mouvement baissier |
| Petite bougie | Indécision, personne ne domine |
| Longue mèche haute | Les vendeurs ont repoussé les acheteurs |
| Longue mèche basse | Les acheteurs ont repoussé les vendeurs |

## 💡 Conseil de BULL

> Regarde toujours **plusieurs bougies** ensemble, pas une seule ! L'histoire se lit sur plusieurs périodes.

## 🧠 À retenir

- Bougie verte = le prix a monté pendant cette période
- Bougie rouge = le prix a baissé
- Les mèches montrent les extrêmes (min et max)
- La taille du corps montre la force du mouvement
""",
            },
            {
                "id": "lesson_2_2",
                "title": "Les tendances",
                "description": "Haussière, baissière ou latérale ?",
                "order": 2,
                "xp_reward": 50,
                "content": """
# 📈 Les Tendances

Salut ! **BULL** au rapport ! 🐂 Parlons des tendances !

## 🎢 C'est quoi une tendance ?

Une tendance, c'est la **direction générale** du prix sur une période.

*Imagine que tu montes une colline : même si tu fais des petits pas en arrière parfois, globalement tu montes !*

## ⬆️ Tendance HAUSSIÈRE (Bullish)

Le prix fait des **hauts de plus en plus hauts** et des **bas de plus en plus hauts**.

```
                    📈
               /\\      
          /\\  /  \\
     /\\  /  \\/    
/\\  /  \\/
  \\/
```

**Comment la reconnaître ?**
- Les sommets sont de plus en plus hauts
- Les creux sont de plus en plus hauts
- On dit que le marché est "BULL" 🐂

## ⬇️ Tendance BAISSIÈRE (Bearish)

Le prix fait des **hauts de plus en plus bas** et des **bas de plus en plus bas**.

```
\\
 \\  /\\
  \\/  \\  /\\
       \\/  \\  /\\
            \\/  \\
                 📉
```

**Comment la reconnaître ?**
- Les sommets sont de plus en plus bas
- Les creux sont de plus en plus bas
- On dit que le marché est "BEAR" 🐻

## ➡️ Tendance LATÉRALE (Range)

Le prix oscille entre deux niveaux sans vraie direction.

```
───────────── Résistance
  /\\    /\\    /\\
 /  \\  /  \\  /  \\
/    \\/    \\/    \\
───────────── Support
```

**Comment la reconnaître ?**
- Le prix rebondit entre deux bornes
- Pas de direction claire
- On dit que le marché "range" ou "consolide"

## 🔍 Identifier la tendance

### Méthode simple : Les 3 derniers points

1. Regarde les 3 derniers sommets
2. Regarde les 3 derniers creux
3. S'ils montent → tendance haussière
4. S'ils descendent → tendance baissière
5. S'ils sont au même niveau → range

## ⚠️ La règle d'or

> **"The trend is your friend"** - La tendance est ton amie !

Ça veut dire : il est plus facile de trader **dans le sens** de la tendance que contre elle.

- En tendance haussière → cherche à **acheter**
- En tendance baissière → cherche à **vendre** (ou attendre)
- En range → attention, plus difficile !

## 💡 Conseil de BULL

> Ne te bats jamais contre la tendance ! Si le marché monte, ne cherche pas à vendre. Surfe sur la vague ! 🏄

## 🧠 À retenir

- Tendance haussière = sommets et creux de plus en plus hauts
- Tendance baissière = sommets et creux de plus en plus bas
- Range = le prix oscille sans direction
- Toujours trader dans le sens de la tendance !
""",
            },
            {
                "id": "lesson_2_3",
                "title": "Les timeframes",
                "description": "Regarder à différentes échelles de temps",
                "order": 3,
                "xp_reward": 50,
                "content": """
# ⏰ Les Timeframes

Yo ! C'est **BULL** ! 🐂 Aujourd'hui, on parle du temps !

## 🔬 C'est quoi un timeframe ?

Un timeframe, c'est la **durée** que représente chaque bougie sur ton graphique.

*Imagine Google Maps : tu peux voir ta rue (zoom), ton quartier, ta ville, ou tout ton pays (dézoom). C'est pareil avec les graphiques !*

## 📏 Les différents timeframes

| Timeframe | Chaque bougie = | Pour qui ? |
|-----------|-----------------|------------|
| 1 minute (1M) | 1 minute | Scalpers (très risqué) |
| 5 minutes (5M) | 5 minutes | Scalpers |
| 15 minutes (15M) | 15 minutes | Day traders |
| 1 heure (1H) | 1 heure | Day traders |
| 4 heures (4H) | 4 heures | Swing traders ⭐ |
| 1 jour (1D) | 1 jour | Swing traders ⭐ |
| 1 semaine (1W) | 1 semaine | Investisseurs |
| 1 mois (1M) | 1 mois | Investisseurs long terme |

## 🎯 Exemple concret

Imagine Bitcoin sur différents timeframes :

### En 1 minute
```
📈📉📈📉📈📉📈📉 → C'est la folie ! Ça bouge tout le temps !
```

### En 4 heures
```
📈📈📈📉📈📈 → Plus calme, on voit une tendance
```

### En 1 jour
```
📈📈📈📈📈 → Tendance claire : ça monte !
```

## 🔭 La règle du multi-timeframe

Les pros regardent **plusieurs timeframes** en même temps :

1. **Grand timeframe** (1D/1W) → Pour voir la tendance générale
2. **Moyen timeframe** (4H) → Pour trouver des opportunités
3. **Petit timeframe** (1H) → Pour entrer au bon moment

*C'est comme vérifier la météo de la semaine (grand), du jour (moyen), et de l'heure (petit) avant de sortir !*

## 📊 Quel timeframe choisir ?

| Tu es... | Utilise... |
|----------|-----------|
| Débutant | 4H et 1D |
| Patient | 1D et 1W |
| Disponible | 1H et 4H |
| Pressé (pas recommandé) | 15M et 1H |

## ⚠️ Attention aux petits timeframes

Plus le timeframe est petit :
- Plus il y a de "bruit" (faux signaux)
- Plus c'est stressant
- Plus il faut être rapide

> Les débutants perdent souvent en tradant sur des timeframes trop petits !

## 💡 Conseil de BULL

> Commence par les graphiques 4H et Daily (1D). Tu verras plus clair et tu seras moins stressé ! 

## 🧠 À retenir

- Timeframe = durée de chaque bougie
- Petit timeframe = plus de bruit, plus de stress
- Grand timeframe = vision plus claire
- Regarde plusieurs timeframes pour avoir la vue complète
- Pour débuter : 4H et 1D sont parfaits !
""",
            },
            {
                "id": "lesson_2_4",
                "title": "Support et Résistance",
                "description": "Les murs invisibles du prix",
                "order": 4,
                "xp_reward": 50,
                "content": """
# 🧱 Support et Résistance

Hey champion ! **BULL** ici ! 🐂 Parlons des niveaux clés !

## 🏠 L'analogie de la maison

Imagine une balle qui rebondit dans une pièce :
- Elle touche le **sol** et remonte → C'est le SUPPORT
- Elle touche le **plafond** et redescend → C'est la RÉSISTANCE

## 📉 Le SUPPORT

Un support est un niveau de prix où le marché a tendance à **rebondir vers le haut**.

```
Prix
  │     
  │  \\    /\\    /
  │   \\  /  \\  /
  │    \\/    \\/
  │━━━━━━━━━━━━━━ ← SUPPORT (le sol)
  │
```

**Pourquoi ?**
- À ce niveau, beaucoup d'acheteurs trouvent que c'est "pas cher"
- Ils achètent → le prix remonte

*C'est comme le prix des sneakers en soldes : à -50%, tout le monde achète !*

## 📈 La RÉSISTANCE

Une résistance est un niveau de prix où le marché a tendance à **rebondir vers le bas**.

```
Prix
  │━━━━━━━━━━━━━━ ← RÉSISTANCE (le plafond)
  │    /\\    /\\
  │   /  \\  /  \\
  │  /    \\/    \\
  │
```

**Pourquoi ?**
- À ce niveau, beaucoup de gens trouvent que c'est "assez cher"
- Ils vendent pour prendre leurs profits → le prix redescend

## 🎯 Comment les trouver ?

1. Regarde où le prix a **rebondi plusieurs fois**
2. Plus il y a de rebonds, plus le niveau est **fort**
3. Utilise des lignes horizontales pour les marquer

### Exemple visuel
```
        Résistance forte (3 touches)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      /\\      /\\      /\\
     /  \\    /  \\    /  \\
    /    \\  /    \\  /    \\
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Support fort (3 touches)
```

## 💥 La cassure (Breakout)

Quand le prix **traverse** un support ou une résistance, c'est une CASSURE !

- Cassure de résistance vers le haut → Signal d'achat potentiel 📈
- Cassure de support vers le bas → Signal de vente potentiel 📉

## 🔄 Le retournement de rôle

**Règle magique** : Quand un support est cassé, il devient une résistance (et vice versa) !

```
        Ancienne résistance
━━━━━━━━━━━━━━━━━━━━━━━━━━━
           /
          /  ← Cassure !
━━━━━━━━━━/━━━━━━━━━━━━━━━━
        Devient support !
```

## 💡 Conseil de BULL

> Les supports et résistances sont comme des zones élastiques, pas des lignes exactes. Le prix peut les dépasser un peu avant de rebondir !

## 🧠 À retenir

- Support = niveau où le prix rebondit vers le haut (sol)
- Résistance = niveau où le prix rebondit vers le bas (plafond)
- Plus il y a de touches, plus le niveau est fort
- Une cassure peut être un signal important
- Support cassé devient résistance (et vice versa)
""",
            },
            {
                "id": "lesson_2_5",
                "title": "Figures chartistes simples",
                "description": "Les formes qui prédisent l'avenir",
                "order": 5,
                "xp_reward": 50,
                "content": """
# 🎨 Figures Chartistes Simples

Salut ! **BULL** au rapport ! 🐂 Les graphiques dessinent des formes qui nous parlent !

## 🔮 C'est quoi une figure chartiste ?

Ce sont des **formes** que dessine le prix sur le graphique. Ces formes se répètent et peuvent nous dire ce qui va se passer ensuite !

*C'est comme reconnaître des formes dans les nuages, mais avec les prix !*

## 📐 Le Triangle

Le prix se compresse entre deux lignes qui convergent.

```
\\
 \\    /
  \\  /  
   \\/   → Cassure probable !
   /\\
  /  \\
```

**Ce que ça signifie :**
- Le prix hésite, il prend son élan
- Une cassure va arriver (vers le haut ou le bas)
- Attends la cassure pour agir !

## 🏔️ Double Sommet (Double Top)

Le prix touche deux fois le même niveau haut sans le dépasser.

```
    /\\        /\\
   /  \\      /  \\
  /    \\    /    \\
 /      \\  /      \\
         \\/        \\
                    📉
```

**Ce que ça signifie :**
- Les acheteurs n'arrivent pas à pousser plus haut
- Signal de **baisse** potentielle
- Forme de la lettre "M"

## 🏖️ Double Creux (Double Bottom)

Le prix touche deux fois le même niveau bas sans le casser.

```
                    📈
         /\\        /
 \\      /  \\      /
  \\    /    \\    /
   \\  /      \\  /
    \\/        \\/
```

**Ce que ça signifie :**
- Les vendeurs n'arrivent pas à pousser plus bas
- Signal de **hausse** potentielle
- Forme de la lettre "W"

## 🚩 Le Drapeau (Flag)

Après un fort mouvement, le prix fait une petite pause en forme de drapeau.

```
      │ \\
      │  \\
      │   \\  ← Le "drapeau"
      │  /
  📈  │ / 
     │/
    │
   │
```

**Ce que ça signifie :**
- C'est une pause dans la tendance
- Le mouvement va probablement **continuer** dans la même direction
- "Le marché reprend son souffle"

## 👤 Épaule-Tête-Épaule

Une des figures les plus connues !

```
        Tête
         /\\
        /  \\
  /\\   /    \\   /\\
 /  \\ /      \\ /  \\  Épaules
/    \\/        \\/    \\
━━━━━━━━━━━━━━━━━━━━━━━ ← Ligne de cou
                        📉
```

**Ce que ça signifie :**
- Si la "ligne de cou" casse → probable baisse
- C'est un signal de retournement

## 💡 Conseil de BULL

> Ces figures marchent mieux sur les **grands timeframes** (4H, 1D). Sur les petits timeframes, il y a trop de "fausses" figures !

## ⚠️ Important

Les figures ne sont pas magiques ! Elles donnent des **probabilités**, pas des certitudes.

## 🧠 À retenir

- Les graphiques forment des figures reconnaissables
- Triangle = compression avant cassure
- Double Top (M) = signal de baisse
- Double Bottom (W) = signal de hausse
- Drapeau = pause puis continuation
- Toujours attendre la confirmation !
""",
            },
        ],
        "quiz": {
            "title": "Quiz - Lecture des Graphiques",
            "description": "Montre que tu sais lire les graphiques !",
            "passing_score": 70,
            "questions": [
                {
                    "id": "q2_1",
                    "question": "Que signifie une bougie VERTE ?",
                    "type": "multiple_choice",
                    "options": [
                        "Le prix a baissé pendant cette période",
                        "Le prix a monté pendant cette période",
                        "Le prix n'a pas bougé",
                        "Le marché était fermé"
                    ],
                    "correct_answer": 1,
                    "explanation": "Une bougie verte signifie que le prix de fermeture est plus haut que le prix d'ouverture = le prix a monté ! 🟢📈"
                },
                {
                    "id": "q2_2",
                    "question": "C'est quoi un SUPPORT ?",
                    "type": "multiple_choice",
                    "options": [
                        "Un niveau où le prix a tendance à rebondir vers le bas",
                        "Un niveau où le prix a tendance à rebondir vers le haut",
                        "Le prix le plus haut de tous les temps",
                        "Une application de trading"
                    ],
                    "correct_answer": 1,
                    "explanation": "Un support est comme un 'sol' où le prix rebondit vers le haut. Les acheteurs y trouvent que c'est 'pas cher' !"
                },
                {
                    "id": "q2_3",
                    "question": "Quel timeframe est recommandé pour les débutants ?",
                    "type": "multiple_choice",
                    "options": [
                        "1 minute",
                        "5 minutes",
                        "4 heures et 1 jour",
                        "1 seconde"
                    ],
                    "correct_answer": 2,
                    "explanation": "Les timeframes 4H et 1D sont parfaits pour débuter. Moins de stress et une vision plus claire ! ⏰"
                },
                {
                    "id": "q2_4",
                    "question": "Comment reconnaître une tendance HAUSSIÈRE ?",
                    "type": "multiple_choice",
                    "options": [
                        "Les sommets et creux sont de plus en plus bas",
                        "Les sommets et creux sont de plus en plus hauts",
                        "Le prix ne bouge pas",
                        "Il y a uniquement des bougies rouges"
                    ],
                    "correct_answer": 1,
                    "explanation": "En tendance haussière, le prix fait des sommets ET des creux de plus en plus hauts. Il monte comme un escalier ! 📈"
                },
                {
                    "id": "q2_5",
                    "question": "Que représente un 'Double Bottom' (forme en W) ?",
                    "type": "multiple_choice",
                    "options": [
                        "Un signal de baisse probable",
                        "Un signal de hausse probable",
                        "Le prix va rester stable",
                        "Il faut vendre immédiatement"
                    ],
                    "correct_answer": 1,
                    "explanation": "Le Double Bottom (W) est un signal haussier ! Le prix a essayé de baisser deux fois sans y arriver = les acheteurs reprennent le contrôle 📈"
                },
                {
                    "id": "q2_6",
                    "question": "Que se passe-t-il quand un support est cassé ?",
                    "type": "multiple_choice",
                    "options": [
                        "Il disparaît complètement",
                        "Il devient une résistance",
                        "Il devient plus fort",
                        "Rien de spécial"
                    ],
                    "correct_answer": 1,
                    "explanation": "Quand un support est cassé, il se transforme en résistance ! C'est le retournement de rôle. 🔄"
                },
                {
                    "id": "q2_7",
                    "question": "À quoi servent les mèches (ombres) d'une bougie ?",
                    "type": "multiple_choice",
                    "options": [
                        "À rien, c'est juste décoratif",
                        "À montrer les prix extrêmes (max et min) de la période",
                        "À calculer le volume",
                        "À prédire le futur"
                    ],
                    "correct_answer": 1,
                    "explanation": "Les mèches montrent jusqu'où le prix est allé pendant la période. Longue mèche = beaucoup de bataille entre acheteurs et vendeurs !"
                },
                {
                    "id": "q2_8",
                    "question": "Que signifie 'The trend is your friend' ?",
                    "type": "multiple_choice",
                    "options": [
                        "Les tendances sont tes ennemies",
                        "Il faut toujours trader contre la tendance",
                        "Il est plus facile de trader dans le sens de la tendance",
                        "Les amis sont importants"
                    ],
                    "correct_answer": 2,
                    "explanation": "La tendance est ton amie ! Il est beaucoup plus facile de gagner en suivant la direction générale du marché. Ne te bats pas contre elle ! 🏄"
                },
            ]
        }
    },
    {
        "id": "module_3",
        "title": "Les Indicateurs Techniques",
        "description": "Des outils mathématiques pour t'aider à prendre des décisions",
        "icon": "🔧",
        "color": "violet",
        "order": 3,
        "estimated_time": "60 min",
        "lessons": [
            {
                "id": "lesson_3_1",
                "title": "RSI - Le thermomètre du marché",
                "description": "Mesure si le marché est 'trop chaud' ou 'trop froid'",
                "order": 1,
                "xp_reward": 50,
                "content": """
# 🌡️ RSI - Le Thermomètre du Marché

Salut ! **BULL** ici ! 🐂 On attaque les indicateurs techniques !

## 🤔 C'est quoi le RSI ?

**RSI** = Relative Strength Index (Indice de Force Relative)

C'est comme un thermomètre qui mesure si le marché est "trop chaud" (suracheté) ou "trop froid" (survendu).

## 📊 Comment ça marche ?

Le RSI va de **0 à 100** :

```
100 ─────────────────────
     Zone de SURACHAT    🔥 Trop chaud !
 70 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
     Zone NEUTRE         😎 Normal
 30 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
     Zone de SURVENTE    🥶 Trop froid !
  0 ─────────────────────
```

## 🔥 RSI au-dessus de 70 = SURACHAT

Quand le RSI dépasse 70 :
- Le marché est "trop chaud"
- Beaucoup de gens ont déjà acheté
- Le prix pourrait bientôt **baisser**

*C'est comme une file d'attente pour un concert : si tout le monde est déjà entré, il n'y a plus de nouveaux acheteurs !*

## 🥶 RSI en-dessous de 30 = SURVENTE

Quand le RSI descend sous 30 :
- Le marché est "trop froid"
- Beaucoup de gens ont déjà vendu
- Le prix pourrait bientôt **monter**

*C'est comme les soldes : quand tout est à -70%, les chasseurs de bonnes affaires arrivent !*

## 📈 Comment l'utiliser ?

### Signal d'ACHAT potentiel
1. RSI descend sous 30 (survente)
2. Puis RSI remonte au-dessus de 30
3. → Possible opportunité d'achat 🟢

### Signal de VENTE potentiel
1. RSI monte au-dessus de 70 (surachat)
2. Puis RSI redescend sous 70
3. → Possible opportunité de vente 🔴

## ⚠️ Attention aux faux signaux !

Le RSI peut rester en surachat ou survente **longtemps** pendant les fortes tendances !

En tendance haussière forte :
- Le RSI peut rester au-dessus de 70 pendant des semaines
- Ne vends pas juste parce que le RSI est haut !

## 🎯 Exemple concret

```
Bitcoin RSI = 25 (survente)
→ Possible rebond à venir !

Bitcoin RSI = 80 (surachat)
→ Prudence, possible correction !
```

## 💡 Conseil de BULL

> Le RSI est un **assistant**, pas un patron ! Combine-le toujours avec d'autres analyses. Un RSI en survente dans une tendance baissière peut rester bas longtemps !

## 🧠 À retenir

- RSI mesure la force du marché (0 à 100)
- RSI > 70 = Surachat (attention à la baisse)
- RSI < 30 = Survente (attention à la hausse)
- Attends toujours que le RSI SORTE de la zone extrême
- Ne l'utilise jamais seul !
""",
            },
            {
                "id": "lesson_3_2",
                "title": "Moyennes Mobiles",
                "description": "Lisser le bruit pour voir la tendance",
                "order": 2,
                "xp_reward": 50,
                "content": """
# 📈 Les Moyennes Mobiles

Hey ! C'est **BULL** ! 🐂 Parlons des moyennes mobiles !

## 🤔 C'est quoi une Moyenne Mobile ?

Une moyenne mobile (MA = Moving Average) calcule le **prix moyen** sur une période donnée.

*Imagine tes notes à l'école : une mauvaise note ne change pas ta moyenne générale d'un coup. C'est pareil avec les prix !*

## 📊 Exemple simple

Prix des 5 derniers jours : 100, 102, 98, 104, 106

**Moyenne Mobile 5 jours** = (100+102+98+104+106) / 5 = **102**

Cette moyenne "lisse" les variations pour montrer la tendance générale.

## 📏 Les MA les plus utilisées

| MA | Utilisation |
|----|-------------|
| MA 20 | Court terme, réagit vite |
| MA 50 | Moyen terme, équilibré |
| MA 200 | Long terme, tendance de fond |

## 📈 Lire les Moyennes Mobiles

### Le prix par rapport à la MA

```
Prix au-dessus de la MA → Tendance haussière 📈
Prix en-dessous de la MA → Tendance baissière 📉
```

### L'ordre des MA

```
Configuration BULLISH (haussière) :
Prix > MA20 > MA50 > MA200
🟢 Tout est bien aligné pour monter !

Configuration BEARISH (baissière) :
Prix < MA20 < MA50 < MA200
🔴 Tout est aligné pour descendre !
```

## ✨ Les croisements (Golden Cross & Death Cross)

### 🌟 Golden Cross (Croix Dorée)
Quand la MA courte (50) **croise au-dessus** de la MA longue (200)
→ Signal HAUSSIER fort !

```
        MA50
          \\ ↗️
           X  ← Golden Cross !
          / 
        MA200
```

### 💀 Death Cross (Croix de la Mort)
Quand la MA courte (50) **croise en-dessous** de la MA longue (200)
→ Signal BAISSIER fort !

```
        MA200
          \\ 
           X  ← Death Cross !
          / ↘️
        MA50
```

## 🛡️ La MA comme support/résistance

Les moyennes mobiles agissent souvent comme des niveaux de support ou résistance !

- En tendance haussière : le prix rebondit souvent sur la MA 20 ou 50
- En tendance baissière : le prix est rejeté par ces mêmes MA

## 💡 Conseil de BULL

> La MA 200 en journalier (Daily) est la plus importante ! Si le prix est au-dessus, le marché est globalement haussier. En-dessous, attention danger !

## ⚠️ Limites des MA

- Elles sont en **retard** (elles utilisent les prix passés)
- En marché latéral, elles donnent de faux signaux
- Ne pas utiliser seules !

## 🧠 À retenir

- MA = moyenne des prix sur X périodes
- Prix > MA = tendance haussière
- Prix < MA = tendance baissière
- Golden Cross = signal d'achat fort
- Death Cross = signal de vente fort
- MA 200 daily = le niveau clé !
""",
            },
            {
                "id": "lesson_3_3",
                "title": "MACD - Le détecteur de momentum",
                "description": "Voir la force et la direction du mouvement",
                "order": 3,
                "xp_reward": 50,
                "content": """
# 🚀 MACD - Le Détecteur de Momentum

Salut champion ! **BULL** au rapport ! 🐂 Le MACD, c'est puissant !

## 🤔 C'est quoi le MACD ?

**MACD** = Moving Average Convergence Divergence
(Convergence et Divergence des Moyennes Mobiles)

Le MACD mesure le **momentum** (la force et la vitesse du mouvement).

*C'est comme le compteur de vitesse d'une voiture, mais pour les prix !*

## 📊 Les composants du MACD

Le MACD a 3 éléments :

1. **Ligne MACD** (bleue) - La différence entre 2 moyennes mobiles
2. **Ligne Signal** (orange) - Une moyenne de la ligne MACD
3. **Histogramme** (barres) - La différence entre MACD et Signal

```
Ligne MACD ───────────
Ligne Signal ─ ─ ─ ─ ─
     █
   █ █ █
 █ █ █ █ █
───────────────── Ligne 0
         █ █ █
           █ █
             █
  Histogramme
```

## 📈 Comment lire le MACD ?

### Position par rapport à 0

- **MACD au-dessus de 0** → Momentum haussier 📈
- **MACD en-dessous de 0** → Momentum baissier 📉

### Les croisements

#### 🟢 Signal d'ACHAT
Quand la ligne MACD croise **au-dessus** de la ligne Signal
```
   MACD
      ↗️ X
       Signal
```

#### 🔴 Signal de VENTE
Quand la ligne MACD croise **en-dessous** de la ligne Signal
```
       Signal
      ↘️ X
   MACD
```

## 📊 L'histogramme

L'histogramme montre la force du momentum :

- **Barres vertes qui grandissent** → Le momentum haussier augmente 💪
- **Barres vertes qui rétrécissent** → Le momentum haussier faiblit 😓
- **Barres rouges qui grandissent** → Le momentum baissier augmente ⚠️
- **Barres rouges qui rétrécissent** → Le momentum baissier faiblit 🤔

## 🎯 Stratégie simple avec le MACD

1. **Attends** que le MACD soit en-dessous de 0
2. **Cherche** un croisement haussier (MACD passe au-dessus du Signal)
3. **Confirme** avec la tendance générale
4. **Entre** en position

## 💡 Divergences (niveau avancé)

Une **divergence**, c'est quand le prix et le MACD ne vont pas dans le même sens :

### Divergence haussière
- Le prix fait un nouveau plus bas 📉
- Mais le MACD fait un plus haut 📈
- → Signal de retournement haussier possible !

### Divergence baissière
- Le prix fait un nouveau plus haut 📈
- Mais le MACD fait un plus bas 📉
- → Signal de retournement baissier possible !

## 💡 Conseil de BULL

> Le MACD marche mieux sur les timeframes plus longs (4H, Daily). Sur 1 minute, il y a trop de bruit !

## 🧠 À retenir

- MACD mesure le momentum (force du mouvement)
- MACD > 0 = momentum haussier
- MACD < 0 = momentum baissier
- Croisement haussier = signal d'achat potentiel
- Croisement baissier = signal de vente potentiel
- Histogramme = visualise la force du momentum
""",
            },
            {
                "id": "lesson_3_4",
                "title": "Bandes de Bollinger",
                "description": "Mesurer la volatilité du marché",
                "order": 4,
                "xp_reward": 50,
                "content": """
# 📐 Bandes de Bollinger

Yo ! **BULL** ici ! 🐂 Parlons de volatilité !

## 🤔 C'est quoi les Bandes de Bollinger ?

Les Bandes de Bollinger mesurent la **volatilité** (à quel point les prix bougent).

*Imagine un élastique autour du prix. Quand il s'étire trop, il finit par revenir au centre !*

## 📊 Les 3 lignes

```
════════════════════════ Bande HAUTE
        /\\    /\\
       /  \\  /  \\
━━━━━━━━━━━━━━━━━━━━━━━━ Moyenne (MA 20)
     /      \\/
    /        
════════════════════════ Bande BASSE
```

1. **Bande Haute** - Limite supérieure
2. **Ligne du Milieu** - Moyenne Mobile 20 périodes
3. **Bande Basse** - Limite inférieure

## 📏 Ce que les bandes nous disent

### Bandes qui s'ÉCARTENT
- La volatilité **augmente**
- Le marché bouge beaucoup
- Fort mouvement en cours !

### Bandes qui se RESSERRENT (Squeeze)
- La volatilité **diminue**
- Le marché se "compresse"
- ⚠️ Un gros mouvement arrive bientôt !

```
Le "Squeeze" :
════════════════════
     ━━━━━━━━━━    ← Bandes serrées
════════════════════
        ↓
   EXPLOSION ! 💥
```

## 🎯 Utilisation pratique

### Prix touche la bande HAUTE
- Le marché est peut-être en surachat
- Possible retour vers le milieu
- ⚠️ Attention si tu veux acheter !

### Prix touche la bande BASSE
- Le marché est peut-être en survente
- Possible rebond vers le milieu
- 🤔 Possible opportunité d'achat ?

### Prix reste DANS les bandes
- Comportement normal
- Le prix se promène entre les deux limites

## 📈 La stratégie du "Mean Reversion"

Le prix a tendance à **revenir vers la moyenne** (la ligne du milieu).

1. Prix touche la bande basse
2. Attends un signal de retournement (bougie verte)
3. Objectif = retour vers la ligne du milieu

*Mais attention ! En forte tendance, le prix peut "surfer" sur une bande longtemps !*

## 🚀 "Walking the Band"

En forte tendance, le prix peut **longer** une bande :

```
Tendance haussière forte :
════════════════════════════════════════
     /  /  /  /  /  /  /  → Prix "marche" sur la bande haute !
━━━━━━━━━━━━━━━━━━━━━━━━━
════════════════════════════════════════
```

Dans ce cas, NE PAS vendre juste parce que le prix touche la bande haute !

## 💡 Conseil de BULL

> Quand les bandes sont TRÈS serrées (squeeze), prépare-toi ! Un gros mouvement arrive. Mais attends de voir dans quelle direction avant d'agir !

## 🧠 À retenir

- Bollinger = mesure la volatilité
- Bandes écartées = forte volatilité
- Bandes serrées (squeeze) = explosion à venir
- Prix touche bande haute = possible surachat
- Prix touche bande basse = possible survente
- En forte tendance, le prix peut longer une bande
""",
            },
            {
                "id": "lesson_3_5",
                "title": "Combiner les indicateurs",
                "description": "La puissance de la convergence",
                "order": 5,
                "xp_reward": 50,
                "content": """
# 🎯 Combiner les Indicateurs

Hey ! **BULL** ici ! 🐂 La vraie force vient de la combinaison !

## 🤔 Pourquoi combiner ?

Un seul indicateur peut donner des **faux signaux**. Mais quand plusieurs indicateurs disent la même chose, la probabilité de succès augmente !

*C'est comme demander l'avis de plusieurs experts avant de prendre une décision importante.*

## ⚠️ La règle d'or

> **Ne te base JAMAIS sur un seul indicateur !**

## 🎮 Le combo parfait pour débutant

### Les 3 mousquetaires :

1. **RSI** - Mesure si c'est suracheté/survendu
2. **Moyennes Mobiles** - Montre la tendance
3. **Support/Résistance** - Donne les niveaux clés

## ✅ Exemple de signal FORT d'achat

Vérifie que tous ces éléments sont réunis :

| Indicateur | Condition | ✓ |
|------------|-----------|---|
| Tendance | Prix > MA 200 (tendance haussière) | ✓ |
| RSI | Vient de sortir de survente (< 30 puis > 30) | ✓ |
| Support | Prix rebondit sur un support | ✓ |
| Bougies | Bougie verte de retournement | ✓ |

**Si tout est vert → Signal FORT ! 💪**

## ❌ Exemple de signal FAIBLE

| Indicateur | Condition | État |
|------------|-----------|------|
| Tendance | Prix < MA 200 (tendance baissière) | ❌ |
| RSI | En survente | ✓ |
| Support | Aucun support proche | ❌ |

**Seulement 1 sur 3 → Signal FAIBLE, évite !**

## 📊 La checklist avant de trader

Avant chaque trade, vérifie :

### 1. La Tendance (MA 200)
- [ ] Prix au-dessus ? → OK pour acheter
- [ ] Prix en-dessous ? → Prudence !

### 2. Le Momentum (RSI ou MACD)
- [ ] RSI en zone d'achat (30-50) ?
- [ ] MACD qui croise à la hausse ?

### 3. Les Niveaux (Support/Résistance)
- [ ] Proche d'un support pour acheter ?
- [ ] Loin de la résistance ?

### 4. La Volatilité (Bollinger)
- [ ] Squeeze = attendre la direction
- [ ] Prix sur bande basse = opportunité ?

## 📈 Exemple concret complet

```
Bitcoin - Analyse complète

✅ MA 200 : Prix au-dessus → Tendance haussière
✅ RSI : 35, sortie de survente → Bon timing
✅ Support : Prix sur support des $85,000
✅ Bollinger : Prix sur bande basse → Possible rebond
✅ MACD : Croisement haussier → Momentum positif

VERDICT : 5/5 → Signal TRÈS FORT ! 🚀
```

## 💡 Conseil de BULL

> Cherche la **confluence** ! C'est quand plusieurs facteurs pointent vers la même direction. Plus il y a de confluence, plus le signal est fiable !

## 🧠 À retenir

- Ne jamais utiliser UN SEUL indicateur
- Cherche la confluence (plusieurs signaux alignés)
- Tendance + Momentum + Niveaux = combo gagnant
- Minimum 3 confirmations avant de trader
- Si tu doutes, n'entre pas !
""",
            },
        ],
        "quiz": {
            "title": "Quiz - Les Indicateurs Techniques",
            "description": "Montre que tu maîtrises les indicateurs !",
            "passing_score": 70,
            "questions": [
                {
                    "id": "q3_1",
                    "question": "Le RSI est à 25. Que signifie cette valeur ?",
                    "type": "multiple_choice",
                    "options": [
                        "Le marché est en surachat (trop chaud)",
                        "Le marché est en survente (trop froid)",
                        "Le marché est parfaitement équilibré",
                        "Le RSI est cassé"
                    ],
                    "correct_answer": 1,
                    "explanation": "Un RSI sous 30 signifie que le marché est en survente (trop froid). Possible rebond à venir ! 🥶"
                },
                {
                    "id": "q3_2",
                    "question": "C'est quoi un 'Golden Cross' ?",
                    "type": "multiple_choice",
                    "options": [
                        "Quand la MA 50 passe sous la MA 200",
                        "Quand la MA 50 passe au-dessus de la MA 200",
                        "Quand le RSI atteint 100",
                        "Quand tu gagnes de l'or"
                    ],
                    "correct_answer": 1,
                    "explanation": "Le Golden Cross arrive quand la MA 50 croise au-dessus de la MA 200. C'est un signal haussier fort ! 🌟"
                },
                {
                    "id": "q3_3",
                    "question": "Que mesure le MACD ?",
                    "type": "multiple_choice",
                    "options": [
                        "Le prix exact de demain",
                        "Le momentum (force du mouvement)",
                        "Le nombre d'acheteurs",
                        "La couleur des bougies"
                    ],
                    "correct_answer": 1,
                    "explanation": "Le MACD mesure le momentum, c'est-à-dire la force et la vitesse du mouvement des prix ! 🚀"
                },
                {
                    "id": "q3_4",
                    "question": "Quand les Bandes de Bollinger se resserrent (squeeze), que se passe-t-il généralement ensuite ?",
                    "type": "multiple_choice",
                    "options": [
                        "Le prix reste calme pour toujours",
                        "Un gros mouvement va arriver",
                        "Les bandes disparaissent",
                        "Rien de spécial"
                    ],
                    "correct_answer": 1,
                    "explanation": "Le squeeze (bandes serrées) est souvent suivi d'une explosion ! La volatilité va augmenter fortement. 💥"
                },
                {
                    "id": "q3_5",
                    "question": "Combien d'indicateurs faut-il utiliser au minimum pour avoir un bon signal ?",
                    "type": "multiple_choice",
                    "options": [
                        "1 seul suffit",
                        "Au moins 2-3 qui convergent",
                        "10 minimum",
                        "Aucun, le feeling suffit"
                    ],
                    "correct_answer": 1,
                    "explanation": "Il faut au moins 2-3 indicateurs qui pointent dans la même direction. C'est la confluence ! 🎯"
                },
                {
                    "id": "q3_6",
                    "question": "Que signifie un prix au-dessus de la MA 200 ?",
                    "type": "multiple_choice",
                    "options": [
                        "Le marché est en tendance baissière",
                        "Le marché est en tendance haussière",
                        "Le marché est fermé",
                        "La MA 200 est cassée"
                    ],
                    "correct_answer": 1,
                    "explanation": "Quand le prix est au-dessus de la MA 200, le marché est globalement haussier. C'est le niveau le plus important ! 📈"
                },
                {
                    "id": "q3_7",
                    "question": "L'histogramme du MACD montre des barres vertes qui grandissent. Que cela signifie-t-il ?",
                    "type": "multiple_choice",
                    "options": [
                        "Le momentum baissier augmente",
                        "Le momentum haussier augmente",
                        "Le marché est stable",
                        "Il faut vendre immédiatement"
                    ],
                    "correct_answer": 1,
                    "explanation": "Des barres vertes qui grandissent = le momentum haussier AUGMENTE. Le mouvement devient plus fort ! 💪"
                },
                {
                    "id": "q3_8",
                    "question": "Quand le prix touche la bande basse de Bollinger, que peut-il se passer ?",
                    "type": "multiple_choice",
                    "options": [
                        "Le prix explose toujours vers le haut",
                        "Le prix peut rebondir vers la moyenne OU continuer si la tendance est forte",
                        "Les bandes se cassent",
                        "Rien du tout"
                    ],
                    "correct_answer": 1,
                    "explanation": "Le prix peut rebondir vers le milieu, mais en forte tendance baissière, il peut aussi 'surfer' sur la bande basse. Context is key ! 🏄"
                },
            ]
        }
    },
]

# On continue avec les modules 4, 5 et 6 dans la suite...
