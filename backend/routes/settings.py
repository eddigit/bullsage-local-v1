from fastapi import APIRouter, Depends

from ..core.config import db
from ..core.auth import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.put("/trading-level")
async def update_trading_level(level: str, current_user: dict = Depends(get_current_user)):
    """Update user's trading level"""
    valid_levels = ["beginner", "intermediate", "advanced"]
    if level not in valid_levels:
        return {"error": f"Invalid level. Must be one of: {valid_levels}"}
    
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"trading_level": level}}
    )
    return {"trading_level": level}
