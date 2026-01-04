"""
Multi-AI Consensus System for Trading Signals
Utilise plusieurs modèles d'IA pour obtenir un consensus sur les signaux de trading.
Modèles utilisés: Grok (xAI), Claude (Anthropic), GPT-4/Gemini (OpenRouter)
"""

import asyncio
import httpx
import json
import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration des modèles disponibles
AI_MODELS = {
    "grok-3": {
        "name": "Grok-3",
        "provider": "xai",
        "model": "grok-3-latest",
        "weight": 1.0,
        "specialty": "Analyse temps réel et sentiment crypto"
    },
    "claude-sonnet": {
        "name": "Claude 3.5 Sonnet",
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20241022",
        "weight": 1.2,  # Poids plus élevé car excellent en analyse
        "specialty": "Analyse fondamentale et raisonnement"
    },
    "gpt-4o": {
        "name": "GPT-4o",
        "provider": "openrouter",
        "model": "openai/gpt-4o",
        "weight": 1.0,
        "specialty": "Analyse technique et patterns"
    },
    "gemini-pro": {
        "name": "Gemini 2.0 Flash",
        "provider": "openrouter",
        "model": "google/gemini-2.0-flash-001",
        "weight": 0.9,
        "specialty": "Analyse rapide multi-marchés"
    }
}

class MultiAIConsensus:
    """
    Système de consensus multi-IA pour des signaux de trading plus fiables.
    Plusieurs modèles analysent les mêmes données et votent ensemble.
    """
    
    def __init__(self, xai_api_key: str, openrouter_api_key: str = None, anthropic_api_key: str = None):
        self.xai_api_key = xai_api_key
        self.openrouter_api_key = openrouter_api_key
        self.anthropic_api_key = anthropic_api_key
        self.timeout = 60.0
        
    async def _call_xai(self, model: str, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Appel à l'API xAI (Grok)"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.xai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "")
                else:
                    logger.error(f"xAI API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calling xAI ({model}): {e}")
            return None

    async def _call_anthropic(self, model: str, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Appel à l'API Anthropic (Claude)"""
        if not self.anthropic_api_key:
            return None
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "max_tokens": 2000,
                        "system": system_prompt,
                        "messages": [
                            {"role": "user", "content": user_prompt}
                        ]
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Claude retourne le contenu dans content[0].text
                    content = data.get("content", [])
                    if content and len(content) > 0:
                        return content[0].get("text", "")
                    return ""
                else:
                    logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calling Anthropic ({model}): {e}")
            return None
    
    async def _call_openrouter(self, model: str, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Appel à OpenRouter pour accéder à GPT-4, Gemini, etc."""
        if not self.openrouter_api_key:
            return None
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://bullsage.app",
                        "X-Title": "Bull Sage Trading"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "")
                else:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calling OpenRouter ({model}): {e}")
            return None

    def _parse_signals_json(self, text: str) -> Optional[Dict]:
        """Parse le JSON des signaux avec gestion robuste des erreurs"""
        if not text:
            return None
            
        # Nettoyer le texte
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace("'", "'").replace("'", "'")
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Chercher le JSON
        json_match = re.search(r'\{[\s\S]*\}', text)
        if not json_match:
            return None
            
        json_str = json_match.group()
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Tentative avec comptage des accolades
            try:
                brace_count = 0
                start_idx = None
                end_idx = None
                for i, char in enumerate(text):
                    if char == '{':
                        if start_idx is None:
                            start_idx = i
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0 and start_idx is not None:
                            end_idx = i + 1
                            break
                
                if start_idx is not None and end_idx is not None:
                    clean_json = text[start_idx:end_idx]
                    clean_json = re.sub(r',\s*([}\]])', r'\1', clean_json)
                    return json.loads(clean_json)
            except Exception:
                pass
        
        return None

    async def get_consensus_signals(self, market_data: Dict, user_id: str) -> Dict:
        """
        Obtient des signaux de trading via consensus de plusieurs IA.
        Chaque IA analyse les données et vote, puis on fusionne les résultats.
        """
        
        system_prompt = """Tu es un trader professionnel expert avec 20 ans d'expérience.
Tu analyses les marchés et donnes des signaux de trading PRÉCIS et ACTIONNABLES.
Tu dois être CONSERVATEUR - ne recommande que les trades à haute probabilité.
Réponds UNIQUEMENT avec un JSON valide, pas de texte avant ou après."""

        user_prompt = self._build_analysis_prompt(market_data)
        
        # Lancer les appels en parallèle
        tasks = []
        model_names = []
        model_weights = []
        
        # Grok-3 (xAI)
        if self.xai_api_key:
            tasks.append(self._call_xai("grok-3-latest", system_prompt, user_prompt))
            model_names.append("grok-3")
            model_weights.append(1.0)
            logger.info("📡 Querying Grok-3...")
        
        # Claude 3.5 Sonnet (Anthropic)
        if self.anthropic_api_key:
            tasks.append(self._call_anthropic("claude-3-5-sonnet-20241022", system_prompt, user_prompt))
            model_names.append("claude-sonnet")
            model_weights.append(1.2)
            logger.info("📡 Querying Claude 3.5 Sonnet...")
        
        # GPT-4o via OpenRouter
        if self.openrouter_api_key:
            tasks.append(self._call_openrouter("openai/gpt-4o", system_prompt, user_prompt))
            model_names.append("gpt-4o")
            model_weights.append(1.0)
            logger.info("📡 Querying GPT-4o...")
            
            # Gemini via OpenRouter
            tasks.append(self._call_openrouter("google/gemini-2.0-flash-001", system_prompt, user_prompt))
            model_names.append("gemini-flash")
            model_weights.append(0.9)
            logger.info("📡 Querying Gemini 2.0 Flash...")
        
        if not tasks:
            logger.error("No AI models available!")
            return {
                "generated_at": datetime.utcnow().isoformat(),
                "market_sentiment": "neutral",
                "signals": [],
                "warning": "Aucune API d'IA configurée.",
                "consensus_info": {"models_queried": 0, "models_responded": 0}
            }
        
        # Exécuter en parallèle
        logger.info(f"🤖 Querying {len(tasks)} AI models for consensus...")
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Parser les réponses
        parsed_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"❌ Model {model_names[i]} failed: {response}")
                continue
            if response:
                parsed = self._parse_signals_json(response)
                if parsed:
                    parsed["_model"] = model_names[i]
                    parsed["_weight"] = model_weights[i]
                    parsed_responses.append(parsed)
                    logger.info(f"✅ Model {model_names[i]} returned {len(parsed.get('signals', []))} signals")
                else:
                    logger.warning(f"⚠️ Model {model_names[i]} returned unparseable response")
        
        if not parsed_responses:
            logger.warning("No valid responses from any AI model")
            return {
                "generated_at": datetime.utcnow().isoformat(),
                "market_sentiment": "neutral",
                "signals": [],
                "warning": "Aucune IA n'a pu générer de signaux. Réessayez.",
                "consensus_info": {"models_queried": len(tasks), "models_responded": 0}
            }
        
        # Fusionner les résultats par consensus
        consensus = self._build_consensus(parsed_responses, market_data)
        
        # Ajouter les infos sur les modèles utilisés
        consensus["models_used"] = [
            {"name": model_names[i], "responded": not isinstance(responses[i], Exception) and responses[i] is not None}
            for i in range(len(model_names))
        ]
        
        return consensus

    def _build_analysis_prompt(self, market_data: Dict) -> str:
        """Construit le prompt d'analyse à partir des données de marché"""
        
        fg = market_data.get("fear_greed", {"value": 50, "label": "Neutral"})
        
        crypto_lines = []
        for c in market_data.get("crypto", [])[:5]:
            try:
                crypto_lines.append(f"- {c.get('name', 'Unknown')} ({c.get('symbol', '?')}): ${c.get('price', 0):,.2f} ({c.get('change_24h', 0):+.1f}%)")
            except:
                pass
                
        forex_lines = []
        for f in market_data.get("forex", []):
            try:
                forex_lines.append(f"- {f.get('name', '')} ({f.get('symbol', '')}): {f.get('price', 0):.4f} ({f.get('change_24h', 0):+.2f}%)")
            except:
                pass
                
        indices_lines = []
        for i in market_data.get("indices", []):
            try:
                indices_lines.append(f"- {i.get('name', '')} ({i.get('symbol', '')}): {i.get('price', 0):,.0f} ({i.get('change_24h', 0):+.2f}%)")
            except:
                pass
                
        stocks_lines = []
        for s in market_data.get("stocks", []):
            try:
                stocks_lines.append(f"- {s.get('name', '')} ({s.get('symbol', '')}): ${s.get('price', 0):.2f} ({s.get('change_24h', 0):+.2f}%)")
            except:
                pass
        
        return f"""ANALYSE MULTI-MARCHÉS - {datetime.now().strftime('%d/%m/%Y %H:%M')}

DONNÉES MARCHÉ:
- Fear & Greed Index: {fg.get('value', 50)} ({fg.get('label', 'Neutral')})

CRYPTO (Top 5):
{chr(10).join(crypto_lines) if crypto_lines else "- Données non disponibles"}

FOREX:
{chr(10).join(forex_lines) if forex_lines else "- Données non disponibles"}

INDICES:
{chr(10).join(indices_lines) if indices_lines else "- Données non disponibles"}

ACTIONS:
{chr(10).join(stocks_lines) if stocks_lines else "- Données non disponibles"}

GÉNÈRE 3-5 SIGNAUX DE TRADING. Format JSON strict:
{{
  "market_sentiment": "bullish|bearish|neutral",
  "signals": [
    {{
      "asset": "BTC",
      "asset_name": "Bitcoin",
      "market_type": "crypto",
      "direction": "ACHAT|VENTE",
      "confidence": 75,
      "duration": "4-8h",
      "entry_price": 98500,
      "take_profit": 3.5,
      "stop_loss": 1.5,
      "reason": "Raison concise du trade"
    }}
  ],
  "warning": "Message de prudence optionnel"
}}"""

    def _build_consensus(self, responses: List[Dict], market_data: Dict) -> Dict:
        """
        Fusionne les réponses de plusieurs IA pour créer un consensus.
        Les signaux qui apparaissent dans plusieurs réponses ont plus de poids.
        """
        
        # Compteur de votes pondérés pour le sentiment
        sentiment_votes = {"bullish": 0.0, "bearish": 0.0, "neutral": 0.0}
        
        # Agrégation des signaux par asset
        signal_votes = {}  # asset -> list of signals from different models
        
        for resp in responses:
            weight = resp.get("_weight", 1.0)
            
            # Voter pour le sentiment
            sentiment = resp.get("market_sentiment", "neutral").lower()
            if sentiment in sentiment_votes:
                sentiment_votes[sentiment] += weight
            
            # Agréger les signaux
            for signal in resp.get("signals", []):
                asset = signal.get("asset", "").upper()
                if not asset:
                    continue
                    
                if asset not in signal_votes:
                    signal_votes[asset] = []
                signal_votes[asset].append({
                    **signal,
                    "_model": resp.get("_model", "unknown"),
                    "_weight": weight
                })
        
        # Déterminer le sentiment consensus
        consensus_sentiment = max(sentiment_votes, key=sentiment_votes.get)
        
        # Construire les signaux finaux
        final_signals = []
        
        for asset, votes in signal_votes.items():
            if len(votes) == 0:
                continue
                
            # Compter les votes pondérés par direction
            buy_weight = sum(v.get("_weight", 1.0) for v in votes if v.get("direction", "").upper() in ["ACHAT", "BUY", "LONG"])
            sell_weight = sum(v.get("_weight", 1.0) for v in votes if v.get("direction", "").upper() in ["VENTE", "SELL", "SHORT"])
            
            # Calculer la confiance moyenne pondérée
            total_weight = sum(v.get("_weight", 1.0) for v in votes)
            avg_confidence = sum(v.get("confidence", 70) * v.get("_weight", 1.0) for v in votes) / total_weight if total_weight > 0 else 70
            
            # Prendre le signal majoritaire
            if buy_weight > sell_weight:
                direction = "ACHAT"
                relevant_votes = [v for v in votes if v.get("direction", "").upper() in ["ACHAT", "BUY", "LONG"]]
            elif sell_weight > buy_weight:
                direction = "VENTE"
                relevant_votes = [v for v in votes if v.get("direction", "").upper() in ["VENTE", "SELL", "SHORT"]]
            else:
                direction = votes[0].get("direction", "ACHAT")
                relevant_votes = votes
            
            if not relevant_votes:
                relevant_votes = votes
                
            # Prendre les valeurs du modèle avec le plus de poids
            relevant_votes.sort(key=lambda x: x.get("_weight", 1.0), reverse=True)
            base_signal = relevant_votes[0]
            
            # Boost de confiance si plusieurs modèles sont d'accord
            agreement_count = len(relevant_votes)
            total_models = len(responses)
            agreement_rate = agreement_count / total_models if total_models > 0 else 0
            
            # Boost proportionnel au taux d'accord
            consensus_boost = min(15, int(agreement_rate * 20))
            final_confidence = min(95, avg_confidence + consensus_boost)
            
            # Construire le signal final
            final_signal = {
                "asset": asset,
                "asset_name": base_signal.get("asset_name", asset),
                "market_type": base_signal.get("market_type", "crypto"),
                "direction": direction,
                "confidence": round(final_confidence),
                "duration": base_signal.get("duration", "4-8h"),
                "entry_price": base_signal.get("entry_price"),
                "take_profit": base_signal.get("take_profit", 3.0),
                "stop_loss": base_signal.get("stop_loss", 1.5),
                "reason": base_signal.get("reason", "Signal de trading"),
                "consensus": {
                    "models_agreed": agreement_count,
                    "total_models": total_models,
                    "agreement_rate": round(agreement_rate * 100)
                }
            }
            
            final_signals.append(final_signal)
        
        # Trier par confiance décroissante
        final_signals.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        # Limiter à 5 signaux max
        final_signals = final_signals[:5]
        
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "market_sentiment": consensus_sentiment,
            "signals": final_signals,
            "fear_greed": market_data.get("fear_greed", {"value": 50, "label": "Neutral"}),
            "consensus_info": {
                "models_queried": len(responses),
                "models_responded": len(responses),
                "sentiment_votes": {k: round(v, 2) for k, v in sentiment_votes.items()},
                "method": "multi-ai-weighted-consensus"
            },
            "markets_analyzed": market_data.get("markets_analyzed", {
                "crypto": len(market_data.get("crypto", [])),
                "forex": len(market_data.get("forex", [])),
                "indices": len(market_data.get("indices", [])),
                "stocks": len(market_data.get("stocks", []))
            })
        }
