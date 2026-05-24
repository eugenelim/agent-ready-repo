"""``kiro-ide-hook`` projection — direct-file copy + ``then.command``
placeholder expansion (RFC-0005, v0.4).

The projection mode is ``direct-file`` byte-for-byte for askAgent-shaped
hooks (no scan surface) and parse-modify-emit for runCommand-shaped
hooks that contain ``${hook-body:<name>}`` placeholders in
``then.command``. RFC-0005 § Substitution rules pins the placeholder
mechanics:

  1. Scan surface — ``then.command`` only. Every other field in the
     ``.kiro.hook`` JSON (``then.prompt``, ``when.patterns``, ``name``,
     ``description``, …) passes through verbatim.
  2. Verbatim substitution — no shell quoting; pack authors quote
     placeholders themselves.
  3. Multiple placeholders allowed; single-pass resolution. Resolved
     text is NOT re-scanned.
  4. Placeholder grammar — strict regex ``\\$\\{hook-body:[a-zA-Z0-9_-]+\\}``.
     Validated upstream at ``validate`` time (T-C2's
     ``check_kiro_ide_hook`` rail in ``scope_rails.py``); a malformed
     placeholder reaching the projector is a defense-in-depth refusal.
  5. Unresolvable references refuse — same defense-in-depth.

The output path's ``<pack>`` placeholder resolves to the source
pack's directory name; the ``<name>`` placeholder resolves to the
``.kiro.hook`` file's bare name (extension stripped). Both are
substituted into the contract-declared ``target.repo`` template.

This module is stdlib-only — ``json`` + ``re`` + ``shutil`` +
``pathlib``.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


class KiroIdeHookRefusal(Exception):
    """Raised when projection refuses to write.

    All reachable paths are defense-in-depth (the validate rail
    refuses these cases upstream); the exception only fires when
    a caller skipped validate or supplied a malformed pack
    directly to the projector.
    """


# Strict placeholder grammar — same regex as the validate rail.
# Kept inline rather than imported so this module's contract is
# self-evident from its source; the rail's regex carries the same
# grammar.
_HOOK_BODY_PLACEHOLDER_RE = re.compile(r"\$\{hook-body:([a-zA-Z0-9_-]+)\}")

# Loose `${...}` matcher; an offender that matches this but not the
# strict regex above is a malformed placeholder.
_ANY_PLACEHOLDER_RE = re.compile(r"\$\{[^}]*\}")

# `.kiro.hook` is a compound extension; pathlib treats ``.hook`` as
# the suffix and ``.kiro`` as the prior segment. Endswith-check on
# the literal extension is more readable than juggling ``suffixes``.
_KIRO_HOOK_EXTENSION = ".kiro.hook"


def project(
    pack_path: Path,
    output_root: Path,
    target_template: str,
    hook_body_target_dir: str,
) -> None:
    """Project every ``.apm/kiro-ide-hooks/<name>.kiro.hook`` under
    *pack_path* into *output_root* per the *target_template* shape.

    Arguments:
      pack_path: pack source root.
      output_root: where to write projected files (the per-pack base
        the caller passes in — typically ``<dist>/<pack>/`` or the
        repo root for ``make build --self``).
      target_template: contract-declared
        ``[adapter.kiro.projections.kiro-ide-hook].target.repo``,
        e.g. ``".kiro/hooks/<pack>/<name>.kiro.hook"``. The
        ``<pack>`` and ``<name>`` placeholders resolve at projection
        time. The pre-bump v0.3 contract carries no such field
        (the v0.4 declaration is probe-gated, T-CONTRACT); callers
        targeting v0.3 contracts simply don't invoke this projector.
      hook_body_target_dir: the projected hook-body directory for
        same-pack ``${hook-body:<name>}`` references — e.g.
        ``"tools/hooks"`` at repo scope (the Kiro adapter's legacy
        ``[[adapter.kiro.projection]] primitive = "hook-body"``
        target). Resolved placeholders emit
        ``./{hook_body_target_dir}/<actual-filename>``.

    Raises:
      KiroIdeHookRefusal: on JSON parse failure, on a malformed
        placeholder reaching projection, or on an unresolvable
        placeholder. All three are validate-rail-covered cases;
        the projector refuses defensively rather than emitting a
        silently-wrong artifact.
    """
    source_dir = pack_path / ".apm" / "kiro-ide-hooks"
    if not source_dir.exists():
        return
    pack_name = pack_path.name
    hook_body_files = _collect_hook_body_files(pack_path)

    for entry in sorted(source_dir.iterdir()):
        if not entry.name.endswith(_KIRO_HOOK_EXTENSION):
            continue
        if not entry.is_file() or entry.is_symlink():
            continue

        bare_name = entry.name[: -len(_KIRO_HOOK_EXTENSION)]
        resolved_target = (
            target_template
            .replace("<pack>", pack_name)
            .replace("<name>", bare_name)
        )
        target_path = output_root / resolved_target.lstrip("/")
        target_path.parent.mkdir(parents=True, exist_ok=True)

        raw_bytes = entry.read_bytes()

        # askAgent byte-copy shortcut. RFC's placeholder grammar uses
        # `${` as the unambiguous prefix; if the raw file carries no
        # such substring AND the parsed JSON's then.type is askAgent,
        # the file has no expansion work to do and a byte copy
        # preserves the source's key order, whitespace, and trailing
        # newline.
        if b"${" not in raw_bytes:
            try:
                parsed = json.loads(raw_bytes.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise KiroIdeHookRefusal(
                    f"pack {pack_name}'s kiro-ide-hook {entry.name} "
                    f"failed to parse: {exc}"
                )
            if (
                isinstance(parsed, dict)
                and isinstance(parsed.get("then"), dict)
                and parsed["then"].get("type") == "askAgent"
            ):
                shutil.copy2(entry, target_path, follow_symlinks=False)
                continue
            # Non-askAgent without placeholders — also byte-copy. No
            # scan surface; nothing to rewrite.
            shutil.copy2(entry, target_path, follow_symlinks=False)
            continue

        # Otherwise: parse, expand, re-emit. The parse step also
        # catches malformed JSON the validate rail would already have
        # refused.
        try:
            body = json.loads(raw_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise KiroIdeHookRefusal(
                f"pack {pack_name}'s kiro-ide-hook {entry.name} "
                f"failed to parse: {exc}"
            )
        if not isinstance(body, dict):
            raise KiroIdeHookRefusal(
                f"pack {pack_name}'s kiro-ide-hook {entry.name} "
                f"is not a JSON object"
            )

        then = body.get("then")
        command = then.get("command") if isinstance(then, dict) else None
        if isinstance(command, str):
            new_command = _expand_placeholders(
                command,
                pack_name=pack_name,
                file_name=entry.name,
                hook_body_files=hook_body_files,
                hook_body_target_dir=hook_body_target_dir.rstrip("/"),
            )
            then["command"] = new_command

        # Emit with stable formatting — `indent=2` matches the
        # fixtures' shape and the RFC's example, `sort_keys=False`
        # preserves source ordering best-effort, trailing newline for
        # POSIX-friendliness.
        target_path.write_text(
            json.dumps(body, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )


def _collect_hook_body_files(pack_path: Path) -> dict[str, str]:
    """Return basename → filename for every hook-body the pack ships.

    e.g. ``{"lint": "lint.py", "format": "format.sh"}``. Used by
    placeholder resolution to emit the actual extension. Symlinks
    silently skipped (Rail B is the gate for symlinked hook-bodies
    at user scope; at repo scope the safer default is to ignore).
    """
    out: dict[str, str] = {}
    hook_body_dir = pack_path / ".apm" / "hooks"
    if not hook_body_dir.exists():
        return out
    for entry in sorted(hook_body_dir.iterdir()):
        if entry.is_symlink():
            continue
        if entry.is_file():
            out[entry.stem] = entry.name
    return out


def _expand_placeholders(
    command: str,
    *,
    pack_name: str,
    file_name: str,
    hook_body_files: dict[str, str],
    hook_body_target_dir: str,
) -> str:
    """Single-pass placeholder expansion against ``then.command``.

    Refuses (defense-in-depth) on malformed or unresolvable
    placeholders even though the validate rail covered these
    upstream. Resolved text is NOT re-scanned (RFC § Substitution
    rules clause 3) — single pass via ``re.sub``.
    """
    # Defense-in-depth check 1 — malformed placeholder.
    for match in _ANY_PLACEHOLDER_RE.finditer(command):
        literal = match.group(0)
        if not _HOOK_BODY_PLACEHOLDER_RE.fullmatch(literal):
            raise KiroIdeHookRefusal(
                f"pack {pack_name}'s kiro-ide-hook {file_name} "
                f"contains malformed placeholder '{literal}'; "
                f"expected ${{hook-body:<name>}} with name "
                f"matching [a-zA-Z0-9_-]+"
            )

    def _resolve(match: re.Match[str]) -> str:
        name = match.group(1)
        filename = hook_body_files.get(name)
        if filename is None:
            raise KiroIdeHookRefusal(
                f"pack {pack_name}'s kiro-ide-hook {file_name} "
                f"references unknown hook-body "
                f"'${{hook-body:{name}}}'; no such hook-body "
                f"in pack"
            )
        return f"./{hook_body_target_dir}/{filename}"

    return _HOOK_BODY_PLACEHOLDER_RE.sub(_resolve, command)
