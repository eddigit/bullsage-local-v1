from fastapi import APIRouter, Depends
from datetime import datetime, timezone

from ..core.config import db
from ..core.auth import get_current_user
from ..models.schemas import WatchlistUpdate

router = APIRouter(tags=["Watchlist"])

@router.put("/watchlist")
async def update_watchlist(update: WatchlistUpdate, current_user: dict = Depends(get_current_user)):
    """Update user's watchlist"""
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"watchlist": update.symbols}}
    )
    return {"watchlist": update.symbols}

@router.post("/watchlist/{symbol}")
async def add_to_watchlist(symbol: str, current_user: dict = Depends(get_current_user)):
    """Add symbol to watchlist"""
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$addToSet": {"watchlist": symbol}}
    )
    return {"message": f"{symbol} added to watchlist"}

@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str, current_user: dict = Depends(get_current_user)):
    """Remove symbol from watchlist"""
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$pull": {"watchlist": symbol}}
    )
    return {"message": f"{symbol} removed from watchlist"}
