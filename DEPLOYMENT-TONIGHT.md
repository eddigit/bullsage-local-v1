# 🚀 DÉPLOIEMENT BULLSAGE TRADER — NUIT DU 07/02/2026

**Responsable :** Jules
**Email utilisé :** julescoachdigital@gmail.com
**Mot de passe :** $$Reussite888!!
**Début :** 23:05

---

## ÉTAPE 1 — MONGODB ATLAS (EN COURS)

**URL :** https://www.mongodb.com/cloud/atlas/register

**Actions :**
1. S'inscrire avec julescoachdigital@gmail.com
2. Créer un cluster M0 (gratuit, 512 MB)
3. Créer un utilisateur database (user: bullsage, password: généré)
4. Network Access → Autoriser 0.0.0.0/0 (toutes IPs)
5. Récupérer la connexion string

**Format attendu :**
```
mongodb+srv://bullsage:PASSWORD@cluster.mongodb.net/?retryWrites=true&w=majority
```

**Statut :** ⏳ EN COURS (navigateur non dispo, création manuelle)

---

## ÉTAPE 2 — CLÉS API

### Alpha Vantage
**URL :** https://www.alphavantage.co/support/#api-key
**Email :** julescoachdigital@gmail.com
**Usage :** Actions US + Indicateurs techniques (25 calls/jour gratuit)
**Statut :** ⏳ À créer

### Finnhub
**URL :** https://finnhub.io/register
**Email :** julescoachdigital@gmail.com
**Usage :** News + Sentiment + Calendrier éco (gratuit rate limited)
**Statut :** ⏳ À créer

### FRED (Federal Reserve)
**URL :** https://fred.stlouisfed.org/docs/api/api_key.html
**Email :** julescoachdigital@gmail.com
**Usage :** Données macro (taux Fed, inflation, VIX) — 100% gratuit
**Statut :** ⏳ À créer

---

## ÉTAPE 3 — CONFIGURATION .ENV

**Fichier :** `backend/.env`

```bash
# MongoDB
MONGO_URL=mongodb+srv://bullsage:PASSWORD@cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=bullsage

# Authentification
JWT_SECRET=BullSage2026SecureToken!RandomGenerated

# APIs IA/LLM
# Anthropic Claude (disponible dans TOOLS.md)
ANTHROPIC_API_KEY=sk-ant-api03-... # À récupérer de TOOLS.md

# APIs Crypto
COINGECKO_API_URL=https://api.coingecko.com/api/v3

# APIs Financières
ALPHA_VANTAGE_API_KEY=XXXXX
FINNHUB_API_KEY=XXXXX
FRED_API_KEY=XXXXX

# Frontend
REACT_APP_BACKEND_URL=https://bullsage-api.onrender.com
```

**Statut :** ⏳ En attente des clés API

---

## ÉTAPE 4 — DÉPLOIEMENT BACKEND (RENDER)

**Token Render :** `rnd_w9EC1OhI929hCW4QdC62gMSiy2Dq` (dans TOOLS.md)

**Actions :**
1. Créer web service `bullsage-api`
2. Connecter repo `eddigit/bullsage-local-v1`
3. Root directory: `backend`
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn server:app --host 0.0.0.0 --port $PORT`
6. Ajouter variables d'environnement (.env)
7. Lancer le build

**URL attendue :** https://bullsage-api.onrender.com

**Statut :** ⏳ En attente config .env

---

## ÉTAPE 5 — DÉPLOIEMENT FRONTEND (VERCEL)

**Token Vercel :** `fQWMWeA7vKDfE97Yfu32x9vX` (dans TOOLS.md)

**Actions :**
1. Créer projet `bullsage-frontend`
2. Connecter repo `eddigit/bullsage-local-v1`
3. Root directory: `frontend`
4. Framework: React
5. Build: `npm install --legacy-peer-deps && npm run build`
6. Output: `build`
7. Variable env: `REACT_APP_BACKEND_URL=https://bullsage-api.onrender.com`
8. Redirects: `/*` → `/index.html` (rewrite)

**URL attendue :** https://bullsage-frontend.vercel.app

**Statut :** ⏳ En attente déploiement backend

---

## ÉTAPE 6 — TESTS

**Checklist de vérification :**
- [ ] Backend API répond (GET /api/health ou équivalent)
- [ ] Frontend charge la page d'accueil
- [ ] Dashboard affiche les prix crypto (CoinGecko)
- [ ] Fear & Greed Index visible
- [ ] Aucune erreur console
- [ ] Screenshot de preuve

**Statut :** ⏳ En attente déploiement

---

## TIMELINE ESTIMÉE

| Étape | Durée estimée | Heure fin |
|-------|---------------|-----------|
| MongoDB Atlas | 15 min | 23:20 |
| Clés API (3) | 30 min | 23:50 |
| Config .env | 10 min | 00:00 |
| Deploy backend Render | 45 min | 00:45 |
| Deploy frontend Vercel | 30 min | 01:15 |
| Tests + Screenshots | 30 min | 01:45 |
| **TOTAL** | **2h40** | **01:45** |

**Livrable :** 02:00 du matin → Site en ligne + Preuves visuelles

---

## BLOCAGES POTENTIELS

1. **MongoDB Atlas** → Nécessite validation email (accès julescoachdigital@gmail.com requis)
2. **Clés API** → Certains services ont validation manuelle (rare mais possible)
3. **Build Render** → Possible erreur dépendances Python (à débugger)
4. **Build Vercel** → Possible erreur dépendances React (--legacy-peer-deps devrait gérer)

---

## PROCHAINE ACTION

**MAINTENANT (23:10) :**
Créer compte MongoDB Atlas via interface web (nécessite accès email julescoachdigital@gmail.com)

**UPDATE dans 10 min**
