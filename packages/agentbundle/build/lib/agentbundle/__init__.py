"""agentbundle — distribution machinery for the agent-ready-repo catalogue.

The `build` submodule ships the adapter contract, the four reference
adapters, the recipe-driven build pipeline, and the self-host gate.

The CLI surface (RFC-0003 F-cli) lives in this package's top-level modules
and imports `agentbundle.build` as a library — no `sys.path` tricks, no
`subprocess` to `tools/build/build.py`.
"""

from agentbundle.version import CLI_VERSION as __version__
from agentbundle.version import SPEC_VERSION

__all__ = ["__version__", "SPEC_VERSION"]
