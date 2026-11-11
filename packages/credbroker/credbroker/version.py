"""Single source of truth for the credbroker package version.

Import ``__version__`` from here rather than writing a literal anywhere else:
``credbroker/__init__.py`` re-exports it, and tests that prove pyproject,
version.py, and the public attribute agree import it from here.
"""

__version__: str = "0.7.0"
