# BULL SAGE - Architecture du Backend

## Structure Modulaire

```
/app/backend/
├── server.py              # Serveur principal FastAPI (~5000 lignes)
├── academy_data.py        # Données des leçons Academy (partie 1)
├── academy_data_part2.py  # Données des leçons Academy (partie 2)
├── requirements.txt       # Dépendances Python
├── .env                   # Variables d'environnement
│
├── core/                  # ✅ Configuration centralisée
│   ├── __init__.py
│   ├── config.py         # MongoDB, JWT, API Keys (CryptoCompare, CoinGecko, Binance, Alpha Vantage)
│   └── auth.py           # Authentification JWT
│
├── models/                # ✅ Modèles Pydantic
│   ├── __init__.py
│   └── schemas.py        # User, Signal, Trade, etc.
│
├── services/              # ✅ NOUVEAU - Services métier réutilisables
│   ├── __init__.py
│   ├── market_data.py    # Service de données marché multi-source (CryptoCompare/CoinGecko/Binance)
│   └── technical_analysis.py  # Service d'analyse technique (RSI, MACD, Bollinger, etc.)
│
└── routes/                # Routes modulaires (partiellement utilisées)
    ├── __init__.py
    ├── auth.py, market.py, trading.py, etc.
```

## Sources de Données Marché

### Ordre de priorité (fallback automatique)
1. **CryptoCompare** (Principal) - Gratuit, fiable, pas de rate limit strict, pas de restriction géographique
2. **CoinGecko** (Fallback) - Gratuit mais rate limited (30 req/min)
3. **Binance** (Fallback) - Peut être bloqué géographiquement

### Cache
- TTL de 5 minutes pour les données crypto
- Cache automatique avec fallback sur données périmées si APIs indisponibles

## Services Créés

### MarketDataService (`services/market_data.py`)
- `get_crypto_list()` - Liste des cryptos avec prix temps réel
- `get_historical_prices(coin_id, days)` - Données historiques pour analyse technique
- `get_crypto_prices(symbols)` - Prix actuels pour plusieurs symboles
- `get_stock_data(symbol)` - Données actions via Alpha Vantage

### TechnicalAnalysisService (`services/technical_analysis.py`)
- `calculate_rsi(prices)` - Relative Strength Index
- `calculate_macd(prices)` - Moving Average Convergence Divergence
- `calculate_bollinger_bands(prices)` - Bandes de Bollinger
- `calculate_moving_averages(prices)` - MA20, MA50, MA200
- `calculate_support_resistance(prices)` - Niveaux de support/résistance
- `generate_trading_signal(prices, current_price)` - Signal complet avec score

## API Endpoints Principaux

### Market Data
- `GET /api/market/crypto` - Liste des 20 top cryptos (CryptoCompare)
- `GET /api/market/crypto/{coin_id}` - Détail d'une crypto
- `GET /api/market/intelligence` - Données macro (Fear&Greed, BTC dominance, etc.)
- `GET /api/market/news` - Actualités financières

### Trading
- `POST /api/trading/analyze` - Analyse technique complète d'une crypto
- `POST /api/smart-invest/analyze` - IA recommande le meilleur investissement
- `POST /api/smart-invest/execute` - Exécute le trade en Paper Trading
- `GET /api/trading/briefing` - Morning briefing
- `GET /api/trading/scan-opportunities` - Scan de la watchlist

## Statut
- ✅ Données temps réel via CryptoCompare (source fiable)
- ✅ Analyse technique complète
- ✅ Smart Invest fonctionnel (crypto + stocks)
- ✅ Aucune donnée mockée
- ✅ Gestion automatique des fallbacks API
