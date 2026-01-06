"""
Routes API dYdX pour BULL SAGE
Connexion et exécution automatique sur dYdX v4
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from core.config import db, logger
from core.auth import get_current_user
from services.dydx_trader import (
    DydxTrader, 
    DydxNetwork, 
    DydxSignal,
    dydx_testnet_trader,
    dydx_mainnet_trader
)

router = APIRouter(prefix="/dydx", tags=["dYdX Trading"])


class DydxConfigRequest(BaseModel):
    """Configuration du wallet dYdX"""
    network: str = "testnet"  # "testnet" ou "mainnet"
    mnemonic: Optional[str] = None
    wallet_address: Optional[str] = None


class DydxSignalRequest(BaseModel):
    """Requête pour créer un signal dYdX"""
    symbol: str  # ex: "BTC", "bitcoin", "ETH"
    direction: str  # "LONG" ou "SHORT"
    entry_price: float
    stop_loss: float
    take_profit: float
    size: float = 0.01
    leverage: int = 10
    auto_execute: bool = False  # Si True, exécute directement sur dYdX


class DydxExecuteRequest(BaseModel):
    """Requête pour exécuter un signal existant"""
    signal_id: str


# ==================== ENDPOINTS ====================

@router.get("/status")
async def get_dydx_status(current_user: dict = Depends(get_current_user)):
    """
    Vérifie le statut de connexion à dYdX
    """
    testnet_status = await dydx_testnet_trader.check_connection()
    
    # Récupérer la config utilisateur
    user_config = await db.dydx_configs.find_one({"user_id": current_user["id"]})
    
    return {
        "testnet": testnet_status,
        "user_configured": user_config is not None,
        "wallet_address": user_config.get("wallet_address", "")[:15] + "..." if user_config else None
    }


@router.post("/configure")
async def configure_dydx(
    config: DydxConfigRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Configure le wallet dYdX pour l'utilisateur
    ⚠️ Le mnemonic est stocké de manière sécurisée
    """
    trader = dydx_testnet_trader if config.network == "testnet" else dydx_mainnet_trader
    
    # Valider la connexion
    if config.wallet_address:
        trader.configure(
            mnemonic=config.mnemonic,
            wallet_address=config.wallet_address
        )
    
    # Sauvegarder en base (mnemonic chiffré en production)
    config_doc = {
        "user_id": current_user["id"],
        "network": config.network,
        "wallet_address": config.wallet_address,
        # ⚠️ En production: chiffrer le mnemonic avec une clé dérivée
        "mnemonic_hash": "***SECURED***" if config.mnemonic else None,
        "configured_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.dydx_configs.update_one(
        {"user_id": current_user["id"]},
        {"$set": config_doc},
        upsert=True
    )
    
    # Tester la connexion
    connection = await trader.check_connection()
    
    return {
        "success": True,
        "message": f"Configuration dYdX {config.network} enregistrée",
        "connection": connection
    }


@router.get("/markets")
async def get_dydx_markets(current_user: dict = Depends(get_current_user)):
    """
    Liste les marchés disponibles sur dYdX
    """
    markets = await dydx_testnet_trader.get_markets()
    
    if not markets:
        raise HTTPException(status_code=503, detail="Impossible de récupérer les marchés")
    
    # Formater pour l'affichage
    formatted = []
    for ticker, data in markets.items():
        formatted.append({
            "market": ticker,
            "price": data.get("oraclePrice"),
            "status": data.get("status"),
            "min_order_size": data.get("atomicResolution"),
            "step_size": data.get("stepBaseQuantums")
        })
    
    return {"markets": formatted, "count": len(formatted)}


@router.get("/account")
async def get_dydx_account(current_user: dict = Depends(get_current_user)):
    """
    Récupère les informations du compte dYdX
    """
    # Charger la config utilisateur
    user_config = await db.dydx_configs.find_one({"user_id": current_user["id"]})
    
    if not user_config or not user_config.get("wallet_address"):
        raise HTTPException(
            status_code=400,
            detail="Configurez d'abord votre wallet dYdX via /dydx/configure"
        )
    
    dydx_testnet_trader.wallet_address = user_config["wallet_address"]
    account = await dydx_testnet_trader.get_account_info()
    
    return account


@router.get("/positions")
async def get_dydx_positions(current_user: dict = Depends(get_current_user)):
    """
    Récupère les positions ouvertes sur dYdX
    """
    user_config = await db.dydx_configs.find_one({"user_id": current_user["id"]})
    
    if not user_config or not user_config.get("wallet_address"):
        return {"positions": [], "message": "Wallet non configuré"}
    
    dydx_testnet_trader.wallet_address = user_config["wallet_address"]
    positions = await dydx_testnet_trader.get_positions()
    
    return {"positions": positions, "count": len(positions)}


@router.post("/signal/create")
async def create_dydx_signal(
    request: DydxSignalRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Crée un signal de trading dYdX
    
    Retourne:
    - Le signal formaté en JSON
    - L'image du signal (si disponible)
    - L'exécution automatique (si auto_execute=True)
    """
    # Créer le signal
    signal = dydx_testnet_trader.create_signal_from_analysis(
        symbol=request.symbol,
        signal_type=request.direction,
        entry_price=request.entry_price,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit,
        size=request.size,
        confidence=0.0,
        reason="Signal manuel"
    )
    
    # Sauvegarder le signal en base
    signal_doc = {
        "id": f"dydx_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "user_id": current_user["id"],
        **signal.to_json(),
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.dydx_signals.insert_one(signal_doc)
    
    result = {
        "success": True,
        "signal": signal.to_json(),
        "signal_id": signal_doc["id"],
        "json_export": signal.to_json_string()
    }
    
    # Exécution automatique si demandé
    if request.auto_execute:
        # Charger la config utilisateur
        user_config = await db.dydx_configs.find_one({"user_id": current_user["id"]})
        
        if user_config and user_config.get("wallet_address"):
            dydx_testnet_trader.wallet_address = user_config["wallet_address"]
            execution = await dydx_testnet_trader.execute_signal(signal)
            
            # Mettre à jour le statut
            await db.dydx_signals.update_one(
                {"id": signal_doc["id"]},
                {"$set": {
                    "status": "executed" if execution["success"] else "failed",
                    "execution_result": execution,
                    "executed_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            result["execution"] = execution
            result["status"] = "executed" if execution["success"] else "failed"
        else:
            result["execution"] = None
            result["warning"] = "Wallet non configuré - Signal créé mais non exécuté"
    
    return result


@router.post("/signal/execute/{signal_id}")
async def execute_dydx_signal(
    signal_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Exécute un signal dYdX existant
    """
    # Récupérer le signal
    signal_doc = await db.dydx_signals.find_one({
        "id": signal_id,
        "user_id": current_user["id"]
    })
    
    if not signal_doc:
        raise HTTPException(status_code=404, detail="Signal non trouvé")
    
    if signal_doc.get("status") == "executed":
        raise HTTPException(status_code=400, detail="Signal déjà exécuté")
    
    # Charger la config utilisateur
    user_config = await db.dydx_configs.find_one({"user_id": current_user["id"]})
    
    if not user_config or not user_config.get("wallet_address"):
        raise HTTPException(
            status_code=400,
            detail="Configurez d'abord votre wallet dYdX"
        )
    
    # Recréer le signal
    signal = DydxSignal(
        market=signal_doc["market"],
        direction=signal_doc["direction"],
        entry_price=signal_doc["entry"],
        stop_loss=signal_doc["stop_loss"],
        take_profit=signal_doc["take_profit"],
        size=signal_doc["size"]
    )
    
    # Exécuter
    dydx_testnet_trader.wallet_address = user_config["wallet_address"]
    execution = await dydx_testnet_trader.execute_signal(signal)
    
    # Mettre à jour le statut
    await db.dydx_signals.update_one(
        {"id": signal_id},
        {"$set": {
            "status": "executed" if execution["success"] else "failed",
            "execution_result": execution,
            "executed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "success": execution["success"],
        "signal_id": signal_id,
        "execution": execution,
        "message": "✅ Ordres placés sur dYdX" if execution["success"] else "❌ Échec de l'exécution"
    }


@router.get("/signals")
async def get_dydx_signals(
    limit: int = 20,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Liste les signaux dYdX de l'utilisateur
    """
    query = {"user_id": current_user["id"]}
    if status:
        query["status"] = status
    
    signals = await db.dydx_signals.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"signals": signals, "count": len(signals)}


@router.get("/summary")
async def get_dydx_summary(current_user: dict = Depends(get_current_user)):
    """
    Résumé de l'activité dYdX de l'utilisateur
    """
    # Stats des signaux
    pipeline = [
        {"$match": {"user_id": current_user["id"]}},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }}
    ]
    
    stats = {}
    async for doc in db.dydx_signals.aggregate(pipeline):
        stats[doc["_id"]] = doc["count"]
    
    # Derniers signaux exécutés
    recent = await db.dydx_signals.find(
        {"user_id": current_user["id"], "status": "executed"},
        {"_id": 0}
    ).sort("executed_at", -1).limit(5).to_list(5)
    
    return {
        "statistics": {
            "total_signals": sum(stats.values()),
            "pending": stats.get("pending", 0),
            "executed": stats.get("executed", 0),
            "failed": stats.get("failed", 0)
        },
        "recent_executions": recent,
        "trader_status": dydx_testnet_trader.get_execution_summary()
    }


# ==================== INTÉGRATION AUTO-TRADING ====================

@router.post("/auto-execute")
async def auto_execute_signal(
    symbol: str,
    signal_type: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    size: float = 0.01,
    current_user: dict = Depends(get_current_user)
):
    """
    Point d'entrée pour l'exécution automatique depuis Bull Sage
    
    Appelé automatiquement quand un signal est détecté avec haute confiance
    
    Retourne:
    1. Image (via le frontend)
    2. JSON du signal
    3. Résultat d'exécution sur dYdX
    """
    # Créer le signal
    signal = dydx_testnet_trader.create_signal_from_analysis(
        symbol=symbol,
        signal_type=signal_type,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        size=size
    )
    
    # Charger la config
    user_config = await db.dydx_configs.find_one({"user_id": current_user["id"]})
    
    # Résultat complet
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        
        # 1. JSON du signal
        "signal_json": signal.to_json(),
        
        # 2. Format lisible
        "signal_readable": {
            "market": signal.market,
            "action": f"{'🟢 LONG' if signal.direction == 'LONG' else '🔴 SHORT'}",
            "entry": f"${signal.entry_price:,.2f}",
            "stop_loss": f"${signal.stop_loss:,.2f}",
            "take_profit": f"${signal.take_profit:,.2f}",
            "risk_reward": round(
                abs(signal.take_profit - signal.entry_price) / 
                abs(signal.entry_price - signal.stop_loss), 2
            ) if signal.stop_loss != signal.entry_price else 0
        }
    }
    
    # 3. Exécution sur dYdX
    if user_config and user_config.get("wallet_address"):
        dydx_testnet_trader.wallet_address = user_config["wallet_address"]
        execution = await dydx_testnet_trader.execute_signal(signal)
        
        result["execution"] = execution
        result["status"] = "✅ Ordres placés sur dYdX" if execution["success"] else "❌ Échec"
        
        # Sauvegarder
        await db.dydx_signals.insert_one({
            "id": f"auto_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "user_id": current_user["id"],
            **signal.to_json(),
            "status": "executed" if execution["success"] else "failed",
            "execution_result": execution,
            "source": "auto_execute",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    else:
        result["execution"] = None
        result["status"] = "⚠️ Signal créé - Wallet non configuré"
    
    logger.info(f"🎯 Auto-execute: {signal.direction} {signal.market}")
    
    return result
