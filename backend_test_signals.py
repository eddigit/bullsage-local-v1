#!/usr/bin/env python3
"""
BULL SAGE - Signal Evaluation Testing
Tests the new signal evaluation functionality and backend endpoints
"""

import requests
import sys
import json
from datetime import datetime

class SignalEvaluationTester:
    def __init__(self, base_url="https://marketoracle-35.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_login(self):
        """Test login with provided credentials"""
        success, response = self.run_test(
            "Admin Login",
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
            self.user_id = response['user']['id']
            print(f"   Logged in as: {response['user']['name']}")
            return True
        return False

    def test_create_test_signal(self):
        """Create a test signal for evaluation"""
        signal_data = {
            "symbol": "bitcoin",
            "symbol_name": "Bitcoin",
            "signal_type": "BUY",
            "entry_price": 45000.0,
            "stop_loss": 42000.0,
            "take_profit_1": 48000.0,
            "take_profit_2": 52000.0,
            "timeframe": "4h",
            "confidence": "high",
            "reason": "Test signal for evaluation",
            "price_at_signal": 45000.0
        }
        
        success, response = self.run_test(
            "Create Test Signal",
            "POST",
            "signals",
            200,
            data=signal_data
        )
        
        if success and 'id' in response:
            print(f"   Created signal ID: {response['id']}")
            return response['id']
        return None

    def test_signals_stats(self):
        """Test signals statistics endpoint"""
        success, response = self.run_test(
            "Get Signals Statistics",
            "GET",
            "signals/stats",
            200
        )
        
        if success:
            print(f"   Total signals: {response.get('total_signals', 0)}")
            print(f"   Active signals: {response.get('active', 0)}")
            print(f"   Win rate: {response.get('win_rate', 0)}%")
        
        return success

    def test_signals_evaluate(self):
        """Test the new signals evaluation endpoint"""
        success, response = self.run_test(
            "Evaluate Active Signals",
            "POST",
            "signals/evaluate",
            200
        )
        
        if success:
            print(f"   Message: {response.get('message', 'No message')}")
            print(f"   Total evaluated: {response.get('total_evaluated', 0)}")
            print(f"   Updated: {response.get('updated', 0)}")
            
            results = response.get('results', [])
            if results:
                print(f"   Results count: {len(results)}")
                for i, result in enumerate(results[:3]):  # Show first 3 results
                    print(f"     Result {i+1}: {result.get('symbol', 'Unknown')} - {result.get('status', 'Unknown')}")
        
        return success

    def test_get_signals(self):
        """Test getting user signals"""
        success, response = self.run_test(
            "Get User Signals",
            "GET",
            "signals",
            200
        )
        
        if success:
            signals_count = len(response) if isinstance(response, list) else 0
            print(f"   Found {signals_count} signals")
            
            if signals_count > 0:
                latest_signal = response[0]
                print(f"   Latest signal: {latest_signal.get('symbol_name', 'Unknown')} - {latest_signal.get('status', 'Unknown')}")
        
        return success

    def test_update_signal_status(self, signal_id):
        """Test updating signal status"""
        if not signal_id:
            print("⚠️  Skipping signal status update - no signal ID")
            return True
            
        success, response = self.run_test(
            "Update Signal Status",
            "PUT",
            f"signals/{signal_id}/status?status=hit_tp1&result_pnl=6.67",
            200
        )
        
        if success:
            print(f"   Updated signal status: {response.get('status', 'Unknown')}")
        
        return success

    def test_market_crypto_prices(self):
        """Test crypto market data for signal evaluation"""
        success, response = self.run_test(
            "Get Crypto Market Data",
            "GET",
            "market/crypto",
            200
        )
        
        if success:
            crypto_count = len(response) if isinstance(response, list) else 0
            print(f"   Found {crypto_count} cryptocurrencies")
            
            if crypto_count > 0:
                btc = next((c for c in response if c.get('id') == 'bitcoin'), None)
                if btc:
                    print(f"   Bitcoin price: ${btc.get('current_price', 0):,.2f}")
        
        return success

def main():
    print("🚀 BULL SAGE - Signal Evaluation Testing")
    print("=" * 50)
    
    tester = SignalEvaluationTester()
    
    # Test authentication
    if not tester.test_login():
        print("❌ Login failed, stopping tests")
        return 1
    
    # Test market data (needed for signal evaluation)
    tester.test_market_crypto_prices()
    
    # Test signals functionality
    tester.test_get_signals()
    tester.test_signals_stats()
    
    # Create a test signal
    signal_id = tester.test_create_test_signal()
    
    # Test signal evaluation (main new feature)
    tester.test_signals_evaluate()
    
    # Test signal status update
    tester.test_update_signal_status(signal_id)
    
    # Final stats check
    tester.test_signals_stats()
    
    # Print results
    print(f"\n📊 Test Results:")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🎉 Signal evaluation functionality is working excellently!")
        return 0
    elif success_rate >= 70:
        print("⚠️  Signal evaluation has some issues but core functionality works")
        return 0
    else:
        print("❌ Signal evaluation has significant issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())