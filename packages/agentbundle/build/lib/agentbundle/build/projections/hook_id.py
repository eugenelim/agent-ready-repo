"""Hook-entry id synthesis — shared between ``user_merge_json`` (Claude
Code user scope) and ``merge_into_agent_json`` (Kiro at both scopes).

Per RFC-0005 § Merge semantics step 2, every hook entry the CLI writes
carries an ``id`` field of the form ``<pack-name>:<hook-source-basename>``.
The id is the ownership tag the merger uses to detect "this is mine"
on reinstall / replace / uninstall. Claude Code today treats unknown
keys on hook entries as opaque (the synthetic ``id`` survives without
runtime effect); Kiro's hook-entry schema is observed-but-not-publicly-
documented and treats it the same. RFC-0005 Unresolved Q1 holds the
``id`` → ``agent-ready-id`` rename open; this module is the single
chokepoint to flip if that resolves.
"""

from __future__ import annotations


def synthesize_id(pack_name: str, hook_source_basename: str) -> str:
    """Return the ownership-tag id for a single (pack, wiring-toml) pair.

    The basename is the wiring TOML filename without ``.toml`` — e.g.
    ``on-prompt`` for ``.apm/hook-wiring/on-prompt.toml``. Both adapters
    share this synthesis: id collision across packs means the same pack
    name + same wiring basename, which is the genuine conflict
    RFC-0005 § Conflict refuses install on.
    """
    return f"{pack_name}:{hook_source_basename}"
