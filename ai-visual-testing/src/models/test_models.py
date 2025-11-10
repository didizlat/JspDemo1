"""
Simple test script to verify data models are working correctly.

Run with: python -m src.models.test_models
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

from src.models import (
    StepStatus,
    ActionType,
    VerdictDecision,
    Severity,
    Verification,
    Action,
    Issue,
    VerificationResult,
    TestStep,
    StepResult,
    TestSuite,
    TestResults,
    Verdict,
)


def test_basic_models():
    """Test basic model creation."""
    print("Testing basic models...")
    
    # Test Verification
    verification = Verification(
        text="Page should display welcome message",
        severity=Severity.MAJOR
    )
    assert verification.text == "Page should display welcome message"
    assert verification.severity == Severity.MAJOR
    print("✅ Verification model works")
    
    # Test Action
    action = Action(
        type=ActionType.CLICK,
        target="Submit Button",
        description="Click the submit button"
    )
    assert action.type == ActionType.CLICK
    assert action.target == "Submit Button"
    print("✅ Action model works")
    
    # Test Issue
    issue = Issue(
        severity=Severity.CRITICAL,
        description="Button not found on page",
        step_number=1
    )
    assert issue.severity == Severity.CRITICAL
    assert issue.step_number == 1
    print("✅ Issue model works")
    
    # Test VerificationResult
    result = VerificationResult(
        requirement="Page should load",
        passed=True,
        confidence=95.5,
        ai_reasoning="Page loaded successfully"
    )
    assert result.passed is True
    assert result.confidence == 95.5
    print("✅ VerificationResult model works")
    
    # Test TestStep
    step = TestStep(
        step_number=1,
        description="Navigate to homepage",
        verifications=[verification],
        actions=[action]
    )
    assert step.step_number == 1
    assert len(step.verifications) == 1
    assert len(step.actions) == 1
    print("✅ TestStep model works")
    
    # Test StepResult
    step_result = StepResult(
        step_number=1,
        description="Navigate to homepage",
        status=StepStatus.PASSED,
        verifications=[result]
    )
    assert step_result.status == StepStatus.PASSED
    assert len(step_result.verifications) == 1
    print("✅ StepResult model works")
    
    # Test TestSuite
    suite = TestSuite(
        name="Homepage Test",
        steps=[step],
        description="Test homepage functionality"
    )
    assert suite.name == "Homepage Test"
    assert len(suite.steps) == 1
    print("✅ TestSuite model works")
    
    # Test TestResults
    test_results = TestResults(
        test_suite_name="Homepage Test",
        step_results=[step_result]
    )
    assert test_results.test_suite_name == "Homepage Test"
    assert test_results.total_steps() == 1
    assert test_results.passed_steps() == 1
    assert test_results.failed_steps() == 0
    print("✅ TestResults model works")
    
    # Test Verdict
    verdict = Verdict(
        decision=VerdictDecision.PASS,
        confidence=90.0,
        reasoning="All tests passed successfully"
    )
    assert verdict.is_pass is True
    assert verdict.confidence == 90.0
    print("✅ Verdict model works")
    
    print("\n🎉 All basic model tests passed!")


def test_validation():
    """Test model validation."""
    print("\nTesting model validation...")
    
    # Test empty verification text
    try:
        Verification(text="")
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ Verification validation works (empty text)")
    
    # Test invalid confidence
    try:
        VerificationResult(
            requirement="Test",
            passed=True,
            confidence=150.0  # Invalid
        )
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ VerificationResult validation works (invalid confidence)")
    
    # Test invalid step number
    try:
        TestStep(step_number=0, description="Test")
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ TestStep validation works (invalid step number)")
    
    # Test empty test suite
    try:
        TestSuite(name="Test", steps=[])
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ TestSuite validation works (empty steps)")
    
    print("✅ All validation tests passed!")


def test_helper_methods():
    """Test helper methods on TestResults."""
    print("\nTesting helper methods...")
    
    # Create test results with multiple steps
    step1 = StepResult(
        step_number=1,
        description="Step 1",
        status=StepStatus.PASSED,
        verifications=[
            VerificationResult(
                requirement="Test 1",
                passed=True,
                confidence=95.0
            )
        ]
    )
    
    step2 = StepResult(
        step_number=2,
        description="Step 2",
        status=StepStatus.FAILED,
        verifications=[
            VerificationResult(
                requirement="Test 2",
                passed=False,
                confidence=30.0,
                issues=[
                    Issue(
                        severity=Severity.CRITICAL,
                        description="Critical issue found",
                        step_number=2
                    )
                ]
            )
        ],
        issues=[
            Issue(severity=Severity.MAJOR, description="Major issue", step_number=2)
        ]
    )
    
    step3 = StepResult(
        step_number=3,
        description="Step 3",
        status=StepStatus.WARNING,
        verifications=[
            VerificationResult(
                requirement="Test 3",
                passed=True,
                confidence=75.0
            )
        ],
        issues=[
            Issue(severity=Severity.MINOR, description="Minor issue", step_number=3)
        ]
    )
    
    results = TestResults(
        test_suite_name="Test Suite",
        step_results=[step1, step2, step3]
    )
    
    assert results.total_steps() == 3
    assert results.passed_steps() == 1
    assert results.failed_steps() == 1
    assert results.warning_steps() == 1
    assert results.count_issues(Severity.CRITICAL) == 1
    assert results.count_issues(Severity.MAJOR) == 1
    assert results.count_issues(Severity.MINOR) == 1
    assert 60.0 < results.average_confidence() < 70.0  # Should be around 66.67
    
    print("✅ All helper method tests passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("Data Models Test Suite")
    print("=" * 60)
    
    try:
        test_basic_models()
        test_validation()
        test_helper_methods()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

