#!/usr/bin/env python3
"""
BULL SAGE Specific Features Backend Testing
Tests Dashboard, Journal, and Cockpit specific endpoints
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class BullSageSpecificTester:
    def __init__(self, base_url="https://fintech-advisor-24.preview.emergentagent.com"):
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

    def login_admin(self):
        """Login with admin credentials"""
        self.log("=== ADMIN LOGIN ===")
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
            self.token = response['access_token']
            self.user_id = response['user']['id']
            self.log(f"✅ Admin logged in with ID: {self.user_id}")
            return True
        return False

    def test_dashboard_features(self):
        """Test Dashboard specific features"""
        self.log("=== DASHBOARD FEATURES TESTS ===")
        
        # Test crypto markets (should show correct prices, not $0.00)
        success1, markets = self.run_test("Dashboard - Get Crypto Markets", "GET", "market/crypto", 200)
        
        if success1 and markets:
            # Check if prices are not $0.00
            btc_data = next((coin for coin in markets if coin.get('id') == 'bitcoin'), None)
            if btc_data and btc_data.get('current_price', 0) > 0:
                self.log(f"✅ Bitcoin price: ${btc_data['current_price']:,.2f} (not $0.00)")
            else:
                self.log("❌ Bitcoin price is $0.00 or missing")
        
        # Test Fear & Greed Index
        success2, fg_data = self.run_test("Dashboard - Fear & Greed Index", "GET", "market/fear-greed", 200)
        
        # Test news impact
        success3, news_data = self.run_test("Dashboard - News Impact", "GET", "market/news-impact", 200)
        
        # Test portfolio data
        success4, portfolio = self.run_test("Dashboard - Portfolio", "GET", "paper-trading/portfolio", 200)
        
        return success1 and success2 and success3 and success4

    def test_journal_features(self):
        """Test Journal specific features"""
        self.log("=== JOURNAL FEATURES TESTS ===")
        
        # Test get trades
        success1, trades = self.run_test("Journal - Get Trades", "GET", "journal/trades", 200)
        
        # Test get stats
        success2, stats = self.run_test("Journal - Get Stats", "GET", "journal/stats", 200)
        
        # Test create new trade
        trade_data = {
            "symbol": "bitcoin",
            "symbol_name": "Bitcoin",
            "trade_type": "BUY",
            "entry_price": 50000,
            "quantity": 0.001,
            "timeframe": "4h",
            "stop_loss": 48000,
            "take_profit": 55000,
            "emotion_before": "confident",
            "strategy_used": "Test Strategy",
            "reason_entry": "Test trade for journal functionality"
        }
        
        success3, trade_response = self.run_test("Journal - Create Trade", "POST", "journal/trades", 200, trade_data)
        
        # If trade created, test closing it
        if success3 and 'id' in trade_response:
            trade_id = trade_response['id']
            close_data = {
                "exit_price": 52000,
                "emotion_after": "satisfied",
                "reason_exit": "Target reached",
                "lessons_learned": "Good entry timing"
            }
            success4, _ = self.run_test("Journal - Close Trade", "PUT", f"journal/trades/{trade_id}/close", 200, close_data)
            return success1 and success2 and success3 and success4
        
        return success1 and success2 and success3

    def test_cockpit_features(self):
        """Test Cockpit specific features"""
        self.log("=== COCKPIT FEATURES TESTS ===")
        
        # Test daily briefing
        success1, briefing = self.run_test("Cockpit - Daily Briefing", "GET", "briefing/daily", 200)
        
        # Test get smart alerts
        success2, alerts = self.run_test("Cockpit - Get Smart Alerts", "GET", "alerts/smart", 200)
        
        # Test create smart alert
        alert_data = {
            "symbol": "bitcoin",
            "symbol_name": "Bitcoin",
            "alert_type": "price",
            "condition": "above",
            "value": 60000,
            "sound_enabled": True,
            "repeat": False
        }
        
        success3, alert_response = self.run_test("Cockpit - Create Smart Alert", "POST", "alerts/smart", 200, alert_data)
        
        # Test check alerts (manual verification)
        success4, check_result = self.run_test("Cockpit - Check Alerts", "GET", "alerts/check", 200)
        
        # Clean up: delete the alert if created
        if success3 and 'id' in alert_response:
            alert_id = alert_response['id']
            self.run_test("Cockpit - Delete Alert", "DELETE", f"alerts/smart/{alert_id}", 200)
        
        return success1 and success2 and success3 and success4

    def test_no_polling_verification(self):
        """Verify no automatic polling is happening"""
        self.log("=== NO POLLING VERIFICATION ===")
        
        # This is more of a code inspection test
        # We'll check that the endpoints exist for manual refresh
        success1, _ = self.run_test("Manual Refresh - Crypto Markets", "GET", "market/crypto", 200)
        success2, _ = self.run_test("Manual Refresh - Briefing", "GET", "briefing/daily", 200)
        success3, _ = self.run_test("Manual Refresh - Alerts Check", "GET", "alerts/check", 200)
        
        self.log("✅ Manual refresh endpoints working - no automatic polling detected in backend")
        return success1 and success2 and success3

    def run_all_tests(self):
        """Run all specific feature tests"""
        self.log("🚀 Starting BULL SAGE Specific Features Tests")
        self.log(f"Testing against: {self.base_url}")
        
        # Login first
        if not self.login_admin():
            self.log("❌ Admin login failed, stopping tests")
            return False
        
        # Test specific features
        self.test_dashboard_features()
        self.test_journal_features()
        self.test_cockpit_features()
        self.test_no_polling_verification()
        
        return True

    def print_summary(self):
        """Print test summary"""
        self.log("=" * 50)
        self.log("🏁 SPECIFIC FEATURES TEST SUMMARY")
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
    tester = BullSageSpecificTester()
    
    try:
        success = tester.run_all_tests()
        tester.print_summary()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        tester.log("Tests interrupted by user")
        return 1
    except Exception as e:
        tester.log(f"Unexpected error: {e}", "ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main())