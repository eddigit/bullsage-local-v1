"""
📈 Routes API Deribit pour Bull Sage
=====================================

Endpoints pour le trading sur Deribit (Testnet/Production):
- /api/deribit/status - État de la connexion
- /api/deribit/account - Résumé du compte
- /api/deribit/positions - Positions ouvertes
- /api/deribit/orders - Ordres en cours et historique
- /api/deribit/buy - Placer un ordre d'achat
- /api/deribit/sell - Placer un ordre de vente
- /api/deribit/close - Fermer une position
- /api/deribit/cancel - Annuler un ordre
"""

import os
import sys
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import asdict

# Ajouter le dossier parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

# Import du client Deribit
from services.deribit_client import (
    get_deribit_client,
    DeribitClient,
    DeribitAPIError,
    DeribitPosition,
    DeribitOrder
)
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/deribit", tags=["Deribit Trading"])


# ==================== MODELS ====================

class OrderRequest(BaseModel):
    """Requête pour placer un ordre"""
    instrument: str = Field(
        default="BTC-PERPETUAL",
        description="Instrument à trader (ex: BTC-PERPETUAL, ETH-PERPETUAL)"
    )
    amount: float = Field(
        ..., 
        gt=0,
        description="Montant en USD pour les perpetuals"
    )
    order_type: Literal["market", "limit"] = Field(
        default="market",
        description="Type d'ordre"
    )
    price: Optional[float] = Field(
        default=None,
        description="Prix limite (requis pour ordre limit)"
    )
    reduce_only: bool = Field(
        default=False,
        description="Si True, ne peut que réduire une position existante"
    )
    label: Optional[str] = Field(
        default=None,
        description="Label pour identifier l'ordre (ex: source de la recommandation)"
    )


class ClosePositionRequest(BaseModel):
    """Requête pour fermer une position"""
    instrument: str = Field(
        default="BTC-PERPETUAL",
        description="Instrument de la position à fermer"
    )
    order_type: Literal["market", "limit"] = Field(
        default="market",
        description="Type d'ordre pour la fermeture"
    )
    price: Optional[float] = Field(
        default=None,
        description="Prix limite (requis pour ordre limit)"
    )


class CancelOrderRequest(BaseModel):
    """Requête pour annuler un ordre"""
    order_id: str = Field(
        ...,
        description="ID de l'ordre à annuler"
    )


# ==================== HELPER FUNCTIONS ====================

def position_to_dict(pos: DeribitPosition) -> Dict[str, Any]:
    """Convertir une position en dictionnaire"""
    return {
        "instrument_name": pos.instrument_name,
        "direction": pos.direction,
        "size": pos.size,
        "average_price": pos.average_price,
        "mark_price": pos.mark_price,
        "unrealized_pnl": pos.unrealized_pnl,
        "realized_pnl": pos.realized_pnl,
        "leverage": pos.leverage,
        "maintenance_margin": pos.maintenance_margin,
        "pnl_percentage": round((pos.unrealized_pnl / (pos.size * pos.average_price)) * 100, 2) if pos.size and pos.average_price else 0
    }


def order_to_dict(order: DeribitOrder) -> Dict[str, Any]:
    """Convertir un ordre en dictionnaire"""
    return {
        "order_id": order.order_id,
        "instrument_name": order.instrument_name,
        "direction": order.direction,
        "order_type": order.order_type,
        "amount": order.amount,
        "price": order.price,
        "filled_amount": order.filled_amount,
        "order_state": order.order_state,
        "created_at": datetime.fromtimestamp(
            order.creation_timestamp / 1000, 
            tz=timezone.utc
        ).isoformat() if order.creation_timestamp else None
    }


# ==================== ROUTES ====================

@router.get("/status")
async def get_deribit_status():
    """
    Vérifier le statut de la connexion Deribit.

    Retourne l'état de la connexion, si authentifié, et les infos de base du compte.
    """
    client = get_deribit_client()

    try:
        result = await client.test_connection()
        logger.info(f"[deribit_status] Connected: {result.get('connected')}, Auth: {result.get('authenticated')}")

        return {
            "success": True,
            "deribit": {
                "connected": result.get("connected", False),
                "authenticated": result.get("authenticated", False),
                "testnet": result.get("testnet", True),
                "api_url": result.get("api_url", ""),
                "server_time": result.get("server_time"),
                "account": result.get("account_info"),
                "error": result.get("auth_error") or result.get("error")
            }
        }
    except Exception as e:
        logger.error(f"[deribit_status] Connection failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "deribit": {
                "connected": False,
                "authenticated": False,
                "testnet": client.config.testnet
            }
        }


@router.get("/account")
async def get_account_summary(currency: str = "BTC"):
    """
    Récupérer le résumé du compte Deribit.
    
    Retourne: balance, equity, margin disponible, etc.
    """
    client = get_deribit_client()
    
    try:
        account = await client.get_account_summary(currency)
        
        return {
            "success": True,
            "currency": currency,
            "account": {
                "equity": account.get("equity", 0),
                "balance": account.get("balance", 0),
                "available_funds": account.get("available_funds", 0),
                "available_withdrawal_funds": account.get("available_withdrawal_funds", 0),
                "initial_margin": account.get("initial_margin", 0),
                "maintenance_margin": account.get("maintenance_margin", 0),
                "margin_balance": account.get("margin_balance", 0),
                "unrealized_pnl": account.get("futures_pl", 0),
                "realized_pnl": account.get("futures_session_rpl", 0),
                "total_pl": account.get("total_pl", 0)
            },
            "testnet": client.config.testnet
        }
    except DeribitAPIError as e:
        raise HTTPException(status_code=e.code if e.code >= 400 else 500, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_positions(currency: str = "BTC"):
    """
    Récupérer toutes les positions ouvertes.
    
    Args:
        currency: BTC ou ETH
    """
    client = get_deribit_client()
    
    try:
        positions = await client.get_positions(currency)
        
        # Calculer les totaux
        total_unrealized = sum(p.unrealized_pnl for p in positions)
        total_realized = sum(p.realized_pnl for p in positions)
        
        return {
            "success": True,
            "currency": currency,
            "positions": [position_to_dict(p) for p in positions],
            "count": len(positions),
            "totals": {
                "unrealized_pnl": round(total_unrealized, 8),
                "realized_pnl": round(total_realized, 8)
            },
            "testnet": client.config.testnet
        }
    except DeribitAPIError as e:
        raise HTTPException(status_code=e.code if e.code >= 400 else 500, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
async def get_orders(
    currency: str = "BTC",
    include_history: bool = False,
    history_count: int = 20
):
    """
    Récupérer les ordres ouverts et optionnellement l'historique.
    """
    client = get_deribit_client()
    
    try:
        open_orders = await client.get_open_orders(currency)
        
        result = {
            "success": True,
            "currency": currency,
            "open_orders": [order_to_dict(o) for o in open_orders],
            "open_count": len(open_orders),
            "testnet": client.config.testnet
        }
        
        if include_history:
            history = await client.get_order_history(currency, history_count)
            result["order_history"] = [order_to_dict(o) for o in history]
            result["history_count"] = len(history)
        
        return result
    except DeribitAPIError as e:
        raise HTTPException(status_code=e.code if e.code >= 400 else 500, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instruments")
async def get_instruments():
    """
    Récupérer les instruments disponibles pour le trading.
    """
    client = get_deribit_client()
    
    try:
        instruments = await client.get_available_instruments()
        
        # Ajouter les perpetuals en premier
        perpetuals = []
        for currency, insts in instruments.items():
            for inst in insts:
                if "PERPETUAL" in inst:
                    perpetuals.append(inst)
        
        return {
            "success": True,
            "perpetuals": perpetuals,
            "all_instruments": instruments,
            "recommended": ["BTC-PERPETUAL", "ETH-PERPETUAL"],
            "testnet": client.config.testnet
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticker/{instrument}")
async def get_ticker(instrument: str):
    """
    Récupérer le ticker d'un instrument.
    
    Args:
        instrument: Ex: BTC-PERPETUAL
    """
    client = get_deribit_client()
    
    try:
        ticker = await client.get_ticker(instrument)
        
        return {
            "success": True,
            "instrument": instrument,
            "ticker": {
                "last_price": ticker.get("last_price"),
                "best_bid": ticker.get("best_bid_price"),
                "best_ask": ticker.get("best_ask_price"),
                "mark_price": ticker.get("mark_price"),
                "index_price": ticker.get("index_price"),
                "open_interest": ticker.get("open_interest"),
                "funding_rate": ticker.get("funding_8h"),
                "volume_24h": ticker.get("stats", {}).get("volume"),
                "price_change_24h": ticker.get("stats", {}).get("price_change")
            },
            "testnet": client.config.testnet
        }
    except DeribitAPIError as e:
        raise HTTPException(status_code=e.code if e.code >= 400 else 500, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buy")
async def place_buy_order(request: OrderRequest):
    """
    Placer un ordre d'achat (LONG).

    Ouvre ou augmente une position longue sur l'instrument spécifié.
    """
    client = get_deribit_client()
    logger.info(f"[deribit_buy] Order request: {request.instrument} ${request.amount} {request.order_type}")

    try:
        order = await client.buy(
            instrument_name=request.instrument,
            amount=request.amount,
            order_type=request.order_type,
            price=request.price,
            reduce_only=request.reduce_only,
            label=request.label or "bullsage_buy"
        )
        logger.info(f"[deribit_buy] Order placed successfully: {order.order_id}")

        return {
            "success": True,
            "action": "buy",
            "order": order_to_dict(order),
            "message": f"Ordre d'achat placé: {request.amount} USD sur {request.instrument}",
            "testnet": client.config.testnet
        }
    except DeribitAPIError as e:
        logger.error(f"[deribit_buy] API error: {e.message}")
        raise HTTPException(status_code=e.code if e.code >= 400 else 500, detail=e.message)
    except ValueError as e:
        logger.error(f"[deribit_buy] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[deribit_buy] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sell")
async def place_sell_order(request: OrderRequest):
    """
    Placer un ordre de vente (SHORT).

    Ouvre ou augmente une position short sur l'instrument spécifié.
    """
    client = get_deribit_client()
    logger.info(f"[deribit_sell] Order request: {request.instrument} ${request.amount} {request.order_type}")

    try:
        order = await client.sell(
            instrument_name=request.instrument,
            amount=request.amount,
            order_type=request.order_type,
            price=request.price,
            reduce_only=request.reduce_only,
            label=request.label or "bullsage_sell"
        )
        logger.info(f"[deribit_sell] Order placed successfully: {order.order_id}")

        return {
            "success": True,
            "action": "sell",
            "order": order_to_dict(order),
            "message": f"Ordre de vente placé: {request.amount} USD sur {request.instrument}",
            "testnet": client.config.testnet
        }
    except DeribitAPIError as e:
        logger.error(f"[deribit_sell] API error: {e.message}")
        raise HTTPException(status_code=e.code if e.code >= 400 else 500, detail=e.message)
    except ValueError as e:
        logger.error(f"[deribit_sell] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[deribit_sell] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/close")
async def close_position(request: ClosePositionRequest):
    """
    Fermer complètement une position.
    """
    client = get_deribit_client()
    
    try:
        result = await client.close_position(
            instrument_name=request.instrument,
            order_type=request.order_type,
            price=request.price
        )
        
        return {
            "success": True,
            "action": "close",
            "instrument": request.instrument,
            "result": result,
            "message": f"Position fermée sur {request.instrument}",
            "testnet": client.config.testnet
        }
    except DeribitAPIError as e:
        raise HTTPException(status_code=e.code if e.code >= 400 else 500, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel")
async def cancel_order(request: CancelOrderRequest):
    """
    Annuler un ordre en cours.
    """
    client = get_deribit_client()
    
    try:
        result = await client.cancel_order(request.order_id)
        
        return {
            "success": True,
            "action": "cancel",
            "order_id": request.order_id,
            "result": result,
            "message": f"Ordre {request.order_id} annulé",
            "testnet": client.config.testnet
        }
    except DeribitAPIError as e:
        raise HTTPException(status_code=e.code if e.code >= 400 else 500, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel-all")
async def cancel_all_orders(currency: str = "BTC"):
    """
    Annuler tous les ordres ouverts pour une devise.
    """
    client = get_deribit_client()
    
    try:
        count = await client.cancel_all_orders(currency)
        
        return {
            "success": True,
            "action": "cancel_all",
            "currency": currency,
            "cancelled_count": count,
            "message": f"{count} ordre(s) annulé(s) pour {currency}",
            "testnet": client.config.testnet
        }
    except DeribitAPIError as e:
        raise HTTPException(status_code=e.code if e.code >= 400 else 500, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== QUICK TRADE ENDPOINTS ====================

@router.post("/quick-buy")
async def quick_buy(
    instrument: str = "BTC-PERPETUAL",
    amount_usd: float = 100,
    source: str = "manual"
):
    """
    Achat rapide au marché.
    
    Endpoint simplifié pour les boutons CTA.
    """
    return await place_buy_order(OrderRequest(
        instrument=instrument,
        amount=amount_usd,
        order_type="market",
        label=f"bullsage_{source}"
    ))


@router.post("/quick-sell")
async def quick_sell(
    instrument: str = "BTC-PERPETUAL",
    amount_usd: float = 100,
    source: str = "manual"
):
    """
    Vente rapide au marché.
    
    Endpoint simplifié pour les boutons CTA.
    """
    return await place_sell_order(OrderRequest(
        instrument=instrument,
        amount=amount_usd,
        order_type="market",
        label=f"bullsage_{source}"
    ))


# ==================== SIGNAL EXECUTION ====================

@router.post("/execute-signal")
async def execute_signal(
    signal_type: Literal["BUY", "SELL", "LONG", "SHORT"],
    instrument: str = "BTC-PERPETUAL",
    amount_usd: float = 100,
    source: str = "ai_recommendation",
    confidence: Optional[float] = None
):
    """
    Exécuter un signal de trading provenant des prévisions IA.
    
    Ce endpoint est conçu pour être appelé automatiquement
    quand l'utilisateur clique sur un bouton CTA après une recommandation.
    
    Args:
        signal_type: BUY/LONG ou SELL/SHORT
        instrument: Instrument à trader
        amount_usd: Montant en USD
        source: Source du signal (ex: "council_consensus", "pro_trader")
        confidence: Score de confiance de l'IA (0-100)
    """
    client = get_deribit_client()
    
    # Normaliser le type de signal
    is_buy = signal_type.upper() in ["BUY", "LONG"]
    
    try:
        if is_buy:
            order = await client.buy(
                instrument_name=instrument,
                amount=amount_usd,
                order_type="market",
                label=f"bullsage_{source}"
            )
        else:
            order = await client.sell(
                instrument_name=instrument,
                amount=amount_usd,
                order_type="market",
                label=f"bullsage_{source}"
            )
        
        return {
            "success": True,
            "signal_executed": True,
            "signal": {
                "type": signal_type,
                "instrument": instrument,
                "amount_usd": amount_usd,
                "source": source,
                "confidence": confidence
            },
            "order": order_to_dict(order),
            "message": f"Signal {signal_type} exécuté: {amount_usd} USD sur {instrument}",
            "testnet": client.config.testnet,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except DeribitAPIError as e:
        raise HTTPException(status_code=e.code if e.code >= 400 else 500, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
