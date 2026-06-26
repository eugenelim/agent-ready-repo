"""``agentbundle reconcile`` — read-only orphan reporter.

Per RFC-0005 § Follow-on artifacts and AC26: walks the Claude Code
settings file (``~/.claude/settings.json``) and every Kiro agent JSON
named in user-scope state, comparing the on-disk ``hooks.<event>``
arrays against the state file's ``hook-wiring-owned`` rows to surface
two classes of orphan:

  - **orphan-in-file** — the target file claims an id-tagged entry the
    state file doesn't know about. Surfaces when a hand-edit on the
    settings file (or on a Kiro agent JSON) adds an entry with an id
    that no installed pack owns.
  - **orphan-in-state** — the state file claims ownership of an entry
    the target file doesn't have. Surfaces when the adopter
    hand-deletes an entry without uninstalling the pack, or when
    multi-machine sync moves a state row without its corresponding
    target-file content.

Output is grouped by adapter (one heading per adapter that has any
orphans, plus an "all clean" line when there are none). The
subcommand is **read-only**: it does not register an ``--apply`` flag.
A write-mode reconciler would re-create the merge-discipline problems
RFC-0005 is designed to avoid; the adopter takes manual action from
this report.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def run(args: "argparse.Namespace") -> int:  # noqa: ARG001
    """Entry point for ``agentbundle reconcile``.

    The report surface is user-scope only (RFC-0005). The old ``--scope``
    flag had a single legal value (``user``) that equalled its default, so
    it could never select anything — it was dropped (CLI-hygiene sweep). A
    future RFC that adds a second scope can reintroduce the flag then.
    """
    from agentbundle import scope as scope_mod
    from agentbundle.config import ConfigError, load_state

    try:
        user_root = scope_mod.resolve_user_root()
    except scope_mod.UserScopeUnresolvable:
        print(
            "reconcile: cannot resolve user scope: $HOME unset or invalid",
            file=sys.stderr,
        )
        return 1

    state_path = user_root / ".agentbundle" / "state.toml"
    if not state_path.exists():
        # An absent state file means no installs at user scope; no
        # orphans to report against. Cleanly exit 0 with the all-clean
        # line so wrapper scripts can short-circuit.
        print("reconcile: all clean (no user-scope state)")
        return 0

    try:
        state = load_state(state_path)
    except ConfigError as exc:
        print(f"reconcile: {exc}", file=sys.stderr)
        return 1

    orphans_by_adapter = _collect_orphans(state, user_root)
    return _print_report(orphans_by_adapter)


def _collect_orphans(state, user_root: Path) -> dict[str, list[str]]:
    """Walk the target files referenced by state and compute orphans.

    Returns a dict of adapter name → list of orphan lines (each line
    a human-readable description suitable for direct print).
    """
    # Group state's hook-wiring-owned rows by (adapter, target-file)
    # so we read each target file exactly once. The default target for
    # claude-code rows is ``~/.claude/settings.json``; kiro rows always
    # carry an explicit ``target-file``.
    grouped: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for pack_state in state.packs.values():
        if pack_state.scope != "user":
            continue
        adapter = pack_state.adapter or "claude-code"
        for row in pack_state.hook_wiring_owned:
            event = row.get("event")
            entry_id = row.get("id")
            if not (isinstance(event, str) and isinstance(entry_id, str)):
                continue
            target_rel = row.get("target-file")
            if not target_rel:
                target_rel = (
                    ".claude/settings.json" if adapter == "claude-code" else ""
                )
            if not target_rel:
                continue
            grouped.setdefault((adapter, target_rel), set()).add((event, entry_id))

    orphans_by_adapter: dict[str, list[str]] = {}
    for (adapter, target_rel), owned_pairs in grouped.items():
        target_path = user_root / target_rel.lstrip("/")
        file_pairs: set[tuple[str, str]] = set()
        if target_path.exists():
            try:
                data = json.loads(target_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                orphans_by_adapter.setdefault(adapter, []).append(
                    f"  unparseable target {target_rel}: {exc}"
                )
                continue
            if isinstance(data, dict):
                hooks = data.get("hooks", {})
                if isinstance(hooks, dict):
                    for event, entries in hooks.items():
                        if not isinstance(entries, list):
                            continue
                        for entry in entries:
                            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                                file_pairs.add((event, entry["id"]))

        # orphan-in-file: present in file, absent from state.
        for event, entry_id in sorted(file_pairs - owned_pairs):
            orphans_by_adapter.setdefault(adapter, []).append(
                f"  orphan-in-file: {target_rel} carries (event={event}, id={entry_id}) "
                f"but no installed pack owns it"
            )
        # orphan-in-state: present in state, absent from file.
        for event, entry_id in sorted(owned_pairs - file_pairs):
            orphans_by_adapter.setdefault(adapter, []).append(
                f"  orphan-in-state: state records ownership of (event={event}, "
                f"id={entry_id}) in {target_rel} but the entry is missing on disk"
            )

    return orphans_by_adapter


def _print_report(orphans_by_adapter: dict[str, list[str]]) -> int:
    if not orphans_by_adapter:
        print("reconcile: all clean")
        return 0
    for adapter in sorted(orphans_by_adapter.keys()):
        lines = orphans_by_adapter[adapter]
        if not lines:
            continue
        print(f"reconcile: {adapter}")
        for line in lines:
            print(line)
    return 0
