"""
Data models for AI-driven testing framework.

This module defines all data structures used throughout the testing framework,
including test suites, steps, verifications, actions, results, and verdicts.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class StepStatus(str, Enum):
    """Status of a test step execution."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    PENDING = "pending"


class ActionType(str, Enum):
    """Type of action to perform on a web page."""
    CLICK = "click"
    TYPE = "type"
    FILL = "fill"
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"
    NAVIGATE = "navigate"
    WAIT = "wait"
    SCROLL = "scroll"


class VerdictDecision(str, Enum):
    """Final verdict decision for a test suite."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


class Severity(str, Enum):
    """Severity level of an issue or verification."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


# ============================================================================
# Core Data Models
# ============================================================================

@dataclass
class Verification:
    """A requirement that needs to be verified."""
    text: str
    severity: Severity = Severity.MAJOR
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate verification data."""
        # Validate text
        if not isinstance(self.text, str):
            raise ValueError(f"Verification text must be a string, got {type(self.text)}")
        if not self.text or not self.text.strip():
            raise ValueError("Verification text cannot be empty")
        self.text = self.text.strip()
        
        # Validate severity
        if not isinstance(self.severity, Severity):
            raise ValueError(f"Severity must be a Severity enum, got {type(self.severity)}")
        
        # Validate description
        if self.description is not None:
            if not isinstance(self.description, str):
                raise ValueError(f"Description must be a string, got {type(self.description)}")
            self.description = self.description.strip()
        else:
            self.description = self.text


@dataclass
class Action:
    """An action to perform during test execution."""
    type: ActionType
    target: str
    value: Optional[str] = None
    description: Optional[str] = None
    wait_after_ms: int = 500
    
    def __post_init__(self):
        """Validate action data."""
        # Validate type
        if not isinstance(self.type, ActionType):
            raise ValueError(f"Action type must be an ActionType enum, got {type(self.type)}")
        
        # Validate target
        if not isinstance(self.target, str):
            raise ValueError(f"Action target must be a string, got {type(self.target)}")
        if not self.target or not self.target.strip():
            raise ValueError("Action target cannot be empty")
        self.target = self.target.strip()
        
        # Validate value for actions that require it
        if self.type in [ActionType.TYPE, ActionType.FILL, ActionType.SELECT]:
            if self.value is None:
                raise ValueError(f"Action type {self.type.value} requires a value")
            if not isinstance(self.value, str):
                raise ValueError(f"Action value must be a string, got {type(self.value)}")
            if not self.value.strip():
                raise ValueError(f"Action value cannot be empty for type {self.type.value}")
            self.value = self.value.strip()
        
        # Validate wait_after_ms
        if not isinstance(self.wait_after_ms, int):
            raise ValueError(f"wait_after_ms must be an integer, got {type(self.wait_after_ms)}")
        if self.wait_after_ms < 0:
            raise ValueError(f"wait_after_ms must be >= 0, got {self.wait_after_ms}")
        if self.wait_after_ms > 60000:  # 60 seconds max
            raise ValueError(f"wait_after_ms must be <= 60000ms (60 seconds), got {self.wait_after_ms}")
        
        # Set default description
        if self.description is None:
            self.description = f"{self.type.value} {self.target}"
        elif not isinstance(self.description, str):
            raise ValueError(f"Description must be a string, got {type(self.description)}")
        else:
            self.description = self.description.strip()


@dataclass
class Issue:
    """An issue found during verification."""
    severity: Severity
    description: str
    step_number: Optional[int] = None
    element: Optional[str] = None
    screenshot_path: Optional[str] = None
    
    def __post_init__(self):
        """Validate issue data."""
        # Validate severity
        if not isinstance(self.severity, Severity):
            raise ValueError(f"Severity must be a Severity enum, got {type(self.severity)}")
        
        # Validate description
        if not isinstance(self.description, str):
            raise ValueError(f"Issue description must be a string, got {type(self.description)}")
        if not self.description or not self.description.strip():
            raise ValueError("Issue description cannot be empty")
        self.description = self.description.strip()
        
        # Validate step_number
        if self.step_number is not None:
            if not isinstance(self.step_number, int):
                raise ValueError(f"step_number must be an integer, got {type(self.step_number)}")
            if self.step_number < 1:
                raise ValueError(f"step_number must be >= 1, got {self.step_number}")
        
        # Validate element
        if self.element is not None:
            if not isinstance(self.element, str):
                raise ValueError(f"element must be a string, got {type(self.element)}")
            self.element = self.element.strip()
        
        # Validate screenshot_path
        if self.screenshot_path is not None:
            if not isinstance(self.screenshot_path, str):
                raise ValueError(f"screenshot_path must be a string, got {type(self.screenshot_path)}")
            self.screenshot_path = self.screenshot_path.strip()


@dataclass
class VerificationResult:
    """Result of a single verification."""
    requirement: str
    passed: bool
    confidence: float  # 0.0 to 100.0
    evidence: Dict[str, Any] = field(default_factory=dict)
    issues: List[Issue] = field(default_factory=list)
    ai_reasoning: Optional[str] = None
    duration_ms: Optional[int] = None
    
    def __post_init__(self):
        """Validate verification result."""
        # Validate requirement
        if not isinstance(self.requirement, str):
            raise ValueError(f"Requirement must be a string, got {type(self.requirement)}")
        if not self.requirement or not self.requirement.strip():
            raise ValueError("Requirement text cannot be empty")
        self.requirement = self.requirement.strip()
        
        # Validate passed
        if not isinstance(self.passed, bool):
            raise ValueError(f"passed must be a boolean, got {type(self.passed)}")
        
        # Validate confidence
        if not isinstance(self.confidence, (int, float)):
            raise ValueError(f"Confidence must be a number, got {type(self.confidence)}")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError(f"Confidence must be between 0.0 and 100.0, got {self.confidence}")
        self.confidence = float(self.confidence)
        
        # Validate evidence
        if not isinstance(self.evidence, dict):
            raise ValueError(f"evidence must be a dictionary, got {type(self.evidence)}")
        
        # Validate issues
        if not isinstance(self.issues, list):
            raise ValueError(f"issues must be a list, got {type(self.issues)}")
        for issue in self.issues:
            if not isinstance(issue, Issue):
                raise ValueError(f"All issues must be Issue instances, got {type(issue)}")
        
        # Validate ai_reasoning
        if self.ai_reasoning is not None:
            if not isinstance(self.ai_reasoning, str):
                raise ValueError(f"ai_reasoning must be a string, got {type(self.ai_reasoning)}")
            self.ai_reasoning = self.ai_reasoning.strip()
        
        # Validate duration_ms
        if self.duration_ms is not None:
            if not isinstance(self.duration_ms, int):
                raise ValueError(f"duration_ms must be an integer, got {type(self.duration_ms)}")
            if self.duration_ms < 0:
                raise ValueError(f"duration_ms must be >= 0, got {self.duration_ms}")


@dataclass
class PageState:
    """State of a web page at a point in time."""
    url: str
    title: str
    screenshot: bytes
    html: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate page state."""
        # Validate URL
        if not isinstance(self.url, str):
            raise ValueError(f"URL must be a string, got {type(self.url)}")
        if not self.url or not self.url.strip():
            raise ValueError("URL cannot be empty")
        self.url = self.url.strip()
        
        # Validate URL format
        try:
            parsed = urlparse(self.url)
            if not parsed.scheme:
                raise ValueError(f"URL must include a scheme (http:// or https://), got: {self.url}")
            if parsed.scheme not in ["http", "https"]:
                raise ValueError(f"URL scheme must be http or https, got: {parsed.scheme}")
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Invalid URL format: {self.url}") from e
        
        # Validate title
        if not isinstance(self.title, str):
            raise ValueError(f"Title must be a string, got {type(self.title)}")
        self.title = self.title.strip()
        
        # Validate screenshot
        if not isinstance(self.screenshot, bytes):
            raise ValueError(f"Screenshot must be bytes, got {type(self.screenshot)}")
        if len(self.screenshot) == 0:
            raise ValueError("Screenshot cannot be empty")
        
        # Validate HTML
        if not isinstance(self.html, str):
            raise ValueError(f"HTML must be a string, got {type(self.html)}")
        
        # Validate timestamp
        if not isinstance(self.timestamp, datetime):
            raise ValueError(f"timestamp must be a datetime, got {type(self.timestamp)}")


@dataclass
class TestStep:
    """A single step in a test suite."""
    step_number: int
    description: str
    verifications: List[Verification] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)
    expected_page: Optional[str] = None
    expected_elements: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate test step."""
        # Validate step_number
        if not isinstance(self.step_number, int):
            raise ValueError(f"step_number must be an integer, got {type(self.step_number)}")
        if self.step_number < 1:
            raise ValueError(f"Step number must be >= 1, got {self.step_number}")
        if self.step_number > 10000:
            raise ValueError(f"Step number must be <= 10000, got {self.step_number}")
        
        # Validate description
        if not isinstance(self.description, str):
            raise ValueError(f"Description must be a string, got {type(self.description)}")
        if not self.description or not self.description.strip():
            raise ValueError("Step description cannot be empty")
        self.description = self.description.strip()
        
        # Validate verifications
        if not isinstance(self.verifications, list):
            raise ValueError(f"verifications must be a list, got {type(self.verifications)}")
        for verification in self.verifications:
            if not isinstance(verification, Verification):
                raise ValueError(f"All verifications must be Verification instances, got {type(verification)}")
        
        # Validate actions
        if not isinstance(self.actions, list):
            raise ValueError(f"actions must be a list, got {type(self.actions)}")
        for action in self.actions:
            if not isinstance(action, Action):
                raise ValueError(f"All actions must be Action instances, got {type(action)}")
        
        # Validate expected_page
        if self.expected_page is not None:
            if not isinstance(self.expected_page, str):
                raise ValueError(f"expected_page must be a string, got {type(self.expected_page)}")
            self.expected_page = self.expected_page.strip()
        
        # Validate expected_elements
        if not isinstance(self.expected_elements, list):
            raise ValueError(f"expected_elements must be a list, got {type(self.expected_elements)}")
        for element in self.expected_elements:
            if not isinstance(element, str):
                raise ValueError(f"All expected_elements must be strings, got {type(element)}")
            if not element.strip():
                raise ValueError("Expected element cannot be empty")


@dataclass
class StepResult:
    """Result of executing a single test step."""
    step_number: int
    description: str
    status: StepStatus
    verifications: List[VerificationResult] = field(default_factory=list)
    screenshot: Optional[bytes] = None
    html_snapshot: Optional[str] = None
    issues: List[Issue] = field(default_factory=list)
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate step result."""
        # Validate step_number
        if not isinstance(self.step_number, int):
            raise ValueError(f"step_number must be an integer, got {type(self.step_number)}")
        if self.step_number < 1:
            raise ValueError(f"Step number must be >= 1, got {self.step_number}")
        
        # Validate description
        if not isinstance(self.description, str):
            raise ValueError(f"Description must be a string, got {type(self.description)}")
        if not self.description or not self.description.strip():
            raise ValueError("Step description cannot be empty")
        self.description = self.description.strip()
        
        # Validate status
        if not isinstance(self.status, StepStatus):
            raise ValueError(f"status must be a StepStatus enum, got {type(self.status)}")
        
        # Validate verifications
        if not isinstance(self.verifications, list):
            raise ValueError(f"verifications must be a list, got {type(self.verifications)}")
        for verification in self.verifications:
            if not isinstance(verification, VerificationResult):
                raise ValueError(
                    f"All verifications must be VerificationResult instances, got {type(verification)}"
                )
        
        # Validate screenshot
        if self.screenshot is not None:
            if not isinstance(self.screenshot, bytes):
                raise ValueError(f"screenshot must be bytes, got {type(self.screenshot)}")
            if len(self.screenshot) == 0:
                raise ValueError("Screenshot cannot be empty")
        
        # Validate html_snapshot
        if self.html_snapshot is not None:
            if not isinstance(self.html_snapshot, str):
                raise ValueError(f"html_snapshot must be a string, got {type(self.html_snapshot)}")
        
        # Validate issues
        if not isinstance(self.issues, list):
            raise ValueError(f"issues must be a list, got {type(self.issues)}")
        for issue in self.issues:
            if not isinstance(issue, Issue):
                raise ValueError(f"All issues must be Issue instances, got {type(issue)}")
        
        # Validate duration_ms
        if self.duration_ms is not None:
            if not isinstance(self.duration_ms, int):
                raise ValueError(f"duration_ms must be an integer, got {type(self.duration_ms)}")
            if self.duration_ms < 0:
                raise ValueError(f"duration_ms must be >= 0, got {self.duration_ms}")
        
        # Validate error_message
        if self.error_message is not None:
            if not isinstance(self.error_message, str):
                raise ValueError(f"error_message must be a string, got {type(self.error_message)}")
            self.error_message = self.error_message.strip()


@dataclass
class TestSuite:
    """A complete test suite with multiple steps."""
    name: str
    steps: List[TestStep] = field(default_factory=list)
    global_requirements: List[Verification] = field(default_factory=list)
    description: Optional[str] = None
    source_file: Optional[str] = None
    
    def __post_init__(self):
        """Validate test suite."""
        # Validate name
        if not isinstance(self.name, str):
            raise ValueError(f"name must be a string, got {type(self.name)}")
        if not self.name or not self.name.strip():
            raise ValueError("Test suite name cannot be empty")
        self.name = self.name.strip()
        
        # Validate steps
        if not isinstance(self.steps, list):
            raise ValueError(f"steps must be a list, got {type(self.steps)}")
        if not self.steps:
            raise ValueError("Test suite must have at least one step")
        
        # Validate step instances
        for step in self.steps:
            if not isinstance(step, TestStep):
                raise ValueError(f"All steps must be TestStep instances, got {type(step)}")
        
        # Validate step numbers are unique and sequential
        step_numbers = [step.step_number for step in self.steps]
        if len(step_numbers) != len(set(step_numbers)):
            duplicates = [num for num in step_numbers if step_numbers.count(num) > 1]
            raise ValueError(f"Step numbers must be unique. Duplicates found: {duplicates}")
        
        sorted_numbers = sorted(step_numbers)
        if step_numbers != sorted_numbers:
            raise ValueError(
                f"Step numbers must be sequential starting from 1. "
                f"Expected: {list(range(1, len(step_numbers) + 1))}, "
                f"Got: {step_numbers}"
            )
        
        # Validate global_requirements
        if not isinstance(self.global_requirements, list):
            raise ValueError(f"global_requirements must be a list, got {type(self.global_requirements)}")
        for requirement in self.global_requirements:
            if not isinstance(requirement, Verification):
                raise ValueError(
                    f"All global_requirements must be Verification instances, got {type(requirement)}"
                )
        
        # Validate description
        if self.description is not None:
            if not isinstance(self.description, str):
                raise ValueError(f"description must be a string, got {type(self.description)}")
            self.description = self.description.strip()
        
        # Validate source_file
        if self.source_file is not None:
            if not isinstance(self.source_file, str):
                raise ValueError(f"source_file must be a string, got {type(self.source_file)}")
            self.source_file = self.source_file.strip()


@dataclass
class TestResults:
    """Results from executing a test suite."""
    test_suite_name: str
    step_results: List[StepResult] = field(default_factory=list)
    verdict: Optional['Verdict'] = None
    execution_date: datetime = field(default_factory=datetime.now)
    duration_ms: Optional[int] = None
    ai_model: Optional[str] = None
    base_url: Optional[str] = None
    
    def __post_init__(self):
        """Validate test results."""
        # Validate test_suite_name
        if not isinstance(self.test_suite_name, str):
            raise ValueError(f"test_suite_name must be a string, got {type(self.test_suite_name)}")
        if not self.test_suite_name or not self.test_suite_name.strip():
            raise ValueError("Test suite name cannot be empty")
        self.test_suite_name = self.test_suite_name.strip()
        
        # Validate step_results
        if not isinstance(self.step_results, list):
            raise ValueError(f"step_results must be a list, got {type(self.step_results)}")
        for step_result in self.step_results:
            if not isinstance(step_result, StepResult):
                raise ValueError(
                    f"All step_results must be StepResult instances, got {type(step_result)}"
                )
        
        # Validate verdict
        if self.verdict is not None:
            if not isinstance(self.verdict, Verdict):
                raise ValueError(f"verdict must be a Verdict instance, got {type(self.verdict)}")
        
        # Validate execution_date
        if not isinstance(self.execution_date, datetime):
            raise ValueError(f"execution_date must be a datetime, got {type(self.execution_date)}")
        
        # Validate duration_ms
        if self.duration_ms is not None:
            if not isinstance(self.duration_ms, int):
                raise ValueError(f"duration_ms must be an integer, got {type(self.duration_ms)}")
            if self.duration_ms < 0:
                raise ValueError(f"duration_ms must be >= 0, got {self.duration_ms}")
        
        # Validate ai_model
        if self.ai_model is not None:
            if not isinstance(self.ai_model, str):
                raise ValueError(f"ai_model must be a string, got {type(self.ai_model)}")
            self.ai_model = self.ai_model.strip()
        
        # Validate base_url
        if self.base_url is not None:
            if not isinstance(self.base_url, str):
                raise ValueError(f"base_url must be a string, got {type(self.base_url)}")
            self.base_url = self.base_url.strip()
            # Validate URL format
            try:
                parsed = urlparse(self.base_url)
                if not parsed.scheme:
                    raise ValueError(f"base_url must include a scheme (http:// or https://), got: {self.base_url}")
                if parsed.scheme not in ["http", "https"]:
                    raise ValueError(f"base_url scheme must be http or https, got: {parsed.scheme}")
            except Exception as e:
                if isinstance(e, ValueError):
                    raise
                raise ValueError(f"Invalid base_url format: {self.base_url}") from e
    
    def count_failures(self, severity: Optional[Severity] = None) -> int:
        """Count failed verifications, optionally filtered by severity."""
        count = 0
        for step_result in self.step_results:
            for verification in step_result.verifications:
                if not verification.passed:
                    if severity is None or any(
                        issue.severity == severity for issue in verification.issues
                    ):
                        count += 1
        return count
    
    def count_issues(self, severity: Severity) -> int:
        """Count issues of a specific severity."""
        count = 0
        for step_result in self.step_results:
            # Count issues directly on step result
            count += sum(1 for issue in step_result.issues if issue.severity == severity)
            # Count issues from verifications
            for verification in step_result.verifications:
                count += sum(1 for issue in verification.issues if issue.severity == severity)
        return count
    
    def average_confidence(self) -> float:
        """Calculate average confidence across all verifications."""
        if not self.step_results:
            return 0.0
        
        confidences = []
        for step_result in self.step_results:
            for verification in step_result.verifications:
                confidences.append(verification.confidence)
        
        if not confidences:
            return 0.0
        
        return sum(confidences) / len(confidences)
    
    def total_steps(self) -> int:
        """Get total number of steps."""
        return len(self.step_results)
    
    def passed_steps(self) -> int:
        """Count passed steps."""
        return sum(1 for sr in self.step_results if sr.status == StepStatus.PASSED)
    
    def failed_steps(self) -> int:
        """Count failed steps."""
        return sum(1 for sr in self.step_results if sr.status == StepStatus.FAILED)
    
    def warning_steps(self) -> int:
        """Count steps with warnings."""
        return sum(1 for sr in self.step_results if sr.status == StepStatus.WARNING)
    
    def skipped_steps(self) -> int:
        """Count skipped steps."""
        return sum(1 for sr in self.step_results if sr.status == StepStatus.SKIPPED)
    
    def pending_steps(self) -> int:
        """Count pending steps."""
        return sum(1 for sr in self.step_results if sr.status == StepStatus.PENDING)
    
    def success_rate(self) -> float:
        """
        Calculate success rate as percentage of passed steps.
        
        Returns:
            Success rate as float between 0.0 and 100.0
        """
        total = self.total_steps()
        if total == 0:
            return 0.0
        return (self.passed_steps() / total) * 100.0
    
    def has_critical_issues(self) -> bool:
        """Check if test results contain any critical issues."""
        return self.count_issues(Severity.CRITICAL) > 0
    
    def has_major_issues(self) -> bool:
        """Check if test results contain any major issues."""
        return self.count_issues(Severity.MAJOR) > 0
    
    def get_all_issues(self) -> List[Issue]:
        """
        Get all issues from all step results and verifications.
        
        Returns:
            List of all Issue instances
        """
        issues = []
        for step_result in self.step_results:
            # Add issues directly on step result
            issues.extend(step_result.issues)
            # Add issues from verifications
            for verification in step_result.verifications:
                issues.extend(verification.issues)
        return issues
    
    def get_issues_by_severity(self, severity: Severity) -> List[Issue]:
        """
        Get all issues of a specific severity.
        
        Args:
            severity: Severity level to filter by
            
        Returns:
            List of Issue instances with the specified severity
        """
        return [issue for issue in self.get_all_issues() if issue.severity == severity]


@dataclass
class Verdict:
    """Final verdict for a test suite."""
    decision: VerdictDecision
    confidence: float  # 0.0 to 100.0
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate verdict."""
        # Validate decision
        if not isinstance(self.decision, VerdictDecision):
            raise ValueError(f"decision must be a VerdictDecision enum, got {type(self.decision)}")
        
        # Validate confidence
        if not isinstance(self.confidence, (int, float)):
            raise ValueError(f"Confidence must be a number, got {type(self.confidence)}")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError(f"Confidence must be between 0.0 and 100.0, got {self.confidence}")
        self.confidence = float(self.confidence)
        
        # Validate reasoning
        if not isinstance(self.reasoning, str):
            raise ValueError(f"reasoning must be a string, got {type(self.reasoning)}")
        if not self.reasoning or not self.reasoning.strip():
            raise ValueError("Verdict reasoning cannot be empty")
        self.reasoning = self.reasoning.strip()
        
        # Validate timestamp
        if not isinstance(self.timestamp, datetime):
            raise ValueError(f"timestamp must be a datetime, got {type(self.timestamp)}")
    
    @property
    def is_pass(self) -> bool:
        """Check if verdict is PASS."""
        return self.decision == VerdictDecision.PASS
    
    @property
    def is_fail(self) -> bool:
        """Check if verdict is FAIL."""
        return self.decision == VerdictDecision.FAIL
    
    @property
    def is_warning(self) -> bool:
        """Check if verdict is WARNING."""
        return self.decision == VerdictDecision.WARNING

