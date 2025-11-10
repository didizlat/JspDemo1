"""
Test script for base AI adapter.

Run with: python -m src.adapters.test_base
"""

import sys
import codecs
import asyncio
from pathlib import Path
from typing import Dict, List, Any

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.adapters.base import (
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


# ============================================================================
# Mock Adapter for Testing
# ============================================================================

class MockAIAdapter(AIAdapter):
    """Mock AI adapter for testing."""
    
    def __init__(self, **kwargs):
        super().__init__(model="mock-model", **kwargs)
        self.call_count = 0
    
    async def analyze_page(self, screenshot: bytes, html: str, prompt: str) -> AIResponse:
        """Mock implementation."""
        self.call_count += 1
        return AIResponse(
            content=f"Mock analysis for: {prompt[:50]}...",
            model=self.model,
            usage={"tokens_used": 100, "tokens_total": 1000},
        )
    
    async def verify_requirement(self, requirement: str, evidence: Dict[str, Any]):
        """Mock implementation."""
        from src.models import VerificationResult
        
        self.call_count += 1
        return VerificationResult(
            requirement=requirement,
            passed=True,
            confidence=95.0,
            ai_reasoning="Mock verification passed",
        )
    
    async def extract_elements(self, html: str, element_descriptions: List[str]) -> Dict[str, bool]:
        """Mock implementation."""
        self.call_count += 1
        return {desc: True for desc in element_descriptions}


# ============================================================================
# Tests
# ============================================================================

def test_response_cache():
    """Test response cache functionality."""
    print("Testing response cache...")
    
    cache = ResponseCache(ttl_seconds=60, max_size=10)
    
    # Test cache miss
    response = cache.get("test prompt")
    assert response is None
    print("✅ Cache miss works")
    
    # Test cache set/get
    test_response = AIResponse(content="test", model="test-model")
    cache.set("test prompt", test_response)
    
    cached = cache.get("test prompt")
    assert cached is not None
    assert cached.content == "test"
    print("✅ Cache set/get works")
    
    # Test cache size limit
    for i in range(15):
        cache.set(f"prompt{i}", AIResponse(content=str(i), model="test"))
    
    assert cache.size() == 10  # Should be limited to max_size
    print("✅ Cache size limit works")
    
    # Test cache clear
    cache.clear()
    assert cache.size() == 0
    print("✅ Cache clear works")


def test_exceptions():
    """Test exception classes."""
    print("\nTesting exceptions...")
    
    # Test base exception
    try:
        raise AIAdapterError("Test error")
    except AIAdapterError as e:
        assert str(e) == "Test error"
        print("✅ AIAdapterError works")
    
    # Test API error
    try:
        raise AIAPIError("API error", status_code=429, retry_after=60)
    except AIAPIError as e:
        assert e.status_code == 429
        assert e.retry_after == 60
        print("✅ AIAPIError works")
    
    # Test timeout error
    try:
        raise AITimeoutError("Timeout")
    except AITimeoutError:
        print("✅ AITimeoutError works")
    
    # Test configuration error
    try:
        raise AIConfigurationError("Config error")
    except AIConfigurationError:
        print("✅ AIConfigurationError works")


async def test_mock_adapter():
    """Test mock adapter implementation."""
    print("\nTesting mock adapter...")
    
    adapter = MockAIAdapter(enable_cache=True)
    
    # Test analyze_page
    screenshot = b"fake screenshot data"
    html = "<html><body>Test</body></html>"
    response = await adapter.analyze_page(screenshot, html, "Test prompt")
    
    assert isinstance(response, AIResponse)
    assert response.model == "mock-model"
    assert "Test prompt" in response.content
    print("✅ analyze_page works")
    
    # Test verify_requirement
    evidence = {
        "screenshot": screenshot,
        "html": html,
        "url": "http://test.com",
        "title": "Test Page",
    }
    result = await adapter.verify_requirement("Test requirement", evidence)
    
    assert result.passed is True
    assert result.confidence == 95.0
    print("✅ verify_requirement works")
    
    # Test extract_elements
    elements = await adapter.extract_elements(html, ["button", "form"])
    assert elements["button"] is True
    assert elements["form"] is True
    print("✅ extract_elements works")


async def test_caching():
    """Test caching functionality."""
    print("\nTesting caching...")
    
    adapter = MockAIAdapter(enable_cache=True)
    
    screenshot = b"fake screenshot"
    html = "<html>Test</html>"
    prompt = "Test prompt"
    
    # First call should hit API
    response1 = await adapter.analyze_page_cached(screenshot, html, prompt)
    assert adapter.call_count == 1
    
    # Second call should use cache
    response2 = await adapter.analyze_page_cached(screenshot, html, prompt)
    assert adapter.call_count == 1  # Should not increment
    
    assert response1.content == response2.content
    print("✅ Caching works")
    
    # Test cache stats
    stats = adapter.get_cache_stats()
    assert stats["enabled"] is True
    assert stats["size"] > 0
    print("✅ Cache stats work")
    
    # Test cache clear
    adapter.clear_cache()
    stats = adapter.get_cache_stats()
    assert stats["size"] == 0
    print("✅ Cache clear works")


def test_helper_methods():
    """Test helper methods."""
    print("\nTesting helper methods...")
    
    adapter = MockAIAdapter()
    
    # Test screenshot hash
    screenshot = b"test data"
    hash1 = adapter._hash_screenshot(screenshot)
    hash2 = adapter._hash_screenshot(screenshot)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex length
    print("✅ Screenshot hashing works")
    
    # Test HTML hash
    html = "<html>Test</html>"
    hash1 = adapter._hash_html(html)
    hash2 = adapter._hash_html(html)
    assert hash1 == hash2
    print("✅ HTML hashing works")
    
    # Test screenshot encoding
    encoded = adapter._encode_screenshot(screenshot)
    assert isinstance(encoded, str)
    # Should be valid base64
    import base64
    decoded = base64.b64decode(encoded)
    assert decoded == screenshot
    print("✅ Screenshot encoding works")
    
    # Test JSON parsing
    json_str = '{"test": "value"}'
    parsed = adapter._parse_json_response(json_str)
    assert parsed["test"] == "value"
    
    # Test JSON parsing with markdown code blocks
    json_with_markdown = "```json\n" + json_str + "\n```"
    parsed = adapter._parse_json_response(json_with_markdown)
    assert parsed["test"] == "value"
    print("✅ JSON parsing works")
    
    # Test verification prompt creation
    evidence = {
        "url": "http://test.com",
        "title": "Test Page",
    }
    prompt = adapter._create_verification_prompt("Test requirement", evidence)
    assert "Test requirement" in prompt
    assert "http://test.com" in prompt
    assert "Test Page" in prompt
    print("✅ Verification prompt creation works")


async def test_error_handling():
    """Test error handling decorators."""
    print("\nTesting error handling...")
    
    class FailingAdapter(MockAIAdapter):
        async def analyze_page(self, screenshot: bytes, html: str, prompt: str) -> AIResponse:
            raise AIAPIError("API error", status_code=500)
    
    adapter = FailingAdapter()
    
    try:
        await adapter.analyze_page_cached(b"test", "<html>", "test")
        assert False, "Should have raised exception"
    except AIAPIError:
        print("✅ Error handling works")


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Base AI Adapter Test Suite")
    print("=" * 60)
    
    test_response_cache()
    test_exceptions()
    await test_mock_adapter()
    await test_caching()
    test_helper_methods()
    await test_error_handling()
    
    print("\n" + "=" * 60)
    print("✅ All base adapter tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

