from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone

from ..core.config import db, ALPHA_VANTAGE_API_KEY, FINNHUB_API_KEY, FRED_API_KEY, MARKETAUX_API_KEY
from ..core.auth import get_current_user, get_admin_user

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users")
async def get_all_users(current_user: dict = Depends(get_admin_user)):
    """Get all users (admin only)"""
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return users

@router.get("/stats")
async def get_admin_stats(current_user: dict = Depends(get_admin_user)):
    """Get admin statistics"""
    total_users = await db.users.count_documents({})
    total_trades = await db.paper_trades.count_documents({})
    total_signals = await db.signals.count_documents({})
    total_alerts = await db.alerts.count_documents({})
    total_journal = await db.journal.count_documents({})
    total_strategies = await db.strategies.count_documents({})
    
    return {
        "total_users": total_users,
        "total_trades": total_trades,
        "total_signals": total_signals,
        "total_alerts": total_alerts,
        "total_journal_entries": total_journal,
        "total_strategies": total_strategies,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_admin_user)):
    """Delete a user and all their data"""
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    await db.users.delete_one({"id": user_id})
    await db.paper_trades.delete_many({"user_id": user_id})
    await db.signals.delete_many({"user_id": user_id})
    await db.alerts.delete_many({"user_id": user_id})
    await db.journal.delete_many({"user_id": user_id})
    await db.strategies.delete_many({"user_id": user_id})
    
    return {"message": "User and all associated data deleted"}

@router.put("/users/{user_id}/admin")
async def toggle_admin(user_id: str, is_admin: bool, current_user: dict = Depends(get_admin_user)):
    """Toggle admin status for a user"""
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot modify your own admin status")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_admin": is_admin}}
    )
    return {"message": f"Admin status set to {is_admin}"}

@router.get("/api-keys")
async def get_api_keys_status(current_user: dict = Depends(get_admin_user)):
    """Check which API keys are configured"""
    return {
        "alpha_vantage": {
            "configured": bool(ALPHA_VANTAGE_API_KEY),
            "key_preview": f"{ALPHA_VANTAGE_API_KEY[:4]}..." if ALPHA_VANTAGE_API_KEY else None,
            "usage": "Forex, Stock quotes, Technical indicators"
        },
        "finnhub": {
            "configured": bool(FINNHUB_API_KEY),
            "key_preview": f"{FINNHUB_API_KEY[:4]}..." if FINNHUB_API_KEY else None,
            "usage": "Market news, Stock quotes, Company info"
        },
        "fred": {
            "configured": bool(FRED_API_KEY),
            "key_preview": f"{FRED_API_KEY[:4]}..." if FRED_API_KEY else None,
            "usage": "Economic data (VIX, DXY, Interest rates)"
        },
        "marketaux": {
            "configured": bool(MARKETAUX_API_KEY),
            "key_preview": f"{MARKETAUX_API_KEY[:4]}..." if MARKETAUX_API_KEY else None,
            "usage": "News sentiment analysis"
        },
        "coingecko": {
            "configured": True,
            "key_preview": "Public API",
            "usage": "Cryptocurrency data (free tier)"
        }
    }
