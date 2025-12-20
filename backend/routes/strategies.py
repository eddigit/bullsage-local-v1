from fastapi import APIRouter, Depends
from datetime import datetime, timezone
import uuid

from ..core.config import db
from ..core.auth import get_current_user
from ..models.schemas import StrategyCreate, StrategyResponse

router = APIRouter(prefix="/strategies", tags=["Strategies"])

@router.post("", response_model=StrategyResponse)
async def create_strategy(strategy: StrategyCreate, current_user: dict = Depends(get_current_user)):
    """Create a new trading strategy"""
    strategy_doc = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        **strategy.dict(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.strategies.insert_one(strategy_doc)
    return StrategyResponse(**strategy_doc)

@router.get("")
async def get_strategies(current_user: dict = Depends(get_current_user)):
    """Get user's trading strategies"""
    strategies = await db.strategies.find(
        {"user_id": current_user["id"]}, 
        {"_id": 0}
    ).to_list(100)
    return strategies

@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a trading strategy"""
    result = await db.strategies.delete_one({
        "id": strategy_id,
        "user_id": current_user["id"]
    })
    return {"deleted": result.deleted_count > 0}
