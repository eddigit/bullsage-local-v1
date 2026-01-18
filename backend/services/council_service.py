"""
Bull Sage Council - Service d'Analyse Multi-Agent Optimisé
============================================================
Utilise la nouvelle architecture modulaire avec agents/.

RÈGLE CRITIQUE: Chaque analyse = 1 action utilisateur explicite
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
import json
import sys
import os

# Ajouter le chemin parent pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.llm_config import LLMConfig
from services.agents import create_agent, OpenAICompatibleAgent

logger = logging.getLogger(__name__)


@dataclass
class CostTracker:
    """Suivi des coûts d'une session d'analyse"""
    session_id: str
    started_at: str
    agents_cost: Dict[str, float] = field(default_factory=dict)
    total_cost_usd: float = 0.0
    
    def add_agent_cost(self, agent_id: str, cost: float):
        """Ajoute le coût d'un agent"""
        self.agents_cost[agent_id] = cost
        self.total_cost_usd += cost
        return cost
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "agents_cost": self.agents_cost,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_cost_eur": round(self.total_cost_usd * 0.92, 6)
        }


class BullSageCouncil:
    """
    Orchestrateur du conseil de 7 IA pour l'analyse trading.
    
    ⚠️ RÈGLE ABSOLUE: Ce service ne s'exécute JAMAIS automatiquement.
    Chaque appel = 1 action utilisateur explicite = 1 facturation.
    """
    
    def __init__(self, on_log: Callable = None):
        self.config = LLMConfig
        self._agents_cache = {}
        self.on_log = on_log  # Callback pour logs temps réel
        
        # Créer l'orchestrateur
        self.orchestrator = OpenAICompatibleAgent({
            **LLMConfig.ORCHESTRATOR,
            "id": "orchestrator"
        })
    
    async def _emit_log(self, agent_id: str, agent_name: str, status: str, message: str):
        """Émet un log vers le callback si défini"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "agent_name": agent_name,
            "status": status,
            "message": message
        }
        logger.info(f"[{agent_name}] {status}: {message}")
        
        if self.on_log:
            try:
                if asyncio.iscoroutinefunction(self.on_log):
                    await self.on_log(log_entry)
                else:
                    self.on_log(log_entry)
            except Exception as e:
                logger.error(f"Log callback error: {e}")
    
    def _get_agent(self, agent_name: str):
        """Récupère ou crée un agent avec cache"""
        if agent_name not in self._agents_cache:
            config = self.config.get_agent_config(agent_name)
            if config:
                config["id"] = agent_name  # Ajouter l'ID
                self._agents_cache[agent_name] = create_agent(config)
        return self._agents_cache.get(agent_name)
    
    def get_cost_estimate(self, mode: str = "standard") -> Dict[str, Any]:
        """
        Retourne l'estimation de coût AVANT l'analyse.
        À afficher à l'utilisateur pour confirmation.
        """
        mode_config = self.config.get_mode_config(mode)
        agents_info = []
        total_cost = 0.0
        
        for agent_name in mode_config["agents"]:
            agent_config = self.config.get_agent_config(agent_name)
            if agent_config:
                cost = agent_config.get("cost_per_request", 0)
                agents_info.append({
                    "id": agent_name,
                    "name": agent_config["name"],
                    "emoji": agent_config.get("emoji", "🤖"),
                    "role": agent_config["role"],
                    "provider": agent_config["provider"],
                    "cost": cost,
                    "configured": bool(agent_config.get("api_key"))
                })
                total_cost += cost
        
        return {
            "mode": mode,
            "mode_name": mode_config["name"],
            "description": mode_config["description"],
            "use_case": mode_config.get("use_case", ""),
            "agents_count": len(agents_info),
            "agents": agents_info,
            "estimated_cost_usd": round(total_cost, 4),
            "estimated_time_seconds": mode_config.get("timeout", 30),
            "orchestrator": self.config.get_orchestrator_status()
        }
    
    def list_modes(self) -> Dict[str, Any]:
        """Liste tous les modes disponibles avec leurs détails"""
        modes = {}
        for mode_name in self.config.ANALYSIS_MODES.keys():
            modes[mode_name] = self.get_cost_estimate(mode_name)
        return {
            "available_modes": modes,
            "default_mode": "standard",
            "note": "Chaque analyse est facturée. Choisissez le mode adapté."
        }
    
    async def analyze(
        self,
        symbol: str,
        mode: str = "standard",
        market_data: Optional[Dict[str, Any]] = None,
        log_callback: Callable = None
    ) -> Dict[str, Any]:
        """
        Lance l'analyse du conseil.
        
        ⚠️ APPELÉ UNIQUEMENT sur action utilisateur explicite.
        """
        start_time = datetime.utcnow()
        session_id = f"council_{start_time.strftime('%Y%m%d_%H%M%S')}"
        mode_config = self.config.get_mode_config(mode)
        
        # Utiliser le callback passé ou celui de l'instance
        callback = log_callback or self.on_log
        
        # Tracker de coûts
        cost_tracker = CostTracker(
            session_id=session_id,
            started_at=start_time.isoformat()
        )
        
        # Préparer les données de marché
        if market_data is None:
            market_data = await self._fetch_market_data(symbol)
        
        # Log démarrage
        await self._emit_log(
            "council", "🏛️ Bull Sage Council", "starting",
            f"Analyse {symbol} en mode {mode_config['name']} avec {len(mode_config['agents'])} agents..."
        )
        
        # Récupérer les agents pour ce mode
        agents = []
        for agent_name in mode_config["agents"]:
            agent = self._get_agent(agent_name)
            if agent:
                agents.append((agent_name, agent))
            else:
                logger.warning(f"Agent {agent_name} non disponible")
        
        # Fonction wrapper pour le callback de log
        async def agent_log_callback(agent_id, agent_name, status, message):
            await self._emit_log(agent_id, agent_name, status, message)
        
        # Exécuter toutes les analyses en parallèle
        tasks = [
            agent.analyze(symbol, market_data, agent_log_callback) 
            for _, agent in agents
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Traiter les résultats
        analyses = []
        errors = []
        
        for i, result in enumerate(results):
            agent_name = agents[i][0]
            if isinstance(result, Exception):
                errors.append({
                    "agent": agent_name,
                    "error": str(result)
                })
            elif isinstance(result, dict):
                if result.get("success"):
                    analyses.append(result)
                    cost_tracker.add_agent_cost(agent_name, result.get("cost", 0))
                else:
                    errors.append({
                        "agent": agent_name,
                        "error": result.get("error", "Unknown error")
                    })
        
        # Synthèse par l'orchestrateur
        await self._emit_log(
            "orchestrator", "🎯 Orchestrateur", "analyzing",
            f"Synthèse de {len(analyses)} analyses..."
        )
        
        synthesis = await self._orchestrate(symbol, analyses, market_data)
        
        # Calculer le consensus
        consensus = self._calculate_consensus(analyses)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Log final
        final_verdict = synthesis.get("recommendation", "HOLD")
        await self._emit_log(
            "council", "🏛️ Bull Sage Council", "completed",
            f"✅ Analyse terminée: {final_verdict} en {execution_time:.1f}s"
        )
        
        return {
            "session_id": session_id,
            "symbol": symbol,
            "mode": mode,
            "mode_name": mode_config["name"],
            "timestamp": datetime.utcnow().isoformat(),
            "execution_time_seconds": round(execution_time, 2),
            "cost": {
                **cost_tracker.to_dict(),
                "estimated_usd": mode_config["estimated_cost"]
            },
            "agents": {
                "requested": len(agents),
                "responded": len(analyses),
                "failed": len(errors),
                "errors": errors if errors else None
            },
            "individual_analyses": analyses,
            "consensus": consensus,
            "synthesis": synthesis,
            "recommendation": {
                "action": synthesis.get("recommendation", "HOLD"),
                "confidence": synthesis.get("confidence", 0.5),
                "summary": synthesis.get("summary", ""),
                "key_levels": synthesis.get("key_levels", {}),
                "action_plan": synthesis.get("action_plan", [])
            }
        }
    
    async def _orchestrate(
        self,
        symbol: str,
        analyses: List[Dict[str, Any]],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """L'orchestrateur Groq synthétise toutes les analyses"""
        
        if not analyses:
            return {
                "recommendation": "HOLD",
                "confidence": 0.3,
                "summary": "Aucune analyse disponible",
                "error": "No analyses received"
            }
        
        # Formater les analyses pour le prompt
        analyses_text = ""
        for a in analyses:
            analysis = a.get("analysis", {})
            analyses_text += f"""
### {a.get('emoji', '🤖')} {a['agent']} ({a['role']})
- Signal: {analysis.get('signal', 'N/A')}
- Confiance: {analysis.get('confidence', 0):.0%}
- Résumé: {analysis.get('summary', 'N/A')}
- Points clés: {', '.join(analysis.get('key_points', [])[:3])}
"""
        
        # Données marché simplifiées
        price = market_data.get("price") or market_data.get("current_price", 0)
        change = market_data.get("change_24h") or market_data.get("price_change_24h", 0)
        
        prompt = f"""Tu es l'orchestrateur du Bull Sage Council - ton rôle est de synthétiser {len(analyses)} analyses d'experts.

=== SYMBOLE ===
{symbol}

=== ANALYSES DES EXPERTS ===
{analyses_text}

=== DONNÉES MARCHÉ ===
Prix: ${price:,.2f}
Variation 24h: {change:+.2f}%

=== TA MISSION ===
Synthétise les analyses et donne une recommandation ACTIONNABLE.

=== FORMAT JSON STRICT ===
{{
    "recommendation": "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL",
    "confidence": 0.0 à 1.0,
    "summary": "Synthèse en 3 phrases max",
    "convergence_points": ["Les experts s'accordent sur..."],
    "divergence_points": ["Les experts divergent sur..."],
    "key_levels": {{
        "entry": number ou null,
        "stop_loss": number ou null,
        "take_profit_1": number ou null,
        "take_profit_2": number ou null
    }},
    "risk_reward_ratio": number,
    "recommended_position_size": "petit" | "moyen" | "grand",
    "timeframe": "court_terme" | "moyen_terme" | "long_terme",
    "action_plan": [
        "Étape 1: ...",
        "Étape 2: ...",
        "Étape 3: ..."
    ]
}}"""
        
        try:
            # Créer un prompt simplifié pour l'orchestrateur
            response = await self.orchestrator._call_api(prompt)
            result = self.orchestrator._parse_response(response)
            
            # Normaliser la réponse
            return {
                "recommendation": result.get("recommendation", "HOLD"),
                "confidence": result.get("confidence", 0.5),
                "summary": result.get("summary", ""),
                "convergence_points": result.get("convergence_points", []),
                "divergence_points": result.get("divergence_points", []),
                "key_levels": result.get("key_levels", {}),
                "risk_reward_ratio": result.get("risk_reward_ratio"),
                "recommended_position_size": result.get("recommended_position_size", "petit"),
                "timeframe": result.get("timeframe", "moyen_terme"),
                "action_plan": result.get("action_plan", [])
            }
            
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            return {
                "recommendation": "HOLD",
                "confidence": 0.3,
                "summary": f"Erreur de synthèse: {str(e)}",
                "error": str(e)
            }
    
    def _calculate_consensus(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcule le niveau de consensus entre les agents"""
        if not analyses:
            return {"level": "none", "percentage": 0}
        
        signals = []
        confidences = []
        
        for a in analyses:
            analysis = a.get("analysis", {})
            signal = analysis.get("signal", "NEUTRAL")
            confidence = analysis.get("confidence", 0.5)
            
            # Normaliser confidence si c'est un pourcentage
            if isinstance(confidence, (int, float)) and confidence > 1:
                confidence = confidence / 100
            
            signals.append(signal)
            confidences.append(float(confidence))
        
        # Compter les signaux
        total = len(signals)
        bullish = signals.count("BULLISH")
        bearish = signals.count("BEARISH")
        neutral = signals.count("NEUTRAL")
        
        # Déterminer le consensus majoritaire
        majority_signal = max(
            [("BULLISH", bullish), ("BEARISH", bearish), ("NEUTRAL", neutral)],
            key=lambda x: x[1]
        )[0]
        
        majority_pct = max(bullish, bearish, neutral) / total * 100
        
        # Niveau de consensus
        if majority_pct >= 80:
            level = "strong"
        elif majority_pct >= 60:
            level = "moderate"
        else:
            level = "weak"
        
        return {
            "level": level,
            "majority_signal": majority_signal,
            "percentage": round(majority_pct, 1),
            "distribution": {
                "bullish": round(bullish / total * 100, 1),
                "bearish": round(bearish / total * 100, 1),
                "neutral": round(neutral / total * 100, 1)
            },
            "votes": {
                "bullish": bullish,
                "bearish": bearish,
                "neutral": neutral,
                "total": total
            },
            "average_confidence": round(sum(confidences) / len(confidences), 2),
            "unanimous": len(set(signals)) == 1
        }
    
    async def _fetch_market_data(self, symbol: str) -> Dict[str, Any]:
        """Récupère les données de marché basiques"""
        # Import ici pour éviter les imports circulaires
        try:
            from services.market_data import MarketDataService
            service = MarketDataService()
            data = await service.get_asset_data(symbol)
            if data:
                return data
        except Exception as e:
            logger.warning(f"Could not fetch market data: {e}")
        
        # Fallback avec données minimales
        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Données de marché limitées"
        }


# ============== FONCTIONS UTILITAIRES ==============

def get_available_agents() -> List[Dict]:
    """Retourne la liste des agents disponibles"""
    return LLMConfig.get_available_agents()

def get_available_modes() -> Dict:
    """Retourne les modes d'analyse disponibles"""
    council = BullSageCouncil()
    return council.list_modes()


# Singleton pour l'application
council = BullSageCouncil()
