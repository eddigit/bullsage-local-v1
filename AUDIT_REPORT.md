# AUDIT REPORT - Bull Sage Platform

**Date**: 2025-01-08
**Version**: 1.0.0
**Auditor**: Claude Code

---

## EXECUTIVE SUMMARY

L'audit de la plateforme Bull Sage a révélé plusieurs problèmes critiques, notamment des **clés API exposées dans le code source**, un fichier backend monolithique de **7849 lignes**, et des failles de sécurité importantes. Une intervention immédiate est requise.

| Priorité | Nombre d'issues |
|----------|-----------------|
| CRITIQUE | 6 |
| HAUTE | 12 |
| MOYENNE | 15 |
| BASSE | 8 |

---

## 1. ARCHITECTURE

### 1.1 Structure Actuelle

```
bullsage-local-v1/
├── backend/           # FastAPI (Python) - 7849 lignes dans server.py
│   ├── server.py      # MONOLITHIQUE - Tout le code
│   ├── core/          # Config et auth (partiellement utilisé)
│   ├── routes/        # Routes séparées (partiellement utilisé)
│   └── services/      # Services métier
├── frontend/          # React.js + Tailwind
└── dydx-executor/     # Node.js - Exécution dYdX
```

### 1.2 Issues Identifiées

| ID | Issue | Priorité | Fichier |
|----|-------|----------|---------|
| ARCH-01 | `server.py` contient 7849 lignes - code monolithique non maintenable | **HAUTE** | `backend/server.py` |
| ARCH-02 | Duplication de code entre `server.py` et `routes/` | **MOYENNE** | Multiple |
| ARCH-03 | Connexion MongoDB instanciée globalement sans gestion du pool | **MOYENNE** | `backend/server.py:44` |
| ARCH-04 | Dépendance circulaire potentielle entre services | **BASSE** | `backend/services/` |
| ARCH-05 | Routes `core/auth.py` vs `server.py:get_current_user()` dupliquées | **MOYENNE** | Multiple |

---

## 2. SÉCURITÉ

### 2.1 Issues CRITIQUES

| ID | Issue | Priorité | Fichier | Ligne |
|----|-------|----------|---------|-------|
| SEC-01 | **CLÉS API EN CLAIR DANS `.env` COMMITÉ** - XAI, Anthropic, OpenRouter, Finnhub, etc. exposés | **CRITIQUE** | `backend/.env` | 1-17 |
| SEC-02 | **DEV_MODE = true** en production désactive l'authentification | **CRITIQUE** | `backend/server.py` | 390 |
| SEC-03 | **JWT_SECRET hardcodé** avec valeur par défaut faible | **CRITIQUE** | `backend/server.py:52` | - |
| SEC-04 | **Mots de passe admin hardcodés** dans le code | **CRITIQUE** | `backend/server.py:7757` | - |
| SEC-05 | **CORS configuré à `*`** accepte toutes les origines | **CRITIQUE** | `backend/.env:3` | - |
| SEC-06 | **Endpoint `/diagnostic`** expose des informations sensibles sans auth | **CRITIQUE** | `dydx-executor/server.js:102` | - |

### 2.2 Issues HAUTES

| ID | Issue | Priorité | Fichier |
|----|-------|----------|---------|
| SEC-07 | Pas de rate limiting sur les endpoints sensibles | **HAUTE** | Global |
| SEC-08 | Pas de validation CSRF | **HAUTE** | Backend |
| SEC-09 | Tokens API passés en query params (log exposure) | **HAUTE** | `backend/server.py:949` |
| SEC-10 | Mnemonic dYdX potentiellement exposé dans les logs | **HAUTE** | `dydx-executor/server.js:120` |
| SEC-11 | Pas de chiffrement du mnemonic en base de données | **HAUTE** | `backend/routes/dydx.py:147` |
| SEC-12 | Auth middleware du dYdX executor bypasse en dev/interne | **HAUTE** | `dydx-executor/server.js:47` |

### 2.3 Issues MOYENNES

| ID | Issue | Priorité | Fichier |
|----|-------|----------|---------|
| SEC-13 | Pas de validation d'email format strict | **MOYENNE** | `backend/server.py:428` |
| SEC-14 | Input `symbol` non sanitisé (injection potentielle) | **MOYENNE** | Multiple routes |
| SEC-15 | Pas de Content-Security-Policy headers | **MOYENNE** | Backend |

### 2.4 Clés API Exposées (backend/.env)

```
XAI_API_KEY=xai-4dM7Hv...
OPENROUTER_API_KEY=sk-or-v1-9fdbe...
ANTHROPIC_API_KEY=sk-ant-api03-foQq...
FINNHUB_API_KEY=d505k1pr01qsab...
MARKETAUX_API_KEY=EUUB4wXMoaAkh...
ALPHA_VANTAGE_API_KEY=RY2XZ59CW2ZE...
FRED_API_KEY=df6c9e3e2d25...
```

**ACTION IMMÉDIATE REQUISE**: Révoquer et régénérer TOUTES ces clés API.

---

## 3. QUALITÉ DU CODE

### 3.1 Issues Identifiées

| ID | Issue | Priorité | Fichier | Détail |
|----|-------|----------|---------|--------|
| QUA-01 | Fichier `server.py` de 7849 lignes - impossible à maintenir | **HAUTE** | `backend/server.py` | Refactoriser en modules |
| QUA-02 | 250 appels MongoDB sans index documenté | **HAUTE** | Backend | Performance |
| QUA-03 | Gestion d'erreur générique `except Exception` partout | **MOYENNE** | Multiple | 408 occurrences |
| QUA-04 | Code dupliqué dans routes vs server.py | **MOYENNE** | Multiple | |
| QUA-05 | Typage incomplet (pas de type hints) | **BASSE** | Services | |
| QUA-06 | Imports non utilisés | **BASSE** | Multiple | |
| QUA-07 | Variables globales mutables (_crypto_cache, etc.) | **MOYENNE** | `backend/server.py` | |
| QUA-08 | Constantes hardcodées (timeouts, limites) | **BASSE** | Multiple | |

### 3.2 Fonctions Trop Longues

| Fonction | Lignes | Fichier |
|----------|--------|---------|
| `get_signal_stats()` | ~180 | `backend/server.py:1319` |
| `execute()` endpoint | ~400 | `dydx-executor/server.js:214` |
| `quick_create_dydx_signal()` | ~200 | `backend/routes/dydx.py:298` |

---

## 4. PERFORMANCE

### 4.1 Issues MongoDB

| ID | Issue | Priorité | Impact |
|----|-------|----------|--------|
| PERF-01 | Pas d'index sur `user_id` dans les collections | **HAUTE** | Queries lentes |
| PERF-02 | `to_list(1000)` charge tout en mémoire | **HAUTE** | `backend/server.py:1322` |
| PERF-03 | Requêtes N+1 dans les boucles | **MOYENNE** | Multiple |
| PERF-04 | Pas de pagination sur les listes | **MOYENNE** | Frontend lag |

### 4.2 Issues API

| ID | Issue | Priorité | Impact |
|----|-------|----------|--------|
| PERF-05 | Appels API externes séquentiels au lieu de parallèles | **MOYENNE** | Latence |
| PERF-06 | Cache crypto de 10 minutes trop long pour trading | **MOYENNE** | Données stales |
| PERF-07 | Pas de connection pooling pour httpx | **BASSE** | Resources |

---

## 5. ROBUSTESSE dYdX

### 5.1 Issues Identifiées

| ID | Issue | Priorité | Fichier |
|----|-------|----------|---------|
| DYD-01 | Pas de retry logic sur les erreurs réseau dYdX | **HAUTE** | `dydx-executor/server.js` |
| DYD-02 | Timeout de 30s peut être insuffisant pour blockchain | **HAUTE** | `backend/routes/dydx.py:446` |
| DYD-03 | Pas de vérification de la liquidité avant trade | **HAUTE** | dydx-executor |
| DYD-04 | Fallback en mode simulation sans avertissement clair | **MOYENNE** | `backend/services/dydx_trader.py:339` |
| DYD-05 | Pas de gestion du slippage max | **MOYENNE** | dydx-executor |
| DYD-06 | Orders SL/TP utilisant LIMIT au lieu de STOP_MARKET | **HAUTE** | `dydx-executor/server.js:531` |
| DYD-07 | Pas de vérification du margin disponible avant trade | **HAUTE** | dydx-executor |
| DYD-08 | Pas de cooldown entre trades sur même marché | **MOYENNE** | Backend |
| DYD-09 | Client ID généré aléatoirement peut causer des conflits | **BASSE** | `dydx-executor/server.js:95` |

### 5.2 Cas Limites Non Gérés

- Position déjà fermée lors de l'ajout de protection
- Market indisponible ou en maintenance
- Solde insuffisant pour margin
- Prix d'entrée trop éloigné du prix actuel
- Expiration d'ordre pendant l'exécution

---

## 6. DETTE TECHNIQUE

### 6.1 Dépendances Obsolètes

| Package | Version Actuelle | Issue |
|---------|-----------------|-------|
| numpy | 2.3.5 (dupliqué dans requirements.txt) | **BASSE** |
| fastapi | 0.110.1 | OK mais pas dernière |
| express | 5.2.1 | Version beta |

### 6.2 Code Mort / Inutilisé

| Fichier | Raison |
|---------|--------|
| `backend/backup/` | Backup non versionné |
| `backend/academy_data.py` + `academy_data_part2.py` | 128KB de données hardcodées |
| `backend/integrate_*.py` | Scripts d'intégration one-shot |
| Tests files à la racine | Non organisés |

### 6.3 Configuration Hardcodée

| Valeur | Fichier | Ligne |
|--------|---------|-------|
| `CHART_CACHE_TTL = 120` | `backend/server.py` | 510 |
| `_crypto_cache["ttl"] = 600` | `backend/server.py` | 504 |
| Leverage default = 10 | Multiple | - |
| Risk % = 2% | Non configurable | - |

### 6.4 TODO/FIXME Non Résolus

Aucun TODO/FIXME trouvé dans le code source (ce qui est suspect - indique un manque de documentation des problèmes connus).

---

## 7. RECOMMANDATIONS PRIORITAIRES

### Immédiat (< 24h)

1. **RÉVOQUER toutes les clés API** exposées dans `.env`
2. **Supprimer `.env` du repo** et l'ajouter à `.gitignore`
3. **Désactiver DEV_MODE** en production
4. **Changer JWT_SECRET** avec une vraie clé aléatoire
5. **Restreindre CORS** aux domaines autorisés

### Court Terme (< 1 semaine)

1. Implémenter rate limiting
2. Ajouter retry logic sur dYdX
3. Créer des index MongoDB
4. Refactoriser `server.py` en modules
5. Ajouter validation des inputs

### Moyen Terme (< 1 mois)

1. Audit de sécurité complet
2. Tests unitaires et d'intégration
3. Documentation API (OpenAPI)
4. Monitoring et alerting
5. CI/CD pipeline sécurisé

---

## 8. FICHIERS À MODIFIER EN PRIORITÉ

1. `backend/.env` - Supprimer du repo
2. `backend/server.py` - Désactiver DEV_MODE, sécuriser JWT
3. `dydx-executor/server.js` - Sécuriser diagnostic, ajouter retry
4. `.gitignore` - Ajouter `.env`
5. `backend/routes/dydx.py` - Validation et garde-fous

---

## ANNEXE A: Statistiques du Code

| Métrique | Valeur |
|----------|--------|
| Lignes backend/server.py | 7849 |
| Fichiers Python | ~40 |
| Fichiers JS/TS | ~100 |
| Appels MongoDB | 250+ |
| Try/Except blocks | 408 |
| Routes API | ~80+ |

---

## ANNEXE B: Commandes de Vérification

```bash
# Vérifier les secrets exposés
git log --all --full-history -- "*/.env"

# Trouver les clés hardcodées
grep -r "api_key\|secret\|password" --include="*.py" --include="*.js"

# Analyser la taille des fichiers
find . -name "*.py" -exec wc -l {} + | sort -n
```

---

**Fin du rapport d'audit**

*Généré par Claude Code - Audit automatisé de la plateforme Bull Sage*
