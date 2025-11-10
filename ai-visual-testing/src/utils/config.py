"""
Configuration system for AI-driven testing framework.

This module provides configuration loading, validation, and environment variable
support for the testing framework.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, List
import yaml


# ============================================================================
# Configuration Data Classes
# ============================================================================

@dataclass
class AIProviderConfig:
    """Configuration for a single AI provider."""
    model: str
    temperature: float = 0.2
    max_tokens: Optional[int] = None
    api_key_env: Optional[str] = None
    
    def __post_init__(self):
        """Validate AI provider configuration."""
        if not self.model or not self.model.strip():
            raise ValueError("AI model name cannot be empty")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"Temperature must be between 0.0 and 2.0, got {self.temperature}")
        if self.max_tokens is not None and self.max_tokens < 1:
            raise ValueError(f"max_tokens must be >= 1, got {self.max_tokens}")


@dataclass
class AIConfig:
    """AI configuration section."""
    default_provider: str = "openai"
    providers: Dict[str, AIProviderConfig] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate AI configuration."""
        if not self.default_provider:
            raise ValueError("default_provider cannot be empty")
        if self.default_provider not in self.providers:
            raise ValueError(f"default_provider '{self.default_provider}' not found in providers")
    
    def get_provider_config(self, provider: Optional[str] = None) -> AIProviderConfig:
        """Get configuration for a specific provider or default."""
        provider_name = provider or self.default_provider
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not configured")
        return self.providers[provider_name]


@dataclass
class ViewportConfig:
    """Browser viewport configuration."""
    width: int = 1920
    height: int = 1080
    
    def __post_init__(self):
        """Validate viewport configuration."""
        if self.width < 1:
            raise ValueError(f"Viewport width must be >= 1, got {self.width}")
        if self.height < 1:
            raise ValueError(f"Viewport height must be >= 1, got {self.height}")


@dataclass
class BrowserConfig:
    """Browser configuration section."""
    headless: bool = False
    viewport: ViewportConfig = field(default_factory=ViewportConfig)
    timeout: int = 30000  # milliseconds
    slow_mo: int = 500  # milliseconds
    browser_type: str = "chromium"  # chromium, firefox, webkit
    
    def __post_init__(self):
        """Validate browser configuration."""
        if self.timeout < 0:
            raise ValueError(f"Timeout must be >= 0, got {self.timeout}")
        if self.slow_mo < 0:
            raise ValueError(f"Slow motion must be >= 0, got {self.slow_mo}")
        if self.browser_type not in ["chromium", "firefox", "webkit"]:
            raise ValueError(f"Browser type must be chromium, firefox, or webkit, got {self.browser_type}")


@dataclass
class TestingConfig:
    """Testing configuration section."""
    base_url: str = "http://localhost:8080"
    screenshot_on_failure: bool = True
    save_html_on_failure: bool = True
    console_error_threshold: int = 0
    stop_on_failure: bool = False
    max_retries: int = 0
    
    def __post_init__(self):
        """Validate testing configuration."""
        if not self.base_url:
            raise ValueError("base_url cannot be empty")
        if self.console_error_threshold < 0:
            raise ValueError(f"console_error_threshold must be >= 0, got {self.console_error_threshold}")
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {self.max_retries}")


@dataclass
class ReportingConfig:
    """Reporting configuration section."""
    output_dir: str = "./test-reports"
    screenshot_dir: str = "./screenshots"
    format: str = "markdown"  # markdown, json, html
    include_screenshots: bool = True
    include_html_snapshots: bool = False
    template_path: Optional[str] = None
    
    def __post_init__(self):
        """Validate reporting configuration."""
        if not self.output_dir:
            raise ValueError("output_dir cannot be empty")
        if not self.screenshot_dir:
            raise ValueError("screenshot_dir cannot be empty")
        if self.format not in ["markdown", "json", "html"]:
            raise ValueError(f"Format must be markdown, json, or html, got {self.format}")
    
    def get_output_path(self) -> Path:
        """Get output directory as Path object."""
        return Path(self.output_dir).expanduser().resolve()
    
    def get_screenshot_path(self) -> Path:
        """Get screenshot directory as Path object."""
        return Path(self.screenshot_dir).expanduser().resolve()


@dataclass
class Config:
    """Main configuration class."""
    ai: AIConfig
    browser: BrowserConfig
    testing: TestingConfig
    reporting: ReportingConfig
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        # Parse AI config
        ai_data = data.get("ai", {})
        providers = {}
        for name, provider_data in ai_data.get("providers", {}).items():
            providers[name] = AIProviderConfig(**provider_data)
        ai_config = AIConfig(
            default_provider=ai_data.get("default_provider", "openai"),
            providers=providers
        )
        
        # Parse browser config
        browser_data = data.get("browser", {})
        viewport_data = browser_data.get("viewport", {})
        browser_config = BrowserConfig(
            headless=browser_data.get("headless", False),
            viewport=ViewportConfig(**viewport_data),
            timeout=browser_data.get("timeout", 30000),
            slow_mo=browser_data.get("slow_mo", 500),
            browser_type=browser_data.get("browser_type", "chromium")
        )
        
        # Parse testing config
        testing_data = data.get("testing", {})
        testing_config = TestingConfig(**testing_data)
        
        # Parse reporting config
        reporting_data = data.get("reporting", {})
        reporting_config = ReportingConfig(**reporting_data)
        
        return cls(
            ai=ai_config,
            browser=browser_config,
            testing=testing_config,
            reporting=reporting_config
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate AI API keys (only if api_key_env is specified)
        for provider_name, provider_config in self.ai.providers.items():
            if provider_config.api_key_env:
                if provider_config.api_key_env not in os.environ:
                    errors.append(
                        f"AI provider '{provider_name}' requires environment variable "
                        f"'{provider_config.api_key_env}' but it is not set"
                    )
        
        # Validate directories (try to create if they don't exist)
        try:
            output_path = self.reporting.get_output_path()
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create output directory: {e}")
        
        try:
            screenshot_path = self.reporting.get_screenshot_path()
            screenshot_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create screenshot directory: {e}")
        
        return errors


# ============================================================================
# Configuration Loading
# ============================================================================

def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from YAML file with environment variable overrides.
    
    Args:
        config_path: Path to YAML config file. If None, uses default.yaml
        
    Returns:
        Config object with loaded configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If configuration is invalid
    """
    if config_path is None:
        # Default to config/default.yaml relative to this file
        config_dir = Path(__file__).parent.parent.parent / "config"
        config_path = config_dir / "default.yaml"
    
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Load YAML
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    
    # Apply environment variable overrides
    _apply_env_overrides(data)
    
    # Create config object
    try:
        config = Config.from_dict(data)
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}") from e
    
    # Validate configuration
    errors = config.validate()
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)
    
    return config


def _apply_env_overrides(data: Dict[str, Any]) -> None:
    """Apply environment variable overrides to configuration."""
    def set_nested_path(path: str, value: Any) -> None:
        """Set a nested path in the dictionary."""
        parts = path.split(".")
        node = data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    
    def parse_value(value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        value_lower = value.lower().strip()
        
        # Boolean
        if value_lower in ("true", "false", "yes", "no", "1", "0"):
            return value_lower in ("true", "yes", "1")
        
        # Integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float
        try:
            return float(value)
        except ValueError:
            pass
        
        # String (default)
        return value
    
    # Environment variable mappings
    env_mappings = {
        # AI Configuration
        "AI_DEFAULT_PROVIDER": "ai.default_provider",
        "AI_OPENAI_MODEL": "ai.providers.openai.model",
        "AI_OPENAI_TEMPERATURE": "ai.providers.openai.temperature",
        "AI_OPENAI_MAX_TOKENS": "ai.providers.openai.max_tokens",
        "AI_CLAUDE_MODEL": "ai.providers.claude.model",
        "AI_CLAUDE_TEMPERATURE": "ai.providers.claude.temperature",
        "AI_GEMINI_MODEL": "ai.providers.gemini.model",
        "AI_GEMINI_TEMPERATURE": "ai.providers.gemini.temperature",
        
        # Browser Configuration
        "BROWSER_HEADLESS": "browser.headless",
        "BROWSER_TIMEOUT": "browser.timeout",
        "BROWSER_SLOW_MO": "browser.slow_mo",
        "BROWSER_TYPE": "browser.browser_type",
        "BROWSER_VIEWPORT_WIDTH": "browser.viewport.width",
        "BROWSER_VIEWPORT_HEIGHT": "browser.viewport.height",
        
        # Testing Configuration
        "TESTING_BASE_URL": "testing.base_url",
        "TESTING_SCREENSHOT_ON_FAILURE": "testing.screenshot_on_failure",
        "TESTING_SAVE_HTML_ON_FAILURE": "testing.save_html_on_failure",
        "TESTING_CONSOLE_ERROR_THRESHOLD": "testing.console_error_threshold",
        "TESTING_STOP_ON_FAILURE": "testing.stop_on_failure",
        "TESTING_MAX_RETRIES": "testing.max_retries",
        
        # Reporting Configuration
        "REPORTING_OUTPUT_DIR": "reporting.output_dir",
        "REPORTING_SCREENSHOT_DIR": "reporting.screenshot_dir",
        "REPORTING_FORMAT": "reporting.format",
        "REPORTING_INCLUDE_SCREENSHOTS": "reporting.include_screenshots",
        "REPORTING_INCLUDE_HTML_SNAPSHOTS": "reporting.include_html_snapshots",
    }
    
    # Apply environment variables
    for env_key, config_path in env_mappings.items():
        if env_key in os.environ:
            value = os.environ[env_key]
            if value:  # Only override if value is not empty
                parsed_value = parse_value(value)
                set_nested_path(config_path, parsed_value)


def get_default_config() -> Config:
    """Get default configuration without loading from file."""
    return Config(
        ai=AIConfig(
            default_provider="openai",
            providers={
                "openai": AIProviderConfig(
                    model="gpt-4o",
                    temperature=0.2,
                    max_tokens=2000
                )
            }
        ),
        browser=BrowserConfig(),
        testing=TestingConfig(),
        reporting=ReportingConfig()
    )
