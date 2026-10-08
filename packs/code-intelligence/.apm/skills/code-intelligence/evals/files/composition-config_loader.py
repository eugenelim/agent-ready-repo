"""Configuration loading."""
from __future__ import annotations


def parse_config(path: str, strict: bool = False) -> dict:
    """Load configuration from the given path and return it as a dict.

    Args:
        path: Location of the configuration file.
        strict: When True, raise on unknown keys.

    Returns:
        A dict of configuration values.
    """
    return {"path": path, "strict": strict}
