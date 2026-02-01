from fastapi import APIRouter, Depends
from datetime import datetime, timezone
import httpx
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])

@router.get("/")
async def root():
    return {"message": "BULL SAGE API is running"}

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "BULL SAGE API",
        "version": "2.0.0"
    }

@router.get("/api/system/health")
async def system_health_check():
    """
    Diagnostic complet de tous les services.
    Teste chaque dépendance externe et retourne un statut.
    """
    results = {}
    overall_status = "healthy"

    # 1. MongoDB
    try:
        from ..core.config import db
        await db.command("ping")
        results["mongodb"] = {"status": "ok", "message": "Connexion active"}
    except Exception as e:
        results["mongodb"] = {"status": "error", "message": str(e)}
        overall_status = "degraded"

    # 2. CryptoCompare (market data)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD")
            if resp.status_code == 200 and resp.json().get("USD"):
                results["cryptocompare"] = {"status": "ok", "message": f"BTC = ${resp.json()['USD']:,.0f}"}
            else:
                results["cryptocompare"] = {"status": "error", "message": f"HTTP {resp.status_code}"}
                overall_status = "degraded"
    except Exception as e:
        results["cryptocompare"] = {"status": "error", "message": str(e)}
        overall_status = "degraded"

    # 3. Kraken (chart data)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://api.kraken.com/0/public/Time")
            if resp.status_code == 200 and not resp.json().get("error"):
                results["kraken"] = {"status": "ok", "message": "API accessible"}
            else:
                results["kraken"] = {"status": "error", "message": f"HTTP {resp.status_code}"}
                overall_status = "degraded"
    except Exception as e:
        results["kraken"] = {"status": "error", "message": str(e)}
        overall_status = "degraded"

    # 4. Finnhub (news)
    finnhub_key = os.environ.get("FINNHUB_API_KEY", "")
    if finnhub_key:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"https://finnhub.io/api/v1/news?category=crypto&token={finnhub_key}")
                if resp.status_code == 200:
                    results["finnhub"] = {"status": "ok", "message": f"{len(resp.json())} articles"}
                else:
                    results["finnhub"] = {"status": "error", "message": f"HTTP {resp.status_code}"}
                    overall_status = "degraded"
        except Exception as e:
            results["finnhub"] = {"status": "error", "message": str(e)}
            overall_status = "degraded"
    else:
        results["finnhub"] = {"status": "warning", "message": "FINNHUB_API_KEY non configurée"}

    # 5. Deribit
    deribit_id = os.environ.get("DERIBIT_CLIENT_ID", "")
    deribit_url = os.environ.get("DERIBIT_API_URL", "https://test.deribit.com/api/v2")
    if deribit_id:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{deribit_url}/public/test")
                if resp.status_code == 200:
                    results["deribit"] = {"status": "ok", "message": f"API accessible ({deribit_url})"}
                else:
                    results["deribit"] = {"status": "error", "message": f"HTTP {resp.status_code}"}
                    overall_status = "degraded"
        except Exception as e:
            results["deribit"] = {"status": "error", "message": str(e)}
            overall_status = "degraded"
    else:
        results["deribit"] = {"status": "warning", "message": "DERIBIT_CLIENT_ID non configurée"}

    # 6. LLM (xAI / Grok)
    xai_key = os.environ.get("XAI_API_KEY", "")
    if xai_key:
        results["llm_xai"] = {"status": "ok", "message": "Clé configurée"}
    else:
        results["llm_xai"] = {"status": "warning", "message": "XAI_API_KEY non configurée"}

    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": results
    }
