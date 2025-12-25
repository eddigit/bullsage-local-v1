from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid
import logging

from ..core.config import db
from ..core.auth import get_current_user
from ..models.schemas import PaperTrade, PaperTradeCreate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/paper-trading", tags=["Paper Trading"])

@router.post("/trade", response_model=PaperTrade)
async def execute_paper_trade(trade: PaperTradeCreate, current_user: dict = Depends(get_current_user)):
    """Execute a paper trade"""
    user_id = current_user["id"]
    
    user = await db.users.find_one({"id": user_id})
    balance = user.get("paper_balance", 10000.0)
    portfolio = user.get("portfolio", {})
    
    total_cost = trade.amount * trade.price
    
    if trade.type == "buy":
        if total_cost > balance:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        new_balance = balance - total_cost
        current_holding = portfolio.get(trade.symbol, {"amount": 0, "avg_price": 0})
        
        total_amount = current_holding["amount"] + trade.amount
        if total_amount > 0:
            new_avg_price = ((current_holding["amount"] * current_holding["avg_price"]) + total_cost) / total_amount
        else:
            new_avg_price = trade.price
        
        portfolio[trade.symbol] = {"amount": total_amount, "avg_price": new_avg_price}
        
    elif trade.type == "sell":
        current_holding = portfolio.get(trade.symbol, {"amount": 0})
        if current_holding["amount"] < trade.amount:
            raise HTTPException(status_code=400, detail="Insufficient holdings")
        
        new_balance = balance + total_cost
        remaining = current_holding["amount"] - trade.amount
        
        if remaining > 0:
            portfolio[trade.symbol] = {"amount": remaining, "avg_price": current_holding.get("avg_price", trade.price)}
        else:
            portfolio.pop(trade.symbol, None)
    else:
        raise HTTPException(status_code=400, detail="Invalid trade type")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"paper_balance": new_balance, "portfolio": portfolio}}
    )
    
    trade_id = str(uuid.uuid4())
    trade_doc = {
        "id": trade_id,
        "user_id": user_id,
        "symbol": trade.symbol,
        "type": trade.type,
        "amount": trade.amount,
        "price": trade.price,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "executed"
    }
    await db.paper_trades.insert_one(trade_doc)
    
    return PaperTrade(**trade_doc)

@router.get("/trades")
async def get_paper_trades(limit: int = 50, current_user: dict = Depends(get_current_user)):
    """Get paper trading history"""
    try:
        user_id = current_user["id"]
        logger.info(f"Fetching trades for user: {user_id}")
        
        trades = await db.paper_trades.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        logger.info(f"Found {len(trades)} trades for user: {user_id}")
        
        # Always return a list
        return trades if trades else []
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        return []

@router.get("/portfolio")
async def get_paper_portfolio(current_user: dict = Depends(get_current_user)):
    """Get paper trading portfolio"""
    try:
        user = await db.users.find_one({"id": current_user["id"]})
        if not user:
            logger.warning(f"User not found for portfolio: {current_user['id']}")
            return {
                "balance": 10000.0,
                "portfolio": {},
                "initial_balance": 10000.0
            }
        
        portfolio = user.get("portfolio", {})
        logger.info(f"Portfolio for user {current_user['id']}: {len(portfolio)} positions")
        
        return {
            "balance": user.get("paper_balance", 10000.0),
            "portfolio": portfolio,
            "initial_balance": 10000.0
        }
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        return {
            "balance": 10000.0,
            "portfolio": {},
            "initial_balance": 10000.0
        }

@router.post("/reset")
async def reset_paper_portfolio(current_user: dict = Depends(get_current_user)):
    """Reset paper trading portfolio"""
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"paper_balance": 10000.0, "portfolio": {}}}
    )
    await db.paper_trades.delete_many({"user_id": current_user["id"]})
    return {"message": "Portfolio reset successfully", "balance": 10000.0}
