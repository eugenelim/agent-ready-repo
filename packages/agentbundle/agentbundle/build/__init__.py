"""Build pipeline: adapter contract, reference adapters, recipes, self-host gate.

`main` is the CLI entrypoint — `python -m agentbundle.build` and the
`tools/build/build.py` shim both call it. Sibling specs (self-hosting,
RFC-0003's CLI) import `agentbundle.build` as a library; the public
surface is `main`, `validate.validate`, and the adapter `project`
functions exposed through `adapters`.
"""

from agentbundle.build.__main__ import main

__all__ = ["main"]
