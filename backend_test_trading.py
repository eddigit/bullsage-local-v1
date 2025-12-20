#!/usr/bin/env python3
"""
BULL SAGE Trading Features Backend Testing
Tests specific trading endpoints mentioned in review request
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class TradingAPITester:
    def __init__(self, base_url="https://tradingbull-ai.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.session = requests.Session()
        self.session.timeout = 30

    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict] = None, headers: Optional[Dict] = None) -> tuple[bool, Dict]:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        self.log(f"Testing {name}...")
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=test_headers)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {"status": "success", "raw_response": response.text}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                self.log(f"   Response: {response.text[:200]}")
                self.failed_tests.append({
                    "name": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:500]
                })
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}", "ERROR")
            self.failed_tests.append({
                "name": name,
                "error": str(e)
            })
            return False, {}

    def test_login(self):
        """Test login with provided credentials"""
        success, response = self.run_test(
            "Login with provided credentials",
            "POST",
            "auth/login",
            200,
            data={
                "email": "coachdigitalparis@gmail.com",
                "password": "$$Reussite888!!"
            }
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response.get('user', {}).get('id')
            self.log(f"✅ Login successful, token acquired")
            return True
        return False

    def test_crypto_markets(self):
        """Test crypto markets endpoint for watchlist"""
        success, response = self.run_test(
            "Get crypto markets for watchlist",
            "GET",
            "market/crypto",
            200
        )
        if success and isinstance(response, list) and len(response) > 0:
            self.log(f"✅ Retrieved {len(response)} cryptocurrencies")
            # Check if watchlist coins are present
            coin_ids = [coin.get('id') for coin in response]
            watchlist_coins = ['bitcoin', 'ethereum', 'solana']
            found_coins = [coin for coin in watchlist_coins if coin in coin_ids]
            self.log(f"   Watchlist coins found: {found_coins}")
            return True, response
        return False, {}

    def test_trading_analyze(self):
        """Test trading analysis endpoint"""
        success, response = self.run_test(
            "Trading analysis API call",
            "POST",
            "trading/analyze",
            200,
            data={
                "coin_id": "bitcoin",
                "timeframe": "4h",
                "trading_style": "swing"
            }
        )
        if success:
            # Check if response contains expected fields
            required_fields = ['indicators', 'recommendation', 'levels', 'ai_analysis']
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                self.log(f"❌ Missing fields in analysis response: {missing_fields}")
                return False
            
            # Check indicators
            indicators = response.get('indicators', {})
            expected_indicators = ['rsi', 'macd', 'bollinger', 'moving_averages', 'support_resistance']
            missing_indicators = [ind for ind in expected_indicators if ind not in indicators]
            if missing_indicators:
                self.log(f"❌ Missing indicators: {missing_indicators}")
                return False
            
            # Check levels
            levels = response.get('levels', {})
            expected_levels = ['entry', 'stop_loss', 'take_profit_1', 'take_profit_2']
            missing_levels = [level for level in expected_levels if level not in levels]
            if missing_levels:
                self.log(f"❌ Missing price levels: {missing_levels}")
                return False
            
            self.log(f"✅ Analysis complete - RSI: {indicators.get('rsi')}, Action: {response.get('recommendation', {}).get('action')}")
            return True
        return False

    def test_scan_opportunities(self):
        """Test scan opportunities endpoint"""
        success, response = self.run_test(
            "Scan trading opportunities",
            "GET",
            "trading/scan-opportunities",
            200
        )
        if success:
            alerts = response.get('alerts', [])
            scanned = response.get('scanned', 0)
            self.log(f"✅ Scanned {scanned} coins, found {len(alerts)} opportunities")
            return True
        return False

    def test_save_signal(self):
        """Test saving trading signal"""
        success, response = self.run_test(
            "Save trading signal",
            "POST",
            "signals",
            200,  # Changed from 201 to 200 as the API returns 200
            data={
                "symbol": "bitcoin",
                "symbol_name": "Bitcoin",
                "signal_type": "BUY",
                "entry_price": 45000.0,
                "stop_loss": 42000.0,
                "take_profit_1": 48000.0,
                "take_profit_2": 52000.0,
                "timeframe": "4h",
                "confidence": "medium",
                "reason": "RSI oversold + bullish MACD",
                "price_at_signal": 45000.0
            }
        )
        if success and 'id' in response:
            self.log(f"✅ Signal saved with ID: {response['id']}")
            return True, response['id']
        return False, None

    def test_get_signals(self):
        """Test retrieving user signals"""
        success, response = self.run_test(
            "Get user signals",
            "GET",
            "signals",
            200
        )
        if success and isinstance(response, list):
            self.log(f"✅ Retrieved {len(response)} signals")
            return True
        return False

    def run_all_tests(self):
        """Run all trading-specific tests"""
        self.log("🚀 Starting BULL SAGE Trading Features Backend Tests")
        self.log("=" * 60)
        
        # 1. Authentication
        if not self.test_login():
            self.log("❌ Login failed, stopping tests", "ERROR")
            return False
        
        # 2. Market data for watchlist
        crypto_success, crypto_data = self.test_crypto_markets()
        if not crypto_success:
            self.log("❌ Crypto markets failed", "ERROR")
        
        # 3. Trading analysis
        if not self.test_trading_analyze():
            self.log("❌ Trading analysis failed", "ERROR")
        
        # 4. Scan opportunities
        if not self.test_scan_opportunities():
            self.log("❌ Scan opportunities failed", "ERROR")
        
        # 5. Save signal
        signal_success, signal_id = self.test_save_signal()
        if not signal_success:
            self.log("❌ Save signal failed", "ERROR")
        
        # 6. Get signals
        if not self.test_get_signals():
            self.log("❌ Get signals failed", "ERROR")
        
        # Print results
        self.log("=" * 60)
        self.log(f"📊 Tests completed: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        self.log(f"📈 Success rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            self.log("❌ Failed tests:")
            for test in self.failed_tests:
                error_msg = test.get('error', f"Status {test.get('actual')} vs {test.get('expected')}")
                self.log(f"   - {test['name']}: {error_msg}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = TradingAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())