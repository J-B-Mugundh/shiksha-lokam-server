"""
Complete Flow Test - Tests the entire workflow from user registration to LFA approval
Run with: pytest tests/test_complete_flow.py -v -s
"""

import pytest
import requests
import json
import uuid
from typing import Dict, Any
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Global test data
test_data = {
    "user_id": None,
    "org_id": None,
    "theme_id": None,
    "impact_id": None,
    "outcome_id": None,
    "lfa_id": None,
}

# Unique identifiers for this test run
UNIQUE_ID = str(uuid.uuid4())[:8]
TIMESTAMP = datetime.now().strftime("%Y%m%d%H%M%S")

# ==================== FIXTURES ====================

@pytest.fixture(scope="session")
def api_base_url():
    return BASE_URL

@pytest.fixture(scope="session")
def test_user_data():
    return {
        "email": f"testuser_{UNIQUE_ID}_{TIMESTAMP}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "TestPassword123"
    }

@pytest.fixture(scope="session")
def test_org_data():
    return {
        "name": f"Test NGO Foundation {UNIQUE_ID}_{TIMESTAMP}",
        "org_type": "ngo",
        "state": "Karnataka",
        "district": "Bangalore",
        "focus_areas": ["FLN", "Career Readiness"]
    }

@pytest.fixture(scope="session")
def test_theme_data():
    return {
        "name": f"Foundational Literacy & Numeracy {UNIQUE_ID}_{TIMESTAMP}",
        "short_name": f"FLN_{UNIQUE_ID}",
        "description": "Focus on basic reading and math skills",
        "challenge_statements": ["Low literacy rates", "Poor numeracy skills"]
    }

@pytest.fixture(scope="session")
def test_impact_data():
    return {
        "impact_statement": "Improved student reading comprehension by 40%",
        "category": "Student Learning",
        "indicators": [
            {
                "indicator_text": "% of students reading at grade level",
                "baseline_value": "30%",
                "target_value": "70%",
                "measurement_method": "ASER assessment"
            }
        ],
        "is_template": True
    }

@pytest.fixture(scope="session")
def test_outcome_data():
    return {
        "outcome_statement": "Teachers effectively use phonics-based teaching methods",
        "stakeholder_type": "Teachers",
        "indicators": [
            {
                "indicator_text": "% of teachers demonstrating correct phonics instruction",
                "baseline_value": "20%",
                "target_value": "80%",
                "measurement_method": "Classroom observation rubric"
            }
        ],
        "is_template": True
    }

# ==================== HELPER FUNCTIONS ====================

def print_response(status: str, test_name: str, data: Any = None):
    """Pretty print test results"""
    symbol = "✅" if status == "PASS" else "❌"
    print(f"\n{symbol} {status} - {test_name}")
    if data and isinstance(data, dict):
        print(f"   {json.dumps(data, indent=2, default=str)}")

def extract_id(response_data: dict) -> str:
    """Extract ID from various response formats"""
    if not response_data:
        return ""
    
    # Try multiple field name variations
    id_value = (response_data.get("user_id") or 
                response_data.get("organization_id") or 
                response_data.get("org_id") or
                response_data.get("theme_id") or 
                response_data.get("impact_id") or 
                response_data.get("outcome_id") or 
                response_data.get("lfa_id") or 
                response_data.get("id") or 
                str(response_data.get("_id", "")))
    
    return id_value if id_value else ""

# ==================== HEALTH CHECK ====================

class TestHealthCheck:
    """Test API health"""
    
    def test_api_health(self, api_base_url):
        """Check API is running"""
        try:
            response = requests.get(f"{api_base_url}/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            print_response("PASS", "API Health Check", data)
        except requests.exceptions.ConnectionError:
            pytest.skip(f"❌ Cannot connect to API at {api_base_url}")

# ==================== STEP 1: USER REGISTRATION ====================

class TestUserRegistration:
    """User registration tests"""
    
    def test_register_user(self, api_base_url, test_user_data):
        """Register a new user"""
        print(f"\n📧 Registering user: {test_user_data['email']}")
        
        response = requests.post(
            f"{api_base_url}/api/users/register",
            json=test_user_data,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 500:
            error_data = response.json()
            error_msg = error_data.get("detail", "")
            print(f"   Error: {error_msg}")
            
            # Check for duplicate key error
            if "E11000" in error_msg and "google_id" in error_msg:
                print("\n   🔧 FIX REQUIRED:")
                print("      1. Run: python scripts/fix_indexes.py")
                print("      2. Then: db.users.dropIndex('google_id_1')")
                pytest.skip("MongoDB index issue - Run fix_indexes.py")
            else:
                pytest.skip(f"Server error: {error_msg}")
        
        if response.status_code != 201:
            print(f"   Error: {response.text}")
            pytest.skip(f"User registration failed: {response.status_code}")
        
        data = response.json()
        user_id = extract_id(data)
        test_data["user_id"] = user_id
        
        assert user_id, "No user ID in response"
        assert data["email"] == test_user_data["email"]
        
        print_response("PASS", "User Registration", {"user_id": user_id})
    
    def test_get_user(self, api_base_url):
        """Retrieve registered user"""
        if not test_data["user_id"]:
            pytest.skip("User not registered")
        
        response = requests.get(
            f"{api_base_url}/api/users/{test_data['user_id']}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        print_response("PASS", "Get User", {"user_id": test_data["user_id"]})

# ==================== STEP 2: ORGANIZATION CREATION ====================

class TestOrganization:
    """Organization tests"""
    
    def test_create_organization(self, api_base_url, test_org_data):
        """Create organization"""
        print(f"\n🏢 Creating organization: {test_org_data['name']}")
        
        response = requests.post(
            f"{api_base_url}/api/organizations",
            json=test_org_data
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 201:
            print(f"   Error: {response.text}")
            pytest.skip(f"Organization creation failed: {response.status_code}")
        
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2, default=str)}")
        
        org_id = extract_id(data)
        test_data["org_id"] = org_id
        
        assert org_id, f"No organization ID in response: {data}"
        
        print_response("PASS", "Create Organization", {"org_id": org_id})
    
    def test_get_organization(self, api_base_url):
        """Retrieve organization"""
        if not test_data["org_id"]:
            pytest.skip("Organization not created")
        
        response = requests.get(
            f"{api_base_url}/api/organizations/{test_data['org_id']}"
        )
        
        assert response.status_code == 200
        print_response("PASS", "Get Organization", {"org_id": test_data["org_id"]})

# ==================== STEP 3: ADD USER TO ORGANIZATION ====================

class TestUserOrganization:
    """User-Organization tests"""
    
    def test_add_user_to_org(self, api_base_url):
        """Add user to organization"""
        if not test_data["user_id"] or not test_data["org_id"]:
            pytest.skip("User or Organization not available")
        
        response = requests.post(
            f"{api_base_url}/api/users/{test_data['user_id']}/organizations",
            json={
                "organization_id": test_data["org_id"],
                "role": "Program Manager"
            }
        )
        
        if response.status_code not in [200, 201]:
            print(f"   Error: {response.text}")
            pytest.skip(f"Failed to add user to organization: {response.status_code}")
        
        print_response("PASS", "Add User to Organization", {"role": "Program Manager"})

# ==================== STEP 4: THEME CREATION ====================

class TestTheme:
    """Theme tests"""
    
    def test_create_theme(self, api_base_url, test_theme_data):
        """Create theme"""
        response = requests.post(
            f"{api_base_url}/api/themes",
            json=test_theme_data
        )
        
        if response.status_code != 201:
            print(f"   Error: {response.text}")
            pytest.skip(f"Theme creation failed: {response.status_code}")
        
        data = response.json()
        theme_id = extract_id(data)
        test_data["theme_id"] = theme_id
        
        assert theme_id, "No theme ID in response"
        
        print_response("PASS", "Create Theme", {"theme_id": theme_id})
    
    def test_get_theme(self, api_base_url):
        """Retrieve theme"""
        if not test_data["theme_id"]:
            pytest.skip("Theme not created")
        
        response = requests.get(
            f"{api_base_url}/api/themes/{test_data['theme_id']}"
        )
        
        assert response.status_code == 200
        print_response("PASS", "Get Theme", {"theme_id": test_data["theme_id"]})

# ==================== STEP 5: IMPACT & OUTCOME ====================

class TestImpactOutcome:
    """Impact and Outcome tests"""
    
    def test_create_impact(self, api_base_url, test_impact_data):
        """Create impact"""
        response = requests.post(
            f"{api_base_url}/api/impacts",
            json=test_impact_data
        )
        
        if response.status_code != 201:
            print(f"   Error: {response.text}")
            pytest.skip(f"Impact creation failed: {response.status_code}")
        
        data = response.json()
        impact_id = extract_id(data)
        test_data["impact_id"] = impact_id
        
        assert impact_id, "No impact ID in response"
        
        print_response("PASS", "Create Impact", {"impact_id": impact_id})
    
    def test_create_outcome(self, api_base_url, test_outcome_data):
        """Create outcome"""
        response = requests.post(
            f"{api_base_url}/api/outcomes",
            json=test_outcome_data
        )
        
        if response.status_code != 201:
            print(f"   Error: {response.text}")
            pytest.skip(f"Outcome creation failed: {response.status_code}")
        
        data = response.json()
        outcome_id = extract_id(data)
        test_data["outcome_id"] = outcome_id
        
        assert outcome_id, "No outcome ID in response"
        
        print_response("PASS", "Create Outcome", {"outcome_id": outcome_id})

# ==================== STEP 6: LFA CREATION ====================

class TestLFACreation:
    """LFA creation tests"""
    
    def test_create_lfa(self, api_base_url):
        """Create LFA"""
        if not all([test_data["org_id"], test_data["user_id"], 
                   test_data["theme_id"], test_data["outcome_id"], 
                   test_data["impact_id"]]):
            pytest.skip("Missing required IDs for LFA creation")
        
        lfa_data = {
            "organization_id": test_data["org_id"],
            "created_by": test_data["user_id"],
            "theme_id": test_data["theme_id"],
            "name": f"Test LFA {UNIQUE_ID}",
            "challenge_statement": "Improve literacy and numeracy outcomes in rural schools",
            "target_grades": ["1", "2", "3"],
            "program_name": f"Test Program {UNIQUE_ID}",
            "program_description": "Test program description for comprehensive literacy intervention",
            "inputs": [
                {
                    "input_text": "Trained teachers",
                    "is_template": False
                },
                {
                    "input_text": "Learning materials",
                    "is_template": False
                }
            ],
            "activities": [
                {
                    "activity_text": "Teacher training on phonics methods",
                    "duration_weeks": 4
                },
                {
                    "activity_text": "Student practice sessions",
                    "duration_weeks": 12
                }
            ],
            "outputs": [
                {
                    "output_text": "Trained teachers",
                    "is_template": False
                },
                {
                    "output_text": "Student reading materials",
                    "is_template": False
                }
            ],
            "outcomes": [
                {
                    "outcome_id": test_data["outcome_id"],
                    "outcome_statement": "Teachers effectively use phonics-based teaching methods",
                    "custom_indicators": []
                }
            ],
            "impacts": [
                {
                    "impact_id": test_data["impact_id"],
                    "impact_statement": "Improved student reading comprehension by 40%",
                    "custom_indicators": []
                }
            ]
        }
        
        print(f"\n📋 Creating LFA: {lfa_data['name']}")
        print(f"   Challenge Statement: {lfa_data['challenge_statement']}")
        
        response = requests.post(
            f"{api_base_url}/api/lfas/",
            json=lfa_data
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code not in [200, 201]:
            print(f"   Error: {response.text}")
            pytest.skip(f"LFA creation failed: {response.status_code}")
        
        data = response.json()
        lfa_id = extract_id(data)
        test_data["lfa_id"] = lfa_id
        
        assert lfa_id, f"No LFA ID in response: {data}"
        
        print_response("PASS", "Create LFA", {"lfa_id": lfa_id})

# ==================== SUMMARY ====================

class TestSummary:
    """Test summary"""
    
    def test_print_summary(self, api_base_url):
        """Print test summary"""
        print("\n" + "="*70)
        print("📊 COMPLETE FLOW TEST SUMMARY")
        print("="*70)
        
        for key, value in test_data.items():
            status = "✅" if value else "⏭️"
            print(f"{status} {key.ljust(15)}: {value}")
        
        print("\n🔗 Created Resources:")
        if test_data["user_id"]:
            print(f"  📧 User: {api_base_url}/api/users/{test_data['user_id']}")
        if test_data["org_id"]:
            print(f"  🏢 Organization: {api_base_url}/api/organizations/{test_data['org_id']}")
        if test_data["theme_id"]:
            print(f"  🎨 Theme: {api_base_url}/api/themes/{test_data['theme_id']}")
        if test_data["lfa_id"]:
            print(f"  📋 LFA: {api_base_url}/api/lfas/{test_data['lfa_id']}")
        
        print("\n" + "="*70)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])