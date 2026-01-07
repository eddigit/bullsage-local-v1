"""
Routes API dYdX pour BULL SAGE
Connexion et exécution automatique sur dYdX v4
"""

from fastapi import APIRouter, Depends, HTTPException, Request
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


class DydxQuickSignalRequest(BaseModel):
    """Format simplifié depuis le frontend Pro Trader AI"""
    market: str  # ex: "BTC-USD", "ETH-USD"
    direction: str  # "LONG" ou "SHORT"
    size: float = 0.01
    # Nouveau: configuration du montant
    sizeMode: Optional[str] = None  # 'percentage' ou 'fixed'
    percentageOfPortfolio: Optional[float] = None  # % du portefeuille (ex: 5)
    fixedAmountUSDC: Optional[float] = None  # Montant fixe en USDC (ex: 100)
    stop_loss_pct: float = 2.0  # % de SL
    take_profit_pct: float = 4.0  # % de TP
    metadata: Optional[dict] = None  # Documentation du trade (urgency, confidence, trade_config, etc.)


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


@router.post("/signal/quick")
async def quick_create_dydx_signal(
    request: DydxQuickSignalRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Route simplifiée pour le frontend Pro Trader AI
    
    Format attendu:
    - market: "BTC-USD", "ETH-USD", "SOL-USD"
    - direction: "LONG" ou "SHORT"
    - size: 0.001 pour BTC, 0.01 pour ETH, 0.1 pour SOL
    - stop_loss_pct: pourcentage de SL (ex: 2.0 = 2%)
    - take_profit_pct: pourcentage de TP (ex: 4.0 = 4%)
    - metadata: { urgency, confidence, wait_pullback, ... }
    """
    import httpx
    from core.config import settings
    
    # Extraire le symbol
    symbol = request.market.replace("-USD", "").replace("-PERP", "")
    
    # Récupérer le prix actuel
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            price_response = await client.get(
                f"https://indexer.v4testnet.dydx.exchange/v4/perpetualMarkets"
            )
            markets_data = price_response.json()
            market_key = f"{symbol}-USD"
            
            if market_key in markets_data.get("markets", {}):
                current_price = float(markets_data["markets"][market_key].get("oraclePrice", 0))
            else:
                # Fallback estimation
                current_price = 100000 if symbol == "BTC" else 3500 if symbol == "ETH" else 150
    except Exception as e:
        logger.warning(f"Erreur prix dYdX: {e}")
        current_price = 100000 if symbol == "BTC" else 3500 if symbol == "ETH" else 150
    
    # Calculer SL et TP
    if request.direction == "LONG":
        stop_loss = current_price * (1 - request.stop_loss_pct / 100)
        take_profit = current_price * (1 + request.take_profit_pct / 100)
    else:
        stop_loss = current_price * (1 + request.stop_loss_pct / 100)
        take_profit = current_price * (1 - request.take_profit_pct / 100)
    
    # Créer le signal
    signal = dydx_testnet_trader.create_signal_from_analysis(
        symbol=symbol,
        signal_type=request.direction,
        entry_price=current_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        size=request.size,
        confidence=request.metadata.get("confidence", 0) if request.metadata else 0,
        reason=f"Pro Trader AI - {request.metadata.get('urgency', 'IMMEDIATE')}" if request.metadata else "Pro Trader AI"
    )
    
    # Documenter l'urgence et le pullback
    metadata = request.metadata or {}
    urgency = metadata.get("urgency", "IMMEDIATE")
    wait_pullback = metadata.get("wait_pullback", False)
    
    # Sauvegarder avec toutes les métadonnées
    signal_doc = {
        "id": f"quick_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "user_id": current_user["id"],
        **signal.to_json(),
        "status": "pending",
        "source": "pro_trader_ai",
        "metadata": {
            "urgency": urgency,
            "wait_pullback": wait_pullback,
            "recommended_entry": metadata.get("recommended_entry"),
            "confidence": metadata.get("confidence"),
            "rr_ratio": metadata.get("rr_ratio"),
            "signals": metadata.get("signals"),
            "executed_at": metadata.get("executed_at")
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.dydx_signals.insert_one(signal_doc)
    
    # Exécuter via le Node.js executor
    execution_result = None
    try:
        executor_url = getattr(settings, 'DYDX_EXECUTOR_URL', 'http://localhost:3001')
        api_secret = getattr(settings, 'DYDX_API_SECRET', '')
        
        logger.info(f"🎯 Exécution dYdX: {signal.market} {signal.direction} via {executor_url}")
        
        headers = {"X-API-Key": api_secret} if api_secret else {}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Construire le payload avec les nouvelles options de taille
            execute_payload = {
                "market": signal.market,
                "direction": signal.direction,
                "size": request.size,
                "stopLoss": stop_loss,
                "takeProfit": take_profit,
                "stop_loss_pct": request.stop_loss_pct,
                "take_profit_pct": request.take_profit_pct,
                # Nouveau: configuration du montant
                "sizeMode": request.sizeMode,
                "percentageOfPortfolio": request.percentageOfPortfolio,
                "fixedAmountUSDC": request.fixedAmountUSDC,
                # Métadonnées pour documentation
                "metadata": {
                    "urgency": urgency,
                    "wait_pullback": wait_pullback,
                    "recommended_entry": metadata.get("recommended_entry"),
                    "confidence": metadata.get("confidence"),
                    "quality": metadata.get("quality"),
                    "rr_ratio": metadata.get("rr_ratio"),
                    "signals": metadata.get("signals"),
                    "trade_type": metadata.get("trade_type"),
                    "timeframe": metadata.get("timeframe"),
                    "estimated_duration": metadata.get("estimated_duration"),
                    "trade_config": metadata.get("trade_config"),
                    "executed_at": metadata.get("executed_at")
                }
            }
            
            response = await client.post(
                f"{executor_url}/execute",
                json=execute_payload,
                headers=headers
            )
            execution_result = response.json()
            
            # Mettre à jour le statut
            success = execution_result.get("success", False)
            await db.dydx_signals.update_one(
                {"id": signal_doc["id"]},
                {"$set": {
                    "status": "executed" if success else "failed",
                    "execution_result": execution_result,
                    "executed_at": datetime.now(timezone.utc).isoformat()
                }}
            )
    except Exception as e:
        logger.error(f"Erreur exécution dYdX: {e}")
        execution_result = {"success": False, "error": str(e)}
    
    # Log l'urgence
    if wait_pullback:
        logger.warning(f"⚠️ Trade {signal.market} exécuté malgré WAIT_PULLBACK recommandé")
    
    return {
        "success": execution_result.get("success", False) if execution_result else False,
        "signal": signal.to_json(),
        "signal_id": signal_doc["id"],
        "execution": execution_result,
        "mode": execution_result.get("mode", "unknown") if execution_result else "error",
        "metadata": signal_doc["metadata"]
    }


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

# ============ POSITIONS & MONITORING (Proxy vers Node.js) ============

class ClosePositionRequest(BaseModel):
    """Requête pour fermer une position"""
    market: str
    reason: Optional[str] = "manual"


@router.get("/positions/detailed")
async def get_dydx_positions_detailed(current_user: dict = Depends(get_current_user)):
    """
    Récupère les positions détaillées avec PnL et ordres de protection
    Proxy vers le serveur Node.js dYdX Executor
    """
    import httpx
    from core.config import settings
    
    try:
        executor_url = getattr(settings, 'DYDX_EXECUTOR_URL', 'http://localhost:3001')
        api_secret = getattr(settings, 'DYDX_API_SECRET', '')
        
        headers = {"X-API-Key": api_secret} if api_secret else {}
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{executor_url}/positions/detailed",
                headers=headers
            )
            
            if response.status_code == 503:
                return {
                    "error": "dYdX Executor non connecté",
                    "positions": [],
                    "equity": 0,
                    "freeCollateral": 0
                }
            
            return response.json()
    except Exception as e:
        logger.error(f"Erreur positions détaillées: {e}")
        raise HTTPException(status_code=503, detail=f"Erreur connexion dYdX: {str(e)}")


@router.post("/positions/close")
async def close_dydx_position(
    request: ClosePositionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Ferme une position sur dYdX
    """
    import httpx
    from core.config import settings
    
    try:
        executor_url = getattr(settings, 'DYDX_EXECUTOR_URL', 'http://localhost:3001')
        api_secret = getattr(settings, 'DYDX_API_SECRET', '')
        
        headers = {"X-API-Key": api_secret} if api_secret else {}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{executor_url}/positions/close",
                json={"market": request.market, "reason": request.reason},
                headers=headers
            )
            
            result = response.json()
            
            # Logger l'action
            await db.dydx_actions.insert_one({
                "user_id": current_user["id"],
                "action": "close_position",
                "market": request.market,
                "reason": request.reason,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return result
    except Exception as e:
        logger.error(f"Erreur fermeture position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ProtectPositionRequest(BaseModel):
    """Requête pour protéger une position avec SL/TP"""
    market: str
    stopLoss: Optional[float] = None
    takeProfit: Optional[float] = None
    expirationHours: Optional[int] = 168  # 7 jours par défaut


@router.post("/positions/protect")
async def protect_dydx_position(
    request: ProtectPositionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Ajoute des protections Stop Loss et/ou Take Profit à une position existante
    """
    import httpx
    from core.config import settings
    
    if not request.stopLoss and not request.takeProfit:
        raise HTTPException(status_code=400, detail="Au moins un Stop Loss ou Take Profit requis")
    
    try:
        executor_url = getattr(settings, 'DYDX_EXECUTOR_URL', 'http://localhost:3001')
        api_secret = getattr(settings, 'DYDX_API_SECRET', '')
        
        headers = {"X-API-Key": api_secret} if api_secret else {}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{executor_url}/positions/protect",
                json={
                    "market": request.market, 
                    "stopLoss": request.stopLoss,
                    "takeProfit": request.takeProfit,
                    "expirationHours": request.expirationHours
                },
                headers=headers
            )
            
            result = response.json()
            
            # Logger l'action
            await db.dydx_actions.insert_one({
                "user_id": current_user["id"],
                "action": "protect_position",
                "market": request.market,
                "stopLoss": request.stopLoss,
                "takeProfit": request.takeProfit,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return result
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json() if e.response.content else str(e)
        raise HTTPException(status_code=e.response.status_code, detail=error_detail)
    except Exception as e:
        logger.error(f"Erreur protection position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor")
async def monitor_dydx_positions(current_user: dict = Depends(get_current_user)):
    """
    Lance un check de monitoring des positions
    Vérifie les protections et ferme automatiquement si nécessaire
    """
    import httpx
    from core.config import settings
    
    try:
        executor_url = getattr(settings, 'DYDX_EXECUTOR_URL', 'http://localhost:3001')
        api_secret = getattr(settings, 'DYDX_API_SECRET', '')
        
        headers = {"X-API-Key": api_secret} if api_secret else {}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{executor_url}/monitor",
                headers=headers
            )
            
            result = response.json()
            
            # Logger le monitoring
            await db.dydx_monitoring.insert_one({
                "user_id": current_user["id"],
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return result
    except Exception as e:
        logger.error(f"Erreur monitoring: {e}")
        raise HTTPException(status_code=503, detail=str(e))


# Endpoint public pour cron job externe (sans auth utilisateur, mais avec clé cron)
@router.get("/cron/monitor")
async def cron_monitor_positions(request: Request):
    """
    Endpoint pour cron job externe (cron-job.org, UptimeRobot, etc.)
    Vérifie et protège les positions automatiquement
    
    Appeler toutes les 5 minutes via:
    - cron-job.org avec header X-Cron-Key
    - UptimeRobot
    - Render Cron Job
    """
    import httpx
    from core.config import settings
    
    # Vérifier la clé cron (optionnel mais recommandé)
    cron_key = getattr(settings, 'CRON_API_KEY', '')
    request_key = request.headers.get('X-Cron-Key', '')
    
    # En production, vérifier la clé si configurée
    if cron_key and request_key != cron_key:
        logger.warning(f"⚠️ Tentative cron non autorisée depuis {request.client.host}")
        # On continue quand même pour ne pas bloquer le monitoring
        # mais on log l'avertissement
    
    try:
        executor_url = getattr(settings, 'DYDX_EXECUTOR_URL', 'http://localhost:3001')
        api_secret = getattr(settings, 'DYDX_API_SECRET', '')
        
        headers = {"X-API-Key": api_secret} if api_secret else {}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{executor_url}/monitor",
                headers=headers
            )
            
            result = response.json()
            
            # Logger
            await db.dydx_cron_logs.insert_one({
                "type": "monitor",
                "source": "cron-job.org" if request_key else "unknown",
                "ip": request.client.host if request.client else "unknown",
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            summary = result.get("summary", {})
            
            return {
                "status": "ok",
                "positions": summary.get("totalPositions", 0),
                "protected": summary.get("protectedPositions", 0),
                "unprotected": summary.get("unprotectedPositions", 0),
                "alerts": len(result.get("alerts", [])),
                "actions": len(result.get("actions", [])),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    except Exception as e:
        logger.error(f"Erreur cron monitoring: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }