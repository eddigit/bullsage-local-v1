from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid
import httpx

from ..core.config import db, COINGECKO_API_URL, logger
from ..core.auth import get_current_user
from ..models.schemas import AlertCreate, AlertResponse, SmartAlertCreate

router = APIRouter(tags=["Alerts"])

@router.post("/alerts", response_model=AlertResponse)
async def create_alert(alert: AlertCreate, current_user: dict = Depends(get_current_user)):
    """Create a price alert"""
    alert_id = str(uuid.uuid4())
    alert_doc = {
        "id": alert_id,
        "user_id": current_user["id"],
        "symbol": alert.symbol.lower(),
        "target_price": alert.target_price,
        "condition": alert.condition,
        "name": alert.name or f"Alert {alert.symbol.upper()} {alert.condition} ${alert.target_price}",
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.alerts.insert_one(alert_doc)
    return AlertResponse(**alert_doc)

@router.get("/alerts")
async def get_alerts(current_user: dict = Depends(get_current_user)):
    """Get all alerts for current user"""
    alerts = await db.alerts.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).to_list(100)
    return alerts

@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an alert"""
    result = await db.alerts.delete_one({"id": alert_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert deleted"}

# Smart Alerts
@router.post("/alerts/smart")
async def create_smart_alert(alert: SmartAlertCreate, current_user: dict = Depends(get_current_user)):
    """Create a smart alert with more conditions"""
    alert_id = str(uuid.uuid4())
    alert_doc = {
        "id": alert_id,
        "user_id": current_user["id"],
        "symbol": alert.symbol.lower(),
        "condition_type": alert.condition_type,
        "value": alert.value,
        "name": alert.name or f"{alert.symbol.upper()} {alert.condition_type} {alert.value}",
        "sound_enabled": alert.sound_enabled,
        "repeat": alert.repeat,
        "active": True,
        "triggered": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.smart_alerts.insert_one(alert_doc)
    return alert_doc

@router.get("/alerts/smart")
async def get_smart_alerts(current_user: dict = Depends(get_current_user)):
    """Get all smart alerts for current user"""
    alerts = await db.smart_alerts.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).to_list(100)
    return alerts

@router.delete("/alerts/smart/{alert_id}")
async def delete_smart_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a smart alert"""
    await db.smart_alerts.delete_one({"id": alert_id, "user_id": current_user["id"]})
    return {"deleted": True}

@router.get("/alerts/check")
async def check_alerts(current_user: dict = Depends(get_current_user)):
    """Check and trigger alerts based on current prices"""
    alerts = await db.smart_alerts.find(
        {"user_id": current_user["id"], "active": True},
        {"_id": 0}
    ).to_list(100)
    
    if not alerts:
        return {"triggered": [], "message": "No active alerts"}
    
    # Get unique symbols
    symbols = list(set([a["symbol"] for a in alerts]))
    
    # Fetch current prices
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{COINGECKO_API_URL}/simple/price",
                params={"ids": ",".join(symbols), "vs_currencies": "usd", "include_24hr_change": "true"},
                timeout=10.0
            )
            if response.status_code == 200:
                prices = response.json()
            else:
                return {"triggered": [], "message": "Unable to fetch prices"}
    except Exception as e:
        logger.error(f"Error checking alerts: {e}")
        return {"triggered": [], "message": "Error fetching prices"}
    
    triggered = []
    for alert in alerts:
        symbol = alert["symbol"]
        if symbol not in prices:
            continue
        
        current_price = prices[symbol].get("usd", 0)
        change_24h = prices[symbol].get("usd_24h_change", 0)
        
        condition_met = False
        condition_type = alert["condition_type"]
        value = alert["value"]
        
        if condition_type == "price_above" and current_price >= value:
            condition_met = True
        elif condition_type == "price_below" and current_price <= value:
            condition_met = True
        elif condition_type == "change_above" and change_24h >= value:
            condition_met = True
        elif condition_type == "change_below" and change_24h <= value:
            condition_met = True
        
        if condition_met:
            triggered.append({
                **alert,
                "current_price": current_price,
                "change_24h": change_24h,
                "triggered_at": datetime.now(timezone.utc).isoformat()
            })
            
            if not alert.get("repeat", False):
                await db.smart_alerts.update_one(
                    {"id": alert["id"]},
                    {"$set": {"active": False, "triggered": True}}
                )
    
    return {"triggered": triggered, "checked": len(alerts)}
