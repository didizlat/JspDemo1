"""
Provider Factory for AI-driven testing framework.

This module provides a factory for creating AI adapters based on configuration.
"""

import logging
from typing import Optional, Dict, Any, List

from src.adapters.base import AIAdapter, AIConfigurationError
from src.utils.config import AIConfig, AIProviderConfig


logger = logging.getLogger(__name__)


# Lazy imports to avoid dependency issues
def _import_openai_adapter():
    """Lazy import OpenAI adapter."""
    try:
        from src.adapters.openai_adapter import OpenAIAdapter
        return OpenAIAdapter
    except ImportError:
        return None


def _import_claude_adapter():
    """Lazy import Claude adapter."""
    try:
        from src.adapters.claude_adapter import ClaudeAdapter
        return ClaudeAdapter
    except ImportError:
        return None


def _import_gemini_adapter():
    """Lazy import Gemini adapter."""
    try:
        from src.adapters.gemini_adapter import GeminiAdapter
        return GeminiAdapter
    except ImportError:
        return None


def _import_custom_adapter():
    """Lazy import Custom adapter."""
    try:
        from src.adapters.custom_adapter import CustomAdapter
        return CustomAdapter
    except ImportError:
        return None


class AdapterFactory:
    """
    Factory for creating AI adapters.
    
    This factory creates adapter instances based on provider name and configuration.
    """
    
    # Provider registry
    _providers: Dict[str, Any] = {
        "openai": _import_openai_adapter,
        "claude": _import_claude_adapter,
        "gemini": _import_gemini_adapter,
        "custom": _import_custom_adapter,
    }
    
    @classmethod
    def create_adapter(
        cls,
        provider: str,
        config: Optional[AIProviderConfig] = None,
        **kwargs
    ) -> AIAdapter:
        """
        Create an AI adapter instance.
        
        Args:
            provider: Provider name (openai, claude, gemini, custom)
            config: Provider configuration (optional)
            **kwargs: Additional adapter-specific parameters
            
        Returns:
            AIAdapter instance
            
        Raises:
            AIConfigurationError: If provider not found or configuration invalid
        """
        provider_lower = provider.lower()
        
        if provider_lower not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise AIConfigurationError(
                f"Unknown provider: {provider}. Available providers: {available}"
            )
        
        # Get adapter class
        adapter_class_getter = cls._providers[provider_lower]
        adapter_class = adapter_class_getter()
        
        if adapter_class is None:
            raise AIConfigurationError(
                f"Provider '{provider}' is not available. "
                f"Install required dependencies or check configuration."
            )
        
        # Prepare adapter parameters
        adapter_kwargs = {}
        
        if config:
            adapter_kwargs["model"] = config.model
            adapter_kwargs["temperature"] = config.temperature
            adapter_kwargs["max_tokens"] = config.max_tokens
            
            # Set API key from environment if api_key_env is specified
            if config.api_key_env:
                import os
                api_key = os.getenv(config.api_key_env)
                if api_key:
                    adapter_kwargs["api_key"] = api_key
                adapter_kwargs["api_key_env"] = config.api_key_env
        
        # Override with explicit kwargs
        adapter_kwargs.update(kwargs)
        
        # Create adapter instance
        try:
            adapter = adapter_class(**adapter_kwargs)
            logger.info(f"Created {provider} adapter with model: {adapter_kwargs.get('model', 'default')}")
            return adapter
        except Exception as e:
            raise AIConfigurationError(
                f"Failed to create {provider} adapter: {e}"
            ) from e
    
    @classmethod
    def create_adapter_from_config(
        cls,
        ai_config: AIConfig,
        provider: Optional[str] = None,
        **kwargs
    ) -> AIAdapter:
        """
        Create an AI adapter from configuration.
        
        Args:
            ai_config: AI configuration object
            provider: Provider name (if None, uses default_provider)
            **kwargs: Additional adapter-specific parameters
            
        Returns:
            AIAdapter instance
        """
        provider_name = provider or ai_config.default_provider
        
        # Get provider configuration
        provider_config = ai_config.get_provider_config(provider_name)
        
        return cls.create_adapter(
            provider=provider_name,
            config=provider_config,
            **kwargs
        )
    
    @classmethod
    def register_provider(cls, name: str, adapter_class_getter):
        """
        Register a custom provider.
        
        Args:
            name: Provider name
            adapter_class_getter: Function that returns adapter class (or None if not available)
        """
        cls._providers[name.lower()] = adapter_class_getter
        logger.info(f"Registered custom provider: {name}")
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """List all available provider names."""
        return list(cls._providers.keys())
    
    @classmethod
    def is_provider_available(cls, provider: str) -> bool:
        """
        Check if a provider is available.
        
        Args:
            provider: Provider name
            
        Returns:
            True if provider is available, False otherwise
        """
        provider_lower = provider.lower()
        if provider_lower not in cls._providers:
            return False
        
        adapter_class_getter = cls._providers[provider_lower]
        adapter_class = adapter_class_getter()
        return adapter_class is not None

