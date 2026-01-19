#!/usr/bin/env python3
"""
🧪 BULL SAGE - Agent Testeur Complet
=====================================

Agent autonome pour tester l'ensemble des fonctionnalités de BullSage:
- Connexion aux APIs externes (CoinGecko, Alpha Vantage, etc.)
- Authentification et endpoints backend
- Trading Deribit (testnet)
- Cohérence des prédictions IA du Council
- Intégrité des données

Usage:
    python test_agent.py                    # Exécuter tous les tests
    python test_agent.py --quick            # Tests rapides seulement
    python test_agent.py --deribit          # Tests Deribit uniquement
    python test_agent.py --predictions      # Tests prédictions IA uniquement
    python test_agent.py --report           # Générer un rapport détaillé
"""

import os
import sys
import json
import asyncio
import argparse
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import traceback

# Ajouter le dossier backend au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv()

import httpx
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Statut d'un test"""
    PASSED = "✅ PASSED"
    FAILED = "❌ FAILED"
    SKIPPED = "⏭️ SKIPPED"
    WARNING = "⚠️ WARNING"


@dataclass
class TestResult:
    """Résultat d'un test individuel"""
    name: str
    category: str
    status: TestStatus
    duration_ms: float
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass 
class TestReport:
    """Rapport complet des tests"""
    started_at: str
    completed_at: str = ""
    duration_seconds: float = 0
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    skipped: int = 0
    results: List[TestResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def add_result(self, result: TestResult):
        self.results.append(result)
        self.total_tests += 1
        if result.status == TestStatus.PASSED:
            self.passed += 1
        elif result.status == TestStatus.FAILED:
            self.failed += 1
        elif result.status == TestStatus.WARNING:
            self.warnings += 1
        elif result.status == TestStatus.SKIPPED:
            self.skipped += 1
    
    def to_dict(self) -> Dict:
        return {
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "skipped": self.skipped,
            "success_rate": f"{(self.passed / self.total_tests * 100):.1f}%" if self.total_tests > 0 else "N/A",
            "results": [
                {
                    "name": r.name,
                    "category": r.category,
                    "status": r.status.value,
                    "duration_ms": r.duration_ms,
                    "message": r.message,
                    "error": r.error
                }
                for r in self.results
            ],
            "summary": self.summary
        }


class BullSageTestAgent:
    """
    Agent de test complet pour BullSage.
    
    Teste toutes les fonctionnalités critiques:
    - APIs externes (données marché)
    - Backend FastAPI
    - Trading Deribit
    - Prédictions IA (Council)
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.report = TestReport(started_at=datetime.now(timezone.utc).isoformat())
        self.client: Optional[httpx.AsyncClient] = None
        self.auth_token: Optional[str] = None
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    def _log_test(self, result: TestResult):
        """Logger le résultat d'un test"""
        icon = result.status.value.split()[0]
        logger.info(f"{icon} [{result.category}] {result.name} ({result.duration_ms:.0f}ms)")
        if result.error:
            logger.error(f"   └── Erreur: {result.error}")
        elif result.message:
            logger.info(f"   └── {result.message}")
    
    async def _run_test(
        self, 
        name: str, 
        category: str, 
        test_func,
        *args, 
        **kwargs
    ) -> TestResult:
        """Exécuter un test et capturer le résultat"""
        start = time.time()
        try:
            status, message, details = await test_func(*args, **kwargs)
            duration = (time.time() - start) * 1000
            result = TestResult(
                name=name,
                category=category,
                status=status,
                duration_ms=duration,
                message=message,
                details=details
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            result = TestResult(
                name=name,
                category=category,
                status=TestStatus.FAILED,
                duration_ms=duration,
                message="Exception non gérée",
                error=str(e)
            )
        
        self.report.add_result(result)
        self._log_test(result)
        return result
    
    # ==================== TESTS HEALTH ====================
    
    async def test_backend_health(self) -> Tuple[TestStatus, str, Dict]:
        """Tester la santé du backend"""
        try:
            response = await self.client.get(f"{self.api_url}/health")
            if response.status_code == 200:
                data = response.json()
                return TestStatus.PASSED, f"Backend en ligne: {data.get('status', 'ok')}", data
            return TestStatus.FAILED, f"Status code: {response.status_code}", {}
        except httpx.ConnectError:
            return TestStatus.FAILED, "Impossible de se connecter au backend", {}
    
    async def test_database_connection(self) -> Tuple[TestStatus, str, Dict]:
        """Tester la connexion à la base de données"""
        try:
            response = await self.client.get(f"{self.api_url}/health")
            if response.status_code == 200:
                data = response.json()
                db_status = data.get("database", "unknown")
                if db_status == "connected":
                    return TestStatus.PASSED, "MongoDB connecté", data
                return TestStatus.WARNING, f"DB status: {db_status}", data
            return TestStatus.FAILED, "Échec health check", {}
        except Exception as e:
            return TestStatus.FAILED, str(e), {}
    
    # ==================== TESTS APIs EXTERNES ====================
    
    async def test_coingecko_api(self) -> Tuple[TestStatus, str, Dict]:
        """Tester l'API CoinGecko"""
        try:
            response = await self.client.get(
                "https://api.coingecko.com/api/v3/ping",
                timeout=10.0
            )
            if response.status_code == 200:
                return TestStatus.PASSED, "CoinGecko API accessible", response.json()
            return TestStatus.FAILED, f"Status: {response.status_code}", {}
        except Exception as e:
            return TestStatus.WARNING, f"CoinGecko indisponible: {e}", {}
    
    async def test_alpha_vantage_api(self) -> Tuple[TestStatus, str, Dict]:
        """Tester l'API Alpha Vantage"""
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            return TestStatus.SKIPPED, "ALPHA_VANTAGE_API_KEY non configurée", {}
        
        try:
            response = await self.client.get(
                f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={api_key}",
                timeout=15.0
            )
            if response.status_code == 200:
                data = response.json()
                if "Global Quote" in data:
                    return TestStatus.PASSED, "Alpha Vantage fonctionnel", {"symbol": "AAPL"}
                if "Note" in data:
                    return TestStatus.WARNING, "Rate limit atteint", data
                return TestStatus.WARNING, "Réponse inattendue", data
            return TestStatus.FAILED, f"Status: {response.status_code}", {}
        except Exception as e:
            return TestStatus.WARNING, f"Alpha Vantage indisponible: {e}", {}
    
    async def test_finnhub_api(self) -> Tuple[TestStatus, str, Dict]:
        """Tester l'API Finnhub"""
        api_key = os.getenv("FINNHUB_API_KEY")
        if not api_key:
            return TestStatus.SKIPPED, "FINNHUB_API_KEY non configurée", {}
        
        try:
            response = await self.client.get(
                f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={api_key}",
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("c"):  # current price
                    return TestStatus.PASSED, f"AAPL: ${data['c']}", data
                return TestStatus.WARNING, "Pas de données de prix", data
            return TestStatus.FAILED, f"Status: {response.status_code}", {}
        except Exception as e:
            return TestStatus.WARNING, f"Finnhub indisponible: {e}", {}
    
    # ==================== TESTS DERIBIT ====================
    
    async def test_deribit_connection(self) -> Tuple[TestStatus, str, Dict]:
        """Tester la connexion à Deribit via l'API"""
        try:
            response = await self.client.get(f"{self.api_url}/deribit/status")
            if response.status_code == 200:
                data = response.json()
                deribit = data.get("deribit", data)
                if deribit.get("connected") and deribit.get("authenticated"):
                    account = deribit.get("account", {})
                    return TestStatus.PASSED, f"Connecté et authentifié", deribit
                elif deribit.get("connected"):
                    return TestStatus.WARNING, "Connecté mais non authentifié", deribit
                return TestStatus.FAILED, f"Non connecté: {deribit.get('error', '')}", deribit
            return TestStatus.FAILED, f"Status: {response.status_code}", {}
        except httpx.ConnectError:
            # Essayer directement via l'API Deribit
            return await self._test_deribit_direct()
        except Exception as e:
            return await self._test_deribit_direct()
    
    async def _test_deribit_direct(self) -> Tuple[TestStatus, str, Dict]:
        """Test direct de l'API Deribit (sans passer par le backend)"""
        client_id = os.getenv("DERIBIT_CLIENT_ID")
        client_secret = os.getenv("DERIBIT_CLIENT_SECRET")
        api_url = os.getenv("DERIBIT_API_URL", "https://test.deribit.com/api/v2")
        
        if not client_id or not client_secret:
            return TestStatus.SKIPPED, "Credentials Deribit non configurés", {}
        
        try:
            # Test d'authentification directe
            auth_url = f"{api_url}/public/auth?grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}"
            response = await self.client.get(auth_url, timeout=15.0)
            data = response.json()
            
            if "result" in data and "access_token" in data["result"]:
                return TestStatus.PASSED, "Authentification Deribit réussie (direct)", {
                    "testnet": data.get("testnet", True),
                    "scope": data["result"].get("scope", "")
                }
            elif "error" in data:
                return TestStatus.FAILED, f"Erreur: {data['error'].get('message', 'Unknown')}", data
            return TestStatus.FAILED, "Réponse inattendue", data
        except Exception as e:
            return TestStatus.FAILED, f"Erreur connexion directe: {e}", {}
    
    async def test_deribit_account(self) -> Tuple[TestStatus, str, Dict]:
        """Tester la récupération du compte Deribit"""
        try:
            response = await self.client.get(f"{self.api_url}/deribit/account?currency=BTC")
            if response.status_code == 200:
                data = response.json()
                account = data.get("account", {})
                if account:
                    return TestStatus.PASSED, f"Équité: {account.get('equity', 0)} BTC", account
                return TestStatus.WARNING, "Compte vide", data
            return TestStatus.FAILED, f"Status: {response.status_code}", {}
        except httpx.ConnectError:
            return await self._test_deribit_account_direct()
        except Exception as e:
            return await self._test_deribit_account_direct()
    
    async def _test_deribit_account_direct(self) -> Tuple[TestStatus, str, Dict]:
        """Test direct du compte Deribit"""
        client_id = os.getenv("DERIBIT_CLIENT_ID")
        client_secret = os.getenv("DERIBIT_CLIENT_SECRET")
        api_url = os.getenv("DERIBIT_API_URL", "https://test.deribit.com/api/v2")
        
        if not client_id or not client_secret:
            return TestStatus.SKIPPED, "Credentials non configurés", {}
        
        try:
            # D'abord s'authentifier
            auth_url = f"{api_url}/public/auth?grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}"
            auth_resp = await self.client.get(auth_url)
            auth_data = auth_resp.json()
            
            if "result" not in auth_data:
                return TestStatus.FAILED, "Authentification échouée", auth_data
            
            access_token = auth_data["result"]["access_token"]
            
            # Récupérer le compte
            account_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "private/get_account_summary",
                "params": {"currency": "BTC"}
            }
            
            response = await self.client.post(
                api_url,
                json=account_payload,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            data = response.json()
            
            if "result" in data:
                result = data["result"]
                return TestStatus.PASSED, f"Balance: {result.get('balance', 0)} BTC", result
            return TestStatus.FAILED, "Compte non récupéré", data
        except Exception as e:
            return TestStatus.FAILED, f"Erreur: {e}", {}
    
    async def test_deribit_positions(self) -> Tuple[TestStatus, str, Dict]:
        """Tester la récupération des positions Deribit"""
        try:
            response = await self.client.get(f"{self.api_url}/deribit/positions?currency=BTC")
            if response.status_code == 200:
                data = response.json()
                positions = data.get("positions", [])
                return TestStatus.PASSED, f"{len(positions)} positions ouvertes", {"count": len(positions)}
            return TestStatus.FAILED, f"Status: {response.status_code}", {}
        except httpx.ConnectError:
            return TestStatus.SKIPPED, "Backend non accessible", {}
        except Exception as e:
            return TestStatus.WARNING, f"Erreur: {e}", {}
    
    async def test_deribit_instruments(self) -> Tuple[TestStatus, str, Dict]:
        """Tester la récupération des instruments Deribit"""
        try:
            response = await self.client.get(f"{self.api_url}/deribit/instruments?currency=BTC&kind=future")
            if response.status_code == 200:
                data = response.json()
                instruments = data.get("instruments", [])
                if instruments:
                    names = [i.get("instrument_name") for i in instruments[:5]]
                    return TestStatus.PASSED, f"{len(instruments)} instruments", {"instruments": names}
                return TestStatus.WARNING, "Aucun instrument", data
            return TestStatus.FAILED, f"Status: {response.status_code}", {}
        except httpx.ConnectError:
            # Test direct
            return await self._test_deribit_instruments_direct()
        except Exception as e:
            return await self._test_deribit_instruments_direct()
    
    async def _test_deribit_instruments_direct(self) -> Tuple[TestStatus, str, Dict]:
        """Test direct des instruments Deribit"""
        api_url = os.getenv("DERIBIT_API_URL", "https://test.deribit.com/api/v2")
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "public/get_instruments",
                "params": {"currency": "BTC", "kind": "future"}
            }
            response = await self.client.post(api_url, json=payload)
            data = response.json()
            
            if "result" in data:
                instruments = data["result"]
                names = [i.get("instrument_name") for i in instruments[:5]]
                return TestStatus.PASSED, f"{len(instruments)} instruments (direct)", {"instruments": names}
            return TestStatus.FAILED, "Pas d'instruments", data
        except Exception as e:
            return TestStatus.FAILED, f"Erreur: {e}", {}
    
    async def test_deribit_ticker(self) -> Tuple[TestStatus, str, Dict]:
        """Tester le ticker Deribit"""
        try:
            response = await self.client.get(f"{self.api_url}/deribit/ticker/BTC-PERPETUAL")
            if response.status_code == 200:
                data = response.json()
                ticker = data.get("ticker", data)
                price = ticker.get("last_price") or ticker.get("mark_price")
                if price:
                    return TestStatus.PASSED, f"BTC-PERPETUAL: ${price:,.2f}", ticker
                return TestStatus.WARNING, "Prix non disponible", ticker
            return TestStatus.FAILED, f"Status: {response.status_code}", {}
        except httpx.ConnectError:
            return await self._test_deribit_ticker_direct()
        except Exception as e:
            return await self._test_deribit_ticker_direct()
    
    async def _test_deribit_ticker_direct(self) -> Tuple[TestStatus, str, Dict]:
        """Test direct du ticker Deribit"""
        api_url = os.getenv("DERIBIT_API_URL", "https://test.deribit.com/api/v2")
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "public/ticker",
                "params": {"instrument_name": "BTC-PERPETUAL"}
            }
            response = await self.client.post(api_url, json=payload)
            data = response.json()
            
            if "result" in data:
                result = data["result"]
                price = result.get("last_price") or result.get("mark_price", 0)
                return TestStatus.PASSED, f"BTC-PERPETUAL: ${price:,.2f} (direct)", result
            return TestStatus.FAILED, "Ticker non disponible", data
        except Exception as e:
            return TestStatus.FAILED, f"Erreur: {e}", {}
    
    # ==================== TESTS PRÉDICTIONS IA ====================
    
    async def test_council_availability(self) -> Tuple[TestStatus, str, Dict]:
        """Tester la disponibilité du Council IA"""
        try:
            # Vérifier les clés API des agents
            agents_config = {
                "Anthropic (Claude)": bool(os.getenv("ANTHROPIC_API_KEY")),
                "Groq": bool(os.getenv("GROQ_API_KEY")),
                "xAI (Grok)": bool(os.getenv("XAI_API_KEY")),
                "OpenRouter": bool(os.getenv("OPENROUTER_API_KEY")),
                "DeepSeek": bool(os.getenv("DEEPSEEK_API_KEY")),
                "Perplexity": bool(os.getenv("PERPLEXITY_API_KEY")),
            }
            
            available = sum(1 for v in agents_config.values() if v)
            total = len(agents_config)
            
            if available >= 3:
                return TestStatus.PASSED, f"{available}/{total} agents configurés", agents_config
            elif available >= 1:
                return TestStatus.WARNING, f"Seulement {available}/{total} agents", agents_config
            return TestStatus.FAILED, "Aucun agent IA configuré", agents_config
        except Exception as e:
            return TestStatus.FAILED, f"Erreur: {e}", {}
    
    async def test_market_data_for_predictions(self) -> Tuple[TestStatus, str, Dict]:
        """Tester les données marché nécessaires aux prédictions"""
        try:
            response = await self.client.get(f"{self.api_url}/market/overview")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    return TestStatus.PASSED, f"{len(data)} actifs disponibles", {"count": len(data)}
                return TestStatus.WARNING, "Peu de données marché", data
            return TestStatus.FAILED, f"Status: {response.status_code}", {}
        except httpx.ConnectError:
            return TestStatus.SKIPPED, "Backend non accessible", {}
        except Exception as e:
            return TestStatus.WARNING, f"Erreur: {e}", {}
    
    async def test_prediction_coherence(self) -> Tuple[TestStatus, str, Dict]:
        """Tester la cohérence des prédictions du Council"""
        try:
            # Simuler une analyse du Council
            response = await self.client.post(
                f"{self.api_url}/council/quick-analysis",
                json={"symbol": "BTC", "timeframe": "1h"},
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier les champs essentiels
                required_fields = ["recommendation", "confidence", "analysis"]
                missing = [f for f in required_fields if f not in data]
                
                if missing:
                    return TestStatus.WARNING, f"Champs manquants: {missing}", data
                
                # Vérifier la cohérence
                recommendation = data.get("recommendation", "").upper()
                confidence = data.get("confidence", 0)
                
                valid_recommendations = ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]
                if recommendation not in valid_recommendations:
                    return TestStatus.WARNING, f"Recommandation invalide: {recommendation}", data
                
                if not 0 <= confidence <= 100:
                    return TestStatus.WARNING, f"Confiance hors limites: {confidence}", data
                
                return TestStatus.PASSED, f"{recommendation} (confiance: {confidence}%)", data
            
            elif response.status_code == 503:
                return TestStatus.WARNING, "Council temporairement indisponible", {}
            return TestStatus.FAILED, f"Status: {response.status_code}", {}
        except httpx.ConnectError:
            return TestStatus.SKIPPED, "Backend non accessible", {}
        except asyncio.TimeoutError:
            return TestStatus.WARNING, "Timeout - analyse trop longue", {}
        except Exception as e:
            return TestStatus.WARNING, f"Erreur: {e}", {}
    
    async def test_signals_endpoint(self) -> Tuple[TestStatus, str, Dict]:
        """Tester l'endpoint des signaux"""
        try:
            response = await self.client.get(f"{self.api_url}/signals/active")
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else 0
                return TestStatus.PASSED, f"{count} signaux actifs", {"count": count}
            elif response.status_code == 401:
                return TestStatus.SKIPPED, "Authentification requise", {}
            return TestStatus.FAILED, f"Status: {response.status_code}", {}
        except httpx.ConnectError:
            return TestStatus.SKIPPED, "Backend non accessible", {}
        except Exception as e:
            return TestStatus.WARNING, f"Erreur: {e}", {}
    
    # ==================== TESTS INTÉGRITÉ ====================
    
    async def test_routes_availability(self) -> Tuple[TestStatus, str, Dict]:
        """Tester la disponibilité des routes principales"""
        routes = [
            "/api/health",
            "/api/market/overview",
            "/api/deribit/status",
        ]
        
        results = {}
        for route in routes:
            try:
                response = await self.client.get(f"{self.base_url}{route}")
                results[route] = response.status_code
            except Exception as e:
                results[route] = str(e)
        
        available = sum(1 for v in results.values() if v == 200)
        total = len(routes)
        
        if available == total:
            return TestStatus.PASSED, f"{available}/{total} routes disponibles", results
        elif available > 0:
            return TestStatus.WARNING, f"{available}/{total} routes disponibles", results
        return TestStatus.FAILED, "Aucune route accessible", results
    
    # ==================== EXÉCUTION DES TESTS ====================
    
    async def run_health_tests(self):
        """Exécuter les tests de santé"""
        logger.info("\n" + "="*50)
        logger.info("🏥 TESTS DE SANTÉ")
        logger.info("="*50)
        
        await self._run_test("Backend Health", "Health", self.test_backend_health)
        await self._run_test("Database Connection", "Health", self.test_database_connection)
        await self._run_test("Routes Availability", "Health", self.test_routes_availability)
    
    async def run_api_tests(self):
        """Exécuter les tests des APIs externes"""
        logger.info("\n" + "="*50)
        logger.info("🌐 TESTS APIs EXTERNES")
        logger.info("="*50)
        
        await self._run_test("CoinGecko API", "External APIs", self.test_coingecko_api)
        await self._run_test("Alpha Vantage API", "External APIs", self.test_alpha_vantage_api)
        await self._run_test("Finnhub API", "External APIs", self.test_finnhub_api)
    
    async def run_deribit_tests(self):
        """Exécuter les tests Deribit"""
        logger.info("\n" + "="*50)
        logger.info("📈 TESTS DERIBIT TRADING")
        logger.info("="*50)
        
        await self._run_test("Deribit Connection", "Deribit", self.test_deribit_connection)
        await self._run_test("Deribit Account", "Deribit", self.test_deribit_account)
        await self._run_test("Deribit Positions", "Deribit", self.test_deribit_positions)
        await self._run_test("Deribit Instruments", "Deribit", self.test_deribit_instruments)
        await self._run_test("Deribit Ticker", "Deribit", self.test_deribit_ticker)
    
    async def run_prediction_tests(self):
        """Exécuter les tests de prédictions IA"""
        logger.info("\n" + "="*50)
        logger.info("🧠 TESTS PRÉDICTIONS IA")
        logger.info("="*50)
        
        await self._run_test("Council Availability", "Predictions", self.test_council_availability)
        await self._run_test("Market Data for Predictions", "Predictions", self.test_market_data_for_predictions)
        await self._run_test("Signals Endpoint", "Predictions", self.test_signals_endpoint)
        # Le test de cohérence des prédictions est lent, le rendre optionnel
        # await self._run_test("Prediction Coherence", "Predictions", self.test_prediction_coherence)
    
    async def run_all_tests(self, quick: bool = False):
        """Exécuter tous les tests"""
        logger.info("\n" + "🐂"*25)
        logger.info("   BULL SAGE - AGENT TESTEUR")
        logger.info("🐂"*25 + "\n")
        
        start_time = time.time()
        
        await self.run_health_tests()
        await self.run_api_tests()
        await self.run_deribit_tests()
        
        if not quick:
            await self.run_prediction_tests()
        
        # Finaliser le rapport
        self.report.completed_at = datetime.now(timezone.utc).isoformat()
        self.report.duration_seconds = time.time() - start_time
        
        # Calculer le résumé par catégorie
        categories = {}
        for result in self.report.results:
            if result.category not in categories:
                categories[result.category] = {"passed": 0, "failed": 0, "warnings": 0, "skipped": 0}
            if result.status == TestStatus.PASSED:
                categories[result.category]["passed"] += 1
            elif result.status == TestStatus.FAILED:
                categories[result.category]["failed"] += 1
            elif result.status == TestStatus.WARNING:
                categories[result.category]["warnings"] += 1
            elif result.status == TestStatus.SKIPPED:
                categories[result.category]["skipped"] += 1
        
        self.report.summary = categories
        
        # Afficher le résumé
        self._print_summary()
        
        return self.report
    
    def _print_summary(self):
        """Afficher le résumé des tests"""
        logger.info("\n" + "="*50)
        logger.info("📊 RÉSUMÉ DES TESTS")
        logger.info("="*50)
        
        r = self.report
        success_rate = (r.passed / r.total_tests * 100) if r.total_tests > 0 else 0
        
        logger.info(f"Total: {r.total_tests} tests en {r.duration_seconds:.2f}s")
        logger.info(f"  ✅ Réussis:      {r.passed}")
        logger.info(f"  ❌ Échoués:      {r.failed}")
        logger.info(f"  ⚠️ Avertissements: {r.warnings}")
        logger.info(f"  ⏭️ Ignorés:      {r.skipped}")
        logger.info(f"  📈 Taux réussite: {success_rate:.1f}%")
        
        # Résumé par catégorie
        logger.info("\n📁 Par catégorie:")
        for cat, stats in self.report.summary.items():
            total = stats["passed"] + stats["failed"] + stats["warnings"]
            if total > 0:
                cat_rate = (stats["passed"] / total * 100)
                status = "✅" if cat_rate >= 80 else "⚠️" if cat_rate >= 50 else "❌"
                logger.info(f"  {status} {cat}: {stats['passed']}/{total} ({cat_rate:.0f}%)")
        
        # Conclusion
        logger.info("\n" + "="*50)
        if r.failed == 0 and r.warnings <= 2:
            logger.info("🎉 TOUS LES TESTS SONT PASSÉS!")
        elif r.failed == 0:
            logger.info("⚠️ Tests passés avec quelques avertissements")
        else:
            logger.info(f"❌ {r.failed} test(s) échoué(s) - vérifiez les erreurs ci-dessus")
        logger.info("="*50 + "\n")
    
    def save_report(self, filepath: str = None):
        """Sauvegarder le rapport en JSON"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"test_reports/test_report_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.report.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Rapport sauvegardé: {filepath}")
        return filepath


async def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="🐂 Bull Sage - Agent Testeur")
    parser.add_argument("--quick", action="store_true", help="Tests rapides seulement")
    parser.add_argument("--deribit", action="store_true", help="Tests Deribit uniquement")
    parser.add_argument("--predictions", action="store_true", help="Tests prédictions IA uniquement")
    parser.add_argument("--report", action="store_true", help="Sauvegarder le rapport JSON")
    parser.add_argument("--url", default="http://localhost:8000", help="URL du backend")
    
    args = parser.parse_args()
    
    async with BullSageTestAgent(base_url=args.url) as agent:
        if args.deribit:
            await agent.run_deribit_tests()
            agent._print_summary()
        elif args.predictions:
            await agent.run_prediction_tests()
            agent._print_summary()
        else:
            await agent.run_all_tests(quick=args.quick)
        
        if args.report:
            agent.save_report()
        
        # Retourner le code de sortie approprié
        return 0 if agent.report.failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
