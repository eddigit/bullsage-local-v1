"""
Service dYdX Trader pour BULL SAGE
Exécution automatique des signaux sur dYdX v4 (Testnet & Mainnet)
"""

import asyncio
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import logging
import httpx

logger = logging.getLogger(__name__)


class DydxNetwork(Enum):
    TESTNET = "testnet"
    MAINNET = "mainnet"


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_MARKET = "STOP_MARKET"
    TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"


@dataclass
class DydxSignal:
    """Signal de trading formaté pour dYdX"""
    market: str  # ex: "BTC-USD"
    direction: str  # "LONG" ou "SHORT"
    entry_price: float
    stop_loss: float
    take_profit: float
    size: float  # Taille de la position
    leverage: int = 10
    timestamp: str = None
    confidence: float = 0.0
    reason: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_json(self) -> Dict:
        """Convertit le signal en JSON pour export"""
        return {
            "market": self.market,
            "direction": self.direction,
            "entry": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "size": self.size,
            "leverage": self.leverage,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
            "reason": self.reason
        }
    
    def to_json_string(self) -> str:
        """Retourne le JSON formaté"""
        return json.dumps(self.to_json(), indent=2)


class DydxTrader:
    """
    Gestionnaire de trading sur dYdX v4
    Supporte Testnet et Mainnet
    """
    
    # Configuration des endpoints
    ENDPOINTS = {
        DydxNetwork.TESTNET: {
            "rest": "https://indexer.v4testnet.dydx.exchange/v4",
            "ws": "wss://indexer.v4testnet.dydx.exchange/v4/ws",
            "chain": "https://test-dydx.kingnodes.com",
            "chain_id": "dydx-testnet-4"
        },
        DydxNetwork.MAINNET: {
            "rest": "https://indexer.dydx.trade/v4",
            "ws": "wss://indexer.dydx.trade/v4/ws",
            "chain": "https://dydx-mainnet.kingnodes.com",
            "chain_id": "dydx-mainnet-1"
        }
    }
    
    # Mapping des symboles Bull Sage -> dYdX
    MARKET_MAPPING = {
        "bitcoin": "BTC-USD",
        "btc": "BTC-USD",
        "BTC": "BTC-USD",
        "ethereum": "ETH-USD",
        "eth": "ETH-USD",
        "ETH": "ETH-USD",
        "solana": "SOL-USD",
        "sol": "SOL-USD",
        "SOL": "SOL-USD",
        "dogecoin": "DOGE-USD",
        "doge": "DOGE-USD",
        "DOGE": "DOGE-USD",
        "ripple": "XRP-USD",
        "xrp": "XRP-USD",
        "XRP": "XRP-USD",
        "cardano": "ADA-USD",
        "ada": "ADA-USD",
        "ADA": "ADA-USD",
        "polygon": "MATIC-USD",
        "matic": "MATIC-USD",
        "MATIC": "MATIC-USD",
        "avalanche": "AVAX-USD",
        "avax": "AVAX-USD",
        "AVAX": "AVAX-USD",
        "chainlink": "LINK-USD",
        "link": "LINK-USD",
        "LINK": "LINK-USD",
        "polkadot": "DOT-USD",
        "dot": "DOT-USD",
        "DOT": "DOT-USD"
    }
    
    def __init__(self, network: DydxNetwork = DydxNetwork.TESTNET):
        self.network = network
        self.endpoints = self.ENDPOINTS[network]
        self.wallet_address: Optional[str] = None
        self.mnemonic: Optional[str] = None
        self.is_connected = False
        self.executed_signals: List[Dict] = []
        
        # Configuration depuis les variables d'environnement
        self._load_config()
    
    def _load_config(self):
        """Charge la configuration depuis les variables d'environnement"""
        if self.network == DydxNetwork.TESTNET:
            self.mnemonic = os.getenv("DYDX_TESTNET_MNEMONIC", "")
            self.wallet_address = os.getenv("DYDX_TESTNET_ADDRESS", "")
        else:
            self.mnemonic = os.getenv("DYDX_MAINNET_MNEMONIC", "")
            self.wallet_address = os.getenv("DYDX_MAINNET_ADDRESS", "")
    
    def configure(self, mnemonic: str = None, wallet_address: str = None):
        """Configure les credentials du wallet"""
        if mnemonic:
            self.mnemonic = mnemonic
        if wallet_address:
            self.wallet_address = wallet_address
        logger.info(f"✅ dYdX Trader configuré pour {self.network.value}")
    
    def get_market(self, symbol: str) -> str:
        """Convertit un symbole Bull Sage en marché dYdX"""
        return self.MARKET_MAPPING.get(symbol, f"{symbol.upper()}-USD")
    
    async def check_connection(self) -> Dict:
        """Vérifie la connexion à dYdX"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.endpoints['rest']}/height",
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    self.is_connected = True
                    return {
                        "connected": True,
                        "network": self.network.value,
                        "height": data.get("height"),
                        "time": data.get("time")
                    }
        except Exception as e:
            logger.error(f"❌ Erreur connexion dYdX: {e}")
        
        self.is_connected = False
        return {"connected": False, "error": "Impossible de se connecter à dYdX"}
    
    async def get_markets(self) -> List[Dict]:
        """Récupère la liste des marchés disponibles"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.endpoints['rest']}/perpetualMarkets",
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("markets", {})
        except Exception as e:
            logger.error(f"❌ Erreur récupération marchés: {e}")
        return []
    
    async def get_market_price(self, market: str) -> Optional[float]:
        """Récupère le prix actuel d'un marché"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.endpoints['rest']}/perpetualMarkets",
                    params={"ticker": market},
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    markets = data.get("markets", {})
                    if market in markets:
                        return float(markets[market].get("oraclePrice", 0))
        except Exception as e:
            logger.error(f"❌ Erreur prix {market}: {e}")
        return None
    
    async def get_account_info(self) -> Dict:
        """Récupère les informations du compte"""
        if not self.wallet_address:
            return {"error": "Wallet non configuré"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.endpoints['rest']}/addresses/{self.wallet_address}/subaccountNumber/0",
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return {"error": "Compte non trouvé. Faites un dépôt sur le testnet d'abord."}
        except Exception as e:
            logger.error(f"❌ Erreur compte: {e}")
        
        return {"error": "Impossible de récupérer les infos du compte"}
    
    async def get_positions(self) -> List[Dict]:
        """Récupère les positions ouvertes"""
        if not self.wallet_address:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.endpoints['rest']}/addresses/{self.wallet_address}/subaccountNumber/0/positions",
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("positions", [])
        except Exception as e:
            logger.error(f"❌ Erreur positions: {e}")
        return []
    
    def create_signal_from_analysis(
        self,
        symbol: str,
        signal_type: str,  # "LONG" ou "SHORT" ou "BUY"/"SELL"
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        size: float = 0.01,
        confidence: float = 0.0,
        reason: str = ""
    ) -> DydxSignal:
        """
        Crée un signal dYdX à partir d'une analyse Bull Sage
        """
        # Normaliser la direction
        direction = "LONG" if signal_type.upper() in ["LONG", "BUY", "ACHAT"] else "SHORT"
        
        # Mapper le marché
        market = self.get_market(symbol)
        
        return DydxSignal(
            market=market,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            size=size,
            confidence=confidence,
            reason=reason
        )
    
    async def execute_signal(self, signal: DydxSignal) -> Dict:
        """
        Exécute un signal sur dYdX via le serveur Node.js
        Place 3 ordres: Market Entry + Stop Loss + Take Profit
        """
        result = {
            "success": False,
            "signal": signal.to_json(),
            "orders": [],
            "errors": [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Essayer d'abord le serveur Node.js (exécution réelle)
        try:
            # Utiliser la config centralisée
            from core.config import DYDX_EXECUTOR_URL, DYDX_API_SECRET
            dydx_executor_url = DYDX_EXECUTOR_URL or os.getenv("DYDX_EXECUTOR_URL", "http://localhost:3001")
            api_secret = DYDX_API_SECRET or os.getenv("DYDX_API_SECRET", "")
            
            headers = {"Content-Type": "application/json"}
            if api_secret:
                headers["X-API-Key"] = api_secret
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{dydx_executor_url}/execute",
                    headers=headers,
                    json={
                        "market": signal.market,
                        "direction": signal.direction,
                        "entry": signal.entry_price,
                        "stopLoss": signal.stop_loss,
                        "takeProfit": signal.take_profit,
                        "size": signal.size
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result["success"] = data.get("success", False)
                    result["orders"] = data.get("orders", [])
                    result["mode"] = "LIVE_TESTNET"
                    result["message"] = f"✅ Signal {signal.direction} {signal.market} exécuté sur dYdX!"
                    
                    self.executed_signals.append(result)
                    logger.info(f"🎯 dYdX: {signal.direction} {signal.market} - {len(result['orders'])} ordres placés")
                    
                    return result
                else:
                    logger.warning(f"⚠️ Serveur dYdX erreur: {response.status_code}")
                    
        except httpx.ConnectError:
            logger.info("ℹ️ Serveur dYdX non disponible, mode simulation")
        except Exception as e:
            logger.warning(f"⚠️ Erreur appel dYdX executor: {e}")
        
        # Fallback: mode simulation
        result["mode"] = "SIMULATION"
        result["success"] = True
        result["orders"] = [
            {
                "type": "MARKET_ENTRY",
                "side": "BUY" if signal.direction == "LONG" else "SELL",
                "market": signal.market,
                "price": signal.entry_price,
                "size": signal.size,
                "status": "SIMULATED"
            },
            {
                "type": "STOP_LOSS",
                "trigger_price": signal.stop_loss,
                "market": signal.market,
                "size": signal.size,
                "status": "SIMULATED"
            },
            {
                "type": "TAKE_PROFIT",
                "trigger_price": signal.take_profit,
                "market": signal.market,
                "size": signal.size,
                "status": "SIMULATED"
            }
        ]
        result["message"] = f"✅ Signal {signal.direction} {signal.market} prêt (simulation)"
        
        self.executed_signals.append(result)
        
        logger.info(f"📊 Signal créé: {signal.direction} {signal.market} @ {signal.entry_price}")
        logger.info(f"   SL: {signal.stop_loss} | TP: {signal.take_profit}")
        
        return result
    
    def export_signal_json(self, signal: DydxSignal, filepath: str = None) -> str:
        """
        Exporte un signal en fichier JSON
        """
        json_data = signal.to_json()
        json_string = json.dumps(json_data, indent=2)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_string)
            logger.info(f"📁 Signal exporté: {filepath}")
        
        return json_string
    
    def get_execution_summary(self) -> Dict:
        """Retourne un résumé des exécutions"""
        return {
            "network": self.network.value,
            "wallet": self.wallet_address[:10] + "..." if self.wallet_address else None,
            "is_connected": self.is_connected,
            "total_executed": len(self.executed_signals),
            "last_signals": self.executed_signals[-5:] if self.executed_signals else []
        }


# Instance globale
dydx_testnet_trader = DydxTrader(DydxNetwork.TESTNET)
dydx_mainnet_trader = DydxTrader(DydxNetwork.MAINNET)


async def test_dydx_connection():
    """Test de connexion au testnet dYdX"""
    trader = DydxTrader(DydxNetwork.TESTNET)
    
    print("🔌 Test de connexion à dYdX Testnet...")
    connection = await trader.check_connection()
    print(f"   Résultat: {connection}")
    
    if connection.get("connected"):
        print("\n📊 Récupération des marchés...")
        markets = await trader.get_markets()
        print(f"   {len(markets)} marchés disponibles")
        
        print("\n💰 Prix BTC-USD...")
        price = await trader.get_market_price("BTC-USD")
        print(f"   Prix: ${price:,.2f}" if price else "   Erreur")
        
        # Test création signal
        print("\n🎯 Création d'un signal test...")
        signal = trader.create_signal_from_analysis(
            symbol="BTC",
            signal_type="LONG",
            entry_price=93648.13,
            stop_loss=78983.30,
            take_profit=115645.38,
            size=0.01,
            confidence=85.0,
            reason="RSI survente + MACD bullish"
        )
        print(f"   JSON:\n{signal.to_json_string()}")
        
        # Test exécution (simulation)
        print("\n🚀 Exécution du signal (simulation)...")
        result = await trader.execute_signal(signal)
        print(f"   Succès: {result['success']}")
        print(f"   Message: {result.get('message', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(test_dydx_connection())
