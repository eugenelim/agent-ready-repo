"""T10: `init-state` subcommand.

Given a working tree that already contains a pack's projection (e.g. from a
manual install or a `make build-self`), hash the on-disk projected files and
write `.agentbundle-state.toml` with their SHA-256s. This is the recovery
path: produce a state file for a tree that doesn't have one.

Algorithm (without ``--migrate``):
  1. Locate `<packs_dir>/<pack>/`; render in-memory via `render.render_pack`
     to learn the projection's relpath set.
  2. For each projected relpath:
     - Compute on-disk SHA at `<root>/<relpath>`.
     - If absent on disk, skip with a warning to stderr.
     - Otherwise add to `PackState.files[relpath] = {sha, from-pack-version}`.
  3. Load existing `.agentbundle-state.toml` (may be absent).
     Replace only `[pack.<args.pack>]`; leave other packs untouched.
  4. Write via `safety.write_jailed(args.root, ".agentbundle-state.toml", ...)`.
  5. Print summary to stdout.

With ``--migrate`` (RFC-0004 T13): the subcommand becomes a migration
verb instead — it reads the on-disk state file, augments every
``[pack.<name>]`` entry with ``scope = "repo"``, sets ``schema-version =
"0.2"``, and writes atomically. Idempotent against already-v0.2 files.
The flag accepts no ``--pack`` (the migration is whole-file), and the
``--scope`` selector picks which scope's state file to operate on
(``repo`` → ``<root>/.agentbundle-state.toml`` — the default;
``user`` → ``~/.agentbundle/state.toml`` via
``safety.user_state_path()``).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentbundle import config, render, safety
from agentbundle.commands._common import check_spec_version_gate


def run(args: argparse.Namespace) -> int:
    """Entry point called by the CLI dispatcher. Returns exit code."""
    # ── --migrate branch (RFC-0004 T13) ──────────────────────────────────
    # Migration is a different verb shape: no pack name, no rendering,
    # just rewrite the state file in place. Run before the regular init-
    # state path so the absent-file vs v0.1-file branches don't trip the
    # `--pack` requirement.
    if getattr(args, "migrate", False):
        return _run_migrate(args)

    root = Path(args.root).resolve()
    packs_dir = Path(getattr(args, "packs_dir", "packs"))
    if not packs_dir.is_absolute():
        packs_dir = root / packs_dir
    pack_name: str | None = getattr(args, "pack", None)
    if not pack_name:
        # argparse can't enforce the "required unless --migrate" shape
        # without an arg-group hack; we enforce it here so the handler's
        # entry contract stays simple and the error message names the
        # right verb.
        print(
            "init-state: --pack is required (omit it only with --migrate)",
            file=sys.stderr,
        )
        return 1
    pack_path = packs_dir / pack_name

    if not pack_path.is_dir():
        print(
            f"error: pack directory not found: {pack_path}",
            file=sys.stderr,
        )
        return 1

    # Read the pack version from pack.toml; refuse if absent (state file with
    # empty version cascades into useless install/uninstall comparisons).
    pack_toml_path = pack_path / "pack.toml"
    try:
        pack_meta = config.load_pack_toml(pack_toml_path)
    except config.ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    gate = check_spec_version_gate(pack_meta)
    if gate is not None:
        return gate

    pack_version = pack_meta.get("pack", {}).get("version")
    if not pack_version:
        print(
            f"error: pack {pack_name!r} has no [pack] version; "
            f"refusing to init-state without a known version anchor",
            file=sys.stderr,
        )
        return 1

    # Render in-memory to get the relpath set.
    try:
        rendered: dict[str, bytes] = render.render_pack(pack_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: render failed for pack '{pack_name}': {exc}", file=sys.stderr)
        return 1

    # Hash on-disk files; skip absent ones with a warning.
    files: dict[str, dict[str, str]] = {}
    skipped = 0
    for relpath in sorted(rendered):
        on_disk = root / relpath
        if not on_disk.exists():
            print(
                f"warning: projected file absent on disk, skipping: {relpath}",
                file=sys.stderr,
            )
            skipped += 1
            continue
        sha = safety.sha256_file(on_disk)
        files[relpath] = {"sha": sha, "from-pack-version": pack_version}

    # Load existing state (may be absent) and replace only this pack's table.
    # init-state is a *write* — refuse-and-explain on a v0.1 file so the
    # adopter opts into migration explicitly.
    state_path = root / ".agentbundle-state.toml"
    try:
        existing_state = config.load_state(state_path, for_write=True)
    except config.StateFileLegacy as exc:
        print(f"init-state: {exc}", file=sys.stderr)
        return 1

    # init-state records the legacy dist-tree projection, which has no
    # per-IDE adapter notion; key the row under the default claude-code
    # adapter so the file is v0.4-shaped (RFC-0052).
    new_pack_state = config.PackState(
        installed_version=pack_version,
        files=files,
        adapter="claude-code",
    )
    existing_state.packs[(pack_name, "claude-code")] = new_pack_state

    serialised = config.dump_state(existing_state)
    try:
        safety.write_jailed(root, ".agentbundle-state.toml", serialised)
    except safety.PathJailError as exc:
        print(f"init-state: {exc}", file=sys.stderr)
        return 1

    hashed_count = len(files)
    print(
        f"init-state: {hashed_count} file(s) hashed"
        + (f", {skipped} skipped (absent)" if skipped else "")
        + f" → {state_path}"
    )
    return 0


def _run_migrate(args: argparse.Namespace) -> int:
    """`init-state --migrate`: report on a state file's schema-version.

    Migration is **greenfield** as of state schema v0.4 (RFC-0052
    Decision 8): there is no converter from a legacy version. The prior
    header-only rewrite (v0.2/v0.3 → bump the version line, preserve the
    body) is unsafe under v0.4 because the body shape changed —
    ``[pack.<name>]`` became ``[pack.<name>.adapters.<adapter>]`` — so a
    header-only bump would relabel a v0.3 body as v0.4 and the reader
    would then mis-parse it. So this command now refuses any non-current
    version with re-install guidance, and treats an already-current file
    as an idempotent no-op.
    """
    scope = getattr(args, "scope", None) or "repo"
    if scope == "user":
        try:
            state_path = safety.user_state_path()
        except OSError as exc:
            print(f"init-state: cannot create user state directory: {exc}", file=sys.stderr)
            return 1
    else:
        root = Path(args.root).resolve()
        state_path = root / ".agentbundle-state.toml"

    if not state_path.exists():
        # Migration of an absent file is meaningless — surface so the
        # adopter doesn't think a no-op succeeded silently.
        print(
            f"init-state --migrate: no state file at {state_path}; nothing to migrate",
            file=sys.stderr,
        )
        return 1

    try:
        original_text = state_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"init-state --migrate: cannot read {state_path}: {exc}", file=sys.stderr)
        return 1

    source_version = _peek_schema_version(original_text)

    # Greenfield migration (RFC-0052 Decision 8): there is no converter
    # from a legacy schema to v0.4. The old header-only rewrite would have
    # relabelled a flat v0.3 ``[pack.<name>]`` body as v0.4 while leaving
    # the body in the v0.3 shape — a file the v0.4 reader would then
    # mis-parse. So any non-current version is refused with re-install
    # guidance; an already-current file is an idempotent no-op.
    if source_version == config.STATE_SCHEMA_VERSION:
        print(
            f"init-state --migrate: {state_path} is already schema-version "
            f"{config.STATE_SCHEMA_VERSION}; nothing to migrate"
        )
        return 0

    print(
        f"init-state --migrate: {state_path} is schema-version "
        f"{source_version or 'absent'}, but this agentbundle speaks "
        f"{config.STATE_SCHEMA_VERSION}. Migration is greenfield (RFC-0052 "
        f"D8) — reinstall the pack(s) to regenerate state instead.",
        file=sys.stderr,
    )
    return 1


import re as _re

# Match the top-level ``schema-version = "X.Y"`` line. The pattern
# anchors to *file* start (``\A``) with optional leading blank lines —
# TOML convention puts top-level keys at the head, and ``dump_state``
# emits ``schema-version`` as the first line. Restricting the regex to
# the file head prevents a stale pack-table value or a comment further
# down from being rewritten by accident.
_SCHEMA_VERSION_LINE_RE = _re.compile(
    r'\A(\s*)(schema-version\s*=\s*")([^"]*)(".*)',
)


def _peek_schema_version(text: str) -> str | None:
    """Return the schema-version string from a state-file body, or None."""
    m = _SCHEMA_VERSION_LINE_RE.match(text)
    return m.group(3) if m else None


def _rewrite_schema_version_line(text: str, new_version: str) -> str:
    """Rewrite the ``schema-version = "X.Y"`` header in *text* to *new_version*.

    Touches only the first match (anchored to file start) — every other
    byte is preserved. Trailing newline is preserved. This is the
    v0.2 → v0.3 (and v0.3 → v0.3 no-op) migration's whole job per
    RFC-0005 § State-file impact.
    """
    def _sub(m: _re.Match[str]) -> str:
        return f"{m.group(1)}{m.group(2)}{new_version}{m.group(4)}"
    return _SCHEMA_VERSION_LINE_RE.sub(_sub, text, count=1)
