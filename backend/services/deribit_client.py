"""
🔐 Client Deribit API avec authentification OAuth2 HMAC-SHA256
===============================================================

Ce module gère la connexion à l'API Deribit (testnet ou production)
avec authentification sécurisée par signature HMAC-SHA256.

Documentation: https://docs.deribit.com
"""

import os
import time
import hmac
import hashlib
import json
import asyncio
from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass, field
from datetime import datetime, timezone
import httpx
import logging

logger = logging.getLogger(__name__)


@dataclass
class DeribitConfig:
    """Configuration du client Deribit"""
    client_id: str = ""
    client_secret: str = ""
    api_url: str = "https://test.deribit.com/api/v2"
    testnet: bool = True
    
    @classmethod
    def from_env(cls) -> "DeribitConfig":
        """Charger la configuration depuis les variables d'environnement"""
        return cls(
            client_id=os.environ.get("DERIBIT_CLIENT_ID", ""),
            client_secret=os.environ.get("DERIBIT_CLIENT_SECRET", ""),
            api_url=os.environ.get("DERIBIT_API_URL", "https://test.deribit.com/api/v2"),
            testnet=os.environ.get("DERIBIT_TESTNET", "true").lower() == "true"
        )


@dataclass
class DeribitPosition:
    """Représentation d'une position Deribit"""
    instrument_name: str
    direction: str  # "buy" ou "sell"
    size: float
    average_price: float
    mark_price: float
    unrealized_pnl: float
    realized_pnl: float
    leverage: float
    maintenance_margin: float
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "DeribitPosition":
        return cls(
            instrument_name=data.get("instrument_name", ""),
            direction=data.get("direction", ""),
            size=float(data.get("size", 0)),
            average_price=float(data.get("average_price", 0)),
            mark_price=float(data.get("mark_price", 0)),
            unrealized_pnl=float(data.get("floating_profit_loss", 0)),
            realized_pnl=float(data.get("realized_profit_loss", 0)),
            leverage=float(data.get("leverage", 1)),
            maintenance_margin=float(data.get("maintenance_margin", 0))
        )


@dataclass
class DeribitOrder:
    """Représentation d'un ordre Deribit"""
    order_id: str
    instrument_name: str
    direction: str
    order_type: str
    amount: float
    price: Optional[float]
    filled_amount: float
    order_state: str
    creation_timestamp: int
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "DeribitOrder":
        return cls(
            order_id=data.get("order_id", ""),
            instrument_name=data.get("instrument_name", ""),
            direction=data.get("direction", ""),
            order_type=data.get("order_type", ""),
            amount=float(data.get("amount", 0)),
            price=float(data.get("price", 0)) if data.get("price") else None,
            filled_amount=float(data.get("filled_amount", 0)),
            order_state=data.get("order_state", ""),
            creation_timestamp=data.get("creation_timestamp", 0)
        )


class DeribitClient:
    """
    Client pour l'API Deribit avec authentification OAuth2.
    
    Supporte:
    - Authentification par client_credentials
    - Trading (buy/sell)
    - Gestion des positions
    - Informations de compte
    """
    
    def __init__(self, config: Optional[DeribitConfig] = None):
        self.config = config or DeribitConfig.from_env()
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: int = 0
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def is_configured(self) -> bool:
        """Vérifier si le client est configuré"""
        return bool(self.config.client_id and self.config.client_secret)
    
    @property
    def base_url(self) -> str:
        """URL de base de l'API"""
        return self.config.api_url
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Obtenir ou créer le client HTTP"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def close(self):
        """Fermer le client HTTP"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _generate_signature(self, timestamp: int, nonce: str, data: str) -> str:
        """
        Générer la signature HMAC-SHA256 pour l'authentification.
        
        La signature est calculée sur: timestamp + "\n" + nonce + "\n" + data
        """
        message = f"{timestamp}\n{nonce}\n{data}"
        signature = hmac.new(
            self.config.client_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def _request(
        self, 
        method: str, 
        params: Optional[Dict[str, Any]] = None,
        require_auth: bool = True
    ) -> Dict[str, Any]:
        """
        Effectuer une requête à l'API Deribit.
        
        Args:
            method: Méthode API (ex: "public/get_instruments")
            params: Paramètres de la requête
            require_auth: Si True, ajoute le token d'authentification
        
        Returns:
            Résultat de la requête
        """
        if require_auth:
            await self._ensure_authenticated()
        
        client = await self._get_client()
        
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": params or {}
        }
        
        headers = {"Content-Type": "application/json"}
        
        if require_auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        try:
            response = await client.post(
                self.base_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                error = result["error"]
                logger.error(f"Deribit API Error: {error}")
                raise DeribitAPIError(
                    code=error.get("code", -1),
                    message=error.get("message", "Unknown error")
                )
            
            return result.get("result", {})
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise DeribitAPIError(code=e.response.status_code, message=str(e))
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise
    
    async def _ensure_authenticated(self):
        """S'assurer que le client est authentifié"""
        if not self.is_configured:
            raise DeribitAPIError(
                code=401,
                message="Deribit client not configured. Set DERIBIT_CLIENT_ID and DERIBIT_CLIENT_SECRET."
            )
        
        # Vérifier si le token est encore valide (avec 60s de marge)
        if self.access_token and time.time() < (self.token_expiry - 60):
            return
        
        # Tenter de rafraîchir le token
        if self.refresh_token:
            try:
                await self._refresh_access_token()
                return
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
        
        # Authentification initiale
        await self._authenticate()
    
    async def _authenticate(self):
        """
        Authentification via client_credentials (méthode simple).
        
        Documentation: https://docs.deribit.com/#public-auth
        
        Pour client_credentials, on envoie simplement client_id et client_secret.
        Pas besoin de signature HMAC.
        """
        params = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret
        }
        
        result = await self._request("public/auth", params, require_auth=False)
        
        self.access_token = result.get("access_token")
        self.refresh_token = result.get("refresh_token")
        self.token_expiry = time.time() + result.get("expires_in", 900)
        
        logger.info("✅ Deribit authentication successful")
    
    async def _refresh_access_token(self):
        """Rafraîchir le token d'accès"""
        params = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        
        result = await self._request("public/auth", params, require_auth=False)
        
        self.access_token = result.get("access_token")
        self.refresh_token = result.get("refresh_token")
        self.token_expiry = time.time() + result.get("expires_in", 900)
        
        logger.info("✅ Deribit token refreshed")
    
    # ==================== PUBLIC METHODS ====================
    
    async def get_instruments(
        self, 
        currency: str = "BTC", 
        kind: str = "future"
    ) -> List[Dict[str, Any]]:
        """
        Récupérer la liste des instruments disponibles.
        
        Args:
            currency: BTC, ETH, etc.
            kind: future, option, spot
        """
        result = await self._request(
            "public/get_instruments",
            {"currency": currency, "kind": kind},
            require_auth=False
        )
        return result
    
    async def get_ticker(self, instrument_name: str) -> Dict[str, Any]:
        """
        Récupérer le ticker d'un instrument.
        
        Args:
            instrument_name: Ex: "BTC-PERPETUAL", "ETH-PERPETUAL"
        """
        result = await self._request(
            "public/ticker",
            {"instrument_name": instrument_name},
            require_auth=False
        )
        return result
    
    async def get_index_price(self, index_name: str = "btc_usd") -> Dict[str, Any]:
        """Récupérer le prix de l'index"""
        result = await self._request(
            "public/get_index_price",
            {"index_name": index_name},
            require_auth=False
        )
        return result
    
    # ==================== ACCOUNT METHODS ====================
    
    async def get_account_summary(self, currency: str = "BTC") -> Dict[str, Any]:
        """
        Récupérer le résumé du compte.
        
        Retourne: balance, equity, margin, available funds, etc.
        """
        result = await self._request(
            "private/get_account_summary",
            {"currency": currency, "extended": True}
        )
        return result
    
    async def get_positions(self, currency: str = "BTC") -> List[DeribitPosition]:
        """
        Récupérer toutes les positions ouvertes.
        
        Args:
            currency: BTC, ETH, etc.
        """
        result = await self._request(
            "private/get_positions",
            {"currency": currency}
        )
        
        positions = []
        for pos_data in result:
            if pos_data.get("size", 0) != 0:  # Ne garder que les positions actives
                positions.append(DeribitPosition.from_api(pos_data))
        
        return positions
    
    async def get_open_orders(
        self, 
        currency: str = "BTC",
        kind: str = "future"
    ) -> List[DeribitOrder]:
        """Récupérer les ordres ouverts"""
        result = await self._request(
            "private/get_open_orders_by_currency",
            {"currency": currency, "kind": kind}
        )
        
        return [DeribitOrder.from_api(order) for order in result]
    
    async def get_order_history(
        self, 
        currency: str = "BTC",
        count: int = 20
    ) -> List[DeribitOrder]:
        """Récupérer l'historique des ordres"""
        result = await self._request(
            "private/get_order_history_by_currency",
            {"currency": currency, "count": count}
        )
        
        return [DeribitOrder.from_api(order) for order in result]
    
    # ==================== TRADING METHODS ====================
    
    async def buy(
        self,
        instrument_name: str,
        amount: float,
        order_type: Literal["market", "limit"] = "market",
        price: Optional[float] = None,
        reduce_only: bool = False,
        post_only: bool = False,
        label: Optional[str] = None
    ) -> DeribitOrder:
        """
        Placer un ordre d'achat (LONG).
        
        Args:
            instrument_name: Ex: "BTC-PERPETUAL"
            amount: Montant en USD pour les perpetuals
            order_type: "market" ou "limit"
            price: Prix limite (requis si order_type="limit")
            reduce_only: Si True, ne peut que réduire une position
            post_only: Si True, l'ordre sera annulé s'il serait exécuté immédiatement
            label: Label optionnel pour identifier l'ordre
        
        Returns:
            DeribitOrder avec les détails de l'ordre
        """
        params = {
            "instrument_name": instrument_name,
            "amount": amount,
            "type": order_type,
            "reduce_only": reduce_only,
            "post_only": post_only
        }
        
        if order_type == "limit":
            if price is None:
                raise ValueError("Price is required for limit orders")
            params["price"] = price
        
        if label:
            params["label"] = label
        
        result = await self._request("private/buy", params)
        
        order_data = result.get("order", {})
        logger.info(f"✅ BUY order placed: {order_data.get('order_id')} - {instrument_name} x{amount}")
        
        return DeribitOrder.from_api(order_data)
    
    async def sell(
        self,
        instrument_name: str,
        amount: float,
        order_type: Literal["market", "limit"] = "market",
        price: Optional[float] = None,
        reduce_only: bool = False,
        post_only: bool = False,
        label: Optional[str] = None
    ) -> DeribitOrder:
        """
        Placer un ordre de vente (SHORT).
        
        Args:
            instrument_name: Ex: "BTC-PERPETUAL"
            amount: Montant en USD pour les perpetuals
            order_type: "market" ou "limit"
            price: Prix limite (requis si order_type="limit")
            reduce_only: Si True, ne peut que réduire une position
            post_only: Si True, l'ordre sera annulé s'il serait exécuté immédiatement
            label: Label optionnel pour identifier l'ordre
        
        Returns:
            DeribitOrder avec les détails de l'ordre
        """
        params = {
            "instrument_name": instrument_name,
            "amount": amount,
            "type": order_type,
            "reduce_only": reduce_only,
            "post_only": post_only
        }
        
        if order_type == "limit":
            if price is None:
                raise ValueError("Price is required for limit orders")
            params["price"] = price
        
        if label:
            params["label"] = label
        
        result = await self._request("private/sell", params)
        
        order_data = result.get("order", {})
        logger.info(f"✅ SELL order placed: {order_data.get('order_id')} - {instrument_name} x{amount}")
        
        return DeribitOrder.from_api(order_data)
    
    async def close_position(
        self,
        instrument_name: str,
        order_type: Literal["market", "limit"] = "market",
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Fermer complètement une position.
        
        Args:
            instrument_name: Ex: "BTC-PERPETUAL"
            order_type: "market" ou "limit"
            price: Prix limite (requis si order_type="limit")
        """
        params = {
            "instrument_name": instrument_name,
            "type": order_type
        }
        
        if order_type == "limit" and price:
            params["price"] = price
        
        result = await self._request("private/close_position", params)
        
        logger.info(f"✅ Position closed: {instrument_name}")
        return result
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Annuler un ordre"""
        result = await self._request(
            "private/cancel",
            {"order_id": order_id}
        )
        logger.info(f"✅ Order cancelled: {order_id}")
        return result
    
    async def cancel_all_orders(self, currency: str = "BTC") -> int:
        """Annuler tous les ordres ouverts"""
        result = await self._request(
            "private/cancel_all_by_currency",
            {"currency": currency}
        )
        count = result if isinstance(result, int) else 0
        logger.info(f"✅ Cancelled {count} orders for {currency}")
        return count
    
    # ==================== UTILITY METHODS ====================
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Tester la connexion à Deribit.
        
        Returns:
            Dictionnaire avec le statut de la connexion
        """
        try:
            # Test public endpoint
            time_result = await self._request(
                "public/get_time",
                require_auth=False
            )
            
            result = {
                "connected": True,
                "testnet": self.config.testnet,
                "api_url": self.config.api_url,
                "server_time": time_result,
                "authenticated": False,
                "account_info": None
            }
            
            # Test authentification si configuré
            if self.is_configured:
                try:
                    await self._ensure_authenticated()
                    account = await self.get_account_summary("BTC")
                    result["authenticated"] = True
                    result["account_info"] = {
                        "equity": account.get("equity", 0),
                        "balance": account.get("balance", 0),
                        "available_funds": account.get("available_funds", 0),
                        "currency": "BTC"
                    }
                except Exception as e:
                    result["auth_error"] = str(e)
            
            return result
            
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "testnet": self.config.testnet
            }
    
    async def get_available_instruments(self) -> Dict[str, List[str]]:
        """
        Récupérer tous les instruments disponibles par devise.
        
        Returns:
            Dict avec les instruments par currency
        """
        result = {}
        
        for currency in ["BTC", "ETH"]:
            try:
                instruments = await self.get_instruments(currency, "future")
                result[currency] = [
                    inst["instrument_name"] 
                    for inst in instruments 
                    if inst.get("is_active", True)
                ]
            except Exception as e:
                logger.warning(f"Error fetching {currency} instruments: {e}")
                result[currency] = []
        
        return result


class DeribitAPIError(Exception):
    """Exception pour les erreurs API Deribit"""
    
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Deribit API Error {code}: {message}")


# Instance globale (singleton)
_deribit_client: Optional[DeribitClient] = None


def get_deribit_client() -> DeribitClient:
    """Obtenir l'instance du client Deribit"""
    global _deribit_client
    if _deribit_client is None:
        _deribit_client = DeribitClient()
    return _deribit_client


async def cleanup_deribit_client():
    """Nettoyer le client Deribit"""
    global _deribit_client
    if _deribit_client:
        await _deribit_client.close()
        _deribit_client = None
