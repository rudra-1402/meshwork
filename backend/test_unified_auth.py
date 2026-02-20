"""
Test Script for Unified Authentication Endpoints

Run Flask server first: python run.py
Then run this script: python test_unified_auth.py
"""

import requests
import json

BASE_URL = "http://localhost:5000/api/auth"

def print_response(title, response):
    """Pretty print response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))
    print(f"{'='*60}\n")


def test_validate_email():
    """Test email validation endpoint"""
    print("\n🔍 Testing Email Validation...")
    
    # Test 1: Valid student email
    response = requests.post(
        f"{BASE_URL}/validate-email",
        json={"email": "student@college.edu"},
        headers={"Content-Type": "application/json"}
    )
    print_response("Test 1: Valid Student Email", response)
    
    # Test 2: Valid personnel email
    response = requests.post(
        f"{BASE_URL}/validate-email",
        json={"email": "faculty@college.edu"},
        headers={"Content-Type": "application/json"}
    )
    print_response("Test 2: Valid Personnel Email", response)
    
    # Test 3: Invalid domain
    response = requests.post(
        f"{BASE_URL}/validate-email",
        json={"email": "test@invalid.com"},
        headers={"Content-Type": "application/json"}
    )
    print_response("Test 3: Invalid Domain", response)
    
    # Test 4: Missing email
    response = requests.post(
        f"{BASE_URL}/validate-email",
        json={},
        headers={"Content-Type": "application/json"}
    )
    print_response("Test 4: Missing Email", response)


def test_signup():
    """Test signup endpoint"""
    print("\n📝 Testing Signup...")
    
    # Test 1: Student signup
    response = requests.post(
        f"{BASE_URL}/signup",
        json={
            "user_type": "student",
            "email": "newstudent@college.edu",
            "password": "TestPassword123!",
            "username": "newstudent",
            "first_name": "John",
            "last_name": "Doe",
            "college_id": 1
        },
        headers={"Content-Type": "application/json"}
    )
    print_response("Test 1: Student Signup", response)
    
    # Test 2: Personnel signup
    response = requests.post(
        f"{BASE_URL}/signup",
        json={
            "user_type": "personnel",
            "email": "newfaculty@college.edu",
            "password": "TestPassword123!",
            "first_name": "Jane",
            "last_name": "Smith",
            "role": "faculty",
            "college_id": 1
        },
        headers={"Content-Type": "application/json"}
    )
    print_response("Test 2: Personnel Signup", response)
    
    # Test 3: Missing required field
    response = requests.post(
        f"{BASE_URL}/signup",
        json={
            "user_type": "student",
            "email": "test@college.edu",
            "password": "password"
            # Missing other fields
        },
        headers={"Content-Type": "application/json"}
    )
    print_response("Test 3: Missing Required Fields", response)


def test_login():
    """Test login endpoint"""
    print("\n🔐 Testing Login...")
    
    # Test 1: Valid student login
    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": "newstudent@college.edu",
            "password": "TestPassword123!"
        },
        headers={"Content-Type": "application/json"}
    )
    print_response("Test 1: Student Login", response)
    
    # Test 2: Valid personnel login
    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": "newfaculty@college.edu",
            "password": "TestPassword123!"
        },
        headers={"Content-Type": "application/json"}
    )
    print_response("Test 2: Personnel Login", response)
    
    # Test 3: Invalid credentials
    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": "test@college.edu",
            "password": "wrongpassword"
        },
        headers={"Content-Type": "application/json"}
    )
    print_response("Test 3: Invalid Credentials", response)


def test_check_username():
    """Test username availability check"""
    print("\n👤 Testing Username Check...")
    
    # Test 1: Available username
    response = requests.post(
        f"{BASE_URL}/check-username",
        json={"username": "availableuser123"},
        headers={"Content-Type": "application/json"}
    )
    print_response("Test 1: Available Username", response)
    
    # Test 2: Taken username
    response = requests.post(
        f"{BASE_URL}/check-username",
        json={"username": "newstudent"},
        headers={"Content-Type": "application/json"}
    )
    print_response("Test 2: Taken Username", response)


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 UNIFIED AUTH API TESTS")
    print("="*60)
    
    try:
        # Test server connectivity
        response = requests.get("http://localhost:5000/api/health")
        if response.status_code != 200:
            print("❌ Server is not running. Please start Flask server first.")
            print("   Run: python run.py")
            return
        
        print("✅ Server is running!")
        
        # Run tests
        test_validate_email()
        test_check_username()
        
        # Note: Signup and login tests may fail if data already exists
        # Adjust test data as needed
        print("\n⚠️  Note: Signup tests may fail if test users already exist.")
        print("   You may need to use different email addresses or clean the database.\n")
        
        test_signup()
        test_login()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please start Flask server first.")
        print("   Run: python run.py")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    run_all_tests()
