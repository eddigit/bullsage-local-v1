#!/usr/bin/env python3
"""
Script de test des endpoints Webhook Bull Sage
==============================================

Ce script teste la disponibilite et le fonctionnement des endpoints webhook.

Usage:
    python scripts/test_webhook.py [--url URL] [--token TOKEN]

Options:
    --url URL       URL de base du backend (defaut: http://localhost:8000)
    --token TOKEN   Token webhook pour authentification
"""

import sys
import os
import argparse
import asyncio
from datetime import datetime

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import httpx
except ImportError:
    print("Erreur: httpx non installe. Installez avec: pip install httpx")
    sys.exit(1)


class WebhookTester:
    """Testeur des endpoints webhook"""

    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.results = []

    def get_headers(self):
        """Retourne les headers avec authentification"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["X-Claude-Token"] = self.token
        return headers

    async def test_endpoint(self, method: str, endpoint: str, data: dict = None):
        """Teste un endpoint et retourne le resultat"""
        url = f"{self.base_url}/api/webhook{endpoint}"
        start_time = datetime.now()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(url, headers=self.get_headers())
                else:
                    response = await client.post(url, headers=self.get_headers(), json=data)

                elapsed = (datetime.now() - start_time).total_seconds() * 1000

                result = {
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": response.status_code,
                    "success": response.status_code < 400,
                    "elapsed_ms": round(elapsed, 2),
                    "response": None
                }

                try:
                    result["response"] = response.json()
                except:
                    result["response"] = response.text[:200] if response.text else None

                return result

        except httpx.ConnectError:
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "success": False,
                "error": "Connection refused - Backend non disponible",
                "elapsed_ms": 0
            }
        except Exception as e:
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "success": False,
                "error": str(e),
                "elapsed_ms": 0
            }

    async def run_tests(self):
        """Execute tous les tests"""
        print("=" * 60)
        print("BULL SAGE - Test des Webhooks")
        print("=" * 60)
        print(f"URL: {self.base_url}")
        print(f"Token: {'Configure' if self.token else 'Non configure'}")
        print("=" * 60)

        tests = [
            ("GET", "/health", None),
            ("GET", "/account-status", None),
            ("GET", "/positions", None),
            ("GET", "/signals?hours=2", None),
        ]

        for method, endpoint, data in tests:
            print(f"\n[TEST] {method} {endpoint}")
            result = await self.test_endpoint(method, endpoint, data)
            self.results.append(result)

            if result["success"]:
                print(f"  ✅ Status: {result['status_code']} ({result['elapsed_ms']}ms)")
                if result.get("response"):
                    resp = result["response"]
                    if isinstance(resp, dict):
                        # Afficher quelques infos cles
                        if "status" in resp:
                            print(f"     Status: {resp['status']}")
                        if "equity" in resp:
                            print(f"     Equity: ${resp['equity']}")
                        if "success" in resp:
                            print(f"     Success: {resp['success']}")
                        if "positions" in resp:
                            print(f"     Positions: {len(resp.get('positions', []))}")
                        if "signals" in resp:
                            print(f"     Signals: {len(resp.get('signals', []))}")
                        if "trading_enabled" in resp:
                            print(f"     Trading: {resp['trading_enabled']}")
            else:
                print(f"  ❌ Erreur: {result.get('error') or result.get('status_code')}")
                if result.get("response"):
                    resp = result["response"]
                    if isinstance(resp, dict) and "detail" in resp:
                        print(f"     Detail: {resp['detail']}")

        # Resume
        print("\n" + "=" * 60)
        print("RESUME")
        print("=" * 60)

        success_count = sum(1 for r in self.results if r["success"])
        total_count = len(self.results)

        print(f"Tests reussis: {success_count}/{total_count}")

        if success_count == total_count:
            print("\n✅ Tous les tests ont reussi!")
        else:
            print("\n⚠️ Certains tests ont echoue")
            for r in self.results:
                if not r["success"]:
                    print(f"   - {r['method']} {r['endpoint']}: {r.get('error', 'Failed')}")

        return success_count == total_count


async def test_trading_config():
    """Teste l'import de trading_config"""
    print("\n" + "=" * 60)
    print("TEST IMPORT trading_config")
    print("=" * 60)

    try:
        from config.trading_config import trading_config, ALLOWED_MARKETS, MAX_RISK_PERCENT

        print("✅ Import reussi!")
        print(f"   MAX_RISK_PERCENT: {trading_config.MAX_RISK_PERCENT}")
        print(f"   MAX_LEVERAGE: {trading_config.MAX_LEVERAGE}")
        print(f"   MIN_CONFIDENCE: {trading_config.MIN_CONFIDENCE}")
        print(f"   COOLDOWN: {trading_config.TRADE_COOLDOWN_SECONDS}s")
        print(f"   ALLOWED_MARKETS: {len(trading_config.ALLOWED_MARKETS)} marches")
        return True

    except ImportError as e:
        print(f"❌ Erreur import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


async def main():
    parser = argparse.ArgumentParser(description="Test des webhooks Bull Sage")
    parser.add_argument("--url", default="http://localhost:8000",
                        help="URL de base du backend")
    parser.add_argument("--token", default=os.getenv("CLAUDE_WEBHOOK_TOKEN", ""),
                        help="Token webhook")

    args = parser.parse_args()

    # Test de l'import
    config_ok = await test_trading_config()

    # Test des endpoints
    tester = WebhookTester(args.url, args.token)
    endpoints_ok = await tester.run_tests()

    # Resultat final
    print("\n" + "=" * 60)
    print("RESULTAT FINAL")
    print("=" * 60)

    if config_ok and endpoints_ok:
        print("✅ Tous les tests ont reussi!")
        return 0
    else:
        print("⚠️ Certains tests ont echoue")
        if not config_ok:
            print("   - Configuration trading non importable")
        if not endpoints_ok:
            print("   - Certains endpoints ont echoue")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
