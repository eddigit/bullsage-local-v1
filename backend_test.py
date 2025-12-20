#!/usr/bin/env python3
"""
BULL SAGE Backend API Testing Suite
Tests all endpoints including auth, markets, AI assistant, paper trading, etc.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class BullSageAPITester:
    def __init__(self, base_url="https://bullsage.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_token = None
        self.user_id = None
        self.admin_user_id = None
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
                 data: Optional[Dict] = None, headers: Optional[Dict] = None, 
                 use_admin: bool = False) -> tuple[bool, Dict]:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        # Add auth token if available
        token = self.admin_token if use_admin and self.admin_token else self.token
        if token:
            test_headers['Authorization'] = f'Bearer {token}'
        
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
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {"message": "Success"}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}")
                except:
                    self.log(f"   Error: {response.text}")
                
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "endpoint": endpoint
                })
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Exception: {str(e)}", "ERROR")
            self.failed_tests.append({
                "test": name,
                "error": str(e),
                "endpoint": endpoint
            })
            return False, {}

    def test_health_check(self):
        """Test basic health endpoints"""
        self.log("=== HEALTH CHECK TESTS ===")
        self.run_test("API Root", "GET", "", 200)
        self.run_test("Health Check", "GET", "health", 200)

    def test_user_registration(self):
        """Test user registration"""
        self.log("=== USER REGISTRATION TEST ===")
        timestamp = datetime.now().strftime("%H%M%S")
        test_user_data = {
            "name": f"Test User {timestamp}",
            "email": f"testuser{timestamp}@example.com",
            "password": "TestPassword123!",
            "trading_level": "beginner"
        }
        
        success, response = self.run_test(
            "User Registration", 
            "POST", 
            "auth/register", 
            200, 
            test_user_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            self.log(f"✅ User registered with ID: {self.user_id}")
            return True
        return False

    def test_admin_login(self):
        """Test admin login with provided credentials"""
        self.log("=== ADMIN LOGIN TEST ===")
        admin_credentials = {
            "email": "coachdigitalparis@gmail.com",
            "password": "$$Reussite888!!"
        }
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            admin_credentials
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.admin_user_id = response['user']['id']
            admin_status = response['user'].get('is_admin', False)
            self.log(f"✅ Admin logged in - Admin status: {admin_status}")
            return admin_status
        return False

    def test_user_login(self):
        """Test user login"""
        self.log("=== USER LOGIN TEST ===")
        # First register a user if we don't have one
        if not self.token:
            if not self.test_user_registration():
                return False
        
        # Test /auth/me endpoint
        success, response = self.run_test("Get Current User", "GET", "auth/me", 200)
        return success

    def test_market_endpoints(self):
        """Test market data endpoints"""
        self.log("=== MARKET DATA TESTS ===")
        
        # Test crypto markets
        success1, markets = self.run_test("Get Crypto Markets", "GET", "market/crypto", 200)
        
        # Test trending
        success2, _ = self.run_test("Get Trending", "GET", "market/trending", 200)
        
        # Test specific coin detail if we have markets data
        if success1 and markets and len(markets) > 0:
            coin_id = markets[0].get('id', 'bitcoin')
            self.run_test("Get Coin Detail", "GET", f"market/crypto/{coin_id}", 200)
            self.run_test("Get Coin Chart", "GET", f"market/crypto/{coin_id}/chart", 200)
        
        return success1 and success2

    def test_ai_assistant(self):
        """Test AI assistant endpoints"""
        self.log("=== AI ASSISTANT TESTS ===")
        
        # Test chat
        chat_data = {
            "message": "Bonjour BULL SAGE, peux-tu me donner une analyse rapide du marché Bitcoin?",
            "context": {}
        }
        
        success1, _ = self.run_test("AI Chat", "POST", "assistant/chat", 200, chat_data)
        
        # Test chat history
        success2, _ = self.run_test("Get Chat History", "GET", "assistant/history", 200)
        
        return success1 and success2

    def test_paper_trading(self):
        """Test paper trading endpoints"""
        self.log("=== PAPER TRADING TESTS ===")
        
        # Get portfolio
        success1, portfolio = self.run_test("Get Portfolio", "GET", "paper-trading/portfolio", 200)
        
        # Get trades history
        success2, _ = self.run_test("Get Trades", "GET", "paper-trading/trades", 200)
        
        # Test a buy trade
        trade_data = {
            "symbol": "bitcoin",
            "type": "buy",
            "amount": 0.001,
            "price": 50000
        }
        success3, _ = self.run_test("Execute Buy Trade", "POST", "paper-trading/trade", 200, trade_data)
        
        # Test a sell trade (should work if we have holdings)
        sell_data = {
            "symbol": "bitcoin", 
            "type": "sell",
            "amount": 0.0005,
            "price": 50000
        }
        # This might fail if no holdings, that's ok
        self.run_test("Execute Sell Trade", "POST", "paper-trading/trade", 200, sell_data)
        
        return success1 and success2 and success3

    def test_watchlist(self):
        """Test watchlist endpoints"""
        self.log("=== WATCHLIST TESTS ===")
        
        # Add to watchlist
        success1, _ = self.run_test("Add to Watchlist", "POST", "watchlist/ethereum", 200)
        
        # Update watchlist
        watchlist_data = {"symbols": ["bitcoin", "ethereum", "solana"]}
        success2, _ = self.run_test("Update Watchlist", "PUT", "watchlist", 200, watchlist_data)
        
        # Remove from watchlist
        success3, _ = self.run_test("Remove from Watchlist", "DELETE", "watchlist/solana", 200)
        
        return success1 and success2 and success3

    def test_alerts(self):
        """Test alerts endpoints"""
        self.log("=== ALERTS TESTS ===")
        
        # Create alert
        alert_data = {
            "symbol": "bitcoin",
            "target_price": 60000,
            "condition": "above",
            "name": "BTC Alert Test"
        }
        success1, alert_response = self.run_test("Create Alert", "POST", "alerts", 200, alert_data)
        
        # Get alerts
        success2, _ = self.run_test("Get Alerts", "GET", "alerts", 200)
        
        # Delete alert if created
        if success1 and 'id' in alert_response:
            alert_id = alert_response['id']
            success3, _ = self.run_test("Delete Alert", "DELETE", f"alerts/{alert_id}", 200)
            return success1 and success2 and success3
        
        return success1 and success2

    def test_strategies(self):
        """Test strategies endpoints"""
        self.log("=== STRATEGIES TESTS ===")
        
        # Create strategy
        strategy_data = {
            "name": "Test Strategy",
            "description": "A test trading strategy",
            "indicators": ["RSI", "MACD"],
            "entry_rules": "RSI < 30 and MACD bullish cross",
            "exit_rules": "RSI > 70 or 5% profit",
            "risk_percentage": 2.0
        }
        success1, strategy_response = self.run_test("Create Strategy", "POST", "strategies", 200, strategy_data)
        
        # Get strategies
        success2, _ = self.run_test("Get Strategies", "GET", "strategies", 200)
        
        # Delete strategy if created
        if success1 and 'id' in strategy_response:
            strategy_id = strategy_response['id']
            success3, _ = self.run_test("Delete Strategy", "DELETE", f"strategies/{strategy_id}", 200)
            return success1 and success2 and success3
        
        return success1 and success2

    def test_admin_endpoints(self):
        """Test admin-only endpoints"""
        self.log("=== ADMIN ENDPOINTS TESTS ===")
        
        if not self.admin_token:
            self.log("❌ No admin token available, skipping admin tests")
            return False
        
        # Test admin stats
        success1, _ = self.run_test("Admin Stats", "GET", "admin/stats", 200, use_admin=True)
        
        # Test admin users list
        success2, _ = self.run_test("Admin Users List", "GET", "admin/users", 200, use_admin=True)
        
        return success1 and success2

    def test_settings(self):
        """Test user settings endpoints"""
        self.log("=== SETTINGS TESTS ===")
        
        # Update trading level
        success, _ = self.run_test("Update Trading Level", "PUT", "settings/trading-level?level=intermediate", 200)
        return success

    def run_all_tests(self):
        """Run all test suites"""
        self.log("🚀 Starting BULL SAGE API Tests")
        self.log(f"Testing against: {self.base_url}")
        
        # Health checks first
        self.test_health_check()
        
        # Authentication tests
        user_reg_success = self.test_user_registration()
        admin_login_success = self.test_admin_login()
        user_auth_success = self.test_user_login()
        
        if not user_auth_success:
            self.log("❌ User authentication failed, stopping tests")
            return False
        
        # Core functionality tests (require auth)
        self.test_market_endpoints()
        self.test_ai_assistant()
        self.test_paper_trading()
        self.test_watchlist()
        self.test_alerts()
        self.test_strategies()
        self.test_settings()
        
        # Admin tests (if admin login successful)
        if admin_login_success:
            self.test_admin_endpoints()
        
        return True

    def print_summary(self):
        """Print test summary"""
        self.log("=" * 50)
        self.log("🏁 TEST SUMMARY")
        self.log(f"Total tests: {self.tests_run}")
        self.log(f"Passed: {self.tests_passed}")
        self.log(f"Failed: {len(self.failed_tests)}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            self.log("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                error_msg = test.get('error', f"Expected {test.get('expected')}, got {test.get('actual')}")
                self.log(f"  - {test['test']}: {error_msg}")
        
        return len(self.failed_tests) == 0

def main():
    """Main test execution"""
    tester = BullSageAPITester()
    
    try:
        success = tester.run_all_tests()
        tester.print_summary()
        
        # Return appropriate exit code
        return 0 if success else 1
        
    except KeyboardInterrupt:
        tester.log("Tests interrupted by user")
        return 1
    except Exception as e:
        tester.log(f"Unexpected error: {e}", "ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main())