# 🐂 Bull Sage - dYdX Executor Service

Service Node.js qui exécute les ordres de trading sur dYdX v4.

## 🏗️ Architecture

```
Backend Python (Render/Railway)
        │
        │ HTTP POST /execute
        ▼
dYdX Executor (Node.js)  ◄── Ce service
        │
        │ WebSocket / gRPC
        ▼
    dYdX v4 Chain
```

## 🚀 Déploiement

### En Local

```bash
cd dydx-executor
npm install
node server.js
```

### Sur Render.com

Le service est configuré dans `render.yaml`. Les variables d'environnement nécessaires :

| Variable | Description | Requis |
|----------|-------------|--------|
| `DYDX_TESTNET_MNEMONIC` | Phrase mnémonique du wallet testnet | ✅ |
| `DYDX_TESTNET_ADDRESS` | Adresse du wallet (dydx1...) | ✅ |
| `DYDX_API_SECRET` | Clé d'API pour sécuriser les appels | ✅ (prod) |
| `DYDX_NETWORK` | `testnet` ou `mainnet` | Optionnel |
| `PORT` | Port du serveur (défaut: 3001) | Optionnel |

### Sur Railway

```bash
railway login
railway link
railway up
```

## 📡 API Endpoints

### GET /status
Retourne le statut de connexion à dYdX.

```json
{
  "connected": true,
  "wallet": "dydx1...",
  "equity": 20290.49,
  "network": "testnet"
}
```

### GET /prices
Retourne les prix actuels de BTC, ETH, SOL.

### GET /positions
Retourne les positions ouvertes.

### GET /orders
Retourne les ordres en cours.

### POST /execute
Exécute un signal de trading.

**Headers:**
- `Content-Type: application/json`
- `X-API-Key: <DYDX_API_SECRET>` (requis en production)

**Body:**
```json
{
  "market": "BTC-USD",
  "direction": "LONG",
  "entry": 105000,
  "stopLoss": 103000,
  "takeProfit": 108000,
  "size": 0.001
}
```

**Response:**
```json
{
  "success": true,
  "orders": [
    { "type": "ENTRY", "success": true, "clientId": 12345 },
    { "type": "STOP_LOSS", "success": true, "price": 103000 },
    { "type": "TAKE_PROFIT", "success": true, "price": 108000 }
  ]
}
```

## 🔐 Sécurité

En production (`NODE_ENV=production`), toutes les requêtes vers `/execute` nécessitent un header `X-API-Key` valide.

## 📊 Marchés Supportés

- BTC-USD
- ETH-USD
- SOL-USD
- DOGE-USD
- XRP-USD
- ADA-USD
- MATIC-USD
- AVAX-USD
- LINK-USD
- DOT-USD
- Et plus...

## 🔗 Liens Utiles

- **dYdX Testnet**: https://v4.testnet.dydx.exchange
- **Faucet USDC**: https://faucet.v4testnet.dydx.exchange
- **Documentation dYdX**: https://docs.dydx.exchange
