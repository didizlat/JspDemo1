"""
Test script for adapter factory and multi-provider support.

Run with: python -m src.adapters.test_factory
"""

import sys
import codecs
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.adapters.factory import AdapterFactory
from src.adapters.base import AIAdapter, AIConfigurationError
from src.utils.config import AIConfig, AIProviderConfig


# ============================================================================
# Tests
# ============================================================================

def test_factory_list_providers():
    """Test listing providers."""
    print("Testing factory list_providers...")
    
    providers = AdapterFactory.list_providers()
    assert isinstance(providers, list)
    assert "openai" in providers
    assert "claude" in providers
    assert "gemini" in providers
    assert "custom" in providers
    print("✅ list_providers works")


def test_factory_create_openai_adapter():
    """Test creating OpenAI adapter via factory."""
    print("\nTesting factory create OpenAI adapter...")
    
    with patch('src.adapters.openai_adapter.AsyncOpenAI') as mock_openai_class:
        mock_client = AsyncMock()
        mock_openai_class.return_value = mock_client
        
        config = AIProviderConfig(
            model="gpt-4o",
            temperature=0.2,
            max_tokens=2000,
            api_key_env="OPENAI_API_KEY",
        )
        
        import os
        os.environ["OPENAI_API_KEY"] = "test-key"
        
        try:
            adapter = AdapterFactory.create_adapter("openai", config=config)
            assert adapter is not None
            assert adapter.model == "gpt-4o"
            print("✅ Factory creates OpenAI adapter")
        finally:
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]


def test_factory_create_from_config():
    """Test creating adapter from config."""
    print("\nTesting factory create from config...")
    
    with patch('src.adapters.openai_adapter.AsyncOpenAI') as mock_openai_class:
        mock_client = AsyncMock()
        mock_openai_class.return_value = mock_client
        
        # Create AI config
        providers = {
            "openai": AIProviderConfig(
                model="gpt-4o",
                temperature=0.2,
                api_key_env="OPENAI_API_KEY",
            )
        }
        ai_config = AIConfig(
            default_provider="openai",
            providers=providers,
        )
        
        import os
        os.environ["OPENAI_API_KEY"] = "test-key"
        
        try:
            adapter = AdapterFactory.create_adapter_from_config(ai_config)
            assert adapter is not None
            assert adapter.model == "gpt-4o"
            print("✅ Factory creates adapter from config")
        finally:
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]


def test_factory_unknown_provider():
    """Test factory with unknown provider."""
    print("\nTesting factory with unknown provider...")
    
    try:
        AdapterFactory.create_adapter("unknown-provider")
        assert False, "Should have raised AIConfigurationError"
    except AIConfigurationError:
        print("✅ Unknown provider error handling works")


def test_factory_provider_availability():
    """Test checking provider availability."""
    print("\nTesting provider availability check...")
    
    # OpenAI should be available (we have it installed)
    available = AdapterFactory.is_provider_available("openai")
    assert isinstance(available, bool)
    print("✅ Provider availability check works")


def test_factory_register_custom_provider():
    """Test registering custom provider."""
    print("\nTesting custom provider registration...")
    
    # Create a mock adapter class
    class MockAdapter(AIAdapter):
        async def analyze_page(self, screenshot, html, prompt):
            from src.adapters.base import AIResponse
            return AIResponse(content="test", model="mock")
        
        async def verify_requirement(self, requirement, evidence):
            from src.models import VerificationResult
            return VerificationResult(requirement=requirement, passed=True, confidence=100.0)
        
        async def extract_elements(self, html, descriptions):
            return {desc: True for desc in descriptions}
    
    # Register custom provider
    AdapterFactory.register_provider("mock", lambda: MockAdapter)
    
    # Verify it's registered
    providers = AdapterFactory.list_providers()
    assert "mock" in providers
    
    # Create adapter
    adapter = AdapterFactory.create_adapter("mock", model="mock-model")
    assert isinstance(adapter, MockAdapter)
    print("✅ Custom provider registration works")


async def test_custom_adapter():
    """Test CustomAdapter with mock functions."""
    print("\nTesting CustomAdapter...")
    
    from src.adapters.custom_adapter import CustomAdapter
    
    # Define custom functions
    async def analyze_func(screenshot, html, prompt):
        return {
            "content": f"Analysis: {prompt}",
            "usage": {"tokens": 100},
        }
    
    async def verify_func(requirement, evidence):
        return {
            "passed": True,
            "confidence": 95.0,
            "reasoning": "Test reasoning",
            "issues": [],
        }
    
    async def extract_func(html, descriptions):
        return {desc: True for desc in descriptions}
    
    adapter = CustomAdapter(
        model="custom-model",
        analyze_func=analyze_func,
        verify_func=verify_func,
        extract_func=extract_func,
        enable_cache=False,
    )
    
    # Test analyze_page
    response = await adapter.analyze_page(b"test", "<html>", "test prompt")
    assert "test prompt" in response.content
    
    # Test verify_requirement
    evidence = {"screenshot": b"test", "html": "<html>", "url": "http://test.com"}
    result = await adapter.verify_requirement("Test requirement", evidence)
    assert result.passed is True
    assert result.confidence == 95.0
    
    # Test extract_elements
    elements = await adapter.extract_elements("<html>", ["button", "form"])
    assert elements["button"] is True
    assert elements["form"] is True
    
    print("✅ CustomAdapter works")


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Adapter Factory & Multi-Provider Test Suite")
    print("=" * 60)
    
    test_factory_list_providers()
    test_factory_create_openai_adapter()
    test_factory_create_from_config()
    test_factory_unknown_provider()
    test_factory_provider_availability()
    test_factory_register_custom_provider()
    await test_custom_adapter()
    
    print("\n" + "=" * 60)
    print("✅ All factory and multi-provider tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

