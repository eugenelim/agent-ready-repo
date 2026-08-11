"""Compile validated pack hook wiring into Claude plugin-manifest hooks."""

from __future__ import annotations

from pathlib import Path

from agentbundle.build.hook_wiring_rules import collect_validated_claude_hooks


def compile_plugin_hooks(
    pack_path: Path,
    *,
    repo_hook_prefix: str,
    plugin_hook_prefix: str,
    hook_source_path: str,
    wiring_source_path: str,
    pack_name: str,
) -> dict[str, list[dict]]:
    """Return a deterministic inline hooks block for one pack.

    All paths are contract inputs. The only transformation is replacing the
    validated direct-route body prefix with the plugin-root body prefix.
    """
    validated = collect_validated_claude_hooks(
        pack_path,
        repo_hook_prefix=repo_hook_prefix,
        hook_source_path=hook_source_path,
        wiring_source_path=wiring_source_path,
        pack_name=pack_name,
    )
    plugin_prefix = plugin_hook_prefix.rstrip("/") + "/"
    compiled: dict[str, list[dict]] = {}
    for item in validated:
        outer: dict = {
            "hooks": [
                {
                    "type": "command",
                    "command": (
                        f'{item.interpreter} "${{CLAUDE_PLUGIN_ROOT}}/'
                        f'{plugin_prefix}{item.body_name}"'
                    ),
                    "timeout": item.timeout,
                }
            ]
        }
        if item.matcher is not None:
            outer["matcher"] = item.matcher
        compiled.setdefault(item.event, []).append(outer)
    return compiled
