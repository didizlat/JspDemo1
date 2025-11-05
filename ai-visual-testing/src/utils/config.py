import os
from dataclasses import dataclass
from typing import Any, Dict

import yaml


@dataclass
class Config:
    raw: Dict[str, Any]

    def get(self, path: str, default: Any = None) -> Any:
        parts = path.split(".")
        node: Any = self.raw
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node


def load_config(config_path: str) -> Config:
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Environment overrides (simple strategy):
    # - AI_* envs, BROWSER_*, TESTING_*, REPORTING_* map to sections
    _apply_env_overrides(data)
    return Config(raw=data)


def _apply_env_overrides(cfg: Dict[str, Any]) -> None:
    def set_path(path: str, value: Any) -> None:
        parts = path.split(".")
        node = cfg
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = value

    env_map = {
        "AI_DEFAULT_PROVIDER": "ai.default_provider",
        "AI_OPENAI_MODEL": "ai.providers.openai.model",
        "AI_OPENAI_TEMPERATURE": "ai.providers.openai.temperature",
        "AI_OPENAI_MAX_TOKENS": "ai.providers.openai.max_tokens",
        "BROWSER_HEADLESS": "browser.headless",
        "BROWSER_TIMEOUT": "browser.timeout",
        "BROWSER_SLOW_MO": "browser.slow_mo",
        "TESTING_BASE_URL": "testing.base_url",
        "REPORTING_OUTPUT_DIR": "reporting.output_dir",
    }

    for env_key, cfg_path in env_map.items():
        if env_key in os.environ and os.environ[env_key] != "":
            raw_val = os.environ[env_key]
            # Basic casting
            if raw_val.lower() in ("true", "false"):
                val: Any = raw_val.lower() == "true"
            elif raw_val.isdigit():
                val = int(raw_val)
            else:
                val = raw_val
            set_path(cfg_path, val)

