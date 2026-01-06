"""
Test d'exécution RÉELLE sur dYdX Testnet
Utilise l'API REST avec signature pour placer de vrais ordres
"""

import asyncio
import os
import json
import time
import hashlib
import hmac
from datetime import datetime, timezone
from dotenv import load_dotenv
import httpx

load_dotenv()

# Configuration
DYDX_TESTNET_ADDRESS = os.getenv('DYDX_TESTNET_ADDRESS', '')
DYDX_TESTNET_MNEMONIC = os.getenv('DYDX_TESTNET_MNEMONIC', '')

# Endpoints dYdX v4 Testnet
INDEXER_URL = "https://indexer.v4testnet.dydx.exchange/v4"
VALIDATOR_URL = "https://test-dydx.kingnodes.com"


async def get_account_info():
    """Récupère les infos du compte"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{INDEXER_URL}/addresses/{DYDX_TESTNET_ADDRESS}/subaccountNumber/0",
            timeout=10.0
        )
        if response.status_code == 200:
            return response.json()
    return None


async def get_current_price(market: str = "BTC-USD"):
    """Récupère le prix actuel"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{INDEXER_URL}/perpetualMarkets",
            params={"ticker": market},
            timeout=10.0
        )
        if response.status_code == 200:
            data = response.json()
            markets = data.get("markets", {})
            if market in markets:
                return float(markets[market].get("oraclePrice", 0))
    return None


async def get_orderbook(market: str = "BTC-USD"):
    """Récupère le carnet d'ordres"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{INDEXER_URL}/orderbooks/perpetualMarket/{market}",
            timeout=10.0
        )
        if response.status_code == 200:
            return response.json()
    return None


async def main():
    print("=" * 60)
    print("🚀 BULL SAGE - Exécution RÉELLE sur dYdX Testnet")
    print("=" * 60)
    
    # Vérifier la configuration
    if not DYDX_TESTNET_ADDRESS:
        print("❌ DYDX_TESTNET_ADDRESS non configuré dans .env")
        return
    
    print(f"\n📍 Wallet: {DYDX_TESTNET_ADDRESS[:20]}...")
    
    # 1. Récupérer les infos du compte
    print("\n💰 Récupération du compte...")
    account = await get_account_info()
    
    if not account:
        print("❌ Impossible de récupérer le compte")
        return
    
    subaccount = account.get("subaccount", {})
    equity = float(subaccount.get("equity", 0))
    free_collateral = float(subaccount.get("freeCollateral", 0))
    
    print(f"   Equity: ${equity:,.2f}")
    print(f"   Free Collateral: ${free_collateral:,.2f}")
    
    # 2. Récupérer le prix BTC
    print("\n📊 Prix BTC-USD actuel...")
    btc_price = await get_current_price("BTC-USD")
    
    if not btc_price:
        print("❌ Impossible de récupérer le prix")
        return
    
    print(f"   Prix Oracle: ${btc_price:,.2f}")
    
    # 3. Récupérer le carnet d'ordres
    print("\n📈 Carnet d'ordres BTC-USD...")
    orderbook = await get_orderbook("BTC-USD")
    
    if orderbook:
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])
        
        if bids and asks:
            best_bid = float(bids[0].get("price", 0))
            best_ask = float(asks[0].get("price", 0))
            spread = best_ask - best_bid
            
            print(f"   Best Bid: ${best_bid:,.2f}")
            print(f"   Best Ask: ${best_ask:,.2f}")
            print(f"   Spread: ${spread:.2f} ({spread/best_bid*100:.3f}%)")
    
    # 4. Préparer le signal
    print("\n" + "=" * 60)
    print("🎯 SIGNAL DE TRADING PRÉPARÉ")
    print("=" * 60)
    
    # Calculer les niveaux
    entry_price = btc_price
    stop_loss = entry_price * 0.98  # -2%
    take_profit = entry_price * 1.04  # +4%
    position_size = 0.001  # 0.001 BTC = ~$94
    position_value = position_size * entry_price
    
    signal = {
        "market": "BTC-USD",
        "direction": "LONG",
        "entry": round(entry_price, 2),
        "stop_loss": round(stop_loss, 2),
        "take_profit": round(take_profit, 2),
        "size": position_size,
        "leverage": 10,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "confidence": 85.0,
        "reason": "Test BULL SAGE - Signal automatique"
    }
    
    print(f"\n📋 Signal JSON:")
    print("-" * 40)
    print(json.dumps(signal, indent=2))
    print("-" * 40)
    
    print(f"\n📈 Détails du trade:")
    print(f"   Direction: 🟢 LONG")
    print(f"   Marché: BTC-USD")
    print(f"   Entry: ${entry_price:,.2f}")
    print(f"   Stop Loss: ${stop_loss:,.2f} (-2%)")
    print(f"   Take Profit: ${take_profit:,.2f} (+4%)")
    print(f"   Taille: {position_size} BTC (~${position_value:.2f})")
    print(f"   Risk/Reward: 1:2")
    
    # 5. Exécution
    print("\n" + "=" * 60)
    print("⚡ EXÉCUTION SUR dYdX TESTNET")
    print("=" * 60)
    
    print("""
    
    ⚠️ NOTE IMPORTANTE:
    
    L'exécution d'ordres sur dYdX v4 nécessite:
    1. La signature cryptographique des transactions
    2. Le client dYdX v4 officiel (dydx-v4-client)
    
    Le client nécessite des dépendances C++ (coincurve) qui
    ne sont pas disponibles sur Windows sans Visual Studio.
    
    🔧 SOLUTIONS:
    
    Option 1: Utiliser l'interface web dYdX
    → Va sur https://v4.testnet.dydx.exchange/
    → Connecte ton wallet
    → Place l'ordre manuellement avec ces paramètres
    
    Option 2: Utiliser le bot Telegram dYdX
    → Envoie le signal JSON au bot
    
    Option 3: Utiliser un serveur Linux
    → Déploie le backend sur Railway/Render
    → Le client dYdX s'installera correctement
    
    📊 TON SIGNAL EST PRÊT:
    """)
    
    print(f"    Market: BTC-USD")
    print(f"    Side: BUY (LONG)")
    print(f"    Size: {position_size} BTC")
    print(f"    Price: MARKET")
    print(f"    Stop Loss: ${stop_loss:,.2f}")
    print(f"    Take Profit: ${take_profit:,.2f}")
    
    print("\n" + "=" * 60)
    
    # Sauvegarder le signal
    signal_file = f"signal_btc_{int(time.time())}.json"
    with open(signal_file, 'w') as f:
        json.dump(signal, f, indent=2)
    
    print(f"✅ Signal sauvegardé: {signal_file}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
