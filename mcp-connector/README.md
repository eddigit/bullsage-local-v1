# Bull Sage MCP Connector

Connecteur MCP pour Claude Desktop permettant l'exécution automatique de trades sur dYdX via Bull Sage.

## Installation

### 1. Installer les dépendances

```bash
cd mcp-connector
npm install
```

### 2. Configurer Claude Desktop

Ajoutez dans votre fichier de configuration Claude Desktop (`claude_desktop_config.json`) :

**Windows** : `%APPDATA%\Claude\claude_desktop_config.json`
**Mac** : `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bullsage-trading": {
      "command": "node",
      "args": ["C:/Users/clari/bullsage-local-v1/mcp-connector/bullsage-mcp-server.js"],
      "env": {
        "BULLSAGE_API_URL": "https://bullsage-api.onrender.com",
        "CLAUDE_WEBHOOK_TOKEN": "VOTRE_TOKEN_ICI"
      }
    }
  }
}
```

### 3. Redémarrer Claude Desktop

Fermez et relancez Claude Desktop pour charger le connecteur.

## Outils disponibles

| Outil | Description |
|-------|-------------|
| `bullsage_account_status` | Vérifie le capital, positions et trades du jour |
| `bullsage_get_positions` | Liste les positions ouvertes sur dYdX |
| `bullsage_get_signals` | Affiche les signaux de trading actifs |
| `bullsage_execute_trade` | Exécute un nouveau trade |
| `bullsage_close_position` | Ferme une position existante |

## Exemple d'utilisation

Dans Claude Desktop, vous pouvez demander :

```
"Vérifie mon compte Bull Sage et dis-moi si j'ai des positions ouvertes"

"Analyse BTC et si le signal est bon (confiance > 80%), ouvre un LONG avec SL 2% et TP 4%"

"Ferme ma position BTC car le marché devient bearish"
```

## Sécurité

- Le token webhook est stocké dans les variables d'environnement
- Rate limiting : 10 requêtes/minute max
- Stop loss obligatoire sur chaque trade
- Risque max : 2% du capital par trade

## Troubleshooting

### Le serveur ne démarre pas
```bash
# Vérifier que Node.js est installé
node --version

# Réinstaller les dépendances
npm install
```

### Erreur d'authentification
Vérifiez que le token dans `CLAUDE_WEBHOOK_TOKEN` correspond à celui configuré sur Render.

### Trades non exécutés
- Confiance < 80% : le trade sera refusé
- Même marché dans les 5 dernières minutes : cooldown actif
- Plus de 10 trades aujourd'hui : limite atteinte
