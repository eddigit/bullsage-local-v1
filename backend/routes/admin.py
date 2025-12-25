from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import httpx
import asyncio
from typing import Optional

from ..core.config import (
    db, 
    ALPHA_VANTAGE_API_KEY, 
    FINNHUB_API_KEY, 
    FRED_API_KEY, 
    MARKETAUX_API_KEY,
    COINGECKO_API_URL,
    EMERGENT_LLM_KEY,
    logger
)
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


# ============== API HEALTH CHECK ==============

async def check_api_health(name: str, url: str, timeout: float = 10.0) -> dict:
    """Test if an API endpoint is reachable and responding"""
    start_time = datetime.now(timezone.utc)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                return {
                    "name": name,
                    "status": "online",
                    "response_time_ms": round(response_time, 2),
                    "status_code": response.status_code,
                    "message": "API fonctionnelle"
                }
            elif response.status_code == 429:
                return {
                    "name": name,
                    "status": "rate_limited",
                    "response_time_ms": round(response_time, 2),
                    "status_code": response.status_code,
                    "message": "Limite de requêtes atteinte"
                }
            else:
                return {
                    "name": name,
                    "status": "error",
                    "response_time_ms": round(response_time, 2),
                    "status_code": response.status_code,
                    "message": f"Code HTTP: {response.status_code}"
                }
    except httpx.TimeoutException:
        return {
            "name": name,
            "status": "timeout",
            "response_time_ms": timeout * 1000,
            "status_code": None,
            "message": "Timeout - API ne répond pas"
        }
    except Exception as e:
        return {
            "name": name,
            "status": "offline",
            "response_time_ms": None,
            "status_code": None,
            "message": str(e)[:100]
        }


@router.get("/api-health")
async def check_all_apis(current_user: dict = Depends(get_admin_user)):
    """Check health status of all external APIs"""
    
    # Define API endpoints to test
    api_checks = [
        ("CoinGecko", f"{COINGECKO_API_URL}/ping"),
        ("MongoDB", None),  # Special handling
        ("Binance", "https://api.binance.com/api/v3/ping"),
        ("CryptoCompare", "https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD"),
    ]
    
    # Add APIs that require keys
    if ALPHA_VANTAGE_API_KEY:
        api_checks.append(("Alpha Vantage", f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey={ALPHA_VANTAGE_API_KEY}"))
    else:
        api_checks.append(("Alpha Vantage", None))
        
    if FINNHUB_API_KEY:
        api_checks.append(("Finnhub", f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={FINNHUB_API_KEY}"))
    else:
        api_checks.append(("Finnhub", None))
        
    if FRED_API_KEY:
        api_checks.append(("FRED", f"https://api.stlouisfed.org/fred/series?series_id=VIXCLS&api_key={FRED_API_KEY}&file_type=json"))
    else:
        api_checks.append(("FRED", None))
    
    if MARKETAUX_API_KEY:
        api_checks.append(("MarketAux", f"https://api.marketaux.com/v1/news/all?api_token={MARKETAUX_API_KEY}&limit=1"))
    else:
        api_checks.append(("MarketAux", None))
    
    # Check LLM
    if EMERGENT_LLM_KEY:
        api_checks.append(("Emergent LLM", "https://api.emergentmind.com/health"))
    else:
        api_checks.append(("Emergent LLM", None))
    
    results = []
    
    # Check MongoDB separately
    try:
        await db.command("ping")
        results.append({
            "name": "MongoDB",
            "status": "online",
            "response_time_ms": 1,
            "status_code": 200,
            "message": "Base de données connectée"
        })
    except Exception as e:
        results.append({
            "name": "MongoDB",
            "status": "offline",
            "response_time_ms": None,
            "status_code": None,
            "message": str(e)[:100]
        })
    
    # Check all HTTP APIs in parallel
    http_checks = [(name, url) for name, url in api_checks if url is not None and name != "MongoDB"]
    unconfigured = [(name, url) for name, url in api_checks if url is None and name != "MongoDB"]
    
    if http_checks:
        tasks = [check_api_health(name, url) for name, url in http_checks]
        http_results = await asyncio.gather(*tasks)
        results.extend(http_results)
    
    # Add unconfigured APIs
    for name, _ in unconfigured:
        results.append({
            "name": name,
            "status": "not_configured",
            "response_time_ms": None,
            "status_code": None,
            "message": "Clé API non configurée"
        })
    
    # Calculate summary
    online_count = sum(1 for r in results if r["status"] == "online")
    total_count = len(results)
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "online": online_count,
            "total": total_count,
            "health_percentage": round((online_count / total_count) * 100, 1) if total_count > 0 else 0
        },
        "apis": sorted(results, key=lambda x: (x["status"] != "online", x["name"]))
    }


# ============== ERROR LOGS ==============

@router.post("/logs")
async def save_error_log(
    error_type: str,
    message: str,
    source: str,
    details: Optional[dict] = None,
    current_user: dict = Depends(get_current_user)
):
    """Save an error log (can be called by frontend or backend)"""
    log_entry = {
        "timestamp": datetime.now(timezone.utc),
        "error_type": error_type,
        "message": message,
        "source": source,
        "details": details or {},
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email")
    }
    
    await db.error_logs.insert_one(log_entry)
    logger.error(f"[{source}] {error_type}: {message}")
    
    return {"status": "logged"}


@router.get("/logs")
async def get_error_logs(
    limit: int = 100,
    error_type: Optional[str] = None,
    source: Optional[str] = None,
    current_user: dict = Depends(get_admin_user)
):
    """Get error logs (admin only)"""
    query = {}
    if error_type:
        query["error_type"] = error_type
    if source:
        query["source"] = source
    
    logs = await db.error_logs.find(
        query,
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # Get log statistics
    total_logs = await db.error_logs.count_documents({})
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_logs = await db.error_logs.count_documents({"timestamp": {"$gte": today_start}})
    
    # Get error types distribution
    pipeline = [
        {"$group": {"_id": "$error_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    error_types = await db.error_logs.aggregate(pipeline).to_list(10)
    
    # Get sources distribution
    pipeline_sources = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    sources = await db.error_logs.aggregate(pipeline_sources).to_list(10)
    
    return {
        "logs": logs,
        "stats": {
            "total": total_logs,
            "today": today_logs,
            "error_types": [{"type": e["_id"], "count": e["count"]} for e in error_types],
            "sources": [{"source": s["_id"], "count": s["count"]} for s in sources]
        }
    }


@router.delete("/logs")
async def clear_error_logs(
    older_than_days: int = 7,
    current_user: dict = Depends(get_admin_user)
):
    """Clear error logs older than specified days (admin only)"""
    from datetime import timedelta
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
    result = await db.error_logs.delete_many({"timestamp": {"$lt": cutoff_date}})
    
    return {
        "deleted_count": result.deleted_count,
        "message": f"Supprimé {result.deleted_count} logs de plus de {older_than_days} jours"
    }
