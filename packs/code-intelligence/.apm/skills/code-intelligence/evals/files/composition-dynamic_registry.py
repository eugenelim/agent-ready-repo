"""Loader registry: maps a loader name to a function in the config loader."""
from __future__ import annotations

_LOADERS: dict[str, str] = {
    "config": "parse_config",
}


def load_via_registry(name: str, path: str) -> dict:
    """Look up a loader function by name and invoke it."""
    func_name = _LOADERS.get(name)
    if func_name is not None:
        import composition_config_loader
        return getattr(composition_config_loader, func_name)(path)
    return {}
