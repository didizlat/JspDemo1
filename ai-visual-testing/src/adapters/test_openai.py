"""
Test script for OpenAI adapter with mocked API.

Run with: python -m src.adapters.test_openai
"""

import sys
import codecs
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.adapters.openai_adapter import OpenAIAdapter
from src.adapters.base import AIAPIError, AITimeoutError, AIConfigurationError
from src.models import VerificationResult, Severity


# ============================================================================
# Mock OpenAI Client
# ============================================================================

def create_mock_openai_client():
    """Create a mock OpenAI client."""
    mock_client = AsyncMock()
    mock_chat = AsyncMock()
    mock_completions = AsyncMock()
    mock_client.chat = mock_chat
    mock_chat.completions = mock_completions
    return mock_client, mock_completions


# ============================================================================
# Tests
# ============================================================================

async def test_adapter_initialization():
    """Test adapter initialization."""
    print("Testing adapter initialization...")
    
    import os
    
    # Mock AsyncOpenAI to avoid actual client initialization
    with patch('src.adapters.openai_adapter.AsyncOpenAI') as mock_openai_class:
        mock_client = AsyncMock()
        mock_openai_class.return_value = mock_client
        
        # Test with API key parameter
        adapter = OpenAIAdapter(
            model="gpt-4o",
            api_key="test-key-123",
            enable_cache=False,
        )
        assert adapter.model == "gpt-4o"
        assert adapter.api_key == "test-key-123"
        print("✅ Initialization with API key works")
        
        # Test with environment variable
        os.environ["OPENAI_API_KEY"] = "env-key-456"
        adapter = OpenAIAdapter(enable_cache=False)
        assert adapter.api_key == "env-key-456"
        print("✅ Initialization with environment variable works")
        
        # Test missing API key
        del os.environ["OPENAI_API_KEY"]
        try:
            OpenAIAdapter(enable_cache=False)
            assert False, "Should have raised AIConfigurationError"
        except AIConfigurationError:
            print("✅ Missing API key detection works")
        
        # Restore for other tests
        os.environ["OPENAI_API_KEY"] = "test-key"


async def test_analyze_page():
    """Test analyze_page method."""
    print("\nTesting analyze_page...")
    
    with patch('src.adapters.openai_adapter.AsyncOpenAI') as mock_openai_class:
        mock_client, mock_completions = create_mock_openai_client()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(api_key="test-key", enable_cache=False)
    
    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a test page analysis."
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150
    
    mock_completions.create = AsyncMock(return_value=mock_response)
    
    # Test analyze_page
    screenshot = b"fake screenshot data"
    html = "<html><body>Test</body></html>"
    prompt = "Analyze this page"
    
    response = await adapter.analyze_page(screenshot, html, prompt)
    
    assert isinstance(response.content, str)
    assert "test page analysis" in response.content.lower()
    assert response.model == "gpt-4o"
    assert response.usage is not None
    assert response.usage["total_tokens"] == 150
    
    # Verify API was called correctly
    mock_completions.create.assert_called_once()
    call_args = mock_completions.create.call_args
    assert call_args.kwargs["model"] == "gpt-4o"
    assert len(call_args.kwargs["messages"]) == 2
    
    print("✅ analyze_page works")


async def test_verify_requirement():
    """Test verify_requirement method."""
    print("\nTesting verify_requirement...")
    
    with patch('src.adapters.openai_adapter.AsyncOpenAI') as mock_openai_class:
        mock_client, mock_completions = create_mock_openai_client()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(api_key="test-key", enable_cache=False)
    
    # Mock response with JSON
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "passed": True,
        "confidence": 95.5,
        "reasoning": "The page meets all requirements",
        "issues": [
            {
                "severity": "minor",
                "description": "Minor styling issue"
            }
        ]
    })
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 200
    mock_response.usage.completion_tokens = 100
    mock_response.usage.total_tokens = 300
    
    mock_completions.create = AsyncMock(return_value=mock_response)
    
    # Test verify_requirement
    evidence = {
        "screenshot": b"fake screenshot",
        "html": "<html><body>Test</body></html>",
        "url": "http://test.com",
        "title": "Test Page",
    }
    
    result = await adapter.verify_requirement("Page should load", evidence)
    
    assert isinstance(result, VerificationResult)
    assert result.passed is True
    assert result.confidence == 95.5
    assert len(result.issues) == 1
    assert result.issues[0].severity == Severity.MINOR
    assert result.duration_ms is not None
    
    print("✅ verify_requirement works")


async def test_extract_elements():
    """Test extract_elements method."""
    print("\nTesting extract_elements...")
    
    with patch('src.adapters.openai_adapter.AsyncOpenAI') as mock_openai_class:
        mock_client, mock_completions = create_mock_openai_client()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(api_key="test-key", enable_cache=False)
    
    # Mock response with JSON
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "Submit button": True,
        "Login form": False,
        "Navigation menu": True,
    })
    
    mock_completions.create = AsyncMock(return_value=mock_response)
    
    # Test extract_elements
    html = "<html><body><button>Submit</button><nav>Menu</nav></body></html>"
    descriptions = ["Submit button", "Login form", "Navigation menu"]
    
    result = await adapter.extract_elements(html, descriptions)
    
    assert isinstance(result, dict)
    assert result["Submit button"] is True
    assert result["Login form"] is False
    assert result["Navigation menu"] is True
    
    print("✅ extract_elements works")


async def test_error_handling():
    """Test error handling."""
    print("\nTesting error handling...")
    
    with patch('src.adapters.openai_adapter.AsyncOpenAI') as mock_openai_class:
        mock_client, mock_completions = create_mock_openai_client()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(api_key="test-key", enable_cache=False)
    
    # Test rate limit error
    from openai import RateLimitError
    mock_response_obj = MagicMock()
    mock_response_obj.headers = {"retry-after": "60"}
    mock_completions.create = AsyncMock(side_effect=RateLimitError(
        message="Rate limit exceeded",
        response=mock_response_obj,
        body={"error": {"message": "Rate limit exceeded"}},
    ))
    
    try:
        await adapter.analyze_page(b"test", "<html>", "test")
        assert False, "Should have raised AIAPIError"
    except AIAPIError as e:
        assert e.status_code == 429
        assert e.retry_after == 60
        print("✅ Rate limit error handling works")
    
    # Test timeout error - create exception instance directly
    from openai import APITimeoutError
    timeout_error = APITimeoutError(request=MagicMock())
    mock_completions.create = AsyncMock(side_effect=timeout_error)
    
    try:
        await adapter.analyze_page(b"test", "<html>", "test")
        assert False, "Should have raised AITimeoutError"
    except AITimeoutError:
        print("✅ Timeout error handling works")
    
    # Test API error - create exception instance directly
    from openai import APIError
    api_error = APIError(
        message="API error",
        request=MagicMock(),
        body={"error": {"message": "API error"}},
    )
    # Set status_code attribute directly
    api_error.status_code = 500
    mock_completions.create = AsyncMock(side_effect=api_error)
    
    try:
        await adapter.analyze_page(b"test", "<html>", "test")
        assert False, "Should have raised AIAPIError"
    except AIAPIError as e:
        assert e.status_code == 500
        print("✅ API error handling works")


async def test_caching():
    """Test caching functionality."""
    print("\nTesting caching...")
    
    with patch('src.adapters.openai_adapter.AsyncOpenAI') as mock_openai_class:
        mock_client, mock_completions = create_mock_openai_client()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(api_key="test-key", enable_cache=True)
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Cached response"
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150
    
    mock_completions.create = AsyncMock(return_value=mock_response)
    
    screenshot = b"test screenshot"
    html = "<html>Test</html>"
    prompt = "Test prompt"
    
    # First call
    response1 = await adapter.analyze_page_cached(screenshot, html, prompt)
    assert mock_completions.create.call_count == 1
    
    # Second call should use cache
    response2 = await adapter.analyze_page_cached(screenshot, html, prompt)
    assert mock_completions.create.call_count == 1  # Should not increment
    
    assert response1.content == response2.content
    print("✅ Caching works")


async def test_json_parsing():
    """Test JSON parsing with markdown code blocks."""
    print("\nTesting JSON parsing...")
    
    with patch('src.adapters.openai_adapter.AsyncOpenAI') as mock_openai_class:
        mock_client = AsyncMock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(api_key="test-key", enable_cache=False)
    
    # Test normal JSON
    json_str = '{"test": "value"}'
    parsed = adapter._parse_json_response(json_str)
    assert parsed["test"] == "value"
    
    # Test JSON with markdown code block
    json_with_markdown = "```json\n" + json_str + "\n```"
    parsed = adapter._parse_json_response(json_with_markdown)
    assert parsed["test"] == "value"
    
    # Test JSON with just code block markers
    json_with_markers = "```\n" + json_str + "\n```"
    parsed = adapter._parse_json_response(json_with_markers)
    assert parsed["test"] == "value"
    
    print("✅ JSON parsing works")


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("OpenAI Adapter Test Suite")
    print("=" * 60)
    
    await test_adapter_initialization()
    await test_analyze_page()
    await test_verify_requirement()
    await test_extract_elements()
    await test_error_handling()
    await test_caching()
    await test_json_parsing()
    
    print("\n" + "=" * 60)
    print("✅ All OpenAI adapter tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

