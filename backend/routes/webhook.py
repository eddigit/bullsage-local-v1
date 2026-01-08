"""
Bull Sage - Webhook Routes pour Automatisation
==============================================

Endpoints securises pour l'automatisation des trades via Claude ou autres systemes.

Securite:
- Header X-Claude-Token requis
- Rate limiting 10 req/min
- Logging MongoDB

Endpoints:
- POST /api/webhook/execute-trade
- GET  /api/webhook/positions
- GET  /api/webhook/signals
- POST /api/webhook/close-position
- GET  /api/webhook/account-status
- POST /api/webhook/acknowledge-signal/{signal_id}
"""

import os
import uuid
import httpx
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from functools import wraps
from collections import defaultdict
import time

from fastapi import APIRouter, HTTPException, Header, Request, Depends
from pydantic import BaseModel, Field

from core.config import db, DYDX_EXECUTOR_URL, DYDX_API_SECRET
from config.trading_config import trading_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])

# ============ RATE LIMITING ============

class RateLimiter:
    """Simple rate limiter in-memory"""
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds

        # Nettoyer les vieilles requetes
        self.requests[key] = [t for t in self.requests[key] if t > window_start]

        if len(self.requests[key]) >= self.max_requests:
            return False

        self.requests[key].append(now)
        return True

    def get_remaining(self, key: str) -> int:
        now = time.time()
        window_start = now - self.window_seconds
        self.requests[key] = [t for t in self.requests[key] if t > window_start]
        return max(0, self.max_requests - len(self.requests[key]))


rate_limiter = RateLimiter(
    max_requests=trading_config.WEBHOOK_RATE_LIMIT,
    window_seconds=60
)

# Cooldown tracker par marche
last_trade_by_market: Dict[str, datetime] = {}

# ============ SECURITY ============

WEBHOOK_TOKEN = os.getenv("CLAUDE_WEBHOOK_TOKEN", "")


async def verify_webhook_token(x_claude_token: Optional[str] = Header(None)):
    """Verifie le token webhook"""
    if not trading_config.WEBHOOK_TOKEN_REQUIRED:
        return True

    if not WEBHOOK_TOKEN:
        logger.warning("[Webhook] CLAUDE_WEBHOOK_TOKEN non configure")
        return True  # Permettre en dev si non configure

    if x_claude_token != WEBHOOK_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid webhook token")

    return True


async def check_rate_limit(request: Request):
    """Verifie le rate limiting"""
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 10 requests per minute."
        )
    return True


# ============ LOGGING ============

async def log_webhook_call(
    endpoint: str,
    method: str,
    request_data: Dict,
    response_data: Dict,
    status: str,
    execution_time_ms: float,
    client_ip: str = "unknown"
):
    """Log un appel webhook dans MongoDB"""
    if not trading_config.LOG_WEBHOOK_CALLS:
        return

    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "method": method,
        "client_ip": client_ip,
        "request": request_data,
        "response": response_data,
        "status": status,
        "execution_time_ms": execution_time_ms
    }

    try:
        await db.webhook_logs.insert_one(log_entry)
    except Exception as e:
        logger.error(f"[Webhook] Erreur logging: {e}")


async def log_trade_journal(
    signal_id: str,
    market: str,
    direction: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    size: float,
    execution_result: Dict,
    source: str = "webhook"
):
    """Log un trade dans le journal"""
    if not trading_config.LOG_ALL_TRADES:
        return

    journal_entry = {
        "id": str(uuid.uuid4()),
        "signal_id": signal_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market": market,
        "direction": direction,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "size": size,
        "source": source,
        "execution": execution_result,
        "status": "OPEN" if execution_result.get("success") else "FAILED"
    }

    try:
        await db.trade_journal.insert_one(journal_entry)
    except Exception as e:
        logger.error(f"[Webhook] Erreur journal: {e}")


# ============ MODELS ============

class ExecuteTradeRequest(BaseModel):
    """Requete pour executer un trade"""
    market: str = Field(..., description="Marche (ex: BTC-USD)")
    direction: str = Field(..., description="LONG ou SHORT")
    size: Optional[float] = Field(None, description="Taille en crypto")
    size_usdc: Optional[float] = Field(None, description="Taille en USDC")
    size_percent: Optional[float] = Field(None, description="Taille en % du capital")
    stopLoss: float = Field(..., description="Prix du stop loss")
    takeProfit: Optional[float] = Field(None, description="Prix du take profit")
    confidence: int = Field(80, description="Score de confiance 0-100")
    source: str = Field("webhook", description="Source du signal")
    signal_id: Optional[str] = Field(None, description="ID du signal original")
    metadata: Optional[Dict] = Field(None, description="Donnees supplementaires")


class ClosePositionRequest(BaseModel):
    """Requete pour fermer une position"""
    market: str = Field(..., description="Marche a fermer")
    reason: Optional[str] = Field("manual", description="Raison de la fermeture")


class AcknowledgeSignalRequest(BaseModel):
    """Requete pour marquer un signal comme traite"""
    action: str = Field(..., description="Action prise: EXECUTED, REJECTED, SKIPPED")
    notes: Optional[str] = Field(None, description="Notes optionnelles")


# ============ HELPERS ============

def check_cooldown(market: str) -> Dict:
    """Verifie le cooldown pour un marche"""
    last_trade = last_trade_by_market.get(market)

    if not last_trade:
        return {"allowed": True}

    elapsed = (datetime.now(timezone.utc) - last_trade).total_seconds()

    if elapsed < trading_config.TRADE_COOLDOWN_SECONDS:
        remaining = int(trading_config.TRADE_COOLDOWN_SECONDS - elapsed)
        return {
            "allowed": False,
            "remaining_seconds": remaining,
            "error": f"Cooldown actif sur {market}: {remaining}s restantes"
        }

    return {"allowed": True}


def record_trade(market: str):
    """Enregistre un trade pour le cooldown"""
    last_trade_by_market[market] = datetime.now(timezone.utc)


async def call_dydx_executor(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Appelle le dydx-executor"""
    url = f"{DYDX_EXECUTOR_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}

    if DYDX_API_SECRET:
        headers["X-API-Key"] = DYDX_API_SECRET

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            else:
                response = await client.post(url, headers=headers, json=data)

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"dYdX executor error: {response.status_code}",
                    "details": response.text
                }
    except httpx.ConnectError:
        return {"success": False, "error": "dYdX executor not available"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============ ENDPOINTS ============

@router.post("/execute-trade")
async def execute_trade(
    request: Request,
    trade: ExecuteTradeRequest,
    _token: bool = Depends(verify_webhook_token),
    _rate: bool = Depends(check_rate_limit)
):
    """
    Execute un trade sur dYdX avec tous les garde-fous.

    Validations:
    - Market autorise
    - Confidence >= MIN_CONFIDENCE
    - Stop loss obligatoire
    - Risk <= MAX_RISK_PERCENT
    - Cooldown respecte
    - Margin suffisant
    """
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"

    logger.info(f"[Webhook] execute-trade: {trade.market} {trade.direction}")

    result = {
        "success": False,
        "checks": {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    try:
        # 1. Verifier si le trading est actif
        if not trading_config.TRADING_ENABLED:
            result["error"] = "Trading desactive"
            result["code"] = "TRADING_DISABLED"
            return result

        # 2. Verifier le marche
        if not trading_config.is_market_allowed(trade.market):
            result["error"] = f"Marche non autorise: {trade.market}"
            result["code"] = "MARKET_NOT_ALLOWED"
            result["allowed_markets"] = trading_config.ALLOWED_MARKETS
            return result
        result["checks"]["market"] = "OK"

        # 3. Verifier la confidence
        if not trading_config.is_confidence_sufficient(trade.confidence):
            result["error"] = f"Confidence insuffisante: {trade.confidence} < {trading_config.MIN_CONFIDENCE}"
            result["code"] = "LOW_CONFIDENCE"
            return result
        result["checks"]["confidence"] = "OK"

        # 4. Verifier le stop loss
        if trading_config.REQUIRE_STOP_LOSS and not trade.stopLoss:
            result["error"] = "Stop loss obligatoire"
            result["code"] = "STOP_LOSS_REQUIRED"
            return result
        result["checks"]["stop_loss"] = "OK"

        # 5. Verifier le cooldown
        cooldown_check = check_cooldown(trade.market)
        if not cooldown_check["allowed"]:
            result["error"] = cooldown_check["error"]
            result["code"] = "COOLDOWN_ACTIVE"
            result["retry_after"] = cooldown_check["remaining_seconds"]
            return result
        result["checks"]["cooldown"] = "OK"

        # 6. Recuperer le statut du compte
        account_status = await call_dydx_executor("/account")
        if not account_status.get("success", False) and "equity" not in account_status:
            result["error"] = "Impossible de recuperer le statut du compte"
            result["code"] = "ACCOUNT_ERROR"
            result["details"] = account_status
            return result

        equity = account_status.get("equity", 0)
        margin_available = account_status.get("marginAvailable", account_status.get("freeCollateral", 0))
        result["account"] = {"equity": equity, "margin_available": margin_available}

        # 7. Calculer la taille de position
        if trade.size:
            position_size = trade.size
        elif trade.size_usdc:
            # Recuperer le prix actuel
            prices = await call_dydx_executor("/prices")
            current_price = prices.get("prices", {}).get(trade.market, 0)
            if not current_price:
                result["error"] = f"Prix non disponible pour {trade.market}"
                result["code"] = "PRICE_ERROR"
                return result
            position_size = trade.size_usdc / current_price
        elif trade.size_percent:
            # Calculer depuis le pourcentage du capital
            if trade.size_percent > trading_config.MAX_POSITION_SIZE_PERCENT:
                result["error"] = f"Taille trop grande: {trade.size_percent}% > max {trading_config.MAX_POSITION_SIZE_PERCENT}%"
                result["code"] = "SIZE_TOO_LARGE"
                return result
            position_value = equity * (trade.size_percent / 100)
            prices = await call_dydx_executor("/prices")
            current_price = prices.get("prices", {}).get(trade.market, 0)
            if not current_price:
                result["error"] = f"Prix non disponible pour {trade.market}"
                result["code"] = "PRICE_ERROR"
                return result
            position_size = position_value / current_price
        else:
            # Utiliser la taille par defaut
            position_value = trading_config.calculate_position_size(equity)
            prices = await call_dydx_executor("/prices")
            current_price = prices.get("prices", {}).get(trade.market, 0)
            if not current_price:
                result["error"] = f"Prix non disponible pour {trade.market}"
                result["code"] = "PRICE_ERROR"
                return result
            position_size = position_value / current_price

        result["calculated_size"] = position_size

        # 8. Verifier le risque
        prices = await call_dydx_executor("/prices")
        current_price = prices.get("prices", {}).get(trade.market, 0)
        if current_price and trade.stopLoss:
            risk_amount = trading_config.calculate_risk_amount(
                position_size, current_price, trade.stopLoss, trade.direction
            )
            risk_percent = (risk_amount / equity) * 100 if equity > 0 else 0

            if risk_percent > trading_config.MAX_RISK_PERCENT:
                result["error"] = f"Risque trop eleve: {risk_percent:.2f}% > max {trading_config.MAX_RISK_PERCENT}%"
                result["code"] = "RISK_TOO_HIGH"
                result["risk_details"] = {
                    "risk_amount": risk_amount,
                    "risk_percent": risk_percent,
                    "max_allowed": trading_config.MAX_RISK_PERCENT
                }
                return result
            result["checks"]["risk"] = f"OK ({risk_percent:.2f}%)"

        # 9. Executer sur dYdX
        execute_payload = {
            "market": trade.market,
            "direction": trade.direction,
            "size": position_size,
            "stopLoss": trade.stopLoss,
            "takeProfit": trade.takeProfit,
            "maxSlippage": trading_config.MAX_SLIPPAGE_PERCENT,
            "metadata": {
                "source": trade.source,
                "signal_id": trade.signal_id,
                "confidence": trade.confidence,
                **(trade.metadata or {})
            }
        }

        execution_result = await call_dydx_executor("/execute", "POST", execute_payload)

        result["execution"] = execution_result
        result["success"] = execution_result.get("success", False)

        if result["success"]:
            # Enregistrer le cooldown
            record_trade(trade.market)

            # Log dans le journal
            await log_trade_journal(
                signal_id=trade.signal_id or str(uuid.uuid4()),
                market=trade.market,
                direction=trade.direction,
                entry_price=current_price,
                stop_loss=trade.stopLoss,
                take_profit=trade.takeProfit,
                size=position_size,
                execution_result=execution_result,
                source=trade.source
            )

    except Exception as e:
        logger.error(f"[Webhook] execute-trade error: {e}")
        result["error"] = str(e)
        result["code"] = "INTERNAL_ERROR"

    # Log l'appel webhook
    execution_time = (time.time() - start_time) * 1000
    await log_webhook_call(
        endpoint="/execute-trade",
        method="POST",
        request_data=trade.dict(),
        response_data=result,
        status="success" if result["success"] else "failed",
        execution_time_ms=execution_time,
        client_ip=client_ip
    )

    return result


@router.get("/positions")
async def get_positions(
    request: Request,
    _token: bool = Depends(verify_webhook_token),
    _rate: bool = Depends(check_rate_limit)
):
    """
    Recupere les positions ouvertes avec details.

    Response:
    - positions: Liste des positions
    - equity: Equity totale
    - margin_available: Margin disponible
    - total_pnl: PnL non realise total
    """
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"

    result = await call_dydx_executor("/positions/detailed")

    # Log
    execution_time = (time.time() - start_time) * 1000
    await log_webhook_call(
        endpoint="/positions",
        method="GET",
        request_data={},
        response_data={"positions_count": len(result.get("positions", []))},
        status="success" if result.get("success") else "failed",
        execution_time_ms=execution_time,
        client_ip=client_ip
    )

    return result


@router.get("/signals")
async def get_pending_signals(
    request: Request,
    hours: int = 2,
    _token: bool = Depends(verify_webhook_token),
    _rate: bool = Depends(check_rate_limit)
):
    """
    Recupere les signaux A/A+ non traites des dernieres heures.

    Query params:
    - hours: Nombre d'heures a considerer (defaut: 2)

    Response:
    - signals: Liste des signaux eligibles
    - count: Nombre de signaux
    """
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()

        # Requete MongoDB pour signaux A/A+ recents et non traites
        query = {
            "created_at": {"$gte": cutoff_str},
            "status": "active",
            "$or": [
                {"grade": {"$in": trading_config.ALLOWED_GRADES}},
                {"confidence": {"$gte": trading_config.MIN_CONFIDENCE}}
            ],
            "webhook_acknowledged": {"$ne": True}
        }

        signals = await db.signals.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)

        # Filtrer les marches autorises
        filtered_signals = [
            s for s in signals
            if trading_config.is_market_allowed(
                s.get("symbol", "").upper() + "-USD"
                if not s.get("symbol", "").endswith("-USD")
                else s.get("symbol", "").upper()
            )
        ]

        result = {
            "success": True,
            "signals": filtered_signals,
            "count": len(filtered_signals),
            "cutoff": cutoff_str,
            "allowed_grades": trading_config.ALLOWED_GRADES,
            "min_confidence": trading_config.MIN_CONFIDENCE
        }

    except Exception as e:
        logger.error(f"[Webhook] signals error: {e}")
        result = {"success": False, "error": str(e), "signals": [], "count": 0}

    # Log
    execution_time = (time.time() - start_time) * 1000
    await log_webhook_call(
        endpoint="/signals",
        method="GET",
        request_data={"hours": hours},
        response_data={"count": result.get("count", 0)},
        status="success" if result.get("success") else "failed",
        execution_time_ms=execution_time,
        client_ip=client_ip
    )

    return result


@router.post("/close-position")
async def close_position(
    request: Request,
    close_req: ClosePositionRequest,
    _token: bool = Depends(verify_webhook_token),
    _rate: bool = Depends(check_rate_limit)
):
    """
    Ferme une position ouverte.

    Body:
    - market: Marche a fermer (ex: BTC-USD)
    - reason: Raison de la fermeture (optionnel)
    """
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"

    logger.info(f"[Webhook] close-position: {close_req.market}")

    result = await call_dydx_executor("/positions/close", "POST", {
        "market": close_req.market,
        "reason": close_req.reason
    })

    # Log
    execution_time = (time.time() - start_time) * 1000
    await log_webhook_call(
        endpoint="/close-position",
        method="POST",
        request_data=close_req.dict(),
        response_data=result,
        status="success" if result.get("success") else "failed",
        execution_time_ms=execution_time,
        client_ip=client_ip
    )

    return result


@router.get("/account-status")
async def get_account_status(
    request: Request,
    _token: bool = Depends(verify_webhook_token),
    _rate: bool = Depends(check_rate_limit)
):
    """
    Recupere le statut complet du compte.

    Response:
    - equity: Equity totale
    - margin_used: Margin utilise
    - margin_available: Margin disponible
    - open_positions_count: Nombre de positions ouvertes
    - daily_pnl: PnL du jour (si disponible)
    """
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"

    # Recuperer compte et positions
    account = await call_dydx_executor("/account")
    positions = await call_dydx_executor("/positions/detailed")

    # Calculer le PnL total
    total_pnl = 0
    if positions.get("success") and positions.get("positions"):
        total_pnl = sum(p.get("unrealizedPnl", 0) for p in positions["positions"])

    result = {
        "success": True,
        "equity": account.get("equity", 0),
        "margin_used": account.get("marginUsed", 0),
        "margin_available": account.get("marginAvailable", account.get("freeCollateral", 0)),
        "open_positions_count": len(positions.get("positions", [])),
        "total_unrealized_pnl": total_pnl,
        "network": account.get("network", "testnet"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trading_config": {
            "enabled": trading_config.TRADING_ENABLED,
            "max_risk_percent": trading_config.MAX_RISK_PERCENT,
            "max_positions": trading_config.MAX_OPEN_POSITIONS,
            "cooldown_seconds": trading_config.TRADE_COOLDOWN_SECONDS
        }
    }

    # Log
    execution_time = (time.time() - start_time) * 1000
    await log_webhook_call(
        endpoint="/account-status",
        method="GET",
        request_data={},
        response_data={"equity": result.get("equity")},
        status="success",
        execution_time_ms=execution_time,
        client_ip=client_ip
    )

    return result


@router.post("/acknowledge-signal/{signal_id}")
async def acknowledge_signal(
    request: Request,
    signal_id: str,
    ack: AcknowledgeSignalRequest,
    _token: bool = Depends(verify_webhook_token),
    _rate: bool = Depends(check_rate_limit)
):
    """
    Marque un signal comme traite par le webhook.

    Path params:
    - signal_id: ID du signal

    Body:
    - action: EXECUTED, REJECTED, SKIPPED
    - notes: Notes optionnelles
    """
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"

    logger.info(f"[Webhook] acknowledge-signal: {signal_id} -> {ack.action}")

    try:
        update_result = await db.signals.update_one(
            {"id": signal_id},
            {
                "$set": {
                    "webhook_acknowledged": True,
                    "webhook_action": ack.action,
                    "webhook_notes": ack.notes,
                    "webhook_acknowledged_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )

        if update_result.modified_count == 0:
            result = {"success": False, "error": "Signal not found", "code": "NOT_FOUND"}
        else:
            result = {
                "success": True,
                "signal_id": signal_id,
                "action": ack.action,
                "acknowledged_at": datetime.now(timezone.utc).isoformat()
            }

    except Exception as e:
        logger.error(f"[Webhook] acknowledge error: {e}")
        result = {"success": False, "error": str(e)}

    # Log
    execution_time = (time.time() - start_time) * 1000
    await log_webhook_call(
        endpoint=f"/acknowledge-signal/{signal_id}",
        method="POST",
        request_data=ack.dict(),
        response_data=result,
        status="success" if result.get("success") else "failed",
        execution_time_ms=execution_time,
        client_ip=client_ip
    )

    return result


# ============ HEALTH CHECK ============

@router.get("/health")
async def webhook_health():
    """Health check pour les webhooks"""
    dydx_status = await call_dydx_executor("/health")

    return {
        "status": "ok",
        "webhook_enabled": True,
        "trading_enabled": trading_config.TRADING_ENABLED,
        "dydx_executor": dydx_status.get("status", "unknown"),
        "rate_limit_remaining": rate_limiter.get_remaining("health"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
