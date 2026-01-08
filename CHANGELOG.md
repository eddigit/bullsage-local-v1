# Changelog - Bull Sage Platform

Toutes les modifications notables de ce projet sont documentees dans ce fichier.

---

## [2.0.0] - 2025-01-08

### AUDIT & CORRECTIONS MAJEURES

Suite a l'audit complet de la plateforme, les corrections suivantes ont ete implementees.

### Ajoute

#### Systeme Webhook pour Automatisation
- **Nouveau fichier**: `backend/routes/webhook.py`
  - `POST /api/webhook/execute-trade` - Execute un trade avec validation complete
  - `GET /api/webhook/positions` - Recupere les positions ouvertes
  - `GET /api/webhook/signals` - Signaux A/A+ non traites
  - `POST /api/webhook/close-position` - Ferme une position
  - `GET /api/webhook/account-status` - Statut du compte
  - `POST /api/webhook/acknowledge-signal/{id}` - Marque un signal traite
  - `GET /api/webhook/health` - Health check

#### Configuration Trading Centralisee
- **Nouveau fichier**: `backend/config/trading_config.py`
  - `MAX_RISK_PERCENT = 2.0` - Risque max par trade
  - `MAX_LEVERAGE = 10` - Levier maximum
  - `MIN_CONFIDENCE = 80` - Score minimum requis
  - `ALLOWED_MARKETS` - Liste des marches autorises
  - `TRADE_COOLDOWN_SECONDS = 60` - Cooldown entre trades
  - `MAX_SLIPPAGE_PERCENT = 1.0` - Slippage maximum

#### Index MongoDB
- **Nouveau fichier**: `backend/scripts/create_indexes.py`
  - Index sur `user_id` pour: signals, trades, positions, trade_journal
  - Index sur `timestamp` pour logs et journal
  - Index sur `status` pour filtrage rapide
  - Index compose pour requetes frequentes

#### Documentation
- **Nouveau fichier**: `WEBHOOK_API.md` - Documentation complete de l'API webhook
- **Nouveau fichier**: `AUDIT_REPORT.md` - Rapport d'audit complet

### Modifie

#### dYdX Executor (`dydx-executor/server.js`)

**DYD-01: Retry Logic avec Backoff Exponentiel**
```javascript
// Nouvelle fonction withRetry()
async function withRetry(fn, maxRetries = 3, baseDelay = 1000, operationName) {
  // 3 tentatives avec delais: 1s, 2s, 4s
  // Gere: timeout, network errors, rate limiting
}
```

**DYD-03 & DYD-07: Verification Margin Avant Trade**
```javascript
// Nouvelle fonction checkMarginAvailable()
async function checkMarginAvailable(sizeUSDC, market) {
  // Verifie equity et freeCollateral
  // Rejette si margin < 10% de la valeur du trade
}
```

**DYD-05: Gestion Slippage Configurable**
```javascript
// Nouvelle fonction applySlippage()
function applySlippage(price, side, slippagePercent = 1.0) {
  // Applique slippage selon BUY/SELL
}
```

**DYD-06: Ordres SL/TP Corriges**
- Utilisation de `OrderType.LIMIT` avec `OrderTimeInForce.GTT`
- Expiration configurable selon le type de trade
- Note: dYdX v4 n'a pas de STOP_MARKET natif

**DYD-08: Cooldown Entre Trades**
```javascript
// Nouveau tracking par marche
const lastTradeByMarket = new Map();

function checkCooldown(market, cooldownSeconds = 60) {
  // Verifie le delai depuis le dernier trade
}
```

**QUA-03: Meilleure Gestion d'Erreur**
- Codes d'erreur standardises (`NOT_CONNECTED`, `MARKET_NOT_ALLOWED`, etc.)
- Messages d'erreur exploitables
- Logging ameliore avec timestamps

#### Backend Server (`backend/server.py`)
- Ajout de l'import et inclusion du router webhook
- Integration avec la nouvelle configuration trading

### Garde-Fous Implementes

| Garde-Fou | Implementation |
|-----------|----------------|
| Risque max 2% | Calcul automatique et rejet si depasse |
| Stop loss obligatoire | Validation dans webhook |
| Confidence min 80 | Filtrage des signaux |
| Markets autorises | Liste blanche configurable |
| Cooldown 60s | Tracking par marche |
| Margin check | Verification avant execution |
| Slippage max 1% | Application sur prix d'entree |

### Logging

Deux nouvelles collections MongoDB:

**webhook_logs**
```json
{
  "endpoint": "/execute-trade",
  "method": "POST",
  "status": "success",
  "execution_time_ms": 1250,
  "timestamp": "2025-01-08T10:30:00Z"
}
```

**trade_journal**
```json
{
  "market": "BTC-USD",
  "direction": "LONG",
  "entry_price": 95000,
  "stop_loss": 92000,
  "source": "webhook",
  "status": "OPEN"
}
```

### Fichiers Crees

| Fichier | Description |
|---------|-------------|
| `backend/config/__init__.py` | Module config |
| `backend/config/trading_config.py` | Configuration trading |
| `backend/routes/webhook.py` | Routes webhook |
| `backend/scripts/create_indexes.py` | Script index MongoDB |
| `WEBHOOK_API.md` | Documentation API |
| `AUDIT_REPORT.md` | Rapport d'audit |
| `CHANGELOG.md` | Ce fichier |

### Fichiers Modifies

| Fichier | Modifications |
|---------|---------------|
| `dydx-executor/server.js` | Refactoring complet v2.0 |
| `backend/server.py` | Ajout router webhook |

---

## [1.x.x] - Versions Precedentes

### [1.0.0] - Initial Release
- Frontend React avec Tailwind
- Backend FastAPI
- Integration dYdX v4 basique
- Paper trading
- Assistant AI
- Academy

---

## Notes de Migration

### De 1.x vers 2.0

1. **Variables d'environnement**
   Ajouter dans `.env`:
   ```
   CLAUDE_WEBHOOK_TOKEN=votre_token_securise
   MAX_RISK_PERCENT=2.0
   MAX_LEVERAGE=10
   MIN_CONFIDENCE=80
   TRADE_COOLDOWN_SECONDS=60
   MAX_SLIPPAGE_PERCENT=1.0
   ALLOWED_MARKETS=BTC-USD,ETH-USD,SOL-USD,AVAX-USD,DOGE-USD,XRP-USD,ADA-USD
   ```

2. **Creer les index MongoDB**
   ```bash
   cd backend
   python scripts/create_indexes.py
   ```

3. **Redemarrer les services**
   ```bash
   # Backend
   cd backend && python server.py

   # dYdX Executor
   cd dydx-executor && npm start
   ```

---

## Auteurs

- Bull Sage Team
- Claude Code (Audit & Corrections)

---

*Changelog genere automatiquement*
