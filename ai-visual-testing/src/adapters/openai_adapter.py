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
        
        # Validate model name
        if not model or not isinstance(model, str) or len(model.strip()) == 0:
            raise AIConfigurationError("Model name must be a non-empty string")
        
        # Validate temperature range
        if temperature < 0.0 or temperature > 2.0:
            raise AIConfigurationError(f"Temperature must be between 0.0 and 2.0, got {temperature}")
        
        # Validate max_tokens if provided
        if max_tokens is not None and (max_tokens < 1 or max_tokens > 100000):
            raise AIConfigurationError(f"max_tokens must be between 1 and 100000, got {max_tokens}")
        
        # Get API key
        self.api_key = api_key or os.getenv(api_key_env)
        if not self.api_key:
            raise AIConfigurationError(
                f"OpenAI API key not found. Set {api_key_env} environment variable or pass api_key parameter."
            )
        
        # Validate API key format (basic check - must be non-empty string)
        if not isinstance(self.api_key, str) or len(self.api_key.strip()) < 3:
            raise AIConfigurationError("API key must be a non-empty string with at least 3 characters")
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        logger.info(f"Initialized OpenAIAdapter with model: {model}, temperature: {temperature}, max_tokens: {max_tokens}")
    
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
        
        # Validate inputs
        if not screenshot or len(screenshot) == 0:
            raise ValueError("Screenshot must be non-empty bytes")
        if not isinstance(html, str):
            raise ValueError(f"HTML must be a string, got {type(html)}")
        if not prompt or not isinstance(prompt, str) or len(prompt.strip()) == 0:
            raise ValueError("Prompt must be a non-empty string")
        
        # Log request details (debug level)
        logger.debug(
            f"Analyzing page with OpenAI: model={self.model}, "
            f"screenshot_size={len(screenshot)} bytes, html_length={len(html)} chars, "
            f"prompt_length={len(prompt)} chars"
        )
        
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
            logger.debug(f"Making OpenAI API call: model={self.model}, messages_count={len(messages)}")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            logger.debug(f"OpenAI API call completed: response_id={getattr(response, 'id', 'unknown')}")
            
            # Extract response content
            content = response.choices[0].message.content or ""
            
            # Validate response content
            if not content or len(content.strip()) == 0:
                logger.warning("OpenAI returned empty response content")
                content = ""  # Ensure non-None value
            
            # Extract usage information (standardized format)
            usage = None
            if response.usage:
                usage = {
                    "input_tokens": getattr(response.usage, 'prompt_tokens', 0),
                    "output_tokens": getattr(response.usage, 'completion_tokens', 0),
                    "total_tokens": getattr(response.usage, 'total_tokens', 0),
                }
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log response summary
            logger.debug(
                f"OpenAI analyze_page completed: duration={duration_ms}ms, "
                f"content_length={len(content)}, usage={usage}"
            )
            
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
            
            logger.warning(
                f"OpenAI rate limit exceeded: {e}, retry_after={retry_after} seconds",
                exc_info=True
            )
            
            raise AIAPIError(
                f"OpenAI rate limit exceeded: {e}",
                status_code=429,
                retry_after=retry_after,
            ) from e
            
        except APITimeoutError as e:
            logger.error(f"OpenAI request timed out: {e}", exc_info=True)
            raise AITimeoutError(f"OpenAI request timed out: {e}") from e
        
        except APIConnectionError as e:
            logger.error(f"OpenAI connection error: {e}", exc_info=True)
            raise AIAPIError(
                f"OpenAI connection error: {e}",
                status_code=0,
            ) from e
        
        except APIError as e:
            status_code = 500
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            
            logger.error(
                f"OpenAI API error: status_code={status_code}, error={e}",
                exc_info=True
            )
            
            raise AIAPIError(
                f"OpenAI API error (status {status_code}): {e}",
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
        
        # Validate inputs
        if not requirement or not isinstance(requirement, str) or len(requirement.strip()) == 0:
            raise ValueError("Requirement must be a non-empty string")
        if not isinstance(evidence, dict):
            raise ValueError(f"Evidence must be a dictionary, got {type(evidence)}")
        
        screenshot = evidence.get("screenshot")
        html = evidence.get("html", "")
        url = evidence.get("url", "unknown")
        title = evidence.get("title", "unknown")
        
        if not screenshot:
            raise ValueError("Screenshot is required for verification")
        if not isinstance(screenshot, bytes) or len(screenshot) == 0:
            raise ValueError("Screenshot must be non-empty bytes")
        
        # Log request details (debug level)
        logger.debug(
            f"Verifying requirement with OpenAI: model={self.model}, "
            f"requirement='{requirement[:50]}...', url={url}, "
            f"screenshot_size={len(screenshot)} bytes"
        )
        
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
            
            # Validate response content
            if not content or len(content.strip()) == 0:
                raise ValueError("OpenAI returned empty response for verification")
            
            result_data = self._parse_json_response(content)
            
            # Validate response structure
            if not isinstance(result_data, dict):
                raise ValueError(f"Expected dict from OpenAI, got {type(result_data)}")
            
            # Extract verification result with validation
            passed = bool(result_data.get("passed", False))
            confidence = float(result_data.get("confidence", 0.0))
            # Clamp confidence to valid range
            confidence = max(0.0, min(100.0, confidence))
            reasoning = str(result_data.get("reasoning", "")).strip()
            issues_data = result_data.get("issues", [])
            
            # Validate issues is a list
            if not isinstance(issues_data, list):
                logger.warning(f"Expected list for issues, got {type(issues_data)}, using empty list")
                issues_data = []
            
            # Convert issues to Issue objects with validation
            issues = []
            for i, issue_data in enumerate(issues_data):
                if not isinstance(issue_data, dict):
                    logger.warning(f"Issue {i} is not a dictionary, skipping")
                    continue
                
                severity_str = issue_data.get("severity", "minor").lower()
                try:
                    severity = Severity(severity_str)
                except ValueError:
                    logger.warning(f"Invalid severity '{severity_str}' for issue {i}, using MINOR")
                    severity = Severity.MINOR
                
                description = str(issue_data.get("description", "")).strip()
                if not description:
                    logger.warning(f"Issue {i} has empty description, skipping")
                    continue
                
                issues.append(Issue(
                    severity=severity,
                    description=description,
                ))
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log verification result summary
            logger.debug(
                f"OpenAI verify_requirement completed: duration={duration_ms}ms, "
                f"passed={passed}, confidence={confidence:.1f}%, issues_count={len(issues)}"
            )
            
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
            logger.error(f"OpenAI request timed out: {e}", exc_info=True)
            raise AITimeoutError(f"OpenAI request timed out: {e}") from e
        
        except APIConnectionError as e:
            logger.error(f"OpenAI connection error: {e}", exc_info=True)
            raise AIAPIError(
                f"OpenAI connection error: {e}",
                status_code=0,
            ) from e
        
        except APIError as e:
            status_code = 500
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            
            logger.error(
                f"OpenAI API error: status_code={status_code}, error={e}",
                exc_info=True
            )
            
            raise AIAPIError(
                f"OpenAI API error (status {status_code}): {e}",
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
        # Validate inputs
        if not isinstance(html, str):
            raise ValueError(f"HTML must be a string, got {type(html)}")
        if not isinstance(element_descriptions, list):
            raise ValueError(f"element_descriptions must be a list, got {type(element_descriptions)}")
        if not element_descriptions:
            return {}
        
        # Validate each description
        valid_descriptions = []
        for i, desc in enumerate(element_descriptions):
            if not isinstance(desc, str) or len(desc.strip()) == 0:
                logger.warning(f"Element description {i} is invalid, skipping")
                continue
            valid_descriptions.append(desc.strip())
        
        if not valid_descriptions:
            logger.warning("No valid element descriptions provided")
            return {}
        
        # Log request details (debug level)
        logger.debug(
            f"Extracting elements with OpenAI: model={self.model}, "
            f"html_length={len(html)} chars, elements_count={len(valid_descriptions)}"
        )
        
        # Create prompt for element extraction
        descriptions_text = "\n".join(f"- {desc}" for desc in valid_descriptions)
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
            
            # Validate response content
            if not content or len(content.strip()) == 0:
                logger.warning("OpenAI returned empty response for element extraction")
                # Return all False if no response
                return {desc: False for desc in valid_descriptions}
            
            result_data = self._parse_json_response(content)
            
            # Validate response structure
            if not isinstance(result_data, dict):
                logger.warning(f"Expected dict from OpenAI, got {type(result_data)}, returning all False")
                return {desc: False for desc in valid_descriptions}
            
            # Convert to dictionary with boolean values
            result = {}
            for desc in valid_descriptions:
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
            
            # Log extraction result summary
            found_count = sum(1 for v in result.values() if v)
            logger.debug(
                f"OpenAI extract_elements completed: found={found_count}/{len(valid_descriptions)} elements"
            )
            
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
            logger.error(f"OpenAI request timed out: {e}", exc_info=True)
            raise AITimeoutError(f"OpenAI request timed out: {e}") from e
        
        except APIConnectionError as e:
            logger.error(f"OpenAI connection error: {e}", exc_info=True)
            raise AIAPIError(
                f"OpenAI connection error: {e}",
                status_code=0,
            ) from e
        
        except APIError as e:
            status_code = 500
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            
            logger.error(
                f"OpenAI API error: status_code={status_code}, error={e}",
                exc_info=True
            )
            
            raise AIAPIError(
                f"OpenAI API error (status {status_code}): {e}",
                status_code=status_code,
            ) from e

