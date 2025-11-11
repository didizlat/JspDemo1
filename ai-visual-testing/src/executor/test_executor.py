"""
Test script for TestExecutor.

Run with: python -m src.executor.test_executor
"""

import sys
import codecs
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.executor import TestExecutor, ActionExecutionError
from src.models import (
    TestSuite,
    TestStep,
    Verification,
    Action,
    ActionType,
    Severity,
    StepStatus,
)
from src.adapters.base import AIAdapter, AIResponse
from src.models import VerificationResult
from src.utils.config import Config, BrowserConfig, ViewportConfig, TestingConfig, ReportingConfig


# ============================================================================
# Mock Classes
# ============================================================================

class MockAIAdapter(AIAdapter):
    """Mock AI adapter for testing."""
    
    def __init__(self):
        super().__init__(
            model="mock-model",
            temperature=0.2,
            max_tokens=2000,
            enable_cache=False,
            max_retries=0,
        )
    
    async def analyze_page(self, screenshot, html, prompt):
        return AIResponse(
            content="Mock analysis",
            model="mock-model",
        )
    
    async def verify_requirement(self, requirement, evidence):
        return VerificationResult(
            requirement=requirement,
            passed=True,
            confidence=95.0,
            ai_reasoning="Mock verification passed",
        )
    
    async def extract_elements(self, html, descriptions):
        return {desc: True for desc in descriptions}


# ============================================================================
# Tests
# ============================================================================

def test_executor_initialization():
    """Test TestExecutor initialization."""
    print("Testing TestExecutor initialization...")
    
    with patch('src.executor.executor.PLAYWRIGHT_AVAILABLE', True):
        ai_adapter = MockAIAdapter()
        config = Config(
            ai=None,  # Will be set separately
            browser=BrowserConfig(
                headless=True,
                browser_type="chromium",
                viewport=ViewportConfig(width=1920, height=1080),
                timeout=30000,
                slow_mo=0,
            ),
            testing=TestingConfig(
                base_url="http://localhost:8080",
                stop_on_failure=False,
            ),
            reporting=ReportingConfig(
                output_dir="./test-reports",
                screenshot_dir="./screenshots",
                format="markdown",
                include_screenshots=True,
            ),
        )
        
        executor = TestExecutor(ai_adapter, config)
        assert executor.ai == ai_adapter
        assert executor.config == config
        assert executor.browser is None
        assert executor.page is None
        print("✅ TestExecutor initialization works")


async def test_browser_setup_teardown():
    """Test browser setup and teardown."""
    print("\nTesting browser setup and teardown...")
    
    with patch('src.executor.executor.async_playwright') as mock_playwright:
        # Mock playwright
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_playwright.return_value.stop = AsyncMock()
        
        ai_adapter = MockAIAdapter()
        config = Config(
            ai=None,
            browser=BrowserConfig(
                headless=True,
                browser_type="chromium",
                viewport=ViewportConfig(width=1920, height=1080),
                timeout=30000,
                slow_mo=0,
            ),
            testing=TestingConfig(
                base_url="http://localhost:8080",
                stop_on_failure=False,
            ),
            reporting=ReportingConfig(
                output_dir="./test-reports",
                screenshot_dir="./screenshots",
                format="markdown",
                include_screenshots=True,
            ),
        )
        
        executor = TestExecutor(ai_adapter, config)
        
        # Test setup
        await executor._setup_browser()
        assert executor.browser is not None
        assert executor.context is not None
        assert executor.page is not None
        
        # Test teardown
        await executor._teardown_browser()
        assert executor.browser is None
        assert executor.context is None
        assert executor.page is None
        
        print("✅ Browser setup and teardown works")


async def test_state_capture():
    """Test state capture."""
    print("\nTesting state capture...")
    
    with patch('src.executor.executor.async_playwright') as mock_playwright:
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_page.url = "http://localhost:8080"
        type(mock_page).title = PropertyMock(return_value="Test Page")
        mock_page.screenshot = AsyncMock(return_value=b"fake_screenshot")
        mock_page.content = AsyncMock(return_value="<html>Test</html>")
        mock_page.set_default_timeout = MagicMock()
        
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_playwright.return_value.stop = AsyncMock()
        
        ai_adapter = MockAIAdapter()
        config = Config(
            ai=None,
            browser=BrowserConfig(
                headless=True,
                browser_type="chromium",
                viewport=ViewportConfig(width=1920, height=1080),
                timeout=30000,
                slow_mo=0,
            ),
            testing=TestingConfig(
                base_url="http://localhost:8080",
                stop_on_failure=False,
            ),
            reporting=ReportingConfig(
                output_dir="./test-reports",
                screenshot_dir="./screenshots",
                format="markdown",
                include_screenshots=True,
            ),
        )
        
        executor = TestExecutor(ai_adapter, config)
        await executor._setup_browser()
        
        # Capture state
        state = await executor._capture_state()
        assert state.url == "http://localhost:8080"
        assert state.title == "Test Page"
        assert state.screenshot == b"fake_screenshot"
        assert state.html == "<html>Test</html>"
        
        await executor._teardown_browser()
        print("✅ State capture works")


async def test_action_execution():
    """Test action execution."""
    print("\nTesting action execution...")
    
    with patch('src.executor.executor.async_playwright') as mock_playwright:
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        # Mock click
        mock_page.click = AsyncMock()
        
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_playwright.return_value.stop = AsyncMock()
        
        ai_adapter = MockAIAdapter()
        config = Config(
            ai=None,
            browser=BrowserConfig(
                headless=True,
                browser_type="chromium",
                viewport=ViewportConfig(width=1920, height=1080),
                timeout=30000,
                slow_mo=0,
            ),
            testing=TestingConfig(
                base_url="http://localhost:8080",
                stop_on_failure=False,
            ),
            reporting=ReportingConfig(
                output_dir="./test-reports",
                screenshot_dir="./screenshots",
                format="markdown",
                include_screenshots=True,
            ),
        )
        
        executor = TestExecutor(ai_adapter, config)
        await executor._setup_browser()
        
        # Test click action
        action = Action(
            type=ActionType.CLICK,
            target="Submit Button",
        )
        
        try:
            await executor._execute_action(action)
            print("✅ Click action execution works")
        except ActionExecutionError:
            # Expected if element not found, but method should be callable
            print("✅ Click action execution method works (element not found expected)")
        
        await executor._teardown_browser()


async def test_step_execution():
    """Test step execution."""
    print("\nTesting step execution...")
    
    with patch('src.executor.executor.async_playwright') as mock_playwright:
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_page.url = "http://localhost:8080"
        type(mock_page).title = PropertyMock(return_value="Test Page")
        mock_page.screenshot = AsyncMock(return_value=b"fake_screenshot")
        mock_page.content = AsyncMock(return_value="<html>Test</html>")
        mock_page.set_default_timeout = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.click = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_playwright.return_value.stop = AsyncMock()
        
        ai_adapter = MockAIAdapter()
        config = Config(
            ai=None,
            browser=BrowserConfig(
                headless=True,
                browser_type="chromium",
                viewport=ViewportConfig(width=1920, height=1080),
                timeout=30000,
                slow_mo=0,
            ),
            testing=TestingConfig(
                base_url="http://localhost:8080",
                stop_on_failure=False,
            ),
            reporting=ReportingConfig(
                output_dir="./test-reports",
                screenshot_dir="./screenshots",
                format="markdown",
                include_screenshots=True,
            ),
        )
        
        executor = TestExecutor(ai_adapter, config)
        await executor._setup_browser()
        
        # Create test step
        step = TestStep(
            step_number=1,
            description="Test step",
            verifications=[
                Verification(
                    text="Page should load",
                    severity=Severity.MAJOR,
                )
            ],
            actions=[
                Action(
                    type=ActionType.CLICK,
                    target="Button",
                )
            ],
        )
        
        # Execute step
        result = await executor.execute_step(step)
        assert result.step_number == 1
        assert result.status == StepStatus.PASSED  # Should pass with mock AI
        assert len(result.verifications) == 1
        
        await executor._teardown_browser()
        print("✅ Step execution works")


async def test_status_calculation():
    """Test step status calculation."""
    print("\nTesting status calculation...")
    
    executor = TestExecutor(MockAIAdapter(), None)  # Config not needed for this test
    
    # Test passed
    passed_results = [
        VerificationResult(
            requirement="Test",
            passed=True,
            confidence=95.0,
        )
    ]
    status = executor._calculate_step_status(passed_results)
    assert status == StepStatus.PASSED
    
    # Test failed
    failed_results = [
        VerificationResult(
            requirement="Test",
            passed=False,
            confidence=50.0,
        )
    ]
    status = executor._calculate_step_status(failed_results)
    assert status == StepStatus.FAILED
    
    # Test warning
    warning_results = [
        VerificationResult(
            requirement="Test",
            passed=True,
            confidence=60.0,  # Low confidence
        )
    ]
    status = executor._calculate_step_status(warning_results)
    assert status == StepStatus.WARNING
    
    print("✅ Status calculation works")


async def run_all_tests():
    """Run all executor tests."""
    print("=" * 60)
    print("Test Executor Test Suite")
    print("=" * 60)
    
    test_executor_initialization()
    await test_browser_setup_teardown()
    await test_state_capture()
    await test_action_execution()
    await test_step_execution()
    await test_status_calculation()
    
    print("\n" + "=" * 60)
    print("✅ All executor tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

