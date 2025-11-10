"""
Test script for configuration system.

Run with: python -m src.utils.test_config
"""

import sys
import codecs
import os
import tempfile
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import yaml
from src.utils.config import (
    load_config,
    get_default_config,
    Config,
    AIConfig,
    BrowserConfig,
    TestingConfig,
    ReportingConfig,
    AIProviderConfig,
    ViewportConfig,
)


def test_default_config():
    """Test default configuration creation."""
    print("Testing default configuration...")
    
    config = get_default_config()
    
    assert config.ai.default_provider == "openai"
    assert "openai" in config.ai.providers
    assert config.browser.headless is False
    assert config.browser.viewport.width == 1920
    assert config.testing.base_url == "http://localhost:8080"
    assert config.reporting.format == "markdown"
    
    print("✅ Default configuration works")


def test_config_loading():
    """Test loading configuration from YAML file."""
    print("\nTesting configuration loading...")
    
    # Create temporary config file
    config_data = {
        "ai": {
            "default_provider": "openai",
            "providers": {
                "openai": {
                    "model": "gpt-4o",
                    "temperature": 0.3,
                    "max_tokens": 3000
                }
            }
        },
        "browser": {
            "headless": True,
            "viewport": {
                "width": 1280,
                "height": 720
            },
            "timeout": 60000
        },
        "testing": {
            "base_url": "http://example.com",
            "stop_on_failure": True
        },
        "reporting": {
            "output_dir": "./custom-reports",
            "format": "json"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        config = load_config(config_path)
        
        assert config.ai.default_provider == "openai"
        assert config.ai.providers["openai"].temperature == 0.3
        assert config.ai.providers["openai"].max_tokens == 3000
        assert config.browser.headless is True
        assert config.browser.viewport.width == 1280
        assert config.browser.viewport.height == 720
        assert config.browser.timeout == 60000
        assert config.testing.base_url == "http://example.com"
        assert config.testing.stop_on_failure is True
        assert config.reporting.output_dir == "./custom-reports"
        assert config.reporting.format == "json"
        
        print("✅ Configuration loading works")
    finally:
        os.unlink(config_path)


def test_environment_overrides():
    """Test environment variable overrides."""
    print("\nTesting environment variable overrides...")
    
    # Set environment variables
    os.environ["AI_DEFAULT_PROVIDER"] = "claude"
    os.environ["BROWSER_HEADLESS"] = "true"
    os.environ["TESTING_BASE_URL"] = "http://test.example.com"
    os.environ["BROWSER_VIEWPORT_WIDTH"] = "1600"
    
    try:
        # Create minimal config file
        config_data = {
            "ai": {
                "default_provider": "openai",
                "providers": {
                    "openai": {"model": "gpt-4o"},
                    "claude": {"model": "claude-3-opus-20240229"}
                }
            },
            "browser": {
                "headless": False,
                "viewport": {"width": 1920, "height": 1080}
            },
            "testing": {"base_url": "http://localhost:8080"},
            "reporting": {"output_dir": "./test-reports"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            
            # Check environment overrides
            assert config.ai.default_provider == "claude"
            assert config.browser.headless is True
            assert config.testing.base_url == "http://test.example.com"
            assert config.browser.viewport.width == 1600
            
            print("✅ Environment variable overrides work")
        finally:
            os.unlink(config_path)
    finally:
        # Clean up environment variables
        for key in ["AI_DEFAULT_PROVIDER", "BROWSER_HEADLESS", "TESTING_BASE_URL", "BROWSER_VIEWPORT_WIDTH"]:
            if key in os.environ:
                del os.environ[key]


def test_validation():
    """Test configuration validation."""
    print("\nTesting configuration validation...")
    
    # Test invalid temperature
    try:
        provider = AIProviderConfig(model="test", temperature=3.0)
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ Temperature validation works")
    
    # Test invalid viewport
    try:
        viewport = ViewportConfig(width=-1)
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ Viewport validation works")
    
    # Test invalid format
    try:
        reporting = ReportingConfig(format="invalid")
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ Format validation works")
    
    # Test missing provider
    try:
        ai_config = AIConfig(default_provider="nonexistent", providers={})
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ Provider validation works")


def test_config_methods():
    """Test configuration helper methods."""
    print("\nTesting configuration methods...")
    
    config = get_default_config()
    
    # Test AI provider config retrieval
    provider_config = config.ai.get_provider_config()
    assert provider_config.model == "gpt-4o"
    
    # Test path resolution
    output_path = config.reporting.get_output_path()
    assert isinstance(output_path, Path)
    
    screenshot_path = config.reporting.get_screenshot_path()
    assert isinstance(screenshot_path, Path)
    
    print("✅ Configuration methods work")


def test_default_yaml_loading():
    """Test loading default.yaml from config directory."""
    print("\nTesting default.yaml loading...")
    
    try:
        # Temporarily set API keys to avoid validation errors
        original_env = {}
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]:
            if key in os.environ:
                original_env[key] = os.environ[key]
            os.environ[key] = "test-key"
        
        try:
            config = load_config()  # Should load config/default.yaml
            assert config is not None
            assert config.ai.default_provider == "openai"
            print("✅ Default YAML loading works")
        finally:
            # Restore original environment
            for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]:
                if key in original_env:
                    os.environ[key] = original_env[key]
                elif key in os.environ:
                    del os.environ[key]
    except FileNotFoundError:
        print("⚠️  Default YAML not found (this is OK if running from different directory)")


if __name__ == "__main__":
    print("=" * 60)
    print("Configuration System Test Suite")
    print("=" * 60)
    
    try:
        test_default_config()
        test_config_loading()
        test_environment_overrides()
        test_validation()
        test_config_methods()
        test_default_yaml_loading()
        
        print("\n" + "=" * 60)
        print("✅ All configuration tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

