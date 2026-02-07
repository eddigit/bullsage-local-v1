# 🚀 DÉPLOIEMENT FRONTEND VERCEL — BullSage Trader

**Date :** 07/02/2026 23:20
**Responsable :** Jules
**Token Vercel :** `fQWMWeA7vKDfE97Yfu32x9vX`
**Org :** gilles-korzec-projects

---

## ÉTAPE 1 — Préparer la variable d'environnement frontend

**Variable requise :**
```
REACT_APP_BACKEND_URL=https://bullsage-api.onrender.com
```

---

## ÉTAPE 2 — Créer le projet Vercel via API

**API Vercel :** https://api.vercel.com/v13/deployments

### Méthode 1 — Via CLI Vercel (si installé)
```bash
cd frontend
npx vercel --token fQWMWeA7vKDfE97Yfu32x9vX
```

### Méthode 2 — Via API
```bash
curl -X POST "https://api.vercel.com/v13/deployments" \
  -H "Authorization: Bearer fQWMWeA7vKDfE97Yfu32x9vX" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "bullsage-frontend",
    "gitSource": {
      "type": "github",
      "repo": "eddigit/bullsage-local-v1",
      "ref": "main"
    },
    "projectSettings": {
      "framework": "create-react-app",
      "buildCommand": "npm install --legacy-peer-deps && npm run build",
      "outputDirectory": "build",
      "rootDirectory": "frontend"
    },
    "env": [
      {
        "key": "REACT_APP_BACKEND_URL",
        "value": "https://bullsage-api.onrender.com"
      }
    ]
  }'
```

---

## ÉTAPE 3 — Configuration redirects/rewrites

**Fichier `vercel.json` déjà présent** dans le repo (à la racine)

Contenu :
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

Si besoin de le déplacer dans `frontend/` :
```bash
cp vercel.json frontend/vercel.json
```

---

## ÉTAPE 4 — Lancer le build

Une fois le projet créé sur Vercel, le build se lance automatiquement.

### Vérifier le statut
```bash
curl "https://api.vercel.com/v13/deployments?projectId=XXXXX&limit=1" \
  -H "Authorization: Bearer fQWMWeA7vKDfE97Yfu32x9vX"
```

---

## ALTERNATIVE — Via dashboard web

Si API ne fonctionne pas :
1. Aller sur https://vercel.com
2. Se connecter avec gilleskorzec@gmail.com
3. New Project
4. Import Git Repository → `eddigit/bullsage-local-v1`
5. Configurer :
   - Project Name: bullsage-frontend
   - Framework Preset: Create React App
   - Root Directory: frontend
   - Build Command: `npm install --legacy-peer-deps && npm run build`
   - Output Directory: build
6. Environment Variables :
   - `REACT_APP_BACKEND_URL` = `https://bullsage-api.onrender.com`
7. Deploy

---

## ÉTAPE 5 — Tester le frontend

```bash
# Une fois déployé
curl https://bullsage-frontend.vercel.app
```

Ou ouvrir dans le navigateur et vérifier :
- [ ] Page d'accueil charge
- [ ] Dashboard visible
- [ ] Prix crypto affichés (via CoinGecko)
- [ ] Pas d'erreur console

---

## URL FINALE ATTENDUE

`https://bullsage-frontend.vercel.app`

Ou domaine personnalisé si configuré : `bullsagetrader.com`

---

## TROUBLESHOOTING

### Erreur "REACT_APP_BACKEND_URL not defined"
→ Vérifier que la variable d'environnement est bien définie dans Vercel
→ Rebuild le projet

### Erreur 404 sur les routes
→ Vérifier que `vercel.json` avec rewrites est bien présent
→ Redéployer

### Erreur CORS backend
→ Vérifier que le backend autorise l'origine `https://bullsage-frontend.vercel.app`
→ Vérifier config CORS dans `backend/server.py`

---

**✅ CHECKLIST FINALE**

- [ ] Backend Render en ligne et répond
- [ ] Frontend Vercel déployé
- [ ] Dashboard affiche prix crypto
- [ ] Fear & Greed Index visible
- [ ] Pas d'erreur 404/500
- [ ] Screenshot de preuve

---

**Prochaine étape :** Tests complets et documentation (voir DEPLOYMENT-TONIGHT.md)
