"""
Test script for requirement parser.

Run with: python -m src.parser.test_parser
"""

import sys
import codecs
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.parser import RequirementParser
from src.models import ActionType, Severity


# ============================================================================
# Test Cases
# ============================================================================

def test_parse_order_flow():
    """Test parsing Order Flow Requirements."""
    print("Testing Order Flow Requirements parsing...")
    
    parser = RequirementParser()
    suite = parser.parse_file("../AIInputData/Order Flow Requirements.txt")
    
    assert suite.name == "Order Flow"
    assert len(suite.global_requirements) > 0
    assert len(suite.steps) == 8
    
    # Check first step
    step1 = suite.steps[0]
    assert step1.step_number == 1
    assert "main page" in step1.description.lower()
    assert len(step1.verifications) > 0
    assert len(step1.actions) > 0
    
    # Check step 2 has click action
    step2 = suite.steps[1]
    assert step2.step_number == 2
    click_actions = [a for a in step2.actions if a.type == ActionType.CLICK]
    assert len(click_actions) > 0
    
    print(f"✅ Parsed {len(suite.steps)} steps")
    print(f"✅ Found {len(suite.global_requirements)} global requirements")
    print(f"✅ Step 1 has {len(step1.verifications)} verifications")
    print(f"✅ Step 2 has {len(step2.actions)} actions")


def test_parse_registration_flow():
    """Test parsing Registration Flow Requirements."""
    print("\nTesting Registration Flow Requirements parsing...")
    
    parser = RequirementParser()
    suite = parser.parse_file("../AIInputData/Registration Flow Requirements.txt")
    
    assert suite.name == "Registration Flow"
    assert len(suite.steps) == 12
    
    # Check form filling step
    step5 = suite.steps[4]  # Step 5
    assert step5.step_number == 5
    type_actions = [a for a in step5.actions if a.type == ActionType.TYPE]
    assert len(type_actions) > 0
    
    # Check select actions
    select_actions = [a for a in step5.actions if a.type == ActionType.SELECT]
    assert len(select_actions) > 0
    
    print(f"✅ Parsed {len(suite.steps)} steps")
    print(f"✅ Step 5 has {len(type_actions)} type actions")
    print(f"✅ Step 5 has {len(select_actions)} select actions")


def test_parse_login_flow():
    """Test parsing Login Flow Requirements."""
    print("\nTesting Login Flow Requirements parsing...")
    
    parser = RequirementParser()
    suite = parser.parse_file("../AIInputData/Login Flow Requirements.txt")
    
    assert suite.name == "Login Flow"
    assert len(suite.steps) == 13
    
    # Check login form verification
    step3 = suite.steps[2]  # Step 3
    assert step3.step_number == 3
    assert len(step3.verifications) > 0
    
    # Check invalid credentials test
    step6 = suite.steps[5]  # Step 6
    assert step6.step_number == 6
    type_actions = [a for a in step6.actions if a.type == ActionType.TYPE]
    assert len(type_actions) >= 2  # Username and password
    
    print(f"✅ Parsed {len(suite.steps)} steps")
    print(f"✅ Step 3 has {len(step3.verifications)} verifications")
    print(f"✅ Step 6 has {len(type_actions)} type actions")


def test_global_requirements():
    """Test global requirements extraction."""
    print("\nTesting global requirements extraction...")
    
    parser = RequirementParser()
    suite = parser.parse_file("../AIInputData/Order Flow Requirements.txt")
    
    assert len(suite.global_requirements) > 0
    
    # Check that global requirements are verifications
    for req in suite.global_requirements:
        assert req.text is not None
        assert len(req.text) > 0
    
    print(f"✅ Extracted {len(suite.global_requirements)} global requirements")
    for i, req in enumerate(suite.global_requirements[:3], 1):
        print(f"   {i}. {req.text[:60]}...")


def test_action_extraction():
    """Test action extraction patterns."""
    print("\nTesting action extraction...")
    
    parser = RequirementParser()
    
    # Test click action
    text = "Click on 'Submit' button"
    actions = parser._extract_actions(text)
    assert len(actions) > 0
    assert actions[0].type == ActionType.CLICK
    assert "Submit" in actions[0].target
    
    # Test type action with field context
    text = "Email: Enter 'test@example.com'"
    actions = parser._extract_actions(text)
    assert len(actions) > 0
    assert actions[0].type == ActionType.TYPE
    assert actions[0].value == "test@example.com"
    assert "Email" in actions[0].target
    
    # Test type action with explicit field
    text = "Enter 'test@example.com' in the email field"
    actions = parser._extract_actions(text)
    assert len(actions) > 0
    assert actions[0].type == ActionType.TYPE
    assert actions[0].value == "test@example.com"
    
    # Test select action with field context
    text = "Country: Select 'USA'"
    actions = parser._extract_actions(text)
    assert len(actions) > 0
    assert actions[0].type == ActionType.SELECT
    assert actions[0].value == "USA"
    assert "Country" in actions[0].target
    
    # Test select action with explicit field
    text = "Select 'USA' from the country dropdown"
    actions = parser._extract_actions(text)
    assert len(actions) > 0
    assert actions[0].type == ActionType.SELECT
    assert actions[0].value == "USA"
    
    print("✅ Click action extraction works")
    print("✅ Type action extraction works")
    print("✅ Select action extraction works")


def test_verification_extraction():
    """Test verification extraction patterns."""
    print("\nTesting verification extraction...")
    
    parser = RequirementParser()
    
    # Test "Make sure" pattern
    text = "Make sure that the page says 'Welcome'"
    verifications = parser._extract_verifications(text)
    assert len(verifications) > 0
    assert "Welcome" in verifications[0].text
    
    # Test "Verify" pattern
    text = "Verify that the form is visible"
    verifications = parser._extract_verifications(text)
    assert len(verifications) > 0
    assert "form is visible" in verifications[0].text
    
    print("✅ 'Make sure' pattern extraction works")
    print("✅ 'Verify' pattern extraction works")


def test_expected_page_extraction():
    """Test expected page extraction."""
    print("\nTesting expected page extraction...")
    
    parser = RequirementParser()
    
    text = "Make sure the browser goes to a page called 'Step 1: Select a Product'"
    expected_page = parser._extract_expected_page(text)
    assert expected_page == "Step 1: Select a Product"
    
    text = "Verify that you are on the 'Login' page"
    expected_page = parser._extract_expected_page(text)
    assert expected_page == "Login"
    
    print("✅ Expected page extraction works")


def test_step_details():
    """Test detailed step parsing."""
    print("\nTesting detailed step parsing...")
    
    parser = RequirementParser()
    suite = parser.parse_file("../AIInputData/Order Flow Requirements.txt")
    
    # Check step 3 has expected page
    step3 = suite.steps[2]  # Step 3
    assert step3.expected_page is not None
    assert "Step 1" in step3.expected_page
    
    # Check step 4 has actions
    step4 = suite.steps[3]  # Step 4
    assert len(step4.actions) > 0
    
    # Check step 5 has verifications
    step5 = suite.steps[4]  # Step 5
    assert len(step5.verifications) > 0
    
    print(f"✅ Step 3 expected page: {step3.expected_page}")
    print(f"✅ Step 4 has {len(step4.actions)} actions")
    print(f"✅ Step 5 has {len(step5.verifications)} verifications")


def run_all_tests():
    """Run all parser tests."""
    print("=" * 60)
    print("Requirement Parser Test Suite")
    print("=" * 60)
    
    try:
        test_parse_order_flow()
        test_parse_registration_flow()
        test_parse_login_flow()
        test_global_requirements()
        test_action_extraction()
        test_verification_extraction()
        test_expected_page_extraction()
        test_step_details()
        
        print("\n" + "=" * 60)
        print("✅ All parser tests passed!")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

