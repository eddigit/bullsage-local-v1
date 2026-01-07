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

// 🆕 Stockage en mémoire des ordres pullback en attente
const pendingPullbacks = new Map();

// Middleware d'authentification pour les routes sensibles (production)
const authMiddleware = (req, res, next) => {
  // En développement local, pas de vérification
  if (!API_SECRET || process.env.NODE_ENV !== 'production') {
    return next();
  }
  
  // Log pour debug
  console.log('🔐 Auth check - Headers:', {
    'x-api-key': req.headers['x-api-key'] ? '***SET***' : 'NOT SET',
    'authorization': req.headers['authorization'] ? '***SET***' : 'NOT SET',
    'origin': req.headers['origin'],
    'referer': req.headers['referer']
  });
  
  const authHeader = req.headers['x-api-key'] || req.headers['authorization'];
  if (authHeader === API_SECRET || authHeader === `Bearer ${API_SECRET}`) {
    return next();
  }
  
  // Permettre les requêtes depuis les services Render internes (même réseau)
  const origin = req.headers['origin'] || req.headers['referer'] || '';
  if (origin.includes('onrender.com') || origin.includes('bullsage')) {
    console.log('✅ Requête autorisée depuis Render internal');
    return next();
  }
  
  console.log('❌ Auth failed - Expected:', API_SECRET ? '***SET***' : 'NOT SET');
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

// Diagnostic complet (sans auth pour debug)
app.get('/diagnostic', async (req, res) => {
  const diag = {
    timestamp: new Date().toISOString(),
    server: {
      node_env: process.env.NODE_ENV,
      port: PORT,
      uptime: process.uptime()
    },
    dydx: {
      connected: isConnected,
      wallet: wallet?.address || 'NOT SET',
      network: 'testnet'
    },
    auth: {
      api_secret_configured: !!API_SECRET,
      api_secret_length: API_SECRET?.length || 0
    },
    env_vars: {
      DYDX_TESTNET_MNEMONIC: MNEMONIC ? 'SET (' + MNEMONIC.split(' ').length + ' words)' : 'NOT SET',
      DYDX_API_SECRET: API_SECRET ? 'SET (' + API_SECRET.length + ' chars)' : 'NOT SET'
    }
  };
  
  // Tester la connexion dYdX si connecté
  if (isConnected) {
    try {
      const account = await client.indexerClient.account.getSubaccount(wallet.address, 0);
      diag.dydx.equity = parseFloat(account.subaccount?.equity || '0');
      diag.dydx.freeCollateral = parseFloat(account.subaccount?.freeCollateral || '0');
      diag.dydx.status = 'OK';
    } catch (e) {
      diag.dydx.status = 'ERROR: ' + e.message;
    }
  }
  
  console.log('📋 Diagnostic requested:', JSON.stringify(diag, null, 2));
  res.json(diag);
});
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
  console.log('\n' + '='.repeat(60));
  console.log('🚀 NOUVELLE REQUÊTE /execute');
  console.log('   Timestamp:', new Date().toISOString());
  console.log('   IP:', req.ip);
  console.log('   Headers:', JSON.stringify({
    'content-type': req.headers['content-type'],
    'x-api-key': req.headers['x-api-key'] ? '***SET***' : 'NOT SET',
    'origin': req.headers['origin'],
    'user-agent': req.headers['user-agent']?.substring(0, 50)
  }));
  console.log('   Body:', JSON.stringify(req.body, null, 2));
  
  if (!isConnected) {
    console.log('❌ ERREUR: Non connecté à dYdX');
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
    // 🆕 Mode d'entrée: 'market' (immédiat) ou 'pullback' (ordre limite)
    entryMode = 'market',
    // Expiration de l'ordre d'entrée pullback en heures (défaut: 4h)
    pullbackExpirationHours = 4,
    // Métadonnées pour documentation
    metadata
  } = req.body;
  
  if (!market || !direction) {
    console.log('❌ ERREUR: Champs manquants - market:', market, 'direction:', direction);
    return res.status(400).json({ error: 'Missing required fields: market, direction' });
  }
  
  // Valider le mode d'entrée
  const validEntryModes = ['market', 'pullback'];
  const normalizedEntryMode = validEntryModes.includes(entryMode?.toLowerCase()) ? entryMode.toLowerCase() : 'market';
  
  console.log(`\n🎯 Signal reçu: ${direction} ${market}`);
  console.log(`   Entry: $${entry || 'market'} | SL: $${stopLoss} | TP: $${takeProfit}`);
  console.log(`   📥 Mode d'entrée: ${normalizedEntryMode.toUpperCase()}${normalizedEntryMode === 'pullback' ? ` (expire: ${pullbackExpirationHours}h)` : ''}`);
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
    const currentMarketPrice = await getMarketPrice(market);
    const entryPrice = entry || currentMarketPrice;
    const entryClientId = randomClientId();
    
    // Calculer l'expiration de l'ordre pullback en secondes
    const pullbackExpirationSeconds = Math.max(1800, Math.min(pullbackExpirationHours * 3600, 604800)); // Min 30min, Max 7 jours
    
    // Vérifier si le pullback est logique
    const isPullbackValid = normalizedEntryMode === 'pullback' && entry && (
      (direction === 'LONG' && entry < currentMarketPrice) || // Long: on attend que le prix descende
      (direction === 'SHORT' && entry > currentMarketPrice)   // Short: on attend que le prix monte
    );
    
    try {
      if (normalizedEntryMode === 'pullback' && entry) {
        // 🆕 MODE PULLBACK: Ordre limite qui attend que le prix revienne
        
        if (!isPullbackValid) {
          // Le prix actuel est déjà au niveau du pullback ou mieux
          console.log(`   ⚠️ Prix actuel ($${currentMarketPrice.toFixed(2)}) déjà ${direction === 'LONG' ? 'en dessous' : 'au-dessus'} du pullback ($${entry})`);
          console.log(`   🔄 Basculement en mode MARKET`);
          
          // Exécuter en market si le pullback n'a plus de sens
          await client.placeShortTermOrder(
            subaccount,
            market,
            entrySide,
            currentMarketPrice * (direction === 'LONG' ? 1.005 : 0.995),
            calculatedSize,
            entryClientId,
            currentBlock + 10,
            OrderTimeInForce.IOC,
            false
          );
          
          console.log(`   ✅ Entry MARKET placé @ ~$${currentMarketPrice.toFixed(2)}`);
          results.orders.push({ 
            type: 'ENTRY', 
            success: true, 
            mode: 'market_fallback',
            price: currentMarketPrice, 
            size: calculatedSize,
            note: 'Pullback ignoré - prix déjà favorable'
          });
        } else {
          // Placer un ordre limite au prix du pullback
          await client.placeOrder(
            subaccount,
            market,
            OrderType.LIMIT,
            entrySide,
            entryPrice,
            calculatedSize,
            entryClientId,
            OrderTimeInForce.GTT,
            pullbackExpirationSeconds,
            OrderExecution.DEFAULT,
            true, // postOnly = true pour s'assurer d'être maker
            false
          );
          
          const pullbackPercent = ((currentMarketPrice - entryPrice) / currentMarketPrice * 100).toFixed(2);
          console.log(`   ✅ Entry PULLBACK placé @ $${entryPrice} (${pullbackPercent}% ${direction === 'LONG' ? 'plus bas' : 'plus haut'})`);
          console.log(`   ⏳ En attente du pullback - expire dans ${pullbackExpirationHours}h`);
          
          results.orders.push({ 
            type: 'ENTRY', 
            success: true, 
            mode: 'pullback',
            price: entryPrice, 
            currentPrice: currentMarketPrice,
            pullbackPercent: parseFloat(pullbackPercent),
            size: calculatedSize,
            expiresIn: pullbackExpirationSeconds,
            expiresAt: new Date(Date.now() + pullbackExpirationSeconds * 1000).toISOString(),
            status: 'PENDING_PULLBACK'
          });
          
          // NOTE: Pour le mode pullback, on NE place PAS les SL/TP immédiatement
          // car la position n'existe pas encore. Ils seront placés quand l'ordre sera exécuté.
          results.pullbackMode = true;
          results.pullbackInfo = {
            entryPrice: entryPrice,
            currentPrice: currentMarketPrice,
            pullbackPercent: parseFloat(pullbackPercent),
            expiresAt: new Date(Date.now() + pullbackExpirationSeconds * 1000).toISOString(),
            note: 'Les SL/TP seront activés automatiquement quand le pullback sera atteint'
          };
          results.pendingSLTP = {
            stopLoss: stopLoss,
            takeProfit: takeProfit,
            note: 'En attente de l\'exécution de l\'ordre d\'entrée'
          };
          
          // 🆕 Enregistrer le pullback pour monitoring automatique
          const pullbackKey = `${market}_${entryClientId}`;
          pendingPullbacks.set(pullbackKey, {
            market,
            direction,
            entryPrice,
            size: calculatedSize,
            stopLoss,
            takeProfit,
            clientId: entryClientId,
            expiresAt: new Date(Date.now() + pullbackExpirationSeconds * 1000).toISOString(),
            createdAt: new Date().toISOString(),
            status: 'PENDING'
          });
          
          results.success = true;
          console.log(`   📊 Mode PULLBACK actif - SL/TP en attente (clé: ${pullbackKey})`);
          
          // Retourner tôt pour le mode pullback
          return res.json(results);
        }
      } else {
        // MODE MARKET: Exécution immédiate (comportement actuel)
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
        
        console.log(`   ✅ Entry MARKET placé`);
        results.orders.push({ type: 'ENTRY', success: true, mode: 'market', price: entryPrice, size: calculatedSize });
      }
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
    
    // LOG COMPLET DU RÉSULTAT
    console.log('='.repeat(60));
    console.log('📊 RÉSULTAT EXÉCUTION:');
    console.log('   Success:', results.success);
    console.log('   Orders:', JSON.stringify(results.orders, null, 2));
    console.log('   Timing:', JSON.stringify(results.timing));
    if (!results.success) {
      console.log('   ⚠️ ÉCHEC - Vérifier les ordres ci-dessus');
    }
    console.log('='.repeat(60));
    
    res.json(results);
    
  } catch (e) {
    console.error('='.repeat(60));
    console.error('❌ ERREUR CRITIQUE dans /execute:');
    console.error('   Message:', e.message);
    console.error('   Stack:', e.stack);
    console.error('='.repeat(60));
    res.status(500).json({ error: e.message, results });
  }
});

async function getMarketPrice(market) {
  const markets = await client.indexerClient.markets.getPerpetualMarkets();
  return parseFloat(markets.markets[market]?.oraclePrice || 0);
}

// ============ POSITIONS DÉTAILLÉES & MONITORING ============

// Positions avec PnL et ordres associés
app.get('/positions/detailed', async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ error: 'Not connected' });
  }
  
  try {
    // Récupérer positions, ordres et prix
    const [positionsRes, ordersRes, markets] = await Promise.all([
      client.indexerClient.account.getSubaccountPerpetualPositions(wallet.address, 0),
      client.indexerClient.account.getSubaccountOrders(wallet.address, 0),
      client.indexerClient.markets.getPerpetualMarkets()
    ]);
    
    // Filtrer les positions fermées (status CLOSED ou taille 0)
    const positions = (positionsRes.positions || []).filter(pos => {
      const size = parseFloat(pos.size || 0);
      const status = pos.status || '';
      // Garder uniquement les positions OPEN avec une taille non nulle
      return status === 'OPEN' && Math.abs(size) > 0.00001;
    });
    const allOrders = ordersRes || [];
    
    const detailedPositions = positions.map(pos => {
      const market = pos.market;
      const marketData = markets.markets[market];
      const currentPrice = parseFloat(marketData?.oraclePrice || 0);
      const size = parseFloat(pos.size || 0);
      const entryPrice = parseFloat(pos.entryPrice || 0);
      const side = size > 0 ? 'LONG' : 'SHORT';
      const absSize = Math.abs(size);
      
      // Calculer PnL
      let unrealizedPnl = 0;
      let pnlPercent = 0;
      if (side === 'LONG') {
        unrealizedPnl = (currentPrice - entryPrice) * absSize;
        pnlPercent = ((currentPrice - entryPrice) / entryPrice) * 100;
      } else {
        unrealizedPnl = (entryPrice - currentPrice) * absSize;
        pnlPercent = ((entryPrice - currentPrice) / entryPrice) * 100;
      }
      
      // Trouver les ordres associés (SL/TP)
      const relatedOrders = allOrders.filter(o => o.ticker === market && o.status === 'OPEN');
      const stopLoss = relatedOrders.find(o => {
        const orderSide = o.side;
        const price = parseFloat(o.price);
        if (side === 'LONG') {
          return orderSide === 'SELL' && price < currentPrice;
        } else {
          return orderSide === 'BUY' && price > currentPrice;
        }
      });
      const takeProfit = relatedOrders.find(o => {
        const orderSide = o.side;
        const price = parseFloat(o.price);
        if (side === 'LONG') {
          return orderSide === 'SELL' && price > currentPrice;
        } else {
          return orderSide === 'BUY' && price < currentPrice;
        }
      });
      
      return {
        market,
        side,
        size: absSize,
        entryPrice,
        currentPrice,
        unrealizedPnl: parseFloat(unrealizedPnl.toFixed(2)),
        pnlPercent: parseFloat(pnlPercent.toFixed(2)),
        status: unrealizedPnl >= 0 ? 'WINNING' : 'LOSING',
        stopLoss: stopLoss ? {
          price: parseFloat(stopLoss.price),
          orderId: stopLoss.id,
          expiresAt: stopLoss.goodTilBlockTime
        } : null,
        takeProfit: takeProfit ? {
          price: parseFloat(takeProfit.price),
          orderId: takeProfit.id,
          expiresAt: takeProfit.goodTilBlockTime
        } : null,
        hasProtection: !!(stopLoss || takeProfit),
        createdAt: pos.createdAt,
        relatedOrders: relatedOrders.length
      };
    });
    
    // Compte
    const account = await client.indexerClient.account.getSubaccount(wallet.address, 0);
    const equity = parseFloat(account.subaccount?.equity || '0');
    const freeCollateral = parseFloat(account.subaccount?.freeCollateral || '0');
    
    res.json({
      wallet: wallet.address,
      equity,
      freeCollateral,
      positionsCount: detailedPositions.length,
      totalUnrealizedPnl: parseFloat(detailedPositions.reduce((sum, p) => sum + p.unrealizedPnl, 0).toFixed(2)),
      positions: detailedPositions,
      unprotectedPositions: detailedPositions.filter(p => !p.hasProtection).length,
      timestamp: new Date().toISOString()
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Fermer une position (market order)
app.post('/positions/close', authMiddleware, async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ error: 'Not connected' });
  }
  
  const { market, reason } = req.body;
  
  if (!market) {
    return res.status(400).json({ error: 'Market required' });
  }
  
  console.log(`\n🔒 Fermeture position ${market} - Raison: ${reason || 'manual'}`);
  
  try {
    // Récupérer la position actuelle
    const positionsRes = await client.indexerClient.account.getSubaccountPerpetualPositions(wallet.address, 0);
    const position = (positionsRes.positions || []).find(p => p.market === market);
    
    if (!position) {
      return res.status(404).json({ error: `Aucune position ouverte sur ${market}` });
    }
    
    const size = Math.abs(parseFloat(position.size || 0));
    const side = parseFloat(position.size) > 0 ? 'LONG' : 'SHORT';
    const closeSide = side === 'LONG' ? OrderSide.SELL : OrderSide.BUY;
    
    // Prix actuel
    const currentPrice = await getMarketPrice(market);
    const currentBlock = await client.validatorClient.get.latestBlockHeight();
    
    // Placer un ordre market pour fermer
    // Note: reduceOnly=false car dYdX v4 désactive reduce-only pour les ordres non-IOC standard
    // On utilise IOC (Immediate-Or-Cancel) pour exécution immédiate
    // La taille exacte de la position garantit la fermeture complète
    await client.placeShortTermOrder(
      subaccount,
      market,
      closeSide,
      currentPrice * (closeSide === OrderSide.BUY ? 1.02 : 0.98), // Slippage 2% pour garantir l'exécution
      size,
      randomClientId(),
      currentBlock + 10,
      OrderTimeInForce.IOC,
      false // reduceOnly désactivé - la taille exacte ferme la position
    );
    
    console.log(`   ✅ Position ${market} fermée (${side} ${size})`);
    
    // Annuler les ordres SL/TP restants
    const ordersRes = await client.indexerClient.account.getSubaccountOrders(wallet.address, 0);
    const relatedOrders = (ordersRes || []).filter(o => o.ticker === market && o.status === 'OPEN');
    
    for (const order of relatedOrders) {
      try {
        await client.cancelOrder(
          subaccount,
          order.clientId,
          order.orderFlags,
          market,
          currentBlock + 10
        );
        console.log(`   🗑️ Ordre annulé: ${order.id}`);
      } catch (e) {
        console.log(`   ⚠️ Impossible d'annuler ${order.id}: ${e.message}`);
      }
    }
    
    res.json({
      success: true,
      market,
      side,
      size,
      closePrice: currentPrice,
      reason: reason || 'manual',
      cancelledOrders: relatedOrders.length,
      timestamp: new Date().toISOString()
    });
    
  } catch (e) {
    console.error(`   ❌ Erreur fermeture: ${e.message}`);
    res.status(500).json({ error: e.message });
  }
});

// �️ AJOUTER DES PROTECTIONS SL/TP À UNE POSITION EXISTANTE
app.post('/positions/protect', authMiddleware, async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ error: 'Not connected' });
  }
  
  const { market, stopLoss, takeProfit, expirationHours } = req.body;
  
  if (!market) {
    return res.status(400).json({ error: 'Market required' });
  }
  
  if (!stopLoss && !takeProfit) {
    return res.status(400).json({ error: 'Au moins un Stop Loss ou Take Profit requis' });
  }
  
  console.log(`\n🛡️ === AJOUT PROTECTION ${market} ===`);
  console.log(`   SL: ${stopLoss ? '$' + stopLoss : 'Non défini'}`);
  console.log(`   TP: ${takeProfit ? '$' + takeProfit : 'Non défini'}`);
  
  try {
    // Récupérer la position actuelle
    const positionsRes = await client.indexerClient.account.getSubaccountPerpetualPositions(wallet.address, 0);
    const position = (positionsRes.positions || []).find(p => p.market === market);
    
    if (!position) {
      return res.status(404).json({ error: `Aucune position ouverte sur ${market}` });
    }
    
    const size = Math.abs(parseFloat(position.size || 0));
    const side = parseFloat(position.size) > 0 ? 'LONG' : 'SHORT';
    const exitSide = side === 'LONG' ? OrderSide.SELL : OrderSide.BUY;
    const entryPrice = parseFloat(position.entryPrice || 0);
    const currentPrice = await getMarketPrice(market);
    
    console.log(`   Position: ${side} ${size} @ $${entryPrice.toFixed(2)}`);
    console.log(`   Prix actuel: $${currentPrice.toFixed(2)}`);
    
    // Validation des prix SL/TP
    if (stopLoss) {
      if (side === 'LONG' && stopLoss >= currentPrice) {
        return res.status(400).json({ 
          error: `Stop Loss ($${stopLoss}) doit être inférieur au prix actuel ($${currentPrice.toFixed(2)}) pour un LONG` 
        });
      }
      if (side === 'SHORT' && stopLoss <= currentPrice) {
        return res.status(400).json({ 
          error: `Stop Loss ($${stopLoss}) doit être supérieur au prix actuel ($${currentPrice.toFixed(2)}) pour un SHORT` 
        });
      }
    }
    
    if (takeProfit) {
      if (side === 'LONG' && takeProfit <= currentPrice) {
        return res.status(400).json({ 
          error: `Take Profit ($${takeProfit}) doit être supérieur au prix actuel ($${currentPrice.toFixed(2)}) pour un LONG` 
        });
      }
      if (side === 'SHORT' && takeProfit >= currentPrice) {
        return res.status(400).json({ 
          error: `Take Profit ($${takeProfit}) doit être inférieur au prix actuel ($${currentPrice.toFixed(2)}) pour un SHORT` 
        });
      }
    }
    
    // Annuler les anciens ordres SL/TP sur ce marché
    const ordersRes = await client.indexerClient.account.getSubaccountOrders(wallet.address, 0);
    const existingOrders = (ordersRes || []).filter(o => o.ticker === market && o.status === 'OPEN');
    const currentBlock = await client.validatorClient.get.latestBlockHeight();
    
    for (const order of existingOrders) {
      try {
        await client.cancelOrder(
          subaccount,
          order.clientId,
          order.orderFlags,
          market,
          currentBlock + 10
        );
        console.log(`   🗑️ Ancien ordre annulé: ${order.id}`);
      } catch (e) {
        console.log(`   ⚠️ Impossible d'annuler ${order.id}: ${e.message}`);
      }
    }
    
    await new Promise(r => setTimeout(r, 1000));
    
    const results = {
      market,
      side,
      size,
      entryPrice,
      currentPrice,
      orders: [],
      cancelledOrders: existingOrders.length
    };
    
    // Durée d'expiration (par défaut 7 jours)
    const orderExpirationSeconds = (expirationHours || 168) * 3600; // 168h = 7 jours
    
    // Placer le Stop Loss
    if (stopLoss) {
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
          orderExpirationSeconds,
          OrderExecution.DEFAULT,
          false, // postOnly
          false  // reduceOnly (désactivé sur dYdX v4)
        );
        
        console.log(`   ✅ Stop Loss placé @ $${stopLoss}`);
        results.orders.push({ 
          type: 'STOP_LOSS', 
          success: true, 
          price: stopLoss,
          expiresIn: `${expirationHours || 168}h`
        });
      } catch (e) {
        console.log(`   ❌ Stop Loss échoué: ${e.message}`);
        results.orders.push({ type: 'STOP_LOSS', success: false, error: e.message });
      }
    }
    
    await new Promise(r => setTimeout(r, 1000));
    
    // Placer le Take Profit
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
          orderExpirationSeconds,
          OrderExecution.DEFAULT,
          false, // postOnly
          false  // reduceOnly
        );
        
        console.log(`   ✅ Take Profit placé @ $${takeProfit}`);
        results.orders.push({ 
          type: 'TAKE_PROFIT', 
          success: true, 
          price: takeProfit,
          expiresIn: `${expirationHours || 168}h`
        });
      } catch (e) {
        console.log(`   ❌ Take Profit échoué: ${e.message}`);
        results.orders.push({ type: 'TAKE_PROFIT', success: false, error: e.message });
      }
    }
    
    results.success = results.orders.every(o => o.success);
    results.timestamp = new Date().toISOString();
    
    // Calculer les % par rapport à l'entrée
    if (stopLoss) {
      results.stopLossPercent = ((stopLoss - entryPrice) / entryPrice * 100).toFixed(2);
    }
    if (takeProfit) {
      results.takeProfitPercent = ((takeProfit - entryPrice) / entryPrice * 100).toFixed(2);
    }
    
    console.log(`   📊 Résultat: ${results.success ? '✅ Position protégée' : '⚠️ Protection partielle'}`);
    
    res.json(results);
    
  } catch (e) {
    console.error(`   ❌ Erreur protection: ${e.message}`);
    res.status(500).json({ error: e.message });
  }
});

// �🔄 CRON/MONITORING - Vérifier les positions et fermer si nécessaire
app.get('/monitor', authMiddleware, async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ error: 'Not connected' });
  }
  
  console.log('\n🔍 === MONITORING DES POSITIONS ===');
  
  try {
    const results = {
      timestamp: new Date().toISOString(),
      positions: [],
      actions: [],
      alerts: []
    };
    
    // Récupérer positions et ordres
    const [positionsRes, ordersRes, markets] = await Promise.all([
      client.indexerClient.account.getSubaccountPerpetualPositions(wallet.address, 0),
      client.indexerClient.account.getSubaccountOrders(wallet.address, 0),
      client.indexerClient.markets.getPerpetualMarkets()
    ]);
    
    const positions = positionsRes.positions || [];
    const allOrders = ordersRes || [];
    
    console.log(`   📊 ${positions.length} positions ouvertes`);
    
    for (const pos of positions) {
      const market = pos.market;
      const marketData = markets.markets[market];
      const currentPrice = parseFloat(marketData?.oraclePrice || 0);
      const size = parseFloat(pos.size || 0);
      const entryPrice = parseFloat(pos.entryPrice || 0);
      const side = size > 0 ? 'LONG' : 'SHORT';
      const absSize = Math.abs(size);
      
      // Calculer PnL
      let pnlPercent = 0;
      if (side === 'LONG') {
        pnlPercent = ((currentPrice - entryPrice) / entryPrice) * 100;
      } else {
        pnlPercent = ((entryPrice - currentPrice) / entryPrice) * 100;
      }
      
      // Vérifier les ordres de protection
      const relatedOrders = allOrders.filter(o => o.ticker === market && o.status === 'OPEN');
      const hasProtection = relatedOrders.length > 0;
      
      const posInfo = {
        market,
        side,
        size: absSize,
        entryPrice,
        currentPrice,
        pnlPercent: parseFloat(pnlPercent.toFixed(2)),
        hasProtection,
        ordersCount: relatedOrders.length
      };
      
      results.positions.push(posInfo);
      
      console.log(`   ${side === 'LONG' ? '🟢' : '🔴'} ${market}: ${pnlPercent.toFixed(2)}% ${hasProtection ? '✅' : '⚠️ SANS PROTECTION'}`);
      
      // ALERTES
      if (!hasProtection) {
        results.alerts.push({
          type: 'NO_PROTECTION',
          market,
          message: `Position ${market} sans Stop Loss ni Take Profit!`,
          pnlPercent: posInfo.pnlPercent
        });
      }
      
      // Si perte > 5% sans protection, ALERTE CRITIQUE
      if (!hasProtection && pnlPercent < -5) {
        results.alerts.push({
          type: 'CRITICAL_LOSS',
          market,
          message: `⚠️ CRITIQUE: ${market} perd ${Math.abs(pnlPercent).toFixed(2)}% sans protection!`,
          pnlPercent: posInfo.pnlPercent
        });
        console.log(`   ⚠️ ALERTE CRITIQUE: ${market} -${Math.abs(pnlPercent).toFixed(2)}%`);
      }
      
      // Auto-close si perte > 10% sans protection (sécurité)
      if (!hasProtection && pnlPercent < -10) {
        console.log(`   🚨 AUTO-FERMETURE: ${market} perte > 10%`);
        
        try {
          const closeSide = side === 'LONG' ? OrderSide.SELL : OrderSide.BUY;
          const currentBlock = await client.validatorClient.get.latestBlockHeight();
          
          // reduceOnly=false car dYdX v4 désactive reduce-only pour short-term
          await client.placeShortTermOrder(
            subaccount,
            market,
            closeSide,
            currentPrice * (closeSide === OrderSide.BUY ? 1.02 : 0.98), // 2% slippage
            absSize,
            randomClientId(),
            currentBlock + 10,
            OrderTimeInForce.IOC,
            false // reduceOnly désactivé
          );
          
          results.actions.push({
            type: 'AUTO_CLOSE',
            market,
            reason: 'Loss > 10% without protection',
            pnlPercent: posInfo.pnlPercent
          });
          
          console.log(`   ✅ ${market} fermé automatiquement`);
        } catch (e) {
          console.log(`   ❌ Échec fermeture auto: ${e.message}`);
        }
      }
    }
    
    results.summary = {
      totalPositions: positions.length,
      protectedPositions: results.positions.filter(p => p.hasProtection).length,
      unprotectedPositions: results.positions.filter(p => !p.hasProtection).length,
      criticalAlerts: results.alerts.filter(a => a.type === 'CRITICAL_LOSS').length,
      actionsPerformed: results.actions.length
    };
    
    console.log(`   📋 Résumé: ${results.summary.protectedPositions}/${results.summary.totalPositions} protégées`);
    
    res.json(results);
    
  } catch (e) {
    console.error(`   ❌ Erreur monitoring: ${e.message}`);
    res.status(500).json({ error: e.message });
  }
});

// ============ PULLBACK MONITORING ============

// Enregistrer un ordre pullback avec ses SL/TP en attente
app.post('/pullback/register', authMiddleware, async (req, res) => {
  const { market, direction, entryPrice, size, stopLoss, takeProfit, expiresAt, clientId } = req.body;
  
  if (!market || !direction || !size) {
    return res.status(400).json({ error: 'Missing required fields' });
  }
  
  const pullbackData = {
    market,
    direction,
    entryPrice,
    size,
    stopLoss,
    takeProfit,
    expiresAt,
    clientId,
    createdAt: new Date().toISOString(),
    status: 'PENDING'
  };
  
  pendingPullbacks.set(`${market}_${clientId || Date.now()}`, pullbackData);
  
  console.log(`📥 Pullback enregistré: ${direction} ${market} @ $${entryPrice}`);
  
  res.json({ success: true, pullback: pullbackData });
});

// Vérifier les ordres pullback et activer les SL/TP si exécutés
app.get('/pullback/check', authMiddleware, async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ error: 'Not connected' });
  }
  
  console.log(`\n🔍 Vérification des pullbacks en attente...`);
  
  const results = {
    checked: [],
    activated: [],
    expired: [],
    pending: []
  };
  
  try {
    // Récupérer les positions actuelles
    const [positionsRes, ordersRes] = await Promise.all([
      client.indexerClient.account.getSubaccountPerpetualPositions(wallet.address, 0),
      client.indexerClient.account.getSubaccountOrders(wallet.address, 0)
    ]);
    
    const positions = positionsRes.positions || [];
    const openOrders = (ordersRes || []).filter(o => o.status === 'OPEN');
    
    for (const [key, pullback] of pendingPullbacks.entries()) {
      results.checked.push(key);
      
      const now = new Date();
      const expiresAt = new Date(pullback.expiresAt);
      
      // Vérifier si expiré
      if (expiresAt < now) {
        console.log(`   ⏰ Pullback expiré: ${pullback.market}`);
        pullback.status = 'EXPIRED';
        results.expired.push(pullback);
        pendingPullbacks.delete(key);
        continue;
      }
      
      // Vérifier si une position existe maintenant (= pullback exécuté)
      const position = positions.find(p => p.market === pullback.market);
      
      if (position && Math.abs(parseFloat(position.size)) >= pullback.size * 0.95) {
        console.log(`   ✅ Pullback exécuté pour ${pullback.market}! Activation SL/TP...`);
        
        const size = Math.abs(parseFloat(position.size));
        const direction = parseFloat(position.size) > 0 ? 'LONG' : 'SHORT';
        const exitSide = direction === 'LONG' ? OrderSide.SELL : OrderSide.BUY;
        
        const activatedOrders = [];
        
        // Placer le Stop Loss
        if (pullback.stopLoss) {
          try {
            await client.placeOrder(
              subaccount,
              pullback.market,
              OrderType.LIMIT,
              exitSide,
              pullback.stopLoss,
              size,
              randomClientId(),
              OrderTimeInForce.GTT,
              604800, // 7 jours
              OrderExecution.DEFAULT,
              false,
              false
            );
            console.log(`      ✅ SL activé @ $${pullback.stopLoss}`);
            activatedOrders.push({ type: 'STOP_LOSS', price: pullback.stopLoss });
          } catch (e) {
            console.log(`      ⚠️ SL échoué: ${e.message}`);
          }
        }
        
        // Placer le Take Profit
        if (pullback.takeProfit) {
          try {
            await client.placeOrder(
              subaccount,
              pullback.market,
              OrderType.LIMIT,
              exitSide,
              pullback.takeProfit,
              size,
              randomClientId(),
              OrderTimeInForce.GTT,
              604800, // 7 jours
              OrderExecution.DEFAULT,
              false,
              false
            );
            console.log(`      ✅ TP activé @ $${pullback.takeProfit}`);
            activatedOrders.push({ type: 'TAKE_PROFIT', price: pullback.takeProfit });
          } catch (e) {
            console.log(`      ⚠️ TP échoué: ${e.message}`);
          }
        }
        
        pullback.status = 'ACTIVATED';
        pullback.activatedOrders = activatedOrders;
        pullback.activatedAt = new Date().toISOString();
        results.activated.push(pullback);
        pendingPullbacks.delete(key);
      } else {
        // Toujours en attente
        results.pending.push(pullback);
      }
    }
    
    console.log(`   📊 Résultat: ${results.activated.length} activés, ${results.expired.length} expirés, ${results.pending.length} en attente`);
    
    res.json({
      success: true,
      timestamp: new Date().toISOString(),
      ...results
    });
    
  } catch (e) {
    console.error(`   ❌ Erreur vérification pullback: ${e.message}`);
    res.status(500).json({ error: e.message });
  }
});

// Liste des pullbacks en attente
app.get('/pullback/pending', authMiddleware, (req, res) => {
  const pending = Array.from(pendingPullbacks.values());
  res.json({
    count: pending.length,
    pullbacks: pending
  });
});

// Annuler un pullback
app.delete('/pullback/:market', authMiddleware, async (req, res) => {
  const { market } = req.params;
  
  let deleted = false;
  for (const [key, pullback] of pendingPullbacks.entries()) {
    if (pullback.market === market) {
      pendingPullbacks.delete(key);
      deleted = true;
      
      // Annuler aussi l'ordre limite sur dYdX si on est connecté
      if (isConnected && pullback.clientId) {
        try {
          const currentBlock = await client.validatorClient.get.latestBlockHeight();
          await client.cancelOrder(
            subaccount,
            pullback.clientId,
            0,
            market,
            currentBlock + 10
          );
          console.log(`   🗑️ Ordre pullback annulé pour ${market}`);
        } catch (e) {
          console.log(`   ⚠️ Impossible d'annuler l'ordre: ${e.message}`);
        }
      }
    }
  }
  
  if (deleted) {
    res.json({ success: true, message: `Pullback ${market} annulé` });
  } else {
    res.status(404).json({ error: `Pas de pullback en attente pour ${market}` });
  }
});

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
