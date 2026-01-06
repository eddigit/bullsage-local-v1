/**
 * 🐂 BULL SAGE - Exécuteur dYdX v4
 * 
 * Ce script exécute réellement des ordres sur dYdX Testnet
 * Utilise le SDK officiel @dydxprotocol/v4-client-js
 */

import { 
  CompositeClient,
  Network,
  OrderSide,
  OrderType,
  OrderTimeInForce,
  OrderExecution,
  SubaccountClient
} from '@dydxprotocol/v4-client-js';
import * as dotenv from 'dotenv';
import * as path from 'path';

// Charger le .env du backend
dotenv.config({ path: path.join(__dirname, '../backend/.env') });

const MNEMONIC = process.env.DYDX_TESTNET_MNEMONIC || '';

interface Signal {
  market: string;
  direction: 'LONG' | 'SHORT';
  entry: number;
  stopLoss: number;
  takeProfit: number;
  size: number;
}

class DydxExecutor {
  private client: CompositeClient | null = null;
  private subaccount: SubaccountClient | null = null;

  async connect(): Promise<boolean> {
    try {
      console.log('🔌 Connexion à dYdX Testnet...');
      
      this.client = await CompositeClient.connect(Network.testnet());
      
      if (!MNEMONIC) {
        console.error('❌ DYDX_TESTNET_MNEMONIC non configuré dans .env');
        return false;
      }

      // Créer le subaccount depuis le mnemonic
      const localWallet = await this.client.validatorClient.post.generateWallet(MNEMONIC);
      this.subaccount = new SubaccountClient(localWallet, 0);
      
      console.log(`✅ Connecté! Adresse: ${this.subaccount.address}`);
      return true;
    } catch (error) {
      console.error('❌ Erreur connexion:', error);
      return false;
    }
  }

  async getAccountInfo(): Promise<void> {
    if (!this.client || !this.subaccount) return;

    try {
      const response = await this.client.indexerClient.account.getSubaccount(
        this.subaccount.address,
        0
      );
      
      const equity = parseFloat(response.subaccount?.equity || '0');
      const freeCollateral = parseFloat(response.subaccount?.freeCollateral || '0');
      
      console.log(`\n💰 Compte:`);
      console.log(`   Equity: $${equity.toLocaleString()}`);
      console.log(`   Free Collateral: $${freeCollateral.toLocaleString()}`);
    } catch (error) {
      console.error('❌ Erreur récupération compte:', error);
    }
  }

  async getMarketPrice(market: string): Promise<number | null> {
    if (!this.client) return null;

    try {
      const response = await this.client.indexerClient.markets.getPerpetualMarkets();
      const marketData = response.markets?.[market];
      return marketData ? parseFloat(marketData.oraclePrice) : null;
    } catch (error) {
      console.error(`❌ Erreur prix ${market}:`, error);
      return null;
    }
  }

  async placeOrder(
    market: string,
    side: 'BUY' | 'SELL',
    size: number,
    price: number,
    orderType: 'MARKET' | 'LIMIT' | 'STOP_LIMIT' = 'LIMIT',
    triggerPrice?: number
  ): Promise<any> {
    if (!this.client || !this.subaccount) {
      throw new Error('Non connecté');
    }

    const clientId = Math.floor(Math.random() * 1000000000);
    
    console.log(`\n📤 Placement ordre ${orderType}:`);
    console.log(`   ${side} ${size} ${market} @ $${price.toLocaleString()}`);
    if (triggerPrice) {
      console.log(`   Trigger: $${triggerPrice.toLocaleString()}`);
    }

    try {
      // Récupérer les infos du marché
      const marketsResponse = await this.client.indexerClient.markets.getPerpetualMarkets();
      const marketInfo = marketsResponse.markets?.[market];
      
      if (!marketInfo) {
        throw new Error(`Marché ${market} non trouvé`);
      }

      // Calculer les quantums
      const orderSide = side === 'BUY' ? OrderSide.BUY : OrderSide.SELL;
      
      let response;
      
      if (orderType === 'MARKET') {
        // Ordre Market (short-term IOC)
        response = await this.client.placeShortTermOrder(
          this.subaccount,
          market,
          orderSide,
          price,
          size,
          clientId,
          0, // goodTilBlock (0 = current + default)
          OrderTimeInForce.IOC,
          false // reduceOnly
        );
      } else if (orderType === 'LIMIT') {
        // Ordre Limit
        response = await this.client.placeOrder(
          this.subaccount,
          market,
          OrderType.LIMIT,
          orderSide,
          price,
          size,
          clientId,
          OrderTimeInForce.GTT,
          60, // 60 seconds
          OrderExecution.DEFAULT,
          false, // postOnly
          false, // reduceOnly
          triggerPrice || undefined
        );
      } else if (orderType === 'STOP_LIMIT' && triggerPrice) {
        // Stop Loss / Take Profit
        response = await this.client.placeOrder(
          this.subaccount,
          market,
          OrderType.STOP_LIMIT,
          orderSide,
          price,
          size,
          clientId,
          OrderTimeInForce.GTT,
          86400, // 24 hours
          OrderExecution.DEFAULT,
          false,
          true, // reduceOnly for SL/TP
          triggerPrice
        );
      }

      console.log(`   ✅ Ordre placé! Client ID: ${clientId}`);
      return { success: true, clientId, response };
      
    } catch (error: any) {
      console.error(`   ❌ Erreur: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  async executeSignal(signal: Signal): Promise<any> {
    console.log('\n' + '='.repeat(60));
    console.log(`🎯 EXÉCUTION SIGNAL ${signal.direction} ${signal.market}`);
    console.log('='.repeat(60));

    console.log(`\n📋 Signal:`);
    console.log(`   Direction: ${signal.direction}`);
    console.log(`   Entry: $${signal.entry.toLocaleString()}`);
    console.log(`   Stop Loss: $${signal.stopLoss.toLocaleString()}`);
    console.log(`   Take Profit: $${signal.takeProfit.toLocaleString()}`);
    console.log(`   Size: ${signal.size}`);

    const results: any = {
      signal,
      orders: [],
      success: false
    };

    // 1. Ordre d'entrée (Market)
    const entrySide = signal.direction === 'LONG' ? 'BUY' : 'SELL';
    const entryResult = await this.placeOrder(
      signal.market,
      entrySide,
      signal.size,
      signal.entry,
      'MARKET'
    );
    results.orders.push({ type: 'ENTRY', ...entryResult });

    if (!entryResult.success) {
      console.log('\n❌ Échec de l\'ordre d\'entrée, annulation des SL/TP');
      return results;
    }

    // Attendre un peu pour que l'ordre soit exécuté
    await new Promise(resolve => setTimeout(resolve, 2000));

    // 2. Stop Loss
    const slSide = signal.direction === 'LONG' ? 'SELL' : 'BUY';
    const slResult = await this.placeOrder(
      signal.market,
      slSide,
      signal.size,
      signal.stopLoss,
      'STOP_LIMIT',
      signal.stopLoss
    );
    results.orders.push({ type: 'STOP_LOSS', ...slResult });

    // 3. Take Profit
    const tpResult = await this.placeOrder(
      signal.market,
      slSide,
      signal.size,
      signal.takeProfit,
      'STOP_LIMIT',
      signal.takeProfit
    );
    results.orders.push({ type: 'TAKE_PROFIT', ...tpResult });

    results.success = results.orders.every((o: any) => o.success);

    console.log('\n' + '='.repeat(60));
    console.log('📊 RÉSUMÉ:');
    console.log('='.repeat(60));
    
    for (const order of results.orders) {
      const icon = order.success ? '✅' : '❌';
      console.log(`   ${icon} ${order.type}: ${order.success ? 'OK' : order.error}`);
    }

    return results;
  }
}

// Exécution principale
async function main() {
  console.log('='.repeat(60));
  console.log('🐂 BULL SAGE - Exécuteur dYdX v4 Testnet');
  console.log('='.repeat(60));

  const executor = new DydxExecutor();
  
  // Connexion
  const connected = await executor.connect();
  if (!connected) {
    process.exit(1);
  }

  // Infos compte
  await executor.getAccountInfo();

  // Prix actuel
  const btcPrice = await executor.getMarketPrice('BTC-USD');
  if (!btcPrice) {
    console.error('❌ Impossible de récupérer le prix BTC');
    process.exit(1);
  }
  console.log(`\n📊 Prix BTC-USD: $${btcPrice.toLocaleString()}`);

  // Créer un signal de test
  const signal: Signal = {
    market: 'BTC-USD',
    direction: 'LONG',
    entry: btcPrice,
    stopLoss: btcPrice * 0.98,  // -2%
    takeProfit: btcPrice * 1.04, // +4%
    size: 0.001  // Petite taille pour test
  };

  // Exécuter le signal
  const result = await executor.executeSignal(signal);

  // Afficher le JSON final
  console.log('\n📋 JSON du signal:');
  console.log(JSON.stringify(signal, null, 2));

  if (result.success) {
    console.log('\n🎉 Signal exécuté avec succès sur dYdX Testnet!');
  } else {
    console.log('\n⚠️ Certains ordres ont échoué');
  }
}

main().catch(console.error);
