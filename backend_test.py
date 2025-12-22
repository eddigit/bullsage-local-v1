#!/usr/bin/env python3
"""
BULL SAGE Market News & Indices Testing
Tests market news integration with NASDAQ/S&P 500 indices and financial news functionality
"""

import requests
import sys
import json
from datetime import datetime
import os

class BullSageMarketNewsTester:
    def __init__(self, base_url="https://marketoracle-35.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []

    def log_result(self, test_name, success, message="", response_data=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: {message}")
        else:
            print(f"❌ {test_name}: {message}")
        
        self.results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "response_data": response_data
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        
        # Default headers
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)
        
        # Remove Content-Type for file uploads
        if files:
            default_headers.pop('Content-Type', None)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=default_headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=default_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers, timeout=30)

            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text[:200]}

            if success:
                self.log_result(name, True, f"Status: {response.status_code}", response_data)
            else:
                self.log_result(name, False, f"Expected {expected_status}, got {response.status_code}. Response: {response.text[:200]}", response_data)

            return success, response_data

        except Exception as e:
            self.log_result(name, False, f"Error: {str(e)}")
            return False, {}

    def test_login(self):
        """Test login with provided credentials"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": "bullsagetrader@gmail.com",
                "password": "$$Reussit888!!"
            }
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            user_data = response.get('user', {})
            self.log_result("Login Success", True, f"Logged in as {user_data.get('name', 'Unknown')}")
            return True
        return False

    def test_market_news_endpoint(self):
        """Test market news endpoint"""
        if not self.token:
            self.log_result("Market News", False, "No token available")
            return False
            
        headers = {'Authorization': f'Bearer {self.token}'}
        success, response = self.run_test(
            "Market News API",
            "GET",
            "market/news?category=general&limit=20",
            200,
            headers=headers
        )
        
        if success:
            # Check response structure
            if 'news' in response and isinstance(response['news'], list):
                news_count = len(response['news'])
                self.log_result("Market News Structure", True, f"Found {news_count} news articles")
                
                # Check first news item structure
                if news_count > 0:
                    news_item = response['news'][0]
                    required_fields = ['title', 'summary', 'url', 'source', 'published_at']
                    missing_fields = [field for field in required_fields if field not in news_item]
                    
                    if missing_fields:
                        self.log_result("News Item Structure", False, f"Missing fields: {missing_fields}")
                    else:
                        self.log_result("News Item Structure", True, "All required fields present")
                        # Log sample news
                        print(f"   Sample: {news_item.get('title', '')[:50]}...")
            else:
                self.log_result("Market News Structure", False, "Invalid response structure")
        
        return success

    def test_market_indices_endpoint(self):
        """Test market indices endpoint"""
        if not self.token:
            self.log_result("Market Indices", False, "No token available")
            return False
            
        headers = {'Authorization': f'Bearer {self.token}'}
        success, response = self.run_test(
            "Market Indices API",
            "GET",
            "market/indices",
            200,
            headers=headers
        )
        
        if success:
            # Check response structure
            if 'indices' in response and isinstance(response['indices'], list):
                indices_count = len(response['indices'])
                self.log_result("Market Indices Structure", True, f"Found {indices_count} indices")
                
                # Check for expected indices
                expected_symbols = ['QQQ', 'SPY', 'DIA', 'IWM', 'VIX']
                found_symbols = [idx.get('symbol') for idx in response['indices']]
                
                for symbol in expected_symbols:
                    if symbol in found_symbols:
                        idx_data = next((idx for idx in response['indices'] if idx.get('symbol') == symbol), None)
                        if idx_data:
                            price = idx_data.get('price', 0)
                            change = idx_data.get('change_percent', 0)
                            self.log_result(f"Index {symbol}", True, f"Price: ${price:.2f}, Change: {change:.2f}%")
                    else:
                        self.log_result(f"Index {symbol}", False, f"Missing {symbol} index")
                
                # Check first index structure
                if indices_count > 0:
                    index_item = response['indices'][0]
                    required_fields = ['symbol', 'name', 'price', 'change', 'change_percent']
                    missing_fields = [field for field in required_fields if field not in index_item]
                    
                    if missing_fields:
                        self.log_result("Index Item Structure", False, f"Missing fields: {missing_fields}")
                    else:
                        self.log_result("Index Item Structure", True, "All required fields present")
            else:
                self.log_result("Market Indices Structure", False, "Invalid response structure")
        
        return success

    def test_economic_calendar_endpoint(self):
        """Test economic calendar endpoint"""
        if not self.token:
            self.log_result("Economic Calendar", False, "No token available")
            return False
            
        headers = {'Authorization': f'Bearer {self.token}'}
        success, response = self.run_test(
            "Economic Calendar API",
            "GET",
            "market/economic-calendar",
            200,
            headers=headers
        )
        
        if success:
            # Check response structure
            if 'events' in response and isinstance(response['events'], list):
                events_count = len(response['events'])
                self.log_result("Economic Calendar Structure", True, f"Found {events_count} events")
                
                # Check event structure if events exist
                if events_count > 0:
                    event_item = response['events'][0]
                    expected_fields = ['event', 'time', 'country', 'impact']
                    missing_fields = [field for field in expected_fields if field not in event_item]
                    
                    if missing_fields:
                        self.log_result("Event Item Structure", False, f"Missing fields: {missing_fields}")
                    else:
                        self.log_result("Event Item Structure", True, "All required fields present")
                        print(f"   Sample: {event_item.get('event', '')[:50]}...")
                else:
                    self.log_result("Economic Calendar Content", True, "No events scheduled (normal)")
            else:
                self.log_result("Economic Calendar Structure", False, "Invalid response structure")
        
        return success

    def test_news_categories(self):
        """Test different news categories"""
        if not self.token:
            self.log_result("News Categories", False, "No token available")
            return False
            
        headers = {'Authorization': f'Bearer {self.token}'}
        categories = ['general', 'forex', 'crypto', 'merger']
        
        for category in categories:
            success, response = self.run_test(
                f"News Category - {category.title()}",
                "GET",
                f"market/news?category={category}&limit=5",
                200,
                headers=headers
            )
            
            if success and 'news' in response:
                news_count = len(response['news'])
                self.log_result(f"Category {category} Content", True, f"Found {news_count} articles")
            else:
                self.log_result(f"Category {category} Content", False, "Failed to fetch category news")
        
        return True

    def test_market_endpoints_performance(self):
        """Test market endpoints for performance and reliability"""
        if not self.token:
            self.log_result("Performance Test", False, "No token available")
            return False
            
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Test multiple calls to check caching and rate limiting
        endpoints = [
            ("market/news?limit=5", "News Performance"),
            ("market/indices", "Indices Performance"),
            ("market/economic-calendar", "Calendar Performance")
        ]
        
        for endpoint, test_name in endpoints:
            start_time = datetime.now()
            success, response = self.run_test(
                test_name,
                "GET",
                endpoint,
                200,
                headers=headers
            )
            end_time = datetime.now()
            
            if success:
                duration = (end_time - start_time).total_seconds()
                if duration < 5.0:  # Should respond within 5 seconds
                    self.log_result(f"{test_name} Speed", True, f"Response time: {duration:.2f}s")
                else:
                    self.log_result(f"{test_name} Speed", False, f"Slow response: {duration:.2f}s")
        
        return True

    def run_all_tests(self):
        """Run all Market News tests"""
        print("🚀 Starting BULL SAGE Market News & Indices Tests")
        print("=" * 60)
        
        # Authentication test
        login_success = self.test_login()
        
        if not login_success:
            print("\n❌ Login failed - cannot proceed with market tests")
            return self.get_summary()
        
        # Market News functionality tests
        print("\n📰 Testing Market News Features...")
        self.test_market_news_endpoint()
        self.test_market_indices_endpoint()
        self.test_economic_calendar_endpoint()
        self.test_news_categories()
        
        # Performance tests
        print("\n⚡ Testing Performance...")
        self.test_market_endpoints_performance()
        
        return self.get_summary()

    def get_summary(self):
        """Get test summary"""
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            failed_tests = [r for r in self.results if not r['success']]
            print(f"\n❌ Failed tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['message']}")
            return 1

def main():
    tester = BullSageMarketNewsTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())