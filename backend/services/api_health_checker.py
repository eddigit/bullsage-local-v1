"""
API Health Checker Service
Vérifie le statut de toutes les API externes et sources de données.
Permet d'identifier rapidement les services en panne.
"""

import asyncio
import httpx
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)

class APIStatus(Enum):
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    DOWN = "down"
    STANDBY = "standby"  # API non configurée ou sans crédits
    UNKNOWN = "unknown"

class APIHealthChecker:
    """
    Service de vérification de santé des API.
    Vérifie toutes les API externes utilisées par Bull Sage.
    """
    
    def __init__(self):
        self.timeout = 10.0
        self.last_check = None
        self.cached_results = None
        self.cache_duration = 60  # Cache pendant 60 secondes
        
    async def check_all(self, force_refresh: bool = False) -> Dict:
        """
        Vérifie toutes les API et retourne leur statut.
        Utilise un cache pour éviter trop de requêtes.
        """
        now = datetime.now(timezone.utc)
        
        # Utiliser le cache si disponible et récent
        if not force_refresh and self.cached_results and self.last_check:
            elapsed = (now - self.last_check).total_seconds()
            if elapsed < self.cache_duration:
                return self.cached_results
        
        # Lancer toutes les vérifications en parallèle
        results = await asyncio.gather(
            self._check_xai(),
            self._check_anthropic(),
            self._check_openrouter(),
            self._check_coingecko(),
            self._check_cryptocompare(),
            self._check_alphavantage(),
            self._check_fear_greed(),
            self._check_mongodb(),
            return_exceptions=True
        )
        
        api_statuses = {
            "ai_models": {
                "xai_grok": results[0] if not isinstance(results[0], Exception) else self._error_status("xAI Grok", results[0]),
                "anthropic_claude": results[1] if not isinstance(results[1], Exception) else self._error_status("Anthropic Claude", results[1]),
                "openrouter": results[2] if not isinstance(results[2], Exception) else self._error_status("OpenRouter", results[2]),
            },
            "market_data": {
                "coingecko": results[3] if not isinstance(results[3], Exception) else self._error_status("CoinGecko", results[3]),
                "cryptocompare": results[4] if not isinstance(results[4], Exception) else self._error_status("CryptoCompare", results[4]),
                "alphavantage": results[5] if not isinstance(results[5], Exception) else self._error_status("Alpha Vantage", results[5]),
                "fear_greed": results[6] if not isinstance(results[6], Exception) else self._error_status("Fear & Greed Index", results[6]),
            },
            "database": {
                "mongodb": results[7] if not isinstance(results[7], Exception) else self._error_status("MongoDB", results[7]),
            },
            "checked_at": now.isoformat(),
            "summary": self._build_summary(results)
        }
        
        self.cached_results = api_statuses
        self.last_check = now
        
        return api_statuses
    
    def _error_status(self, name: str, error: Exception) -> Dict:
        """Crée un statut d'erreur pour une API"""
        return {
            "name": name,
            "status": APIStatus.DOWN.value,
            "message": str(error),
            "response_time_ms": None
        }
    
    def _build_summary(self, results: List) -> Dict:
        """Construit un résumé des statuts"""
        operational = 0
        degraded = 0
        down = 0
        standby = 0
        
        for r in results:
            if isinstance(r, Exception):
                down += 1
            elif isinstance(r, dict):
                status = r.get("status", "unknown")
                if status == APIStatus.OPERATIONAL.value:
                    operational += 1
                elif status == APIStatus.DEGRADED.value:
                    degraded += 1
                elif status == APIStatus.DOWN.value:
                    down += 1
                elif status == APIStatus.STANDBY.value:
                    standby += 1
        
        total = len(results)
        health_score = round((operational / total) * 100) if total > 0 else 0
        
        return {
            "total_apis": total,
            "operational": operational,
            "degraded": degraded,
            "down": down,
            "standby": standby,
            "health_score": health_score,
            "overall_status": self._get_overall_status(operational, degraded, down, total)
        }
    
    def _get_overall_status(self, operational: int, degraded: int, down: int, total: int) -> str:
        """Détermine le statut global du système"""
        if operational == total:
            return "healthy"
        elif operational >= total * 0.7:
            return "degraded"
        elif operational >= total * 0.3:
            return "critical"
        else:
            return "down"

    async def _check_xai(self) -> Dict:
        """Vérifie l'API xAI (Grok)"""
        api_key = os.environ.get('XAI_API_KEY')
        
        if not api_key:
            return {
                "name": "xAI Grok",
                "status": APIStatus.STANDBY.value,
                "message": "Clé API non configurée",
                "response_time_ms": None
            }
        
        try:
            start = datetime.now()
            async with httpx.AsyncClient() as client:
                # Test avec un prompt minimal
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-3-mini-latest",
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 5
                    },
                    timeout=self.timeout
                )
                elapsed = (datetime.now() - start).total_seconds() * 1000
                
                if response.status_code == 200:
                    return {
                        "name": "xAI Grok",
                        "status": APIStatus.OPERATIONAL.value,
                        "message": "Opérationnel",
                        "response_time_ms": round(elapsed)
                    }
                elif response.status_code == 403:
                    error_data = response.json()
                    return {
                        "name": "xAI Grok",
                        "status": APIStatus.STANDBY.value,
                        "message": "Crédits insuffisants - Achetez des crédits sur console.x.ai",
                        "response_time_ms": round(elapsed)
                    }
                else:
                    return {
                        "name": "xAI Grok",
                        "status": APIStatus.DOWN.value,
                        "message": f"Erreur {response.status_code}",
                        "response_time_ms": round(elapsed)
                    }
        except Exception as e:
            return {
                "name": "xAI Grok",
                "status": APIStatus.DOWN.value,
                "message": str(e),
                "response_time_ms": None
            }

    async def _check_anthropic(self) -> Dict:
        """Vérifie l'API Anthropic (Claude)"""
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        
        if not api_key:
            return {
                "name": "Anthropic Claude",
                "status": APIStatus.STANDBY.value,
                "message": "Clé API non configurée",
                "response_time_ms": None
            }
        
        try:
            start = datetime.now()
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": 5,
                        "messages": [{"role": "user", "content": "ping"}]
                    },
                    timeout=self.timeout
                )
                elapsed = (datetime.now() - start).total_seconds() * 1000
                
                if response.status_code == 200:
                    return {
                        "name": "Anthropic Claude",
                        "status": APIStatus.OPERATIONAL.value,
                        "message": "Opérationnel",
                        "response_time_ms": round(elapsed)
                    }
                elif response.status_code == 400:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "")
                    if "credit" in error_msg.lower():
                        return {
                            "name": "Anthropic Claude",
                            "status": APIStatus.STANDBY.value,
                            "message": "Crédits insuffisants - Rechargez sur console.anthropic.com",
                            "response_time_ms": round(elapsed)
                        }
                    return {
                        "name": "Anthropic Claude",
                        "status": APIStatus.DOWN.value,
                        "message": error_msg,
                        "response_time_ms": round(elapsed)
                    }
                else:
                    return {
                        "name": "Anthropic Claude",
                        "status": APIStatus.DOWN.value,
                        "message": f"Erreur {response.status_code}",
                        "response_time_ms": round(elapsed)
                    }
        except Exception as e:
            return {
                "name": "Anthropic Claude",
                "status": APIStatus.DOWN.value,
                "message": str(e),
                "response_time_ms": None
            }

    async def _check_openrouter(self) -> Dict:
        """Vérifie l'API OpenRouter"""
        api_key = os.environ.get('OPENROUTER_API_KEY')
        
        if not api_key:
            return {
                "name": "OpenRouter",
                "status": APIStatus.STANDBY.value,
                "message": "Clé API non configurée",
                "response_time_ms": None
            }
        
        try:
            start = datetime.now()
            async with httpx.AsyncClient() as client:
                # Utiliser un modèle gratuit pour le test
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "google/gemini-2.0-flash-001",
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 5
                    },
                    timeout=self.timeout
                )
                elapsed = (datetime.now() - start).total_seconds() * 1000
                
                if response.status_code == 200:
                    return {
                        "name": "OpenRouter",
                        "status": APIStatus.OPERATIONAL.value,
                        "message": "Opérationnel (GPT-4o, Gemini, Claude)",
                        "response_time_ms": round(elapsed)
                    }
                elif response.status_code == 402:
                    return {
                        "name": "OpenRouter",
                        "status": APIStatus.STANDBY.value,
                        "message": "Crédits insuffisants",
                        "response_time_ms": round(elapsed)
                    }
                else:
                    return {
                        "name": "OpenRouter",
                        "status": APIStatus.DOWN.value,
                        "message": f"Erreur {response.status_code}",
                        "response_time_ms": round(elapsed)
                    }
        except Exception as e:
            return {
                "name": "OpenRouter",
                "status": APIStatus.DOWN.value,
                "message": str(e),
                "response_time_ms": None
            }

    async def _check_coingecko(self) -> Dict:
        """Vérifie l'API CoinGecko"""
        try:
            start = datetime.now()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.coingecko.com/api/v3/ping",
                    timeout=self.timeout
                )
                elapsed = (datetime.now() - start).total_seconds() * 1000
                
                if response.status_code == 200:
                    return {
                        "name": "CoinGecko",
                        "status": APIStatus.OPERATIONAL.value,
                        "message": "Opérationnel - Données crypto",
                        "response_time_ms": round(elapsed)
                    }
                elif response.status_code == 429:
                    return {
                        "name": "CoinGecko",
                        "status": APIStatus.DEGRADED.value,
                        "message": "Rate limit atteint",
                        "response_time_ms": round(elapsed)
                    }
                else:
                    return {
                        "name": "CoinGecko",
                        "status": APIStatus.DOWN.value,
                        "message": f"Erreur {response.status_code}",
                        "response_time_ms": round(elapsed)
                    }
        except Exception as e:
            return {
                "name": "CoinGecko",
                "status": APIStatus.DOWN.value,
                "message": str(e),
                "response_time_ms": None
            }

    async def _check_cryptocompare(self) -> Dict:
        """Vérifie l'API CryptoCompare"""
        try:
            start = datetime.now()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD",
                    timeout=self.timeout
                )
                elapsed = (datetime.now() - start).total_seconds() * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    if "USD" in data:
                        return {
                            "name": "CryptoCompare",
                            "status": APIStatus.OPERATIONAL.value,
                            "message": "Opérationnel - Prix crypto temps réel",
                            "response_time_ms": round(elapsed)
                        }
                return {
                    "name": "CryptoCompare",
                    "status": APIStatus.DOWN.value,
                    "message": f"Réponse invalide",
                    "response_time_ms": round(elapsed)
                }
        except Exception as e:
            return {
                "name": "CryptoCompare",
                "status": APIStatus.DOWN.value,
                "message": str(e),
                "response_time_ms": None
            }

    async def _check_alphavantage(self) -> Dict:
        """Vérifie l'API Alpha Vantage"""
        api_key = os.environ.get('ALPHA_VANTAGE_API_KEY', 'RY2XZ59CW2ZETVQ2')
        
        try:
            start = datetime.now()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={api_key}",
                    timeout=self.timeout
                )
                elapsed = (datetime.now() - start).total_seconds() * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    if "Note" in data:  # Rate limit message
                        return {
                            "name": "Alpha Vantage",
                            "status": APIStatus.DEGRADED.value,
                            "message": "Rate limit atteint (5 req/min)",
                            "response_time_ms": round(elapsed)
                        }
                    if "Global Quote" in data or "Realtime Currency Exchange Rate" in data:
                        return {
                            "name": "Alpha Vantage",
                            "status": APIStatus.OPERATIONAL.value,
                            "message": "Opérationnel - Données forex/actions",
                            "response_time_ms": round(elapsed)
                        }
                return {
                    "name": "Alpha Vantage",
                    "status": APIStatus.DEGRADED.value,
                    "message": "Réponse partielle",
                    "response_time_ms": round(elapsed)
                }
        except Exception as e:
            return {
                "name": "Alpha Vantage",
                "status": APIStatus.DOWN.value,
                "message": str(e),
                "response_time_ms": None
            }

    async def _check_fear_greed(self) -> Dict:
        """Vérifie l'API Fear & Greed Index"""
        try:
            start = datetime.now()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.alternative.me/fng/?limit=1",
                    timeout=self.timeout
                )
                elapsed = (datetime.now() - start).total_seconds() * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data:
                        return {
                            "name": "Fear & Greed Index",
                            "status": APIStatus.OPERATIONAL.value,
                            "message": "Opérationnel - Sentiment marché",
                            "response_time_ms": round(elapsed)
                        }
                return {
                    "name": "Fear & Greed Index",
                    "status": APIStatus.DOWN.value,
                    "message": "Réponse invalide",
                    "response_time_ms": round(elapsed)
                }
        except Exception as e:
            return {
                "name": "Fear & Greed Index",
                "status": APIStatus.DOWN.value,
                "message": str(e),
                "response_time_ms": None
            }

    async def _check_mongodb(self) -> Dict:
        """Vérifie la connexion MongoDB"""
        mongo_uri = os.environ.get('MONGODB_URI')
        
        if not mongo_uri:
            return {
                "name": "MongoDB",
                "status": APIStatus.STANDBY.value,
                "message": "URI non configurée",
                "response_time_ms": None
            }
        
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            start = datetime.now()
            
            client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
            await client.admin.command('ping')
            elapsed = (datetime.now() - start).total_seconds() * 1000
            client.close()
            
            return {
                "name": "MongoDB",
                "status": APIStatus.OPERATIONAL.value,
                "message": "Opérationnel - Base de données",
                "response_time_ms": round(elapsed)
            }
        except Exception as e:
            return {
                "name": "MongoDB",
                "status": APIStatus.DOWN.value,
                "message": str(e),
                "response_time_ms": None
            }


# Instance globale
api_health_checker = APIHealthChecker()
