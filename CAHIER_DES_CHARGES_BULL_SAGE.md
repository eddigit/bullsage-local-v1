# 📊 CAHIER DES CHARGES - BULL SAGE

## Assistant Intelligent de Trading

**Version** : 1.0  
**Date** : Décembre 2024  
**Statut** : Production  

---

# 1. PRÉSENTATION GÉNÉRALE

## 1.1 Contexte

Dans un monde financier de plus en plus complexe et volatil, les traders particuliers ont besoin d'outils professionnels pour prendre des décisions éclairées. BULL SAGE répond à ce besoin en offrant une plateforme complète d'analyse et d'assistance au trading, combinant données temps réel, intelligence artificielle et outils de gestion de portefeuille.

## 1.2 Objectif Principal

**BULL SAGE** est un assistant de trading intelligent conçu pour :
- Fournir des analyses de marché en temps réel (crypto + actions + indices)
- Générer des recommandations de trading (BUY/SELL/WAIT) basées sur l'IA
- Permettre aux utilisateurs de s'entraîner sans risque via le Paper Trading
- Éduquer les traders débutants via une Academy gamifiée
- Automatiser la recherche d'opportunités sur tous les marchés

## 1.3 Vision

> *"Démocratiser l'accès aux outils de trading professionnels et à l'intelligence artificielle pour permettre à chaque utilisateur de prendre des décisions de trading informées et rentables."*

## 1.4 Public Cible

| Profil | Description | Besoins |
|--------|-------------|---------|
| **Trader Débutant** | Novice souhaitant apprendre | Formation, Paper Trading, Conseils IA |
| **Trader Intermédiaire** | Expérience basique | Analyses techniques, Signaux, Alertes |
| **Trader Confirmé** | Expérimenté cherchant l'automatisation | Scanner IA, Auto-Trading, Multi-marchés |
| **Investisseur Long Terme** | Focus sur les tendances | News, Indices, Analyses fondamentales |

---

# 2. FONCTIONNALITÉS DÉTAILLÉES

## 2.1 Module Dashboard

### Description
Page d'accueil centralisant toutes les informations essentielles du marché.

### Fonctionnalités
- **Prix Crypto en temps réel** : Top 10 cryptomonnaies avec variation 24h
- **Fear & Greed Index** : Indicateur de sentiment du marché (0-100)
- **News Impact** : Dernières actualités avec analyse IA de l'impact
- **Résumé Portfolio** : Valeur totale et performance Paper Trading
- **Signaux Actifs** : Dernières recommandations de trading

### Données affichées
```
┌─────────────────────────────────────────────────────────────┐
│  DASHBOARD                                                   │
├─────────────────────────────────────────────────────────────┤
│  💰 Bitcoin      $87,914    ▲ +1.2%                         │
│  💎 Ethereum     $2,947     ▼ -0.8%                         │
│  ☀️ Solana       $124       ▲ +2.1%                         │
├─────────────────────────────────────────────────────────────┤
│  😨 Fear & Greed: 24 (EXTREME FEAR)                         │
├─────────────────────────────────────────────────────────────┤
│  📰 NEWS IMPACT                                              │
│  "Fed maintient les taux..." → Impact: NEUTRE               │
└─────────────────────────────────────────────────────────────┘
```

---

## 2.2 Module Scanner IA Unifié 🔍

### Description
Scanner intelligent analysant TOUS les marchés (crypto + actions + indices) pour identifier les meilleures opportunités de trading du moment.

### Fonctionnalités
- **Scan Multi-Marchés** : Cryptos, Actions US, ETF Indices
- **Scoring Automatique** : Algorithme de notation des opportunités
- **Recommandation IA** : GPT-4o analyse et recommande le meilleur trade
- **Filtres Personnalisables** : Activer/désactiver chaque type d'actif

### Actifs Scannés

| Type | Actifs |
|------|--------|
| **Cryptos** | BTC, ETH, SOL, XRP, ADA, DOGE, AVAX, DOT, LINK, LTC |
| **Actions US** | AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, AMD, COIN, MSTR |
| **Indices ETF** | QQQ (NASDAQ), SPY (S&P 500), DIA (Dow Jones), IWM (Russell) |

### Algorithme de Scoring
```
Score = Position Prix + Variation 24h + Signaux Techniques

Position Prix:
  - Prix proche du bas 24h → +3 points
  - Prix en zone basse → +1 point
  - Prix proche du haut → -2 points

Variation 24h:
  - Baisse > 5% → +2 points (rebond potentiel)
  - Hausse > 5% → -1 point (surchauffe)

Action:
  - Score ≥ 2 → BUY
  - Score ≤ -2 → SELL
  - Sinon → WATCH
```

---

## 2.3 Module Mode Trading 📈

### Description
Interface d'analyse technique avancée pour étudier un actif en profondeur.

### Fonctionnalités
- **Sélection d'actif** : Crypto ou Action
- **Analyse Technique IA** : RSI, MACD, Moyennes Mobiles
- **Recommandation Détaillée** : BUY/SELL/WAIT avec justification
- **Niveaux Clés** : Support et Résistance identifiés
- **Score de Confiance** : Probabilité de succès du trade

### Output Exemple
```json
{
  "symbol": "BTC",
  "recommendation": "BUY",
  "confidence": 78,
  "entry_price": 87500,
  "target_price": 92000,
  "stop_loss": 85000,
  "risk_reward": "1:2.5",
  "signals": [
    "RSI en zone de survente (28)",
    "MACD croisement haussier imminent",
    "Prix sur support majeur"
  ]
}
```

---

## 2.4 Module Paper Trading 💵

### Description
Simulateur de trading permettant de s'entraîner avec un capital virtuel sans risquer d'argent réel.

### Fonctionnalités
- **Capital Initial** : $10,000 virtuels
- **Trading Multi-Actifs** : Cryptos + Actions + Indices
- **Historique des Trades** : Suivi complet de chaque transaction
- **Performance** : P&L, Win Rate, Meilleur/Pire trade
- **Portfolio Temps Réel** : Valeur actualisée avec les prix live

### Types de Trades
- **BUY** : Achat d'un actif
- **SELL** : Vente d'un actif détenu

### Calculs
```
Valeur Position = Quantité × Prix Actuel
P&L = (Prix Actuel - Prix Achat) × Quantité
Win Rate = Trades Gagnants / Total Trades × 100
```

---

## 2.5 Module Graphique TradingView 📊

### Description
Interface de charting professionnelle avec chandeliers japonais et données temps réel.

### Fonctionnalités
- **Chandeliers Japonais** : Visualisation OHLC
- **Timeframes Multiples** : 1m, 5m, 15m, 1H, 4H, 1D
- **Sélecteur de Paires** : Top cryptos disponibles
- **Données Temps Réel** : Prix, variation, volume 24h
- **High/Low 24h** : Niveaux extrêmes de la journée

### Timeframes Disponibles

| Intervalle | Usage | Refresh |
|------------|-------|---------|
| 1 minute | Scalping | Manuel |
| 5 minutes | Day Trading | Manuel |
| 15 minutes | Intraday | Manuel |
| 1 heure | Swing Trading | Manuel |
| 4 heures | Position Trading | Manuel |
| 1 jour | Investissement | Manuel |

---

## 2.6 Module Smart Invest 🎯

### Description
Outil d'investissement intelligent recommandant les meilleures opportunités basées sur l'analyse IA.

### Fonctionnalités
- **Analyse de Marché** : Tendance générale du marché
- **Top Opportunités** : Actifs avec le meilleur potentiel
- **Risk Assessment** : Évaluation du risque par actif
- **Allocation Suggérée** : Répartition optimale du capital

---

## 2.7 Module Auto-Trading 🤖

### Description
Système de trading automatisé basé sur des règles prédéfinies et l'analyse IA.

### Fonctionnalités
- **Configuration des Règles** : Conditions d'entrée/sortie
- **Stop-Loss Automatique** : Protection contre les pertes
- **Take-Profit** : Prise de bénéfices automatique
- **Scan Périodique** : Recherche d'opportunités toutes les 15 minutes
- **Notifications** : Alertes sur les trades exécutés

### Paramètres Configurables
```
- Montant par trade : $100 - $10,000
- Stop-Loss : 2% - 10%
- Take-Profit : 5% - 50%
- Nombre max de positions : 1-10
- Cryptos autorisées : Liste personnalisable
```

---

## 2.8 Module Actualités & Indices 📰

### Description
Agrégateur de news financières et suivi des indices boursiers majeurs.

### Fonctionnalités
- **News en Temps Réel** : Actualités de Finnhub et Marketaux
- **Indices US** : NASDAQ 100, S&P 500, Dow Jones, Russell 2000
- **Filtres par Catégorie** : Général, Forex, Crypto, Économie
- **Calendrier Économique** : Événements à venir (Fed, emploi, etc.)

### Sources de Données
- Finnhub (news financières)
- Marketaux (news supplémentaires)
- Alpha Vantage (prix indices)

---

## 2.9 Module Academy 🎓

### Description
Plateforme éducative gamifiée pour apprendre le trading.

### Fonctionnalités
- **Modules de Formation** : Du débutant à l'expert
- **Quiz Interactifs** : Validation des connaissances
- **Système de Points** : XP et niveaux
- **Badges** : Récompenses pour les accomplissements
- **Progression** : Suivi de l'avancement

### Parcours de Formation
```
1. 📚 Les Bases du Trading
   - Qu'est-ce que le trading ?
   - Les différents marchés
   - Vocabulaire essentiel

2. 📊 Analyse Technique
   - Chandeliers japonais
   - Support et Résistance
   - Indicateurs (RSI, MACD)

3. 📰 Analyse Fondamentale
   - Lire les news
   - Impact des événements
   - Sentiment de marché

4. 💰 Gestion du Risque
   - Position sizing
   - Stop-loss et Take-profit
   - Money management

5. 🤖 Trading Automatisé
   - Algorithmes de base
   - Backtesting
   - Optimisation
```

---

## 2.10 Module Assistant IA 💬

### Description
Chatbot IA conversationnel pour répondre aux questions de trading.

### Fonctionnalités
- **Questions/Réponses** : Dialogue naturel sur le trading
- **Analyse à la Demande** : "Que penses-tu de Bitcoin ?"
- **Conseils Personnalisés** : Basés sur le contexte du marché
- **Historique** : Conservation des conversations

### Exemples de Questions
```
- "Quel est le meilleur moment pour acheter ETH ?"
- "Explique-moi le RSI"
- "Que penses-tu du marché actuellement ?"
- "Donne-moi une stratégie pour débutant"
```

---

## 2.11 Module Journal de Trading 📓

### Description
Carnet de bord pour documenter et analyser ses trades.

### Fonctionnalités
- **Enregistrement des Trades** : Entrée, sortie, résultat
- **Notes et Commentaires** : Réflexions personnelles
- **Émotions** : Suivi de l'état psychologique
- **Statistiques** : Performance globale et par période

---

## 2.12 Module Alertes 🔔

### Description
Système de notifications pour ne pas manquer les opportunités.

### Types d'Alertes
- **Alerte de Prix** : Notification quand un actif atteint un niveau
- **Alerte de Signal** : Nouveau signal de trading généré
- **Alerte News** : Actualité importante détectée

---

## 2.13 Module DeFi 🌐

### Description
Outils pour le trading décentralisé et les wallets crypto.

### Fonctionnalités

#### Wallets DeFi
- **Connexion Wallet** : Phantom (Solana), MetaMask (EVM)
- **Suivi Balance** : Solde en temps réel
- **Multi-Chain** : Solana, Ethereum, Polygon, BSC

#### Scanner DeFi
- **Scan DEX** : Tokens tendance sur les exchanges décentralisés
- **Scoring** : Évaluation du potentiel (Hot, Trending, Watch)
- **Sources** : GeckoTerminal, DexScreener

---

## 2.14 Module Administration 👑

### Description
Interface d'administration pour les gestionnaires de la plateforme.

### Fonctionnalités
- **Gestion Utilisateurs** : CRUD complet
- **Promotion Admin** : Attribuer les droits admin
- **Configuration Newsletter** : Paramètres SMTP
- **Statistiques Plateforme** : Nombre d'utilisateurs, trades, etc.

---

# 3. ARCHITECTURE TECHNIQUE

## 3.1 Stack Technologique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| **Frontend** | React.js | 18.x |
| **UI Components** | Shadcn/UI + TailwindCSS | Latest |
| **Backend** | FastAPI (Python) | 0.100+ |
| **Base de Données** | MongoDB | 6.x |
| **IA/LLM** | GPT-4o via Emergent | Latest |
| **Graphiques** | Lightweight Charts | 4.x |
| **Authentification** | JWT | - |

## 3.2 APIs Externes

| API | Usage | Coût |
|-----|-------|------|
| **Kraken** | Prix crypto, OHLC | Gratuit, illimité |
| **Alpha Vantage** | Actions, Indices | Gratuit, 25 req/jour |
| **Finnhub** | News financières | Gratuit, 60 req/min |
| **Marketaux** | News supplémentaires | Gratuit, 100 req/jour |
| **Emergent LLM** | Analyses IA (GPT-4o) | Selon balance |

## 3.3 Schéma d'Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      UTILISATEUR                             │
│                    (Navigateur Web)                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │Dashboard│ │ Scanner │ │ Trading │ │ Academy │  ...       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS (/api)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    API Router                        │   │
│  │  /auth  /market  /scanner  /paper-trading  /admin   │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                   │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐               │
│  │  Services │  │   Cache   │  │    IA     │               │
│  │  (APIs)   │  │ (In-mem)  │  │ (GPT-4o)  │               │
│  └───────────┘  └───────────┘  └───────────┘               │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ MongoDB  │   │  Kraken  │   │ Finnhub  │
    │ (Data)   │   │  (Crypto)│   │  (News)  │
    └──────────┘   └──────────┘   └──────────┘
```

---

# 4. MODÈLE DE DONNÉES

## 4.1 Collection `users`

```javascript
{
  id: "uuid",
  email: "user@example.com",
  password: "hashed_password",
  name: "John Doe",
  is_admin: false,
  profile_image_url: "/uploads/avatars/xxx.jpg",
  trading_level: "intermediate",
  paper_balance: 10000.0,
  newsletter_subscribed: true,
  preferences: {
    theme: "dark",
    notifications: true,
    favorite_cryptos: ["BTC", "ETH"]
  },
  created_at: "2024-12-01T00:00:00Z",
  onboarding_completed: true
}
```

## 4.2 Collection `paper_trades`

```javascript
{
  id: "uuid",
  user_id: "user_uuid",
  symbol: "bitcoin",
  type: "buy",
  amount: 0.5,
  price: 87000,
  total: 43500,
  timestamp: "2024-12-22T10:30:00Z",
  status: "completed"
}
```

## 4.3 Collection `signals`

```javascript
{
  id: "uuid",
  symbol: "BTC",
  type: "BUY",
  entry_price: 87500,
  target_price: 92000,
  stop_loss: 85000,
  confidence: 78,
  signals: ["RSI oversold", "MACD bullish"],
  created_at: "2024-12-22T14:00:00Z",
  status: "active"
}
```

## 4.4 Collection `alerts`

```javascript
{
  id: "uuid",
  user_id: "user_uuid",
  symbol: "ETH",
  condition: "price_above",
  value: 3000,
  triggered: false,
  created_at: "2024-12-22T09:00:00Z"
}
```

---

# 5. SÉCURITÉ

## 5.1 Authentification

- **JWT Tokens** : Expiration 24h
- **Password Hashing** : Bcrypt avec salt
- **Protected Routes** : Middleware de vérification

## 5.2 Autorisation

- **Rôles** : User, Admin
- **Routes Admin** : Vérification `is_admin`
- **CORS** : Configuration restrictive en production

## 5.3 Données Sensibles

- **API Keys** : Stockées en variables d'environnement
- **Passwords** : Jamais stockés en clair
- **Tokens** : Non exposés dans les logs

---

# 6. PERFORMANCE

## 6.1 Optimisations Implémentées

| Optimisation | Description |
|--------------|-------------|
| **Cache Crypto** | 10 minutes TTL |
| **Cache Charts** | 2 minutes TTL |
| **Pas d'Auto-Refresh** | Chargement sur action utilisateur |
| **API Kraken** | Gratuite et illimitée |
| **Lazy Loading** | Composants chargés à la demande |

## 6.2 Métriques Cibles

- **Temps de Chargement** : < 3 secondes
- **Temps de Réponse API** : < 500ms
- **Disponibilité** : 99.9%

---

# 7. ÉVOLUTIONS FUTURES

## 7.1 Court Terme (P1)

- [ ] Indicateurs techniques sur graphique (RSI, MACD, Bollinger)
- [ ] Stop-loss automatique pour Auto-Trading
- [ ] Notifications push (Telegram/SMS)

## 7.2 Moyen Terme (P2)

- [ ] Intégration exchange réel (Binance, Kraken)
- [ ] Backtesting de stratégies
- [ ] Application mobile (React Native)

## 7.3 Long Terme (P3)

- [ ] Social Trading (copier les meilleurs traders)
- [ ] Marketplace de stratégies
- [ ] API publique pour développeurs

---

# 8. GLOSSAIRE

| Terme | Définition |
|-------|------------|
| **BUY** | Signal d'achat |
| **SELL** | Signal de vente |
| **WAIT** | Attendre, pas d'action |
| **Paper Trading** | Trading simulé sans argent réel |
| **OHLC** | Open, High, Low, Close (données de chandelier) |
| **RSI** | Relative Strength Index (indicateur de momentum) |
| **MACD** | Moving Average Convergence Divergence |
| **Stop-Loss** | Ordre de vente automatique pour limiter les pertes |
| **Take-Profit** | Ordre de vente automatique pour sécuriser les gains |
| **Fear & Greed** | Indicateur de sentiment du marché (0-100) |
| **DeFi** | Finance Décentralisée |
| **DEX** | Decentralized Exchange |

---

# 9. ANNEXES

## 9.1 Endpoints API Complets

```
AUTH
  POST /api/auth/register
  POST /api/auth/login
  GET  /api/auth/me
  POST /api/auth/logout

MARKET DATA
  GET  /api/market/crypto
  GET  /api/market/fear-greed
  GET  /api/market/news
  GET  /api/market/indices

CHART
  GET  /api/chart/klines/{symbol}
  GET  /api/chart/ticker/{symbol}
  GET  /api/chart/pairs

SCANNER
  POST /api/scanner/unified
  GET  /api/scanner/best-opportunity

PAPER TRADING
  GET  /api/paper-trading/portfolio
  POST /api/paper-trading/trade
  GET  /api/paper-trading/trades
  GET  /api/paper-trading/stats

TRADING
  POST /api/trading/analyze
  GET  /api/trading/signals

ADMIN
  GET  /api/admin/users
  PUT  /api/admin/users/{id}
  DELETE /api/admin/users/{id}
  POST /api/admin/users/{id}/promote
```

## 9.2 Codes d'Erreur

| Code | Message | Description |
|------|---------|-------------|
| 400 | Bad Request | Paramètres invalides |
| 401 | Not Authenticated | Token manquant ou invalide |
| 403 | Forbidden | Accès non autorisé |
| 404 | Not Found | Ressource non trouvée |
| 429 | Rate Limited | Trop de requêtes |
| 500 | Internal Error | Erreur serveur |
| 502 | Bad Gateway | Backend indisponible |
| 503 | Service Unavailable | API externe indisponible |

---

**Document rédigé pour BULL SAGE**  
**© 2024 - Tous droits réservés**
