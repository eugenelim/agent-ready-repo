"""Cross-command helpers re-used by more than one subcommand.

This module is imported lazily (alongside its sibling command modules) so it
does not add startup cost to `--version` / `--help`. Only pure stdlib is
allowed here — see spec § Never do.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple

from agentbundle.version import SPEC_VERSION

if TYPE_CHECKING:
    import argparse

    from agentbundle.config import PackState
    from agentbundle.safety import Tier


def resolve_catalogue_uri(args: "argparse.Namespace") -> str:
    """Resolve the catalogue URI for ``install`` / ``upgrade``.

    Applies the four-layer default chain (RFC-0046 / ADR-0036) when the
    ``catalogue`` positional was omitted. An explicit positional is returned
    verbatim (layer 1 short-circuits before any metadata/bundle read), so the
    default chain runs only on a bare invocation. May raise ``CatalogueError``
    when no layer yields a source — handlers catch it alongside their existing
    ``resolve_catalogue`` error handling.
    """
    from agentbundle.source_defaults import resolve_default_source

    user_cfg = getattr(args, "_user_config", None)
    config_source = getattr(user_cfg, "source", None)
    return resolve_default_source(
        getattr(args, "catalogue", None),
        config_source=config_source,
    )


def resolve_state_path(scope: str, root: Path) -> Path:
    """Return the state-file path for *scope* under *root*.

    ``scope="repo"`` → ``<root>/.agentbundle-state.toml``
    ``scope="user"`` → ``<root>/.agentbundle/state.toml``
    """
    if scope == "user":
        return root / ".agentbundle" / "state.toml"
    return root / ".agentbundle-state.toml"


class SeedDelivery(NamedTuple):
    """One seed file's delivery outcome, returned by ``deliver_seeds``.

    ``content`` is the *incoming* bytes the delivery used — for ``AGENTS.md``
    that is the composed body+footer, not the raw seed file — so a caller that
    records state hashes the same bytes the Tier comparison used. ``action`` is
    one of ``"wrote"`` (Tier-1, absent on disk), ``"skipped"`` (already
    byte-identical), or ``"companion"`` (Tier-2, adopter-edited → companion
    dropped). ``companion_relpath`` is the POSIX ``*.upstream.<ext>`` path when
    ``action == "companion"``, else ``None``.
    """

    relpath: str
    content: bytes
    action: str
    companion_relpath: str | None


def _compose_agents_md_bytes(body: bytes, footer_path: Path) -> bytes:
    """Compose the root ``AGENTS.md`` bytes from the body seed and optional footer.

    Mirrors ``build/self_host.py:_compose_agents_md`` (lines 268-281): LF-normalise
    and ensure a trailing newline on both halves, then concatenate. When the
    ``_agents-footer.md`` fragment is absent the body passes through **byte-for-byte
    unchanged** (no normalisation) so a footer-less pack delivers ``AGENTS.md`` verbatim.
    """
    if not footer_path.exists():
        return body
    text = body.decode("utf-8").replace("\r\n", "\n")
    if text and not text.endswith("\n"):
        text += "\n"
    footer = footer_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if footer and not footer.endswith("\n"):
        footer += "\n"
    return (text + footer).encode("utf-8")


def deliver_seeds(seeds_dir: Path, output: Path) -> list[SeedDelivery]:
    """Deliver a pack's ``seeds/`` into ``output`` with Tier-1/2/3 safety.

    For each file under ``seeds_dir`` (recursively):
      - **Composition fragments** (name starts with ``_``, e.g.
        ``_agents-footer.md``) are *not* delivered standalone — they are folded
        into ``AGENTS.md`` instead (per ``CONVENTIONS.md`` §Pack source-of-truth split).
      - **Absent on disk** → write the seed (Tier-1).
      - **Present, content matches** → no-op (already in sync).
      - **Present, content differs** → write a ``*.upstream.<ext>`` companion
        next to the original; leave the original untouched (Tier-2).

    Every write routes through ``safety.write_jailed`` / ``safety.write_companion``
    with the **bare under-root jail** (no ``allowed_prefixes`` — seeds land at the
    repo root and ``docs/``, outside the adapter projection prefixes). The caller
    decides whether to record state; this helper never writes ``.agentbundle-state.toml``.

    Raises ``safety.PathJailError`` if any seed relpath would escape ``output``;
    the caller is expected to catch it, print to stderr, and exit 1.
    """
    import os

    from agentbundle import safety

    footer_path = seeds_dir / "_agents-footer.md"
    # Guard the footer read too — ``_compose_agents_md_bytes`` reads
    # ``footer_path`` directly, so a symlinked footer would be read through.
    footer_ok = footer_path.is_file() and not footer_path.is_symlink()

    # Defence-in-depth against a malicious pack exfiltrating a host file
    # (``/etc/passwd``, ``~/.ssh/id_rsa``) into the adopter tree by symlinking
    # a seed — never read *through* a pack-shipped symlink. We must not rely on
    # ``Path.rglob``'s symlink posture: on Python 3.11/3.12 ``rglob`` recurses
    # *into* symlinked directories (3.13 changed the default to
    # ``recurse_symlinks=False``), so ``seeds/x -> /`` would surface real host
    # files as non-symlink entries. ``os.walk(followlinks=False)`` never
    # descends into a symlinked directory on any supported Python, and we also
    # skip symlinked files — closing both the file and directory cases.
    seed_files: list[Path] = []
    for dirpath, _dirnames, filenames in os.walk(seeds_dir, followlinks=False):
        for fname in filenames:
            fpath = Path(dirpath) / fname
            if fpath.is_symlink():
                continue
            seed_files.append(fpath)

    results: list[SeedDelivery] = []
    for seed_file in sorted(seed_files):
        # Composition fragments are folded in, never delivered standalone.
        if seed_file.name.startswith("_"):
            continue
        relpath = seed_file.relative_to(seeds_dir).as_posix()
        content = seed_file.read_bytes()
        if relpath == "AGENTS.md" and footer_ok:
            content = _compose_agents_md_bytes(content, footer_path)

        on_disk = output / relpath
        if not on_disk.exists():
            safety.write_jailed(output, relpath, content)
            results.append(SeedDelivery(relpath, content, "wrote", None))
        elif on_disk.read_bytes() == content:
            results.append(SeedDelivery(relpath, content, "skipped", None))
        else:
            safety.write_companion(output, relpath, content)
            companion = safety.companion_path(Path(relpath)).as_posix()
            results.append(SeedDelivery(relpath, content, "companion", companion))
    return results


def check_spec_version_gate(pack_toml: dict[str, Any]) -> int | None:
    """Refuse if the pack's declared spec major version differs from ours.

    Returns:
        None — caller may proceed (pack does not gate, or majors agree).
        1    — caller should `return` this immediately; refusal already
               printed to stderr with both versions named.

    The pack declares its version under `[pack.adapter-contract] version`;
    the CLI's version comes from `agentbundle.version.SPEC_VERSION` (read
    at import time from the bundled `adapter.toml`). AC #14 in the spec
    requires every subcommand that consumes a pack manifest to invoke
    this gate before any I/O the pack would drive — uniform refusal, no
    partial behaviour.
    """
    from agentbundle.config import pack_spec_version  # local import avoids circular

    declared = pack_spec_version(pack_toml)
    if declared is None:
        return None

    cli_major = _major(SPEC_VERSION)
    pack_major = _major(declared)
    if cli_major != pack_major:
        print(
            f"error: pack declares adapter-contract version {declared!r} "
            f"(major {pack_major}), but this CLI ships spec version {SPEC_VERSION!r} "
            f"(major {cli_major}); refusing to operate on incompatible pack.",
            file=sys.stderr,
        )
        return 1
    return None


def load_pack_and_gate(pack_path: Path) -> tuple[dict[str, Any], int] | tuple[dict[str, Any], None]:
    """Load a pack's `pack.toml` and apply the spec-version gate.

    Returns `(pack_toml, None)` on accept and `(pack_toml, 1)` on refusal.
    The pack_toml is returned in both cases so the caller can introspect
    even on refusal — useful for `validate` which reports schema errors
    and version errors together.
    """
    from agentbundle.config import load_pack_toml

    pack_toml = load_pack_toml(pack_path / "pack.toml")
    return pack_toml, check_spec_version_gate(pack_toml)


def _major(version: str) -> str:
    """Return the major component of a version string like '0.1' or 'v2.0'."""
    v = version.lstrip("v")
    return v.split(".")[0]


def format_adapter_versions(rows: "dict[str, PackState]") -> str:
    """Render sorted ``adapter (version)`` pairs for a multi-adapter
    disambiguator message (RFC-0052).

    ``rows`` is a ``{adapter: PackState}`` mapping (the shape
    ``State.rows_for_pack`` returns). Output e.g. ``claude-code (0.9.0),
    codex (0.9.0)`` — so a "pass --adapter" refusal names not just *which*
    adapters are installed but *at what version*, making the next command
    actionable without a second lookup.
    """
    return ", ".join(
        f"{adapter} ({rows[adapter].installed_version})" for adapter in sorted(rows)
    )


def count_drifted_files(pack_state: "PackState", root: Path) -> int:
    """Count *pack_state*'s files whose on-disk SHA differs from the recorded SHA.

    Row-scoped drift (Tier-2): compares each file against this row's own
    recorded SHA — **not** ``safety.classify``, which resolves against the SHA
    set across *all* rows and would undercount a co-owned path. A file absent on
    disk is not drift (it is Tier-1, "about to (re)write"). Render-free: needs
    only the loaded state plus on-disk bytes, so it is cheap enough to run
    before an upgrade confirm. Shared by ``list-installed --check-drift`` and
    the upgrade upfront drift notice.
    """
    from agentbundle.safety import sha256_file

    count = 0
    for relpath in pack_state.files:
        on_disk = root / relpath
        if not on_disk.exists():
            continue
        recorded = pack_state.file_sha(relpath)
        if recorded is not None and sha256_file(on_disk) != recorded:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Dry-run plan formatting (shared by `install --dry-run` and `upgrade --dry-run`)
# ---------------------------------------------------------------------------

# The complete set of action verbs `plan_action` can emit, in display order.
# `summarize_plan` counts against exactly this tuple, so the two must stay in
# sync: a new verb returned by `plan_action` must be added here or the summary
# would silently drop it from the per-action breakdown.
_PLAN_ACTIONS: tuple[str, ...] = ("create", "overwrite", "companion")


def plan_action(tier: "Tier", *, on_disk: bool) -> str:
    """Map a classified ``Tier`` + on-disk presence to a dry-run plan verb.

    The verb mirrors what a real run would do at that file:

      - ``Tier.TIER_2`` → ``"companion"`` — the adopter edited the file, so a
        real run drops a ``.upstream.<ext>`` companion and leaves the original.
      - ``Tier.TIER_1`` already on disk → ``"overwrite"``.
      - ``Tier.TIER_1`` absent → ``"create"``.

    Shared so a file is labelled identically whether the real run would
    ``install`` or ``upgrade`` it; the ``Tier`` itself comes from each command's
    own classifier (`commands.install._classify_for_install` / `safety.classify`)
    — this helper never reclassifies, it only names the action.
    """
    from agentbundle.safety import Tier

    if tier is Tier.TIER_2:
        return "companion"
    return "overwrite" if on_disk else "create"


def format_plan_line(
    action: str, tier: str, target: str, companion: str | None = None
) -> str:
    """Render one ``--dry-run`` plan line: ``<action> <tier> <target>``.

    For a Tier-2 ``companion`` action the line also names the companion the
    real run would drop: ``<target> -> <companion>``. ``tier`` is the stable,
    greppable tier label (``tier-1`` / ``tier-2`` / ``tier-3``). Columns are
    left-aligned so a multi-line plan reads as a table.
    """
    line = f"{action:<9} {tier:<6} {target}"
    if companion is not None:
        line += f" -> {companion}"
    return line


def summarize_plan(actions: list[str]) -> str:
    """One-line count summary closing a ``--dry-run`` plan.

    Counts each action verb (in the fixed order create / overwrite / companion)
    and restates the no-write guarantee, e.g.
    ``dry-run: 5 file(s) — 3 create, 2 companion. Nothing written.``
    """
    from collections import Counter

    counts = Counter(actions)
    parts = [
        f"{counts[verb]} {verb}"
        for verb in _PLAN_ACTIONS
        if counts.get(verb)
    ]
    body = ", ".join(parts) if parts else "no files"
    return f"dry-run: {len(actions)} file(s) — {body}. Nothing written."


# ---------------------------------------------------------------------------
# Destructive-confirmation mechanics (shared by `uninstall`, `install --force`,
# the `install`→`upgrade` offer, and `upgrade`)
# ---------------------------------------------------------------------------


def confirm_or_refuse(
    *,
    yes: bool,
    question: str,
    refuse_message: str,
    abort_message: str,
) -> bool:
    """Decide whether a destructive command may proceed.

    The single home for the confirm / non-TTY-refuse / ``--yes`` mechanics first
    introduced for ``upgrade`` in PR #374, so ``uninstall``, ``install --force``,
    and the ``install``→``upgrade`` offer share one implementation:

      - ``yes`` (the ``--yes`` flag) → return ``True`` without touching stdin.
      - non-interactive stdin (``not sys.stdin.isatty()``) → print
        ``refuse_message`` to stderr and return ``False`` (never block on
        ``input()``).
      - interactive stdin → prompt with ``question``; return ``True`` only when
        the reply is ``y``/``yes`` (case-insensitive, stripped). Any other reply
        — including EOF — prints ``abort_message`` to stderr and returns
        ``False``.

    The caller owns the ``--dry-run`` short-circuit (a dry run writes nothing, so
    it must return *before* calling this), and owns every command-specific
    message string passed in here — so each call site preserves its own exact
    stderr contract.
    """
    if yes:
        return True
    if not sys.stdin.isatty():
        print(refuse_message, file=sys.stderr)
        return False
    try:
        reply = input(question)
    except EOFError:
        reply = ""
    if reply.strip().lower() not in ("y", "yes"):
        print(abort_message, file=sys.stderr)
        return False
    return True


# ---------------------------------------------------------------------------
# Terminal-aware table rendering (shared by `list-packs`, `list-profiles`)
# ---------------------------------------------------------------------------

# Floor for the wrapped column so a very narrow terminal still gets a readable
# (if tall) cell rather than one-character-per-line. Below this we let the row
# overflow the terminal rather than shred the text.
_MIN_WRAP_WIDTH = 20

# Spaces between columns.
_COL_GAP = 2


def _stream_is_tty(stream: Any) -> bool:
    """True only when *stream* is a real interactive terminal.

    A closed or non-tty stream (pytest's capture, a pipe, a file) answers
    False — and may raise ``ValueError`` on a closed file — so we swallow both.
    """
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError):
        return False


def render_table(
    headers: list[str],
    rows: list[list[str]],
    *,
    wrap_col: int | None = None,
    stream: Any = None,
) -> None:
    """Print a left-justified, content-sized column table to *stream*.

    Columns are sized to the widest of their header and cells. When *wrap_col*
    is given **and** the destination is an interactive terminal **and** the
    natural table would overflow that terminal's width, that one column is
    word-wrapped to the leftover width; every other column keeps its content
    width, the row spans as many physical lines as the wrap needs, and the
    columns that follow the wrapped one appear on the row's first line only.

    Wrapping is deliberately suppressed when stdout is **not** a TTY (piped or
    redirected): the table is emitted at full content width, untruncated, so
    downstream tools (`grep`, `awk`, `cut`) see stable, parseable columns — the
    convention `gh`, `git`, and `ls` follow. It is likewise suppressed when the
    natural table already fits, leaving that output byte-identical to a plain
    content-width table.

    ``stream`` defaults to ``sys.stdout`` (read at call time, not import time,
    so a window resize between invocations is honoured).
    """
    import shutil
    import textwrap

    if stream is None:
        stream = sys.stdout

    ncols = len(headers)
    widths = [len(h) for h in headers]
    for row in rows:
        for i in range(ncols):
            widths[i] = max(widths[i], len(row[i]))

    # Decide the wrapped column's width, if any.
    wrap_width: int | None = None
    if wrap_col is not None and _stream_is_tty(stream):
        term_cols = shutil.get_terminal_size(fallback=(80, 24)).columns
        natural = sum(widths) + _COL_GAP * (ncols - 1)
        if natural > term_cols:
            others = natural - widths[wrap_col]
            wrap_width = max(_MIN_WRAP_WIDTH, term_cols - others)
            widths[wrap_col] = wrap_width

    gap = " " * _COL_GAP

    def emit(cells: list[str]) -> None:
        if wrap_width is None:
            line = gap.join(cells[i].ljust(widths[i]) for i in range(ncols))
            print(line.rstrip(), file=stream)
            return
        chunks = textwrap.wrap(cells[wrap_col], width=wrap_width) or [""]
        for li, chunk in enumerate(chunks):
            parts = [
                (chunk if i == wrap_col else (cells[i] if li == 0 else "")).ljust(
                    widths[i]
                )
                for i in range(ncols)
            ]
            print(gap.join(parts).rstrip(), file=stream)

    emit(headers)
    # Separator built directly so a long dash run is never word-wrapped.
    print(gap.join("-" * widths[i] for i in range(ncols)).rstrip(), file=stream)
    for row in rows:
        emit(row)
