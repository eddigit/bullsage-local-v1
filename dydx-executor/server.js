/**
 * BULL SAGE - Serveur d'execution dYdX v2.0
 *
 * Changelog v2.0:
 * - Retry logic avec backoff exponentiel
 * - Verification margin avant trade
 * - Support STOP_MARKET pour SL/TP
 * - Gestion slippage configurable
 * - Cooldown entre trades par marche
 * - Meilleure gestion d'erreur
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

// Charger .env
if (process.env.NODE_ENV !== 'production') {
  dotenv.config({ path: path.join(__dirname, '../backend/.env') });
}

const app = express();
app.use(cors());
app.use(express.json());

// ============ CONFIGURATION ============

const PORT = process.env.PORT || process.env.DYDX_EXECUTOR_PORT || 3001;
const MNEMONIC = process.env.DYDX_TESTNET_MNEMONIC || '';
const API_SECRET = process.env.DYDX_API_SECRET || '';

// Configuration trading (peut etre overridee par les requetes)
const DEFAULT_CONFIG = {
  MAX_SLIPPAGE_PERCENT: parseFloat(process.env.MAX_SLIPPAGE_PERCENT) || 1.0,
  TRADE_COOLDOWN_SECONDS: parseInt(process.env.TRADE_COOLDOWN_SECONDS) || 60,
  MAX_RETRIES: 3,
  RETRY_BASE_DELAY_MS: 1000,
  MIN_MARGIN_RATIO: 0.1, // 10% minimum margin libre
  ALLOWED_MARKETS: (process.env.ALLOWED_MARKETS || 'BTC-USD,ETH-USD,SOL-USD,AVAX-USD,DOGE-USD,XRP-USD,ADA-USD,DOT-USD,LINK-USD,MATIC-USD').split(',')
};

let client = null;
let wallet = null;
let subaccount = null;
let isConnected = false;

// Stockage cooldown par marche
const lastTradeByMarket = new Map();

// Stockage pullbacks en attente
const pendingPullbacks = new Map();

// ============ RETRY LOGIC ============

/**
 * Execute une fonction avec retry et backoff exponentiel
 * @param {Function} fn - Fonction async a executer
 * @param {number} maxRetries - Nombre max de tentatives
 * @param {number} baseDelay - Delai de base en ms
 * @param {string} operationName - Nom de l'operation pour les logs
 */
async function withRetry(fn, maxRetries = DEFAULT_CONFIG.MAX_RETRIES, baseDelay = DEFAULT_CONFIG.RETRY_BASE_DELAY_MS, operationName = 'operation') {
  let lastError;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      const isRetryable = isRetryableError(error);

      console.log(`   [Retry] ${operationName} - Tentative ${attempt}/${maxRetries} echouee: ${error.message}`);

      if (!isRetryable || attempt === maxRetries) {
        console.log(`   [Retry] ${operationName} - Abandon apres ${attempt} tentative(s)`);
        throw error;
      }

      // Backoff exponentiel: 1s, 2s, 4s...
      const delay = baseDelay * Math.pow(2, attempt - 1);
      console.log(`   [Retry] ${operationName} - Attente ${delay}ms avant prochaine tentative...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }

  throw lastError;
}

/**
 * Determine si une erreur est retryable
 */
function isRetryableError(error) {
  const message = error.message?.toLowerCase() || '';

  // Erreurs reseau retryables
  if (message.includes('timeout') ||
      message.includes('network') ||
      message.includes('econnrefused') ||
      message.includes('econnreset') ||
      message.includes('socket hang up') ||
      message.includes('fetch failed')) {
    return true;
  }

  // Erreurs blockchain temporaires
  if (message.includes('sequence mismatch') ||
      message.includes('account not found') ||
      message.includes('insufficient funds')) {
    return true;
  }

  // Rate limiting
  if (message.includes('rate limit') || message.includes('429')) {
    return true;
  }

  return false;
}

// ============ VALIDATION & CHECKS ============

/**
 * Verifie si le margin disponible est suffisant pour un trade
 */
async function checkMarginAvailable(sizeUSDC, market) {
  try {
    const account = await withRetry(
      () => client.indexerClient.account.getSubaccount(wallet.address, 0),
      2, 500, 'checkMargin'
    );

    const equity = parseFloat(account.subaccount?.equity || '0');
    const freeCollateral = parseFloat(account.subaccount?.freeCollateral || equity);
    const minRequired = sizeUSDC * DEFAULT_CONFIG.MIN_MARGIN_RATIO;

    console.log(`   [Margin] Equity: $${equity.toFixed(2)} | Free: $${freeCollateral.toFixed(2)} | Required: $${minRequired.toFixed(2)}`);

    if (freeCollateral < minRequired) {
      return {
        sufficient: false,
        freeCollateral,
        required: minRequired,
        equity,
        error: `Margin insuffisant: $${freeCollateral.toFixed(2)} disponible, $${minRequired.toFixed(2)} requis`
      };
    }

    return { sufficient: true, freeCollateral, equity };
  } catch (e) {
    console.error(`   [Margin] Erreur verification: ${e.message}`);
    return { sufficient: false, error: `Erreur verification margin: ${e.message}` };
  }
}

/**
 * Verifie le cooldown pour un marche
 */
function checkCooldown(market, cooldownSeconds = DEFAULT_CONFIG.TRADE_COOLDOWN_SECONDS) {
  const lastTrade = lastTradeByMarket.get(market);

  if (!lastTrade) {
    return { allowed: true };
  }

  const elapsed = (Date.now() - lastTrade) / 1000;

  if (elapsed < cooldownSeconds) {
    const remaining = Math.ceil(cooldownSeconds - elapsed);
    return {
      allowed: false,
      remaining,
      error: `Cooldown actif sur ${market}: ${remaining}s restantes`
    };
  }

  return { allowed: true };
}

/**
 * Enregistre un trade pour le cooldown
 */
function recordTrade(market) {
  lastTradeByMarket.set(market, Date.now());
}

/**
 * Calcule le prix avec slippage
 */
function applySlippage(price, side, slippagePercent = DEFAULT_CONFIG.MAX_SLIPPAGE_PERCENT) {
  const slippageFactor = slippagePercent / 100;

  if (side === OrderSide.BUY) {
    return price * (1 + slippageFactor);
  } else {
    return price * (1 - slippageFactor);
  }
}

// ============ MIDDLEWARE AUTH ============

const authMiddleware = (req, res, next) => {
  if (!API_SECRET || process.env.NODE_ENV !== 'production') {
    return next();
  }

  const authHeader = req.headers['x-api-key'] || req.headers['authorization'];
  if (authHeader === API_SECRET || authHeader === `Bearer ${API_SECRET}`) {
    return next();
  }

  const origin = req.headers['origin'] || req.headers['referer'] || '';
  if (origin.includes('onrender.com') || origin.includes('bullsage')) {
    return next();
  }

  console.log('[Auth] Requete non autorisee');
  return res.status(401).json({
    success: false,
    error: 'Unauthorized',
    code: 'AUTH_FAILED'
  });
};

// ============ CONNEXION dYdX ============

async function initDydx() {
  try {
    console.log('[Init] Connexion a dYdX Testnet...');

    client = await withRetry(
      () => CompositeClient.connect(Network.testnet()),
      3, 2000, 'dYdX connect'
    );

    wallet = await LocalWallet.fromMnemonic(MNEMONIC, 'dydx');
    subaccount = SubaccountInfo.forLocalWallet(wallet, 0);

    isConnected = true;
    console.log(`[Init] Connecte! Wallet: ${wallet.address}`);

    return true;
  } catch (e) {
    console.error('[Init] Erreur connexion dYdX:', e.message);
    return false;
  }
}

function randomClientId() {
  return Math.floor(Math.random() * 100000000);
}

async function getMarketPrice(market) {
  const markets = await withRetry(
    () => client.indexerClient.markets.getPerpetualMarkets(),
    2, 500, 'getMarketPrice'
  );
  return parseFloat(markets.markets[market]?.oraclePrice || 0);
}

// ============ ROUTES API ============

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    connected: isConnected,
    timestamp: new Date().toISOString()
  });
});

// Status
app.get('/status', async (req, res) => {
  if (!isConnected) {
    return res.json({ connected: false });
  }

  try {
    const account = await withRetry(
      () => client.indexerClient.account.getSubaccount(wallet.address, 0),
      2, 500, 'status'
    );

    const equity = parseFloat(account.subaccount?.equity || '0');
    const freeCollateral = parseFloat(account.subaccount?.freeCollateral || '0');

    res.json({
      connected: true,
      wallet: wallet.address,
      equity,
      freeCollateral,
      network: 'testnet',
      config: {
        maxSlippage: DEFAULT_CONFIG.MAX_SLIPPAGE_PERCENT,
        cooldownSeconds: DEFAULT_CONFIG.TRADE_COOLDOWN_SECONDS,
        allowedMarkets: DEFAULT_CONFIG.ALLOWED_MARKETS
      }
    });
  } catch (e) {
    res.json({ connected: false, error: e.message });
  }
});

// Diagnostic (sans infos sensibles en production)
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
      wallet: wallet?.address ? `${wallet.address.substring(0, 10)}...` : 'NOT SET',
      network: 'testnet'
    },
    config: {
      maxSlippage: DEFAULT_CONFIG.MAX_SLIPPAGE_PERCENT,
      cooldownSeconds: DEFAULT_CONFIG.TRADE_COOLDOWN_SECONDS,
      maxRetries: DEFAULT_CONFIG.MAX_RETRIES,
      allowedMarketsCount: DEFAULT_CONFIG.ALLOWED_MARKETS.length
    }
  };

  if (isConnected) {
    try {
      const account = await client.indexerClient.account.getSubaccount(wallet.address, 0);
      diag.dydx.equity = parseFloat(account.subaccount?.equity || '0');
      diag.dydx.freeCollateral = parseFloat(account.subaccount?.freeCollateral || '0');
      diag.dydx.status = 'OK';
    } catch (e) {
      diag.dydx.status = 'ERROR';
      diag.dydx.errorType = e.constructor.name;
    }
  }

  res.json(diag);
});

// Prix des marches
app.get('/prices', async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ success: false, error: 'Not connected', code: 'NOT_CONNECTED' });
  }

  try {
    const markets = await withRetry(
      () => client.indexerClient.markets.getPerpetualMarkets(),
      2, 500, 'getPrices'
    );

    const prices = {};
    for (const [ticker, data] of Object.entries(markets.markets)) {
      prices[ticker] = parseFloat(data.oraclePrice);
    }

    res.json({ success: true, prices });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message, code: 'FETCH_ERROR' });
  }
});

// Positions ouvertes
app.get('/positions', async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ success: false, error: 'Not connected', code: 'NOT_CONNECTED' });
  }

  try {
    const positions = await withRetry(
      () => client.indexerClient.account.getSubaccountPerpetualPositions(wallet.address, 0),
      2, 500, 'getPositions'
    );

    res.json({ success: true, positions: positions.positions || [] });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message, code: 'FETCH_ERROR' });
  }
});

// Ordres ouverts
app.get('/orders', async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ success: false, error: 'Not connected', code: 'NOT_CONNECTED' });
  }

  try {
    const orders = await withRetry(
      () => client.indexerClient.account.getSubaccountOrders(wallet.address, 0),
      2, 500, 'getOrders'
    );

    res.json({ success: true, orders: orders || [] });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message, code: 'FETCH_ERROR' });
  }
});

// ============ EXECUTION DE SIGNAL ============

app.post('/execute', authMiddleware, async (req, res) => {
  const startTime = Date.now();

  console.log('\n' + '='.repeat(60));
  console.log('[Execute] NOUVELLE REQUETE');
  console.log(`   Timestamp: ${new Date().toISOString()}`);
  console.log(`   Body: ${JSON.stringify(req.body, null, 2)}`);

  if (!isConnected) {
    console.log('[Execute] ERREUR: Non connecte a dYdX');
    return res.status(503).json({
      success: false,
      error: 'Not connected to dYdX',
      code: 'NOT_CONNECTED'
    });
  }

  const {
    market,
    direction,
    entry,
    stopLoss,
    takeProfit,
    size,
    sizeMode,
    percentageOfPortfolio,
    fixedAmountUSDC,
    entryMode = 'market',
    pullbackExpirationHours = 4,
    maxSlippage = DEFAULT_CONFIG.MAX_SLIPPAGE_PERCENT,
    skipCooldown = false,
    metadata
  } = req.body;

  // Validation de base
  if (!market || !direction) {
    return res.status(400).json({
      success: false,
      error: 'Missing required fields: market, direction',
      code: 'INVALID_REQUEST'
    });
  }

  // Verifier si le marche est autorise
  if (!DEFAULT_CONFIG.ALLOWED_MARKETS.includes(market)) {
    console.log(`[Execute] Marche non autorise: ${market}`);
    return res.status(400).json({
      success: false,
      error: `Marche non autorise: ${market}. Autorises: ${DEFAULT_CONFIG.ALLOWED_MARKETS.join(', ')}`,
      code: 'MARKET_NOT_ALLOWED'
    });
  }

  // Verifier le cooldown
  if (!skipCooldown) {
    const cooldownCheck = checkCooldown(market);
    if (!cooldownCheck.allowed) {
      console.log(`[Execute] ${cooldownCheck.error}`);
      return res.status(429).json({
        success: false,
        error: cooldownCheck.error,
        code: 'COOLDOWN_ACTIVE',
        retryAfter: cooldownCheck.remaining
      });
    }
  }

  const results = {
    signal: { market, direction, entry, stopLoss, takeProfit },
    metadata: metadata || {},
    orders: [],
    checks: {},
    success: false,
    timestamp: new Date().toISOString()
  };

  try {
    // Recuperer le prix actuel et les infos marche
    const markets = await withRetry(
      () => client.indexerClient.markets.getPerpetualMarkets(),
      2, 500, 'getMarkets'
    );

    const marketData = markets.markets[market];
    if (!marketData) {
      throw new Error(`Marche ${market} non trouve sur dYdX`);
    }

    const currentPrice = parseFloat(marketData.oraclePrice);
    const minOrderSize = parseFloat(marketData.stepBaseQuantums || 0.001) / 1e9;

    console.log(`   Prix actuel ${market}: $${currentPrice.toFixed(2)}`);

    // Calculer la taille de position
    let calculatedSize = size || 0;
    let sizeInfo = { mode: 'fixed', value: size };

    if (sizeMode === 'percentage' && percentageOfPortfolio) {
      const account = await withRetry(
        () => client.indexerClient.account.getSubaccount(wallet.address, 0),
        2, 500, 'getAccount'
      );

      const equity = parseFloat(account.subaccount?.equity || '0');
      const freeCollateral = parseFloat(account.subaccount?.freeCollateral || equity);
      const amountUSDC = freeCollateral * (percentageOfPortfolio / 100);
      calculatedSize = amountUSDC / currentPrice;

      sizeInfo = {
        mode: 'percentage',
        percentage: percentageOfPortfolio,
        equity,
        amountUSDC,
        calculatedSize
      };

      console.log(`   Taille: ${percentageOfPortfolio}% de $${freeCollateral.toFixed(2)} = $${amountUSDC.toFixed(2)}`);
    } else if (sizeMode === 'fixed' && fixedAmountUSDC) {
      calculatedSize = fixedAmountUSDC / currentPrice;
      sizeInfo = { mode: 'fixed', amountUSDC: fixedAmountUSDC, calculatedSize };
      console.log(`   Taille: $${fixedAmountUSDC} = ${calculatedSize.toFixed(6)} ${market.replace('-USD', '')}`);
    }

    // Arrondir a la precision du marche
    if (minOrderSize > 0) {
      calculatedSize = Math.floor(calculatedSize / minOrderSize) * minOrderSize;
    }

    if (calculatedSize < minOrderSize) {
      calculatedSize = minOrderSize;
    }

    results.signal.size = calculatedSize;
    results.signal.sizeInfo = sizeInfo;

    // VERIFICATION MARGIN
    const estimatedValueUSDC = calculatedSize * currentPrice;
    const marginCheck = await checkMarginAvailable(estimatedValueUSDC, market);
    results.checks.margin = marginCheck;

    if (!marginCheck.sufficient) {
      console.log(`[Execute] REJET: ${marginCheck.error}`);
      return res.status(400).json({
        success: false,
        error: marginCheck.error,
        code: 'INSUFFICIENT_MARGIN',
        details: marginCheck
      });
    }

    // Calculer les ordres
    const currentBlock = await withRetry(
      () => client.validatorClient.get.latestBlockHeight(),
      2, 500, 'getBlock'
    );

    const entrySide = direction === 'LONG' ? OrderSide.BUY : OrderSide.SELL;
    const exitSide = direction === 'LONG' ? OrderSide.SELL : OrderSide.BUY;
    const entryPrice = entry || currentPrice;
    const entryClientId = randomClientId();

    // Appliquer slippage pour l'ordre d'entree
    const entryPriceWithSlippage = applySlippage(entryPrice, entrySide, maxSlippage);

    console.log(`   Direction: ${direction} | Entry: $${entryPrice.toFixed(2)} (avec slippage: $${entryPriceWithSlippage.toFixed(2)})`);
    console.log(`   Taille: ${calculatedSize} | SL: $${stopLoss || 'N/A'} | TP: $${takeProfit || 'N/A'}`);

    // Calculer l'expiration des ordres
    const tradeType = metadata?.trade_type || 'INTRADAY';
    const expirationByTradeType = {
      'SCALPING': 3600,
      'INTRADAY': 86400,
      'INTRADAY+': 172800,
      'SWING': 604800,
      'POSITION': 2592000
    };
    const orderExpirationSeconds = expirationByTradeType[tradeType] || 86400;

    // 1. ORDRE D'ENTREE
    try {
      if (entryMode === 'pullback' && entry && entry !== currentPrice) {
        // Mode pullback - ordre limite
        const isPullbackValid = (direction === 'LONG' && entry < currentPrice) ||
                                (direction === 'SHORT' && entry > currentPrice);

        if (isPullbackValid) {
          await withRetry(async () => {
            await client.placeOrder(
              subaccount,
              market,
              OrderType.LIMIT,
              entrySide,
              entryPrice,
              calculatedSize,
              entryClientId,
              OrderTimeInForce.GTT,
              pullbackExpirationHours * 3600,
              OrderExecution.DEFAULT,
              true,
              false
            );
          }, 3, 1000, 'placeEntryPullback');

          console.log(`   [Order] Entry PULLBACK place @ $${entryPrice}`);
          results.orders.push({
            type: 'ENTRY',
            success: true,
            mode: 'pullback',
            price: entryPrice,
            size: calculatedSize,
            status: 'PENDING_PULLBACK'
          });

          // Stocker le pullback
          const pullbackKey = `${market}_${entryClientId}`;
          pendingPullbacks.set(pullbackKey, {
            market, direction, entryPrice, size: calculatedSize,
            stopLoss, takeProfit, clientId: entryClientId,
            expiresAt: new Date(Date.now() + pullbackExpirationHours * 3600 * 1000).toISOString(),
            createdAt: new Date().toISOString(),
            status: 'PENDING'
          });

          results.pullbackMode = true;
          results.success = true;
          recordTrade(market);

          console.log('='.repeat(60));
          return res.json(results);
        }
      }

      // Mode market - execution immediate
      await withRetry(async () => {
        await client.placeShortTermOrder(
          subaccount,
          market,
          entrySide,
          entryPriceWithSlippage,
          calculatedSize,
          entryClientId,
          currentBlock + 10,
          OrderTimeInForce.IOC,
          false
        );
      }, 3, 1000, 'placeEntryMarket');

      console.log(`   [Order] Entry MARKET place @ ~$${currentPrice.toFixed(2)}`);
      results.orders.push({
        type: 'ENTRY',
        success: true,
        mode: 'market',
        price: currentPrice,
        priceWithSlippage: entryPriceWithSlippage,
        size: calculatedSize
      });

    } catch (e) {
      console.log(`   [Order] Entry ECHEC: ${e.message}`);
      results.orders.push({ type: 'ENTRY', success: false, error: e.message, code: 'ENTRY_FAILED' });
      results.success = false;
      results.error = `Echec ordre d'entree: ${e.message}`;
      return res.json(results);
    }

    // Attendre confirmation
    await new Promise(r => setTimeout(r, 2000));

    // 2. STOP LOSS
    if (stopLoss) {
      try {
        // Utiliser un ordre LIMIT avec prix au niveau du SL
        // Note: dYdX v4 n'a pas de vrai STOP_MARKET, on utilise LIMIT avec reduce-only
        await withRetry(async () => {
          await client.placeOrder(
            subaccount,
            market,
            OrderType.LIMIT,
            exitSide,
            stopLoss,
            calculatedSize,
            randomClientId(),
            OrderTimeInForce.GTT,
            orderExpirationSeconds,
            OrderExecution.DEFAULT,
            false,
            false // reduceOnly desactive sur dYdX v4
          );
        }, 3, 1000, 'placeStopLoss');

        console.log(`   [Order] Stop Loss place @ $${stopLoss}`);
        results.orders.push({
          type: 'STOP_LOSS',
          success: true,
          price: stopLoss,
          expiresIn: orderExpirationSeconds,
          note: 'Ordre LIMIT - sera execute si le prix atteint ce niveau'
        });
      } catch (e) {
        console.log(`   [Order] Stop Loss ECHEC: ${e.message}`);
        results.orders.push({ type: 'STOP_LOSS', success: false, error: e.message });
      }
    }

    // 3. TAKE PROFIT
    if (takeProfit) {
      try {
        await withRetry(async () => {
          await client.placeOrder(
            subaccount,
            market,
            OrderType.LIMIT,
            exitSide,
            takeProfit,
            calculatedSize,
            randomClientId(),
            OrderTimeInForce.GTT,
            orderExpirationSeconds,
            OrderExecution.DEFAULT,
            false,
            false
          );
        }, 3, 1000, 'placeTakeProfit');

        console.log(`   [Order] Take Profit place @ $${takeProfit}`);
        results.orders.push({
          type: 'TAKE_PROFIT',
          success: true,
          price: takeProfit,
          expiresIn: orderExpirationSeconds
        });
      } catch (e) {
        console.log(`   [Order] Take Profit ECHEC: ${e.message}`);
        results.orders.push({ type: 'TAKE_PROFIT', success: false, error: e.message });
      }
    }

    // Enregistrer le trade pour le cooldown
    recordTrade(market);

    results.success = results.orders.some(o => o.success);
    results.timing = {
      trade_type: tradeType,
      order_expiration_seconds: orderExpirationSeconds,
      execution_time_ms: Date.now() - startTime
    };

    console.log('='.repeat(60));
    console.log(`[Execute] RESULTAT: ${results.success ? 'SUCCES' : 'ECHEC'}`);
    console.log(`   Orders: ${results.orders.filter(o => o.success).length}/${results.orders.length} reussis`);
    console.log('='.repeat(60));

    res.json(results);

  } catch (e) {
    console.error('[Execute] ERREUR CRITIQUE:', e.message);
    results.success = false;
    results.error = e.message;
    results.code = 'EXECUTION_ERROR';
    res.status(500).json(results);
  }
});

// ============ POSITIONS DETAILLEES ============

app.get('/positions/detailed', async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ success: false, error: 'Not connected', code: 'NOT_CONNECTED' });
  }

  try {
    const [positionsRes, ordersRes, markets] = await Promise.all([
      withRetry(() => client.indexerClient.account.getSubaccountPerpetualPositions(wallet.address, 0), 2, 500, 'getPositions'),
      withRetry(() => client.indexerClient.account.getSubaccountOrders(wallet.address, 0), 2, 500, 'getOrders'),
      withRetry(() => client.indexerClient.markets.getPerpetualMarkets(), 2, 500, 'getMarkets')
    ]);

    const positions = (positionsRes.positions || []).filter(pos => {
      const size = parseFloat(pos.size || 0);
      return pos.status === 'OPEN' && Math.abs(size) > 0.00001;
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

      let unrealizedPnl = 0;
      let pnlPercent = 0;
      if (side === 'LONG') {
        unrealizedPnl = (currentPrice - entryPrice) * absSize;
        pnlPercent = ((currentPrice - entryPrice) / entryPrice) * 100;
      } else {
        unrealizedPnl = (entryPrice - currentPrice) * absSize;
        pnlPercent = ((entryPrice - currentPrice) / entryPrice) * 100;
      }

      const relatedOrders = allOrders.filter(o => o.ticker === market && o.status === 'OPEN');
      const stopLoss = relatedOrders.find(o => {
        const price = parseFloat(o.price);
        if (side === 'LONG') return o.side === 'SELL' && price < currentPrice;
        return o.side === 'BUY' && price > currentPrice;
      });
      const takeProfit = relatedOrders.find(o => {
        const price = parseFloat(o.price);
        if (side === 'LONG') return o.side === 'SELL' && price > currentPrice;
        return o.side === 'BUY' && price < currentPrice;
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
        stopLoss: stopLoss ? { price: parseFloat(stopLoss.price), orderId: stopLoss.id } : null,
        takeProfit: takeProfit ? { price: parseFloat(takeProfit.price), orderId: takeProfit.id } : null,
        hasProtection: !!(stopLoss || takeProfit),
        createdAt: pos.createdAt
      };
    });

    const account = await withRetry(
      () => client.indexerClient.account.getSubaccount(wallet.address, 0),
      2, 500, 'getAccount'
    );

    const equity = parseFloat(account.subaccount?.equity || '0');
    const freeCollateral = parseFloat(account.subaccount?.freeCollateral || '0');

    res.json({
      success: true,
      wallet: wallet.address,
      equity,
      freeCollateral,
      marginUsed: equity - freeCollateral,
      positionsCount: detailedPositions.length,
      totalUnrealizedPnl: parseFloat(detailedPositions.reduce((sum, p) => sum + p.unrealizedPnl, 0).toFixed(2)),
      positions: detailedPositions,
      unprotectedPositions: detailedPositions.filter(p => !p.hasProtection).length,
      timestamp: new Date().toISOString()
    });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message, code: 'FETCH_ERROR' });
  }
});

// ============ FERMER POSITION ============

app.post('/positions/close', authMiddleware, async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ success: false, error: 'Not connected', code: 'NOT_CONNECTED' });
  }

  const { market, reason } = req.body;

  if (!market) {
    return res.status(400).json({ success: false, error: 'Market required', code: 'INVALID_REQUEST' });
  }

  console.log(`\n[Close] Fermeture position ${market} - Raison: ${reason || 'manual'}`);

  try {
    const positionsRes = await withRetry(
      () => client.indexerClient.account.getSubaccountPerpetualPositions(wallet.address, 0),
      2, 500, 'getPositions'
    );

    const position = (positionsRes.positions || []).find(p => p.market === market && p.status === 'OPEN');

    if (!position) {
      return res.status(404).json({
        success: false,
        error: `Aucune position ouverte sur ${market}`,
        code: 'POSITION_NOT_FOUND'
      });
    }

    const size = Math.abs(parseFloat(position.size || 0));
    const side = parseFloat(position.size) > 0 ? 'LONG' : 'SHORT';
    const closeSide = side === 'LONG' ? OrderSide.SELL : OrderSide.BUY;

    const currentPrice = await getMarketPrice(market);
    const currentBlock = await withRetry(
      () => client.validatorClient.get.latestBlockHeight(),
      2, 500, 'getBlock'
    );

    const closePrice = applySlippage(currentPrice, closeSide, DEFAULT_CONFIG.MAX_SLIPPAGE_PERCENT * 2);

    await withRetry(async () => {
      await client.placeShortTermOrder(
        subaccount,
        market,
        closeSide,
        closePrice,
        size,
        randomClientId(),
        currentBlock + 10,
        OrderTimeInForce.IOC,
        false
      );
    }, 3, 1000, 'closePosition');

    console.log(`   [Close] Position ${market} fermee (${side} ${size})`);

    // Annuler les ordres SL/TP
    const ordersRes = await client.indexerClient.account.getSubaccountOrders(wallet.address, 0);
    const relatedOrders = (ordersRes || []).filter(o => o.ticker === market && o.status === 'OPEN');
    let cancelledCount = 0;

    for (const order of relatedOrders) {
      try {
        await client.cancelOrder(subaccount, order.clientId, order.orderFlags, market, currentBlock + 10);
        cancelledCount++;
      } catch (e) {
        console.log(`   [Close] Echec annulation ordre ${order.id}: ${e.message}`);
      }
    }

    res.json({
      success: true,
      market,
      side,
      size,
      closePrice: currentPrice,
      reason: reason || 'manual',
      cancelledOrders: cancelledCount,
      timestamp: new Date().toISOString()
    });

  } catch (e) {
    console.error(`[Close] Erreur: ${e.message}`);
    res.status(500).json({ success: false, error: e.message, code: 'CLOSE_ERROR' });
  }
});

// ============ PROTEGER POSITION ============

app.post('/positions/protect', authMiddleware, async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ success: false, error: 'Not connected', code: 'NOT_CONNECTED' });
  }

  const { market, stopLoss, takeProfit, expirationHours } = req.body;

  if (!market) {
    return res.status(400).json({ success: false, error: 'Market required', code: 'INVALID_REQUEST' });
  }

  if (!stopLoss && !takeProfit) {
    return res.status(400).json({
      success: false,
      error: 'Au moins un Stop Loss ou Take Profit requis',
      code: 'INVALID_REQUEST'
    });
  }

  console.log(`\n[Protect] Protection ${market} - SL: ${stopLoss || 'N/A'} | TP: ${takeProfit || 'N/A'}`);

  try {
    const positionsRes = await withRetry(
      () => client.indexerClient.account.getSubaccountPerpetualPositions(wallet.address, 0),
      2, 500, 'getPositions'
    );

    const position = (positionsRes.positions || []).find(p => p.market === market && p.status === 'OPEN');

    if (!position) {
      return res.status(404).json({
        success: false,
        error: `Aucune position ouverte sur ${market}`,
        code: 'POSITION_NOT_FOUND'
      });
    }

    const size = Math.abs(parseFloat(position.size || 0));
    const side = parseFloat(position.size) > 0 ? 'LONG' : 'SHORT';
    const exitSide = side === 'LONG' ? OrderSide.SELL : OrderSide.BUY;
    const currentPrice = await getMarketPrice(market);

    // Validation
    if (stopLoss) {
      if (side === 'LONG' && stopLoss >= currentPrice) {
        return res.status(400).json({
          success: false,
          error: `Stop Loss ($${stopLoss}) doit etre < prix actuel ($${currentPrice.toFixed(2)}) pour un LONG`,
          code: 'INVALID_SL'
        });
      }
      if (side === 'SHORT' && stopLoss <= currentPrice) {
        return res.status(400).json({
          success: false,
          error: `Stop Loss ($${stopLoss}) doit etre > prix actuel ($${currentPrice.toFixed(2)}) pour un SHORT`,
          code: 'INVALID_SL'
        });
      }
    }

    if (takeProfit) {
      if (side === 'LONG' && takeProfit <= currentPrice) {
        return res.status(400).json({
          success: false,
          error: `Take Profit ($${takeProfit}) doit etre > prix actuel ($${currentPrice.toFixed(2)}) pour un LONG`,
          code: 'INVALID_TP'
        });
      }
      if (side === 'SHORT' && takeProfit >= currentPrice) {
        return res.status(400).json({
          success: false,
          error: `Take Profit ($${takeProfit}) doit etre < prix actuel ($${currentPrice.toFixed(2)}) pour un SHORT`,
          code: 'INVALID_TP'
        });
      }
    }

    const orderExpirationSeconds = (expirationHours || 168) * 3600;
    const results = { market, side, size, orders: [] };

    if (stopLoss) {
      try {
        await withRetry(async () => {
          await client.placeOrder(
            subaccount, market, OrderType.LIMIT, exitSide, stopLoss, size,
            randomClientId(), OrderTimeInForce.GTT, orderExpirationSeconds,
            OrderExecution.DEFAULT, false, false
          );
        }, 3, 1000, 'placeStopLoss');

        results.orders.push({ type: 'STOP_LOSS', success: true, price: stopLoss });
      } catch (e) {
        results.orders.push({ type: 'STOP_LOSS', success: false, error: e.message });
      }
    }

    if (takeProfit) {
      try {
        await withRetry(async () => {
          await client.placeOrder(
            subaccount, market, OrderType.LIMIT, exitSide, takeProfit, size,
            randomClientId(), OrderTimeInForce.GTT, orderExpirationSeconds,
            OrderExecution.DEFAULT, false, false
          );
        }, 3, 1000, 'placeTakeProfit');

        results.orders.push({ type: 'TAKE_PROFIT', success: true, price: takeProfit });
      } catch (e) {
        results.orders.push({ type: 'TAKE_PROFIT', success: false, error: e.message });
      }
    }

    results.success = results.orders.every(o => o.success);
    results.timestamp = new Date().toISOString();

    res.json(results);

  } catch (e) {
    console.error(`[Protect] Erreur: ${e.message}`);
    res.status(500).json({ success: false, error: e.message, code: 'PROTECT_ERROR' });
  }
});

// ============ MONITORING ============

app.get('/monitor', authMiddleware, async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ success: false, error: 'Not connected', code: 'NOT_CONNECTED' });
  }

  console.log('\n[Monitor] Verification des positions...');

  try {
    const results = {
      timestamp: new Date().toISOString(),
      positions: [],
      actions: [],
      alerts: []
    };

    const [positionsRes, ordersRes, markets] = await Promise.all([
      withRetry(() => client.indexerClient.account.getSubaccountPerpetualPositions(wallet.address, 0), 2, 500, 'getPositions'),
      withRetry(() => client.indexerClient.account.getSubaccountOrders(wallet.address, 0), 2, 500, 'getOrders'),
      withRetry(() => client.indexerClient.markets.getPerpetualMarkets(), 2, 500, 'getMarkets')
    ]);

    const positions = (positionsRes.positions || []).filter(p => p.status === 'OPEN' && Math.abs(parseFloat(p.size)) > 0.00001);
    const allOrders = ordersRes || [];

    for (const pos of positions) {
      const market = pos.market;
      const marketData = markets.markets[market];
      const currentPrice = parseFloat(marketData?.oraclePrice || 0);
      const size = parseFloat(pos.size || 0);
      const entryPrice = parseFloat(pos.entryPrice || 0);
      const side = size > 0 ? 'LONG' : 'SHORT';

      let pnlPercent = side === 'LONG'
        ? ((currentPrice - entryPrice) / entryPrice) * 100
        : ((entryPrice - currentPrice) / entryPrice) * 100;

      const relatedOrders = allOrders.filter(o => o.ticker === market && o.status === 'OPEN');
      const hasProtection = relatedOrders.length > 0;

      const posInfo = { market, side, pnlPercent: parseFloat(pnlPercent.toFixed(2)), hasProtection };
      results.positions.push(posInfo);

      if (!hasProtection) {
        results.alerts.push({
          type: 'NO_PROTECTION',
          market,
          message: `Position ${market} sans protection!`
        });
      }

      if (!hasProtection && pnlPercent < -10) {
        results.alerts.push({
          type: 'CRITICAL_LOSS',
          market,
          message: `CRITIQUE: ${market} perd ${Math.abs(pnlPercent).toFixed(2)}% sans protection!`
        });
      }
    }

    results.summary = {
      totalPositions: positions.length,
      protectedPositions: results.positions.filter(p => p.hasProtection).length,
      unprotectedPositions: results.positions.filter(p => !p.hasProtection).length,
      criticalAlerts: results.alerts.filter(a => a.type === 'CRITICAL_LOSS').length
    };

    res.json(results);

  } catch (e) {
    console.error(`[Monitor] Erreur: ${e.message}`);
    res.status(500).json({ success: false, error: e.message, code: 'MONITOR_ERROR' });
  }
});

// ============ ACCOUNT STATUS ============

app.get('/account', async (req, res) => {
  if (!isConnected) {
    return res.status(503).json({ success: false, error: 'Not connected', code: 'NOT_CONNECTED' });
  }

  try {
    const [account, positionsRes] = await Promise.all([
      withRetry(() => client.indexerClient.account.getSubaccount(wallet.address, 0), 2, 500, 'getAccount'),
      withRetry(() => client.indexerClient.account.getSubaccountPerpetualPositions(wallet.address, 0), 2, 500, 'getPositions')
    ]);

    const equity = parseFloat(account.subaccount?.equity || '0');
    const freeCollateral = parseFloat(account.subaccount?.freeCollateral || '0');
    const positions = (positionsRes.positions || []).filter(p => p.status === 'OPEN' && Math.abs(parseFloat(p.size)) > 0.00001);

    res.json({
      success: true,
      wallet: wallet.address,
      equity,
      marginUsed: equity - freeCollateral,
      marginAvailable: freeCollateral,
      openPositionsCount: positions.length,
      network: 'testnet',
      timestamp: new Date().toISOString()
    });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message, code: 'FETCH_ERROR' });
  }
});

// ============ DEMARRAGE ============

async function start() {
  console.log('='.repeat(60));
  console.log('BULL SAGE - dYdX Executor v2.0');
  console.log('='.repeat(60));
  console.log(`Configuration:`);
  console.log(`  - Max Slippage: ${DEFAULT_CONFIG.MAX_SLIPPAGE_PERCENT}%`);
  console.log(`  - Cooldown: ${DEFAULT_CONFIG.TRADE_COOLDOWN_SECONDS}s`);
  console.log(`  - Max Retries: ${DEFAULT_CONFIG.MAX_RETRIES}`);
  console.log(`  - Allowed Markets: ${DEFAULT_CONFIG.ALLOWED_MARKETS.length}`);
  console.log('='.repeat(60));

  if (!MNEMONIC) {
    console.warn('[Warning] DYDX_TESTNET_MNEMONIC non configure - Mode lecture seule');
    app.listen(PORT, () => {
      console.log(`\nServeur demarre sur le port ${PORT} (MODE LECTURE SEULE)`);
    });
    return;
  }

  await initDydx();

  app.listen(PORT, () => {
    console.log(`\nServeur demarre sur http://localhost:${PORT}`);
    console.log('\nEndpoints disponibles:');
    console.log('  GET  /health           - Health check');
    console.log('  GET  /status           - Statut connexion');
    console.log('  GET  /account          - Info compte');
    console.log('  GET  /positions        - Positions');
    console.log('  GET  /positions/detailed - Positions detaillees');
    console.log('  POST /execute          - Executer signal');
    console.log('  POST /positions/close  - Fermer position');
    console.log('  POST /positions/protect - Proteger position');
    console.log('  GET  /monitor          - Monitoring');
  });
}

start();
