# Token BST Interne — Spécifications Techniques

**Date de création :** 08/02/2026 00:24
**Développeur :** Jules
**Validation :** Gilles (08/02/2026 00:23)
**Timeline :** Livraison dimanche 09/02/2026 soir

---

## 🎯 Objectif

Créer un **système de token interne gamification** pour BullSage Trader :
- Récompenser l'activité utilisateurs (bons trades, missions, leaderboard)
- Débloquer des features premium
- Créer une économie interne sans blockchain
- Possibilité de migration vers blockchain publique plus tard

---

## 🏗️ Architecture Technique

### Stack
- **Database :** MongoDB existant (`cluster0.bighmiz.mongodb.net/bullsage`)
- **Backend :** Node.js / Express (intégration au backend existant)
- **Frontend :** React (dashboard admin + user)
- **Auth :** JWT existant (pas de nouvelle auth)

### Collection MongoDB

**Nom :** `bst_tokens`

**Schema :**
```javascript
{
  _id: ObjectId,
  user_id: String,           // Référence à l'utilisateur
  balance: Number,           // Solde actuel en BST
  total_earned: Number,      // Total gagné depuis le début
  total_spent: Number,       // Total dépensé depuis le début
  transactions: [
    {
      type: String,          // 'mint', 'transfer', 'burn', 'reward', 'spend'
      amount: Number,        // Montant (positif ou négatif)
      reason: String,        // Raison de la transaction
      timestamp: Date,       // Date/heure
      from: String,          // User ID source (pour transfers)
      to: String,            // User ID destination (pour transfers)
      admin: String          // Admin qui a effectué l'action (si applicable)
    }
  ],
  created_at: Date,
  updated_at: Date
}
```

### Indexation
- `user_id` : unique, index principal
- `transactions.timestamp` : index pour performances des historiques

---

## 🔌 API Endpoints

**Base URL :** `/api/bst`

### 1. **GET /api/bst/balance/:userId**
Récupérer le solde BST d'un utilisateur.

**Auth :** User ou Admin
**Response :**
```json
{
  "user_id": "123456",
  "balance": 1500,
  "total_earned": 2000,
  "total_spent": 500
}
```

### 2. **GET /api/bst/history/:userId**
Récupérer l'historique des transactions BST.

**Auth :** User ou Admin
**Query params :** `?limit=50&offset=0`
**Response :**
```json
{
  "user_id": "123456",
  "transactions": [
    {
      "type": "reward",
      "amount": 100,
      "reason": "Top 10 leaderboard",
      "timestamp": "2026-02-08T12:00:00Z"
    },
    {
      "type": "spend",
      "amount": -50,
      "reason": "Unlock premium feature",
      "timestamp": "2026-02-08T13:00:00Z"
    }
  ]
}
```

### 3. **POST /api/bst/mint**
Créer des tokens BST et les attribuer à un utilisateur.

**Auth :** Admin uniquement
**Body :**
```json
{
  "user_id": "123456",
  "amount": 500,
  "reason": "Welcome bonus"
}
```
**Response :**
```json
{
  "success": true,
  "new_balance": 1500,
  "transaction_id": "txn_abc123"
}
```

### 4. **POST /api/bst/transfer**
Transférer des tokens BST entre utilisateurs.

**Auth :** User (pour ses propres transfers) ou Admin
**Body :**
```json
{
  "from_user_id": "123456",
  "to_user_id": "789012",
  "amount": 100,
  "reason": "Gift"
}
```
**Response :**
```json
{
  "success": true,
  "from_balance": 1400,
  "to_balance": 600
}
```

### 5. **POST /api/bst/burn**
Détruire des tokens BST (retirer du solde utilisateur).

**Auth :** Admin uniquement
**Body :**
```json
{
  "user_id": "123456",
  "amount": 200,
  "reason": "Penalty for violation"
}
```
**Response :**
```json
{
  "success": true,
  "new_balance": 1200
}
```

### 6. **POST /api/bst/reward**
Récompenser un utilisateur avec des tokens BST (alias de mint avec type "reward").

**Auth :** Admin ou système automatique
**Body :**
```json
{
  "user_id": "123456",
  "amount": 50,
  "reason": "Good trade (+5% profit)"
}
```

### 7. **POST /api/bst/spend**
Dépenser des tokens BST (débloquer feature, etc.).

**Auth :** User ou Admin
**Body :**
```json
{
  "user_id": "123456",
  "amount": 100,
  "reason": "Unlock AI premium analysis"
}
```

### 8. **GET /api/bst/leaderboard**
Récupérer le classement des utilisateurs par balance BST.

**Auth :** Public ou User
**Query params :** `?limit=100`
**Response :**
```json
{
  "leaderboard": [
    {
      "user_id": "123456",
      "username": "trader_pro",
      "balance": 5000,
      "rank": 1
    },
    {
      "user_id": "789012",
      "username": "crypto_king",
      "balance": 4500,
      "rank": 2
    }
  ]
}
```

### 9. **GET /api/bst/stats**
Statistiques globales du système BST.

**Auth :** Admin uniquement
**Response :**
```json
{
  "total_supply": 50000,
  "total_users": 120,
  "avg_balance": 416,
  "top_holder": {
    "user_id": "123456",
    "balance": 5000
  }
}
```

---

## 🎨 Interfaces

### Dashboard Admin

**URL :** `/admin/bst`

**Fonctionnalités :**
- Mint des tokens (créer et distribuer)
- Burn des tokens (retirer du solde utilisateur)
- Voir tous les utilisateurs + balances
- Statistiques globales (supply, distribution, etc.)
- Historique de toutes les transactions
- Recherche par user_id

**UI :**
- Tableau de bord avec stats clés (total supply, nb users, avg balance)
- Formulaire mint (user_id, amount, reason)
- Formulaire burn (user_id, amount, reason)
- Table des top holders
- Graphiques de distribution

### Dashboard Utilisateur

**URL :** `/dashboard/bst`

**Fonctionnalités :**
- Voir son solde BST
- Historique de ses transactions
- Leaderboard public
- Possibilité de transférer des tokens (si activé)
- Liste des features premium déblocables avec BST

**UI :**
- Carte avec solde BST en évidence
- Total earned / total spent
- Timeline des transactions récentes
- Section "Débloquer avec BST" (features premium)
- Classement leaderboard avec sa position

---

## 🚀 Fonctionnalités de Gamification

### Récompenses Automatiques

**Idées à implémenter :**
1. **Bon trade** : +50 BST pour chaque trade gagnant >5% profit
2. **Streak** : +100 BST pour 5 jours consécutifs de connexion
3. **Leaderboard** : +500 BST pour Top 10 hebdomadaire
4. **Missions** : Compléter des tâches (ex: faire 10 trades) = +200 BST
5. **Parrainage** : +100 BST pour chaque utilisateur parrainé actif

### Dépenses / Déblocages

**Idées à implémenter :**
1. **AI Premium Analysis** : -100 BST pour analyse IA approfondie
2. **Advanced Indicators** : -500 BST (déblocage permanent)
3. **Custom Alerts** : -200 BST pour 10 alertes personnalisées
4. **Priority Support** : -1000 BST pour support prioritaire 1 mois
5. **Exclusive Webinars** : -300 BST pour accès webinar VIP

---

## 🔐 Sécurité

### Authentification
- Vérifier JWT pour tous les endpoints
- Role-based access : `admin` vs `user`
- User ne peut voir que ses propres données (sauf leaderboard)

### Validation
- Vérifier que `amount > 0` pour mint/transfer/burn
- Vérifier solde suffisant avant transfer/spend
- Vérifier que `user_id` existe avant mint/burn
- Rate limiting sur les endpoints (éviter spam)

### Logs
- Logger toutes les actions admin (mint, burn)
- Logger les transactions importantes (>1000 BST)
- Système d'audit trail

---

## 📊 Migration Future vers Blockchain

**Si décision de migrer vers blockchain publique :**

1. **Snapshot des balances** MongoDB → Export CSV
2. **Créer smart contract** (Solana/Pump.fun ou Ethereum)
3. **Airdrop** aux utilisateurs selon leurs balances actuelles
4. **Ratio conversion** : 1 BST interne = X tokens blockchain
5. **Freeze** du système interne après migration

**Code à prévoir :** Flag `migrated: boolean` dans la collection pour marquer les comptes migrés.

---

## ✅ Checklist Développement

**Backend :**
- [ ] Collection MongoDB `bst_tokens` créée
- [ ] Endpoints API (mint, transfer, burn, balance, history)
- [ ] Middleware auth (vérification JWT + role)
- [ ] Validation des inputs
- [ ] Tests unitaires (Jest)
- [ ] Documentation API (Swagger/Postman)

**Frontend :**
- [ ] Dashboard admin (mint/burn/stats)
- [ ] Dashboard utilisateur (balance/history)
- [ ] Composant Leaderboard
- [ ] UI "Débloquer avec BST"
- [ ] Notifications (toast) pour récompenses/dépenses

**Tests :**
- [ ] Tests backend complets
- [ ] Tests frontend (composants)
- [ ] Tests end-to-end (Cypress/Playwright)
- [ ] Test de charge (vérifier performances avec 1000+ users)

**Documentation :**
- [ ] README.md du système BST
- [ ] Guide admin (comment mint, burn, gérer)
- [ ] Guide utilisateur (comment gagner/dépenser BST)

---

## 📅 Timeline

**Samedi 08/02 :**
- ✅ Specs documentées
- [ ] Backend API complet (endpoints + MongoDB)
- [ ] Tests backend

**Dimanche 09/02 :**
- [ ] Interface admin complète
- [ ] Dashboard utilisateur
- [ ] Tests end-to-end
- [ ] Documentation complète
- [ ] **LIVRAISON : Dimanche soir** ✅

---

**Développeur :** Jules
**Contact :** julescoachdigital@gmail.com
**Validation avant merge :** Gilles obligatoire
**Branche :** `feature/bst-token`
