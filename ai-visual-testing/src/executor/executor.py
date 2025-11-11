"""
Test Executor for AI-driven testing framework.

This module provides the TestExecutor class that uses Playwright for browser
automation and integrates with AI adapters for verification.
"""

import asyncio
import logging
import time
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = None
    Page = None
    BrowserContext = None
    PlaywrightTimeoutError = None

from src.models import (
    TestSuite,
    TestStep,
    TestResults,
    StepResult,
    StepStatus,
    Verification,
    VerificationResult,
    Action,
    ActionType,
    PageState,
    Issue,
    Severity,
)
from src.adapters.base import AIAdapter
from src.utils.config import Config


logger = logging.getLogger(__name__)


class ActionExecutionError(Exception):
    """Error executing an action."""
    pass


class TestExecutor:
    """
    Executes test suites using Playwright and AI verification.
    
    This class orchestrates browser automation, action execution, and
    AI-powered verification of test requirements.
    """
    
    def __init__(
        self,
        ai_adapter: AIAdapter,
        config: Config,
    ):
        """
        Initialize TestExecutor.
        
        Args:
            ai_adapter: AI adapter for verification
            config: Configuration object
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright not installed. Install with: pip install playwright && playwright install"
            )
        
        self.ai = ai_adapter
        self.config = config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        logger.info("Initialized TestExecutor")
    
    async def execute_test_suite(self, test_suite: TestSuite) -> TestResults:
        """
        Execute a complete test suite.
        
        Args:
            test_suite: TestSuite to execute
            
        Returns:
            TestResults object with execution results
        """
        start_time = time.time()
        
        logger.info(f"Starting test suite execution: {test_suite.name}")
        
        # Initialize browser
        await self._setup_browser()
        
        # Initialize results
        results = TestResults(test_suite_name=test_suite.name)
        
        try:
            # Navigate to base URL
            base_url = self.config.testing.base_url
            if base_url:
                logger.info(f"Navigating to base URL: {base_url}")
                await self.page.goto(base_url, wait_until="networkidle", timeout=self.config.browser.timeout)
                await asyncio.sleep(1)  # Allow page to settle
            
            # Execute each step
            for step in test_suite.steps:
                try:
                    step_result = await self.execute_step(step)
                    results.step_results.append(step_result)
                    
                    # Stop on failure if configured
                    if step_result.status == StepStatus.FAILED:
                        if self.config.testing.stop_on_failure:
                            logger.warning(f"Stopping execution due to failure in step {step.step_number}")
                            break
                except Exception as e:
                    logger.error(f"Error executing step {step.step_number}: {e}", exc_info=True)
                    # Create error result
                    error_result = StepResult(
                        step_number=step.step_number,
                        description=step.description,
                        status=StepStatus.FAILED,
                        error_message=str(e),
                    )
                    results.step_results.append(error_result)
                    
                    if self.config.testing.stop_on_failure:
                        break
        
        finally:
            # Cleanup browser
            await self._teardown_browser()
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        results.duration_ms = duration_ms
        
        logger.info(f"Test suite execution completed in {duration_ms}ms")
        return results
    
    async def execute_step(self, step: TestStep) -> StepResult:
        """
        Execute a single test step.
        
        Args:
            step: TestStep to execute
            
        Returns:
            StepResult with execution results
        """
        start_time = time.time()
        
        logger.info(f"Executing step {step.step_number}: {step.description}")
        
        try:
            # Execute actions
            for action in step.actions:
                try:
                    await self._execute_action(action)
                    # Wait after action
                    await asyncio.sleep(action.wait_after_ms / 1000.0)
                except Exception as e:
                    logger.error(f"Error executing action {action.type}: {e}")
                    raise ActionExecutionError(f"Failed to execute action: {action.description}") from e
            
            # Capture state after actions
            state_after = await self._capture_state()
            
            # Verify requirements with AI
            verification_results = []
            for verification in step.verifications:
                try:
                    result = await self._verify_with_ai(verification, state_after)
                    verification_results.append(result)
                except Exception as e:
                    logger.error(f"Error verifying requirement: {e}")
                    # Create failed verification result
                    failed_result = VerificationResult(
                        requirement=verification.text,
                        passed=False,
                        confidence=0.0,
                        ai_reasoning=f"Verification error: {str(e)}",
                    )
                    verification_results.append(failed_result)
            
            # Determine step status
            status = self._calculate_step_status(verification_results)
            
            # Extract issues
            issues = self._extract_issues(verification_results)
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            return StepResult(
                step_number=step.step_number,
                description=step.description,
                status=status,
                verifications=verification_results,
                screenshot=state_after.screenshot,
                html_snapshot=state_after.html,
                issues=issues,
                duration_ms=duration_ms,
            )
        
        except Exception as e:
            logger.error(f"Error executing step {step.step_number}: {e}", exc_info=True)
            return StepResult(
                step_number=step.step_number,
                description=step.description,
                status=StepStatus.FAILED,
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )
    
    async def _setup_browser(self):
        """Initialize Playwright browser."""
        logger.info("Setting up browser...")
        
        self.playwright = await async_playwright().start()
        
        # Get browser type from config
        browser_type_name = self.config.browser.browser_type.lower()
        
        if browser_type_name == "chromium":
            browser_type = self.playwright.chromium
        elif browser_type_name == "firefox":
            browser_type = self.playwright.firefox
        elif browser_type_name == "webkit":
            browser_type = self.playwright.webkit
        else:
            logger.warning(f"Unknown browser type: {browser_type_name}, using chromium")
            browser_type = self.playwright.chromium
        
        # Launch browser
        self.browser = await browser_type.launch(
            headless=self.config.browser.headless,
            slow_mo=self.config.browser.slow_mo,
        )
        
        # Create context with viewport
        viewport = self.config.browser.viewport
        self.context = await self.browser.new_context(
            viewport={
                "width": viewport.width,
                "height": viewport.height,
            },
        )
        
        # Create page
        self.page = await self.context.new_page()
        
        # Set timeout
        self.page.set_default_timeout(self.config.browser.timeout)
        
        logger.info(f"Browser setup complete ({browser_type_name}, headless={self.config.browser.headless})")
    
    async def _teardown_browser(self):
        """Cleanup browser resources."""
        logger.info("Tearing down browser...")
        
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Error during browser teardown: {e}")
        finally:
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
        
        logger.info("Browser teardown complete")
    
    async def _capture_state(self) -> PageState:
        """
        Capture current page state (screenshot, HTML, URL, title).
        
        Returns:
            PageState object
        """
        if not self.page:
            raise RuntimeError("Browser page not initialized")
        
        # Get URL and title
        url = self.page.url
        title = self.page.title
        
        # Capture screenshot
        screenshot = await self.page.screenshot(type="png", full_page=True)
        
        # Get HTML content
        html = await self.page.content()
        
        return PageState(
            url=url,
            title=title,
            screenshot=screenshot,
            html=html,
            timestamp=datetime.now(),
        )
    
    async def _execute_action(self, action: Action):
        """
        Execute an action on the page.
        
        Args:
            action: Action to execute
        """
        logger.debug(f"Executing action: {action.type} on {action.target}")
        
        if action.type == ActionType.CLICK:
            await self._click(action.target)
        elif action.type == ActionType.TYPE:
            await self._type(action.target, action.value)
        elif action.type == ActionType.FILL:
            await self._fill(action.target, action.value)
        elif action.type == ActionType.SELECT:
            await self._select(action.target, action.value)
        elif action.type == ActionType.CHECK:
            await self._check(action.target)
        elif action.type == ActionType.UNCHECK:
            await self._uncheck(action.target)
        elif action.type == ActionType.NAVIGATE:
            await self._navigate(action.target)
        elif action.type == ActionType.WAIT:
            await self._wait(action.target)
        elif action.type == ActionType.SCROLL:
            await self._scroll(action.target)
        else:
            raise ActionExecutionError(f"Unknown action type: {action.type}")
    
    async def _click(self, target: str):
        """Click on an element using multiple strategies."""
        strategies = [
            # Try exact text match
            lambda: self.page.click(f'text="{target}"'),
            # Try button with text
            lambda: self.page.click(f'button:has-text("{target}")'),
            # Try link with text
            lambda: self.page.click(f'a:has-text("{target}")'),
            # Try aria-label
            lambda: self.page.click(f'[aria-label="{target}"]'),
            # Try title attribute
            lambda: self.page.click(f'[title="{target}"]'),
            # Try partial text match
            lambda: self.page.click(f'text=/{target}/i'),
            # Try by ID if target looks like an ID
            lambda: self.page.click(f'#{target}') if target.startswith('#') else None,
            # Try by class if target looks like a class
            lambda: self.page.click(f'.{target}') if target.startswith('.') else None,
        ]
        
        last_error = None
        for strategy in strategies:
            try:
                result = strategy()
                if result is not None:
                    await result
                else:
                    continue
                logger.debug(f"Successfully clicked: {target}")
                return
            except Exception as e:
                last_error = e
                continue
        
        raise ActionExecutionError(f"Could not click element: {target}. Last error: {last_error}")
    
    async def _type(self, target: str, value: str):
        """Type text into a field."""
        # Find input field
        selectors = [
            f'input[name="{target}"]',
            f'input[placeholder*="{target}"]',
            f'input[id*="{target}"]',
            f'textarea[name="{target}"]',
            f'textarea[placeholder*="{target}"]',
            f'label:has-text("{target}") + input',
            f'label:has-text("{target}") + textarea',
        ]
        
        for selector in selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=self.config.browser.timeout)
                await element.fill(value)
                logger.debug(f"Successfully typed '{value}' into {target}")
                return
            except Exception:
                continue
        
        raise ActionExecutionError(f"Could not find input field: {target}")
    
    async def _fill(self, target: str, value: str):
        """Fill a form field (alias for type)."""
        await self._type(target, value)
    
    async def _select(self, target: str, value: str):
        """Select an option from a dropdown."""
        # Try to find select element
        selectors = [
            f'select[name="{target}"]',
            f'select[id*="{target}"]',
            f'label:has-text("{target}") + select',
        ]
        
        for selector in selectors:
            try:
                select_element = await self.page.wait_for_selector(selector, timeout=self.config.browser.timeout)
                await select_element.select_option(value)
                logger.debug(f"Successfully selected '{value}' from {target}")
                return
            except Exception:
                continue
        
        # Try clicking on option text directly
        try:
            await self.page.click(f'text="{value}"')
            logger.debug(f"Successfully clicked option '{value}'")
            return
        except Exception:
            pass
        
        raise ActionExecutionError(f"Could not select '{value}' from {target}")
    
    async def _check(self, target: str):
        """Check a checkbox or radio button."""
        selectors = [
            f'input[type="checkbox"][name="{target}"]',
            f'input[type="radio"][name="{target}"]',
            f'input[type="checkbox"][id*="{target}"]',
            f'input[type="radio"][id*="{target}"]',
            f'label:has-text("{target}") input[type="checkbox"]',
            f'label:has-text("{target}") input[type="radio"]',
        ]
        
        for selector in selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=self.config.browser.timeout)
                await element.check()
                logger.debug(f"Successfully checked: {target}")
                return
            except Exception:
                continue
        
        raise ActionExecutionError(f"Could not check element: {target}")
    
    async def _uncheck(self, target: str):
        """Uncheck a checkbox."""
        selectors = [
            f'input[type="checkbox"][name="{target}"]',
            f'input[type="checkbox"][id*="{target}"]',
            f'label:has-text("{target}") input[type="checkbox"]',
        ]
        
        for selector in selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=self.config.browser.timeout)
                await element.uncheck()
                logger.debug(f"Successfully unchecked: {target}")
                return
            except Exception:
                continue
        
        raise ActionExecutionError(f"Could not uncheck element: {target}")
    
    async def _navigate(self, target: str):
        """Navigate to a URL or page."""
        # If target looks like a URL, navigate directly
        if target.startswith("http://") or target.startswith("https://"):
            await self.page.goto(target, wait_until="networkidle", timeout=self.config.browser.timeout)
            logger.debug(f"Navigated to URL: {target}")
            return
        
        # Otherwise, try to click a link or button
        await self._click(target)
        # Wait for navigation (with timeout handling)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=self.config.browser.timeout)
        except PlaywrightTimeoutError:
            # Navigation may not have occurred, continue anyway
            logger.debug(f"Navigation wait timed out for {target}, continuing...")
        logger.debug(f"Navigated via click: {target}")
    
    async def _wait(self, target: str):
        """Wait for a condition or timeout."""
        try:
            # Try to parse as milliseconds
            wait_ms = int(target)
            await asyncio.sleep(wait_ms / 1000.0)
        except ValueError:
            # Try to wait for selector
            await self.page.wait_for_selector(target, timeout=self.config.browser.timeout)
    
    async def _scroll(self, target: str):
        """Scroll to an element or position."""
        if target.lower() == "top":
            await self.page.evaluate("window.scrollTo(0, 0)")
        elif target.lower() == "bottom":
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        else:
            # Try to scroll to element
            try:
                element = await self.page.wait_for_selector(target, timeout=self.config.browser.timeout)
                await element.scroll_into_view_if_needed()
            except Exception:
                raise ActionExecutionError(f"Could not scroll to: {target}")
    
    async def _verify_with_ai(
        self,
        verification: Verification,
        state: PageState,
    ) -> VerificationResult:
        """
        Verify a requirement using AI.
        
        Args:
            verification: Verification requirement
            state: Current page state
            
        Returns:
            VerificationResult
        """
        logger.debug(f"Verifying requirement: {verification.text}")
        
        evidence = {
            "screenshot": state.screenshot,
            "html": state.html,
            "url": state.url,
            "title": state.title,
        }
        
        result = await self.ai.verify_requirement(
            requirement=verification.text,
            evidence=evidence,
        )
        
        return result
    
    def _calculate_step_status(self, verification_results: List[VerificationResult]) -> StepStatus:
        """
        Calculate step status based on verification results.
        
        Args:
            verification_results: List of verification results
            
        Returns:
            StepStatus
        """
        if not verification_results:
            return StepStatus.PENDING
        
        # Check for failures
        failed = any(not vr.passed for vr in verification_results)
        if failed:
            # Any failure results in FAILED status
            return StepStatus.FAILED
        
        # Check for warnings (low confidence or minor issues)
        warnings = any(
            vr.confidence < 70.0 or any(issue.severity == Severity.MINOR for issue in vr.issues)
            for vr in verification_results
        )
        
        if warnings:
            return StepStatus.WARNING
        
        return StepStatus.PASSED
    
    def _extract_issues(self, verification_results: List[VerificationResult]) -> List[Issue]:
        """
        Extract all issues from verification results.
        
        Args:
            verification_results: List of verification results
            
        Returns:
            List of Issue objects
        """
        issues = []
        for vr in verification_results:
            if not vr.passed:
                for issue in vr.issues:
                    issues.append(issue)
        return issues

