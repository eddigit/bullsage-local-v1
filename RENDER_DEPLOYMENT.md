# Bull Sage - Guide de Deploiement Render

## Services a deployer

1. **bullsage-api** (Backend FastAPI)
2. **bullsage-dydx-executor** (Node.js dYdX Executor)
3. **bullsage-frontend** (React Frontend) - si applicable

---

## 1. Backend (bullsage-api)

### Variables d'environnement REQUISES

```env
# ===== MongoDB =====
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=bullsage

# ===== Authentification =====
JWT_SECRET=GENERER_UNE_CLE_ALEATOIRE_64_CHARS

# ===== CORS =====
CORS_ORIGINS=https://bullsagetrader.com,https://www.bullsagetrader.com,https://bullsage-frontend.onrender.com

# ===== dYdX Executor =====
DYDX_EXECUTOR_URL=https://bullsage-dydx-executor.onrender.com
DYDX_API_SECRET=VOTRE_SECRET_API_PARTAGE

# ===== Webhook Automatisation =====
CLAUDE_WEBHOOK_TOKEN=GENERER_TOKEN_SECURISE_64_CHARS

# ===== Trading Configuration =====
MAX_RISK_PERCENT=2.0
MAX_LEVERAGE=10
MIN_CONFIDENCE=80
TRADE_COOLDOWN_SECONDS=60
MAX_SLIPPAGE_PERCENT=1.0
ALLOWED_MARKETS=BTC-USD,ETH-USD,SOL-USD,AVAX-USD,DOGE-USD,XRP-USD,ADA-USD
TRADING_ENABLED=true
```

### Variables d'environnement OPTIONNELLES (APIs)

```env
# ===== LLM / IA =====
XAI_API_KEY=votre_cle_xai
OPENAI_API_KEY=votre_cle_openai
OPENROUTER_API_KEY=votre_cle_openrouter
ANTHROPIC_API_KEY=votre_cle_anthropic

# ===== APIs Financieres =====
ALPHA_VANTAGE_API_KEY=votre_cle
FINNHUB_API_KEY=votre_cle
FRED_API_KEY=votre_cle
MARKETAUX_API_KEY=votre_cle
COINGECKO_API_URL=https://api.coingecko.com/api/v3
```

### Commande de demarrage

```
uvicorn server:app --host 0.0.0.0 --port $PORT
```

---

## 2. dYdX Executor (bullsage-dydx-executor)

### Variables d'environnement REQUISES

```env
# ===== dYdX Testnet =====
DYDX_TESTNET_MNEMONIC=vos 24 mots du wallet testnet
DYDX_TESTNET_ADDRESS=dydx1votre_adresse_testnet

# ===== Securite =====
DYDX_API_SECRET=MEME_SECRET_QUE_BACKEND
NODE_ENV=production

# ===== Trading Configuration =====
MAX_SLIPPAGE_PERCENT=1.0
TRADE_COOLDOWN_SECONDS=60
ALLOWED_MARKETS=BTC-USD,ETH-USD,SOL-USD,AVAX-USD,DOGE-USD,XRP-USD,ADA-USD
```

### Variables pour MAINNET (quand pret)

```env
# ===== dYdX Mainnet =====
DYDX_MAINNET_MNEMONIC=vos 24 mots du wallet mainnet
DYDX_MAINNET_ADDRESS=dydx1votre_adresse_mainnet
DYDX_NETWORK=mainnet
```

### Commande de demarrage

```
npm start
```

---

## 3. Frontend (si deploye separement)

### Variables d'environnement

```env
REACT_APP_BACKEND_URL=https://bullsage-api.onrender.com
```

---

## Checklist Pre-Deploiement

### Securite

- [ ] Regenerer TOUTES les cles API exposees dans l'audit
- [ ] Generer un nouveau JWT_SECRET (64 caracteres)
- [ ] Generer un nouveau CLAUDE_WEBHOOK_TOKEN (64 caracteres)
- [ ] Generer un nouveau DYDX_API_SECRET (32 caracteres)
- [ ] Verifier que .env n'est PAS dans le repo git

### Configuration

- [ ] CORS_ORIGINS configure avec les bons domaines
- [ ] DYDX_EXECUTOR_URL pointe vers le bon service Render
- [ ] MongoDB Atlas configure et accessible
- [ ] Index MongoDB crees (executer create_indexes.py)

### Tests

- [ ] Backend demarre sans erreur
- [ ] dYdX Executor se connecte au testnet
- [ ] Webhook /health repond OK
- [ ] Frontend peut appeler le backend

---

## Commandes utiles

### Generer des secrets securises

```bash
# JWT_SECRET (64 chars)
python -c "import secrets; print(secrets.token_hex(32))"

# CLAUDE_WEBHOOK_TOKEN (64 chars)
python -c "import secrets; print(secrets.token_hex(32))"

# DYDX_API_SECRET (32 chars)
python -c "import secrets; print(secrets.token_hex(16))"
```

### Creer les index MongoDB

```bash
cd backend
python scripts/create_indexes.py
```

### Tester les webhooks

```bash
cd backend
python scripts/test_webhook.py --url https://bullsage-api.onrender.com --token VOTRE_TOKEN
```

---

## URLs de Production

| Service | URL |
|---------|-----|
| Backend API | https://bullsage-api.onrender.com |
| dYdX Executor | https://bullsage-dydx-executor.onrender.com |
| Frontend | https://bullsagetrader.com |

---

## Endpoints a tester apres deploiement

```bash
# Health check backend
curl https://bullsage-api.onrender.com/api/health

# Health check dYdX
curl https://bullsage-dydx-executor.onrender.com/health

# Health check webhook
curl -H "X-Claude-Token: VOTRE_TOKEN" \
  https://bullsage-api.onrender.com/api/webhook/health
```

---

*Documentation de deploiement - Bull Sage v2.0*
