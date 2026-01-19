from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid
import httpx

from ..core.config import db, COINGECKO_API_URL, logger
from ..core.auth import get_current_user
from ..models.schemas import TradingSignal, SignalCreate

router = APIRouter(prefix="/signals", tags=["Signals"])

@router.post("", response_model=TradingSignal)
async def create_signal(signal: SignalCreate, current_user: dict = Depends(get_current_user)):
    """Create a new trading signal with multi-platform support (paper, dydx, gmx)"""
    signal_id = str(uuid.uuid4())
    
    # Déterminer la plateforme
    platform = getattr(signal, 'platform', 'paper') or 'paper'
    
    signal_doc = {
        "id": signal_id,
        "user_id": current_user["id"],
        "symbol": signal.symbol,
        "symbol_name": signal.symbol_name,
        "signal_type": signal.signal_type,
        "entry_price": signal.entry_price,
        "stop_loss": signal.stop_loss,
        "take_profit_1": signal.take_profit_1,
        "take_profit_2": signal.take_profit_2,
        "timeframe": signal.timeframe,
        "confidence": signal.confidence,
        "reason": signal.reason,
        "price_at_signal": signal.price_at_signal,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "active",
        "result_pnl": None,
        # Multi-platform support
        "platform": platform,
        "leverage": getattr(signal, 'leverage', None),
        "collateral_token": getattr(signal, 'collateral_token', None),
    }
    
    # Si auto_execute et plateforme spécifiée, exécuter sur la plateforme
    auto_execute = getattr(signal, 'auto_execute', False)
    execution_result = None
    
    if auto_execute and platform == "gmx":
        try:
            # Créer automatiquement une position GMX
            gmx_position = {
                "id": f"gmx_auto_{signal_id[:8]}",
                "user_id": current_user["id"],
                "platform": "gmx_v2",
                "mode": "paper",
                "source": "signals_auto_execute",
                "market": f"{signal.symbol}-USD",
                "direction": signal.signal_type.upper(),
                "is_long": signal.signal_type.upper() == "LONG",
                "size_usd": signal.entry_price * 10,  # Size basée sur le prix
                "collateral_token": signal.collateral_token or "USDC",
                "leverage": signal.leverage or 10.0,
                "entry_price": signal.price_at_signal,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit_1,
                "collateral_usd": (signal.entry_price * 10) / (signal.leverage or 10.0),
                "status": "open",
                "keeper_status": "executed",
                "linked_signal_id": signal_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await db.gmx_paper_trades.insert_one(gmx_position)
            execution_result = {"success": True, "position_id": gmx_position["id"], "platform": "gmx"}
            signal_doc["execution_result"] = execution_result
            logger.info(f"✅ Signal auto-exécuté sur GMX: {gmx_position['id']}")
        except Exception as e:
            logger.error(f"❌ Erreur auto-execute GMX: {e}")
            execution_result = {"success": False, "error": str(e)}
            signal_doc["execution_result"] = execution_result
    
    await db.signals.insert_one(signal_doc)
    return TradingSignal(**signal_doc)

@router.get("")
async def get_signals(limit: int = 50, status: str = None, current_user: dict = Depends(get_current_user)):
    """Get user's trading signals"""
    query = {"user_id": current_user["id"]}
    if status:
        query["status"] = status
    
    signals = await db.signals.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return signals


@router.get("/active")
async def get_active_signals(current_user: dict = Depends(get_current_user)):
    """Get currently active trading signals"""
    query = {
        "user_id": current_user["id"],
        "status": {"$in": ["active", "pending", "open"]}
    }
    
    signals = await db.signals.find(query, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
    return {"signals": signals, "count": len(signals)}


@router.get("/history")
async def get_signal_history(
    limit: int = 100,
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Get historical trading signals"""
    from datetime import timedelta
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = {
        "user_id": current_user["id"],
        "created_at": {"$gte": cutoff.isoformat()}
    }
    
    signals = await db.signals.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Calculer des stats
    wins = sum(1 for s in signals if s.get("status") in ["hit_tp1", "hit_tp2", "profit"])
    losses = sum(1 for s in signals if s.get("status") in ["hit_sl", "loss"])
    
    return {
        "signals": signals,
        "count": len(signals),
        "wins": wins,
        "losses": losses,
        "win_rate": (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    }


@router.get("/stats")
async def get_signal_stats(current_user: dict = Depends(get_current_user)):
    """Get trading signal statistics"""
    signals = await db.signals.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    
    total = len(signals)
    if total == 0:
        return {
            "total_signals": 0,
            "active": 0,
            "hit_tp1": 0,
            "hit_tp2": 0,
            "hit_sl": 0,
            "expired": 0,
            "win_rate": 0,
            "by_symbol": {},
            "by_timeframe": {}
        }
    
    active = len([s for s in signals if s["status"] == "active"])
    hit_tp1 = len([s for s in signals if s["status"] == "hit_tp1"])
    hit_tp2 = len([s for s in signals if s["status"] == "hit_tp2"])
    hit_sl = len([s for s in signals if s["status"] == "hit_sl"])
    expired = len([s for s in signals if s["status"] == "expired"])
    
    completed = hit_tp1 + hit_tp2 + hit_sl
    wins = hit_tp1 + hit_tp2
    win_rate = (wins / completed * 100) if completed > 0 else 0
    
    by_symbol = {}
    for s in signals:
        sym = s["symbol"]
        if sym not in by_symbol:
            by_symbol[sym] = {"total": 0, "wins": 0}
        by_symbol[sym]["total"] += 1
        if s["status"] in ["hit_tp1", "hit_tp2"]:
            by_symbol[sym]["wins"] += 1
    
    by_timeframe = {}
    for s in signals:
        tf = s["timeframe"]
        if tf not in by_timeframe:
            by_timeframe[tf] = {"total": 0, "wins": 0}
        by_timeframe[tf]["total"] += 1
        if s["status"] in ["hit_tp1", "hit_tp2"]:
            by_timeframe[tf]["wins"] += 1
    
    return {
        "total_signals": total,
        "active": active,
        "hit_tp1": hit_tp1,
        "hit_tp2": hit_tp2,
        "hit_sl": hit_sl,
        "expired": expired,
        "win_rate": round(win_rate, 1),
        "by_symbol": by_symbol,
        "by_timeframe": by_timeframe
    }

@router.put("/{signal_id}/status")
async def update_signal_status(signal_id: str, status: str, result_pnl: float = None, current_user: dict = Depends(get_current_user)):
    """Update signal status"""
    valid_statuses = ["active", "hit_tp1", "hit_tp2", "hit_sl", "expired"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    update_data = {"status": status}
    if result_pnl is not None:
        update_data["result_pnl"] = result_pnl
    
    result = await db.signals.update_one(
        {"id": signal_id, "user_id": current_user["id"]},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    return {"message": "Signal updated", "status": status}

@router.delete("/{signal_id}")
async def delete_signal(signal_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a signal"""
    result = await db.signals.delete_one({"id": signal_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Signal not found")
    return {"message": "Signal deleted"}

@router.post("/evaluate")
async def evaluate_signals(current_user: dict = Depends(get_current_user)):
    """Automatically evaluate active signals against current market prices"""
    active_signals = await db.signals.find(
        {"user_id": current_user["id"], "status": "active"},
        {"_id": 0}
    ).to_list(100)
    
    if not active_signals:
        return {"message": "No active signals to evaluate", "updated": 0, "results": []}
    
    symbols = list(set([s["symbol"] for s in active_signals]))
    symbols_str = ",".join(symbols)
    
    current_prices = {}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{COINGECKO_API_URL}/simple/price",
                params={"ids": symbols_str, "vs_currencies": "usd"},
                timeout=15.0
            )
            if response.status_code == 200:
                price_data = response.json()
                for symbol, data in price_data.items():
                    current_prices[symbol] = data.get("usd", 0)
        except Exception as e:
            logger.error(f"Error fetching prices for evaluation: {e}")
            raise HTTPException(status_code=500, detail="Could not fetch current prices")
    
    results = []
    updated_count = 0
    
    for signal in active_signals:
        symbol = signal["symbol"]
        current_price = current_prices.get(symbol)
        
        if not current_price:
            results.append({"signal_id": signal["id"], "symbol": symbol, "status": "error", "message": "Could not fetch current price"})
            continue
        
        entry_price = signal["entry_price"]
        stop_loss = signal["stop_loss"]
        tp1 = signal["take_profit_1"]
        tp2 = signal.get("take_profit_2")
        signal_type = signal["signal_type"]
        
        new_status = None
        pnl_percent = 0
        
        if signal_type == "BUY":
            if current_price <= stop_loss:
                new_status = "hit_sl"
                pnl_percent = ((stop_loss - entry_price) / entry_price) * 100
            elif tp2 and current_price >= tp2:
                new_status = "hit_tp2"
                pnl_percent = ((tp2 - entry_price) / entry_price) * 100
            elif current_price >= tp1:
                new_status = "hit_tp1"
                pnl_percent = ((tp1 - entry_price) / entry_price) * 100
        elif signal_type == "SELL":
            if current_price >= stop_loss:
                new_status = "hit_sl"
                pnl_percent = ((entry_price - stop_loss) / entry_price) * 100
            elif tp2 and current_price <= tp2:
                new_status = "hit_tp2"
                pnl_percent = ((entry_price - tp2) / entry_price) * 100
            elif current_price <= tp1:
                new_status = "hit_tp1"
                pnl_percent = ((entry_price - tp1) / entry_price) * 100
        
        created_at = datetime.fromisoformat(signal["created_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age_hours = (now - created_at).total_seconds() / 3600
        
        if signal["timeframe"] == "daily" and age_hours > 168:
            if not new_status:
                new_status = "expired"
                pnl_percent = ((current_price - entry_price) / entry_price) * 100 if signal_type == "BUY" else ((entry_price - current_price) / entry_price) * 100
        elif signal["timeframe"] in ["1h", "4h"] and age_hours > 24:
            if not new_status:
                new_status = "expired"
                pnl_percent = ((current_price - entry_price) / entry_price) * 100 if signal_type == "BUY" else ((entry_price - current_price) / entry_price) * 100
        
        if new_status:
            await db.signals.update_one(
                {"id": signal["id"]},
                {"$set": {
                    "status": new_status,
                    "result_pnl": round(pnl_percent, 2),
                    "evaluated_at": datetime.now(timezone.utc).isoformat(),
                    "price_at_evaluation": current_price
                }}
            )
            updated_count += 1
            results.append({
                "signal_id": signal["id"],
                "symbol": signal["symbol_name"],
                "signal_type": signal_type,
                "old_status": "active",
                "new_status": new_status,
                "entry_price": entry_price,
                "current_price": current_price,
                "pnl_percent": round(pnl_percent, 2)
            })
        else:
            unrealized_pnl = ((current_price - entry_price) / entry_price) * 100 if signal_type == "BUY" else ((entry_price - current_price) / entry_price) * 100
            results.append({
                "signal_id": signal["id"],
                "symbol": signal["symbol_name"],
                "signal_type": signal_type,
                "status": "active",
                "entry_price": entry_price,
                "current_price": current_price,
                "unrealized_pnl": round(unrealized_pnl, 2)
            })
    
    return {
        "message": f"Evaluated {len(active_signals)} signals, updated {updated_count}",
        "total_evaluated": len(active_signals),
        "updated": updated_count,
        "results": results
    }
