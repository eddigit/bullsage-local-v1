from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone
from collections import Counter
import uuid

from ..core.config import db
from ..core.auth import get_current_user
from ..models.schemas import TradeJournalCreate, TradeJournalClose

router = APIRouter(prefix="/journal", tags=["Trading Journal"])

@router.post("/trades")
async def create_journal_entry(entry: TradeJournalCreate, current_user: dict = Depends(get_current_user)):
    """Create a new trade journal entry"""
    if entry.trade_type == "BUY":
        risk = entry.entry_price - entry.stop_loss
        reward = entry.take_profit - entry.entry_price
    else:
        risk = entry.stop_loss - entry.entry_price
        reward = entry.entry_price - entry.take_profit
    
    rr_ratio = round(reward / risk, 2) if risk > 0 else 0
    
    journal_entry = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "symbol": entry.symbol,
        "symbol_name": entry.symbol_name,
        "trade_type": entry.trade_type,
        "entry_price": entry.entry_price,
        "exit_price": None,
        "quantity": entry.quantity,
        "entry_date": datetime.now(timezone.utc).isoformat(),
        "exit_date": None,
        "timeframe": entry.timeframe,
        "stop_loss": entry.stop_loss,
        "take_profit": entry.take_profit,
        "risk_reward_ratio": rr_ratio,
        "status": "open",
        "pnl_amount": None,
        "pnl_percent": None,
        "emotion_before": entry.emotion_before,
        "emotion_after": None,
        "strategy_used": entry.strategy_used,
        "reason_entry": entry.reason_entry,
        "reason_exit": None,
        "lessons_learned": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None
    }
    
    await db.journal.insert_one(journal_entry)
    journal_entry.pop("_id", None)
    return journal_entry

@router.get("/trades")
async def get_journal_entries(
    status: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get trade journal entries"""
    query = {"user_id": current_user["id"]}
    if status:
        query["status"] = status
    
    entries = await db.journal.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return entries

@router.put("/trades/{trade_id}/close")
async def close_journal_trade(trade_id: str, close_data: TradeJournalClose, current_user: dict = Depends(get_current_user)):
    """Close a trade and calculate P&L"""
    trade = await db.journal.find_one({"id": trade_id, "user_id": current_user["id"]}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade["status"] != "open":
        raise HTTPException(status_code=400, detail="Trade already closed")
    
    if trade["trade_type"] == "BUY":
        pnl_amount = (close_data.exit_price - trade["entry_price"]) * trade["quantity"]
        pnl_percent = ((close_data.exit_price - trade["entry_price"]) / trade["entry_price"]) * 100
    else:
        pnl_amount = (trade["entry_price"] - close_data.exit_price) * trade["quantity"]
        pnl_percent = ((trade["entry_price"] - close_data.exit_price) / trade["entry_price"]) * 100
    
    if pnl_percent > 0.5:
        status = "closed_profit"
    elif pnl_percent < -0.5:
        status = "closed_loss"
    else:
        status = "closed_breakeven"
    
    update_data = {
        "exit_price": close_data.exit_price,
        "exit_date": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "pnl_amount": round(pnl_amount, 2),
        "pnl_percent": round(pnl_percent, 2),
        "emotion_after": close_data.emotion_after,
        "reason_exit": close_data.reason_exit,
        "lessons_learned": close_data.lessons_learned,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.journal.update_one({"id": trade_id}, {"$set": update_data})
    return {"message": "Trade closed", "pnl_percent": round(pnl_percent, 2), "status": status}

@router.get("/stats")
async def get_trading_stats(current_user: dict = Depends(get_current_user)):
    """Get comprehensive trading statistics"""
    trades = await db.journal.find(
        {"user_id": current_user["id"], "status": {"$ne": "open"}},
        {"_id": 0}
    ).to_list(1000)
    
    if not trades:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "average_win": 0,
            "average_loss": 0,
            "best_trade": 0,
            "worst_trade": 0,
            "profit_factor": 0,
            "average_rr": 0,
            "most_traded_symbol": "N/A",
            "best_timeframe": "N/A",
            "current_streak": 0,
            "max_drawdown": 0
        }
    
    total = len(trades)
    winning = [t for t in trades if t["status"] == "closed_profit"]
    losing = [t for t in trades if t["status"] == "closed_loss"]
    
    win_rate = (len(winning) / total * 100) if total > 0 else 0
    
    pnls = [t.get("pnl_percent", 0) for t in trades]
    total_pnl = sum(pnls)
    
    win_pnls = [t.get("pnl_percent", 0) for t in winning]
    loss_pnls = [t.get("pnl_percent", 0) for t in losing]
    
    avg_win = sum(win_pnls) / len(win_pnls) if win_pnls else 0
    avg_loss = sum(loss_pnls) / len(loss_pnls) if loss_pnls else 0
    
    best_trade = max(pnls) if pnls else 0
    worst_trade = min(pnls) if pnls else 0
    
    gross_profit = sum([p for p in pnls if p > 0])
    gross_loss = abs(sum([p for p in pnls if p < 0]))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit
    
    rrs = [t.get("risk_reward_ratio", 0) for t in trades]
    avg_rr = sum(rrs) / len(rrs) if rrs else 0
    
    symbols = [t["symbol"] for t in trades]
    most_traded = Counter(symbols).most_common(1)[0][0] if symbols else "N/A"
    
    timeframes = {}
    for t in trades:
        tf = t.get("timeframe", "unknown")
        if tf not in timeframes:
            timeframes[tf] = {"wins": 0, "total": 0}
        timeframes[tf]["total"] += 1
        if t["status"] == "closed_profit":
            timeframes[tf]["wins"] += 1
    
    best_tf = max(timeframes.items(), key=lambda x: x[1]["wins"]/x[1]["total"] if x[1]["total"] > 0 else 0)[0] if timeframes else "N/A"
    
    sorted_trades = sorted(trades, key=lambda x: x.get("exit_date", ""), reverse=True)
    streak = 0
    streak_type = None
    for t in sorted_trades:
        if streak_type is None:
            streak_type = t["status"]
            streak = 1
        elif t["status"] == streak_type:
            streak += 1
        else:
            break
    
    current_streak = streak if streak_type == "closed_profit" else -streak
    
    cumulative = 0
    peak = 0
    max_dd = 0
    for pnl in pnls:
        cumulative += pnl
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd
    
    return {
        "total_trades": total,
        "winning_trades": len(winning),
        "losing_trades": len(losing),
        "win_rate": round(win_rate, 1),
        "total_pnl": round(total_pnl, 2),
        "average_win": round(avg_win, 2),
        "average_loss": round(avg_loss, 2),
        "best_trade": round(best_trade, 2),
        "worst_trade": round(worst_trade, 2),
        "profit_factor": round(profit_factor, 2),
        "average_rr": round(avg_rr, 2),
        "most_traded_symbol": most_traded,
        "best_timeframe": best_tf,
        "current_streak": current_streak,
        "max_drawdown": round(max_dd, 2)
    }
