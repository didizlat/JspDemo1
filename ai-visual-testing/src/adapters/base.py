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
    """
    Response from AI analysis.
    
    Attributes:
        content: Response content text
        model: Model identifier used for the response
        usage: Optional usage statistics (tokens, etc.)
        metadata: Optional metadata dictionary
        timestamp: Timestamp when response was created
    """
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None  # tokens_used, tokens_total, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate response data after initialization."""
        if not isinstance(self.content, str):
            raise ValueError(f"Content must be a string, got {type(self.content)}")
        if not isinstance(self.model, str) or len(self.model.strip()) == 0:
            raise ValueError("Model must be a non-empty string")
        if self.usage is not None and not isinstance(self.usage, dict):
            raise ValueError(f"Usage must be a dictionary or None, got {type(self.usage)}")
        if not isinstance(self.metadata, dict):
            raise ValueError(f"Metadata must be a dictionary, got {type(self.metadata)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation of the response
        """
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
    """
    Error from AI API (rate limit, invalid request, etc.).
    
    Attributes:
        message: Error message
        status_code: HTTP status code (if available)
        retry_after: Seconds to wait before retrying (if available)
    """
    def __init__(self, message: str, status_code: Optional[int] = None, retry_after: Optional[int] = None):
        if not message or not isinstance(message, str):
            raise ValueError("Error message must be a non-empty string")
        
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after
    
    def __str__(self) -> str:
        """Return formatted error message."""
        msg = self.args[0] if self.args else "AI API error"
        if self.status_code:
            msg += f" (status: {self.status_code})"
        if self.retry_after:
            msg += f" (retry after: {self.retry_after}s)"
        return msg


class AITimeoutError(AIAdapterError):
    """
    Timeout error from AI API.
    
    This exception is raised when an AI API request times out.
    """
    pass


class AIConfigurationError(AIAdapterError):
    """
    Configuration error (missing API key, invalid settings, etc.).
    
    This exception is raised when there's a problem with adapter configuration,
    such as missing API keys, invalid parameter values, or misconfigured settings.
    """
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
            
        Raises:
            ValueError: If ttl_seconds or max_size are invalid
        """
        if not isinstance(ttl_seconds, int) or ttl_seconds < 1:
            raise ValueError(f"ttl_seconds must be a positive integer, got {ttl_seconds}")
        if not isinstance(max_size, int) or max_size < 1:
            raise ValueError(f"max_size must be a positive integer, got {max_size}")
        
        self.cache: Dict[str, tuple[datetime, AIResponse]] = {}
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
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
        """
        Get cached response if available and not expired.
        
        Args:
            prompt: Prompt string
            screenshot_hash: Optional screenshot hash
            html_hash: Optional HTML hash
            
        Returns:
            Cached AIResponse if available and not expired, None otherwise
        """
        # Validate inputs
        if not prompt or not isinstance(prompt, str):
            logger.warning("Invalid prompt provided to cache.get(), returning None")
            self.misses += 1
            return None
        
        key = self._generate_key(prompt, screenshot_hash, html_hash)
        
        if key not in self.cache:
            self.misses += 1
            logger.debug(f"Cache miss for key: {key[:16]}...")
            return None
        
        cached_time, response = self.cache[key]
        age = (datetime.now() - cached_time).total_seconds()
        
        if age > self.ttl_seconds:
            # Expired, remove from cache
            del self.cache[key]
            self.misses += 1
            logger.debug(f"Cache entry expired for key: {key[:16]}...")
            return None
        
        self.hits += 1
        logger.debug(f"Cache hit for key: {key[:16]}... (age: {age:.1f}s)")
        return response
    
    def set(self, prompt: str, response: AIResponse, screenshot_hash: Optional[str] = None, html_hash: Optional[str] = None) -> None:
        """
        Cache a response.
        
        Args:
            prompt: Prompt string
            response: AIResponse to cache
            screenshot_hash: Optional screenshot hash
            html_hash: Optional HTML hash
            
        Raises:
            ValueError: If prompt or response are invalid
        """
        # Validate inputs
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt must be a non-empty string")
        if not isinstance(response, AIResponse):
            raise ValueError(f"Response must be an AIResponse instance, got {type(response)}")
        
        key = self._generate_key(prompt, screenshot_hash, html_hash)
        
        # Evict oldest entries if cache is full
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][0])
            del self.cache[oldest_key]
            logger.debug(f"Evicted oldest cache entry (key: {oldest_key[:16]}...) to make room")
        
        self.cache[key] = (datetime.now(), response)
        logger.debug(f"Cached response for key: {key[:16]}... (cache size: {len(self.cache)}/{self.max_size})")
    
    def clear(self) -> None:
        """Clear all cached responses."""
        size_before = len(self.cache)
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.debug(f"Response cache cleared ({size_before} entries removed)")
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of expired entries removed
        """
        now = datetime.now()
        expired_keys = [
            key for key, (cached_time, _) in self.cache.items()
            if (now - cached_time).total_seconds() > self.ttl_seconds
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"Removed {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics including hits, misses, hit rate, etc.
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 2),
        }


# ============================================================================
# Decorators
# ============================================================================

def handle_ai_errors(func):
    """
    Decorator to handle AI adapter errors.
    
    This decorator catches unexpected exceptions and wraps them in AIAdapterError,
    while preserving AI adapter errors as-is.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AIAdapterError:
            # Re-raise AI adapter errors as-is
            raise
        except Exception as e:
            # Wrap unexpected errors
            error_type = type(e).__name__
            logger.error(
                f"Unexpected error in {func.__name__}: {error_type}: {e}",
                exc_info=True
            )
            raise AIAdapterError(f"Unexpected error in {func.__name__} ({error_type}): {e}") from e
    return wrapper


def retry_on_api_error(max_attempts: int = 3, base_delay: float = 1.0):
    """
    Decorator to retry on API errors with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts (must be >= 1)
        base_delay: Base delay in seconds for exponential backoff (must be > 0)
        
    Raises:
        ValueError: If max_attempts or base_delay are invalid
    """
    # Validate parameters
    if not isinstance(max_attempts, int) or max_attempts < 1:
        raise ValueError(f"max_attempts must be a positive integer, got {max_attempts}")
    if not isinstance(base_delay, (int, float)) or base_delay <= 0:
        raise ValueError(f"base_delay must be a positive number, got {base_delay}")
    
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
                last_exception = e.last_attempt.exception() if hasattr(e, 'last_attempt') else None
                error_info = f": {last_exception}" if last_exception else ""
                logger.error(
                    f"Failed after {max_attempts} attempts in {func.__name__}{error_info}",
                    exc_info=True
                )
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
            
        Raises:
            AIConfigurationError: If configuration is invalid
        """
        # Validate model
        if not model or not isinstance(model, str) or len(model.strip()) == 0:
            raise AIConfigurationError("Model name must be a non-empty string")
        
        # Validate temperature range
        if not isinstance(temperature, (int, float)) or temperature < 0.0 or temperature > 2.0:
            raise AIConfigurationError(f"Temperature must be between 0.0 and 2.0, got {temperature}")
        
        # Validate max_tokens if provided
        if max_tokens is not None:
            if not isinstance(max_tokens, int) or max_tokens < 1 or max_tokens > 100000:
                raise AIConfigurationError(f"max_tokens must be between 1 and 100000, got {max_tokens}")
        
        # Validate cache_ttl_seconds
        if not isinstance(cache_ttl_seconds, int) or cache_ttl_seconds < 1:
            raise AIConfigurationError(f"cache_ttl_seconds must be a positive integer, got {cache_ttl_seconds}")
        
        # Validate max_retries
        if not isinstance(max_retries, int) or max_retries < 0 or max_retries > 10:
            raise AIConfigurationError(f"max_retries must be between 0 and 10, got {max_retries}")
        
        self.model = model.strip()
        self.temperature = float(temperature)
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        
        self.cache: Optional[ResponseCache] = None
        if enable_cache:
            self.cache = ResponseCache(ttl_seconds=cache_ttl_seconds)
        
        logger.info(
            f"Initialized {self.__class__.__name__} with model: {self.model}, "
            f"temperature: {self.temperature}, max_tokens: {self.max_tokens}, "
            f"cache: {'enabled' if enable_cache else 'disabled'}"
        )
    
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
        """
        Generate hash for screenshot.
        
        Args:
            screenshot: Screenshot bytes
            
        Returns:
            SHA256 hash as hexadecimal string
            
        Raises:
            ValueError: If screenshot is invalid
        """
        if not isinstance(screenshot, bytes):
            raise ValueError(f"Screenshot must be bytes, got {type(screenshot)}")
        if len(screenshot) == 0:
            raise ValueError("Screenshot must be non-empty")
        
        return hashlib.sha256(screenshot).hexdigest()
    
    def _hash_html(self, html: str) -> str:
        """
        Generate hash for HTML.
        
        Args:
            html: HTML content string
            
        Returns:
            SHA256 hash as hexadecimal string
            
        Raises:
            ValueError: If HTML is invalid
        """
        if not isinstance(html, str):
            raise ValueError(f"HTML must be a string, got {type(html)}")
        
        return hashlib.sha256(html.encode('utf-8')).hexdigest()
    
    def _encode_screenshot(self, screenshot: bytes) -> str:
        """
        Encode screenshot to base64.
        
        Args:
            screenshot: Screenshot bytes
            
        Returns:
            Base64-encoded string
            
        Raises:
            ValueError: If screenshot is invalid
        """
        if not isinstance(screenshot, bytes):
            raise ValueError(f"Screenshot must be bytes, got {type(screenshot)}")
        if len(screenshot) == 0:
            raise ValueError("Screenshot must be non-empty")
        
        try:
            return base64.b64encode(screenshot).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to encode screenshot: {e}") from e
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON response from AI, handling markdown code blocks.
        
        Args:
            content: Response content (may be wrapped in ```json blocks)
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            ValueError: If content is invalid or JSON cannot be parsed
        """
        # Validate input
        if not isinstance(content, str):
            raise ValueError(f"Content must be a string, got {type(content)}")
        
        # Remove markdown code blocks if present
        original_content = content
        content = content.strip()
        
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        elif content.startswith("```"):
            content = content[3:]  # Remove ```
        
        if content.endswith("```"):
            content = content[:-3]  # Remove closing ```
        
        content = content.strip()
        
        # Validate content is not empty after cleaning
        if not content:
            raise ValueError("Content is empty after removing markdown code blocks")
        
        try:
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError(f"Expected JSON object (dict), got {type(parsed)}")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content (first 500 chars): {original_content[:500]}...")
            logger.debug(f"Cleaned content (first 500 chars): {content[:500]}...")
            raise ValueError(f"Invalid JSON response: {e}") from e
    
    def _create_verification_prompt(self, requirement: str, evidence: Dict[str, Any]) -> str:
        """
        Create a prompt for requirement verification.
        
        Args:
            requirement: Requirement to verify
            evidence: Evidence dictionary
            
        Returns:
            Formatted prompt string
            
        Raises:
            ValueError: If requirement or evidence are invalid
        """
        # Validate inputs
        if not requirement or not isinstance(requirement, str) or len(requirement.strip()) == 0:
            raise ValueError("Requirement must be a non-empty string")
        if not isinstance(evidence, dict):
            raise ValueError(f"Evidence must be a dictionary, got {type(evidence)}")
        
        url = evidence.get("url", "unknown")
        title = evidence.get("title", "unknown")
        
        # Escape special characters in requirement to prevent prompt injection
        requirement_escaped = requirement.replace('{', '{{').replace('}', '}}')
        
        prompt = f"""You are a web testing assistant. Analyze the provided web page and verify if the following requirement is met:

REQUIREMENT: {requirement_escaped}

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
        
        Args:
            screenshot: Screenshot of the page as bytes
            html: HTML content of the page
            prompt: Analysis prompt/question
            
        Returns:
            AIResponse with analysis results (may be from cache)
            
        Raises:
            AIAPIError: If API call fails
            AITimeoutError: If request times out
            ValueError: If inputs are invalid
        """
        # Validate inputs
        if not prompt or not isinstance(prompt, str) or len(prompt.strip()) == 0:
            raise ValueError("Prompt must be a non-empty string")
        
        screenshot_hash = self._hash_screenshot(screenshot)
        html_hash = self._hash_html(html)
        
        # Check cache
        if self.cache:
            cached_response = self.cache.get(prompt, screenshot_hash, html_hash)
            if cached_response:
                logger.debug(f"Using cached response for analyze_page (prompt: '{prompt[:50]}...')")
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
        
        Args:
            requirement: Requirement text to verify
            evidence: Evidence dictionary containing screenshot, html, url, title, etc.
            
        Returns:
            VerificationResult with pass/fail status and reasoning
            
        Raises:
            AIAPIError: If API call fails
            AITimeoutError: If request times out
            ValueError: If inputs are invalid
        """
        # Validate inputs
        if not requirement or not isinstance(requirement, str) or len(requirement.strip()) == 0:
            raise ValueError("Requirement must be a non-empty string")
        if not isinstance(evidence, dict):
            raise ValueError(f"Evidence must be a dictionary, got {type(evidence)}")
        
        screenshot = evidence.get("screenshot")
        html = evidence.get("html", "")
        
        screenshot_hash = None
        html_hash = None
        
        if screenshot:
            screenshot_hash = self._hash_screenshot(screenshot)
        if html:
            html_hash = self._hash_html(html)
        
        # Note: We don't cache VerificationResult directly since it's a model object
        # and verification results may need to be fresh. Instead, we'll let the
        # implementation handle caching if needed. For now, just call the actual implementation.
        return await self.verify_requirement(requirement, evidence)
    
    def clear_cache(self) -> None:
        """
        Clear the response cache.
        
        Removes all cached responses and resets cache statistics.
        """
        if self.cache:
            self.cache.clear()
            logger.debug("Cache cleared via clear_cache()")
    
    def cleanup_expired_cache(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of expired entries removed
        """
        if not self.cache:
            return 0
        
        return self.cache.cleanup_expired()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics including enabled status, size, hits, misses, hit rate, etc.
        """
        if not self.cache:
            return {"enabled": False}
        
        cache_stats = self.cache.get_stats()
        return {
            "enabled": True,
            **cache_stats,
        }

