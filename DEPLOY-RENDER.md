# 🚀 DÉPLOIEMENT BACKEND RENDER — BullSage Trader

**Date :** 07/02/2026 23:15
**Responsable :** Jules
**Token Render :** `rnd_w9EC1OhI929hCW4QdC62gMSiy2Dq`

---

## ÉTAPE 1 — Préparer les variables d'environnement

**Fichier `.env` déjà créé** dans `backend/.env`

**Variables requises :**
```bash
MONGO_URL=mongodb+srv://bullsage:PASSWORD@cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=bullsage
JWT_SECRET=BullSage2026SecureJWTToken!RandomGenerated789
ANTHROPIC_API_KEY=sk-ant-api03-XXXXX
COINGECKO_API_URL=https://api.coingecko.com/api/v3
ALPHA_VANTAGE_API_KEY=XXXXX
FINNHUB_API_KEY=XXXXX
FRED_API_KEY=XXXXX
```

---

## ÉTAPE 2 — Créer le service Render via API

**API Render :** https://api.render.com/v1/services

### Request Body
```json
{
  "type": "web_service",
  "name": "bullsage-api",
  "repo": "https://github.com/eddigit/bullsage-local-v1",
  "branch": "main",
  "rootDir": "backend",
  "runtime": "python",
  "buildCommand": "pip install -r requirements.txt",
  "startCommand": "uvicorn server:app --host 0.0.0.0 --port $PORT",
  "envVars": [
    {"key": "MONGO_URL", "value": "PLACEHOLDER"},
    {"key": "DB_NAME", "value": "bullsage"},
    {"key": "JWT_SECRET", "value": "BullSage2026SecureJWTToken!RandomGenerated789"},
    {"key": "COINGECKO_API_URL", "value": "https://api.coingecko.com/api/v3"}
  ]
}
```

### Commande cURL
```bash
curl -X POST "https://api.render.com/v1/services" \
  -H "Authorization: Bearer rnd_w9EC1OhI929hCW4QdC62gMSiy2Dq" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "web_service",
    "name": "bullsage-api",
    "repo": "https://github.com/eddigit/bullsage-local-v1",
    "branch": "main",
    "rootDir": "backend",
    "runtime": "python",
    "buildCommand": "pip install -r requirements.txt",
    "startCommand": "uvicorn server:app --host 0.0.0.0 --port $PORT",
    "envVars": [
      {"key": "MONGO_URL", "value": "PLACEHOLDER"},
      {"key": "DB_NAME", "value": "bullsage"},
      {"key": "JWT_SECRET", "value": "BullSage2026SecureJWTToken!RandomGenerated789"}
    ]
  }'
```

---

## ÉTAPE 3 — Mettre à jour les variables d'environnement

Une fois le service créé, récupérer le `serviceId` et mettre à jour les env vars :

```bash
SERVICE_ID=srv_XXXXX  # À récupérer de la création

curl -X PUT "https://api.render.com/v1/services/${SERVICE_ID}/env-vars" \
  -H "Authorization: Bearer rnd_w9EC1OhI929hCW4QdC62gMSiy2Dq" \
  -H "Content-Type: application/json" \
  -d '{
    "MONGO_URL": "mongodb+srv://...",
    "ALPHA_VANTAGE_API_KEY": "XXXXX",
    "FINNHUB_API_KEY": "XXXXX",
    "FRED_API_KEY": "XXXXX"
  }'
```

---

## ÉTAPE 4 — Déclencher le déploiement

```bash
curl -X POST "https://api.render.com/v1/services/${SERVICE_ID}/deploys" \
  -H "Authorization: Bearer rnd_w9EC1OhI929hCW4QdC62gMSiy2Dq"
```

---

## ÉTAPE 5 — Vérifier le build

### Récupérer les logs
```bash
curl "https://api.render.com/v1/services/${SERVICE_ID}/deploys" \
  -H "Authorization: Bearer rnd_w9EC1OhI929hCW4QdC62gMSiy2Dq"
```

### Tester l'API
```bash
# Une fois déployé
curl https://bullsage-api.onrender.com/
# ou
curl https://bullsage-api.onrender.com/api/health
```

---

## ALTERNATIVE — Via dashboard web

Si API ne fonctionne pas :
1. Aller sur https://dashboard.render.com
2. Se connecter avec gilleskorzec@gmail.com / $$Reussite888!!
3. New → Web Service
4. Connect repo `eddigit/bullsage-local-v1`
5. Configurer :
   - Name: bullsage-api
   - Root Directory: backend
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
6. Ajouter les variables d'environnement
7. Create Web Service

---

## URL FINALE ATTENDUE

`https://bullsage-api.onrender.com`

---

**Prochaine étape :** Déployer le frontend sur Vercel (voir DEPLOY-VERCEL.md)
