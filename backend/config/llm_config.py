"""
Bull Sage Council - Configuration LLM Centralisée
==================================================
7 agents spécialisés + orchestrateur Groq

RÈGLE ABSOLUE: MODE = on_demand (JAMAIS auto)
"""
import os
from typing import Dict, Any, List, Optional


class LLMConfig:
    """Configuration centralisée pour le Bull Sage Council"""
    
    # Mode de fonctionnement - JAMAIS "auto"
    MODE = os.getenv("LLM_MODE", "on_demand")
    
    # ============== ORCHESTRATEUR (Groq - GRATUIT et rapide) ==============
    ORCHESTRATOR = {
        "name": "orchestrator",
        "provider": "groq",
        "api_key": os.getenv("GROQ_API_KEY"),
        "model": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1",
        "role": "Synthèse finale et décision du Council",
        "cost_per_request": 0.0,
        "timeout": 30
    }
    
    # ============== 7 AGENTS SPÉCIALISÉS ==============
    AGENTS = {
        "groq_technical": {
            "name": "Technical Analyst",
            "emoji": "📊",
            "color": "#3B82F6",
            "provider": "groq",
            "api_key": os.getenv("GROQ_API_KEY"),
            "model": "llama-3.3-70b-versatile",
            "base_url": "https://api.groq.com/openai/v1",
            "role": "Analyse technique",
            "prompt_focus": "RSI, MACD, Bollinger, supports/résistances, patterns chartistes, volumes, divergences",
            "cost_per_request": 0.0,
            "priority": 1,
            "timeout": 20
        },
        "deepseek_quant": {
            "name": "Quant Analyst",
            "emoji": "🔢",
            "color": "#8B5CF6",
            "provider": "deepseek",
            "api_key": os.getenv("DEEPSEEK_API_KEY"),
            "model": "deepseek-chat",
            "base_url": "https://api.deepseek.com/v1",
            "role": "Analyse quantitative",
            "prompt_focus": "Probabilités, corrélations, volatilité, ratios risk/reward, modèles mathématiques, sharpe ratio",
            "cost_per_request": 0.001,
            "priority": 1,
            "timeout": 25
        },
        "openrouter_macro": {
            "name": "Macro Economist",
            "emoji": "🌍",
            "color": "#F59E0B",
            "provider": "openrouter",
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model": "mistralai/mixtral-8x7b-instruct",
            "base_url": "https://openrouter.ai/api/v1",
            "role": "Analyse macroéconomique",
            "prompt_focus": "Fed, taux d'intérêt, inflation, DXY, corrélation marchés traditionnels, géopolitique, cycles",
            "cost_per_request": 0.002,
            "priority": 2,
            "timeout": 25
        },
        "grok_sentiment": {
            "name": "Sentiment Analyst",
            "emoji": "🐦",
            "color": "#1DA1F2",
            "provider": "xai",
            "api_key": os.getenv("XAI_API_KEY"),
            "model": "grok-beta",
            "base_url": "https://api.x.ai/v1",
            "role": "Analyse sentiment",
            "prompt_focus": "Twitter/X, réseaux sociaux, tendances virales, sentiment retail vs institutionnel, fear & greed",
            "cost_per_request": 0.005,
            "priority": 2,
            "timeout": 20
        },
        "perplexity_news": {
            "name": "News Researcher",
            "emoji": "📰",
            "color": "#10B981",
            "provider": "perplexity",
            "api_key": os.getenv("PERPLEXITY_API_KEY"),
            "model": "sonar-pro",
            "base_url": "https://api.perplexity.ai",
            "role": "Recherche et actualités",
            "prompt_focus": "News récentes, régulations, annonces, partenariats, événements majeurs avec sources vérifiées",
            "cost_per_request": 0.005,
            "priority": 2,
            "timeout": 30
        },
        "claude_fundamental": {
            "name": "Fundamental Analyst",
            "emoji": "🔍",
            "color": "#EC4899",
            "provider": "anthropic",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "model": "claude-sonnet-4-20250514",
            "role": "Analyse fondamentale",
            "prompt_focus": "Tokenomics, équipe, roadmap, TVL, revenus, compétition, moat, adoption, métriques on-chain",
            "cost_per_request": 0.01,
            "priority": 3,
            "timeout": 30
        },
        "manus_strategy": {
            "name": "Strategy Advisor",
            "emoji": "🎯",
            "color": "#EF4444",
            "provider": "manus",
            "api_key": os.getenv("MANUS_API_KEY"),
            "model": "manus-1",
            "base_url": "https://manus.im/api/v1",
            "role": "Stratégie et plan d'action",
            "prompt_focus": "Plan de trading détaillé, scénarios bull/bear, gestion du risque, timing, position sizing",
            "cost_per_request": 0.01,
            "priority": 3,
            "timeout": 30
        }
    }
    
    # ============== MODES D'ANALYSE ==============
    ANALYSIS_MODES = {
        "quick": {
            "name": "⚡ Analyse Rapide",
            "description": "2 agents gratuits - Aperçu rapide en 15s",
            "agents": ["groq_technical", "deepseek_quant"],
            "estimated_cost": 0.001,
            "timeout": 15,
            "use_case": "Screening rapide, vérification de setup"
        },
        "standard": {
            "name": "📊 Analyse Standard",
            "description": "4 agents - Équilibre coût/qualité",
            "agents": ["groq_technical", "deepseek_quant", "grok_sentiment", "openrouter_macro"],
            "estimated_cost": 0.008,
            "timeout": 30,
            "use_case": "Décision de trade quotidienne"
        },
        "full": {
            "name": "🏆 Analyse Complète",
            "description": "7 agents - Conseil complet du Bull Sage",
            "agents": [
                "groq_technical", "deepseek_quant", "openrouter_macro",
                "grok_sentiment", "perplexity_news", "claude_fundamental", "manus_strategy"
            ],
            "estimated_cost": 0.033,
            "timeout": 60,
            "use_case": "Décision majeure, gros trade, analyse hebdomadaire"
        }
    }
    
    # ============== MÉTHODES UTILITAIRES ==============
    
    @classmethod
    def get_agent_config(cls, agent_name: str) -> Dict[str, Any]:
        """Récupère la config d'un agent"""
        return cls.AGENTS.get(agent_name)
    
    @classmethod
    def get_mode_config(cls, mode: str) -> Dict[str, Any]:
        """Récupère la config d'un mode"""
        return cls.ANALYSIS_MODES.get(mode, cls.ANALYSIS_MODES["standard"])
    
    @classmethod
    def get_active_agents(cls, mode: str) -> List[Dict[str, Any]]:
        """Retourne les agents actifs pour un mode"""
        mode_config = cls.get_mode_config(mode)
        return [cls.AGENTS[name] for name in mode_config["agents"] if name in cls.AGENTS]
    
    @classmethod
    def get_available_agents(cls) -> List[Dict[str, Any]]:
        """Retourne tous les agents avec leur statut de configuration"""
        agents = []
        for agent_id, config in cls.AGENTS.items():
            agents.append({
                "id": agent_id,
                "name": config["name"],
                "emoji": config.get("emoji", "🤖"),
                "provider": config["provider"],
                "role": config["role"],
                "cost": config["cost_per_request"],
                "configured": bool(config.get("api_key")),
                "priority": config.get("priority", 2)
            })
        return sorted(agents, key=lambda x: x["priority"])
    
    @classmethod
    def calculate_mode_cost(cls, mode: str) -> float:
        """Calcule le coût réel d'un mode basé sur les agents"""
        mode_config = cls.get_mode_config(mode)
        total = 0.0
        for agent_name in mode_config["agents"]:
            agent = cls.AGENTS.get(agent_name)
            if agent:
                total += agent.get("cost_per_request", 0)
        return round(total, 4)
    
    @classmethod
    def get_orchestrator_status(cls) -> Dict[str, Any]:
        """Statut de l'orchestrateur"""
        return {
            "provider": cls.ORCHESTRATOR["provider"],
            "model": cls.ORCHESTRATOR["model"],
            "configured": bool(cls.ORCHESTRATOR.get("api_key")),
            "cost": "GRATUIT"
        }
    
    # ============== BACKWARD COMPATIBILITY ==============
    # Pour les anciens imports
    PROVIDER = os.environ.get('LLM_PROVIDER', 'xai')
    XAI_API_KEY = os.environ.get('XAI_API_KEY')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
    
    @classmethod
    def get_active_config(cls) -> Dict[str, Any]:
        """Backward compatible - retourne config provider actif"""
        provider = cls.PROVIDER.lower()
        if provider == "anthropic":
            return {"provider": "anthropic", "api_key": cls.ANTHROPIC_API_KEY, "model": "claude-sonnet-4-20250514"}
        elif provider == "openrouter":
            return {"provider": "openrouter", "api_key": cls.OPENROUTER_API_KEY, "base_url": "https://openrouter.ai/api/v1"}
        return {"provider": "xai", "api_key": cls.XAI_API_KEY, "base_url": "https://api.x.ai/v1", "model": "grok-3-latest"}
    
    @classmethod
    def is_configured(cls) -> bool:
        """Vérifie si un provider est configuré"""
        return bool(cls.get_active_config().get("api_key"))


# Fonctions utilitaires backward compatible
def get_llm_api_key() -> Optional[str]:
    return LLMConfig.get_active_config().get("api_key")

def get_llm_model() -> str:
    return LLMConfig.get_active_config().get("model", "grok-3-latest")

def get_llm_base_url() -> Optional[str]:
    return LLMConfig.get_active_config().get("base_url")
