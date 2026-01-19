"""
Bull Sage Council API Routes - Version Optimisée
=================================================
Endpoints pour le système multi-agent de trading.

RÈGLE CRITIQUE: Aucun appel automatique - confirmation utilisateur requise.
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import asyncio
import os
import sys

# Ajouter le chemin pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import db, logger
from core.auth import get_current_user
from services.council_service import BullSageCouncil, get_available_agents, get_available_modes
from config.llm_config import LLMConfig

router = APIRouter(prefix="/council", tags=["Council"])

# WebSocket connections pour logs temps réel
active_connections: Dict[str, WebSocket] = {}


# ============== MODELS ==============

class AnalysisRequest(BaseModel):
    """Requête d'analyse - requiert confirmation utilisateur"""
    symbol: str = Field(..., description="Symbole de l'actif (ex: BTC, ETH, bitcoin)")
    mode: str = Field("standard", description="Mode d'analyse: quick, standard, full")
    confirm_cost: bool = Field(False, description="L'utilisateur a confirmé les coûts")


class CostEstimateRequest(BaseModel):
    """Demande d'estimation de coûts AVANT analyse"""
    symbol: str
    mode: str = "standard"


# ============== ENDPOINTS ==============

@router.get("/modes")
async def list_analysis_modes(current_user: dict = Depends(get_current_user)):
    """
    Liste les modes d'analyse disponibles avec leurs coûts.
    Permet à l'utilisateur de choisir avant de lancer une analyse.
    """
    modes = get_available_modes()
    
    return {
        **modes,
        "recommendation": {
            "quick": "Pour un screening rapide ou vérifier un setup",
            "standard": "Pour les trades quotidiens - meilleur rapport coût/qualité",
            "full": "Pour les décisions importantes ou gros trades"
        }
    }


@router.get("/agents")
async def get_council_agents(current_user: dict = Depends(get_current_user)):
    """
    Liste tous les agents disponibles dans le Council.
    """
    agents = get_available_agents()
    orchestrator = LLMConfig.get_orchestrator_status()
    
    return {
        "agents": agents,
        "total": len(agents),
        "orchestrator": orchestrator
    }


@router.get("/pricing")
async def get_llm_pricing(current_user: dict = Depends(get_current_user)):
    """
    Retourne la grille tarifaire par mode.
    """
    modes = {}
    for mode_name in LLMConfig.ANALYSIS_MODES.keys():
        mode_config = LLMConfig.ANALYSIS_MODES[mode_name]
        modes[mode_name] = {
            "name": mode_config["name"],
            "cost_usd": mode_config["estimated_cost"],
            "agents_count": len(mode_config["agents"])
        }
    
    return {
        "modes": modes,
        "currency": "USD",
        "note": "Coûts par requête. L'orchestrateur Groq est GRATUIT."
    }


@router.get("/cost-estimate/{mode}")
async def get_cost_estimate(
    mode: str = "standard",
    current_user: dict = Depends(get_current_user)
):
    """
    Affiche le coût estimé AVANT de lancer l'analyse.
    L'utilisateur doit voir ce coût et confirmer.
    """
    council = BullSageCouncil()
    estimate = council.get_cost_estimate(mode)
    
    if not estimate:
        raise HTTPException(status_code=400, detail=f"Mode invalide: {mode}")
    
    return {
        "status": "estimate",
        "message": f"Cette analyse coûtera environ ${estimate['estimated_cost_usd']:.4f}",
        **estimate
    }


@router.post("/estimate-cost")
async def estimate_analysis_cost(
    request: CostEstimateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    ⚠️ ÉTAPE 1: Estimer le coût AVANT de lancer l'analyse.
    L'utilisateur doit confirmer avant de procéder.
    """
    council = BullSageCouncil()
    estimate = council.get_cost_estimate(request.mode)
    
    return {
        "status": "estimation",
        "symbol": request.symbol,
        "requires_confirmation": True,
        "estimate": estimate,
        "message": f"⚠️ Analyse {request.symbol} en mode '{request.mode}' coûtera ~${estimate['estimated_cost_usd']:.4f}"
    }


@router.post("/analyze")
async def run_council_analysis(
    request: AnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    🎯 Lance l'analyse du Council.
    
    ⚠️ REQUIERT: confirm_cost = true
    Sans confirmation, seule une estimation est retournée.
    """
    council = BullSageCouncil()
    
    # Vérifier le mode
    estimate = council.get_cost_estimate(request.mode)
    if not estimate:
        raise HTTPException(status_code=400, detail=f"Mode invalide: {request.mode}")
    
    # Si pas de confirmation, retourner l'estimation
    if not request.confirm_cost:
        return {
            "status": "confirmation_required",
            "symbol": request.symbol,
            "mode": request.mode,
            "estimate": estimate,
            "message": f"⚠️ Analyse {request.symbol} en mode '{request.mode}' coûtera ~${estimate['estimated_cost_usd']:.4f}",
            "action": "Renvoyez avec confirm_cost=true pour confirmer et lancer l'analyse"
        }
    
    # L'utilisateur a confirmé - Lancer l'analyse
    try:
        # Créer le council avec callback pour logs
        logs_buffer: List[Dict] = []
        
        async def on_log(log: Dict):
            logs_buffer.append(log)
            # Envoyer via WebSocket si connecté
            await _broadcast_log(current_user["id"], log)
        
        council = BullSageCouncil(on_log=on_log)
        
        # Lancer l'analyse
        result = await council.analyze(
            symbol=request.symbol.upper(),
            mode=request.mode
        )
        
        # Sauvegarder l'analyse en base
        analysis_doc = {
            "user_id": current_user["id"],
            "session_id": result["session_id"],
            "symbol": request.symbol.upper(),
            "mode": request.mode,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents_count": result["agents"]["requested"],
            "final_verdict": result["recommendation"]["action"],
            "confidence": result["recommendation"]["confidence"],
            "consensus": result["consensus"],
            "costs": result["cost"],
            "execution_time": result["execution_time_seconds"]
        }
        await db.council_analyses.insert_one(analysis_doc)
        
        # Mettre à jour les stats de coûts utilisateur
        await _update_user_costs(current_user["id"], result["cost"]["total_cost_usd"])
        
        return {
            "status": "completed",
            "result": result,
            "logs": logs_buffer
        }
        
    except Exception as e:
        logger.error(f"Council analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/{symbol}")
async def analyze_symbol_get(
    symbol: str,
    mode: str = Query(default="standard", description="Mode: quick, standard, full"),
    confirm_cost: bool = Query(default=False, description="Confirmation du coût"),
    current_user: dict = Depends(get_current_user)
):
    """
    Analyse via GET (alternative à POST).
    """
    request = AnalysisRequest(
        symbol=symbol,
        mode=mode,
        confirm_cost=confirm_cost
    )
    return await run_council_analysis(request, current_user)


@router.get("/history")
async def get_analysis_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """
    Historique des analyses Council de l'utilisateur.
    """
    analyses = await db.council_analyses.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return {
        "analyses": analyses,
        "count": len(analyses)
    }


@router.get("/costs/summary")
async def get_user_costs_summary(current_user: dict = Depends(get_current_user)):
    """
    Résumé des coûts LLM de l'utilisateur.
    """
    pipeline = [
        {"$match": {"user_id": current_user["id"]}},
        {"$group": {
            "_id": None,
            "total_analyses": {"$sum": 1},
            "total_cost_usd": {"$sum": "$costs.total_cost_usd"}
        }}
    ]
    
    result = await db.council_analyses.aggregate(pipeline).to_list(1)
    
    if result:
        stats = result[0]
        return {
            "total_analyses": stats.get("total_analyses", 0),
            "total_cost_usd": round(stats.get("total_cost_usd", 0), 4),
            "total_cost_eur": round(stats.get("total_cost_usd", 0) * 0.92, 4),
            "average_cost_per_analysis": round(
                stats.get("total_cost_usd", 0) / max(stats.get("total_analyses", 1), 1), 4
            )
        }
    
    return {
        "total_analyses": 0,
        "total_cost_usd": 0,
        "total_cost_eur": 0,
        "average_cost_per_analysis": 0
    }


@router.get("/costs/daily")
async def get_daily_costs(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """
    Coûts quotidiens sur les X derniers jours.
    """
    from datetime import timedelta
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    pipeline = [
        {"$match": {
            "user_id": current_user["id"],
            "timestamp": {"$gte": start_date.isoformat()}
        }},
        {"$group": {
            "_id": {"$substr": ["$timestamp", 0, 10]},
            "analyses_count": {"$sum": 1},
            "cost_usd": {"$sum": "$costs.total_cost_usd"}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    result = await db.council_analyses.aggregate(pipeline).to_list(100)
    
    return {
        "period_days": days,
        "daily_costs": [
            {
                "date": r["_id"],
                "analyses": r["analyses_count"],
                "cost_usd": round(r["cost_usd"], 4)
            }
            for r in result
        ]
    }


# ============== WEBSOCKET POUR LOGS TEMPS RÉEL ==============

@router.websocket("/ws/{user_id}")
async def websocket_logs(websocket: WebSocket, user_id: str):
    """
    WebSocket pour recevoir les logs d'analyse en temps réel.
    """
    await websocket.accept()
    active_connections[user_id] = websocket
    
    try:
        # Envoyer un message de connexion
        await websocket.send_json({
            "type": "connected",
            "message": "Connecté au Bull Sage Council",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        while True:
            # Keep-alive et recevoir des commandes
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        if user_id in active_connections:
            del active_connections[user_id]


async def _broadcast_log(user_id: str, log: Dict):
    """Envoie un log au WebSocket de l'utilisateur"""
    if user_id in active_connections:
        try:
            await active_connections[user_id].send_json({
                "type": "agent_log",
                **log
            })
        except Exception as e:
            logger.error(f"WebSocket send error: {e}")


# ============== HELPERS ==============

async def _update_user_costs(user_id: str, cost_usd: float):
    """Met à jour les statistiques de coûts de l'utilisateur"""
    await db.users.update_one(
        {"id": user_id},
        {
            "$inc": {
                "council_total_cost_usd": cost_usd,
                "council_analyses_count": 1
            },
            "$set": {
                "council_last_analysis": datetime.now(timezone.utc).isoformat()
            }
        }
    )
