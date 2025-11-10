"""
AI Adapters package for AI-driven testing framework.

This package contains adapters for various AI providers (OpenAI, Claude, Gemini)
and the base adapter interface.
"""

from .base import (
    AIAdapter,
    AIResponse,
    ResponseCache,
    AIAdapterError,
    AIAPIError,
    AITimeoutError,
    AIConfigurationError,
    handle_ai_errors,
    retry_on_api_error,
)

__all__ = [
    "AIAdapter",
    "AIResponse",
    "ResponseCache",
    "AIAdapterError",
    "AIAPIError",
    "AITimeoutError",
    "AIConfigurationError",
    "handle_ai_errors",
    "retry_on_api_error",
]
