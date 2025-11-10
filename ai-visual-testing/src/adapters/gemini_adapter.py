"""
Gemini Adapter for AI-driven testing framework.

This module provides Google Gemini integration with vision API support.
"""

import os
import json
import base64
import logging
from typing import Any, Dict, List, Optional
import time

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

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


class GeminiAdapter(AIAdapter):
    """
    Google Gemini adapter with vision API support.
    
    This adapter implements the AIAdapter interface using Google's Gemini API,
    supporting both text and vision (screenshot) analysis.
    """
    
    def __init__(
        self,
        model: str = "gemini-pro-vision",
        temperature: float = 0.2,
        max_tokens: Optional[int] = 2000,
        api_key: Optional[str] = None,
        api_key_env: str = "GOOGLE_API_KEY",
        enable_cache: bool = True,
        cache_ttl_seconds: int = 3600,
        max_retries: int = 3,
    ):
        """
        Initialize Gemini adapter.
        
        Args:
            model: Gemini model identifier (default: gemini-pro-vision)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            api_key: Google API key (if None, reads from environment)
            api_key_env: Environment variable name for API key
            enable_cache: Enable response caching
            cache_ttl_seconds: Cache time-to-live in seconds
            max_retries: Maximum retry attempts for API calls
        """
        if not GEMINI_AVAILABLE:
            raise AIConfigurationError(
                "Google Generative AI library not installed. Install with: pip install google-generativeai"
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
                f"Google API key not found. Set {api_key_env} environment variable or pass api_key parameter."
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(model_name=self.model)
        
        logger.info(f"Initialized GeminiAdapter with model: {model}")
    
    @handle_ai_errors
    @retry_on_api_error(max_attempts=3)
    async def analyze_page(
        self,
        screenshot: bytes,
        html: str,
        prompt: str,
    ) -> AIResponse:
        """Analyze a web page using Gemini vision API."""
        start_time = time.time()
        
        try:
            # Prepare content with image and text
            content_parts = [
                {
                    "mime_type": "image/png",
                    "data": screenshot
                },
                f"{prompt}\n\nHTML Content:\n{html[:2000]}"
            ]
            
            # Generate content
            response = await self.client.generate_content_async(
                content_parts,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                },
                system_instruction=SYSTEM_PROMPT_ANALYSIS,
            )
            
            # Extract response content
            content = ""
            if response.text:
                content = response.text
            
            # Extract usage information
            usage = None
            if hasattr(response, 'usage_metadata'):
                usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                }
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return AIResponse(
                content=content,
                model=self.model,
                usage=usage,
                metadata={"duration_ms": duration_ms},
            )
            
        except Exception as e:
            # Gemini doesn't have specific error types, so we handle generically
            error_str = str(e).lower()
            if "rate limit" in error_str or "quota" in error_str:
                raise AIAPIError(
                    f"Gemini rate limit exceeded: {e}",
                    status_code=429,
                ) from e
            elif "timeout" in error_str:
                raise AITimeoutError(f"Gemini request timed out: {e}") from e
            else:
                raise AIAPIError(
                    f"Gemini API error: {e}",
                    status_code=500,
                ) from e
    
    @handle_ai_errors
    @retry_on_api_error(max_attempts=3)
    async def verify_requirement(
        self,
        requirement: str,
        evidence: Dict[str, Any],
    ) -> VerificationResult:
        """Verify a specific requirement against evidence using Gemini."""
        start_time = time.time()
        
        screenshot = evidence.get("screenshot")
        html = evidence.get("html", "")
        url = evidence.get("url", "unknown")
        title = evidence.get("title", "unknown")
        
        if not screenshot:
            raise ValueError("Screenshot is required for verification")
        
        # Create verification prompt
        prompt = self._create_verification_prompt(requirement, evidence)
        
        # Prepare content with image and text
        content_parts = [
            {
                "mime_type": "image/png",
                "data": screenshot
            },
            prompt
        ]
        
        try:
            # Generate content
            response = await self.client.generate_content_async(
                content_parts,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                },
                system_instruction=SYSTEM_PROMPT_VERIFICATION,
            )
            
            # Extract response content
            content = ""
            if response.text:
                content = response.text
            
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
            
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str or "quota" in error_str:
                raise AIAPIError(
                    f"Gemini rate limit exceeded: {e}",
                    status_code=429,
                ) from e
            elif "timeout" in error_str:
                raise AITimeoutError(f"Gemini request timed out: {e}") from e
            else:
                raise AIAPIError(
                    f"Gemini API error: {e}",
                    status_code=500,
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
        
        try:
            # Generate content
            response = await self.client.generate_content_async(
                prompt,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                },
                system_instruction=SYSTEM_PROMPT_ELEMENT_EXTRACTION,
            )
            
            # Extract response content
            content = ""
            if response.text:
                content = response.text
            
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
            
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str or "quota" in error_str:
                raise AIAPIError(
                    f"Gemini rate limit exceeded: {e}",
                    status_code=429,
                ) from e
            elif "timeout" in error_str:
                raise AITimeoutError(f"Gemini request timed out: {e}") from e
            else:
                raise AIAPIError(
                    f"Gemini API error: {e}",
                    status_code=500,
                ) from e

