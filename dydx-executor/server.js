/**
 * 🐂 BULL SAGE - Serveur d'exécution dYdX
 * 
 * API REST qui reçoit les signaux du backend Python
 * et les exécute sur dYdX
 */

const express = require('express');
const cors = require('cors');
const { 
  CompositeClient,
  Network,
  OrderSide,
  OrderType,
  OrderTimeInForce,
  OrderExecution,
  LocalWallet,
  SubaccountInfo
} = require('@dydxprotocol/v4-client-js');
const dotenv = require('dotenv');
const path = require('path');

// Charger .env - en local depuis backend/.env, en prod depuis les vars d'environnement
if (process.env.NODE_ENV !== 'production') {
  dotenv.config({ path: path.join(__dirname, '../backend/.env') });
}

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || process.env.DYDX_EXECUTOR_PORT || 3001;
const MNEMONIC = process.env.DYDX_TESTNET_MNEMONIC || '';
const API_SECRET = process.env.DYDX_API_SECRET || '';

let client = null;
let wallet = null;
let subaccount = null;
let isConnected = false;

// Middleware d'authentification pour les routes sensibles (production)
const authMiddleware = (req, res, next) => {
  // En développement local, pas de vérification
  if (!API_SECRET || process.env.NODE_ENV !== 'production') {
    return next();
  }
  
  const authHeader = req.headers['x-api-key'] || req.headers['authorization'];
  if (authHeader === API_SECRET || authHeader === `Bearer ${API_SECRET}`) {
    return next();
  }
  
  return res.status(401).json({ error: 'Unauthorized' });
};

// Initialiser la connexion dYdX
async function initDydx() {
  try {
    console.log('🔌 Connexion à dYdX Testnet...');
    client = await CompositeClient.connect(Network.testnet());
    
    wallet = await LocalWallet.fromMnemonic(MNEMONIC, 'dydx');
    subaccount = SubaccountInfo.forLocalWallet(wallet, 0);
    
    isConnected = true;
    console.log(`✅ Connecté! Wallet: ${wallet.address}`);
    
    return true;
  } catch (e) {
    console.error('❌ Erreur connexion dYdX:', e.message);
    return false;
  }
}

// Helper functions
function randomClientId() {
  return Math.floor(Math.random() * 100000000);
}

// ============ ROUTES API ============

// Status
app.get('/status', async (req, res) => {
  if (!isConnected) {
    return res.json({ connected: false });
  }
  
  try {
    const account = await client.indexerClient.account.getSubaccount(wallet.address, 0);
    const equity = parseFloat(account.subaccount?.equity || '0');
    
    res.json({
      connected: true,
      wallet: wallet.address,
      equity: equity,
      network: 'testnet'
    });
  } catch (e) {
    res.json({ connected: false, error: e.message });
  }
});

// Prix des marchés
app.get('/prices', async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ error: 'Not connected' });
  }
  
  try {
    const markets = await client.indexerClient.markets.getPerpetualMarkets();
    const prices = {};
    
    for (const [ticker, data] of Object.entries(markets.markets)) {
      prices[ticker] = parseFloat(data.oraclePrice);
    }
    
    res.json({ prices });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Positions ouvertes
app.get('/positions', async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ error: 'Not connected' });
  }
  
  try {
    const positions = await client.indexerClient.account.getSubaccountPerpetualPositions(
      wallet.address, 0
    );
    res.json({ positions: positions.positions || [] });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Ordres ouverts
app.get('/orders', async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ error: 'Not connected' });
  }
  
  try {
    const orders = await client.indexerClient.account.getSubaccountOrders(
      wallet.address, 0
    );
    res.json({ orders: orders || [] });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// 🎯 EXÉCUTER UN SIGNAL (protégé par auth en production)
app.post('/execute', authMiddleware, async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ error: 'Not connected to dYdX' });
  }
  
  const { market, direction, entry, stopLoss, takeProfit, size } = req.body;
  
  if (!market || !direction || !size) {
    return res.status(400).json({ error: 'Missing required fields: market, direction, size' });
  }
  
  console.log(`\n🎯 Signal reçu: ${direction} ${market}`);
  console.log(`   Entry: $${entry || 'market'} | SL: $${stopLoss} | TP: $${takeProfit}`);
  
  const results = {
    signal: { market, direction, entry, stopLoss, takeProfit, size },
    orders: [],
    success: false,
    timestamp: new Date().toISOString()
  };
  
  try {
    const currentBlock = await client.validatorClient.get.latestBlockHeight();
    const entrySide = direction === 'LONG' ? OrderSide.BUY : OrderSide.SELL;
    const exitSide = direction === 'LONG' ? OrderSide.SELL : OrderSide.BUY;
    
    // 1. Ordre d'entrée
    const entryPrice = entry || (await getMarketPrice(market));
    const entryClientId = randomClientId();
    
    try {
      await client.placeShortTermOrder(
        subaccount,
        market,
        entrySide,
        entryPrice * (direction === 'LONG' ? 1.005 : 0.995),
        size,
        entryClientId,
        currentBlock + 10,
        OrderTimeInForce.IOC,
        false
      );
      
      console.log(`   ✅ Entry placé`);
      results.orders.push({ type: 'ENTRY', success: true, price: entryPrice });
    } catch (e) {
      console.log(`   ❌ Entry échoué: ${e.message}`);
      results.orders.push({ type: 'ENTRY', success: false, error: e.message });
      return res.json(results);
    }
    
    // Attendre
    await new Promise(r => setTimeout(r, 2000));
    
    // 2. Stop Loss (si fourni)
    if (stopLoss) {
      const slBlock = await client.validatorClient.get.latestBlockHeight();
      try {
        await client.placeOrder(
          subaccount,
          market,
          OrderType.LIMIT,
          exitSide,
          stopLoss,
          size,
          randomClientId(),
          OrderTimeInForce.GTT,
          86400,
          OrderExecution.DEFAULT,
          false,
          false
        );
        console.log(`   ✅ Stop Loss placé @ $${stopLoss}`);
        results.orders.push({ type: 'STOP_LOSS', success: true, price: stopLoss });
      } catch (e) {
        console.log(`   ⚠️ SL échoué: ${e.message}`);
        results.orders.push({ type: 'STOP_LOSS', success: false, error: e.message });
      }
    }
    
    // 3. Take Profit (si fourni)
    if (takeProfit) {
      try {
        await client.placeOrder(
          subaccount,
          market,
          OrderType.LIMIT,
          exitSide,
          takeProfit,
          size,
          randomClientId(),
          OrderTimeInForce.GTT,
          86400,
          OrderExecution.DEFAULT,
          false,
          false
        );
        console.log(`   ✅ Take Profit placé @ $${takeProfit}`);
        results.orders.push({ type: 'TAKE_PROFIT', success: true, price: takeProfit });
      } catch (e) {
        console.log(`   ⚠️ TP échoué: ${e.message}`);
        results.orders.push({ type: 'TAKE_PROFIT', success: false, error: e.message });
      }
    }
    
    results.success = results.orders.some(o => o.success);
    console.log(`   📊 Résultat: ${results.success ? '✅ OK' : '❌ Échec'}`);
    
    res.json(results);
    
  } catch (e) {
    console.error(`   ❌ Erreur: ${e.message}`);
    res.status(500).json({ error: e.message, results });
  }
});

async function getMarketPrice(market) {
  const markets = await client.indexerClient.markets.getPerpetualMarkets();
  return parseFloat(markets.markets[market]?.oraclePrice || 0);
}

// Démarrer le serveur
async function start() {
  console.log('='.repeat(60));
  console.log('🐂 BULL SAGE - Serveur dYdX Executor');
  console.log('='.repeat(60));
  
  if (!MNEMONIC) {
    console.error('❌ DYDX_TESTNET_MNEMONIC non configuré dans .env');
    process.exit(1);
  }
  
  await initDydx();
  
  app.listen(PORT, () => {
    console.log(`\n🚀 Serveur démarré sur http://localhost:${PORT}`);
    console.log('\n📋 Endpoints disponibles:');
    console.log(`   GET  /status     - Statut de la connexion`);
    console.log(`   GET  /prices     - Prix des marchés`);
    console.log(`   GET  /positions  - Positions ouvertes`);
    console.log(`   GET  /orders     - Ordres ouverts`);
    console.log(`   POST /execute    - Exécuter un signal`);
    console.log('\n💡 Exemple d\'exécution:');
    console.log(`   curl -X POST http://localhost:${PORT}/execute \\`);
    console.log(`     -H "Content-Type: application/json" \\`);
    console.log(`     -d '{"market":"BTC-USD","direction":"LONG","size":0.001}'`);
  });
}

start();
