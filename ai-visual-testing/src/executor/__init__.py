"""
Test Executor package for AI-driven testing framework.

This package contains the TestExecutor class that orchestrates browser automation
and AI-powered verification.
"""

from .executor import TestExecutor, ActionExecutionError

__all__ = ["TestExecutor", "ActionExecutionError"]
