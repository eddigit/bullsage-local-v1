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
  
  const { 
    market, 
    direction, 
    entry, 
    stopLoss, 
    takeProfit, 
    size,
    // Nouveau: configuration du montant
    sizeMode,
    percentageOfPortfolio,
    fixedAmountUSDC,
    // Métadonnées pour documentation
    metadata
  } = req.body;
  
  if (!market || !direction) {
    return res.status(400).json({ error: 'Missing required fields: market, direction' });
  }
  
  console.log(`\n🎯 Signal reçu: ${direction} ${market}`);
  console.log(`   Entry: $${entry || 'market'} | SL: $${stopLoss} | TP: $${takeProfit}`);
  if (metadata) {
    console.log(`   📋 Métadonnées:`, JSON.stringify(metadata, null, 2));
  }
  
  // Calculer la taille de position basée sur le mode
  let calculatedSize = size || 0;
  let sizeInfo = { mode: 'fixed', value: size };
  
  try {
    // Récupérer le prix actuel du marché
    const markets = await client.indexerClient.markets.getPerpetualMarkets();
    const marketData = markets.markets[market];
    const currentPrice = parseFloat(marketData?.oraclePrice || entry || 0);
    const minOrderSize = parseFloat(marketData?.stepBaseQuantums || 0.001) / 1e9;
    
    if (sizeMode === 'percentage' && percentageOfPortfolio) {
      // Calculer basé sur le % du portefeuille
      const account = await client.indexerClient.account.getSubaccount(wallet.address, 0);
      const equity = parseFloat(account.subaccount?.equity || '0');
      const freeCollateral = parseFloat(account.subaccount?.freeCollateral || equity);
      
      const amountUSDC = freeCollateral * (percentageOfPortfolio / 100);
      calculatedSize = amountUSDC / currentPrice;
      
      console.log(`   💼 Portefeuille: $${equity.toFixed(2)}`);
      console.log(`   📊 ${percentageOfPortfolio}% = $${amountUSDC.toFixed(2)} → ${calculatedSize.toFixed(6)} ${market.replace('-USD', '')}`);
      
      sizeInfo = {
        mode: 'percentage',
        percentage: percentageOfPortfolio,
        equity: equity,
        amountUSDC: amountUSDC,
        calculatedSize: calculatedSize
      };
    } else if (sizeMode === 'fixed' && fixedAmountUSDC) {
      // Montant fixe en USDC
      calculatedSize = fixedAmountUSDC / currentPrice;
      
      console.log(`   💵 Montant fixe: $${fixedAmountUSDC} → ${calculatedSize.toFixed(6)} ${market.replace('-USD', '')}`);
      
      sizeInfo = {
        mode: 'fixed',
        amountUSDC: fixedAmountUSDC,
        calculatedSize: calculatedSize
      };
    }
    
    // Arrondir à la précision minimale du marché
    if (minOrderSize > 0) {
      calculatedSize = Math.floor(calculatedSize / minOrderSize) * minOrderSize;
    }
    
    // Vérification taille minimum
    if (calculatedSize < minOrderSize) {
      console.log(`   ⚠️ Taille trop petite (${calculatedSize} < ${minOrderSize})`);
      calculatedSize = minOrderSize;
    }
    
    console.log(`   📦 Taille finale: ${calculatedSize}`);
    
  } catch (e) {
    console.log(`   ⚠️ Erreur calcul taille: ${e.message}, utilisation size par défaut`);
    if (!calculatedSize || calculatedSize <= 0) {
      // Fallback par défaut selon le marché
      if (market.includes('BTC')) calculatedSize = 0.001;
      else if (market.includes('ETH')) calculatedSize = 0.01;
      else calculatedSize = 0.1;
    }
  }
  
  const results = {
    signal: { market, direction, entry, stopLoss, takeProfit, size: calculatedSize, sizeInfo },
    metadata: metadata || {},
    orders: [],
    success: false,
    timestamp: new Date().toISOString()
  };
  
  // Calculer la durée d'expiration des ordres basée sur le trade_type
  let orderExpirationSeconds = 86400; // Par défaut 24h
  const tradeType = metadata?.trade_type || 'INTRADAY';
  const estimatedDuration = metadata?.estimated_duration || '';
  
  // Mapper le trade_type vers une durée d'expiration appropriée
  const expirationByTradeType = {
    'SCALPING': 3600,        // 1 heure
    'INTRADAY': 86400,       // 24 heures
    'INTRADAY+': 172800,     // 48 heures
    'SWING': 604800,         // 7 jours
    'POSITION': 2592000      // 30 jours
  };
  
  orderExpirationSeconds = expirationByTradeType[tradeType] || 86400;
  
  // Si on a une durée estimée plus précise, essayer de l'utiliser
  if (estimatedDuration) {
    const durationMatch = estimatedDuration.match(/(\d+)\s*(heure|hour|jour|day|semaine|week)/i);
    if (durationMatch) {
      const value = parseInt(durationMatch[1]);
      const unit = durationMatch[2].toLowerCase();
      
      if (unit.includes('heure') || unit.includes('hour')) {
        orderExpirationSeconds = value * 3600 * 1.5; // +50% marge
      } else if (unit.includes('jour') || unit.includes('day')) {
        orderExpirationSeconds = value * 86400 * 1.5;
      } else if (unit.includes('semaine') || unit.includes('week')) {
        orderExpirationSeconds = value * 604800 * 1.5;
      }
    }
  }
  
  // Minimum 1h, maximum 30 jours
  orderExpirationSeconds = Math.max(3600, Math.min(orderExpirationSeconds, 2592000));
  
  const expirationHours = (orderExpirationSeconds / 3600).toFixed(1);
  console.log(`   ⏱️ Type: ${tradeType} | Expiration ordres: ${expirationHours}h`);
  
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
        calculatedSize,
        entryClientId,
        currentBlock + 10,
        OrderTimeInForce.IOC,
        false
      );
      
      console.log(`   ✅ Entry placé`);
      results.orders.push({ type: 'ENTRY', success: true, price: entryPrice, size: calculatedSize });
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
          calculatedSize,
          randomClientId(),
          OrderTimeInForce.GTT,
          orderExpirationSeconds, // Durée dynamique selon le trade_type
          OrderExecution.DEFAULT,
          false,
          false
        );
        console.log(`   ✅ Stop Loss placé @ $${stopLoss} (expire: ${expirationHours}h)`);
        results.orders.push({ type: 'STOP_LOSS', success: true, price: stopLoss, expiresIn: orderExpirationSeconds });
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
          calculatedSize,
          randomClientId(),
          OrderTimeInForce.GTT,
          orderExpirationSeconds, // Durée dynamique selon le trade_type
          OrderExecution.DEFAULT,
          false,
          false
        );
        console.log(`   ✅ Take Profit placé @ $${takeProfit} (expire: ${expirationHours}h)`);
        results.orders.push({ type: 'TAKE_PROFIT', success: true, price: takeProfit, expiresIn: orderExpirationSeconds });
      } catch (e) {
        console.log(`   ⚠️ TP échoué: ${e.message}`);
        results.orders.push({ type: 'TAKE_PROFIT', success: false, error: e.message });
      }
    }
    
    // Ajouter les infos de timing dans les résultats
    results.timing = {
      trade_type: tradeType,
      estimated_duration: estimatedDuration,
      order_expiration_seconds: orderExpirationSeconds,
      order_expiration_hours: parseFloat(expirationHours),
      orders_expire_at: new Date(Date.now() + orderExpirationSeconds * 1000).toISOString()
    };
    
    results.success = results.orders.some(o => o.success);
    console.log(`   📊 Résultat: ${results.success ? '✅ OK' : '❌ Échec'}`);
    console.log(`   📅 Ordres expirent: ${results.timing.orders_expire_at}`);
    
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
    console.warn('⚠️ DYDX_TESTNET_MNEMONIC non configuré');
    console.warn('   Le serveur démarre en mode LECTURE SEULE');
    console.warn('   Configurez la variable sur Render Dashboard pour activer le trading');
    
    // Démarrer quand même le serveur en mode lecture seule
    app.listen(PORT, () => {
      console.log(`\n🚀 Serveur démarré sur le port ${PORT} (MODE LECTURE SEULE)`);
      console.log('\n📋 Endpoints disponibles:');
      console.log(`   GET  /status     - Statut (non connecté)`);
      console.log(`   POST /execute    - Retournera une erreur`);
    });
    return;
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
