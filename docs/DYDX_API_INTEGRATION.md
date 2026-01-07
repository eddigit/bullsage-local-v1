# 🐂 BULL SAGE - Documentation API dYdX v4

## Connexion à dYdX Testnet pour Robot Trader

Ce document explique comment connecter votre robot trader à la plateforme dYdX via Bull Sage.

---

## 📋 Informations de Connexion

### Environnement
| Paramètre | Valeur |
|-----------|--------|
| **Réseau** | dYdX v4 Testnet |
| **Chain ID** | `dydx-testnet-4` |
| **Indexer API** | `https://indexer.v4testnet.dydx.exchange` |
| **Validator API** | `https://test-dydx.kingnodes.com` |
| **WebSocket** | `wss://indexer.v4testnet.dydx.exchange/v4/ws` |
| **Faucet** | https://v4.testnet.dydx.exchange (bouton "Get Test Tokens") |

---

## 🔑 Configuration des Secrets

### Variables d'environnement requises

```env
# ============================================
# CONFIGURATION DYDX TESTNET
# ============================================

# Mnemonic de votre wallet dYdX (24 mots)
# ⚠️ NE JAMAIS PARTAGER - Garder secret !
DYDX_TESTNET_MNEMONIC=word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15 word16 word17 word18 word19 word20 word21 word22 word23 word24

# Adresse du wallet (commence par dydx1...)
DYDX_TESTNET_ADDRESS=dydx1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Réseau (testnet ou mainnet)
DYDX_NETWORK=testnet

# Port du serveur d'exécution (défaut: 3001)
DYDX_EXECUTOR_PORT=3001

# URL du serveur d'exécution dYdX
DYDX_EXECUTOR_URL=http://localhost:3001

# Clé API secrète pour sécuriser les appels (générez-en une unique)
DYDX_API_SECRET=votre_cle_api_secrete_unique_32_caracteres
```

---

## 🔌 API Endpoints Bull Sage

### URL de base
- **Local**: `http://localhost:3001`
- **Production**: `https://bullsage-dydx-executor.onrender.com`

### Authentification
Ajoutez le header `X-API-Key` avec votre `DYDX_API_SECRET` :
```
X-API-Key: votre_cle_api_secrete
```

---

## 📡 Endpoints Disponibles

### 1. Statut de connexion
```http
GET /status
```

**Réponse:**
```json
{
  "connected": true,
  "wallet": "dydx1abc...xyz",
  "equity": 10000.50,
  "network": "testnet"
}
```

---

### 2. Prix des marchés
```http
GET /prices
```

**Réponse:**
```json
{
  "prices": {
    "BTC-USD": 97500.25,
    "ETH-USD": 3450.80,
    "SOL-USD": 195.50
  }
}
```

---

### 3. Positions ouvertes
```http
GET /positions
```

**Réponse:**
```json
{
  "positions": [
    {
      "market": "BTC-USD",
      "size": "0.001",
      "entryPrice": "96000",
      "side": "LONG"
    }
  ]
}
```

---

### 4. Positions détaillées (avec PnL)
```http
GET /positions/detailed
```

**Réponse:**
```json
{
  "wallet": "dydx1abc...xyz",
  "equity": 10000.50,
  "freeCollateral": 8500.00,
  "positions": [
    {
      "market": "BTC-USD",
      "side": "LONG",
      "size": 0.001,
      "entryPrice": 96000,
      "currentPrice": 97500,
      "unrealizedPnl": 1.50,
      "pnlPercent": 1.56,
      "hasProtection": true,
      "stopLoss": { "price": 94000 },
      "takeProfit": { "price": 100000 }
    }
  ]
}
```

---

### 5. Exécuter un signal de trading
```http
POST /execute
Content-Type: application/json
X-API-Key: votre_cle_api_secrete
```

**Body (Mode MARKET - exécution immédiate):**
```json
{
  "market": "BTC-USD",
  "direction": "LONG",
  "size": 0.001,
  "entry": 97000,
  "stopLoss": 95000,
  "takeProfit": 102000,
  "entryMode": "market",
  "sizeMode": "fixed",
  "metadata": {
    "trade_type": "INTRADAY",
    "confidence": 85,
    "source": "robot_trader"
  }
}
```

**Body (Mode PULLBACK - attendre le prix d'entrée):**
```json
{
  "market": "BTC-USD",
  "direction": "LONG",
  "size": 0.001,
  "entry": 95500,
  "stopLoss": 94000,
  "takeProfit": 102000,
  "entryMode": "pullback",
  "pullbackExpirationHours": 4,
  "sizeMode": "fixed",
  "metadata": {
    "trade_type": "SWING",
    "confidence": 80,
    "source": "robot_trader"
  }
}
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `entryMode` | string | `"market"` (défaut) ou `"pullback"` |
| `pullbackExpirationHours` | number | Durée d'attente du pullback en heures (défaut: 4h) |

**Réponse (Mode MARKET):**
```json
{
  "success": true,
  "signal": {
    "market": "BTC-USD",
    "direction": "LONG",
    "size": 0.001
  },
  "orders": [
    { "type": "ENTRY", "success": true, "mode": "market", "price": 97000 },
    { "type": "STOP_LOSS", "success": true, "price": 95000 },
    { "type": "TAKE_PROFIT", "success": true, "price": 102000 }
  ],
  "timestamp": "2026-01-06T15:30:00.000Z"
}
```

**Réponse (Mode PULLBACK):**
```json
{
  "success": true,
  "pullbackMode": true,
  "pullbackInfo": {
    "entryPrice": 95500,
    "currentPrice": 97000,
    "pullbackPercent": 1.55,
    "expiresAt": "2026-01-06T19:30:00.000Z",
    "note": "Les SL/TP seront activés automatiquement quand le pullback sera atteint"
  },
  "pendingSLTP": {
    "stopLoss": 94000,
    "takeProfit": 102000
  },
  "orders": [
    { 
      "type": "ENTRY", 
      "mode": "pullback",
      "price": 95500,
      "currentPrice": 97000,
      "pullbackPercent": 1.55,
      "status": "PENDING_PULLBACK",
      "expiresAt": "2026-01-06T19:30:00.000Z"
    }
  ]
}
```

---

### 6. Protéger une position existante
```http
POST /positions/protect
Content-Type: application/json
X-API-Key: votre_cle_api_secrete
```

**Body:**
```json
{
  "market": "BTC-USD",
  "stopLoss": 95000,
  "takeProfit": 105000,
  "expirationHours": 168
}
```

**Réponse:**
```json
{
  "success": true,
  "market": "BTC-USD",
  "side": "LONG",
  "orders": [
    { "type": "STOP_LOSS", "success": true, "price": 95000 },
    { "type": "TAKE_PROFIT", "success": true, "price": 105000 }
  ],
  "stopLossPercent": "-2.08",
  "takeProfitPercent": "+8.33"
}
```

---

### 7. Fermer une position
```http
POST /positions/close
Content-Type: application/json
X-API-Key: votre_cle_api_secrete
```

**Body:**
```json
{
  "market": "BTC-USD",
  "reason": "robot_signal_exit"
}
```

**Réponse:**
```json
{
  "success": true,
  "market": "BTC-USD",
  "side": "LONG",
  "size": 0.001,
  "closePrice": 98500,
  "cancelledOrders": 2,
  "timestamp": "2026-01-06T16:00:00.000Z"
}
```

---

### 8. Ordres ouverts
```http
GET /orders
```

**Réponse:**
```json
{
  "orders": [
    {
      "id": "abc123",
      "market": "BTC-USD",
      "side": "SELL",
      "price": "95000",
      "size": "0.001",
      "status": "OPEN",
      "type": "LIMIT"
    }
  ]
}
```

---

### 9. Monitoring des positions
```http
GET /monitor
X-API-Key: votre_cle_api_secrete
```

**Réponse:**
```json
{
  "timestamp": "2026-01-06T15:30:00.000Z",
  "positions": [...],
  "alerts": [],
  "actions": [],
  "summary": {
    "totalPositions": 3,
    "protectedPositions": 2,
    "unprotectedPositions": 1
  }
}
```

---

### 10. Liste des pullbacks en attente
```http
GET /pullback/pending
X-API-Key: votre_cle_api_secrete
```

**Réponse:**
```json
{
  "count": 1,
  "pullbacks": [
    {
      "market": "BTC-USD",
      "direction": "LONG",
      "entryPrice": 95500,
      "size": 0.001,
      "stopLoss": 94000,
      "takeProfit": 102000,
      "expiresAt": "2026-01-06T19:30:00.000Z",
      "status": "PENDING"
    }
  ]
}
```

---

### 11. Vérifier et activer les pullbacks exécutés
```http
GET /pullback/check
X-API-Key: votre_cle_api_secrete
```

Cette route vérifie si les ordres pullback ont été exécutés et active automatiquement les SL/TP.

**Réponse:**
```json
{
  "success": true,
  "checked": ["BTC-USD_12345678"],
  "activated": [
    {
      "market": "BTC-USD",
      "stopLoss": 94000,
      "takeProfit": 102000,
      "activatedOrders": [
        { "type": "STOP_LOSS", "price": 94000 },
        { "type": "TAKE_PROFIT", "price": 102000 }
      ]
    }
  ],
  "expired": [],
  "pending": []
}
```

---

### 12. Annuler un pullback
```http
DELETE /pullback/:market
X-API-Key: votre_cle_api_secrete
```

**Exemple:** `DELETE /pullback/BTC-USD`

**Réponse:**
```json
{
  "success": true,
  "message": "Pullback BTC-USD annulé"
}
```

---

## 💻 Exemples de Code

### Python
```python
import requests

API_URL = "http://localhost:3001"
API_KEY = "votre_cle_api_secrete"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Vérifier le statut
status = requests.get(f"{API_URL}/status").json()
print(f"Connecté: {status['connected']}, Equity: ${status['equity']}")

# Exécuter un trade LONG BTC
trade = {
    "market": "BTC-USD",
    "direction": "LONG",
    "size": 0.001,
    "stopLoss": 95000,
    "takeProfit": 102000
}

response = requests.post(
    f"{API_URL}/execute",
    json=trade,
    headers=headers
)

print(f"Trade exécuté: {response.json()}")
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

const API_URL = 'http://localhost:3001';
const API_KEY = 'votre_cle_api_secrete';

const headers = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY
};

// Vérifier le statut
async function checkStatus() {
  const { data } = await axios.get(`${API_URL}/status`);
  console.log(`Connecté: ${data.connected}, Equity: $${data.equity}`);
}

// Exécuter un trade
async function executeTrade() {
  const trade = {
    market: 'BTC-USD',
    direction: 'LONG',
    size: 0.001,
    stopLoss: 95000,
    takeProfit: 102000
  };

  const { data } = await axios.post(`${API_URL}/execute`, trade, { headers });
  console.log('Trade exécuté:', data);
}

checkStatus();
executeTrade();
```

### cURL
```bash
# Vérifier le statut
curl http://localhost:3001/status

# Exécuter un trade
curl -X POST http://localhost:3001/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: votre_cle_api_secrete" \
  -d '{
    "market": "BTC-USD",
    "direction": "LONG",
    "size": 0.001,
    "stopLoss": 95000,
    "takeProfit": 102000
  }'

# Fermer une position
curl -X POST http://localhost:3001/positions/close \
  -H "Content-Type: application/json" \
  -H "X-API-Key: votre_cle_api_secrete" \
  -d '{"market": "BTC-USD", "reason": "manual"}'
```

---

## 🔐 Sécurité

### Bonnes pratiques
1. **Ne jamais exposer le mnemonic** dans le code ou les logs
2. **Utiliser des variables d'environnement** pour tous les secrets
3. **Activer l'authentification API** en production (`X-API-Key`)
4. **Utiliser HTTPS** en production
5. **Limiter les IP autorisées** si possible

### Rotation des clés
```bash
# Générer une nouvelle clé API secrète
openssl rand -hex 32
```

---

## 🌐 Marchés Disponibles (Testnet)

| Marché | Symbole | Taille Min | Levier Max |
|--------|---------|------------|------------|
| Bitcoin | BTC-USD | 0.0001 | 20x |
| Ethereum | ETH-USD | 0.001 | 20x |
| Solana | SOL-USD | 0.01 | 20x |
| Avalanche | AVAX-USD | 0.1 | 20x |
| Dogecoin | DOGE-USD | 10 | 20x |
| Polygon | MATIC-USD | 10 | 20x |
| ... | ... | ... | ... |

---

## 🚀 Démarrage Rapide

### 1. Créer un wallet dYdX Testnet
1. Allez sur https://v4.testnet.dydx.exchange
2. Connectez-vous avec Keplr ou créez un nouveau wallet
3. Récupérez votre **mnemonic** (24 mots) et **adresse**
4. Cliquez sur "Get Test Tokens" pour obtenir des fonds de test

### 2. Configurer les variables
```bash
# Créer le fichier .env
cp dydx-executor/.env.example backend/.env

# Éditer et ajouter vos credentials
nano backend/.env
```

### 3. Démarrer le serveur
```bash
cd dydx-executor
npm install
npm start
```

### 4. Tester la connexion
```bash
curl http://localhost:3001/status
```

---

## 📞 Support

- **Interface dYdX Testnet**: https://v4.testnet.dydx.exchange
- **Documentation dYdX**: https://docs.dydx.exchange
- **Discord dYdX**: https://discord.gg/dydx

---

## ⚠️ Avertissement

> **TESTNET UNIQUEMENT** - Cette configuration est pour le réseau de test.
> Ne pas utiliser de vrais fonds. Pour le mainnet, des configurations
> supplémentaires de sécurité sont requises.

---

*Documentation générée pour Bull Sage - Janvier 2026*
