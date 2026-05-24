"""Projection-mode implementations for v0.3 user-scope hook handling.

Each module here implements one projection ``mode`` value from the
adapter contract: ``user_merge_json`` (Claude Code user scope —
shared-file merge into ``~/.claude/settings.json``) and
``merge_into_agent_json`` (Kiro repo + user scope — merge into the
pack-owned agent JSON). Shared id-synthesis lives in ``hook_id``.

The pipeline (T7) wires these in; the CLI install / uninstall surface
(T8b) drives them. Per RFC-0005 § Pipeline ordering invariant, the
build pipeline must project ``agent`` files before any wiring merges
run — that ordering is the pipeline's concern, not these modules'.
"""
