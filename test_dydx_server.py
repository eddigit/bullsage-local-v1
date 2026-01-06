#!/usr/bin/env python3
"""
Test du serveur dYdX Executor depuis Python
"""
import httpx
import asyncio
import json

DYDX_EXECUTOR_URL = "http://localhost:3001"


async def test_status():
    """Test du statut du serveur"""
    print("\n📊 Test du statut...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{DYDX_EXECUTOR_URL}/status")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return response.json()


async def test_prices():
    """Test des prix"""
    print("\n💰 Test des prix...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{DYDX_EXECUTOR_URL}/prices")
        data = response.json()
        if data.get("success"):
            for market, info in data["prices"].items():
                print(f"   {market}: ${info.get('price', 'N/A')}")
        return data


async def test_positions():
    """Test des positions"""
    print("\n📈 Test des positions...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{DYDX_EXECUTOR_URL}/positions")
        data = response.json()
        if data.get("success"):
            if data["positions"]:
                for pos in data["positions"]:
                    side = pos.get("side", "?")
                    market = pos.get("market", "?")
                    size = pos.get("size", "0")
                    pnl = pos.get("unrealizedPnl", "0")
                    print(f"   {side} {market}: size={size}, PnL=${pnl}")
            else:
                print("   Aucune position ouverte")
        return data


async def test_execute_signal():
    """Test d'exécution d'un signal"""
    print("\n🎯 Test d'exécution d'un signal BTC LONG...")
    
    signal = {
        "market": "BTC-USD",
        "direction": "LONG",
        "entry": 105000,
        "stopLoss": 103000,
        "takeProfit": 108000,
        "size": 0.001
    }
    
    print(f"   Signal: {json.dumps(signal)}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{DYDX_EXECUTOR_URL}/execute",
            json=signal
        )
        data = response.json()
        
        if data.get("success"):
            print(f"   ✅ Succès!")
            for order in data.get("orders", []):
                status = "✓" if order.get("success") else "✗"
                print(f"      {status} {order.get('type')}: {order.get('message', '')}")
        else:
            print(f"   ❌ Erreur: {data.get('error', 'Unknown')}")
        
        return data


async def main():
    print("=" * 60)
    print("🐂 BULL SAGE - Test du serveur dYdX Executor")
    print("=" * 60)
    
    try:
        await test_status()
        await test_prices()
        await test_positions()
        await test_execute_signal()
        await test_positions()  # Vérifier après exécution
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests terminés!")
        print("=" * 60)
        
    except httpx.ConnectError:
        print("\n❌ ERREUR: Le serveur dYdX n'est pas accessible!")
        print("   Assurez-vous que le serveur est lancé avec:")
        print("   cd dydx-executor && node server.js")
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")


if __name__ == "__main__":
    asyncio.run(main())
