#!/usr/bin/env node
/**
 * Bull Sage MCP Server
 * Connecteur pour Claude Desktop permettant l'exécution automatique de trades
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');

// Configuration
const BULLSAGE_API_URL = process.env.BULLSAGE_API_URL || 'https://bullsage-api.onrender.com';
const CLAUDE_TOKEN = process.env.CLAUDE_WEBHOOK_TOKEN || '';

class BullSageMCPServer {
  constructor() {
    this.server = new Server(
      { name: 'bullsage-trading', version: '1.0.0' },
      { capabilities: { tools: {} } }
    );
    
    this.setupTools();
  }

  async callAPI(endpoint, method = 'GET', body = null) {
    const url = `${BULLSAGE_API_URL}${endpoint}`;
    const options = {
      method,
      headers: {
        'X-Claude-Token': CLAUDE_TOKEN,
        'Content-Type': 'application/json'
      }
    };
    
    if (body) {
      options.body = JSON.stringify(body);
    }
    
    const response = await fetch(url, options);
    return response.json();
  }

  setupTools() {
    // Liste des outils disponibles
    this.server.setRequestHandler('tools/list', async () => ({
      tools: [
        {
          name: 'bullsage_account_status',
          description: 'Vérifie le statut du compte dYdX (capital, positions, trades du jour)',
          inputSchema: { type: 'object', properties: {} }
        },
        {
          name: 'bullsage_get_positions',
          description: 'Liste les positions ouvertes sur dYdX',
          inputSchema: { type: 'object', properties: {} }
        },
        {
          name: 'bullsage_get_signals',
          description: 'Liste les signaux de trading actifs',
          inputSchema: { type: 'object', properties: {} }
        },
        {
          name: 'bullsage_execute_trade',
          description: 'Exécute un trade sur dYdX',
          inputSchema: {
            type: 'object',
            properties: {
              market: { type: 'string', description: 'Marché (BTC-USD, ETH-USD, SOL-USD)' },
              direction: { type: 'string', enum: ['LONG', 'SHORT'], description: 'Direction du trade' },
              size: { type: 'number', description: 'Taille de la position' },
              stop_loss_pct: { type: 'number', description: 'Stop loss en pourcentage (ex: 2.0)' },
              take_profit_pct: { type: 'number', description: 'Take profit en pourcentage (ex: 4.0)' },
              confidence: { type: 'number', description: 'Niveau de confiance 0-100' },
              reason: { type: 'string', description: 'Raison du trade' }
            },
            required: ['market', 'direction', 'size', 'stop_loss_pct', 'take_profit_pct', 'confidence', 'reason']
          }
        },
        {
          name: 'bullsage_close_position',
          description: 'Ferme une position existante',
          inputSchema: {
            type: 'object',
            properties: {
              market: { type: 'string', description: 'Marché à fermer (BTC-USD, etc.)' },
              reason: { type: 'string', description: 'Raison de la fermeture' }
            },
            required: ['market']
          }
        }
      ]
    }));

    // Handler pour l'exécution des outils
    this.server.setRequestHandler('tools/call', async (request) => {
      const { name, arguments: args } = request.params;
      
      try {
        let result;
        
        switch (name) {
          case 'bullsage_account_status':
            result = await this.callAPI('/api/webhook/account-status');
            break;
            
          case 'bullsage_get_positions':
            result = await this.callAPI('/api/webhook/positions');
            break;
            
          case 'bullsage_get_signals':
            result = await this.callAPI('/api/webhook/signals');
            break;
            
          case 'bullsage_execute_trade':
            result = await this.callAPI('/api/webhook/execute-trade', 'POST', args);
            break;
            
          case 'bullsage_close_position':
            result = await this.callAPI('/api/webhook/close-position', 'POST', args);
            break;
            
          default:
            throw new Error(`Outil inconnu: ${name}`);
        }
        
        return {
          content: [{ type: 'text', text: JSON.stringify(result, null, 2) }]
        };
        
      } catch (error) {
        return {
          content: [{ type: 'text', text: `Erreur: ${error.message}` }],
          isError: true
        };
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Bull Sage MCP Server démarré');
  }
}

const server = new BullSageMCPServer();
server.run().catch(console.error);
