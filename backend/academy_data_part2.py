"""
BULL SAGE ACADEMY - Suite des modules (4, 5, 6)
Gestion du risque, Psychologie, Stratégies
"""

ACADEMY_MODULES_PART2 = [
    {
        "id": "module_4",
        "title": "Gestion du Risque",
        "description": "Protège ton capital ! C'est LA compétence la plus importante.",
        "icon": "🛡️",
        "color": "rose",
        "order": 4,
        "estimated_time": "45 min",
        "lessons": [
            {
                "id": "lesson_4_1",
                "title": "Le Stop-Loss - Ton parachute",
                "description": "Ne jamais perdre plus que prévu",
                "order": 1,
                "xp_reward": 50,
                "content": """
# 🪂 Le Stop-Loss - Ton Parachute

Salut ! **BULL** ici ! 🐂 Aujourd'hui, on parle de ta protection !

## 🤔 C'est quoi un Stop-Loss ?

Un **Stop-Loss** (SL) est un ordre qui vend automatiquement si le prix descend trop.

*C'est comme un parachute : tu espères ne jamais l'utiliser, mais tu es content de l'avoir quand tu en as besoin !*

## 🛡️ Pourquoi c'est SUPER important ?

### Sans Stop-Loss :
```
Tu achètes Bitcoin à $90,000
Le prix tombe à $70,000
Tu perds $20,000 😱
Tu paniques et vends au pire moment
```

### Avec Stop-Loss :
```
Tu achètes Bitcoin à $90,000
Tu places un SL à $87,000 (-3.3%)
Le prix tombe → Tu es vendu à $87,000
Tu perds $3,000 (maîtrisé ✅)
Tu gardes ton capital pour la suite !
```

## 📍 Où placer son Stop-Loss ?

### ❌ Mauvais placements
- Trop serré (1%) → Tu te fais sortir pour rien
- Sur un chiffre rond ($90,000) → Tout le monde le fait !
- Au hasard → Pas de logique

### ✅ Bons placements
- Sous un support important
- Sous la dernière mèche basse
- À une distance qui "laisse respirer" le trade

## 📏 Exemple de placement

```
Prix d'achat : $90,000
Support : $87,500
Dernière mèche basse : $87,000

Stop-Loss recommandé : $86,500
(Un peu sous le support pour éviter les faux-outs)
```

## 🚫 La règle d'or

> **JAMAIS trader sans Stop-Loss !**

C'est comme conduire sans ceinture. Tu peux faire 1000 trajets sans accident, mais le jour où ça arrive...

## 💰 Combien risquer par trade ?

La règle du **1-2%** :

- Ne jamais risquer plus de 1-2% de ton capital par trade
- Si tu as 1000€ → risque max = 10-20€ par trade
- Ça te permet de survivre à une série de pertes

## 📊 Calcul simple

```
Capital : 1000€
Risque max : 2% = 20€

Si ton SL est à 4% du prix d'entrée :
Position max = 20€ / 4% = 500€
```

## 💡 Types de Stop-Loss

### Stop-Loss FIXE
- Tu le places et tu ne le touches plus
- Simple et efficace

### Stop-Loss SUIVEUR (Trailing Stop)
- Il suit le prix quand il monte
- Se déclenche si le prix redescend
- Protège tes gains !

## 💡 Conseil de BULL

> Une fois ton Stop-Loss placé, NE LE DÉPLACE JAMAIS vers le bas ! C'est la première erreur du débutant. Le déplacer vers le haut pour protéger des gains, oui. Vers le bas, JAMAIS !

## 🧠 À retenir

- Stop-Loss = vente automatique si ça baisse trop
- TOUJOURS en placer un !
- Le placer sous un support, pas au hasard
- Risquer max 1-2% du capital par trade
- Ne jamais le déplacer vers le bas
""",
            },
            {
                "id": "lesson_4_2",
                "title": "Le Take-Profit - Prendre ses gains",
                "description": "Savoir quand encaisser la victoire",
                "order": 2,
                "xp_reward": 50,
                "content": """
# 🎯 Le Take-Profit - Prendre ses Gains

Hey champion ! **BULL** au rapport ! 🐂 Parlons de prendre tes gains !

## 🤔 C'est quoi un Take-Profit ?

Un **Take-Profit** (TP) est un ordre qui vend automatiquement quand tu atteins ton objectif de gain.

*C'est comme décider AVANT le match que tu rentres chez toi si tu mènes 3-0 !*

## 💡 Pourquoi c'est important ?

### Sans Take-Profit :
```
Tu achètes à $90,000
Le prix monte à $100,000 (+11%) 🎉
Tu veux plus... tu gardes
Le prix redescend à $85,000
Tu es en perte 😭
```

### Avec Take-Profit :
```
Tu achètes à $90,000
TP1 à $95,000 (+5.5%)
Le prix atteint $95,000 → Vendu !
Tu encaisses ton gain ✅
```

## 📍 Stratégie des TP multiples

Beaucoup de traders utilisent **plusieurs Take-Profit** :

```
Achat : $90,000

TP1 : $93,000 → Tu vends 50% (gains sécurisés)
TP2 : $97,000 → Tu vends 30% (plus de gains)
TP3 : $102,000 → Tu vends les 20% restants (objectif ambitieux)
```

**Avantage** : Tu sécurises des gains tout en gardant du potentiel !

## 📏 Où placer ses Take-Profit ?

### Les meilleurs endroits :
- Juste AVANT une résistance importante
- Aux niveaux de Fibonacci (78.6%, 100%, 127.2%)
- À un ratio Risk/Reward intéressant (2:1, 3:1)

### Exemple :
```
Achat : $90,000
Stop-Loss : $87,000 (risque $3,000)

TP1 : $96,000 (gain $6,000) → Ratio 2:1 ✅
TP2 : $99,000 (gain $9,000) → Ratio 3:1 ✅
```

## ⚖️ Le Ratio Risk/Reward (R:R)

C'est le rapport entre ce que tu peux gagner et ce que tu risques.

```
Risque : $100 (si SL touché)
Gain potentiel : $300 (si TP touché)

Ratio = 300/100 = 3:1
```

### Règle simple :
> Ne prends que des trades avec un ratio **minimum de 2:1**

Avec 2:1, tu peux perdre 50% de tes trades et rester rentable !

## 💡 Conseil de BULL

> Fixe TOUJOURS ton Take-Profit AVANT d'entrer en position. Une fois dans le trade, tes émotions vont te jouer des tours !

## 🧮 La magie du ratio R:R

Avec un ratio 3:1 et 40% de trades gagnants :

```
10 trades à 100€ de risque chacun
4 gagnants × 300€ = +1200€
6 perdants × 100€ = -600€
Profit net = +600€ 🎉
```

**Tu gagnes même en perdant plus souvent que tu ne gagnes !**

## 🧠 À retenir

- Take-Profit = vente automatique quand tu gagnes assez
- Utilise plusieurs TP pour sécuriser progressivement
- Place-les avant les résistances
- Minimum ratio 2:1 (risquer 1 pour gagner 2)
- Décide AVANT d'entrer, pas pendant !
""",
            },
            {
                "id": "lesson_4_3",
                "title": "La règle du 1-2%",
                "description": "Protéger ton capital comme un pro",
                "order": 3,
                "xp_reward": 50,
                "content": """
# 💰 La Règle du 1-2%

Salut ! **BULL** ici ! 🐂 LA règle que tous les pros respectent !

## 🎯 La règle simple

> **Ne jamais risquer plus de 1-2% de ton capital total sur UN SEUL trade.**

*C'est comme au casino : ne mise jamais plus de 2% de ton argent sur une seule main !*

## 🤔 Pourquoi cette règle ?

### Avec 10% de risque par trade :
```
Capital : 1000€
Tu perds 5 trades d'affilée (ça arrive !)
1000 → 900 → 810 → 729 → 656 → 590€
Tu as perdu 41% de ton capital 😱
```

### Avec 2% de risque par trade :
```
Capital : 1000€
Tu perds 5 trades d'affilée
1000 → 980 → 960 → 941 → 922 → 903€
Tu as perdu seulement 9.7% 💪
```

## 📊 Calcul pratique

### Étape 1 : Calcule ton risque max
```
Capital : 5000€
Risque 2% = 5000 × 0.02 = 100€ max par trade
```

### Étape 2 : Calcule ta taille de position
```
Prix d'entrée : 1000€
Stop-Loss : 950€ (5% sous l'entrée)
Risque par unité : 50€

Position max = 100€ / 50€ = 2 unités max
```

## 📈 Adaptation selon le niveau

| Niveau | Risque recommandé |
|--------|-------------------|
| Débutant | 0.5-1% |
| Intermédiaire | 1-2% |
| Avancé | 2-3% max |

## 🛡️ Pourquoi même les pros l'utilisent

Les meilleurs traders du monde risquent rarement plus de 1-2% par trade. Pourquoi ?

1. **Survie** - Tu peux perdre 50 trades d'affilée et garder ton capital
2. **Émotions** - Petites pertes = pas de panique
3. **Récupération** - Facile de récupérer 2%, dur de récupérer 50%

## 📉 La difficulté de la récupération

| Perte | Gain nécessaire pour récupérer |
|-------|-------------------------------|
| -10% | +11% |
| -25% | +33% |
| -50% | +100% 😱 |
| -75% | +300% 😵 |

*Plus tu perds, plus c'est dur de revenir !*

## 💡 Conseil de BULL

> Commence encore plus petit ! 0.5% par trade quand tu débutes. Tu feras des erreurs, autant qu'elles ne te coûtent pas cher !

## 🧮 Template de calcul

Remplis à chaque trade :
```
Mon capital total : ____€
Risque max (2%) : ____€
Mon SL est à ___% du prix
Ma position max : ____€
```

## 🧠 À retenir

- Maximum 1-2% du capital par trade
- Cette règle te permet de survivre aux mauvaises périodes
- Plus facile de récupérer des petites pertes
- Les pros utilisent cette règle
- Calcule AVANT d'entrer en position !
""",
            },
            {
                "id": "lesson_4_4",
                "title": "Position Sizing",
                "description": "Calculer la bonne taille de position",
                "order": 4,
                "xp_reward": 50,
                "content": """
# 📐 Position Sizing

Hey ! **BULL** au rapport ! 🐂 Calculons ensemble !

## 🤔 C'est quoi le Position Sizing ?

Le Position Sizing, c'est **calculer combien investir** sur chaque trade pour respecter ta règle de risque.

*C'est comme choisir la taille de tes paris au poker : ni trop gros (dangereux), ni trop petit (pas intéressant).*

## 📊 La formule magique

```
Taille de position = Risque en € / (% de distance au Stop-Loss)
```

## 🎯 Exemple complet

### Données :
- Capital : **1000€**
- Risque max : **2%** = 20€
- Prix d'entrée Bitcoin : **$90,000**
- Stop-Loss : **$87,300** (3% sous l'entrée)

### Calcul :
```
Distance au SL = 3%
Risque accepté = 20€

Taille de position = 20€ / 0.03 = 666€
```

**Tu peux investir maximum 666€ sur ce trade !**

### Vérification :
```
Si le SL est touché :
666€ × 3% = 20€ de perte ✅
```

## 📋 Tableau de référence rapide

| Distance SL | Position pour 20€ de risque |
|------------|----------------------------|
| 2% | 1000€ |
| 3% | 666€ |
| 5% | 400€ |
| 10% | 200€ |

*Plus ton SL est loin, plus ta position doit être petite !*

## 🎮 Exercice pratique

### Situation :
- Capital : 2000€
- Risque : 1.5% = 30€
- Tu veux acheter Ethereum à $3,000
- Ton SL sera à $2,850 (5% sous)

### Calcul :
```
Taille position = 30€ / 0.05 = 600€

Tu peux acheter pour 600€ d'Ethereum
= 600 / 3000 = 0.2 ETH
```

## ⚠️ Erreurs courantes

### ❌ Erreur 1 : Position trop grande
"Je suis sûr de moi, je mets 50% de mon capital !"
→ Une mauvaise trade = catastrophe

### ❌ Erreur 2 : Ignorer le calcul
"Bof, je mets 500€, ça ira"
→ Tu ne maîtrises pas ton risque

### ❌ Erreur 3 : Oublier les frais
N'oublie pas les frais de transaction dans ton calcul !

## 💡 Conseil de BULL

> Fais ce calcul SYSTÉMATIQUEMENT avant chaque trade. Avec le temps, ça deviendra automatique. Mais au début, écris-le !

## 📱 Astuce : Le calculateur

Crée-toi un petit tableau Excel ou utilise une app :
1. Entre ton capital
2. Entre ton % de risque
3. Entre la distance du SL
4. → Position calculée automatiquement !

## 🧠 À retenir

- Calcule TOUJOURS ta taille de position avant de trader
- Formule : Risque € / Distance SL %
- Plus le SL est loin, plus la position est petite
- Cette discipline te sauvera sur le long terme
- Fais-en une habitude !
""",
            },
            {
                "id": "lesson_4_5",
                "title": "Plan de Trading",
                "description": "Ton guide avant chaque trade",
                "order": 5,
                "xp_reward": 50,
                "content": """
# 📋 Le Plan de Trading

Salut champion ! **BULL** ici ! 🐂 Créons ton plan !

## 🤔 C'est quoi un Plan de Trading ?

Un plan de trading, c'est un **document écrit** qui définit toutes tes règles AVANT de trader.

*C'est comme la recette d'un chef : sans elle, impossible de reproduire le plat parfaitement !*

## 🎯 Pourquoi c'est essentiel ?

### Sans plan :
- Tu trades sur l'émotion 😰
- Tu changes d'avis en cours de route
- Tu ne sais pas pourquoi tu gagnes ou perds
- Résultat : Inconsistant

### Avec plan :
- Tu suis des règles claires ✅
- Tu élimines l'émotion
- Tu peux analyser ce qui marche
- Résultat : Progression !

## 📝 Les éléments d'un bon plan

### 1. Tes règles de marché
```
- Je ne trade que les cryptos majeures (BTC, ETH, SOL)
- Je trade uniquement en tendance haussière (> MA200)
- Timeframe principal : 4H
```

### 2. Tes critères d'entrée
```
Pour acheter, je dois avoir :
✓ Prix > MA200
✓ RSI < 50 (pas en surachat)
✓ Rebond sur support confirmé
✓ 3 confirmations minimum
```

### 3. Ta gestion du risque
```
- Risque max par trade : 2%
- Pas plus de 3 trades ouverts
- Pas de trading pendant les news majeures
```

### 4. Tes règles de sortie
```
- SL : Toujours sous le support
- TP1 : 50% à ratio 2:1
- TP2 : 30% à ratio 3:1
- TP3 : 20% trailing stop
```

### 5. Tes horaires
```
- J'analyse le marché : 9h et 18h
- Je ne trade pas après 22h (fatigue)
- Week-end : Analyse seulement, pas de trade
```

## 📊 Template de Plan

```
=== MON PLAN DE TRADING ===

MARCHÉS :
[ ] Crypto : BTC, ETH, SOL
[ ] Timeframe : 4H / Daily

ENTRÉES :
[ ] Tendance : Prix > MA50
[ ] Indicateur : RSI sort de survente
[ ] Niveau : Rebond sur support
[ ] Confirmation : Bougie verte

RISQUE :
[ ] Max par trade : 1%
[ ] Trades simultanés max : 2
[ ] Perte journalière max : 3%

SORTIES :
[ ] SL : Sous dernier creux
[ ] TP1 : Ratio 2:1 (50%)
[ ] TP2 : Résistance (50%)

DISCIPLINE :
[ ] Pas de trade sans plan
[ ] Pas de trade en colère
[ ] Journal de trading à jour
```

## ⚠️ Les règles non négociables

1. **JAMAIS de trade sans SL**
2. **JAMAIS plus de 2% de risque**
3. **JAMAIS de "revenge trading"** (trader pour récupérer)
4. **JAMAIS de FOMO** (acheter parce que ça monte)

## 💡 Conseil de BULL

> Imprime ton plan et affiche-le à côté de ton écran. Avant chaque trade, vérifie que TOUTES les conditions sont remplies. Si une seule manque → Pas de trade !

## 📈 Évalue ton plan

Chaque semaine, revois :
- Combien de trades ont respecté le plan ?
- Résultat des trades "dans le plan" vs "hors plan" ?
- Ajustements nécessaires ?

## 🧠 À retenir

- Un plan écrit élimine les émotions
- Définis tes critères d'entrée et sortie
- Respecte TOUJOURS tes règles
- Évalue et améliore régulièrement
- Le plan est ton meilleur ami !
""",
            },
        ],
        "quiz": {
            "title": "Quiz - Gestion du Risque",
            "description": "Prouve que tu sais protéger ton capital !",
            "passing_score": 70,
            "questions": [
                {
                    "id": "q4_1",
                    "question": "C'est quoi un Stop-Loss ?",
                    "type": "multiple_choice",
                    "options": [
                        "Un ordre pour acheter plus bas",
                        "Un ordre qui vend automatiquement si le prix baisse trop",
                        "Une technique pour gagner plus",
                        "Un type de crypto"
                    ],
                    "correct_answer": 1,
                    "explanation": "Le Stop-Loss te protège en vendant automatiquement si le prix baisse trop. C'est ton parachute ! 🪂"
                },
                {
                    "id": "q4_2",
                    "question": "Selon la règle du 1-2%, combien peux-tu risquer sur un trade si tu as 2000€ ?",
                    "type": "multiple_choice",
                    "options": [
                        "200€",
                        "20-40€",
                        "500€",
                        "Tout"
                    ],
                    "correct_answer": 1,
                    "explanation": "2% de 2000€ = 40€ max par trade. 1% = 20€. Tu protèges ainsi ton capital ! 💰"
                },
                {
                    "id": "q4_3",
                    "question": "C'est quoi un bon ratio Risk/Reward minimum ?",
                    "type": "multiple_choice",
                    "options": [
                        "1:1",
                        "1:2 ou mieux",
                        "5:1",
                        "Le ratio n'est pas important"
                    ],
                    "correct_answer": 1,
                    "explanation": "Minimum 1:2 ! Risquer 1 pour gagner 2. Comme ça, même avec 50% de trades perdants, tu gagnes ! ⚖️"
                },
                {
                    "id": "q4_4",
                    "question": "Que faire si ton trade est en perte et ton Stop-Loss n'est pas encore touché ?",
                    "type": "multiple_choice",
                    "options": [
                        "Déplacer le SL plus bas pour éviter d'être sorti",
                        "Attendre patiemment, respecter le plan",
                        "Ajouter plus d'argent pour moyenner à la baisse",
                        "Fermer immédiatement de peur"
                    ],
                    "correct_answer": 1,
                    "explanation": "Respecte ton plan ! Si tu as bien placé ton SL, attends. Ne le déplace JAMAIS vers le bas ! 📋"
                },
                {
                    "id": "q4_5",
                    "question": "Ton capital est 1000€, tu risques 2% (20€), ton SL est à 4% de l'entrée. Quelle position max ?",
                    "type": "multiple_choice",
                    "options": [
                        "1000€",
                        "500€",
                        "200€",
                        "50€"
                    ],
                    "correct_answer": 1,
                    "explanation": "Position = Risque / Distance SL = 20€ / 0.04 = 500€ max. C'est le Position Sizing ! 📐"
                },
                {
                    "id": "q4_6",
                    "question": "Pourquoi utiliser plusieurs Take-Profit (TP1, TP2, TP3) ?",
                    "type": "multiple_choice",
                    "options": [
                        "Pour compliquer les choses",
                        "Pour sécuriser des gains tout en gardant du potentiel",
                        "C'est obligatoire",
                        "Pour payer plus de frais"
                    ],
                    "correct_answer": 1,
                    "explanation": "Avec plusieurs TP, tu sécurises des gains à différents niveaux tout en laissant une partie profiter si ça continue ! 🎯"
                },
                {
                    "id": "q4_7",
                    "question": "Tu as perdu 3 trades d'affilée. Que dois-tu faire ?",
                    "type": "multiple_choice",
                    "options": [
                        "Trader plus gros pour récupérer vite",
                        "Faire une pause, analyser, puis reprendre calmement",
                        "Abandonner le trading",
                        "Ignorer et continuer pareil"
                    ],
                    "correct_answer": 1,
                    "explanation": "Après des pertes, fais une PAUSE ! Analyse ce qui n'a pas marché. Le 'revenge trading' est ton pire ennemi. 🧘"
                },
                {
                    "id": "q4_8",
                    "question": "C'est quoi l'élément le PLUS important d'un plan de trading ?",
                    "type": "multiple_choice",
                    "options": [
                        "Les indicateurs utilisés",
                        "Le respect des règles définies",
                        "La couleur du graphique",
                        "Le nombre de trades par jour"
                    ],
                    "correct_answer": 1,
                    "explanation": "Le meilleur plan du monde est inutile si tu ne le respectes pas ! La discipline est la clé du succès. 🔑"
                },
            ]
        }
    },
    {
        "id": "module_5",
        "title": "Psychologie du Trading",
        "description": "Maîtrise tes émotions, elles sont ton plus grand ennemi.",
        "icon": "🧘",
        "color": "amber",
        "order": 5,
        "estimated_time": "40 min",
        "lessons": [
            {
                "id": "lesson_5_1",
                "title": "Tes émotions : l'ennemi intérieur",
                "description": "Comprendre pourquoi on fait des erreurs",
                "order": 1,
                "xp_reward": 50,
                "content": """
# 🎭 Tes Émotions : L'Ennemi Intérieur

Hey ! **BULL** ici ! 🐂 Le sujet le plus important !

## 🧠 La vérité sur le trading

> **80% du succès en trading vient de la psychologie, pas de la technique.**

Tu peux avoir la meilleure stratégie du monde, si tu ne maîtrises pas tes émotions, tu perdras.

## 😰 Les émotions dangereuses

### 1. LA PEUR 😱
```
Situation : Ton trade perd 1%
Pensée : "Je vais tout perdre !"
Action : Tu vends en panique
Résultat : Le prix remonte ensuite 📈
```

### 2. LA CUPIDITÉ 🤑
```
Situation : Ton trade gagne 10%
Pensée : "Je peux gagner plus !"
Action : Tu ne vends pas
Résultat : Le prix redescend à 0% 📉
```

### 3. L'ESPOIR 🙏
```
Situation : Ton trade perd 15%
Pensée : "Ça va remonter..."
Action : Tu ne coupes pas ta perte
Résultat : Tu perds 30% 💸
```

### 4. LE REGRET 😢
```
Situation : Tu as raté une opportunité
Pensée : "J'aurais dû acheter !"
Action : Tu achètes en retard
Résultat : Tu achètes au plus haut 📉
```

## 🎢 Le cycle émotionnel

```
        Euphorie 🤩
           /\\
          /  \\
   Espoir/    \\Anxiété
        /      \\
       /   😐   \\
      /  Déni    \\
     /            \\
    /         Peur \\
   /                \\
  Dépression 😢      Panique 😱
```

*Ce cycle se répète à chaque mouvement du marché !*

## 💡 Pourquoi on réagit comme ça ?

Notre cerveau est programmé pour la **survie**, pas pour le trading :

- Perdre fait 2x plus "mal" que gagner fait "plaisir"
- On préfère éviter la douleur que rechercher le plaisir
- Notre cerveau cherche des patterns même où il n'y en a pas

## 🛡️ Comment se protéger ?

### 1. Avoir un PLAN
- Décide TOUT avant d'entrer
- Quand exécuter, le cerveau est en mode "pilote automatique"

### 2. Réduire l'enjeu
- Trade petit jusqu'à être zen avec les pertes
- Si tu ressens du stress, ta position est trop grosse

### 3. Accepter les pertes
- Perdre fait partie du jeu
- Même les meilleurs perdent 40-50% du temps

## 💡 Conseil de BULL

> Avant chaque trade, demande-toi : "Est-ce que je serais OK de perdre cette somme ?" Si la réponse est non, réduis ta position !

## 🧠 À retenir

- Les émotions sont ton plus grand ennemi
- Peur et cupidité causent 90% des erreurs
- Un plan écrit neutralise les émotions
- Si tu ressens du stress, ta position est trop grande
- Accepte les pertes comme partie du jeu
""",
            },
            {
                "id": "lesson_5_2",
                "title": "FOMO et FUD",
                "description": "Les pièges émotionnels du marché",
                "order": 2,
                "xp_reward": 50,
                "content": """
# 😱 FOMO et FUD

Salut ! **BULL** au rapport ! 🐂 Deux pièges redoutables !

## 🚀 C'est quoi le FOMO ?

**FOMO** = Fear Of Missing Out
*La peur de rater une opportunité*

### Le scénario FOMO classique :
```
1. Bitcoin monte de 20% en 2 jours
2. Tu vois tout le monde en parler
3. Tu penses : "Je dois acheter, ça va continuer !"
4. Tu achètes au sommet
5. Le prix corrige de 15%
6. Tu paniques et vends en perte 😭
```

### Signes que tu es en FOMO :
- ❌ Tu vois le prix monter et tu DOIS acheter
- ❌ Tu n'as pas analysé, juste vu que ça monte
- ❌ Tu as peur que ce soit "ta seule chance"
- ❌ Tout le monde en parle (Twitter, news...)

### La vérité sur le FOMO :
> Le meilleur moment pour acheter n'est PAS quand tout le monde parle d'un actif !

## 😰 C'est quoi le FUD ?

**FUD** = Fear, Uncertainty, Doubt
*Peur, Incertitude, Doute*

### Le scénario FUD classique :
```
1. Une news négative sort (hack, régulation, etc.)
2. Le prix chute de 10%
3. Tu paniques : "C'est la fin !"
4. Tu vends en catastrophe
5. La news était exagérée
6. Le prix remonte +30% sans toi 📈
```

### Exemples de FUD :
- "La Chine bannit le Bitcoin" (pour la 10ème fois 🙄)
- "Untel dit que le Bitcoin va à $0"
- "Cette crypto est une arnaque" (sans preuves)

## 🛡️ Comment se protéger ?

### Contre le FOMO :
1. **Rappelle-toi** : Il y aura TOUJOURS d'autres opportunités
2. **Vérifie ton plan** : Ce trade respecte-t-il mes critères ?
3. **Attends** : Si c'est vraiment bon, ça le sera encore demain
4. **Demande-toi** : "Est-ce que j'achèterais si ça n'avait pas monté ?"

### Contre le FUD :
1. **Respire** : Ne réagis pas à chaud
2. **Vérifie les sources** : C'est vrai ou c'est du bruit ?
3. **Perspective** : Le Bitcoin a survécu à TOUTES les news négatives
4. **Plan** : Si ton SL n'est pas touché, ne vends pas !

## 📰 Les médias et réseaux sociaux

### Ce qu'ils font :
- Titres sensationnalistes pour les clics
- Disent "TO THE MOON 🚀" quand ça monte
- Disent "C'EST FINI 💀" quand ça descend

### Ce que tu devrais faire :
- Limiter ta consommation de news crypto
- Ne pas suivre les "influenceurs" crypto
- Avoir TON propre avis basé sur ton analyse

## 💡 Conseil de BULL

> "Sois craintif quand les autres sont cupides, et cupide quand les autres sont craintifs." - Warren Buffett

En d'autres termes : Fais le CONTRAIRE de la foule ! 

## 🧠 À retenir

- FOMO = acheter parce que ça monte (mauvais)
- FUD = vendre parce que ça fait peur (mauvais)
- Les deux mènent à acheter haut et vendre bas
- Coupe les réseaux sociaux pendant que tu trades
- Il y aura TOUJOURS d'autres opportunités !
""",
            },
            {
                "id": "lesson_5_3",
                "title": "La discipline",
                "description": "La clé de la réussite à long terme",
                "order": 3,
                "xp_reward": 50,
                "content": """
# 🎯 La Discipline

Hey champion ! **BULL** ici ! 🐂 La qualité N°1 du trader !

## 🏆 Qu'est-ce qui différencie les gagnants ?

Ce n'est PAS :
- ❌ Une stratégie secrète
- ❌ Des indicateurs magiques
- ❌ De la chance
- ❌ Un capital énorme

C'est :
- ✅ La **DISCIPLINE** de suivre un plan
- ✅ La **PATIENCE** d'attendre les bonnes opportunités
- ✅ La **CONSTANCE** jour après jour

## 📋 La discipline, c'est quoi ?

> Faire ce qui est PRÉVU, même quand tu n'en as pas envie.

### Exemples de discipline :
- ✅ Ne pas trader quand il n'y a pas de setup clair
- ✅ Couper ses pertes au SL prévu
- ✅ Prendre ses profits au TP prévu
- ✅ Respecter sa taille de position max
- ✅ Arrêter après la perte journalière max

## 🚫 Ce qui arrive sans discipline

```
Jour 1 : "Je suis discipliné, je suis mon plan" ✅
Jour 2 : "Ce trade a l'air bien, mais ne respecte pas mes critères... bon allez, je tente" ❌
Jour 3 : "J'ai perdu, je vais récupérer avec un trade plus gros" ❌❌
Jour 4 : "J'ai vidé mon compte" 💸😭
```

## 💪 Comment développer la discipline ?

### 1. Commence PETIT
- Trade avec des petites sommes
- L'enjeu faible = moins d'émotions = plus de discipline

### 2. Créé des RITUELS
```
Avant chaque trade :
□ Vérifier le plan
□ Calculer la position
□ Définir SL et TP
□ Respirer 3 fois
□ Exécuter
```

### 3. Tiens un JOURNAL
Note après chaque trade :
- As-tu respecté ton plan ? Oui/Non
- Si non, pourquoi ?
- Que ferais-tu différemment ?

### 4. Fixe des RÈGLES STRICTES
```
Mes règles non négociables :
1. Pas de trade sans SL
2. Max 2% de risque
3. Max 3 trades par jour
4. Stop si -5% dans la journée
```

## 🎮 La discipline comme un muscle

Plus tu pratiques, plus c'est facile !

```
Semaine 1 : Dur de respecter le plan 😓
Semaine 4 : Ça devient plus facile 🙂
Mois 3 : C'est automatique ! 😎
```

## 📊 Résultats discipline vs chaos

| | Trader discipliné | Trader impulsif |
|---|------------------|-----------------|
| Win rate | 45% | 45% |
| Respecte R:R | Oui (2:1) | Non (varie) |
| Après 100 trades | +20% | -30% |

*Même win rate, résultats opposés !*

## 💡 Conseil de BULL

> Si tu ne peux pas respecter tes règles avec 100€, tu ne les respecteras pas avec 10,000€. Commence petit et construis la discipline !

## 🧠 À retenir

- La discipline > l'intelligence en trading
- Suis ton plan même quand c'est dur
- Crée des rituels et routines
- Tiens un journal de trading
- La discipline se muscle avec la pratique
""",
            },
            {
                "id": "lesson_5_4",
                "title": "Accepter les pertes",
                "description": "Perdre fait partie du jeu",
                "order": 4,
                "xp_reward": 50,
                "content": """
# 💔 Accepter les Pertes

Salut ! **BULL** au rapport ! 🐂 Un sujet difficile mais essentiel !

## 📊 La vérité sur les pertes

> **TOUS les traders perdent. Même les meilleurs.**

### Stats des traders pro :
- Taux de réussite : 40-60%
- Ils perdent sur 40-60% de leurs trades
- Mais ils gagnent quand même sur l'année !

*Le secret ? Ils perdent PETIT et gagnent GROS.*

## 🤔 Pourquoi on déteste perdre ?

Notre cerveau est programmé ainsi :
- Gagner 100€ → Plaisir niveau 5 😊
- Perdre 100€ → Douleur niveau 10 😢

On ressent les pertes **2 fois plus** que les gains !

*C'est pour ça qu'on a tendance à couper nos gains trop tôt et laisser courir nos pertes.*

## 🎰 Le bon mindset

### ❌ Mauvais mindset :
"Si je perds ce trade, je suis nul"
"Je dois avoir raison"
"Une perte = un échec"

### ✅ Bon mindset :
"Une perte fait partie du métier"
"Je gère mon risque, une perte est prévue"
"Une perte n'est pas un échec si j'ai suivi mon plan"

## 📈 Comment les pros gèrent les pertes

### 1. Ils les PRÉVOIENT
```
"Sur mes 10 prochains trades, je vais probablement en perdre 4-5.
C'est NORMAL et PRÉVU."
```

### 2. Ils les LIMITENT
```
"Chaque perte sera maximum 1-2% de mon capital.
Je peux survivre à 20 pertes d'affilée."
```

### 3. Ils APPRENNENT
```
"Cette perte m'a appris quelque chose.
Je suis un meilleur trader qu'avant."
```

## 📊 L'exercice des 100 lancers

Imagine que tu joues à pile ou face :
- Face = Tu gagnes 2€
- Pile = Tu perds 1€

Sur 100 lancers (50 face, 50 pile) :
- Gains : 50 × 2€ = 100€
- Pertes : 50 × 1€ = 50€
- **Profit net : +50€** 🎉

*Tu as perdu 50 fois mais tu es rentable !*

## 🛡️ Comment mieux accepter les pertes

### 1. Réduis l'enjeu émotionnel
- Trade petit jusqu'à ce que perdre ne te stresse plus
- Si une perte te fait mal, ta position est trop grande

### 2. Prends du recul
- Une perte sur 1 trade ≠ Ta valeur comme trader
- Regarde tes résultats sur 20, 50, 100 trades

### 3. Célèbre les bonnes pertes
- Tu as coupé ta perte au SL prévu ? BRAVO ! 👏
- C'est une victoire de discipline !

## 💡 Conseil de BULL

> Après une perte, demande-toi : "Ai-je suivi mon plan ?"
> - Si oui → C'est juste la variance, passe au suivant
> - Si non → Apprends et améliore-toi

## 🧠 À retenir

- Perdre est NORMAL et INÉVITABLE
- Les pros perdent 40-60% du temps
- L'important : perdre PETIT, gagner GROS
- Une perte n'est pas un échec si tu as suivi le plan
- Célèbre quand tu coupes ta perte comme prévu !
""",
            },
            {
                "id": "lesson_5_5",
                "title": "La routine du trader",
                "description": "Organise-toi pour réussir",
                "order": 5,
                "xp_reward": 50,
                "content": """
# 🌅 La Routine du Trader

Hey ! **BULL** ici ! 🐂 Créons ta routine gagnante !

## ⏰ Pourquoi une routine ?

Une routine te permet de :
- ✅ Être **constant** dans ton approche
- ✅ **Éliminer** les décisions émotionnelles
- ✅ Ne rien **oublier** d'important
- ✅ Progresser **méthodiquement**

## 🌄 Routine du MATIN

### Avant de trader (15-20 min) :

```
□ 1. CHECK MENTAL
   - Comment je me sens ?
   - Suis-je reposé et focus ?
   - Y a-t-il du stress extérieur ?

□ 2. CHECK MARCHÉ
   - Que s'est-il passé cette nuit ?
   - Y a-t-il des news importantes ?
   - Quel est le sentiment général ?

□ 3. ANALYSE
   - Vérifier mes graphiques en Daily/4H
   - Identifier les niveaux clés
   - Y a-t-il des setups intéressants ?

□ 4. PLAN DU JOUR
   - Quels trades je considère ?
   - À quel prix j'entre ?
   - Où sont mes SL/TP ?
```

## 🌙 Routine du SOIR

### Après la journée (10-15 min) :

```
□ 1. REVIEW DES TRADES
   - Qu'ai-je fait aujourd'hui ?
   - Ai-je respecté mon plan ?
   - Résultat de chaque trade ?

□ 2. JOURNAL
   - Noter chaque trade
   - Noter mes émotions
   - Ce que j'ai bien fait / à améliorer

□ 3. PRÉPARATION DEMAIN
   - Setups à surveiller
   - Niveaux d'alerte à placer
   - News importantes prévues

□ 4. DÉCONNEXION
   - Fermer les graphiques
   - Pas de trading la nuit
   - Profiter de la vie !
```

## 📝 Le journal de trading

### Que noter à chaque trade :

```
DATE : ___
ACTIF : ___
TYPE : Achat / Vente
PRIX D'ENTRÉE : ___
STOP-LOSS : ___
TAKE-PROFIT : ___
TAILLE : ___
RAISON D'ENTRÉE : ___

--- APRÈS CLÔTURE ---

PRIX DE SORTIE : ___
RÉSULTAT : +/- ___% 
AI-JE SUIVI MON PLAN ? Oui / Non
ÉMOTION PENDANT LE TRADE : ___
LEÇON APPRISE : ___
```

## 🗓️ Routine HEBDOMADAIRE

### Chaque dimanche (30 min) :

```
□ BILAN DE LA SEMAINE
   - Combien de trades ?
   - Win rate de la semaine ?
   - P&L total ?

□ ANALYSE DES ERREURS
   - Quels trades n'ont pas respecté le plan ?
   - Pattern dans mes erreurs ?

□ POINTS POSITIFS
   - Qu'ai-je bien fait ?
   - Progrès vs semaine dernière ?

□ OBJECTIFS SEMAINE PROCHAINE
   - Sur quoi je travaille ?
   - Quelle discipline améliorer ?
```

## ⚠️ Quand NE PAS trader

Ton routine doit inclure des "NO TRADE" days :

- ❌ Quand tu es fatigué ou malade
- ❌ Après une grosse perte
- ❌ Pendant des events majeurs (news importantes)
- ❌ Quand tu as un stress personnel
- ❌ Quand tu n'as pas fait ton analyse

## 💡 Conseil de BULL

> "La discipline de la routine quotidienne sépare les amateurs des pros. 20 minutes par jour de routine vaut plus que 8h de trading chaotique !"

## 🧠 À retenir

- Une routine crée de la constance
- 15-20 min le matin, 10-15 min le soir
- Le journal est ton outil de progression
- Review hebdomadaire pour s'améliorer
- Savoir quand NE PAS trader !
""",
            },
        ],
        "quiz": {
            "title": "Quiz - Psychologie du Trading",
            "description": "Prouve que tu maîtrises tes émotions !",
            "passing_score": 70,
            "questions": [
                {
                    "id": "q5_1",
                    "question": "C'est quoi le FOMO ?",
                    "type": "multiple_choice",
                    "options": [
                        "Une cryptomonnaie",
                        "La peur de rater une opportunité",
                        "Un indicateur technique",
                        "Un type de graphique"
                    ],
                    "correct_answer": 1,
                    "explanation": "FOMO = Fear Of Missing Out. C'est quand tu achètes juste parce que ça monte et que tu as peur de rater le train ! 🚂"
                },
                {
                    "id": "q5_2",
                    "question": "Quel pourcentage du succès en trading vient de la psychologie ?",
                    "type": "multiple_choice",
                    "options": [
                        "10%",
                        "30%",
                        "80%",
                        "100%"
                    ],
                    "correct_answer": 2,
                    "explanation": "80% du succès vient de la psychologie ! La technique est importante, mais sans discipline mentale, tu perdras. 🧠"
                },
                {
                    "id": "q5_3",
                    "question": "Après 3 trades perdants d'affilée, que dois-tu faire ?",
                    "type": "multiple_choice",
                    "options": [
                        "Trader plus gros pour récupérer vite",
                        "Faire une pause, analyser, et revenir calme",
                        "Abandonner le trading",
                        "Trader plus vite"
                    ],
                    "correct_answer": 1,
                    "explanation": "Après des pertes, PAUSE ! Analyse ce qui s'est passé et reviens quand tu es calme. Le revenge trading est dangereux ! 🧘"
                },
                {
                    "id": "q5_4",
                    "question": "Qu'est-ce qui différencie les traders gagnants des perdants ?",
                    "type": "multiple_choice",
                    "options": [
                        "Une stratégie secrète",
                        "La chance",
                        "La discipline de suivre leur plan",
                        "Plus d'argent au départ"
                    ],
                    "correct_answer": 2,
                    "explanation": "La DISCIPLINE ! Les gagnants suivent leur plan même quand c'est difficile. Pas de secret, juste de la constance. 🎯"
                },
                {
                    "id": "q5_5",
                    "question": "Si un pro gagne 45% de ses trades, est-il rentable ?",
                    "type": "multiple_choice",
                    "options": [
                        "Non, il perd plus qu'il ne gagne",
                        "Oui, si ses gains sont plus gros que ses pertes",
                        "Impossible à dire",
                        "Non, il faut au moins 70%"
                    ],
                    "correct_answer": 1,
                    "explanation": "OUI ! Avec un bon ratio Risk/Reward (ex: 1:2), tu peux être très rentable même avec 45% de trades gagnants ! 📊"
                },
                {
                    "id": "q5_6",
                    "question": "Quand le marché chute et que tout le monde a peur, que dit Warren Buffett ?",
                    "type": "multiple_choice",
                    "options": [
                        "Vends tout !",
                        "Sois cupide quand les autres ont peur",
                        "Suis la foule",
                        "Arrête de regarder"
                    ],
                    "correct_answer": 1,
                    "explanation": "\"Sois craintif quand les autres sont cupides, et cupide quand les autres ont peur.\" Les meilleures opportunités arrivent dans la peur ! 💎"
                },
                {
                    "id": "q5_7",
                    "question": "Pourquoi tenir un journal de trading ?",
                    "type": "multiple_choice",
                    "options": [
                        "C'est obligatoire pour trader",
                        "Pour identifier ses erreurs et progresser",
                        "Pour faire joli",
                        "Ce n'est pas utile"
                    ],
                    "correct_answer": 1,
                    "explanation": "Le journal te permet de voir tes patterns d'erreurs et de t'améliorer. Sans feedback, pas de progression ! 📝"
                },
                {
                    "id": "q5_8",
                    "question": "C'est quoi le FUD ?",
                    "type": "multiple_choice",
                    "options": [
                        "Un nouveau Bitcoin",
                        "Peur, Incertitude, Doute",
                        "Une technique de trading",
                        "Un type d'ordre"
                    ],
                    "correct_answer": 1,
                    "explanation": "FUD = Fear, Uncertainty, Doubt. C'est quand les news négatives te font paniquer et vendre au pire moment ! 😰"
                },
            ]
        }
    },
]

# Module 6 continue...
ACADEMY_MODULE_6 = {
    "id": "module_6",
    "title": "Tes Premières Stratégies",
    "description": "Des méthodes simples et efficaces pour commencer à trader",
    "icon": "♟️",
    "color": "cyan",
    "order": 6,
    "estimated_time": "50 min",
    "lessons": [
        {
            "id": "lesson_6_1",
            "title": "DCA - Investir régulièrement",
            "description": "La stratégie la plus simple et efficace",
            "order": 1,
            "xp_reward": 50,
            "content": """
# 📅 DCA - Investir Régulièrement

Salut champion ! **BULL** ici ! 🐂 La stratégie parfaite pour débuter !

## 🤔 C'est quoi le DCA ?

**DCA** = Dollar Cost Averaging
*Investir la même somme à intervalles réguliers*

C'est ULTRA simple :
- Même montant (ex: 50€)
- Même fréquence (ex: chaque semaine)
- Peu importe le prix !

## 🎯 Exemple concret

Tu décides : **50€ de Bitcoin chaque lundi**

| Semaine | Prix BTC | Tu reçois |
|---------|----------|-----------|
| 1 | 40,000€ | 0.00125 BTC |
| 2 | 35,000€ | 0.00143 BTC |
| 3 | 45,000€ | 0.00111 BTC |
| 4 | 38,000€ | 0.00132 BTC |
| **Total** | | **0.00511 BTC** |

Investissement : 200€
Prix moyen : 39,140€ (au lieu de potentiellement 45,000€ si all-in)

## ✅ Pourquoi le DCA est génial ?

### 1. Pas de timing à trouver
Tu n'as pas à deviner le "bon moment" pour acheter !

### 2. Tu profites des baisses
Quand le prix baisse, tu achètes PLUS d'unités 📈

### 3. Zéro stress
Pas besoin de regarder les graphiques chaque jour

### 4. Discipline automatique
Tu investis régulièrement, sans émotion

## 📊 DCA vs Lump Sum

**Lump Sum** = Tout investir d'un coup

| Situation | DCA | Lump Sum |
|-----------|-----|----------|
| Marché monte | 😐 Moins de gains | 😊 Plus de gains |
| Marché descend | 😊 Prix moyen bas | 😭 Grosse perte |
| Marché volatile | 😊 Stress réduit | 😰 Montagnes russes |

*Historiquement, le lump sum gagne souvent, MAIS le DCA réduit énormément le risque et le stress !*

## 🛠️ Comment mettre en place ton DCA

### 1. Choisis ton actif
Bitcoin et Ethereum sont parfaits pour le DCA

### 2. Définis ton budget
Montant que tu peux mettre CHAQUE période sans stress

### 3. Choisis ta fréquence
- Hebdomadaire (recommandé)
- Bi-mensuel
- Mensuel

### 4. Automatise !
Beaucoup de plateformes permettent le DCA automatique

## ⚠️ Important

- Le DCA ne protège pas d'une baisse générale du marché
- Choisis des actifs solides (BTC, ETH) pas des shitcoins
- C'est une stratégie LONG TERME (minimum 1-2 ans)

## 💡 Conseil de BULL

> Le DCA est parfait pour construire une position sans stress. Commence avec un montant que tu ne remarquerais même pas s'il disparaissait. 50€/semaine vaut mieux que 500€ une fois tous les 3 mois !

## 🧠 À retenir

- DCA = même somme, même fréquence, peu importe le prix
- Tu achètes plus quand c'est bas, moins quand c'est haut
- Zéro stress, zéro timing à trouver
- Parfait pour les débutants
- Vision long terme obligatoire !
""",
        },
        {
            "id": "lesson_6_2",
            "title": "Swing Trading basique",
            "description": "Surfer sur les vagues du marché",
            "order": 2,
            "xp_reward": 50,
            "content": """
# 🏄 Swing Trading Basique

Hey ! **BULL** au rapport ! 🐂 Apprenons à surfer les vagues !

## 🤔 C'est quoi le Swing Trading ?

Le Swing Trading consiste à :
- Acheter quand le prix est "bas" dans une tendance
- Vendre quand il est "haut"
- Garder la position quelques jours à quelques semaines

*C'est comme surfer : tu attends la bonne vague, tu la prends, et tu profites du ride !*

## 🎯 Le concept clé : Les "Swings"

Le prix ne monte jamais en ligne droite. Il fait des vagues :

```
         /\\     /\\
        /  \\   /  \\     → Tendance haussière
       /    \\ /    \\
      /      V       \\
     /    "Swing     \\
    /      Low"       
   
Tu achètes ICI 👆
```

## 📋 Stratégie simple en 5 étapes

### 1. Identifie la tendance
- Prix > MA200 = Tendance haussière → On cherche à ACHETER
- Prix < MA200 = Tendance baissière → On reste en dehors (débutant)

### 2. Attends un "pullback"
Le prix revient vers un support ou une MA

### 3. Cherche une confirmation
- Bougie de retournement
- RSI sortant de survente
- Rebond sur support

### 4. Entre avec un plan
- Point d'entrée défini
- Stop-Loss sous le swing low
- Take-Profit vers la résistance

### 5. Gère ton trade
- Laisse courir si ça va dans ton sens
- Coupe si le SL est touché

## 📊 Exemple concret

```
Bitcoin en tendance haussière (>MA200)

1. Prix : $95,000 → Trop haut pour acheter
2. Pullback vers $88,000 (support)
3. RSI à 35 (survente) + bougie verte
4. Entrée : $89,000
   SL : $86,000 (-3.4%)
   TP : $96,000 (+7.9%)
   Ratio : 1:2.3 ✅

5. Le prix atteint $96,000 après 5 jours
   Profit : +7.9% 🎉
```

## ⏰ Timeframes recommandés

| Usage | Timeframe |
|-------|-----------|
| Tendance générale | Daily (1D) |
| Entrées | 4H |
| Affinage | 1H (optionnel) |

## ⚠️ Erreurs à éviter

### ❌ Acheter en surachat
N'achète pas quand le RSI est > 70

### ❌ Ignorer la tendance
Ne fais pas de swing long en tendance baissière !

### ❌ Être impatient
Attends le bon setup, ne force pas

### ❌ SL trop serré
Laisse de la place pour respirer

## 💡 Conseil de BULL

> Le Swing Trading demande de la PATIENCE. Tu peux attendre plusieurs jours pour un bon setup. C'est normal ! Mieux vaut un excellent trade par semaine que 10 trades moyens.

## 🧠 À retenir

- Swing = acheter les creux en tendance haussière
- Toujours vérifier la tendance d'abord (MA200)
- Attendre les pullbacks vers les supports
- Timeframes : Daily pour tendance, 4H pour entrées
- Patience et discipline sont essentiels !
""",
        },
        {
            "id": "lesson_6_3",
            "title": "La stratégie de rebond sur support",
            "description": "Une technique simple et efficace",
            "order": 3,
            "xp_reward": 50,
            "content": """
# 🎯 Stratégie de Rebond sur Support

Salut ! **BULL** ici ! 🐂 Une stratégie claire et simple !

## 📋 Le concept

L'idée est simple :
1. Identifie un support fort
2. Attends que le prix y arrive
3. Achète au rebond
4. Vends à la résistance

## 🔍 Étape 1 : Trouver un bon support

Un support est FORT quand :
- ✅ Le prix y a rebondi 2-3 fois minimum
- ✅ Il correspond à un ancien plus bas important
- ✅ Il est visible sur le Daily

```
                                    Prix actuel
                                         ↓
─────────────────────────────────────────────
    ↑      ↑      ↑        
    1      2      3    ← Chaque rebond renforce le support
```

## 👀 Étape 2 : Surveiller l'approche

Quand le prix s'approche du support :
- Mets une alerte de prix
- Ne te précipite pas !
- Attends de voir COMMENT il réagit

## ✅ Étape 3 : Confirmation du rebond

N'achète PAS dès que le prix touche le support !

**Attends une confirmation :**
- Bougie verte avec longue mèche basse (rejet)
- Ou bougie "hammer" (marteau)
- Ou RSI qui remonte de la survente

```
   Support
─────────────────
        │   ← Mèche de rejet
      ┌─┴─┐
      │ 🟢│ ← Corps vert (ferme au-dessus de l'ouverture)
      └───┘
      
      C'est un signal d'achat ! ✅
```

## 📏 Étape 4 : Placer son trade

### Entrée
Juste au-dessus de la bougie de confirmation

### Stop-Loss
Sous le support (avec un peu de marge)

### Take-Profit
À la prochaine résistance significative

### Exemple :
```
Support : $85,000
Bougie de confirmation close à : $86,000

Entrée : $86,200
Stop-Loss : $84,000 (-2.5%)
Take-Profit : $92,000 (+6.7%)
Ratio R:R : 1:2.7 ✅
```

## ⚠️ Quand NE PAS prendre le trade

### ❌ Support en tendance baissière
Si le prix est sous la MA200, le support peut casser !

### ❌ Trop de bougies rouges d'affilée
Momentum trop fort vers le bas

### ❌ News importante imminente
Attend que la volatilité se calme

### ❌ RSI déjà haut
Si le RSI est > 50, le rebond a peut-être déjà eu lieu

## 💡 Astuces de pro

### 1. Plus le support est testé, plus il est fragile
Un support testé 5+ fois risque de casser !

### 2. Le meilleur moment
Acheter au PREMIER ou DEUXIÈME test d'un nouveau support

### 3. Combine avec d'autres facteurs
- Support + MA50 = super fort
- Support + RSI survente = super signal

## 💡 Conseil de BULL

> Cette stratégie a un excellent taux de réussite car tu trades AVEC la logique du marché. Les supports existent parce que beaucoup d'acheteurs y attendent !

## 🧠 À retenir

- Cherche des supports avec 2-3 rebonds minimum
- Attends TOUJOURS une bougie de confirmation
- SL sous le support, TP à la résistance
- Ne trade pas les supports en tendance baissière
- Plus c'est testé, plus c'est fragile
""",
        },
        {
            "id": "lesson_6_4",
            "title": "Quand entrer et quand sortir",
            "description": "Le timing simplifié",
            "order": 4,
            "xp_reward": 50,
            "content": """
# ⏰ Quand Entrer et Quand Sortir

Hey champion ! **BULL** au rapport ! 🐂 Le timing simplifié !

## 🎯 La règle d'or de l'entrée

> **N'entre JAMAIS sur impulsion. Entre sur SIGNAL.**

## ✅ Checklist d'ENTRÉE

Avant chaque achat, vérifie :

```
□ 1. TENDANCE
   Est-ce que le prix est > MA200 ?
   → Si NON, je n'achète pas

□ 2. NIVEAU
   Est-ce que je suis près d'un support ?
   → Si NON, j'attends

□ 3. INDICATEURS
   RSI < 50 ? (pas en surachat)
   → Si RSI > 70, je n'achète pas

□ 4. CONFIRMATION
   Y a-t-il une bougie de signal ?
   → Si NON, j'attends

□ 5. RISK/REWARD
   Mon ratio est-il > 2:1 ?
   → Si NON, je passe
```

**5/5 coché ? → ENTRE !**
**Moins de 5 ? → ATTENDS !**

## 📊 Les meilleurs moments pour entrer

### 🟢 BON moment (forte probabilité)
- Pullback sur support EN tendance haussière
- RSI sortant de survente (< 30 → > 30)
- Bougie de retournement sur niveau clé
- Golden Cross récent

### 🔴 MAUVAIS moment (faible probabilité)
- Après une grosse hausse (+20% en 3 jours)
- RSI > 70 (surachat)
- Cassure de support
- News majeure imminente

## 🚪 Quand SORTIR ?

### Sortie planifiée (la meilleure)
Tu as défini tes TP avant d'entrer :
- TP1 : 50% de la position
- TP2 : 30% de la position
- TP3 : 20% (ou trailing stop)

### Sortie forcée (le SL)
Ton Stop-Loss est touché → Tu sors, pas de discussion !

### Sortie opportuniste
Le prix atteint une zone de résistance majeure + signes de faiblesse

## 📉 Signes qu'il faut sortir (même avant le TP)

### ⚠️ Drapeaux rouges :
- RSI en divergence baissière
- Volume qui diminue pendant la hausse
- Bougie d'engloutissement bearish
- Cassure de la MA20 vers le bas

## 🎮 Exercice mental

Avant chaque trade, demande-toi :

**Pour l'entrée :**
"Si je n'avais pas cette position, est-ce que j'achèterais maintenant ?"

**Pour la sortie :**
"Si j'avais cet argent en cash, est-ce que j'achèterais ce trade maintenant ?"

Si la réponse est NON → Agis en conséquence !

## 💡 L'erreur classique du débutant

```
❌ Ce que fait le débutant :
- Entre trop tôt (impatience)
- Sort trop tôt (peur)
- OU reste trop longtemps (cupidité)

✅ Ce que fait le pro :
- Entre tard (attend confirmation)
- Sort selon le PLAN (pas l'émotion)
```

## 💡 Conseil de BULL

> "Le meilleur trade est souvent celui que tu ne prends PAS."

Quand tu hésites, c'est probablement que tous les critères ne sont pas réunis. Attends le prochain setup parfait !

## 🧠 À retenir

- Entre sur SIGNAL, pas sur impulsion
- Checklist obligatoire avant chaque entrée
- 5 critères validés = GO
- Moins de 5 = ATTENDS
- Sors selon ton plan, pas selon tes émotions
- En cas de doute, abstiens-toi !
""",
        },
        {
            "id": "lesson_6_5",
            "title": "Créer TON propre plan",
            "description": "Personnalise ta stratégie",
            "order": 5,
            "xp_reward": 50,
            "content": """
# 📝 Créer TON Propre Plan

Salut ! **BULL** ici ! 🐂 Construisons TON plan personnalisé !

## 🎯 Pourquoi ton PROPRE plan ?

Copier la stratégie d'un autre ne marchera pas pour toi car :
- Tu n'as pas les mêmes horaires
- Tu n'as pas le même capital
- Tu n'as pas la même tolérance au risque
- Tu n'as pas le même tempérament

## 📋 Template de Plan Personnel

Remplis ce template :

```
═══════════════════════════════════════
       MON PLAN DE TRADING PERSONNEL
              Par: [Ton nom]
═══════════════════════════════════════

📊 MES MARCHÉS
─────────────────────────────────────────
Je trade : □ Bitcoin □ Ethereum □ Autre:___
Je NE trade PAS : ____________________
Timeframe principal : □ 4H □ Daily □ Weekly

⏰ MES HORAIRES
─────────────────────────────────────────
Analyse marché : ___h le matin
Gestion positions : ___h le soir
Jours de trading : □ L □ M □ Me □ J □ V □ S □ D
Je NE trade PAS quand : _________________

💰 MA GESTION DU RISQUE
─────────────────────────────────────────
Capital total : ___€
Risque max par trade : ___% = ___€
Trades max simultanés : ___
Perte max par jour : ___€
Perte max par semaine : ___€

🎯 MES CRITÈRES D'ENTRÉE
─────────────────────────────────────────
Pour acheter, je DOIS avoir :
□ Critère 1 : _________________________
□ Critère 2 : _________________________
□ Critère 3 : _________________________
□ Critère 4 : _________________________
(minimum ___/4 critères)

🚪 MES RÈGLES DE SORTIE
─────────────────────────────────────────
Stop-Loss : Toujours sous ________________
TP1 : ___% de la position à ratio ___:1
TP2 : ___% à _________________________
TP3 : ___% trailing / résistance

⛔ MES RÈGLES NON NÉGOCIABLES
─────────────────────────────────────────
1. ___________________________________
2. ___________________________________
3. ___________________________________

📔 MON ENGAGEMENT
─────────────────────────────────────────
Je m'engage à suivre ce plan.
Si je le viole, je ferai une pause de ___ jour(s).

Signé : _________________ Date : _______
═══════════════════════════════════════
```

## 🎯 Exemple de plan complété

```
MON PLAN - DÉBUTANT PRUDENT

MARCHÉS : Bitcoin uniquement
TIMEFRAME : Daily + 4H

HORAIRES :
- Analyse : 8h matin
- Check : 18h soir
- Trading : Lun-Ven seulement

RISQUE :
- Capital : 500€
- Risque/trade : 1% = 5€
- Max 2 trades ouverts
- Stop si -3% dans la semaine

ENTRÉE (3/4 minimum) :
□ Prix > MA200 (Daily)
□ RSI 4H < 50
□ Rebond sur support
□ Bougie de confirmation

SORTIE :
- SL : Sous le dernier support
- TP1 : 50% à ratio 2:1
- TP2 : 50% à la résistance

RÈGLES NON NÉGOCIABLES :
1. Jamais sans stop-loss
2. Jamais plus de 5€ de risque
3. Jamais de trade le week-end
4. Jamais de revenge trading
```

## 📈 Comment l'améliorer avec le temps

### Semaine 1-4 : Observe et note
- Suis ton plan strictement
- Note TOUT dans ton journal
- Ne change rien encore

### Mois 2 : Analyse
- Quels trades ont fonctionné ?
- Lesquels ont échoué ?
- Y a-t-il un pattern ?

### Mois 3+ : Ajuste
- Modifie UN élément à la fois
- Teste pendant 1 mois
- Garde ce qui marche

## 💡 Conseil de BULL

> Ton plan va évoluer avec ton expérience. Mais TOUJOURS avoir un plan écrit ! Un plan imparfait qu'on suit est 100x mieux que pas de plan du tout.

## 🎉 Félicitations !

Tu as terminé le Module 6 ! Tu as maintenant toutes les bases pour commencer à trader de manière intelligente et disciplinée.

## 🧠 À retenir

- Ton plan doit être PERSONNALISÉ
- Écris-le noir sur blanc
- Suis-le à la lettre pendant 1 mois
- Analyse et améliore progressivement
- Le plan est ton garde-fou !
""",
        },
    ],
    "quiz": {
        "title": "Quiz Final - Tes Premières Stratégies",
        "description": "Prouve que tu es prêt à trader !",
        "passing_score": 70,
        "questions": [
            {
                "id": "q6_1",
                "question": "C'est quoi le DCA ?",
                "type": "multiple_choice",
                "options": [
                    "Acheter tout d'un coup",
                    "Investir la même somme régulièrement",
                    "Vendre quand ça baisse",
                    "Une cryptomonnaie"
                ],
                "correct_answer": 1,
                "explanation": "DCA = Dollar Cost Averaging. Tu investis la même somme à intervalles réguliers, peu importe le prix ! 📅"
            },
            {
                "id": "q6_2",
                "question": "En Swing Trading, quand achète-t-on ?",
                "type": "multiple_choice",
                "options": [
                    "Quand le prix est au plus haut",
                    "Pendant les pullbacks (creux) en tendance haussière",
                    "N'importe quand",
                    "Uniquement le lundi"
                ],
                "correct_answer": 1,
                "explanation": "Le Swing Trading consiste à acheter les creux (pullbacks) dans une tendance haussière. Surfer sur les vagues ! 🏄"
            },
            {
                "id": "q6_3",
                "question": "Pour la stratégie de rebond sur support, que faut-il attendre avant d'acheter ?",
                "type": "multiple_choice",
                "options": [
                    "Rien, achète dès que ça touche le support",
                    "Une bougie de confirmation (rejet, hammer...)",
                    "Que le support casse",
                    "Minuit"
                ],
                "correct_answer": 1,
                "explanation": "TOUJOURS attendre une confirmation ! Une bougie de rejet (longue mèche basse) ou un hammer confirme le rebond. ✅"
            },
            {
                "id": "q6_4",
                "question": "Combien de critères doivent être validés avant d'entrer dans un trade ?",
                "type": "multiple_choice",
                "options": [
                    "1 suffit",
                    "Au moins 3-4 critères",
                    "10 minimum",
                    "Aucun, on y va au feeling"
                ],
                "correct_answer": 1,
                "explanation": "Minimum 3-4 critères doivent être cochés ! Tendance + Niveau + Indicateur + Confirmation. C'est la confluence ! 🎯"
            },
            {
                "id": "q6_5",
                "question": "Pourquoi créer son PROPRE plan de trading ?",
                "type": "multiple_choice",
                "options": [
                    "Pour le fun",
                    "Parce que chacun a son propre tempérament, capital et disponibilité",
                    "C'est obligatoire par la loi",
                    "Ce n'est pas nécessaire"
                ],
                "correct_answer": 1,
                "explanation": "Ton plan doit correspondre à TOI : ton capital, tes horaires, ta tolérance au risque. Copier quelqu'un ne marchera pas ! 📝"
            },
            {
                "id": "q6_6",
                "question": "Quel est l'avantage principal du DCA ?",
                "type": "multiple_choice",
                "options": [
                    "Gains garantis",
                    "Pas besoin de timer le marché + stress réduit",
                    "Tu deviens riche en 1 semaine",
                    "Tu paies moins de frais"
                ],
                "correct_answer": 1,
                "explanation": "Le DCA élimine le stress du timing ! Tu n'as pas à deviner le 'bon moment' et tu obtiens un prix moyen lissé. 😌"
            },
            {
                "id": "q6_7",
                "question": "Quand faut-il modifier son plan de trading ?",
                "type": "multiple_choice",
                "options": [
                    "Après chaque trade perdant",
                    "Après 1 mois d'analyse et de recul",
                    "Jamais",
                    "Tous les jours"
                ],
                "correct_answer": 1,
                "explanation": "Suis ton plan strictement pendant 1 mois, analyse les résultats, PUIS ajuste UN élément à la fois. Pas de changements impulsifs ! 📊"
            },
            {
                "id": "q6_8",
                "question": "Tu as repéré un setup parfait mais un seul critère manque. Que fais-tu ?",
                "type": "multiple_choice",
                "options": [
                    "J'entre quand même, c'est presque bon",
                    "J'attends ou je passe, la discipline d'abord",
                    "J'entre avec une position double",
                    "J'appelle un ami"
                ],
                "correct_answer": 1,
                "explanation": "DISCIPLINE ! Si tous les critères ne sont pas réunis, tu passes. Il y aura d'autres opportunités ! 🎯"
            },
        ]
    }
}
