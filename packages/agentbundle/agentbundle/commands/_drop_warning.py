"""Shared drop-warning helpers for the install and validate commands.

Owns the per-file hook-wiring enumerator and the unified formatter that
produces both the install-time ``warning:`` line and the validate-time
``info:`` line.

docs/specs/incompatible-hook-event-drop AC6 / AC6b / AC6c / AC7.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Literal


# ---------------------------------------------------------------------------
# Pinned ordering for <reason-summary> in the formatter.
# Any future category is appended after these three in stable-sorted order.
# ---------------------------------------------------------------------------
_REASON_ORDER: tuple[str, ...] = (
    "event not in adapter vocabulary",
    "kiro requires 'attach-to-agent'",
    "hook-wiring TOML failed to parse",
)


def _adapter_agent_event_vocabulary(
    contract: dict,
    adapter: str,
) -> list[str] | None:
    """Return the ``agent-event-vocabulary`` list for *adapter*'s
    hook-wiring projections, or ``None`` if the adapter doesn't declare
    one.

    Reads ``[adapter.<name>.projections.hook-wiring].agent-event-vocabulary``
    from the contract dict.
    """
    projections = (
        contract.get("adapter", {})
        .get(adapter, {})
        .get("projections", {})
        .get("hook-wiring", {})
    )
    vocab = projections.get("agent-event-vocabulary")
    if isinstance(vocab, list):
        return vocab
    return None


def _is_primitive_type_dropped(
    contract: dict,
    adapter: str,
    primitive: str,
) -> bool:
    """Return ``True`` when the adapter projects *primitive* with
    ``mode = "dropped"`` at the type level.

    Walks ``[[adapter.<name>.projection]]`` entries — the legacy array
    that carries the coarse-grained per-type mode (used by the
    ``_enumerate_dropped_primitives`` rail in install.py). Returns
    ``False`` for any adapter that has no entry for the primitive or
    whose entry uses a non-dropped mode.
    """
    adapter_entries = (
        contract.get("adapter", {}).get(adapter, {}).get("projection", [])
    )
    for entry in adapter_entries:
        if entry.get("primitive") == primitive and entry.get("mode") == "dropped":
            return True
    return False


def enumerate_event_dropped_wirings(
    pack_dir: Path,
    adapter: str,
    contract: dict,
) -> list[tuple[str, str]]:
    """Return per-file hook-wiring drops as ``(relpath, reason_category)`` pairs.

    AC6 / AC6b / AC6c of spec incompatible-hook-event-drop.

    Walk semantics:
      Step 1 (type-level gate): if hook-wiring is ``mode = "dropped"``
        for the adapter at the type level, return ``[]`` early — the
        coarse-grained rail already covers it; no double-warning.
      Step 2: walk ``<pack_dir>/.apm/hook-wiring/*.toml`` (sorted by
        basename):
        2a (vocab check): if the adapter declares ``agent-event-vocabulary``
          and any ``[[hooks.<EventName>]]`` event-name isn't in the vocab,
          append one drop entry per file (break after first — one entry per
          file per reason category, AC6 dedup).
        2b (attach-to-agent, kiro-only): if ``attach-to-agent`` is omitted
          or empty (truthy check), append ``(relpath,
          "kiro requires 'attach-to-agent'")``.
        Parse-fail (AC6c): on ``tomllib.TOMLDecodeError`` or ``OSError``,
          append ``(relpath, "hook-wiring TOML failed to parse")``.
    """
    # Step 1: gate on non-dropped type.
    if _is_primitive_type_dropped(contract, adapter, "hook-wiring"):
        return []

    drops: list[tuple[str, str]] = []
    hook_wiring_dir = pack_dir / ".apm" / "hook-wiring"
    if not hook_wiring_dir.exists():
        return []

    vocab = _adapter_agent_event_vocabulary(contract, adapter)

    for toml_path in sorted(hook_wiring_dir.glob("*.toml")):
        relpath = f"hook-wiring/{toml_path.name}"
        # Split read + parse so OSError (unreadable file: permission,
        # truncation, race after glob) doesn't masquerade as a parse
        # failure in the warning. Unreadable files are skipped silently
        # — they'll surface elsewhere (project_pack's read attempt) and
        # the warning rail is for compatibility issues, not I/O.
        try:
            text = toml_path.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            data = tomllib.loads(text)
        except tomllib.TOMLDecodeError:
            # AC6c: install-time emits a parse-fail drop entry;
            # validate-time refuses earlier (separate code path).
            drops.append((relpath, "hook-wiring TOML failed to parse"))
            continue

        # Step 2a: vocab check.
        if vocab is not None:
            events = data.get("hooks", {})
            if isinstance(events, dict):
                for event_name in sorted(events.keys()):
                    if event_name not in vocab:
                        drops.append((relpath, "event not in adapter vocabulary"))
                        break  # one entry per file per reason category (AC6 dedup)

        # Step 2b: attach-to-agent check (kiro-only, presence-only).
        # AC4b carve-out: non-empty unknown-agent references remain
        # validate-time refusals; omitted-or-empty both flow here as
        # install-side drops. The validate side refuses on attach = ""
        # per the test pin, but install-side enumerator treats
        # omitted-or-empty as "effectively missing" for warning purposes.
        if adapter == "kiro":
            attach = data.get("attach-to-agent")
            if not isinstance(attach, str) or not attach:
                drops.append((relpath, "kiro requires 'attach-to-agent'"))

    return drops


def _join_serial_comma(items: list[str]) -> str:
    """Project's list-formatting convention: serial comma + 'and'.

    Examples:
      - ``[]`` → ``""``
      - ``["a"]`` → ``"a"``
      - ``["a", "b"]`` → ``"a and b"``
      - ``["a", "b", "c"]`` → ``"a, b, and c"``
    """
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + ", and " + items[-1]


def _build_reason_summary(reason_categories: list[str]) -> str:
    """Build the ``<reason-summary>`` string: deduplicated reason
    categories in pinned order, joined with `` + ``.

    Pinned order: vocabulary first, then attach-to-agent, then
    parse-fail. Any future category appears after in stable-sorted
    order.
    """
    seen: set[str] = set()
    ordered: list[str] = []
    for cat in _REASON_ORDER:
        if cat in reason_categories and cat not in seen:
            ordered.append(cat)
            seen.add(cat)
    # Defensive: any future category not in _REASON_ORDER.
    for cat in sorted(set(reason_categories)):
        if cat not in seen:
            ordered.append(cat)
    return " + ".join(ordered)


def _join_serial_comma_files(items: list[str]) -> str:
    """File-list variant: always uses serial comma (Oxford comma) before
    ``and``, including for two-item lists.

    AC2 pins the two-file form as ``"a, and b"`` (comma before "and")
    — differs from the compatible-list formatter which uses ``"a and b"``
    for two items. Isolating the file-list join prevents the two
    contracts from drifting if either is changed independently.

    Examples:
      - ``[]`` → ``""``
      - ``["a"]`` → ``"a"``
      - ``["a", "b"]`` → ``"a, and b"``
      - ``["a", "b", "c"]`` → ``"a, b, and c"``
    """
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + ", and " + items[-1]


def _build_file_list(file_relpath_pairs: list[tuple[str, str]]) -> str:
    """Build the ``<file-list>`` string: deduplicated file paths,
    lexicographically sorted, joined with serial-comma-plus-``and``.
    """
    files = sorted(set(f for f, _ in file_relpath_pairs))
    return _join_serial_comma_files(files)


def _pluralize_primitive_name(name: str) -> str:
    """Plural form of a primitive-type name."""
    if name == "hook-body":
        return "hook-bodies"
    return name + "s"


def format_drop_message(
    *,
    pack_name: str,
    adapter: str,
    dropped_counts: dict[str, int],
    compatible_types: list[str],
    event_drops: list[tuple[str, str]] | None = None,
    mode: Literal["install_warning", "validate_info"] = "install_warning",
) -> str:
    """Build the drop warning / info message.

    ``install_warning`` mode composes the three-clause grammar per
    spec AC7 + AC10's "Pinned wording":
      - Primitive-type clause (when ``dropped_counts`` non-empty).
      - Event-level clause (when ``event_drops`` non-empty), prefixed
        ``Additionally, `` when primitive clause also present.
      - Closing clause (when either prior fired).

    ``validate_info`` mode (AC2):
      - Ignores ``dropped_counts`` and ``compatible_types``.
      - Raises ``ValueError`` if ``dropped_counts`` is non-empty.
      - Raises ``ValueError`` if ``event_drops`` is empty.
      - Output: ``info: pack <name>: the following hook-wiring file(s)
        will not project to <adapter> (<reason-summary>): <file-list>.``

    Raises:
        ValueError: in ``install_warning`` mode when both
          ``dropped_counts`` and ``event_drops`` are empty.
        ValueError: in ``validate_info`` mode when ``event_drops`` is
          empty or when ``dropped_counts`` is non-empty.
    """
    effective_event_drops: list[tuple[str, str]] = event_drops or []

    if mode == "validate_info":
        if dropped_counts:
            raise ValueError(
                "format_drop_message: validate_info mode does not accept "
                "dropped_counts; validate-side rail is event-only"
            )
        if not effective_event_drops:
            raise ValueError(
                "format_drop_message: validate_info mode requires non-empty event_drops"
            )
        reason_cats = [reason for _, reason in effective_event_drops]
        reason_summary = _build_reason_summary(reason_cats)
        file_list = _build_file_list(effective_event_drops)
        return (
            f"info: pack {pack_name}: the following hook-wiring file(s) "
            f"will not project to {adapter} ({reason_summary}): {file_list}."
        )

    # install_warning mode
    # Determine non-zero dropped counts.
    nonzero_dropped = {
        ptype: count for ptype, count in dropped_counts.items() if count > 0
    }
    has_prim = bool(nonzero_dropped)
    has_event = bool(effective_event_drops)

    if not has_prim and not has_event:
        raise ValueError(
            "format_drop_message: install_warning mode has nothing to format; "
            "both dropped_counts and event_drops are empty"
        )

    clauses: list[str] = []

    # Primitive-type clause.
    if has_prim:
        count_parts: list[str] = []
        for ptype, count in sorted(nonzero_dropped.items()):
            if count == 1:
                count_parts.append(f"1 {ptype}")
            else:
                count_parts.append(f"{count} {_pluralize_primitive_name(ptype)}")
        count_list = _join_serial_comma(count_parts)
        clauses.append(
            f"pack {pack_name} ships {count_list} that {adapter} "
            f"projects as 'dropped'; these primitives will not be installed."
        )

    # Event-level clause.
    if has_event:
        reason_cats = [reason for _, reason in effective_event_drops]
        reason_summary = _build_reason_summary(reason_cats)
        file_list = _build_file_list(effective_event_drops)
        event_clause = (
            f"the following hook-wiring file(s) will be skipped "
            f"({reason_summary}): {file_list}."
        )
        if has_prim:
            event_clause = "Additionally, " + event_clause
        clauses.append(event_clause)

    # Closing clause.
    compatible_parts = [
        _pluralize_primitive_name(ptype) for ptype in sorted(compatible_types)
    ]
    compatible_list = _join_serial_comma(compatible_parts)
    clauses.append(f"The compatible primitives ({compatible_list}) will proceed.")

    return "warning: " + " ".join(clauses)
