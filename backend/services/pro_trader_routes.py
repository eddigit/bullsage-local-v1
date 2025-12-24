"""
🧠 Routes API pour le Pro Trader AI
Endpoints pour les recommandations de trading professionnelles
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import logging

from services.pro_trader_ai import pro_trader

logger = logging.getLogger(__name__)

# Router
pro_trader_router = APIRouter(prefix="/api/pro", tags=["Pro Trader AI"])


class ScanRequest(BaseModel):
    symbols: Optional[List[str]] = None


# ==================== ENDPOINTS ====================

@pro_trader_router.get("/health")
async def pro_health():
    """Vérifie l'état du Pro Trader AI"""
    return {
        "status": "ready",
        "service": "Pro Trader AI",
        "version": "1.0",
        "features": [
            "Smart Money Analysis",
            "Multi-Timeframe Trend Detection",
            "Trade Quality Scoring (A+ to D)",
            "Automatic Entry/SL/TP Calculation",
            "Professional Action Plans"
        ]
    }


@pro_trader_router.get("/analyze/{symbol}")
async def analyze_symbol(symbol: str):
    """
    📊 Analyse complète d'un actif
    
    Retourne l'analyse détaillée avec tendances, RSI, phase du marché, etc.
    """
    result = await pro_trader.analyze_asset(symbol.upper())
    
    if "error" in result:
        raise HTTPException(400, result["error"])
    
    return result


@pro_trader_router.get("/recommendation/{symbol}")
async def get_recommendation(symbol: str):
    """
    🎯 Obtenir une recommandation de trade complète
    
    Comme un trader professionnel vous conseillerait:
    - Qualité du setup (A+ à D)
    - Direction (LONG/SHORT/WAIT)
    - Niveaux d'entrée, Stop Loss, Take Profits
    - Ratio Risque/Récompense
    - Plan d'action détaillé
    - Raisonnement complet
    """
    result = await pro_trader.get_trade_recommendation(symbol.upper())
    
    if "error" in result:
        raise HTTPException(400, result["error"])
    
    return result


@pro_trader_router.get("/scan")
async def scan_opportunities(symbols: str = "BTC,ETH,SOL,XRP,ADA,AVAX,DOT,LINK"):
    """
    🔍 Scanner le marché pour trouver les meilleures opportunités
    
    Analyse plusieurs actifs et retourne UNIQUEMENT les setups de qualité A+ et A.
    Ces sont les seuls trades que vous devriez prendre!
    
    Paramètre:
    - symbols: Liste de symboles séparés par des virgules
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    
    result = await pro_trader.scan_best_opportunities(symbol_list)
    
    return result


@pro_trader_router.post("/scan")
async def scan_opportunities_post(request: ScanRequest):
    """
    🔍 Scanner le marché (POST version)
    
    Body: { "symbols": ["BTC", "ETH", "SOL"] }
    """
    symbols = request.symbols or ["BTC", "ETH", "SOL", "XRP", "ADA", "AVAX", "DOT", "LINK"]
    
    result = await pro_trader.scan_best_opportunities(symbols)
    
    return result


@pro_trader_router.get("/quick/{symbol}")
async def quick_analysis(symbol: str):
    """
    ⚡ Analyse rapide - Dois-je trader maintenant?
    
    Réponse simple et directe pour savoir si vous devez agir.
    """
    result = await pro_trader.get_trade_recommendation(symbol.upper())
    
    if "error" in result:
        raise HTTPException(400, result["error"])
    
    quality = result["recommendation"]["quality"]
    direction = result["recommendation"]["direction"]
    confidence = result["recommendation"]["confidence"]
    urgency = result["recommendation"]["urgency"]
    
    # Générer réponse simple
    if quality in ["A+", "A"]:
        if urgency == "IMMEDIATE":
            action = f"🟢 OUI! {direction} maintenant"
            advice = "Setup excellent - Agissez!"
        else:
            action = f"🟡 BIENTÔT - Attendez pullback"
            advice = "Bon setup mais attendez meilleur prix"
    elif quality == "B":
        action = "🟠 PEUT-ÊTRE - Avec prudence"
        advice = "Setup correct mais pas optimal"
    else:
        action = "🔴 NON - Ne tradez pas"
        advice = "Conditions non favorables"
    
    return {
        "symbol": symbol.upper(),
        "action": action,
        "advice": advice,
        "quality": quality,
        "direction": direction,
        "confidence": confidence,
        "entry": result["levels"]["entry"],
        "stop_loss": result["levels"]["stop"],
        "take_profit": result["levels"]["tp1"],
        "risk_reward": result["levels"]["rr_ratio"]
    }


@pro_trader_router.get("/dashboard")
async def pro_dashboard():
    """
    📊 Dashboard Pro Trader
    
    Vue d'ensemble du marché avec les meilleures opportunités actuelles.
    """
    # Scanner les principales cryptos
    main_cryptos = ["BTC", "ETH", "SOL", "XRP", "ADA"]
    
    scan_result = await pro_trader.scan_best_opportunities(main_cryptos)
    
    # Analyses rapides
    market_overview = []
    for symbol in main_cryptos[:3]:  # Top 3 pour rapidité
        try:
            analysis = await pro_trader.analyze_asset(symbol)
            if "error" not in analysis:
                market_overview.append({
                    "symbol": symbol,
                    "price": analysis["current_price"],
                    "trend_1d": analysis["trends"]["1d"]["direction"],
                    "rsi_4h": round(analysis["rsi"]["4h"], 1),
                    "phase": analysis["market_phase"]
                })
        except:
            pass
    
    return {
        "timestamp": scan_result["timestamp"],
        "market_overview": market_overview,
        "best_opportunities": scan_result["best_setups"][:3],
        "total_opportunities": scan_result["opportunities_found"],
        "summary": scan_result["message"],
        "advice": "Concentrez-vous sur les setups A+ et A uniquement. La patience est la clé!"
    }


@pro_trader_router.get("/rules")
async def trading_rules():
    """
    📚 Règles de Trading du Pro Trader AI
    
    Les règles d'or pour trader comme un professionnel.
    """
    return {
        "title": "🧠 RÈGLES D'OR DU TRADING GAGNANT",
        "rules": [
            {
                "number": 1,
                "rule": "Ne tradez QUE les setups A+ et A",
                "explanation": "La qualité prime sur la quantité. Attendre le bon setup est la clé."
            },
            {
                "number": 2,
                "rule": "Risquez maximum 1-2% par trade",
                "explanation": "Même 10 pertes consécutives ne ruineront pas votre compte."
            },
            {
                "number": 3,
                "rule": "Ratio Risque/Récompense minimum 1:2",
                "explanation": "Vous pouvez vous tromper 50% du temps et rester rentable."
            },
            {
                "number": 4,
                "rule": "TOUJOURS placer un Stop Loss",
                "explanation": "Un trade sans SL est du gambling, pas du trading."
            },
            {
                "number": 5,
                "rule": "Respectez le plan - pas d'émotions",
                "explanation": "Entrez, placez SL/TP, et laissez le trade travailler."
            },
            {
                "number": 6,
                "rule": "Prenez des profits partiels",
                "explanation": "30% à TP1, 40% à TP2, 30% à TP3 - sécurisez vos gains."
            },
            {
                "number": 7,
                "rule": "Tradez AVEC la tendance",
                "explanation": "La tendance est votre amie. N'allez pas contre elle."
            },
            {
                "number": 8,
                "rule": "Attendez la confirmation multi-timeframe",
                "explanation": "1H + 4H + 1D alignés = trade haute probabilité."
            },
            {
                "number": 9,
                "rule": "Ne tradez pas par ennui ou revenge",
                "explanation": "Pas de setup = pas de trade. C'est aussi simple."
            },
            {
                "number": 10,
                "rule": "Tenez un journal de trading",
                "explanation": "Analysez vos trades pour vous améliorer constamment."
            }
        ],
        "reminder": "💡 Le trading gagnant = Patience + Discipline + Gestion du risque"
    }
