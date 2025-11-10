"""
Base AI Adapter for AI-driven testing framework.

This module provides the abstract base class and utilities for AI adapters,
including error handling, retry logic, and response caching.
"""

import base64
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional
from pathlib import Path

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)

from src.models import VerificationResult, Issue, Severity


logger = logging.getLogger(__name__)


# ============================================================================
# Response Models
# ============================================================================

@dataclass
class AIResponse:
    """Response from AI analysis."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None  # tokens_used, tokens_total, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


# ============================================================================
# Exceptions
# ============================================================================

class AIAdapterError(Exception):
    """Base exception for AI adapter errors."""
    pass


class AIAPIError(AIAdapterError):
    """Error from AI API (rate limit, invalid request, etc.)."""
    def __init__(self, message: str, status_code: Optional[int] = None, retry_after: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class AITimeoutError(AIAdapterError):
    """Timeout error from AI API."""
    pass


class AIConfigurationError(AIAdapterError):
    """Configuration error (missing API key, invalid settings, etc.)."""
    pass


# ============================================================================
# Response Cache
# ============================================================================

class ResponseCache:
    """Simple in-memory cache for AI responses."""
    
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        """
        Initialize response cache.
        
        Args:
            ttl_seconds: Time-to-live for cached responses in seconds
            max_size: Maximum number of cached responses
        """
        self.cache: Dict[str, tuple[datetime, AIResponse]] = {}
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
    
    def _generate_key(self, prompt: str, screenshot_hash: Optional[str] = None, html_hash: Optional[str] = None) -> str:
        """Generate cache key from inputs."""
        components = [prompt]
        if screenshot_hash:
            components.append(f"screenshot:{screenshot_hash}")
        if html_hash:
            components.append(f"html:{html_hash}")
        key_string = "|".join(components)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def get(self, prompt: str, screenshot_hash: Optional[str] = None, html_hash: Optional[str] = None) -> Optional[AIResponse]:
        """Get cached response if available and not expired."""
        key = self._generate_key(prompt, screenshot_hash, html_hash)
        
        if key not in self.cache:
            return None
        
        cached_time, response = self.cache[key]
        age = (datetime.now() - cached_time).total_seconds()
        
        if age > self.ttl_seconds:
            # Expired, remove from cache
            del self.cache[key]
            return None
        
        logger.debug(f"Cache hit for key: {key[:16]}...")
        return response
    
    def set(self, prompt: str, response: AIResponse, screenshot_hash: Optional[str] = None, html_hash: Optional[str] = None) -> None:
        """Cache a response."""
        key = self._generate_key(prompt, screenshot_hash, html_hash)
        
        # Evict oldest entries if cache is full
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][0])
            del self.cache[oldest_key]
        
        self.cache[key] = (datetime.now(), response)
        logger.debug(f"Cached response for key: {key[:16]}...")
    
    def clear(self) -> None:
        """Clear all cached responses."""
        self.cache.clear()
        logger.debug("Response cache cleared")
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)


# ============================================================================
# Decorators
# ============================================================================

def handle_ai_errors(func):
    """Decorator to handle AI adapter errors."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AIAdapterError:
            # Re-raise AI adapter errors as-is
            raise
        except Exception as e:
            # Wrap unexpected errors
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise AIAdapterError(f"Unexpected error in {func.__name__}: {e}") from e
    return wrapper


def retry_on_api_error(max_attempts: int = 3, base_delay: float = 1.0):
    """
    Decorator to retry on API errors with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
    """
    def decorator(func):
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=base_delay, min=1, max=60),
            retry=retry_if_exception_type((AIAPIError, AITimeoutError)),
            reraise=True,
        )
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except RetryError as e:
                # Last attempt failed
                logger.error(f"Failed after {max_attempts} attempts: {e}")
                raise
        return wrapper
    return decorator


# ============================================================================
# Base AI Adapter
# ============================================================================

class AIAdapter(ABC):
    """
    Abstract base class for AI adapters.
    
    This class defines the interface that all AI providers must implement.
    It provides common functionality like error handling, retry logic, and caching.
    """
    
    def __init__(
        self,
        model: str,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        enable_cache: bool = True,
        cache_ttl_seconds: int = 3600,
        max_retries: int = 3,
    ):
        """
        Initialize AI adapter.
        
        Args:
            model: Model identifier
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            enable_cache: Enable response caching
            cache_ttl_seconds: Cache time-to-live in seconds
            max_retries: Maximum retry attempts for API calls
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        
        self.cache: Optional[ResponseCache] = None
        if enable_cache:
            self.cache = ResponseCache(ttl_seconds=cache_ttl_seconds)
        
        logger.info(f"Initialized {self.__class__.__name__} with model: {model}")
    
    @abstractmethod
    async def analyze_page(
        self,
        screenshot: bytes,
        html: str,
        prompt: str,
    ) -> AIResponse:
        """
        Analyze a web page using AI vision and text analysis.
        
        Args:
            screenshot: Screenshot of the page as bytes (PNG/JPEG)
            html: HTML content of the page
            prompt: Analysis prompt/question
            
        Returns:
            AIResponse with analysis results
            
        Raises:
            AIAPIError: If API call fails
            AITimeoutError: If request times out
            AIConfigurationError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    async def verify_requirement(
        self,
        requirement: str,
        evidence: Dict[str, Any],
    ) -> VerificationResult:
        """
        Verify a specific requirement against evidence.
        
        Args:
            requirement: Requirement text to verify
            evidence: Evidence dictionary containing:
                - screenshot: bytes
                - html: str
                - url: str
                - title: str
                - (any other relevant data)
            
        Returns:
            VerificationResult with pass/fail status and reasoning
            
        Raises:
            AIAPIError: If API call fails
            AITimeoutError: If request times out
        """
        pass
    
    @abstractmethod
    async def extract_elements(
        self,
        html: str,
        element_descriptions: List[str],
    ) -> Dict[str, bool]:
        """
        Check if elements exist on the page based on descriptions.
        
        Args:
            html: HTML content of the page
            element_descriptions: List of element descriptions to find
            
        Returns:
            Dictionary mapping element descriptions to boolean (exists/not exists)
            
        Raises:
            AIAPIError: If API call fails
        """
        pass
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _hash_screenshot(self, screenshot: bytes) -> str:
        """Generate hash for screenshot."""
        return hashlib.sha256(screenshot).hexdigest()
    
    def _hash_html(self, html: str) -> str:
        """Generate hash for HTML."""
        return hashlib.sha256(html.encode()).hexdigest()
    
    def _encode_screenshot(self, screenshot: bytes) -> str:
        """Encode screenshot to base64."""
        return base64.b64encode(screenshot).decode('utf-8')
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON response from AI, handling markdown code blocks.
        
        Args:
            content: Response content (may be wrapped in ```json blocks)
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            ValueError: If JSON cannot be parsed
        """
        # Remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        elif content.startswith("```"):
            content = content[3:]  # Remove ```
        
        if content.endswith("```"):
            content = content[:-3]  # Remove closing ```
        
        content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content: {content[:500]}...")
            raise ValueError(f"Invalid JSON response: {e}") from e
    
    def _create_verification_prompt(self, requirement: str, evidence: Dict[str, Any]) -> str:
        """
        Create a prompt for requirement verification.
        
        Args:
            requirement: Requirement to verify
            evidence: Evidence dictionary
            
        Returns:
            Formatted prompt string
        """
        url = evidence.get("url", "unknown")
        title = evidence.get("title", "unknown")
        
        prompt = f"""You are a web testing assistant. Analyze the provided web page and verify if the following requirement is met:

REQUIREMENT: {requirement}

PAGE INFORMATION:
- URL: {url}
- Title: {title}

Please analyze the screenshot and HTML content provided, and respond with a JSON object containing:
{{
    "passed": true/false,
    "confidence": 0.0-100.0,
    "reasoning": "explanation of your decision",
    "issues": [
        {{
            "severity": "critical|major|minor",
            "description": "issue description"
        }}
    ]
}}

Be thorough and specific in your analysis."""
        
        return prompt
    
    # ========================================================================
    # Cached Wrapper Methods
    # ========================================================================
    
    @handle_ai_errors
    @retry_on_api_error(max_attempts=3)
    async def analyze_page_cached(
        self,
        screenshot: bytes,
        html: str,
        prompt: str,
    ) -> AIResponse:
        """
        Analyze page with caching support.
        
        This is a convenience wrapper around analyze_page that adds caching.
        """
        screenshot_hash = self._hash_screenshot(screenshot)
        html_hash = self._hash_html(html)
        
        # Check cache
        if self.cache:
            cached_response = self.cache.get(prompt, screenshot_hash, html_hash)
            if cached_response:
                logger.debug("Using cached response for analyze_page")
                return cached_response
        
        # Call actual implementation
        response = await self.analyze_page(screenshot, html, prompt)
        
        # Cache response
        if self.cache:
            self.cache.set(prompt, response, screenshot_hash, html_hash)
        
        return response
    
    @handle_ai_errors
    @retry_on_api_error(max_attempts=3)
    async def verify_requirement_cached(
        self,
        requirement: str,
        evidence: Dict[str, Any],
    ) -> VerificationResult:
        """
        Verify requirement with caching support.
        
        This is a convenience wrapper around verify_requirement that adds caching.
        """
        screenshot = evidence.get("screenshot")
        html = evidence.get("html", "")
        
        screenshot_hash = None
        html_hash = None
        
        if screenshot:
            screenshot_hash = self._hash_screenshot(screenshot)
        if html:
            html_hash = self._hash_html(html)
        
        # Create cache key from requirement and evidence
        cache_key = f"{requirement}|{screenshot_hash}|{html_hash}"
        
        # Note: We don't cache VerificationResult directly since it's a model object
        # Instead, we'll let the implementation handle caching if needed
        # For now, just call the actual implementation
        return await self.verify_requirement(requirement, evidence)
    
    def clear_cache(self) -> None:
        """Clear the response cache."""
        if self.cache:
            self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.cache:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "size": self.cache.size(),
            "max_size": self.cache.max_size,
            "ttl_seconds": self.cache.ttl_seconds,
        }

