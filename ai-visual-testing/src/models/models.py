"""
Data models for AI-driven testing framework.

This module defines all data structures used throughout the testing framework,
including test suites, steps, verifications, actions, results, and verdicts.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


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
        if not self.text or not self.text.strip():
            raise ValueError("Verification text cannot be empty")
        if self.description is None:
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
        if not self.target or not self.target.strip():
            raise ValueError("Action target cannot be empty")
        if self.type in [ActionType.TYPE, ActionType.FILL, ActionType.SELECT] and not self.value:
            raise ValueError(f"Action type {self.type} requires a value")
        if self.description is None:
            self.description = f"{self.type.value} {self.target}"


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
        if not self.description or not self.description.strip():
            raise ValueError("Issue description cannot be empty")


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
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError(f"Confidence must be between 0.0 and 100.0, got {self.confidence}")
        if not self.requirement or not self.requirement.strip():
            raise ValueError("Requirement text cannot be empty")


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
        if not self.url:
            raise ValueError("URL cannot be empty")
        if not isinstance(self.screenshot, bytes):
            raise ValueError("Screenshot must be bytes")


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
        if self.step_number < 1:
            raise ValueError(f"Step number must be >= 1, got {self.step_number}")
        if not self.description or not self.description.strip():
            raise ValueError("Step description cannot be empty")


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
        if self.step_number < 1:
            raise ValueError(f"Step number must be >= 1, got {self.step_number}")
        if not self.description or not self.description.strip():
            raise ValueError("Step description cannot be empty")


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
        if not self.name or not self.name.strip():
            raise ValueError("Test suite name cannot be empty")
        if not self.steps:
            raise ValueError("Test suite must have at least one step")
        
        # Validate step numbers are sequential
        step_numbers = [step.step_number for step in self.steps]
        if step_numbers != sorted(set(step_numbers)):
            raise ValueError("Step numbers must be unique and sequential")


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
        if not self.test_suite_name or not self.test_suite_name.strip():
            raise ValueError("Test suite name cannot be empty")
    
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


@dataclass
class Verdict:
    """Final verdict for a test suite."""
    decision: VerdictDecision
    confidence: float  # 0.0 to 100.0
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate verdict."""
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError(f"Confidence must be between 0.0 and 100.0, got {self.confidence}")
        if not self.reasoning or not self.reasoning.strip():
            raise ValueError("Verdict reasoning cannot be empty")
    
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

