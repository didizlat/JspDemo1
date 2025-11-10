"""
Custom Adapter for AI-driven testing framework.

This module provides a generic adapter for custom AI APIs that follow
a similar interface pattern.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Callable, Awaitable
import time

from src.adapters.base import (
    AIAdapter,
    AIResponse,
    AIAPIError,
    AITimeoutError,
    AIConfigurationError,
    handle_ai_errors,
    retry_on_api_error,
)
from src.models import VerificationResult, Issue, Severity


logger = logging.getLogger(__name__)


class CustomAdapter(AIAdapter):
    """
    Custom adapter for generic AI APIs.
    
    This adapter allows users to provide custom functions for API calls,
    making it flexible for any AI provider that follows a similar pattern.
    """
    
    def __init__(
        self,
        model: str = "custom-model",
        temperature: float = 0.2,
        max_tokens: Optional[int] = 2000,
        analyze_func: Optional[Callable[[bytes, str, str], Awaitable[Dict[str, Any]]]] = None,
        verify_func: Optional[Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None,
        extract_func: Optional[Callable[[str, List[str]], Awaitable[Dict[str, bool]]]] = None,
        enable_cache: bool = True,
        cache_ttl_seconds: int = 3600,
        max_retries: int = 3,
    ):
        """
        Initialize Custom adapter.
        
        Args:
            model: Model identifier
            temperature: Sampling temperature (for documentation)
            max_tokens: Maximum tokens (for documentation)
            analyze_func: Async function(screenshot, html, prompt) -> {content, usage, ...}
            verify_func: Async function(requirement, evidence) -> {passed, confidence, reasoning, issues}
            extract_func: Async function(html, descriptions) -> {desc: bool, ...}
            enable_cache: Enable response caching
            cache_ttl_seconds: Cache time-to-live in seconds
            max_retries: Maximum retry attempts for API calls
        """
        super().__init__(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            enable_cache=enable_cache,
            cache_ttl_seconds=cache_ttl_seconds,
            max_retries=max_retries,
        )
        
        self.analyze_func = analyze_func
        self.verify_func = verify_func
        self.extract_func = extract_func
        
        if not analyze_func or not verify_func or not extract_func:
            raise AIConfigurationError(
                "Custom adapter requires analyze_func, verify_func, and extract_func to be provided"
            )
        
        logger.info(f"Initialized CustomAdapter with model: {model}")
    
    @handle_ai_errors
    @retry_on_api_error(max_attempts=3)
    async def analyze_page(
        self,
        screenshot: bytes,
        html: str,
        prompt: str,
    ) -> AIResponse:
        """Analyze a web page using custom function."""
        start_time = time.time()
        
        try:
            result = await self.analyze_func(screenshot, html, prompt)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return AIResponse(
                content=result.get("content", ""),
                model=self.model,
                usage=result.get("usage"),
                metadata={
                    "duration_ms": duration_ms,
                    **result.get("metadata", {}),
                },
            )
        except Exception as e:
            raise AIAPIError(
                f"Custom adapter error: {e}",
                status_code=500,
            ) from e
    
    @handle_ai_errors
    @retry_on_api_error(max_attempts=3)
    async def verify_requirement(
        self,
        requirement: str,
        evidence: Dict[str, Any],
    ) -> VerificationResult:
        """Verify a specific requirement using custom function."""
        start_time = time.time()
        
        try:
            result = await self.verify_func(requirement, evidence)
            
            # Convert issues to Issue objects
            issues = []
            for issue_data in result.get("issues", []):
                severity_str = issue_data.get("severity", "minor").lower()
                try:
                    severity = Severity(severity_str)
                except ValueError:
                    severity = Severity.MINOR
                
                issues.append(Issue(
                    severity=severity,
                    description=issue_data.get("description", ""),
                ))
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return VerificationResult(
                requirement=requirement,
                passed=result.get("passed", False),
                confidence=float(result.get("confidence", 0.0)),
                evidence=evidence,
                issues=issues,
                ai_reasoning=result.get("reasoning"),
                duration_ms=duration_ms,
            )
        except Exception as e:
            raise AIAPIError(
                f"Custom adapter error: {e}",
                status_code=500,
            ) from e
    
    @handle_ai_errors
    @retry_on_api_error(max_attempts=3)
    async def extract_elements(
        self,
        html: str,
        element_descriptions: List[str],
    ) -> Dict[str, bool]:
        """Check if elements exist using custom function."""
        try:
            result = await self.extract_func(html, element_descriptions)
            return result
        except Exception as e:
            raise AIAPIError(
                f"Custom adapter error: {e}",
                status_code=500,
            ) from e

