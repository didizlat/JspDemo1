# Configuration System Documentation

**Phase:** 1.3 - Configuration System  
**Status:** ✅ Complete

---

## Overview

The configuration system provides a flexible way to configure the AI-driven testing framework using YAML files with environment variable overrides.

## Configuration File Structure

The configuration is organized into four main sections:

### 1. AI Configuration (`ai`)

Controls AI provider settings and model selection.

```yaml
ai:
  default_provider: openai  # Default AI provider to use
  providers:
    openai:
      model: gpt-4o                    # Model name
      temperature: 0.2                 # 0.0 to 2.0
      max_tokens: 2000                 # Optional: max response tokens
      api_key_env: OPENAI_API_KEY      # Environment variable for API key
    claude:
      model: claude-3-opus-20240229
      temperature: 0.2
      api_key_env: ANTHROPIC_API_KEY
    gemini:
      model: gemini-pro-vision
      temperature: 0.2
      api_key_env: GOOGLE_API_KEY
```

**Fields:**
- `default_provider` (required): Name of the default AI provider
- `providers` (required): Dictionary of provider configurations
  - `model` (required): Model identifier
  - `temperature` (optional, default: 0.2): Sampling temperature (0.0-2.0)
  - `max_tokens` (optional): Maximum tokens in response
  - `api_key_env` (optional): Environment variable name for API key

### 2. Browser Configuration (`browser`)

Controls browser automation settings.

```yaml
browser:
  headless: false              # Run browser in headless mode
  browser_type: chromium       # chromium, firefox, or webkit
  viewport:
    width: 1920                 # Viewport width in pixels
    height: 1080                 # Viewport height in pixels
  timeout: 30000                # Default timeout in milliseconds
  slow_mo: 500                   # Delay between actions in milliseconds
```

**Fields:**
- `headless` (optional, default: false): Run browser without GUI
- `browser_type` (optional, default: chromium): Browser engine to use
- `viewport` (optional): Viewport dimensions
  - `width` (required): Width in pixels (>= 1)
  - `height` (required): Height in pixels (>= 1)
- `timeout` (optional, default: 30000): Default timeout in milliseconds (>= 0)
- `slow_mo` (optional, default: 500): Delay between actions in milliseconds (>= 0)

### 3. Testing Configuration (`testing`)

Controls test execution behavior.

```yaml
testing:
  base_url: http://localhost:8080      # Base URL for tests
  screenshot_on_failure: true           # Capture screenshots on failure
  save_html_on_failure: true            # Save HTML snapshots on failure
  console_error_threshold: 0            # Max console errors allowed
  stop_on_failure: false                # Stop test suite on first failure
  max_retries: 0                       # Maximum retry attempts per step
```

**Fields:**
- `base_url` (required): Base URL for the application under test
- `screenshot_on_failure` (optional, default: true): Capture screenshots when tests fail
- `save_html_on_failure` (optional, default: true): Save HTML when tests fail
- `console_error_threshold` (optional, default: 0): Maximum console errors allowed (>= 0)
- `stop_on_failure` (optional, default: false): Stop test execution on first failure
- `max_retries` (optional, default: 0): Maximum retry attempts per step (>= 0)

### 4. Reporting Configuration (`reporting`)

Controls test report generation.

```yaml
reporting:
  output_dir: ./test-reports           # Output directory for reports
  screenshot_dir: ./screenshots        # Directory for screenshots
  format: markdown                      # Report format: markdown, json, html
  include_screenshots: true             # Include screenshots in reports
  include_html_snapshots: false        # Include HTML snapshots in reports
  template_path: null                   # Optional custom template path
```

**Fields:**
- `output_dir` (required): Directory for test reports
- `screenshot_dir` (required): Directory for screenshots
- `format` (optional, default: markdown): Report format (markdown, json, html)
- `include_screenshots` (optional, default: true): Include screenshots in reports
- `include_html_snapshots` (optional, default: false): Include HTML snapshots
- `template_path` (optional): Path to custom report template

---

## Environment Variable Overrides

All configuration values can be overridden using environment variables. The system uses a dot-notation mapping:

### AI Configuration
- `AI_DEFAULT_PROVIDER` → `ai.default_provider`
- `AI_OPENAI_MODEL` → `ai.providers.openai.model`
- `AI_OPENAI_TEMPERATURE` → `ai.providers.openai.temperature`
- `AI_OPENAI_MAX_TOKENS` → `ai.providers.openai.max_tokens`
- `AI_CLAUDE_MODEL` → `ai.providers.claude.model`
- `AI_CLAUDE_TEMPERATURE` → `ai.providers.claude.temperature`
- `AI_GEMINI_MODEL` → `ai.providers.gemini.model`
- `AI_GEMINI_TEMPERATURE` → `ai.providers.gemini.temperature`

### Browser Configuration
- `BROWSER_HEADLESS` → `browser.headless` (true/false)
- `BROWSER_TIMEOUT` → `browser.timeout` (integer)
- `BROWSER_SLOW_MO` → `browser.slow_mo` (integer)
- `BROWSER_TYPE` → `browser.browser_type` (chromium/firefox/webkit)
- `BROWSER_VIEWPORT_WIDTH` → `browser.viewport.width` (integer)
- `BROWSER_VIEWPORT_HEIGHT` → `browser.viewport.height` (integer)

### Testing Configuration
- `TESTING_BASE_URL` → `testing.base_url`
- `TESTING_SCREENSHOT_ON_FAILURE` → `testing.screenshot_on_failure` (true/false)
- `TESTING_SAVE_HTML_ON_FAILURE` → `testing.save_html_on_failure` (true/false)
- `TESTING_CONSOLE_ERROR_THRESHOLD` → `testing.console_error_threshold` (integer)
- `TESTING_STOP_ON_FAILURE` → `testing.stop_on_failure` (true/false)
- `TESTING_MAX_RETRIES` → `testing.max_retries` (integer)

### Reporting Configuration
- `REPORTING_OUTPUT_DIR` → `reporting.output_dir`
- `REPORTING_SCREENSHOT_DIR` → `reporting.screenshot_dir`
- `REPORTING_FORMAT` → `reporting.format` (markdown/json/html)
- `REPORTING_INCLUDE_SCREENSHOTS` → `reporting.include_screenshots` (true/false)
- `REPORTING_INCLUDE_HTML_SNAPSHOTS` → `reporting.include_html_snapshots` (true/false)

### Type Conversion

Environment variables are automatically converted to appropriate types:
- **Boolean**: `true`, `false`, `yes`, `no`, `1`, `0`
- **Integer**: Numeric strings (e.g., `"30000"` → `30000`)
- **Float**: Decimal strings (e.g., `"0.2"` → `0.2`)
- **String**: Everything else

---

## Usage Examples

### Basic Usage

```python
from src.utils.config import load_config

# Load default configuration (config/default.yaml)
config = load_config()

# Access configuration values
print(config.ai.default_provider)
print(config.browser.headless)
print(config.testing.base_url)
```

### Custom Configuration File

```python
from src.utils.config import load_config

# Load custom configuration file
config = load_config("path/to/custom-config.yaml")
```

### Environment Variable Overrides

```bash
# Set environment variables
export AI_DEFAULT_PROVIDER=claude
export BROWSER_HEADLESS=true
export TESTING_BASE_URL=http://staging.example.com

# Run tests (will use environment overrides)
python run_ai_test.py
```

### Programmatic Configuration

```python
from src.utils.config import get_default_config, Config, AIConfig, BrowserConfig

# Get default configuration
config = get_default_config()

# Or create custom configuration programmatically
config = Config(
    ai=AIConfig(
        default_provider="openai",
        providers={
            "openai": AIProviderConfig(
                model="gpt-4o",
                temperature=0.2
            )
        }
    ),
    browser=BrowserConfig(headless=True),
    testing=TestingConfig(base_url="http://localhost:8080"),
    reporting=ReportingConfig()
)
```

---

## Validation

The configuration system validates:

1. **Required Fields**: All required fields must be present
2. **Type Validation**: Values must be of correct type
3. **Range Validation**: Numeric values must be within valid ranges
4. **Enum Validation**: String values must match allowed options
5. **API Keys**: If `api_key_env` is specified, the environment variable must exist
6. **Directory Creation**: Output directories are created if they don't exist

### Validation Errors

If validation fails, a `ValueError` is raised with detailed error messages:

```python
try:
    config = load_config("invalid-config.yaml")
except ValueError as e:
    print(f"Configuration error: {e}")
```

---

## Configuration File Location

By default, the system looks for `config/default.yaml` relative to the project root. You can specify a custom path:

```python
config = load_config("/path/to/config.yaml")
```

---

## Best Practices

1. **Use Environment Variables for Secrets**: Never commit API keys to configuration files. Use `api_key_env` to reference environment variables.

2. **Version Control**: Commit `config/default.yaml` but use environment variables for environment-specific settings.

3. **Validation**: Always validate configuration before use. The `load_config()` function validates automatically.

4. **Default Values**: Use sensible defaults in `default.yaml` that work for local development.

5. **Documentation**: Document any custom configuration options in your project's README.

---

## Troubleshooting

### Configuration File Not Found

```
FileNotFoundError: Configuration file not found: config/default.yaml
```

**Solution**: Ensure the configuration file exists or provide a custom path.

### Invalid Configuration

```
ValueError: Invalid configuration: ...
```

**Solution**: Check the error message for specific validation failures and fix the configuration file.

### Missing API Key

```
ValueError: Configuration validation failed:
  - AI provider 'openai' requires environment variable 'OPENAI_API_KEY' but it is not set
```

**Solution**: Set the required environment variable:
```bash
export OPENAI_API_KEY=your-api-key-here
```

---

*Configuration system documentation - Phase 1.3*

