"""``user-merge-json`` projection mode — Claude Code user scope.

Merges a pack's ``.apm/hook-wiring/*.toml`` content into the
hand-edited shared ``~/.claude/settings.json`` under the ``hooks`` key,
using **array-append-with-id** (not key-replace). The merger respects
three boundaries documented in RFC-0005 § Merge semantics:

1. Adopter-authored keys at the top level (``theme``, ``model``,
   ``env``, ...) are never read or rewritten.
2. Adopter-authored entries under ``hooks.<event>`` (entries without
   an id matching any installed pack's owned ids) are never reordered,
   never rewritten, and only inspected for textual collision against
   incoming pack commands.
3. Empty ``hooks.<event>`` arrays are removed after ``unproject``, so
   the file stays tidy across upgrade churn.

The module exposes two callables: ``project`` (install / reinstall)
and ``unproject`` (uninstall). Both write atomically via tmp + rename.

This module is stdlib-only — ``json`` + ``pathlib`` per the spec's
*Never do — No new top-level dependency* boundary.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from agentbundle.build.projections.hook_id import synthesize_id


class UserMergeRefusal(Exception):
    """Raised when ``project`` / ``unproject`` refuses to write.

    The exception's string is the refuse-and-explain text RFC-0005
    specifies. CLI callers (T8b's install / uninstall handlers) catch
    and print to stderr without paraphrasing.
    """


# RFC-0005 § Merge semantics: "textual equality after whitespace
# normalisation". Collapse runs of whitespace to a single space and
# strip leading/trailing whitespace before comparing commands.
_WS_RE = re.compile(r"\s+")


def _normalize_command(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return _WS_RE.sub(" ", value).strip()


def project(
    target_path: Path,
    pack_name: str,
    wiring_tomls: dict[str, dict],
    force_merge: bool = False,
) -> list[tuple[str, str]]:
    """Merge *wiring_tomls* into the JSON file at *target_path*.

    Arguments:
      target_path: ``~/.claude/settings.json`` (or test-redirected
        equivalent). Created with ``{}`` if absent.
      pack_name: the pack's ``[pack].name``. Substituted into id tags
        and into refusal text.
      wiring_tomls: map of wiring TOML basename (no ``.toml``) → parsed
        TOML body (typically ``{"hooks": {"<Event>": [entries]}}``).
        Iteration order is the call's order.
      force_merge: when True, an adopter-authored entry whose
        ``command`` collides with an incoming pack command is replaced
        rather than refused (RFC-0005 § User-already-set-this-key).

    Returns:
      List of ``(event, id)`` tuples reflecting every owned entry the
      call wrote. T8b records these in the state file's
      ``hook-wiring-owned`` table so ``unproject`` can be precise.

    Raises:
      UserMergeRefusal: on unparseable settings, wrong-shape ``hooks``
        or ``hooks.<event>``, adopter collision without ``force_merge``.
    """
    data = _load_settings(target_path)
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
                _merge_one_entry(
                    target_path=target_path,
                    pack_name=pack_name,
                    basename=basename,
                    event=event,
                    event_array=event_array,
                    tagged_entry=tagged,
                    force_merge=force_merge,
                )
                owned.append((event, entry_id))

    _atomic_write(target_path, data)
    # Deduplicate (event, id) tuples — a single wiring TOML may contribute
    # multiple entries under one event, but the state-side ownership
    # record only needs (event, id) once per logical pair.
    seen: set[tuple[str, str]] = set()
    result: list[tuple[str, str]] = []
    for item in owned:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def unproject(target_path: Path, owned: list[tuple[str, str]]) -> None:
    """Remove every ``(event, id)`` pair in *owned* from *target_path*.

    Empty ``hooks.<event>`` arrays are removed (not left as ``[]``).
    If the target file is absent, ``unproject`` is a no-op — there's
    nothing to remove. Unparseable JSON refuses with the same shape
    ``project`` does.

    Absent-file no-op note: a state row pointing at a now-absent
    target is an orphan-in-state condition that T9's
    ``reconcile --scope user`` reporter will surface. Refusing here
    would block uninstall of unrelated packs whose own target files
    happen to be absent — too aggressive for the uninstall path.
    """
    if not target_path.exists():
        return

    data = _load_settings(target_path)
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

    if not hooks:
        # Empty hooks dict is kept (it might still hold un-owned events
        # other than the ones we just cleared); only purely empty
        # arrays get pruned. If hooks is itself now empty after the
        # loop above, leave it as an empty object — other packs may
        # still target it on a future install.
        pass

    _atomic_write(target_path, data)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _load_settings(target_path: Path) -> dict:
    """Read the settings file. Returns ``{}`` for an absent file;
    raises ``UserMergeRefusal`` with the RFC-0005 unparseable text
    when the file exists but is not valid JSON."""
    if not target_path.exists():
        return {}
    try:
        text = target_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise UserMergeRefusal(
            f"cannot parse {target_path}: {exc}; fix or back up the file and retry"
        ) from exc
    if not text.strip():
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise UserMergeRefusal(
            f"cannot parse {target_path}: {exc}; fix or back up the file and retry"
        ) from exc
    if not isinstance(data, dict):
        # Root is structurally a different file shape than v0.2 ever
        # produced; route through the `cannot parse` text so the
        # refusal aligns with the unparseable case rather than
        # introducing a third dialect of `<key-path> has unexpected
        # shape` (the latter only applies under the `hooks` key path
        # tree, not at the JSON root).
        raise UserMergeRefusal(
            f"cannot parse {target_path}: top-level value is "
            f"{type(data).__name__}, expected object; fix or back up "
            f"the file and retry"
        )
    return data


def _shape_check_hooks(target_path: Path, data: dict) -> None:
    if "hooks" in data and not isinstance(data["hooks"], dict):
        raise UserMergeRefusal(
            f"{target_path}: hooks has unexpected shape {type(data['hooks']).__name__}; "
            f"expected object"
        )


def _shape_check_event_array(target_path: Path, event: str, value: object) -> None:
    if not isinstance(value, list):
        raise UserMergeRefusal(
            f"{target_path}: hooks.{event} has unexpected shape {type(value).__name__}; "
            f"expected array"
        )


def _merge_one_entry(
    *,
    target_path: Path,
    pack_name: str,
    basename: str,
    event: str,
    event_array: list,
    tagged_entry: dict,
    force_merge: bool,
) -> None:
    """Append, replace-in-place, or refuse for a single tagged entry.

    Mutates ``event_array`` in place. Three cases per RFC-0005:
      1. An existing entry with the same ``id`` → replace in place
         (idempotency / reinstall).
      2. An existing entry without ``id`` whose ``command`` matches
         (after whitespace normalisation) → adopter collision. Refuse
         unless ``force_merge`` (then replace in place).
      3. Otherwise → append.
    """
    incoming_id = tagged_entry["id"]
    incoming_cmd = _normalize_command(tagged_entry.get("command"))

    for index, existing in enumerate(event_array):
        if not isinstance(existing, dict):
            continue
        if existing.get("id") == incoming_id:
            event_array[index] = tagged_entry
            return
        if existing.get("id") is None:
            existing_cmd = _normalize_command(existing.get("command"))
            if existing_cmd and existing_cmd == incoming_cmd:
                if force_merge:
                    event_array[index] = tagged_entry
                    return
                raise UserMergeRefusal(
                    f"pack {pack_name}'s hook {basename} at event {event} "
                    f"appears to be already wired in {target_path}; "
                    f"remove the manual entry or pass --force-merge to take "
                    f"ownership"
                )

    event_array.append(tagged_entry)


def _atomic_write(target_path: Path, data: dict) -> None:
    """Write *data* to *target_path* via a temp file + rename.

    The rename is the atomic step on POSIX — readers either see the
    old file or the fully-written new file, never a partial. Uses
    ``tempfile.NamedTemporaryFile`` in the target's parent so the
    rename stays on the same filesystem (cross-filesystem rename is
    a copy, not atomic). The serialiser writes pretty JSON with
    2-space indent so the file diffs cleanly under version control —
    adopters who track ``~/.claude/settings.json`` in a dotfiles repo
    are the load-bearing audience here.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    serialised = json.dumps(data, indent=2, sort_keys=False) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
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
    # fsync the parent directory so the rename's directory entry hits
    # disk. Without this, a power loss between `replace()` and the
    # directory entry being flushed can leave the target absent
    # despite the rename appearing to succeed — the same byte-stability
    # concern AC9 / AC13 pin via their "file unchanged on refusal"
    # contracts. Tolerate OSError on platforms where dir-fsync is a
    # no-op (some macOS configurations).
    try:
        dir_fd = os.open(str(target_path.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:
        pass
