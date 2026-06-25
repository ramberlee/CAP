"""Configuration loader.

Returns a typed AppConfig model with validation at parse time.
The model supports dict-style .get() for backward compatibility
during migration — consumers can transition to typed attribute
access (config.generation.max_tokens) incrementally.
"""

from pathlib import Path

import yaml

from modules.config_model import AppConfig


def load_config(config_path: str = "config.yaml") -> AppConfig:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return AppConfig(**raw)
