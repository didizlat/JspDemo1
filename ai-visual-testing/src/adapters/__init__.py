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

# Import adapters (lazy import to avoid dependency issues)
try:
    from .openai_adapter import OpenAIAdapter
except ImportError:
    OpenAIAdapter = None  # type: ignore

try:
    from .claude_adapter import ClaudeAdapter
except ImportError:
    ClaudeAdapter = None  # type: ignore

try:
    from .gemini_adapter import GeminiAdapter
except ImportError:
    GeminiAdapter = None  # type: ignore

try:
    from .custom_adapter import CustomAdapter
except ImportError:
    CustomAdapter = None  # type: ignore

# Import factory
from .factory import AdapterFactory

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
    "OpenAIAdapter",
    "ClaudeAdapter",
    "GeminiAdapter",
    "CustomAdapter",
    "AdapterFactory",
]
