"""Cross-command helpers re-used by more than one subcommand.

This module is imported lazily (alongside its sibling command modules) so it
does not add startup cost to `--version` / `--help`. Only pure stdlib is
allowed here — see spec § Never do.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, NamedTuple

from agentbundle.version import SPEC_VERSION


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
