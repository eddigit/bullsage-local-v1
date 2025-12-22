#!/usr/bin/env python3
"""
BULL SAGE Academy Testing Suite
Tests all Academy endpoints including modules, lessons, quizzes, badges, and leaderboard
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class AcademyTester:
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
        
        # Add auth token if available
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

    def test_login(self):
        """Test login with provided credentials"""
        self.log("=== ACADEMY LOGIN TEST ===")
        credentials = {
            "email": "coachdigitalparis@gmail.com",
            "password": "$$Reussite888!!"
        }
        
        success, response = self.run_test(
            "Academy Login",
            "POST",
            "auth/login",
            200,
            credentials
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            self.log(f"✅ User logged in with ID: {self.user_id}")
            return True
        return False

    def test_academy_modules(self):
        """Test Academy modules endpoint"""
        self.log("=== ACADEMY MODULES TEST ===")
        
        success, modules_data = self.run_test(
            "Get Academy Modules",
            "GET",
            "academy/modules",
            200
        )
        
        if success and modules_data:
            modules = modules_data.get('modules', [])
            self.log(f"✅ Found {len(modules)} modules")
            
            # Verify we have 6 modules as expected
            if len(modules) == 6:
                self.log("✅ Correct number of modules (6)")
                
                # Check each module has required fields
                for i, module in enumerate(modules, 1):
                    required_fields = ['id', 'title', 'description', 'icon', 'color', 'order', 'estimated_time', 'total_lessons', 'completed_lessons']
                    missing_fields = [field for field in required_fields if field not in module]
                    
                    if not missing_fields:
                        self.log(f"✅ Module {i} ({module['title']}) has all required fields")
                    else:
                        self.log(f"❌ Module {i} missing fields: {missing_fields}")
                        return False
                
                # Check module progression data
                user_progress = modules_data.get('user_progress', {})
                if user_progress:
                    self.log(f"✅ User progress data: Level {user_progress.get('level', 1)} - {user_progress.get('title', 'Unknown')}")
                
                return True
            else:
                self.log(f"❌ Expected 6 modules, got {len(modules)}")
                return False
        
        return False

    def test_module_details(self):
        """Test individual module details"""
        self.log("=== MODULE DETAILS TEST ===")
        
        # Test module 1 (Les Bases du Trading)
        success, module_data = self.run_test(
            "Get Module 1 Details",
            "GET",
            "academy/modules/module_1",
            200
        )
        
        if success and module_data:
            lessons = module_data.get('lessons', [])
            self.log(f"✅ Module 1 has {len(lessons)} lessons")
            
            # Verify we have 5 lessons as expected
            if len(lessons) == 5:
                self.log("✅ Correct number of lessons (5) in Module 1")
                
                # Check each lesson has required fields
                for i, lesson in enumerate(lessons, 1):
                    required_fields = ['id', 'title', 'description', 'order', 'xp_reward']
                    missing_fields = [field for field in required_fields if field not in lesson]
                    
                    if not missing_fields:
                        self.log(f"✅ Lesson {i} ({lesson['title']}) has all required fields")
                    else:
                        self.log(f"❌ Lesson {i} missing fields: {missing_fields}")
                        return False
                
                # Check quiz info
                quiz_info = module_data.get('quiz_info', {})
                if quiz_info:
                    self.log(f"✅ Quiz info available: {quiz_info.get('question_count', 0)} questions")
                
                return True
            else:
                self.log(f"❌ Expected 5 lessons, got {len(lessons)}")
                return False
        
        return False

    def test_lesson_content(self):
        """Test lesson content retrieval"""
        self.log("=== LESSON CONTENT TEST ===")
        
        # Test first lesson content
        success, lesson_data = self.run_test(
            "Get Lesson 1.1 Content",
            "GET",
            "academy/lessons/lesson_1_1",
            200
        )
        
        if success and lesson_data:
            lesson = lesson_data.get('lesson', {})
            if lesson:
                content = lesson.get('content', '')
                if content and len(content) > 100:  # Should have substantial content
                    self.log(f"✅ Lesson content loaded ({len(content)} characters)")
                    
                    # Check for BULL mascot presence
                    if 'BULL' in content:
                        self.log("✅ BULL mascot found in content")
                    
                    # Check for markdown formatting
                    if '#' in content and '**' in content:
                        self.log("✅ Markdown formatting detected")
                    
                    return True
                else:
                    self.log("❌ Lesson content too short or missing")
            else:
                self.log("❌ No lesson data in response")
        
        return False

    def test_lesson_completion(self):
        """Test lesson completion functionality"""
        self.log("=== LESSON COMPLETION TEST ===")
        
        # Complete first lesson
        success, completion_data = self.run_test(
            "Complete Lesson 1.1",
            "POST",
            "academy/lessons/lesson_1_1/complete",
            200,
            {}
        )
        
        if success and completion_data:
            xp_earned = completion_data.get('xp_earned', 0)
            badges_earned = completion_data.get('badges_earned', [])
            
            if xp_earned > 0:
                self.log(f"✅ XP earned: {xp_earned}")
            
            if badges_earned:
                self.log(f"✅ Badges earned: {badges_earned}")
            
            return True
        
        return False

    def test_quiz_functionality(self):
        """Test quiz retrieval and submission"""
        self.log("=== QUIZ FUNCTIONALITY TEST ===")
        
        # Get quiz for module 1
        success, quiz_data = self.run_test(
            "Get Module 1 Quiz",
            "GET",
            "academy/quiz/module_1",
            200
        )
        
        if success and quiz_data:
            questions = quiz_data.get('questions', [])
            self.log(f"✅ Quiz loaded with {len(questions)} questions")
            
            if len(questions) == 8:  # Expected 8 questions
                self.log("✅ Correct number of quiz questions (8)")
                
                # Prepare quiz answers (all correct for testing)
                answers = {}
                for question in questions:
                    question_id = question.get('id')
                    correct_answer = question.get('correct_answer', 0)
                    if question_id is not None:
                        answers[question_id] = correct_answer
                
                # Submit quiz
                quiz_submission = {
                    "lesson_id": "module_1",
                    "answers": answers
                }
                
                success_submit, result_data = self.run_test(
                    "Submit Module 1 Quiz",
                    "POST",
                    "academy/quiz/module_1/submit",
                    200,
                    quiz_submission
                )
                
                if success_submit and result_data:
                    score = result_data.get('score', 0)
                    total = result_data.get('total', 0)
                    percentage = result_data.get('percentage', 0)
                    passed = result_data.get('passed', False)
                    
                    self.log(f"✅ Quiz submitted: {score}/{total} ({percentage}%) - Passed: {passed}")
                    return True
                
            else:
                self.log(f"❌ Expected 8 questions, got {len(questions)}")
        
        return False

    def test_badges_system(self):
        """Test badges retrieval"""
        self.log("=== BADGES SYSTEM TEST ===")
        
        success, badges_data = self.run_test(
            "Get User Badges",
            "GET",
            "academy/badges",
            200
        )
        
        if success and badges_data:
            badges = badges_data if isinstance(badges_data, list) else []
            self.log(f"✅ Badges system loaded with {len(badges)} badges")
            
            # Check for expected badges
            unlocked_badges = [badge for badge in badges if badge.get('unlocked', False)]
            self.log(f"✅ User has {len(unlocked_badges)} unlocked badges")
            
            return True
        
        return False

    def test_leaderboard(self):
        """Test leaderboard functionality"""
        self.log("=== LEADERBOARD TEST ===")
        
        success, leaderboard_data = self.run_test(
            "Get Academy Leaderboard",
            "GET",
            "academy/leaderboard",
            200
        )
        
        if success and leaderboard_data:
            leaderboard = leaderboard_data.get('leaderboard', [])
            current_user_rank = leaderboard_data.get('current_user_rank')
            
            self.log(f"✅ Leaderboard loaded with {len(leaderboard)} users")
            
            if current_user_rank:
                self.log(f"✅ Current user rank: #{current_user_rank}")
            
            return True
        
        return False

    def test_academy_stats(self):
        """Test academy statistics"""
        self.log("=== ACADEMY STATS TEST ===")
        
        # Re-fetch modules to get updated stats
        success, modules_data = self.run_test(
            "Get Updated Academy Stats",
            "GET",
            "academy/modules",
            200
        )
        
        if success and modules_data:
            total_xp = modules_data.get('total_xp', 0)
            streak_days = modules_data.get('streak_days', 0)
            badges_count = len(modules_data.get('badges', []))
            
            self.log(f"✅ Academy stats - XP: {total_xp}, Streak: {streak_days} days, Badges: {badges_count}")
            
            return True
        
        return False

    def run_all_tests(self):
        """Run all Academy test suites"""
        self.log("🚀 Starting BULL SAGE Academy Tests")
        self.log(f"Testing against: {self.base_url}")
        
        # Login first
        if not self.test_login():
            self.log("❌ Login failed, stopping tests")
            return False
        
        # Run Academy tests
        tests = [
            self.test_academy_modules,
            self.test_module_details,
            self.test_lesson_content,
            self.test_lesson_completion,
            self.test_quiz_functionality,
            self.test_badges_system,
            self.test_leaderboard,
            self.test_academy_stats
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log(f"❌ Test {test.__name__} failed with exception: {e}", "ERROR")
        
        return True

    def print_summary(self):
        """Print test summary"""
        self.log("=" * 50)
        self.log("🏁 ACADEMY TEST SUMMARY")
        self.log(f"Total tests: {self.tests_run}")
        self.log(f"Passed: {self.tests_passed}")
        self.log(f"Failed: {len(self.failed_tests)}")
        
        if self.tests_run > 0:
            success_rate = (self.tests_passed / self.tests_run) * 100
            self.log(f"Success rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            self.log("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                error_msg = test.get('error', f"Expected {test.get('expected')}, got {test.get('actual')}")
                self.log(f"  - {test['test']}: {error_msg}")
        
        return len(self.failed_tests) == 0

def main():
    """Main test execution"""
    tester = AcademyTester()
    
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