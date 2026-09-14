"""Send JSONL records to an OpenTelemetry Collector as OTLP logs.

The public surface is the `jsonl-otlp-export` console script. Nothing is sent
until an endpoint is configured, and what may be sent is decided by a profile
the caller supplies as data.
"""

from __future__ import annotations

__all__ = ["__version__"]


def _installed_version() -> str:
    """The version of the *installed distribution*, not a second literal here.

    A module-level version string is a second place for the number to live, and
    the two drift the first time one is bumped alone. Reading the metadata means
    `--version` can only ever report what was actually installed.
    """
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("jsonl-otlp-exporter")
    except PackageNotFoundError:  # running from a source tree, not installed
        return "0+unknown"


__version__ = _installed_version()
