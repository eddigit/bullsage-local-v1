"""
Vérification de la configuration dYdX
"""
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from services.dydx_trader import DydxTrader, DydxNetwork

async def check_config():
    print("=" * 50)
    print("🔍 Vérification configuration dYdX")
    print("=" * 50)
    
    # Variables d'environnement
    address = os.getenv('DYDX_TESTNET_ADDRESS', '')
    mnemonic = os.getenv('DYDX_TESTNET_MNEMONIC', '')
    
    print(f"\n📍 Adresse: {address[:25]}..." if len(address) > 25 else f"\n📍 Adresse: {address or 'Non configurée'}")
    
    if mnemonic:
        word_count = len(mnemonic.split())
        print(f"🔐 Mnemonic: Configuré ({word_count} mots)")
    else:
        print("🔐 Mnemonic: Non configuré")
    
    # Test connexion
    print("\n📡 Test de connexion...")
    trader = DydxTrader(DydxNetwork.TESTNET)
    trader.configure(mnemonic=mnemonic, wallet_address=address)
    
    connection = await trader.check_connection()
    if connection.get("connected"):
        print("✅ Connecté au réseau dYdX Testnet")
    else:
        print(f"❌ Erreur: {connection.get('error')}")
        return
    
    # Récupérer infos compte
    if address:
        print(f"\n💰 Récupération du compte...")
        account = await trader.get_account_info()
        
        if "error" in account:
            print(f"⚠️ {account['error']}")
            print("\n💡 Pour obtenir des fonds de test:")
            print("   1. Va sur https://v4.testnet.dydx.exchange/")
            print("   2. Connecte ton wallet")
            print("   3. Utilise le faucet pour recevoir des USDC de test")
        else:
            # Afficher les infos du compte
            subaccount = account.get("subaccount", {})
            equity = subaccount.get("equity", "N/A")
            free_collateral = subaccount.get("freeCollateral", "N/A")
            
            print(f"   Equity: ${equity}")
            print(f"   Free Collateral: ${free_collateral}")
            
            # Positions
            positions = await trader.get_positions()
            print(f"   Positions ouvertes: {len(positions)}")
    
    print("\n" + "=" * 50)
    print("✅ Configuration vérifiée !")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(check_config())
