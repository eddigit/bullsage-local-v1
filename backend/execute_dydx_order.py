"""
Exécution réelle d'ordres sur dYdX v4 Testnet
Utilise l'API REST + signature Cosmos SDK
"""

import asyncio
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Optional

import httpx
from dotenv import load_dotenv

# Crypto libs
from mnemonic import Mnemonic
from ecdsa import SigningKey, SECP256k1
import bech32

load_dotenv()


class DydxV4Executor:
    """
    Exécuteur d'ordres dYdX v4 via API REST
    """
    
    TESTNET_INDEXER = "https://indexer.v4testnet.dydx.exchange/v4"
    TESTNET_VALIDATOR = "https://test-dydx-rpc.kingnodes.com"
    
    # Paramètres des marchés (quantums)
    MARKET_PARAMS = {
        "BTC-USD": {
            "clob_pair_id": 0,
            "atomic_resolution": -10,
            "step_base_quantums": 1000000,
            "subticks_per_tick": 100000,
            "quantum_conversion_exponent": -9,
            "min_order_size": 0.0001
        },
        "ETH-USD": {
            "clob_pair_id": 1,
            "atomic_resolution": -9,
            "step_base_quantums": 1000000,
            "subticks_per_tick": 100000,
            "quantum_conversion_exponent": -9,
            "min_order_size": 0.001
        }
    }
    
    def __init__(self):
        self.mnemonic = os.getenv("DYDX_TESTNET_MNEMONIC", "")
        self.address = os.getenv("DYDX_TESTNET_ADDRESS", "")
        self.private_key = None
        self.public_key = None
        
        if self.mnemonic:
            self._derive_keys()
    
    def _derive_keys(self):
        """Dérive les clés depuis le mnemonic (BIP44 path pour dYdX)"""
        try:
            # dYdX utilise le path m/44'/118'/0'/0/0 (Cosmos standard)
            mnemo = Mnemonic("english")
            seed = mnemo.to_seed(self.mnemonic)
            
            # Dérivation simplifiée pour demo
            # En production, utiliser une lib BIP32/BIP44 complète
            key_material = hashlib.sha256(seed).digest()
            self.private_key = SigningKey.from_string(key_material, curve=SECP256k1)
            self.public_key = self.private_key.get_verifying_key()
            
            print("✅ Clés dérivées avec succès")
        except Exception as e:
            print(f"❌ Erreur dérivation clés: {e}")
    
    async def get_account_info(self) -> Dict:
        """Récupère les infos du compte"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.TESTNET_INDEXER}/addresses/{self.address}/subaccountNumber/0"
            )
            if response.status_code == 200:
                return response.json()
            return {"error": response.text}
    
    async def get_market_price(self, market: str) -> Optional[float]:
        """Récupère le prix actuel"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.TESTNET_INDEXER}/perpetualMarkets",
                params={"ticker": market}
            )
            if response.status_code == 200:
                data = response.json()
                markets = data.get("markets", {})
                if market in markets:
                    return float(markets[market].get("oraclePrice", 0))
        return None
    
    async def place_short_term_order(
        self,
        market: str,
        side: str,  # "BUY" ou "SELL"
        size: float,
        price: float = None,  # None = market order
    ) -> Dict:
        """
        Place un ordre court-terme sur dYdX v4
        
        Note: dYdX v4 utilise des "Short-Term Orders" qui sont placés
        directement sur le CLOB sans passer par la blockchain
        """
        
        result = {
            "success": False,
            "market": market,
            "side": side,
            "size": size,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Récupérer le prix actuel si market order
        if price is None:
            price = await self.get_market_price(market)
            if not price:
                result["error"] = "Impossible de récupérer le prix"
                return result
            
            # Ajuster le prix pour market order (slippage 0.5%)
            if side == "BUY":
                price = price * 1.005
            else:
                price = price * 0.995
        
        result["price"] = price
        
        # Paramètres du marché
        params = self.MARKET_PARAMS.get(market)
        if not params:
            result["error"] = f"Marché {market} non supporté"
            return result
        
        # Construire les paramètres de l'ordre
        order_params = {
            "subaccount": {
                "owner": self.address,
                "number": 0
            },
            "market": market,
            "side": side,
            "size": str(size),
            "price": str(round(price, 2)),
            "type": "LIMIT",  # IOC pour simuler market
            "timeInForce": "IOC",  # Immediate or Cancel
            "postOnly": False,
            "reduceOnly": False,
            "clientId": int(time.time() * 1000) % (2**32),
            "goodTilBlock": 0,  # Court-terme
        }
        
        print(f"\n📤 Envoi de l'ordre:")
        print(f"   Marché: {market}")
        print(f"   Côté: {side}")
        print(f"   Taille: {size}")
        print(f"   Prix: ${price:,.2f}")
        
        # Note: Pour vraiment placer l'ordre, il faut:
        # 1. Signer avec la clé privée
        # 2. Envoyer via gRPC au validateur
        # 
        # dYdX v4 n'a pas d'API REST pour placer des ordres directement
        # Il faut utiliser leur SDK TypeScript ou le client Python officiel
        
        # Pour l'instant, on simule et on retourne les paramètres
        result["success"] = True
        result["mode"] = "SIMULATION"
        result["order_params"] = order_params
        result["message"] = f"Ordre {side} {size} {market} @ ${price:,.2f} préparé"
        result["note"] = "Pour exécution réelle: utiliser dYdX TypeScript SDK ou interface web"
        
        return result
    
    async def execute_signal(
        self,
        market: str,
        direction: str,  # "LONG" ou "SHORT"
        size: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float
    ) -> Dict:
        """
        Exécute un signal complet avec Entry + SL + TP
        """
        
        print("\n" + "=" * 60)
        print(f"🎯 EXÉCUTION SIGNAL {direction} {market}")
        print("=" * 60)
        
        results = {
            "signal": {
                "market": market,
                "direction": direction,
                "entry": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "size": size
            },
            "orders": [],
            "success": False
        }
        
        # 1. Ordre d'entrée
        entry_side = "BUY" if direction == "LONG" else "SELL"
        entry_result = await self.place_short_term_order(
            market=market,
            side=entry_side,
            size=size,
            price=entry_price
        )
        results["orders"].append({"type": "ENTRY", **entry_result})
        
        # 2. Stop Loss
        sl_side = "SELL" if direction == "LONG" else "BUY"
        sl_result = await self.place_short_term_order(
            market=market,
            side=sl_side,
            size=size,
            price=stop_loss
        )
        results["orders"].append({"type": "STOP_LOSS", **sl_result})
        
        # 3. Take Profit
        tp_result = await self.place_short_term_order(
            market=market,
            side=sl_side,
            size=size,
            price=take_profit
        )
        results["orders"].append({"type": "TAKE_PROFIT", **tp_result})
        
        results["success"] = all(o.get("success") for o in results["orders"])
        
        return results


async def main():
    """Test d'exécution réelle"""
    
    print("=" * 60)
    print("🐂 BULL SAGE - Exécution dYdX v4 Testnet")
    print("=" * 60)
    
    executor = DydxV4Executor()
    
    # Vérifier le compte
    print("\n💰 Vérification du compte...")
    account = await executor.get_account_info()
    
    if "error" not in account:
        subaccount = account.get("subaccount", {})
        equity = float(subaccount.get("equity", 0))
        print(f"   Equity: ${equity:,.2f}")
    else:
        print(f"   Erreur: {account.get('error')}")
        return
    
    # Prix actuel BTC
    print("\n📊 Prix actuel BTC-USD...")
    btc_price = await executor.get_market_price("BTC-USD")
    print(f"   Prix: ${btc_price:,.2f}")
    
    # Calculer les niveaux
    entry = btc_price
    stop_loss = entry * 0.98  # -2%
    take_profit = entry * 1.04  # +4%
    size = 0.001  # Petite taille pour test
    
    print(f"\n📋 Signal préparé:")
    print(f"   Direction: LONG")
    print(f"   Entry: ${entry:,.2f}")
    print(f"   Stop Loss: ${stop_loss:,.2f} (-2%)")
    print(f"   Take Profit: ${take_profit:,.2f} (+4%)")
    print(f"   Taille: {size} BTC (~${size * entry:,.2f})")
    
    # Exécuter le signal
    result = await executor.execute_signal(
        market="BTC-USD",
        direction="LONG",
        size=size,
        entry_price=entry,
        stop_loss=stop_loss,
        take_profit=take_profit
    )
    
    print("\n" + "=" * 60)
    print("📊 RÉSULTAT:")
    print("=" * 60)
    
    for order in result["orders"]:
        status = "✅" if order.get("success") else "❌"
        print(f"   {status} {order['type']}: {order.get('message', 'N/A')}")
    
    # JSON du signal
    print("\n📋 JSON du signal:")
    print("-" * 40)
    print(json.dumps(result["signal"], indent=2))
    print("-" * 40)
    
    print("\n⚠️  NOTE IMPORTANTE:")
    print("   dYdX v4 nécessite leur SDK TypeScript pour placer de vrais ordres.")
    print("   Les ordres sont préparés mais pas encore envoyés à la blockchain.")
    print("\n💡 Pour exécuter vraiment:")
    print("   1. Aller sur https://v4.testnet.dydx.exchange/")
    print("   2. Connecter ton wallet")
    print("   3. Placer les ordres manuellement")
    print("   OU utiliser le SDK TypeScript de dYdX")


if __name__ == "__main__":
    asyncio.run(main())
