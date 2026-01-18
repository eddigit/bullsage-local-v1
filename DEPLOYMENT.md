# Guide de Déploiement - Bull Sage

Ce guide vous explique comment déployer Bull Sage gratuitement sur différentes plateformes.

## 🚀 Options de Déploiement Recommandées

### Option 1 : Render.com (Recommandé - Le plus simple)

Render offre un hébergement gratuit avec des URLs de type `votre-app.onrender.com`.

#### Étapes :

1. **Créez un compte sur [Render.com](https://render.com)**

2. **Configurez MongoDB Atlas (Base de données gratuite)**
   - Allez sur [MongoDB Atlas](https://www.mongodb.com/atlas)
   - Créez un cluster gratuit (M0)
   - Créez un utilisateur de base de données
   - Autorisez toutes les IPs (0.0.0.0/0) pour le déploiement
   - Copiez l'URL de connexion

3. **Déployez le Backend**
   - Cliquez sur "New +" → "Web Service"
   - Connectez votre dépôt GitHub
   - Configurez :
     - **Name** : `bullsage-api`
     - **Root Directory** : `backend`
     - **Runtime** : Python 3
     - **Build Command** : `pip install -r requirements.txt`
     - **Start Command** : `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - Ajoutez les variables d'environnement :
     ```
     MONGO_URL=mongodb+srv://...
     DB_NAME=bullsage
     JWT_SECRET=votre_secret_securise
     XAI_API_KEY=votre_cle_xai
     LLM_PROVIDER=xai
     ```
   - Cliquez sur "Create Web Service"

4. **Déployez le Frontend**
   - Cliquez sur "New +" → "Static Site"
   - Configurez :
     - **Name** : `bullsage-frontend`
     - **Root Directory** : `frontend`
     - **Build Command** : `npm install --legacy-peer-deps && npm run build`
     - **Publish Directory** : `build`
   - Ajoutez la variable d'environnement :
     ```
     REACT_APP_BACKEND_URL=https://bullsage-api.onrender.com
     ```
   - Dans "Redirects/Rewrites", ajoutez :
     - Source : `/*`
     - Destination : `/index.html`
     - Action : Rewrite

5. **Vos URLs seront :**
   - Backend : `https://bullsage-api.onrender.com`
   - Frontend : `https://bullsage-frontend.onrender.com`

---

### Option 2 : Railway.app

Railway offre $5/mois de crédit gratuit avec des URLs automatiques.

#### Étapes :

1. **Créez un compte sur [Railway.app](https://railway.app)**

2. **Déployez le Backend**
   - Cliquez sur "New Project" → "Deploy from GitHub repo"
   - Sélectionnez votre repo et le dossier `backend`
   - Ajoutez les variables d'environnement dans l'onglet "Variables"
   - Railway détectera automatiquement Python et utilisera le fichier `railway.toml`

3. **Déployez le Frontend**
   - Créez un nouveau service dans le même projet
   - Sélectionnez le dossier `frontend`
   - Ajoutez `REACT_APP_BACKEND_URL` pointant vers l'URL du backend

4. **Générez les domaines publics**
   - Cliquez sur chaque service → "Settings" → "Generate Domain"

---

### Option 3 : Fly.io

Fly.io offre des ressources gratuites généreuses.

#### Installation CLI :
```powershell
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex
```

#### Déploiement :
```bash
# Backend
cd backend
fly launch --name bullsage-api
fly secrets set MONGO_URL="mongodb+srv://..." DB_NAME="bullsage" JWT_SECRET="votre_secret"
fly deploy

# Frontend  
cd ../frontend
fly launch --name bullsage-frontend
fly deploy
```

---

### Option 4 : Vercel + Railway (Frontend + Backend séparés)

- **Frontend sur Vercel** (optimisé pour React)
- **Backend sur Railway** (pour FastAPI)

```bash
# Frontend
cd frontend
npx vercel

# Configurez REACT_APP_API_URL vers votre backend Railway
```

---

## 📦 Déploiement avec Docker (VPS/Serveur)

Si vous avez accès à un VPS (DigitalOcean, Hetzner, OVH, etc.) :

```bash
# Cloner le projet
git clone https://github.com/votre-repo/bullsage-local-v1.git
cd bullsage-local-v1

# Créer le fichier .env
cp .env.example .env
# Éditez .env avec vos vraies valeurs

# Lancer avec Docker Compose
docker-compose up -d --build
```

L'application sera accessible sur l'IP de votre serveur.

---

## 🗄️ Configuration MongoDB Atlas (Gratuit)

1. Allez sur [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Créez un compte gratuit
3. Créez un cluster "M0 Sandbox" (gratuit, 512 MB)
4. Créez un utilisateur base de données
5. Dans "Network Access", ajoutez `0.0.0.0/0` pour autoriser toutes les connexions
6. Cliquez sur "Connect" → "Connect your application"
7. Copiez l'URL et remplacez `<password>` par votre mot de passe

---

## ⚙️ Variables d'Environnement Requises

| Variable | Description | Obligatoire |
|----------|-------------|-------------|
| `MONGO_URL` | URL de connexion MongoDB | ✅ |
| `DB_NAME` | Nom de la base de données | ✅ |
| `JWT_SECRET` | Clé secrète pour les tokens | ✅ |
| `XAI_API_KEY` | Clé API xAI (Grok) | ✅ |
| `ANTHROPIC_API_KEY` | Clé API Anthropic (Claude) | ❌ |
| `OPENROUTER_API_KEY` | Clé API OpenRouter | ❌ |
| `LLM_PROVIDER` | Provider actif (xai/anthropic/openrouter) | ❌ |
| `REACT_APP_BACKEND_URL` | URL du backend (frontend) | ✅ |
| `COINGECKO_API_URL` | URL API CoinGecko | ❌ |
| `ALPHA_VANTAGE_API_KEY` | Clé Alpha Vantage | ❌ |
| `FINNHUB_API_KEY` | Clé Finnhub | ❌ |

---

## 🔧 Dépannage

### Le frontend ne se connecte pas au backend
- Vérifiez que `REACT_APP_API_URL` pointe vers la bonne URL du backend
- Assurez-vous que le CORS est configuré dans le backend

### Erreur MongoDB
- Vérifiez que l'IP de votre serveur est autorisée dans MongoDB Atlas
- Vérifiez les credentials dans `MONGO_URL`

### Build frontend échoue
- Utilisez `npm install --legacy-peer-deps` pour les dépendances

---

## 🌐 Après le Déploiement

Une fois déployé, vous aurez :
- **Backend** : `https://bullsage-api.onrender.com/api`
- **Frontend** : `https://bullsage-frontend.onrender.com`

Vous pouvez ensuite acheter un nom de domaine et le configurer pour pointer vers ces URLs.
