"""
Test de l'intégration dYdX pour Bull Sage
"""

import asyncio
import sys
sys.path.append('.')

from services.dydx_trader import (
    DydxTrader, 
    DydxNetwork, 
    DydxSignal,
    test_dydx_connection
)


async def test_full_workflow():
    """Test complet du workflow dYdX"""
    
    print("=" * 60)
    print("🐂 BULL SAGE - Test d'intégration dYdX")
    print("=" * 60)
    
    # 1. Créer le trader testnet
    trader = DydxTrader(DydxNetwork.TESTNET)
    
    # 2. Tester la connexion
    print("\n📡 Test de connexion au Testnet dYdX...")
    connection = await trader.check_connection()
    
    if connection.get("connected"):
        print(f"   ✅ Connecté au réseau dYdX")
        print(f"   Block Height: {connection.get('height')}")
    else:
        print(f"   ❌ Connexion échouée: {connection.get('error')}")
        return
    
    # 3. Récupérer les marchés
    print("\n📊 Récupération des marchés disponibles...")
    markets = await trader.get_markets()
    print(f"   {len(markets)} marchés trouvés")
    
    # Afficher les 5 premiers
    for i, (ticker, data) in enumerate(list(markets.items())[:5]):
        price = data.get('oraclePrice', 'N/A')
        print(f"   • {ticker}: ${float(price):,.2f}" if price != 'N/A' else f"   • {ticker}")
    
    # 4. Créer un signal de test (BTC LONG)
    print("\n🎯 Création d'un signal de test...")
    signal = trader.create_signal_from_analysis(
        symbol="BTC",
        signal_type="LONG",
        entry_price=93648.13,
        stop_loss=78983.30,
        take_profit=115645.38,
        size=0.01,
        confidence=85.0,
        reason="RSI survente (28.5) + MACD bullish crossover"
    )
    
    # 5. Afficher le JSON
    print("\n📋 Signal JSON généré:")
    print("-" * 40)
    print(signal.to_json_string())
    print("-" * 40)
    
    # 6. Calculer le Risk/Reward
    risk = abs(signal.entry_price - signal.stop_loss)
    reward = abs(signal.take_profit - signal.entry_price)
    rr_ratio = reward / risk if risk > 0 else 0
    
    print(f"\n📈 Analyse du signal:")
    print(f"   Direction: {signal.direction}")
    print(f"   Marché: {signal.market}")
    print(f"   Entry: ${signal.entry_price:,.2f}")
    print(f"   Stop Loss: ${signal.stop_loss:,.2f} ({(signal.stop_loss/signal.entry_price-1)*100:.1f}%)")
    print(f"   Take Profit: ${signal.take_profit:,.2f} ({(signal.take_profit/signal.entry_price-1)*100:.1f}%)")
    print(f"   Risk/Reward: 1:{rr_ratio:.2f}")
    
    # 7. Simuler l'exécution
    print("\n🚀 Exécution du signal (mode simulation)...")
    result = await trader.execute_signal(signal)
    
    if result["success"]:
        print(f"   ✅ {result.get('message')}")
        print(f"   Mode: {result.get('mode')}")
        print(f"   Ordres créés:")
        for order in result.get("orders", []):
            print(f"      • {order['type']}: {order.get('side', 'N/A')} @ ${order.get('price', order.get('trigger_price', 'N/A'))}")
    else:
        print(f"   ❌ Erreurs: {result.get('errors')}")
    
    # 8. Résumé
    print("\n📊 Résumé de l'exécution:")
    summary = trader.get_execution_summary()
    print(f"   Réseau: {summary['network']}")
    print(f"   Connecté: {summary['is_connected']}")
    print(f"   Signaux exécutés: {summary['total_executed']}")
    
    print("\n" + "=" * 60)
    print("✅ Test terminé avec succès !")
    print("=" * 60)
    
    print("\n💡 Prochaines étapes:")
    print("   1. Ajouter DYDX_TESTNET_MNEMONIC dans .env")
    print("   2. Ajouter DYDX_TESTNET_ADDRESS dans .env")
    print("   3. Obtenir des fonds test: https://faucet.v4testnet.dydx.exchange")
    print("   4. Lancer le serveur et tester /api/dydx/status")


if __name__ == "__main__":
    asyncio.run(test_full_workflow())
