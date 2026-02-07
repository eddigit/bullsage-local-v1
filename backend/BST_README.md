# 🪙 BST Token System — Documentation Développeur

**Développeur :** Jules  
**Date :** 08/02/2026  
**Version :** 1.0.0 (Phase 1 - Système interne)

---

## 📖 Vue d'ensemble

Le **BST Token System** est un système de gamification interne pour BullSage Trader permettant de :
- Récompenser les utilisateurs pour leur activité (bons trades, missions, leaderboard)
- Permettre de débloquer des features premium avec des tokens BST
- Créer une économie interne sans blockchain
- Migrer vers blockchain publique plus tard si souhaité

---

## 🏗️ Architecture

### Structure des fichiers

```
backend/
├── models/bst/
│   └── BSTToken.js           # Modèle MongoDB (schema + méthodes)
├── controllers/bst/
│   └── bstController.js      # Logique métier (mint, transfer, burn, etc.)
├── routes/bst/
│   └── bstRoutes.js          # Routes Express
├── middleware/bst/
│   └── adminMiddleware.js    # Middleware vérification admin
└── BST_README.md             # Cette documentation
```

### Stack Technique

- **Database :** MongoDB (collection `bst_tokens`)
- **Backend :** Node.js / Express
- **Auth :** JWT (système existant BullSage)
- **Frontend :** React (à développer)

---

## 🗄️ Modèle de données

### Collection `bst_tokens`

```javascript
{
  _id: ObjectId,
  user_id: String,           // Référence utilisateur (unique)
  balance: Number,           // Solde actuel en BST
  total_earned: Number,      // Total gagné depuis le début
  total_spent: Number,       // Total dépensé depuis le début
  transactions: [
    {
      type: String,          // 'mint', 'transfer', 'burn', 'reward', 'spend'
      amount: Number,        // Montant (positif ou négatif)
      reason: String,        // Raison de la transaction
      from: String,          // User ID source (pour transfers)
      to: String,            // User ID destination (pour transfers)
      admin: String,         // Admin qui a effectué l'action
      timestamp: Date        // Date/heure
    }
  ],
  created_at: Date,
  updated_at: Date
}
```

### Index

- `user_id` : unique, index principal
- `transactions.timestamp` : index pour performances

---

## 🔌 API Endpoints

### Public/User Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/bst/balance/:userId` | User/Admin | Récupérer solde BST |
| GET | `/api/bst/history/:userId` | User/Admin | Historique transactions |
| GET | `/api/bst/leaderboard` | Public | Classement utilisateurs |
| POST | `/api/bst/transfer` | User/Admin | Transférer tokens |
| POST | `/api/bst/spend` | User/Admin | Dépenser tokens |

### Admin Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/bst/mint` | Admin | Créer et distribuer tokens |
| POST | `/api/bst/burn` | Admin | Détruire tokens |
| POST | `/api/bst/reward` | Admin | Récompenser utilisateur |
| GET | `/api/bst/stats` | Admin | Statistiques globales |

---

## 🚀 Utilisation

### 1. Mint (Créer des tokens)

**Admin uniquement**

```bash
POST /api/bst/mint
{
  "user_id": "123456",
  "amount": 500,
  "reason": "Welcome bonus"
}
```

**Réponse :**
```json
{
  "success": true,
  "new_balance": 500,
  "transaction_id": "txn_abc123"
}
```

### 2. Transfer (Transférer des tokens)

**User ou Admin**

```bash
POST /api/bst/transfer
{
  "from_user_id": "123456",
  "to_user_id": "789012",
  "amount": 100,
  "reason": "Gift"
}
```

**Réponse :**
```json
{
  "success": true,
  "from_balance": 400,
  "to_balance": 100
}
```

### 3. Reward (Récompenser)

**Admin uniquement**

```bash
POST /api/bst/reward
{
  "user_id": "123456",
  "amount": 50,
  "reason": "Good trade (+5% profit)"
}
```

### 4. Spend (Dépenser)

**User ou Admin**

```bash
POST /api/bst/spend
{
  "user_id": "123456",
  "amount": 100,
  "reason": "Unlock AI premium analysis"
}
```

### 5. Balance (Consulter solde)

```bash
GET /api/bst/balance/123456
```

**Réponse :**
```json
{
  "success": true,
  "user_id": "123456",
  "balance": 450,
  "total_earned": 550,
  "total_spent": 100
}
```

### 6. Leaderboard (Classement)

```bash
GET /api/bst/leaderboard?limit=100
```

**Réponse :**
```json
{
  "success": true,
  "leaderboard": [
    {
      "user_id": "123456",
      "balance": 5000,
      "total_earned": 6000,
      "total_spent": 1000,
      "rank": 1
    }
  ]
}
```

---

## 🔐 Sécurité

### Règles de sécurité

1. **Authentification obligatoire** : Tous les endpoints sauf leaderboard nécessitent JWT
2. **Isolation des données** : User ne peut voir que ses propres données (sauf admin)
3. **Validation des montants** : `amount > 0` pour toutes les opérations
4. **Vérification du solde** : Impossible de dépenser/transférer plus que le solde
5. **Logs admin** : Toutes les actions admin sont loggées avec `admin: user_id`

### Middleware

**`authenticate`** : Vérifie le JWT et décode `req.user`  
**`requireAdmin`** : Vérifie que `req.user.role === 'admin'`

---

## 🎨 Frontend (à développer)

### Dashboard Admin

**URL :** `/admin/bst`

**Fonctionnalités :**
- Mint des tokens (formulaire user_id, amount, reason)
- Burn des tokens (formulaire user_id, amount, reason)
- Statistiques globales (total supply, nb users, avg balance)
- Top holders
- Recherche par user_id

### Dashboard Utilisateur

**URL :** `/dashboard/bst`

**Fonctionnalités :**
- Carte avec solde BST
- Historique des transactions (timeline)
- Leaderboard avec position de l'utilisateur
- Section "Débloquer avec BST" (features premium)
- Possibilité de transférer (optionnel)

---

## 🧪 Tests

### Tests Backend (à implémenter)

```bash
cd backend
npm test -- bst
```

**Couverture attendue :**
- Tests unitaires (modèles + controllers)
- Tests d'intégration (endpoints API)
- Tests de sécurité (auth, permissions)

### Tests à implémenter

- [ ] Création de compte BST automatique
- [ ] Mint avec montant valide
- [ ] Mint avec montant négatif (doit échouer)
- [ ] Transfer avec solde suffisant
- [ ] Transfer avec solde insuffisant (doit échouer)
- [ ] Burn avec solde suffisant
- [ ] User ne peut pas mint (doit échouer)
- [ ] User ne peut voir que son propre solde
- [ ] Leaderboard trié correctement

---

## 📊 Intégration au Backend Existant

### 1. Ajouter les routes au serveur principal

**`backend/server.js` :**

```javascript
const bstRoutes = require('./routes/bst/bstRoutes');

// ...

app.use('/api/bst', bstRoutes);
```

### 2. Vérifier que le middleware auth existe

Le système BST utilise le middleware `authenticate` existant.

**Vérifier :** `backend/middleware/auth.js` doit exporter `authenticate`

---

## 🎯 Gamification (Récompenses automatiques)

### Idées à implémenter

**1. Bon trade**
```javascript
if (trade.profit > 0.05) {  // Profit > 5%
  await bstController.reward({
    user_id: trade.user_id,
    amount: 50,
    reason: `Good trade: +${(trade.profit * 100).toFixed(2)}% profit`
  });
}
```

**2. Streak de connexion**
```javascript
if (user.consecutive_login_days >= 5) {
  await bstController.reward({
    user_id: user.id,
    amount: 100,
    reason: '5-day login streak'
  });
}
```

**3. Leaderboard hebdomadaire**
```javascript
const topTraders = await getWeeklyLeaderboard();
if (topTraders.slice(0, 10).includes(user.id)) {
  await bstController.reward({
    user_id: user.id,
    amount: 500,
    reason: 'Top 10 weekly trader'
  });
}
```

---

## 🔄 Migration Future vers Blockchain

### Étapes de migration

1. **Snapshot des balances**
   ```bash
   mongoexport --collection=bst_tokens --out=bst_snapshot.json
   ```

2. **Créer smart contract** (Solana ou Ethereum)

3. **Airdrop** selon les balances actuelles

4. **Freeze** du système interne
   - Ajouter flag `migrated: true` dans les documents
   - Bloquer mint/transfer/burn sur les comptes migrés

---

## 📅 Roadmap

### Phase 1 (Ce weekend — 08-09/02/2026) ✅
- [x] Modèle MongoDB
- [x] Controller + routes
- [ ] Tests backend
- [ ] Interface admin
- [ ] Dashboard utilisateur

### Phase 2 (Semaine suivante)
- [ ] Récompenses automatiques
- [ ] Features premium déblocables
- [ ] Système de missions

### Phase 3 (À déterminer)
- [ ] Migration blockchain publique
- [ ] Smart contract Solana/Ethereum
- [ ] Token spéculatif

---

## 🐛 Troubleshooting

### Problème : "Authentication required"
**Solution :** Vérifier que le JWT est passé dans le header `Authorization: Bearer <token>`

### Problème : "Admin access required"
**Solution :** Vérifier que l'utilisateur a `role: 'admin'` dans la DB

### Problème : "Insufficient balance"
**Solution :** Vérifier le solde avec `GET /api/bst/balance/:userId` avant transfer/spend

---

## 👨‍💻 Contact

**Développeur :** Jules  
**Email :** julescoachdigital@gmail.com  
**Validation avant merge :** Gilles obligatoire  
**Branche :** `feature/bst-token`

---

**Dernière mise à jour :** 08/02/2026 00:30
