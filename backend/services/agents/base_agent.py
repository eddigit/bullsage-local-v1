"""
Base Agent - Classe abstraite pour tous les agents du Bull Sage Council
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseTradingAgent(ABC):
    """Classe de base pour tous les agents du conseil"""
    
    def __init__(self, config: Dict[str, Any]):
        self.id = config.get("id", "unknown")
        self.name = config.get("name", "Agent")
        self.emoji = config.get("emoji", "🤖")
        self.provider = config.get("provider", "unknown")
        self.api_key = config.get("api_key")
        self.model = config.get("model", "")
        self.base_url = config.get("base_url", "")
        self.role = config.get("role", "")
        self.prompt_focus = config.get("prompt_focus", "")
        self.cost = config.get("cost_per_request", 0)
        self.timeout = config.get("timeout", 30)
        self.color = config.get("color", "#6B7280")
    
    async def analyze(self, symbol: str, market_data: Dict[str, Any], log_callback=None) -> Dict[str, Any]:
        """Effectue l'analyse spécialisée"""
        start_time = datetime.utcnow()
        
        # Log début
        if log_callback:
            await log_callback(self.id, self.name, "analyzing", f"🔍 Analyse {symbol}...")
        
        try:
            prompt = self._build_prompt(symbol, market_data)
            response = await self._call_api(prompt)
            analysis = self._parse_response(response)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log succès
            if log_callback:
                signal = analysis.get("signal", "NEUTRAL")
                confidence = analysis.get("confidence", 0.5)
                await log_callback(
                    self.id, self.name, "completed",
                    f"✅ {signal} (confiance: {confidence:.0%}) - {execution_time:.1f}s"
                )
            
            return {
                "agent_id": self.id,
                "agent": self.name,
                "emoji": self.emoji,
                "provider": self.provider,
                "model": self.model,
                "role": self.role,
                "success": True,
                "execution_time": round(execution_time, 2),
                "cost": self.cost,
                "analysis": analysis
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Agent {self.name} error: {error_msg}")
            
            # Log erreur
            if log_callback:
                await log_callback(self.id, self.name, "error", f"❌ Erreur: {error_msg[:100]}")
            
            return {
                "agent_id": self.id,
                "agent": self.name,
                "emoji": self.emoji,
                "provider": self.provider,
                "role": self.role,
                "success": False,
                "error": error_msg,
                "cost": 0
            }
    
    def _build_prompt(self, symbol: str, market_data: Dict[str, Any]) -> str:
        """Construit le prompt pour l'agent"""
        # Formatter les données de marché de façon concise
        market_summary = self._format_market_data(market_data)
        
        return f"""Tu es un expert en {self.role} pour le trading crypto/forex.

=== SYMBOLE À ANALYSER ===
{symbol}

=== DONNÉES DE MARCHÉ ===
{market_summary}

=== TON EXPERTISE ===
{self.prompt_focus}

=== INSTRUCTIONS ===
1. Analyse selon ton expertise spécifique
2. Sois précis, factuel et actionnable
3. Donne un signal clair avec niveau de confiance

=== FORMAT DE RÉPONSE (JSON STRICT) ===
{{
    "signal": "BULLISH" | "BEARISH" | "NEUTRAL",
    "confidence": 0.0 à 1.0,
    "summary": "Résumé en 2-3 phrases maximum",
    "key_points": ["point1", "point2", "point3"],
    "risks": ["risque1", "risque2"],
    "price_targets": {{
        "support": number ou null,
        "resistance": number ou null,
        "stop_loss": number ou null,
        "take_profit": number ou null
    }},
    "timeframe": "court_terme" | "moyen_terme" | "long_terme"
}}

RÉPONDS UNIQUEMENT EN JSON VALIDE, SANS COMMENTAIRES."""
    
    def _format_market_data(self, data: Dict[str, Any]) -> str:
        """Formate les données de marché de façon lisible"""
        if not data:
            return "Données non disponibles"
        
        parts = []
        
        # Prix
        if "price" in data or "current_price" in data:
            price = data.get("price") or data.get("current_price")
            parts.append(f"Prix actuel: ${price:,.2f}" if isinstance(price, (int, float)) else f"Prix: {price}")
        
        # Variation 24h
        if "change_24h" in data or "price_change_24h" in data:
            change = data.get("change_24h") or data.get("price_change_24h", 0)
            parts.append(f"Variation 24h: {change:+.2f}%")
        
        # Volume
        if "volume_24h" in data:
            vol = data.get("volume_24h", 0)
            if vol > 1_000_000_000:
                parts.append(f"Volume 24h: ${vol/1_000_000_000:.2f}B")
            elif vol > 1_000_000:
                parts.append(f"Volume 24h: ${vol/1_000_000:.2f}M")
        
        # Market cap
        if "market_cap" in data:
            mc = data.get("market_cap", 0)
            if mc > 1_000_000_000:
                parts.append(f"Market Cap: ${mc/1_000_000_000:.2f}B")
        
        # Indicateurs techniques si présents
        if "indicators" in data:
            ind = data["indicators"]
            if "rsi" in ind:
                parts.append(f"RSI(14): {ind['rsi']:.1f}")
            if "macd" in ind:
                parts.append(f"MACD: {ind['macd']}")
        
        # High/Low
        if "high_24h" in data and "low_24h" in data:
            parts.append(f"Range 24h: ${data['low_24h']:,.2f} - ${data['high_24h']:,.2f}")
        
        return "\n".join(parts) if parts else json.dumps(data, indent=2, default=str)[:1500]
    
    @abstractmethod
    async def _call_api(self, prompt: str) -> str:
        """Appel API spécifique au provider - à implémenter"""
        pass
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse la réponse JSON de l'agent"""
        try:
            # Nettoyer la réponse
            cleaned = response.strip()
            
            # Retirer les marqueurs de code
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1]
            if "```" in cleaned:
                cleaned = cleaned.split("```")[0]
            
            cleaned = cleaned.strip()
            
            # Parser le JSON
            result = json.loads(cleaned)
            
            # Valider et normaliser
            return self._validate_analysis(result)
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error for {self.name}: {e}")
            # Fallback si parsing échoue
            return {
                "signal": "NEUTRAL",
                "confidence": 0.4,
                "summary": response[:300] if response else "Erreur de parsing",
                "key_points": [],
                "risks": ["Réponse non structurée"],
                "price_targets": {},
                "timeframe": "inconnu",
                "raw_response": response[:500]
            }
    
    def _validate_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valide et normalise l'analyse"""
        # Signal
        signal = str(data.get("signal", "NEUTRAL")).upper()
        if signal not in ["BULLISH", "BEARISH", "NEUTRAL"]:
            signal = "NEUTRAL"
        
        # Confidence
        confidence = data.get("confidence", 0.5)
        if isinstance(confidence, str):
            try:
                confidence = float(confidence.replace("%", "")) / 100 if "%" in confidence else float(confidence)
            except:
                confidence = 0.5
        confidence = max(0.0, min(1.0, float(confidence)))
        
        return {
            "signal": signal,
            "confidence": confidence,
            "summary": str(data.get("summary", ""))[:500],
            "key_points": data.get("key_points", [])[:5],
            "risks": data.get("risks", [])[:3],
            "price_targets": data.get("price_targets", {}),
            "timeframe": data.get("timeframe", "moyen_terme")
        }
