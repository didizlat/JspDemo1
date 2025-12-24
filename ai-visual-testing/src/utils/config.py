"""
Configuration system for AI-driven testing framework.

This module provides configuration loading, validation, and environment variable
support for the testing framework.
"""

import os
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, List
from urllib.parse import urlparse
import yaml

logger = logging.getLogger(__name__)


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
        # Validate model
        if not isinstance(self.model, str):
            raise ValueError(f"Model must be a string, got {type(self.model)}")
        if not self.model or not self.model.strip():
            raise ValueError("AI model name cannot be empty")
        self.model = self.model.strip()
        
        # Validate temperature
        if not isinstance(self.temperature, (int, float)):
            raise ValueError(f"Temperature must be a number, got {type(self.temperature)}")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"Temperature must be between 0.0 and 2.0, got {self.temperature}")
        self.temperature = float(self.temperature)
        
        # Validate max_tokens
        if self.max_tokens is not None:
            if not isinstance(self.max_tokens, int):
                raise ValueError(f"max_tokens must be an integer, got {type(self.max_tokens)}")
            if self.max_tokens < 1:
                raise ValueError(f"max_tokens must be >= 1, got {self.max_tokens}")
            if self.max_tokens > 100000:
                raise ValueError(f"max_tokens must be <= 100000, got {self.max_tokens}")
        
        # Validate api_key_env
        if self.api_key_env is not None:
            if not isinstance(self.api_key_env, str):
                raise ValueError(f"api_key_env must be a string, got {type(self.api_key_env)}")
            if not self.api_key_env.strip():
                raise ValueError("api_key_env cannot be empty if specified")
            self.api_key_env = self.api_key_env.strip()


@dataclass
class AIConfig:
    """AI configuration section."""
    default_provider: str = "openai"
    providers: Dict[str, AIProviderConfig] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate AI configuration."""
        # Validate default_provider
        if not isinstance(self.default_provider, str):
            raise ValueError(f"default_provider must be a string, got {type(self.default_provider)}")
        if not self.default_provider or not self.default_provider.strip():
            raise ValueError("default_provider cannot be empty")
        self.default_provider = self.default_provider.strip()
        
        # Validate providers
        if not isinstance(self.providers, dict):
            raise ValueError(f"providers must be a dictionary, got {type(self.providers)}")
        if not self.providers:
            raise ValueError("At least one AI provider must be configured")
        
        # Validate provider names and configs
        for provider_name, provider_config in self.providers.items():
            if not isinstance(provider_name, str) or not provider_name.strip():
                raise ValueError(f"Provider name must be a non-empty string, got {provider_name}")
            if not isinstance(provider_config, AIProviderConfig):
                raise ValueError(f"Provider config must be AIProviderConfig instance, got {type(provider_config)}")
        
        # Validate default_provider exists
        if self.default_provider not in self.providers:
            available = ", ".join(sorted(self.providers.keys()))
            raise ValueError(
                f"default_provider '{self.default_provider}' not found in providers. "
                f"Available providers: {available}"
            )
    
    def get_provider_config(self, provider: Optional[str] = None) -> AIProviderConfig:
        """
        Get configuration for a specific provider or default.
        
        Args:
            provider: Provider name. If None, uses default_provider.
            
        Returns:
            AIProviderConfig for the specified provider.
            
        Raises:
            ValueError: If provider is not configured.
        """
        provider_name = provider or self.default_provider
        
        if provider_name is not None:
            provider_name = provider_name.strip() if isinstance(provider_name, str) else str(provider_name)
        
        if provider_name not in self.providers:
            available = ", ".join(sorted(self.providers.keys()))
            raise ValueError(
                f"Provider '{provider_name}' not configured. "
                f"Available providers: {available}"
            )
        
        return self.providers[provider_name]


@dataclass
class ViewportConfig:
    """Browser viewport configuration."""
    width: int = 1920
    height: int = 1080
    
    def __post_init__(self):
        """Validate viewport configuration."""
        # Validate width
        if not isinstance(self.width, int):
            raise ValueError(f"Viewport width must be an integer, got {type(self.width)}")
        if self.width < 1:
            raise ValueError(f"Viewport width must be >= 1, got {self.width}")
        if self.width > 100000:
            raise ValueError(f"Viewport width must be <= 100000, got {self.width}")
        
        # Validate height
        if not isinstance(self.height, int):
            raise ValueError(f"Viewport height must be an integer, got {type(self.height)}")
        if self.height < 1:
            raise ValueError(f"Viewport height must be >= 1, got {self.height}")
        if self.height > 100000:
            raise ValueError(f"Viewport height must be <= 100000, got {self.height}")


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
        # Validate timeout
        if not isinstance(self.timeout, int):
            raise ValueError(f"Timeout must be an integer, got {type(self.timeout)}")
        if self.timeout < 0:
            raise ValueError(f"Timeout must be >= 0, got {self.timeout}")
        if self.timeout > 600000:  # 10 minutes max
            raise ValueError(f"Timeout must be <= 600000ms (10 minutes), got {self.timeout}")
        
        # Validate slow_mo
        if not isinstance(self.slow_mo, int):
            raise ValueError(f"Slow motion must be an integer, got {type(self.slow_mo)}")
        if self.slow_mo < 0:
            raise ValueError(f"Slow motion must be >= 0, got {self.slow_mo}")
        if self.slow_mo > 10000:  # 10 seconds max
            raise ValueError(f"Slow motion must be <= 10000ms (10 seconds), got {self.slow_mo}")
        
        # Validate browser_type
        if not isinstance(self.browser_type, str):
            raise ValueError(f"Browser type must be a string, got {type(self.browser_type)}")
        self.browser_type = self.browser_type.strip().lower()
        if self.browser_type not in ["chromium", "firefox", "webkit"]:
            raise ValueError(
                f"Browser type must be one of: chromium, firefox, webkit. "
                f"Got: {self.browser_type}"
            )
        
        # Validate viewport
        if not isinstance(self.viewport, ViewportConfig):
            raise ValueError(f"Viewport must be a ViewportConfig instance, got {type(self.viewport)}")


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
        # Validate base_url
        if not isinstance(self.base_url, str):
            raise ValueError(f"base_url must be a string, got {type(self.base_url)}")
        if not self.base_url or not self.base_url.strip():
            raise ValueError("base_url cannot be empty")
        self.base_url = self.base_url.strip()
        
        # Validate URL format
        try:
            parsed = urlparse(self.base_url)
            if not parsed.scheme:
                raise ValueError(f"base_url must include a scheme (http:// or https://), got: {self.base_url}")
            if parsed.scheme not in ["http", "https"]:
                raise ValueError(f"base_url scheme must be http or https, got: {parsed.scheme}")
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Invalid base_url format: {self.base_url}") from e
        
        # Validate console_error_threshold
        if not isinstance(self.console_error_threshold, int):
            raise ValueError(f"console_error_threshold must be an integer, got {type(self.console_error_threshold)}")
        if self.console_error_threshold < 0:
            raise ValueError(f"console_error_threshold must be >= 0, got {self.console_error_threshold}")
        
        # Validate max_retries
        if not isinstance(self.max_retries, int):
            raise ValueError(f"max_retries must be an integer, got {type(self.max_retries)}")
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {self.max_retries}")
        if self.max_retries > 100:
            raise ValueError(f"max_retries must be <= 100, got {self.max_retries}")


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
        # Validate output_dir
        if not isinstance(self.output_dir, str):
            raise ValueError(f"output_dir must be a string, got {type(self.output_dir)}")
        if not self.output_dir or not self.output_dir.strip():
            raise ValueError("output_dir cannot be empty")
        self.output_dir = self.output_dir.strip()
        
        # Validate screenshot_dir
        if not isinstance(self.screenshot_dir, str):
            raise ValueError(f"screenshot_dir must be a string, got {type(self.screenshot_dir)}")
        if not self.screenshot_dir or not self.screenshot_dir.strip():
            raise ValueError("screenshot_dir cannot be empty")
        self.screenshot_dir = self.screenshot_dir.strip()
        
        # Validate format
        if not isinstance(self.format, str):
            raise ValueError(f"Format must be a string, got {type(self.format)}")
        self.format = self.format.strip().lower()
        if self.format not in ["markdown", "json", "html"]:
            raise ValueError(
                f"Format must be one of: markdown, json, html. "
                f"Got: {self.format}"
            )
        
        # Validate template_path
        if self.template_path is not None:
            if not isinstance(self.template_path, str):
                raise ValueError(f"template_path must be a string, got {type(self.template_path)}")
            if not self.template_path.strip():
                raise ValueError("template_path cannot be empty if specified")
            self.template_path = self.template_path.strip()
    
    def get_output_path(self) -> Path:
        """
        Get output directory as Path object.
        
        Returns:
            Resolved Path object for output directory.
        """
        try:
            path = Path(self.output_dir).expanduser().resolve()
            return path
        except Exception as e:
            raise ValueError(f"Invalid output_dir path '{self.output_dir}': {e}") from e
    
    def get_screenshot_path(self) -> Path:
        """
        Get screenshot directory as Path object.
        
        Returns:
            Resolved Path object for screenshot directory.
        """
        try:
            path = Path(self.screenshot_dir).expanduser().resolve()
            return path
        except Exception as e:
            raise ValueError(f"Invalid screenshot_dir path '{self.screenshot_dir}': {e}") from e


@dataclass
class Config:
    """Main configuration class."""
    ai: AIConfig
    browser: BrowserConfig
    testing: TestingConfig
    reporting: ReportingConfig
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """
        Create Config from dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            Config instance
            
        Raises:
            ValueError: If dictionary structure is invalid
        """
        if not isinstance(data, dict):
            raise ValueError(f"Configuration data must be a dictionary, got {type(data)}")
        
        # Parse AI config
        ai_data = data.get("ai", {})
        if not isinstance(ai_data, dict):
            raise ValueError(f"AI configuration must be a dictionary, got {type(ai_data)}")
        
        providers = {}
        providers_data = ai_data.get("providers", {})
        if not isinstance(providers_data, dict):
            raise ValueError(f"AI providers must be a dictionary, got {type(providers_data)}")
        
        for name, provider_data in providers_data.items():
            if not isinstance(provider_data, dict):
                raise ValueError(
                    f"Provider '{name}' configuration must be a dictionary, "
                    f"got {type(provider_data)}"
                )
            try:
                providers[name] = AIProviderConfig(**provider_data)
            except Exception as e:
                raise ValueError(f"Invalid configuration for provider '{name}': {e}") from e
        
        try:
            ai_config = AIConfig(
                default_provider=ai_data.get("default_provider", "openai"),
                providers=providers
            )
        except Exception as e:
            raise ValueError(f"Invalid AI configuration: {e}") from e
        
        # Parse browser config
        browser_data = data.get("browser", {})
        if not isinstance(browser_data, dict):
            raise ValueError(f"Browser configuration must be a dictionary, got {type(browser_data)}")
        
        viewport_data = browser_data.get("viewport", {})
        if not isinstance(viewport_data, dict):
            raise ValueError(f"Viewport configuration must be a dictionary, got {type(viewport_data)}")
        
        try:
            browser_config = BrowserConfig(
                headless=browser_data.get("headless", False),
                viewport=ViewportConfig(**viewport_data),
                timeout=browser_data.get("timeout", 30000),
                slow_mo=browser_data.get("slow_mo", 500),
                browser_type=browser_data.get("browser_type", "chromium")
            )
        except Exception as e:
            raise ValueError(f"Invalid browser configuration: {e}") from e
        
        # Parse testing config
        testing_data = data.get("testing", {})
        if not isinstance(testing_data, dict):
            raise ValueError(f"Testing configuration must be a dictionary, got {type(testing_data)}")
        
        try:
            testing_config = TestingConfig(**testing_data)
        except Exception as e:
            raise ValueError(f"Invalid testing configuration: {e}") from e
        
        # Parse reporting config
        reporting_data = data.get("reporting", {})
        if not isinstance(reporting_data, dict):
            raise ValueError(f"Reporting configuration must be a dictionary, got {type(reporting_data)}")
        
        try:
            reporting_config = ReportingConfig(**reporting_data)
        except Exception as e:
            raise ValueError(f"Invalid reporting configuration: {e}") from e
        
        return cls(
            ai=ai_config,
            browser=browser_config,
            testing=testing_config,
            reporting=reporting_config
        )
    
    def validate(self) -> List[str]:
        """
        Validate configuration and return list of errors.
        
        Returns:
            List of validation error messages. Empty list if validation passes.
        """
        errors = []
        
        # Validate AI API keys (only if api_key_env is specified)
        for provider_name, provider_config in self.ai.providers.items():
            if provider_config.api_key_env:
                env_var = provider_config.api_key_env
                if env_var not in os.environ:
                    errors.append(
                        f"AI provider '{provider_name}' requires environment variable "
                        f"'{env_var}' but it is not set"
                    )
                elif not os.environ[env_var] or not os.environ[env_var].strip():
                    errors.append(
                        f"AI provider '{provider_name}' requires environment variable "
                        f"'{env_var}' but it is empty"
                    )
        
        # Validate directories (try to create if they don't exist)
        try:
            output_path = self.reporting.get_output_path()
            output_path.mkdir(parents=True, exist_ok=True)
            # Check write permissions
            test_file = output_path / ".test_write"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                errors.append(f"Cannot write to output directory '{output_path}': {e}")
        except Exception as e:
            errors.append(f"Cannot create output directory '{self.reporting.output_dir}': {e}")
        
        try:
            screenshot_path = self.reporting.get_screenshot_path()
            screenshot_path.mkdir(parents=True, exist_ok=True)
            # Check write permissions
            test_file = screenshot_path / ".test_write"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                errors.append(f"Cannot write to screenshot directory '{screenshot_path}': {e}")
        except Exception as e:
            errors.append(f"Cannot create screenshot directory '{self.reporting.screenshot_dir}': {e}")
        
        # Validate template_path if specified
        if self.reporting.template_path:
            template_path = Path(self.reporting.template_path).expanduser().resolve()
            if not template_path.exists():
                errors.append(f"Template file not found: {self.reporting.template_path}")
            elif not template_path.is_file():
                errors.append(f"Template path is not a file: {self.reporting.template_path}")
        
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
        yaml.YAMLError: If YAML parsing fails
    """
    if config_path is None:
        # Default to config/default.yaml relative to this file
        config_dir = Path(__file__).parent.parent.parent / "config"
        config_path = config_dir / "default.yaml"
    
    config_path = Path(config_path)
    
    # Validate file exists
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}. "
            f"Please ensure the file exists and the path is correct."
        )
    
    # Validate it's a file
    if not config_path.is_file():
        raise ValueError(f"Configuration path is not a file: {config_path}")
    
    # Load YAML with multiple encoding fallbacks
    data = {}
    encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
    
    for encoding in encodings:
        try:
            with open(config_path, "r", encoding=encoding) as f:
                data = yaml.safe_load(f) or {}
                logger.debug(f"Successfully loaded config from {config_path} with encoding {encoding}")
                break
        except UnicodeDecodeError:
            continue
        except yaml.YAMLError as e:
            raise ValueError(
                f"Failed to parse YAML file '{config_path}': {e}. "
                f"Please check the YAML syntax."
            ) from e
        except Exception as e:
            raise ValueError(
                f"Failed to read configuration file '{config_path}': {e}"
            ) from e
    else:
        # If all encodings failed, try with error replacement
        try:
            with open(config_path, "r", encoding="utf-8", errors="replace") as f:
                data = yaml.safe_load(f) or {}
                logger.warning(f"Loaded config with encoding errors replaced: {config_path}")
        except Exception as e:
            raise ValueError(
                f"Failed to read configuration file '{config_path}' with any encoding: {e}"
            ) from e
    
    if not isinstance(data, dict):
        raise ValueError(
            f"Configuration file must contain a YAML dictionary, got {type(data)}"
        )
    
    # Apply environment variable overrides
    try:
        _apply_env_overrides(data)
    except Exception as e:
        raise ValueError(f"Failed to apply environment variable overrides: {e}") from e
    
    # Create config object
    try:
        config = Config.from_dict(data)
    except ValueError as e:
        raise ValueError(f"Invalid configuration: {e}") from e
    except Exception as e:
        raise ValueError(
            f"Unexpected error creating configuration object: {e}"
        ) from e
    
    # Validate configuration
    errors = config.validate()
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)
    
    logger.info(f"Successfully loaded configuration from {config_path}")
    return config


def _apply_env_overrides(data: Dict[str, Any]) -> None:
    """
    Apply environment variable overrides to configuration.
    
    Args:
        data: Configuration dictionary to modify in-place.
    """
    def set_nested_path(path: str, value: Any) -> None:
        """
        Set a nested path in the dictionary.
        
        Args:
            path: Dot-separated path (e.g., "ai.providers.openai.model")
            value: Value to set
        """
        if not path or not isinstance(path, str):
            raise ValueError(f"Path must be a non-empty string, got {path}")
        
        parts = path.split(".")
        if not parts:
            raise ValueError(f"Invalid path format: {path}")
        
        node = data
        for part in parts[:-1]:
            if not isinstance(node, dict):
                raise ValueError(
                    f"Cannot set nested path '{path}': "
                    f"'{'.'.join(parts[:parts.index(part)])}' is not a dictionary"
                )
            node = node.setdefault(part, {})
        
        node[parts[-1]] = value
        logger.debug(f"Set config path '{path}' = {value}")
    
    def parse_value(value: str, env_key: str) -> Any:
        """
        Parse environment variable value to appropriate type.
        
        Args:
            value: Environment variable value string
            env_key: Environment variable name (for error messages)
            
        Returns:
            Parsed value (bool, int, float, or str)
        """
        if not isinstance(value, str):
            raise ValueError(f"Environment variable value must be a string, got {type(value)}")
        
        value_stripped = value.strip()
        value_lower = value_stripped.lower()
        
        # Boolean
        if value_lower in ("true", "false", "yes", "no", "1", "0", "on", "off"):
            result = value_lower in ("true", "yes", "1", "on")
            logger.debug(f"Parsed {env_key} as boolean: {result}")
            return result
        
        # Integer
        try:
            result = int(value_stripped)
            logger.debug(f"Parsed {env_key} as integer: {result}")
            return result
        except ValueError:
            pass
        
        # Float
        try:
            result = float(value_stripped)
            logger.debug(f"Parsed {env_key} as float: {result}")
            return result
        except ValueError:
            pass
        
        # String (default)
        logger.debug(f"Parsed {env_key} as string: {value_stripped}")
        return value_stripped
    
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
                try:
                    parsed_value = parse_value(value, env_key)
                    set_nested_path(config_path, parsed_value)
                except Exception as e:
                    logger.warning(
                        f"Failed to apply environment variable override '{env_key}': {e}. "
                        f"Skipping this override."
                    )
                    # Continue with other overrides instead of failing completely


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
