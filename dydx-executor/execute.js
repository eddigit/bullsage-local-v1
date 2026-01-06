/**
 * 🐂 BULL SAGE - Exécuteur dYdX v4 COMPLET
 * 
 * Exécute Entry + Stop Loss + Take Profit sur dYdX Testnet
 */

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

dotenv.config({ path: path.join(__dirname, '../backend/.env') });

const MNEMONIC = process.env.DYDX_TESTNET_MNEMONIC || '';

// Fonction pour générer un clientId unique
function randomClientId() {
  return Math.floor(Math.random() * 100000000);
}

// Fonction d'attente
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function executeFullSignal(client, subaccount, signal) {
  console.log('\n' + '='.repeat(60));
  console.log(`🎯 EXÉCUTION SIGNAL COMPLET: ${signal.direction} ${signal.market}`);
  console.log('='.repeat(60));

  const results = {
    signal,
    orders: [],
    success: false
  };

  // Récupérer le bloc actuel
  const currentBlock = await client.validatorClient.get.latestBlockHeight();

  // 1. ORDRE D'ENTRÉE (Market/IOC)
  console.log('\n📤 1. ORDRE D\'ENTRÉE...');
  const entrySide = signal.direction === 'LONG' ? OrderSide.BUY : OrderSide.SELL;
  const entryClientId = randomClientId();
  
  try {
    const entryTx = await client.placeShortTermOrder(
      subaccount,
      signal.market,
      entrySide,
      signal.entry * (signal.direction === 'LONG' ? 1.005 : 0.995), // Slippage 0.5%
      signal.size,
      entryClientId,
      currentBlock + 10,
      OrderTimeInForce.IOC,
      false
    );
    
    console.log(`   ✅ Entry placé! ClientId: ${entryClientId}`);
    results.orders.push({ type: 'ENTRY', success: true, clientId: entryClientId, tx: entryTx });
  } catch (e) {
    console.log(`   ❌ Entry échoué: ${e.message}`);
    results.orders.push({ type: 'ENTRY', success: false, error: e.message });
    return results;
  }

  // Attendre que l'ordre soit exécuté
  await sleep(3000);

  // 2. STOP LOSS (Short-term IOC car reduce-only)
  console.log('\n📤 2. STOP LOSS...');
  const slSide = signal.direction === 'LONG' ? OrderSide.SELL : OrderSide.BUY;
  const slClientId = randomClientId();
  const slBlock = await client.validatorClient.get.latestBlockHeight();
  
  try {
    // Sur dYdX v4, utiliser des ordres long-term (GTT) pour SL/TP
    // Les ordres short-term avec reduce-only sont désactivés
    const slTx = await client.placeOrder(
      subaccount,
      signal.market,
      OrderType.STOP_LIMIT,
      slSide,
      signal.stopLoss,
      signal.size,
      slClientId,
      OrderTimeInForce.GTT,
      86400, // 24 heures
      OrderExecution.DEFAULT,
      false, // postOnly
      false  // reduceOnly désactivé
    );
    
    console.log(`   ✅ Stop Loss placé @ $${signal.stopLoss.toLocaleString()}`);
    results.orders.push({ type: 'STOP_LOSS', success: true, clientId: slClientId, price: signal.stopLoss });
  } catch (e) {
    // Fallback: ordre limit normal sans reduce-only
    try {
      const slTx2 = await client.placeOrder(
        subaccount,
        signal.market,
        OrderType.LIMIT,
        slSide,
        signal.stopLoss,
        signal.size,
        slClientId + 1,
        OrderTimeInForce.GTT,
        86400,
        OrderExecution.DEFAULT,
        false,
        false  // Sans reduce-only
      );
      console.log(`   ✅ Stop Loss (limit) placé @ $${signal.stopLoss.toLocaleString()}`);
      results.orders.push({ type: 'STOP_LOSS', success: true, clientId: slClientId + 1, price: signal.stopLoss });
    } catch (e2) {
      console.log(`   ⚠️ Stop Loss échoué: ${e2.message}`);
      results.orders.push({ type: 'STOP_LOSS', success: false, error: e2.message });
    }
  }

  await sleep(2000);

  // 3. TAKE PROFIT (Short-term IOC)
  console.log('\n📤 3. TAKE PROFIT...');
  const tpClientId = randomClientId();
  const tpBlock = await client.validatorClient.get.latestBlockHeight();
  
  try {
    // Ordre long-term pour Take Profit
    const tpTx = await client.placeOrder(
      subaccount,
      signal.market,
      OrderType.LIMIT,
      slSide,
      signal.takeProfit,
      signal.size,
      tpClientId,
      OrderTimeInForce.GTT,
      86400, // 24 heures
      OrderExecution.DEFAULT,
      false, // postOnly
      false  // reduceOnly désactivé
    );
    
    console.log(`   ✅ Take Profit placé @ $${signal.takeProfit.toLocaleString()}`);
    results.orders.push({ type: 'TAKE_PROFIT', success: true, clientId: tpClientId, price: signal.takeProfit });
  } catch (e) {
    // Fallback: ordre limit normal
    try {
      const tpTx2 = await client.placeOrder(
        subaccount,
        signal.market,
        OrderType.LIMIT,
        slSide,
        signal.takeProfit,
        signal.size,
        tpClientId + 1,
        OrderTimeInForce.GTT,
        86400,
        OrderExecution.DEFAULT,
        false,
        false
      );
      console.log(`   ✅ Take Profit (limit) placé @ $${signal.takeProfit.toLocaleString()}`);
      results.orders.push({ type: 'TAKE_PROFIT', success: true, clientId: tpClientId + 1, price: signal.takeProfit });
    } catch (e2) {
      console.log(`   ⚠️ Take Profit échoué: ${e2.message}`);
      results.orders.push({ type: 'TAKE_PROFIT', success: false, error: e2.message });
    }
  }

  results.success = results.orders.filter(o => o.success).length >= 1;
  return results;
}

async function main() {
  console.log('='.repeat(60));
  console.log('🐂 BULL SAGE - Exécuteur dYdX v4 COMPLET');
  console.log('='.repeat(60));

  if (!MNEMONIC) {
    console.error('❌ DYDX_TESTNET_MNEMONIC non configuré');
    process.exit(1);
  }

  try {
    // Connexion
    console.log('\n🔌 Connexion à dYdX Testnet...');
    const client = await CompositeClient.connect(Network.testnet());
    console.log('✅ Client connecté');

    // Wallet
    console.log('\n🔐 Création du wallet...');
    const wallet = await LocalWallet.fromMnemonic(MNEMONIC, 'dydx');
    const subaccount = SubaccountInfo.forLocalWallet(wallet, 0);
    console.log(`✅ Wallet: ${wallet.address}`);

    // Compte
    console.log('\n💰 Récupération du compte...');
    const account = await client.indexerClient.account.getSubaccount(wallet.address, 0);
    const equity = parseFloat(account.subaccount?.equity || '0');
    console.log(`   Equity: $${equity.toLocaleString()}`);

    // Prix des cryptos
    console.log('\n📊 Prix actuels...');
    const markets = await client.indexerClient.markets.getPerpetualMarkets();
    
    const btcPrice = parseFloat(markets.markets['BTC-USD'].oraclePrice);
    const ethPrice = parseFloat(markets.markets['ETH-USD'].oraclePrice);
    const solPrice = parseFloat(markets.markets['SOL-USD'].oraclePrice);
    
    console.log(`   BTC: $${btcPrice.toLocaleString()}`);
    console.log(`   ETH: $${ethPrice.toLocaleString()}`);
    console.log(`   SOL: $${solPrice.toLocaleString()}`);

    // ============ SIGNAL 1: BTC LONG ============
    const btcSignal = {
      market: 'BTC-USD',
      direction: 'LONG',
      entry: btcPrice,
      stopLoss: btcPrice * 0.98,
      takeProfit: btcPrice * 1.04,
      size: 0.001
    };
    
    console.log('\n📋 Signal BTC:');
    console.log(`   ${btcSignal.direction} @ $${btcSignal.entry.toLocaleString()}`);
    console.log(`   SL: $${btcSignal.stopLoss.toLocaleString()} | TP: $${btcSignal.takeProfit.toLocaleString()}`);
    
    const btcResult = await executeFullSignal(client, subaccount, btcSignal);

    await sleep(5000);

    // ============ SIGNAL 2: ETH LONG ============
    const ethSignal = {
      market: 'ETH-USD',
      direction: 'LONG',
      entry: ethPrice,
      stopLoss: ethPrice * 0.97,
      takeProfit: ethPrice * 1.06,
      size: 0.01
    };
    
    console.log('\n📋 Signal ETH:');
    console.log(`   ${ethSignal.direction} @ $${ethSignal.entry.toLocaleString()}`);
    console.log(`   SL: $${ethSignal.stopLoss.toLocaleString()} | TP: $${ethSignal.takeProfit.toLocaleString()}`);
    
    const ethResult = await executeFullSignal(client, subaccount, ethSignal);

    await sleep(5000);

    // ============ SIGNAL 3: SOL LONG ============
    const solSignal = {
      market: 'SOL-USD',
      direction: 'LONG',
      entry: solPrice,
      stopLoss: solPrice * 0.95,
      takeProfit: solPrice * 1.10,
      size: 0.1
    };
    
    console.log('\n📋 Signal SOL:');
    console.log(`   ${solSignal.direction} @ $${solSignal.entry.toLocaleString()}`);
    console.log(`   SL: $${solSignal.stopLoss.toLocaleString()} | TP: $${solSignal.takeProfit.toLocaleString()}`);
    
    const solResult = await executeFullSignal(client, subaccount, solSignal);

    // ============ RÉSUMÉ FINAL ============
    console.log('\n' + '='.repeat(60));
    console.log('📊 RÉSUMÉ FINAL');
    console.log('='.repeat(60));

    const allResults = [
      { name: 'BTC', ...btcResult },
      { name: 'ETH', ...ethResult },
      { name: 'SOL', ...solResult }
    ];

    for (const r of allResults) {
      const entryOk = r.orders.find(o => o.type === 'ENTRY')?.success ? '✅' : '❌';
      const slOk = r.orders.find(o => o.type === 'STOP_LOSS')?.success ? '✅' : '⚠️';
      const tpOk = r.orders.find(o => o.type === 'TAKE_PROFIT')?.success ? '✅' : '⚠️';
      
      console.log(`\n${r.name}-USD ${r.signal.direction}:`);
      console.log(`   ${entryOk} Entry @ $${r.signal.entry.toLocaleString()}`);
      console.log(`   ${slOk} Stop Loss @ $${r.signal.stopLoss.toLocaleString()}`);
      console.log(`   ${tpOk} Take Profit @ $${r.signal.takeProfit.toLocaleString()}`);
    }

    // JSON des signaux
    console.log('\n' + '='.repeat(60));
    console.log('📋 JSON DES SIGNAUX:');
    console.log('='.repeat(60));
    console.log(JSON.stringify([btcSignal, ethSignal, solSignal], null, 2));

    console.log('\n🎉 TERMINÉ!');
    console.log('👉 Vérifie sur: https://v4.testnet.dydx.exchange/portfolio/orders');
    console.log('👉 Positions: https://v4.testnet.dydx.exchange/portfolio/positions');

  } catch (error) {
    console.error('\n❌ Erreur:', error.message);
  }
}

main();
