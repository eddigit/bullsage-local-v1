#!/usr/bin/env python3
"""
BULL SAGE Admin Panel & Avatar Upload Testing
Tests admin functionality and profile picture upload features
"""

import requests
import sys
import json
from datetime import datetime
import os

class BullSageAPITester:
    def __init__(self, base_url="https://marketoracle-35.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.regular_token = None
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

    def test_admin_login(self):
        """Test admin login with bullsagetrader@gmail.com"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": "bullsagetrader@gmail.com",
                "password": "$$Reussit888!!"
            }
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            user_data = response.get('user', {})
            if user_data.get('is_admin'):
                self.log_result("Admin Status Check", True, "User has admin privileges")
                return True
            else:
                self.log_result("Admin Status Check", False, "User does not have admin privileges")
                return False
        return False

    def test_regular_login(self):
        """Test login with regular admin account"""
        success, response = self.run_test(
            "Regular Admin Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": "coachdigitalparis@gmail.com",
                "password": "$$Reussite888!!"
            }
        )
        
        if success and 'access_token' in response:
            self.regular_token = response['access_token']
            return True
        return False

    def test_admin_stats(self):
        """Test admin stats endpoint"""
        if not self.admin_token:
            self.log_result("Admin Stats", False, "No admin token available")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Admin Stats",
            "GET",
            "admin/stats",
            200,
            headers=headers
        )
        
        if success:
            # Check if stats contain expected fields
            expected_fields = ['users', 'paper_trades', 'ai_chats', 'alerts', 'strategies']
            missing_fields = [field for field in expected_fields if field not in response]
            if missing_fields:
                self.log_result("Admin Stats Fields", False, f"Missing fields: {missing_fields}")
            else:
                self.log_result("Admin Stats Fields", True, "All expected fields present")
        
        return success

    def test_admin_users_list(self):
        """Test admin users list endpoint"""
        if not self.admin_token:
            self.log_result("Admin Users List", False, "No admin token available")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Admin Users List",
            "GET",
            "admin/users",
            200,
            headers=headers
        )
        
        if success and isinstance(response, list):
            self.log_result("Admin Users List Format", True, f"Found {len(response)} users")
            
            # Check if admin user is in the list
            admin_found = any(user.get('email') == 'bullsagetrader@gmail.com' for user in response)
            if admin_found:
                self.log_result("Admin User in List", True, "Admin user found in users list")
            else:
                self.log_result("Admin User in List", False, "Admin user not found in users list")
        
        return success

    def test_user_promotion(self):
        """Test promoting/demoting users to admin"""
        if not self.admin_token:
            self.log_result("User Promotion", False, "No admin token available")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # First get users list to find a non-admin user
        success, users = self.run_test(
            "Get Users for Promotion Test",
            "GET",
            "admin/users",
            200,
            headers=headers
        )
        
        if not success:
            return False
            
        # Find a non-admin user (not the current admin)
        target_user = None
        for user in users:
            if user.get('email') != 'bullsagetrader@gmail.com' and not user.get('is_admin', False):
                target_user = user
                break
        
        if not target_user:
            self.log_result("User Promotion", False, "No suitable user found for promotion test")
            return False
        
        user_id = target_user['id']
        
        # Test promoting to admin
        success, response = self.run_test(
            "Promote User to Admin",
            "PUT",
            f"admin/users/{user_id}/admin?is_admin=true",
            200,
            headers=headers
        )
        
        if success:
            # Test demoting from admin
            success2, response2 = self.run_test(
                "Demote User from Admin",
                "PUT",
                f"admin/users/{user_id}/admin?is_admin=false",
                200,
                headers=headers
            )
            return success2
        
        return success

    def test_avatar_upload(self):
        """Test avatar upload functionality"""
        if not self.admin_token:
            self.log_result("Avatar Upload", False, "No admin token available")
            return False
        
        # Create a simple test image file
        test_image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        files = {'file': ('test_avatar.png', test_image_content, 'image/png')}
        
        success, response = self.run_test(
            "Avatar Upload",
            "POST",
            "profile/avatar",
            200,
            headers=headers,
            files=files
        )
        
        if success and 'avatar' in response:
            avatar_path = response['avatar']
            self.log_result("Avatar Path Check", True, f"Avatar path: {avatar_path}")
            
            # Test avatar deletion
            success2, response2 = self.run_test(
                "Avatar Delete",
                "DELETE",
                "profile/avatar",
                200,
                headers=headers
            )
            return success2
        
        return success

    def test_settings_endpoints(self):
        """Test settings related endpoints"""
        if not self.admin_token:
            self.log_result("Settings Endpoints", False, "No admin token available")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test trading level update
        success, response = self.run_test(
            "Update Trading Level",
            "PUT",
            "settings/trading-level?level=advanced",
            200,
            headers=headers
        )
        
        return success

    def test_non_admin_access(self):
        """Test that non-admin users cannot access admin endpoints"""
        if not self.regular_token:
            self.log_result("Non-Admin Access Test", False, "No regular token available")
            return False
            
        headers = {'Authorization': f'Bearer {self.regular_token}'}
        
        # Try to access admin stats (should fail)
        success, response = self.run_test(
            "Non-Admin Stats Access",
            "GET",
            "admin/stats",
            403,  # Expecting forbidden
            headers=headers
        )
        
        return success

    def test_defi_wallet_endpoints(self):
        """Test DeFi wallet endpoints"""
        if not self.admin_token:
            self.log_result("DeFi Wallet Endpoints", False, "No admin token available")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test supported chains endpoint
        success1, chains_response = self.run_test(
            "Get Supported Chains",
            "GET",
            "wallet/supported-chains",
            200,
            headers=headers
        )
        
        if success1 and isinstance(chains_response, list):
            expected_chains = ['solana', 'ethereum', 'polygon', 'bsc']
            found_chains = [chain.get('id') for chain in chains_response]
            missing_chains = [chain for chain in expected_chains if chain not in found_chains]
            
            if missing_chains:
                self.log_result("Supported Chains Content", False, f"Missing chains: {missing_chains}")
            else:
                self.log_result("Supported Chains Content", True, f"All 4 chains found: {found_chains}")
        
        # Test wallet list endpoint
        success2, wallets_response = self.run_test(
            "Get Wallet List",
            "GET",
            "wallet/list",
            200,
            headers=headers
        )
        
        # Test wallet connect endpoint
        success3, connect_response = self.run_test(
            "Connect Wallet",
            "POST",
            "wallet/connect",
            200,
            data={
                "wallet_type": "phantom",
                "address": "7xKXtg2CW3UBuRT88WrVnjRRiAXzFkq4DmTdM2hkHNv",
                "chain": "solana"
            },
            headers=headers
        )
        
        return success1 and success2

    def test_defi_scanner_endpoints(self):
        """Test DeFi scanner endpoints"""
        if not self.admin_token:
            self.log_result("DeFi Scanner Endpoints", False, "No admin token available")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test DeFi scanner with different chains
        chains_to_test = ['solana', 'ethereum']
        
        for chain in chains_to_test:
            success, scanner_response = self.run_test(
                f"DeFi Scanner - {chain.title()}",
                "GET",
                f"defi-scanner/scan?chain={chain}&limit=5&min_liquidity=1000&min_volume=500",
                200,
                headers=headers
            )
            
            if success and isinstance(scanner_response, dict):
                if 'tokens' in scanner_response:
                    tokens = scanner_response['tokens']
                    self.log_result(f"DeFi Scanner {chain} - Tokens", True, f"Found {len(tokens)} tokens")
                    
                    # Check token structure
                    if tokens and len(tokens) > 0:
                        token = tokens[0]
                        required_fields = ['symbol', 'name', 'price_usd', 'volume_24h', 'liquidity', 'score', 'chain']
                        missing_fields = [field for field in required_fields if field not in token]
                        
                        if missing_fields:
                            self.log_result(f"DeFi Scanner {chain} - Token Fields", False, f"Missing fields: {missing_fields}")
                        else:
                            self.log_result(f"DeFi Scanner {chain} - Token Fields", True, "All required fields present")
                else:
                    self.log_result(f"DeFi Scanner {chain} - Response", False, "No 'tokens' field in response")
            else:
                self.log_result(f"DeFi Scanner {chain} - Response", False, "Invalid response format")
        
        return True

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting BULL SAGE Admin Panel & DeFi Features Tests")
        print("=" * 60)
        
        # Authentication tests
        admin_login_success = self.test_admin_login()
        regular_login_success = self.test_regular_login()
        
        if not admin_login_success:
            print("\n❌ Admin login failed - cannot proceed with admin tests")
            return self.get_summary()
        
        # Admin functionality tests
        self.test_admin_stats()
        self.test_admin_users_list()
        self.test_user_promotion()
        
        # Avatar upload tests
        self.test_avatar_upload()
        
        # Settings tests
        self.test_settings_endpoints()
        
        # DeFi functionality tests
        print("\n🔗 Testing DeFi Features...")
        self.test_defi_wallet_endpoints()
        self.test_defi_scanner_endpoints()
        
        # Security tests
        if regular_login_success:
            self.test_non_admin_access()
        
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
    tester = BullSageAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())