#!/usr/bin/env python3
"""
🐂 BULL SAGE - Test de tous les Agents IA
==========================================

Test complet de tous les agents et outils de BullSage.
Inclut l'authentification et le test du Council complet.

Usage:
    python test_all_agents.py
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
load_dotenv()

import httpx

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_URL = f"{BACKEND_URL}/api"


class AgentTester:
    """Testeur de tous les agents BullSage"""
    
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.access_token: Optional[str] = None
        self.results: Dict[str, Any] = {}
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=120.0)
        return self
    
    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()
    
    def _print_section(self, title: str):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print('='*60)
    
    def _print_result(self, label: str, value: Any, status: str = "✅"):
        print(f"  {status} {label}: {value}")
    
    # ==================== AUTHENTIFICATION ====================
    
    async def authenticate(self) -> bool:
        """S'authentifier avec le compte admin ou test"""
        self._print_section("🔐 AUTHENTIFICATION")
        
        # Essayer d'abord avec le compte test
        credentials = [
            {"email": "test@test.com", "password": "Test123!"},
            {"email": "admin@bullsage.com", "password": "BullSage2024Admin!"},
        ]
        
        for creds in credentials:
            try:
                resp = await self.client.post(
                    f"{API_URL}/auth/login",
                    json=creds
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.access_token = data.get("access_token")
                    self._print_result("Connexion", f"{creds['email']}")
                    return True
            except Exception as e:
                pass
        
        # Si pas de compte, créer un compte test
        try:
            resp = await self.client.post(
                f"{API_URL}/auth/register",
                json={
                    "email": "test_agent@bullsage.com",
                    "password": "TestAgent2024!",
                    "name": "Agent de Test"
                }
            )
            if resp.status_code in [200, 201]:
                data = resp.json()
                self.access_token = data.get("access_token")
                self._print_result("Nouveau compte créé", "test_agent@bullsage.com")
                return True
            else:
                # Essayer de se connecter
                resp = await self.client.post(
                    f"{API_URL}/auth/login",
                    json={
                        "email": "test_agent@bullsage.com",
                        "password": "TestAgent2024!"
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.access_token = data.get("access_token")
                    self._print_result("Connexion", "test_agent@bullsage.com")
                    return True
        except Exception as e:
            self._print_result("Authentification", str(e), "❌")
        
        self._print_result("Authentification", "Échec - continuer en mode non-authentifié", "⚠️")
        return False
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Obtenir les headers d'authentification"""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
    
    # ==================== TEST DES CLÉS API ====================
    
    async def test_api_keys(self) -> Dict[str, bool]:
        """Vérifier toutes les clés API configurées"""
        self._print_section("🔑 CLÉS API CONFIGURÉES")
        
        keys = {
            "Anthropic (Claude)": "ANTHROPIC_API_KEY",
            "Groq": "GROQ_API_KEY",
            "xAI (Grok)": "XAI_API_KEY",
            "OpenRouter": "OPENROUTER_API_KEY",
            "DeepSeek": "DEEPSEEK_API_KEY",
            "Perplexity": "PERPLEXITY_API_KEY",
            "OpenAI": "OPENAI_API_KEY",
            "Alpha Vantage": "ALPHA_VANTAGE_API_KEY",
            "Finnhub": "FINNHUB_API_KEY",
            "Deribit Client ID": "DERIBIT_CLIENT_ID",
            "Deribit Secret": "DERIBIT_CLIENT_SECRET",
        }
        
        results = {}
        for name, env_var in keys.items():
            value = os.getenv(env_var)
            configured = bool(value and len(value) > 5)
            results[name] = configured
            status = "✅" if configured else "❌"
            masked = f"{value[:4]}...{value[-4:]}" if configured else "Non configurée"
            self._print_result(name, masked, status)
        
        self.results["api_keys"] = results
        return results
    
    # ==================== TEST DU COUNCIL ====================
    
    async def test_council_agents(self) -> Dict[str, Any]:
        """Tester les agents du Council"""
        self._print_section("🧠 AGENTS DU COUNCIL")
        
        council_results = {"agents": [], "modes": []}
        
        # Liste des agents
        try:
            resp = await self.client.get(
                f"{API_URL}/council/agents",
                headers=self._get_auth_headers()
            )
            if resp.status_code == 200:
                data = resp.json()
                agents = data.get("agents", [])
                council_results["agents"] = agents
                
                print(f"  🤖 {len(agents)} agents configurés:")
                for agent in agents:
                    name = agent.get("name", "Unknown")
                    provider = agent.get("provider", "Unknown")
                    active = agent.get("active", False)
                    status = "✅" if active else "❌"
                    print(f"     {status} {name} ({provider})")
            elif resp.status_code == 403:
                self._print_result("Agents", "Authentification requise", "⚠️")
            else:
                self._print_result("Agents", f"Erreur {resp.status_code}", "❌")
        except Exception as e:
            self._print_result("Agents Council", str(e), "❌")
        
        # Modes disponibles
        try:
            resp = await self.client.get(
                f"{API_URL}/council/modes",
                headers=self._get_auth_headers()
            )
            if resp.status_code == 200:
                data = resp.json()
                modes = data.get("modes", [])
                council_results["modes"] = modes
                
                print(f"\n  ⚡ Modes disponibles:")
                for mode in modes:
                    name = mode.get("name", "Unknown")
                    cost = mode.get("estimated_cost_usd", 0)
                    print(f"     • {name}: ~${cost:.4f}")
        except Exception as e:
            pass
        
        self.results["council"] = council_results
        return council_results
    
    # ==================== TEST MARKET ROUTES ====================
    
    async def test_market_routes(self) -> Dict[str, Any]:
        """Tester les routes du marché"""
        self._print_section("📊 ROUTES MARCHÉ")
        
        market_results = {}
        
        routes_to_test = [
            ("/market/overview", "GET", "Vue d'ensemble"),
            ("/market/bitcoin", "GET", "Données Bitcoin"),
            ("/market/fear-greed", "GET", "Fear & Greed Index"),
            ("/market/trending", "GET", "Cryptos tendance"),
            ("/market/crypto/BTC", "GET", "Données BTC"),
        ]
        
        for route, method, desc in routes_to_test:
            try:
                if method == "GET":
                    resp = await self.client.get(
                        f"{API_URL}{route}",
                        headers=self._get_auth_headers()
                    )
                else:
                    resp = await self.client.post(
                        f"{API_URL}{route}",
                        headers=self._get_auth_headers()
                    )
                
                market_results[route] = {
                    "status": resp.status_code,
                    "success": resp.status_code == 200
                }
                
                status = "✅" if resp.status_code == 200 else "⚠️" if resp.status_code == 403 else "❌"
                self._print_result(desc, f"[{resp.status_code}]", status)
            except Exception as e:
                market_results[route] = {"status": "error", "success": False}
                self._print_result(desc, str(e), "❌")
        
        self.results["market_routes"] = market_results
        return market_results
    
    # ==================== TEST SIGNALS ROUTES ====================
    
    async def test_signals_routes(self) -> Dict[str, Any]:
        """Tester les routes des signaux"""
        self._print_section("📡 ROUTES SIGNAUX")
        
        signals_results = {}
        
        routes_to_test = [
            ("/signals", "GET", "Liste signaux"),
            ("/signals/active", "GET", "Signaux actifs"),
            ("/signals/history", "GET", "Historique"),
            ("/signals/stats", "GET", "Statistiques"),
        ]
        
        for route, method, desc in routes_to_test:
            try:
                if method == "GET":
                    resp = await self.client.get(
                        f"{API_URL}{route}",
                        headers=self._get_auth_headers()
                    )
                else:
                    resp = await self.client.post(
                        f"{API_URL}{route}",
                        headers=self._get_auth_headers()
                    )
                
                signals_results[route] = {
                    "status": resp.status_code,
                    "success": resp.status_code == 200
                }
                
                status = "✅" if resp.status_code == 200 else "⚠️" if resp.status_code == 403 else "❌"
                self._print_result(desc, f"[{resp.status_code}]", status)
            except Exception as e:
                signals_results[route] = {"status": "error", "success": False}
                self._print_result(desc, str(e), "❌")
        
        self.results["signals_routes"] = signals_results
        return signals_results
    
    # ==================== TEST DERIBIT ====================
    
    async def test_deribit(self) -> Dict[str, Any]:
        """Tester Deribit Trading"""
        self._print_section("📈 DERIBIT TRADING")
        
        deribit_results = {}
        
        # Compte
        try:
            resp = await self.client.get(
                f"{API_URL}/deribit/account",
                params={"currency": "BTC"}
            )
            if resp.status_code == 200:
                data = resp.json()
                account = data.get("account", {})
                balance = account.get("balance", 0)
                deribit_results["account"] = {"balance": balance, "success": True}
                self._print_result("Compte", f"{balance} BTC")
            else:
                deribit_results["account"] = {"success": False}
                self._print_result("Compte", f"Erreur {resp.status_code}", "❌")
        except Exception as e:
            deribit_results["account"] = {"success": False, "error": str(e)}
            self._print_result("Compte", str(e), "❌")
        
        # Ticker
        try:
            resp = await self.client.get(f"{API_URL}/deribit/ticker/BTC-PERPETUAL")
            if resp.status_code == 200:
                data = resp.json()
                ticker = data.get("ticker", data)
                price = ticker.get("last_price") or ticker.get("mark_price", 0)
                deribit_results["ticker"] = {"price": price, "success": True}
                self._print_result("BTC-PERPETUAL", f"${price:,.2f}")
            else:
                deribit_results["ticker"] = {"success": False}
                self._print_result("Ticker", f"Erreur {resp.status_code}", "❌")
        except Exception as e:
            deribit_results["ticker"] = {"success": False, "error": str(e)}
            self._print_result("Ticker", str(e), "❌")
        
        # Positions
        try:
            resp = await self.client.get(
                f"{API_URL}/deribit/positions",
                params={"currency": "BTC"}
            )
            if resp.status_code == 200:
                data = resp.json()
                positions = data.get("positions", [])
                deribit_results["positions"] = {"count": len(positions), "success": True}
                self._print_result("Positions", f"{len(positions)} ouvertes")
        except Exception as e:
            deribit_results["positions"] = {"success": False, "error": str(e)}
        
        self.results["deribit"] = deribit_results
        return deribit_results
    
    # ==================== TEST ASSISTANT/CHAT ====================
    
    async def test_assistant(self) -> Dict[str, Any]:
        """Tester l'assistant IA"""
        self._print_section("💬 ASSISTANT IA")
        
        assistant_results = {}
        
        try:
            resp = await self.client.post(
                f"{API_URL}/assistant/chat",
                headers=self._get_auth_headers(),
                json={"message": "Quelle est la tendance Bitcoin?"}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                response = data.get("response", data.get("message", ""))
                assistant_results["chat"] = {"success": True, "response": response[:100]}
                self._print_result("Chat", "Réponse reçue ✓")
                print(f"     💬 {response[:150]}...")
            elif resp.status_code == 403:
                self._print_result("Chat", "Authentification requise", "⚠️")
                assistant_results["chat"] = {"success": False, "auth_required": True}
            else:
                self._print_result("Chat", f"Erreur {resp.status_code}", "❌")
                assistant_results["chat"] = {"success": False}
        except Exception as e:
            assistant_results["chat"] = {"success": False, "error": str(e)}
            self._print_result("Chat", str(e), "❌")
        
        self.results["assistant"] = assistant_results
        return assistant_results
    
    # ==================== TEST PAPER TRADING ====================
    
    async def test_paper_trading(self) -> Dict[str, Any]:
        """Tester le paper trading"""
        self._print_section("📝 PAPER TRADING")
        
        paper_results = {}
        
        routes_to_test = [
            ("/paper-trading/account", "GET", "Compte Paper"),
            ("/paper-trading/positions", "GET", "Positions Paper"),
            ("/paper-trading/history", "GET", "Historique Paper"),
        ]
        
        for route, method, desc in routes_to_test:
            try:
                resp = await self.client.get(
                    f"{API_URL}{route}",
                    headers=self._get_auth_headers()
                )
                
                paper_results[route] = {
                    "status": resp.status_code,
                    "success": resp.status_code == 200
                }
                
                status = "✅" if resp.status_code == 200 else "⚠️" if resp.status_code == 403 else "❌"
                self._print_result(desc, f"[{resp.status_code}]", status)
            except Exception as e:
                paper_results[route] = {"status": "error", "success": False}
                self._print_result(desc, str(e), "❌")
        
        self.results["paper_trading"] = paper_results
        return paper_results
    
    # ==================== TEST WATCHLIST ====================
    
    async def test_watchlist(self) -> Dict[str, Any]:
        """Tester la watchlist"""
        self._print_section("👁️ WATCHLIST")
        
        watchlist_results = {}
        
        try:
            resp = await self.client.get(
                f"{API_URL}/watchlist",
                headers=self._get_auth_headers()
            )
            
            if resp.status_code == 200:
                data = resp.json()
                items = data if isinstance(data, list) else data.get("watchlist", [])
                watchlist_results["items"] = len(items)
                watchlist_results["success"] = True
                self._print_result("Watchlist", f"{len(items)} éléments")
            elif resp.status_code == 403:
                self._print_result("Watchlist", "Authentification requise", "⚠️")
                watchlist_results["success"] = False
            else:
                self._print_result("Watchlist", f"Erreur {resp.status_code}", "❌")
                watchlist_results["success"] = False
        except Exception as e:
            watchlist_results["success"] = False
            self._print_result("Watchlist", str(e), "❌")
        
        self.results["watchlist"] = watchlist_results
        return watchlist_results
    
    # ==================== RÉSUMÉ ====================
    
    def generate_summary(self):
        """Générer le résumé final"""
        self._print_section("📋 RÉSUMÉ DES TESTS")
        
        total = 0
        passed = 0
        warnings = 0
        failed = 0
        
        # Calculer les statistiques
        for category, data in self.results.items():
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict) and "success" in value:
                        total += 1
                        if value["success"]:
                            passed += 1
                        else:
                            failed += 1
                    elif isinstance(value, bool):
                        total += 1
                        if value:
                            passed += 1
                        else:
                            failed += 1
        
        print(f"  📊 Total: {total} tests")
        print(f"  ✅ Réussis: {passed}")
        print(f"  ❌ Échecs: {failed}")
        
        score = (passed / total * 100) if total > 0 else 0
        
        if score >= 80:
            print(f"\n  🟢 Score global: {score:.1f}% - Excellent!")
        elif score >= 60:
            print(f"\n  🟡 Score global: {score:.1f}% - Bon")
        elif score >= 40:
            print(f"\n  🟠 Score global: {score:.1f}% - Améliorations nécessaires")
        else:
            print(f"\n  🔴 Score global: {score:.1f}% - Problèmes critiques")
        
        return {"total": total, "passed": passed, "failed": failed, "score": score}
    
    # ==================== EXÉCUTION ====================
    
    async def run_all_tests(self):
        """Exécuter tous les tests"""
        print("\n" + "🐂"*30)
        print("   BULL SAGE - TEST DE TOUS LES AGENTS")
        print("   " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("🐂"*30)
        
        # 1. Authentification
        await self.authenticate()
        
        # 2. Tests des clés API
        await self.test_api_keys()
        
        # 3. Tests du Council
        await self.test_council_agents()
        
        # 4. Tests des routes
        await self.test_market_routes()
        await self.test_signals_routes()
        
        # 5. Tests Deribit
        await self.test_deribit()
        
        # 6. Tests Assistant
        await self.test_assistant()
        
        # 7. Tests Paper Trading
        await self.test_paper_trading()
        
        # 8. Tests Watchlist
        await self.test_watchlist()
        
        # Résumé
        summary = self.generate_summary()
        
        # Sauvegarder le rapport
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"test_reports/agents_test_{timestamp}.json"
        os.makedirs("test_reports", exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "summary": summary,
                "results": self.results
            }, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Rapport sauvegardé: {filepath}")
        print("="*60 + "\n")
        
        return self.results


async def main():
    async with AgentTester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
