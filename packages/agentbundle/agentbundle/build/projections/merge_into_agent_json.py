"""``merge-into-agent-json`` projection mode — Kiro at both scopes.

Merges a pack's ``.apm/hook-wiring/*.toml`` content into a **pack-owned**
agent JSON at ``<scope-root>/.kiro/agents/<attach-to-agent>.json`` under
the ``hooks`` key. The mode reuses ``user-merge-json``'s
array-append-with-id discipline, with structural differences from the
Claude-Code-user-scope shape:

1. **Target is pack-owned, not adopter-shared.** Adopter hand-edits to
   the agent JSON are squatting on a managed surface — the next upgrade
   replaces the file via the agent primitive's ``direct-file``
   projection. No collision detection, no ``--force-merge`` flag.
2. **Agent file must exist before merge runs.** RFC-0005 establishes
   the build-pipeline ordering invariant — agents project before any
   wiring merges run. The absent-file case is a refuse-with-internal-
   error path, exercised only via test instrumentation.
3. **Per-agent target, scope-conditional.** Each wiring TOML targets
   a single agent named by its ``attach-to-agent`` field. The caller
   (T8b) is responsible for resolving the target file path; this
   module operates on the resolved path.

This module is stdlib-only — ``json`` + ``pathlib`` + ``tempfile``.

T8b will own the install/uninstall CLI threading; T7 enforces the
pipeline ordering in the iterator. T6 (this module) ships the merge
engine plus the per-adapter event-vocabulary rail used by
``commands/validate.py``.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from agentbundle.build.projections.hook_id import synthesize_id


class AgentJsonRefusal(Exception):
    """Raised when ``project`` / ``unproject`` refuses to write.

    The exception's string is the refuse-and-explain text RFC-0005
    specifies. CLI callers (T8b) catch and print to stderr without
    paraphrasing.
    """


def project(
    target_path: Path,
    pack_name: str,
    wiring_tomls: dict[str, dict],
) -> list[tuple[str, str]]:
    """Merge *wiring_tomls* into the agent JSON at *target_path*.

    Arguments:
      target_path: resolved path to the agent JSON. **Must exist** —
        the build pipeline (T7) projects agents before wiring runs.
        Absent → refuse with the ``internal:`` text.
      pack_name: the pack's ``[pack].name``. Substituted into id tags.
      wiring_tomls: map of wiring TOML basename (no ``.toml``) → parsed
        TOML body (typically ``{"attach-to-agent": "<name>", "hooks":
        {"<Event>": [entries]}}``). The ``attach-to-agent`` field is
        not consumed here — the caller has already resolved
        *target_path* using it.

    Returns:
      List of ``(event, id)`` tuples reflecting every owned entry
      written. T8b records these in the state file's
      ``hook-wiring-owned`` table so ``unproject`` can be precise.

    Raises:
      AgentJsonRefusal: missing agent file (pipeline-ordering
        violation), unparseable JSON, wrong-shape ``hooks`` or
        ``hooks.<event>``.
    """
    if not target_path.exists():
        # The text below extends RFC-0005's bare `internal: <agent-file>
        # missing` shape with diagnostic context. This is intentional —
        # the message is a CLI-internal-error string, not an
        # adopter-facing contract, so we trade brevity for the breadcrumb
        # "agent must project before wiring" that points at the
        # pipeline-ordering invariant. Tests assert the substrings
        # `internal:` / `missing` / `agent must project before wiring`
        # to keep T8b's CLI handler portable across text refinements.
        raise AgentJsonRefusal(
            f"internal: {target_path} missing at hook-wiring merge time; "
            f"agent must project before wiring"
        )

    data = _load_agent_json(target_path)
    _shape_check_hooks(target_path, data)

    owned: list[tuple[str, str]] = []
    for basename, body in wiring_tomls.items():
        entry_id = synthesize_id(pack_name, basename)
        hooks_in_wiring = body.get("hooks", {}) if isinstance(body, dict) else {}
        if not isinstance(hooks_in_wiring, dict):
            continue
        for event, incoming_entries in hooks_in_wiring.items():
            if not isinstance(incoming_entries, list):
                continue
            data.setdefault("hooks", {})
            data["hooks"].setdefault(event, [])
            event_array = data["hooks"][event]
            _shape_check_event_array(target_path, event, event_array)
            for incoming in incoming_entries:
                if not isinstance(incoming, dict):
                    continue
                tagged = dict(incoming)
                tagged["id"] = entry_id
                _merge_one_entry(event_array, tagged)
                owned.append((event, entry_id))

    _atomic_write(target_path, data)
    # Deduplicate (event, id) tuples — see T5's note in user_merge_json.
    seen: set[tuple[str, str]] = set()
    result: list[tuple[str, str]] = []
    for item in owned:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def unproject(target_path: Path, owned: list[tuple[str, str]]) -> None:
    """Remove every ``(event, id)`` pair in *owned* from *target_path*.

    Empty ``hooks.<event>`` arrays are removed. The agent file itself
    is **never** removed by this function — that's the agent
    primitive's ``direct-file`` uninstall's responsibility (RFC-0005
    § Conflict, idempotency, uninstall).

    If the target file is absent, ``unproject`` is a no-op — same
    rationale as T5's ``user_merge_json.unproject``: a state row
    pointing at a now-absent file is an orphan-in-state condition that
    T9's reconcile surfaces. Refusing here would block uninstall of
    unrelated packs whose own target files happen to be absent.
    """
    if not target_path.exists():
        return

    data = _load_agent_json(target_path)
    _shape_check_hooks(target_path, data)

    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return

    owned_by_event: dict[str, set[str]] = {}
    for event, entry_id in owned:
        owned_by_event.setdefault(event, set()).add(entry_id)

    for event, ids_to_remove in owned_by_event.items():
        if event not in hooks:
            continue
        event_array = hooks[event]
        if not isinstance(event_array, list):
            continue
        hooks[event] = [
            e for e in event_array
            if not (isinstance(e, dict) and e.get("id") in ids_to_remove)
        ]
        if not hooks[event]:
            del hooks[event]

    _atomic_write(target_path, data)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _load_agent_json(target_path: Path) -> dict:
    """Read the agent JSON. Raises ``AgentJsonRefusal`` on
    unparseable content (matches T5's `user_merge_json` shape)."""
    try:
        text = target_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AgentJsonRefusal(
            f"cannot parse {target_path}: {exc}; fix or back up the file and retry"
        ) from exc
    if not text.strip():
        # An empty agent JSON file is a Kiro-side artifact (an agent
        # body with no fields yet) — treat as `{}` for merge.
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AgentJsonRefusal(
            f"cannot parse {target_path}: {exc}; fix or back up the file and retry"
        ) from exc
    if not isinstance(data, dict):
        raise AgentJsonRefusal(
            f"cannot parse {target_path}: top-level value is "
            f"{type(data).__name__}, expected object; fix or back up "
            f"the file and retry"
        )
    return data


def _shape_check_hooks(target_path: Path, data: dict) -> None:
    if "hooks" in data and not isinstance(data["hooks"], dict):
        raise AgentJsonRefusal(
            f"{target_path}: hooks has unexpected shape {type(data['hooks']).__name__}; "
            f"expected object"
        )


def _shape_check_event_array(target_path: Path, event: str, value: object) -> None:
    if not isinstance(value, list):
        raise AgentJsonRefusal(
            f"{target_path}: hooks.{event} has unexpected shape {type(value).__name__}; "
            f"expected array"
        )


def _merge_one_entry(event_array: list, tagged_entry: dict) -> None:
    """Append or replace-in-place by id.

    No adopter-collision branch: the agent JSON is pack-owned (RFC-0005
    § What this section does NOT add — no ``--force-merge`` for Kiro).
    Adopter hand-edits to the agent file are squatting on a managed
    surface; the next upgrade replaces the file via the agent
    primitive's ``direct-file`` projection.
    """
    incoming_id = tagged_entry["id"]
    for index, existing in enumerate(event_array):
        if isinstance(existing, dict) and existing.get("id") == incoming_id:
            event_array[index] = tagged_entry
            return
    event_array.append(tagged_entry)


def _atomic_write(target_path: Path, data: dict) -> None:
    """Write *data* to *target_path* via temp + rename + dir-fsync.

    Same shape as T5's ``user_merge_json._atomic_write`` — see there
    for the directory-fsync rationale.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    serialised = json.dumps(data, indent=2, sort_keys=False) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8", newline="\n",
        dir=str(target_path.parent),
        prefix=target_path.name + ".",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        tmp.write(serialised)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    tmp_path.replace(target_path)
    try:
        dir_fd = os.open(str(target_path.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:
        pass
