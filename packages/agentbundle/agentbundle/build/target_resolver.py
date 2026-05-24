"""Scope-conditional `target` resolver for v0.3 projection declarations.

The v0.3 adapter contract (RFC-0005) introduced a string-or-scope-map shape
for `target` on `[adapter.<x>.projections.<primitive>]` entries:

    # bare-string (v0.1 legacy shorthand)
    target = "tools/hooks/<name>.{sh,py}"

    # scope-map (v0.3 fork)
    target.repo = "tools/hooks/<name>.{sh,py}"
    target.user = ".claude/hooks/<name>.{sh,py}"

Some templates also carry the `<attach-to-agent>` placeholder for
`merge-into-agent-json` consumers (Kiro hook-wiring), resolved per wiring
entry from the pack-side TOML's `attach-to-agent` field.

This module is a pure-function utility — no I/O, no filesystem access.
Scope-root resolution (`.` vs `~`) and `<name>` / `<pack>` placeholder
substitution are the pipeline consumers' (T5/T6) concern; the resolver
returns a target-template string they can further process.
"""

from __future__ import annotations


_ATTACH_TO_AGENT_PLACEHOLDER = "<attach-to-agent>"


def resolve_target(
    projection: dict,
    scope: str,
    attach_to_agent: str | None = None,
) -> str:
    """Resolve a projection entry's `target` for a given scope.

    Arguments:
      projection: a single entry from `adapter.<x>.projections.<primitive>`.
        Must contain a `target` key (bare string or `{repo, user}` table).
      scope: `"repo"` or `"user"`.
      attach_to_agent: optional pack-side agent name; substituted for any
        `<attach-to-agent>` placeholder in the resolved template. If the
        template contains the placeholder but no name is given, the call
        refuses — passing an unsubstituted template downstream is a bug.

    Returns:
      The resolved target template as a string. `<name>` and `<pack>`
      placeholders survive verbatim — they're the pipeline's responsibility,
      not this resolver's.

    Raises:
      ValueError: when `target` is absent, when the requested `scope` is
        absent from a scope-map declaration, or when the resolved template
        contains the `<attach-to-agent>` placeholder but `attach_to_agent`
        is None.
    """
    if "target" not in projection:
        raise ValueError("projection missing 'target' field")

    target = projection["target"]
    if isinstance(target, str):
        resolved = target
    elif isinstance(target, dict):
        if scope not in target:
            raise ValueError(
                f"projection target has no entry for scope {scope!r}; "
                f"declared scopes: {sorted(target.keys())}"
            )
        resolved = target[scope]
        if not isinstance(resolved, str):
            raise ValueError(
                f"projection target.{scope} is not a string: {type(resolved).__name__}"
            )
    else:
        raise ValueError(
            f"projection target must be string or scope-map; got {type(target).__name__}"
        )

    if _ATTACH_TO_AGENT_PLACEHOLDER in resolved:
        if attach_to_agent is None:
            raise ValueError(
                f"target template requires attach-to-agent; got None. Template: {resolved!r}"
            )
        resolved = resolved.replace(_ATTACH_TO_AGENT_PLACEHOLDER, attach_to_agent)

    return resolved
