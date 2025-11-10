"""
OpenAI Adapter for AI-driven testing framework.

This module provides OpenAI GPT-4o integration with vision API support.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional
import time

from openai import AsyncOpenAI
from openai import APIError, RateLimitError, APITimeoutError, APIConnectionError

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


# System prompts for different use cases
SYSTEM_PROMPT_ANALYSIS = """You are a web testing assistant. Analyze web pages and provide detailed insights about their content, structure, and functionality. Be thorough and specific in your analysis."""

SYSTEM_PROMPT_VERIFICATION = """You are a web testing assistant. Your task is to verify if web pages meet specific requirements. Analyze the provided evidence (screenshot and HTML) and determine if the requirement is met. Be objective and precise in your assessment."""

SYSTEM_PROMPT_ELEMENT_EXTRACTION = """You are a web testing assistant. Analyze HTML content and identify if specific elements exist on the page. Return a JSON object mapping element descriptions to boolean values indicating their presence."""


class OpenAIAdapter(AIAdapter):
    """
    OpenAI adapter using GPT-4o with vision API support.
    
    This adapter implements the AIAdapter interface using OpenAI's API,
    supporting both text and vision (screenshot) analysis.
    """
    
    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.2,
        max_tokens: Optional[int] = 2000,
        api_key: Optional[str] = None,
        api_key_env: str = "OPENAI_API_KEY",
        enable_cache: bool = True,
        cache_ttl_seconds: int = 3600,
        max_retries: int = 3,
    ):
        """
        Initialize OpenAI adapter.
        
        Args:
            model: OpenAI model identifier (default: gpt-4o)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            api_key: OpenAI API key (if None, reads from environment)
            api_key_env: Environment variable name for API key
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
        
        # Get API key
        self.api_key = api_key or os.getenv(api_key_env)
        if not self.api_key:
            raise AIConfigurationError(
                f"OpenAI API key not found. Set {api_key_env} environment variable or pass api_key parameter."
            )
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        logger.info(f"Initialized OpenAIAdapter with model: {model}")
    
    @handle_ai_errors
    @retry_on_api_error(max_attempts=3)
    async def analyze_page(
        self,
        screenshot: bytes,
        html: str,
        prompt: str,
    ) -> AIResponse:
        """
        Analyze a web page using OpenAI vision API.
        
        Args:
            screenshot: Screenshot of the page as bytes (PNG/JPEG)
            html: HTML content of the page
            prompt: Analysis prompt/question
            
        Returns:
            AIResponse with analysis results
            
        Raises:
            AIAPIError: If API call fails
            AITimeoutError: If request times out
        """
        start_time = time.time()
        
        try:
            # Encode screenshot to base64
            base64_image = self._encode_screenshot(screenshot)
            
            # Prepare messages with vision support
            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT_ANALYSIS
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{prompt}\n\nHTML Content:\n{html[:2000]}"  # Include HTML context (truncated)
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            # Extract response content
            content = response.choices[0].message.content or ""
            
            # Extract usage information
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return AIResponse(
                content=content,
                model=self.model,
                usage=usage,
                metadata={"duration_ms": duration_ms},
            )
            
        except RateLimitError as e:
            # Extract retry-after from headers if available
            retry_after = None
            if hasattr(e, 'response') and e.response:
                retry_after_header = e.response.headers.get('retry-after')
                if retry_after_header:
                    try:
                        retry_after = int(retry_after_header)
                    except ValueError:
                        pass
            
            raise AIAPIError(
                f"OpenAI rate limit exceeded: {e}",
                status_code=429,
                retry_after=retry_after,
            ) from e
            
        except APITimeoutError as e:
            raise AITimeoutError(f"OpenAI request timed out: {e}") from e
            
        except APIConnectionError as e:
            raise AIAPIError(
                f"OpenAI connection error: {e}",
                status_code=0,
            ) from e
            
        except APIError as e:
            status_code = 500
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            
            raise AIAPIError(
                f"OpenAI API error: {e}",
                status_code=status_code,
            ) from e
    
    @handle_ai_errors
    @retry_on_api_error(max_attempts=3)
    async def verify_requirement(
        self,
        requirement: str,
        evidence: Dict[str, Any],
    ) -> VerificationResult:
        """
        Verify a specific requirement against evidence using OpenAI.
        
        Args:
            requirement: Requirement text to verify
            evidence: Evidence dictionary containing screenshot, html, url, title, etc.
            
        Returns:
            VerificationResult with pass/fail status and reasoning
        """
        start_time = time.time()
        
        screenshot = evidence.get("screenshot")
        html = evidence.get("html", "")
        url = evidence.get("url", "unknown")
        title = evidence.get("title", "unknown")
        
        if not screenshot:
            raise ValueError("Screenshot is required for verification")
        
        # Create verification prompt
        prompt = self._create_verification_prompt(requirement, evidence)
        
        # Encode screenshot
        base64_image = self._encode_screenshot(screenshot)
        
        # Prepare messages
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT_VERIFICATION
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        try:
            # Make API call with JSON response format
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )
            
            # Parse JSON response
            content = response.choices[0].message.content or "{}"
            result_data = self._parse_json_response(content)
            
            # Extract verification result
            passed = result_data.get("passed", False)
            confidence = float(result_data.get("confidence", 0.0))
            reasoning = result_data.get("reasoning", "")
            issues_data = result_data.get("issues", [])
            
            # Convert issues to Issue objects
            issues = []
            for issue_data in issues_data:
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
                passed=passed,
                confidence=confidence,
                evidence={
                    "url": url,
                    "title": title,
                    "screenshot_size": len(screenshot),
                    "html_length": len(html),
                },
                issues=issues,
                ai_reasoning=reasoning,
                duration_ms=duration_ms,
            )
            
        except RateLimitError as e:
            retry_after = None
            if hasattr(e, 'response') and e.response:
                retry_after_header = e.response.headers.get('retry-after')
                if retry_after_header:
                    try:
                        retry_after = int(retry_after_header)
                    except ValueError:
                        pass
            
            raise AIAPIError(
                f"OpenAI rate limit exceeded: {e}",
                status_code=429,
                retry_after=retry_after,
            ) from e
            
        except APITimeoutError as e:
            raise AITimeoutError(f"OpenAI request timed out: {e}") from e
            
        except APIConnectionError as e:
            raise AIAPIError(
                f"OpenAI connection error: {e}",
                status_code=0,
            ) from e
            
        except APIError as e:
            status_code = 500
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            
            raise AIAPIError(
                f"OpenAI API error: {e}",
                status_code=status_code,
            ) from e
    
    @handle_ai_errors
    @retry_on_api_error(max_attempts=3)
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
        """
        if not element_descriptions:
            return {}
        
        # Create prompt for element extraction
        descriptions_text = "\n".join(f"- {desc}" for desc in element_descriptions)
        prompt = f"""Analyze the following HTML content and determine which of these elements exist on the page:

ELEMENTS TO FIND:
{descriptions_text}

HTML CONTENT:
{html[:4000]}  # Truncate HTML to avoid token limits

Respond with a JSON object mapping each element description to a boolean value indicating if it exists.
Example: {{"Submit button": true, "Login form": false}}"""
        
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT_ELEMENT_EXTRACTION
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            # Make API call with JSON response format
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )
            
            # Parse JSON response
            content = response.choices[0].message.content or "{}"
            result_data = self._parse_json_response(content)
            
            # Convert to dictionary with boolean values
            result = {}
            for desc in element_descriptions:
                # Try exact match first
                if desc in result_data:
                    result[desc] = bool(result_data[desc])
                else:
                    # Try case-insensitive match
                    found = False
                    for key, value in result_data.items():
                        if key.lower() == desc.lower():
                            result[desc] = bool(value)
                            found = True
                            break
                    if not found:
                        # Default to False if not found
                        result[desc] = False
            
            return result
            
        except RateLimitError as e:
            retry_after = None
            if hasattr(e, 'response') and e.response:
                retry_after_header = e.response.headers.get('retry-after')
                if retry_after_header:
                    try:
                        retry_after = int(retry_after_header)
                    except ValueError:
                        pass
            
            raise AIAPIError(
                f"OpenAI rate limit exceeded: {e}",
                status_code=429,
                retry_after=retry_after,
            ) from e
            
        except APITimeoutError as e:
            raise AITimeoutError(f"OpenAI request timed out: {e}") from e
            
        except APIConnectionError as e:
            raise AIAPIError(
                f"OpenAI connection error: {e}",
                status_code=0,
            ) from e
            
        except APIError as e:
            status_code = 500
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            
            raise AIAPIError(
                f"OpenAI API error: {e}",
                status_code=status_code,
            ) from e

