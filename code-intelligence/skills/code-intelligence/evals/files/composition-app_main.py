"""Application entry point."""
from __future__ import annotations

from composition_config_loader import parse_config


def bootstrap(config_path: str) -> None:
    """Start the application with settings loaded from config_path."""
    config = parse_config(config_path)
    print(f"Started with config: {config}")
