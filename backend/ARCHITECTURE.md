# BULL SAGE - Architecture du Backend

## Structure Modulaire (En cours de refactoring)

```
/app/backend/
├── server.py              # Serveur principal (monolithique actuel ~3600 lignes)
├── academy_data.py        # Données des leçons Academy (partie 1)
├── academy_data_part2.py  # Données des leçons Academy (partie 2)
├── requirements.txt       # Dépendances Python
├── .env                   # Variables d'environnement
│
├── core/                  # ✅ REFACTORISÉ
│   ├── __init__.py
│   ├── config.py         # Configuration MongoDB, JWT, API Keys
│   └── auth.py           # Authentification (get_current_user, get_admin_user)
│
├── models/                # ✅ REFACTORISÉ
│   ├── __init__.py
│   └── schemas.py        # Modèles Pydantic (User, Signal, Trade, etc.)
│
├── routes/                # 🔄 PARTIELLEMENT REFACTORISÉ
│   ├── __init__.py       # Agrégateur de tous les routers
│   ├── auth.py           # ✅ /auth/* (register, login, me)
│   ├── health.py         # ✅ /, /health
│   ├── watchlist.py      # ✅ /watchlist/*
│   ├── strategies.py     # ✅ /strategies/*
│   ├── settings.py       # ✅ /settings/*
│   ├── paper_trading.py  # ✅ /paper-trading/*
│   ├── alerts.py         # ✅ /alerts/*, /alerts/smart/*
│   ├── signals.py        # ✅ /signals/*
│   ├── journal.py        # ✅ /journal/*
│   ├── onboarding.py     # ✅ /onboarding/*
│   ├── admin.py          # ✅ /admin/*
│   ├── market.py         # 📋 À FAIRE - /market/*
│   ├── trading.py        # 📋 À FAIRE - /trading/*
│   ├── assistant.py      # 📋 À FAIRE - /assistant/*
│   └── academy.py        # 📋 À FAIRE - /academy/*
│
└── services/              # 📋 À CRÉER
    ├── __init__.py
    ├── market_data.py    # Service de récupération des données marché
    └── ai_analysis.py    # Service d'analyse IA (GPT)
```

## Statut du Refactoring

### ✅ Phase 1 : Core & Models (TERMINÉ)
- Configuration centralisée dans `core/config.py`
- Authentification extraite dans `core/auth.py`
- Modèles Pydantic dans `models/schemas.py`

### ✅ Phase 2 : Routes Simples (TERMINÉ)
- Auth, Health, Watchlist, Strategies, Settings
- Paper Trading, Alerts, Signals, Journal
- Onboarding, Admin

### 📋 Phase 3 : Routes Complexes (À FAIRE)
Les routes suivantes contiennent beaucoup de logique métier et nécessitent un travail supplémentaire :

1. **Market Routes** (~600 lignes)
   - Données crypto (CoinGecko)
   - Données forex/stocks (Alpha Vantage)
   - Fear & Greed Index
   - Données économiques (FRED)

2. **Trading Routes** (~400 lignes)
   - Analyse technique complète (pandas-ta)
   - Génération de signaux IA
   - Morning Briefing

3. **Assistant Routes** (~300 lignes)
   - Chat avec GPT-5.1
   - Contexte de trading
   - Historique des conversations

4. **Academy Routes** (~500 lignes)
   - Modules et leçons
   - Quiz et scores
   - XP, badges, niveaux
   - Leaderboard

## API Endpoints

### Authentification
- `POST /api/auth/register` - Inscription
- `POST /api/auth/login` - Connexion
- `GET /api/auth/me` - Profil utilisateur

### Market Data
- `GET /api/market/crypto` - Liste des cryptos
- `GET /api/market/crypto/{coin_id}` - Détail d'une crypto
- `GET /api/market/intelligence` - Intelligence marché (macro)
- `GET /api/market/news` - Actualités

### Trading
- `GET /api/trading/analysis/{symbol}` - Analyse technique
- `POST /api/trading/generate-signal` - Générer un signal IA
- `GET /api/trading/briefing` - Morning Briefing

### Academy
- `GET /api/academy/modules` - Liste des modules
- `GET /api/academy/modules/{id}` - Détail d'un module
- `GET /api/academy/lessons/{id}` - Contenu d'une leçon
- `POST /api/academy/lessons/{id}/complete` - Marquer terminé
- `POST /api/academy/quiz/{module_id}/submit` - Soumettre quiz
- `GET /api/academy/leaderboard` - Classement

## Notes pour le Développeur

1. **Ne pas casser l'existant** : Le `server.py` actuel fonctionne parfaitement. Le refactoring doit être progressif.

2. **Tester après chaque changement** : Utiliser le testing agent après chaque migration de route.

3. **Priorité** : Commencer par les routes les moins dépendantes des services externes.

4. **Variables d'environnement** : Ne jamais hardcoder les clés API. Utiliser `core/config.py`.
