"""
Claude Adapter for AI-driven testing framework.

This module provides Anthropic Claude integration with vision API support.
"""

import os
import json
import base64
import logging
from typing import Any, Dict, List, Optional
import time

try:
    from anthropic import AsyncAnthropic
    from anthropic import APIError, RateLimitError, APITimeoutError, APIConnectionError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    AsyncAnthropic = None

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

SYSTEM_PROMPT_VERIFICATION = """You are a web testing assistant. Your task is to verify if web pages meet specific requirements. Analyze the provided evidence (screenshot and HTML) and determine if the requirement is met. Be objective and precise in your assessment. Respond with a JSON object containing: {"passed": true/false, "confidence": 0.0-100.0, "reasoning": "explanation", "issues": [{"severity": "critical|major|minor", "description": "issue"}]}"""

SYSTEM_PROMPT_ELEMENT_EXTRACTION = """You are a web testing assistant. Analyze HTML content and identify if specific elements exist on the page. Return a JSON object mapping element descriptions to boolean values indicating their presence."""


class ClaudeAdapter(AIAdapter):
    """
    Anthropic Claude adapter with vision API support.
    
    This adapter implements the AIAdapter interface using Anthropic's API,
    supporting both text and vision (screenshot) analysis.
    """
    
    def __init__(
        self,
        model: str = "claude-3-opus-20240229",
        temperature: float = 0.2,
        max_tokens: Optional[int] = 2000,
        api_key: Optional[str] = None,
        api_key_env: str = "ANTHROPIC_API_KEY",
        enable_cache: bool = True,
        cache_ttl_seconds: int = 3600,
        max_retries: int = 3,
    ):
        """
        Initialize Claude adapter.
        
        Args:
            model: Claude model identifier (default: claude-3-opus-20240229)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            api_key: Anthropic API key (if None, reads from environment)
            api_key_env: Environment variable name for API key
            enable_cache: Enable response caching
            cache_ttl_seconds: Cache time-to-live in seconds
            max_retries: Maximum retry attempts for API calls
        """
        if not ANTHROPIC_AVAILABLE:
            raise AIConfigurationError(
                "Anthropic library not installed. Install with: pip install anthropic"
            )
        
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
                f"Anthropic API key not found. Set {api_key_env} environment variable or pass api_key parameter."
            )
        
        # Initialize Anthropic client
        self.client = AsyncAnthropic(api_key=self.api_key)
        
        logger.info(f"Initialized ClaudeAdapter with model: {model}")
    
    @handle_ai_errors
    @retry_on_api_error(max_attempts=3)
    async def analyze_page(
        self,
        screenshot: bytes,
        html: str,
        prompt: str,
    ) -> AIResponse:
        """Analyze a web page using Claude vision API."""
        start_time = time.time()
        
        try:
            # Encode screenshot to base64
            base64_image = self._encode_screenshot(screenshot)
            
            # Prepare messages
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{prompt}\n\nHTML Content:\n{html[:2000]}"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ]
            
            # Make API call
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens or 4096,
                temperature=self.temperature,
                system=SYSTEM_PROMPT_ANALYSIS,
                messages=messages,
            )
            
            # Extract response content
            content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
            
            # Extract usage information
            usage = None
            if hasattr(response, 'usage'):
                usage = {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                }
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return AIResponse(
                content=content,
                model=self.model,
                usage=usage,
                metadata={"duration_ms": duration_ms},
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
                f"Claude rate limit exceeded: {e}",
                status_code=429,
                retry_after=retry_after,
            ) from e
            
        except APITimeoutError as e:
            raise AITimeoutError(f"Claude request timed out: {e}") from e
            
        except APIConnectionError as e:
            raise AIAPIError(
                f"Claude connection error: {e}",
                status_code=0,
            ) from e
            
        except APIError as e:
            status_code = 500
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            
            raise AIAPIError(
                f"Claude API error: {e}",
                status_code=status_code,
            ) from e
    
    @handle_ai_errors
    @retry_on_api_error(max_attempts=3)
    async def verify_requirement(
        self,
        requirement: str,
        evidence: Dict[str, Any],
    ) -> VerificationResult:
        """Verify a specific requirement against evidence using Claude."""
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
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_image
                        }
                    }
                ]
            }
        ]
        
        try:
            # Make API call
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens or 4096,
                temperature=self.temperature,
                system=SYSTEM_PROMPT_VERIFICATION,
                messages=messages,
            )
            
            # Extract response content
            content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
            
            # Parse JSON response
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
                f"Claude rate limit exceeded: {e}",
                status_code=429,
                retry_after=retry_after,
            ) from e
            
        except APITimeoutError as e:
            raise AITimeoutError(f"Claude request timed out: {e}") from e
            
        except APIConnectionError as e:
            raise AIAPIError(
                f"Claude connection error: {e}",
                status_code=0,
            ) from e
            
        except APIError as e:
            status_code = 500
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            
            raise AIAPIError(
                f"Claude API error: {e}",
                status_code=status_code,
            ) from e
    
    @handle_ai_errors
    @retry_on_api_error(max_attempts=3)
    async def extract_elements(
        self,
        html: str,
        element_descriptions: List[str],
    ) -> Dict[str, bool]:
        """Check if elements exist on the page based on descriptions."""
        if not element_descriptions:
            return {}
        
        # Create prompt for element extraction
        descriptions_text = "\n".join(f"- {desc}" for desc in element_descriptions)
        prompt = f"""Analyze the following HTML content and determine which of these elements exist on the page:

ELEMENTS TO FIND:
{descriptions_text}

HTML CONTENT:
{html[:4000]}

Respond with a JSON object mapping each element description to a boolean value indicating if it exists.
Example: {{"Submit button": true, "Login form": false}}"""
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
        
        try:
            # Make API call
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens or 4096,
                temperature=self.temperature,
                system=SYSTEM_PROMPT_ELEMENT_EXTRACTION,
                messages=messages,
            )
            
            # Extract response content
            content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
            
            # Parse JSON response
            result_data = self._parse_json_response(content)
            
            # Convert to dictionary with boolean values
            result = {}
            for desc in element_descriptions:
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
                f"Claude rate limit exceeded: {e}",
                status_code=429,
                retry_after=retry_after,
            ) from e
            
        except APITimeoutError as e:
            raise AITimeoutError(f"Claude request timed out: {e}") from e
            
        except APIConnectionError as e:
            raise AIAPIError(
                f"Claude connection error: {e}",
                status_code=0,
            ) from e
            
        except APIError as e:
            status_code = 500
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            
            raise AIAPIError(
                f"Claude API error: {e}",
                status_code=status_code,
            ) from e

