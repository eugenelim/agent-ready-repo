"""``agentbundle creds`` — credential setup/check/where/rm verbs (T8).

Four subcommands per spec.md § AC16-AC23:

- ``setup <namespace>`` — prompt for required keys, write to the highest-
  available tier (keyring on Darwin/Windows; dotfile on Linux or when
  ``--allow-insecure-fallback`` is passed), announce the tier on stderr.
- ``check <namespace>`` — exit 0 when all required keys resolve, 2 when
  any is missing, 3 for other errors (schema parse, Tier-2 hard-fail).
- ``where <namespace>`` — print one line per required key naming the
  resolving tier (``env`` / ``keyring`` / ``dotfile`` / ``missing``).
  Never prints the value.
- ``rm <namespace>`` — delete every key in the namespace from every tier
  that holds it. Refuses if no tier holds anything.

**No ``get`` subcommand.** Per RFC-0006 § 5 and spec § AC21, printing the
cleartext token to stdout is foreclosed in v1 — the architecture rule
("primitives own the secret; the LLM never sees cleartext as a tool
argument") collapses if any verb writes the token to a file descriptor
a skill body can capture.

**Tombstone arguments for the argv ban** (spec § AC23): the ``setup``
subparser registers ``--token`` / ``--api-token`` / ``--api-key`` /
``--bearer`` / ``--pat`` / ``--password`` with a custom action that
prints the verbatim sentinel ``tokens cannot be passed via argv`` to
stderr and exits non-zero. The argparse default ``unrecognized
arguments:`` text would not match the AC23 anchor; the custom action
is what closes the contract.

Per-subcommand exit codes match the sibling-verb convention at
``agentbundle.commands.*``:

- 0 success.
- 2 missing-credential (the namespace's required keys did not all
  resolve; ``check`` is the canonical site).
- 3 other error (schema parse failure; Tier-2 hard-fail; no state-file
  hit for the namespace; the helper's own argv refusal).
"""

from __future__ import annotations

import argparse
import getpass
import os
import pathlib
import re
import sys

# Sentinel emitted by the tombstone-argument action. AC23 names this
# byte sequence as the canonical anchor; tests grep for it verbatim.
_ARGV_REFUSAL_STDERR = "tokens cannot be passed via argv"


# ── Tombstone argparse action (spec § AC23) ────────────────────────────


class _RefuseTokenArgvAction(argparse.Action):
    """Refuse any of the argv-borne credential flags.

    Registered on the ``setup`` subparser only — other ``agentbundle``
    verbs (and other ``creds`` subcommands) keep their default argparse
    behaviour so the tombstone shape is scoped, not global.

    The action emits the AC23-canonical stderr sentinel and exits with
    code 3 (the spec's "other error" bucket for the CLI verb).
    """

    def __init__(self, option_strings, dest, **kwargs):  # type: ignore[no-untyped-def]
        # ``nargs=0`` would make argparse refuse to consume a following
        # value, which is exactly wrong: ``--token foo`` must be caught
        # (the user is trying to pass the secret). Accept one value and
        # discard it before the refusal so the message is the same
        # whether the flag was given a value or not.
        kwargs.setdefault("nargs", "?")
        kwargs.setdefault("default", argparse.SUPPRESS)
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):  # type: ignore[no-untyped-def]
        sys.stderr.write(f"{_ARGV_REFUSAL_STDERR}\n")
        raise SystemExit(3)


# ── ``creds`` parser with custom error rewrite (spec § AC21) ──────────


class _CredsSubcommandParser(argparse.ArgumentParser):
    """Rewrites ``invalid choice: 'get'`` to ``unknown command: get``
    so AC21's negative-test contract holds.

    Argparse's default text would read ``argument <subcommand>: invalid
    choice: 'get' (choose from 'setup', 'check', 'where', 'rm')``; the
    test asserts the exact ``unknown command: get`` shape.
    """

    def error(self, message: str) -> None:  # type: ignore[override]
        m = re.search(r"invalid choice:\s*'([^']+)'", message)
        if m is not None:
            sys.stderr.write(f"unknown command: {m.group(1)}\n")
            raise SystemExit(3)
        super().error(message)


def build_parser(parent_subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Build the ``creds`` subparser and its four subcommands.

    Called from ``agentbundle.cli._build_parser`` so the verb plugs in
    next to the existing eleven siblings without a registry.
    """
    creds = parent_subparsers.add_parser(
        "creds",
        help="Manage credentials for credentialed primitives.",
        description=(
            "Set up, check, locate, or remove credentials for "
            "credentialed-primitive skills. Three tiers: env var, OS "
            "keyring (Darwin/Windows), dotfile (~/.agent-ready/"
            "credentials.env). No `get` subcommand — secrets do not "
            "leave their resolving process."
        ),
    )
    sub = creds.add_subparsers(
        dest="creds_subcommand",
        metavar="<subcommand>",
        parser_class=_CredsSubcommandParser,
    )
    # ``invalid choice`` rewriting also needs to fire on the parent
    # ``creds`` parser when the bad name is at *its* slot, not just
    # the subparser's.
    creds.__class__ = _CredsSubcommandParser

    # ── setup ─────────────────────────────────────────────────────────
    setup_p = sub.add_parser(
        "setup",
        help="Prompt for required keys and write to the highest-available tier.",
    )
    setup_p.add_argument(
        "namespace",
        nargs="?",
        help=(
            "The credential namespace (e.g. 'jira'). If omitted, the "
            "CLI walks both scope state files for installed primitives "
            "declaring credentialed: true and prompts for a selection."
        ),
    )
    setup_p.add_argument(
        "--allow-insecure-fallback",
        action="store_true",
        help=(
            "On a Tier-2-capable platform (Darwin/Windows), write to "
            "the Tier-3 dotfile instead of the OS keyring. No-op on "
            "Linux (Tier 2 is deferred to a v2 RFC; Linux always lands "
            "on Tier 3)."
        ),
    )
    setup_p.add_argument(
        "--allow-permissive-acl",
        action="store_true",
        help=(
            "On Windows, accept a Tier-3 dotfile parent whose DACL "
            "grants read access to non-default principals "
            "(BUILTIN\\Users, Everyone, Authenticated Users). No-op on "
            "POSIX."
        ),
    )
    setup_p.add_argument(
        "--root",
        default=".",
        help=(
            "Repo-scope root for the state-file walk (default: '.'). "
            "User-scope walks $HOME/.agent-ready/state.toml regardless."
        ),
    )
    # Tombstone arguments — spec § AC23. Scoped to the ``setup``
    # subparser only so other verbs (and other ``creds`` subcommands)
    # keep their default argparse shapes.
    for flag in (
        "--token", "--api-token", "--api-key",
        "--bearer", "--pat", "--password",
    ):
        setup_p.add_argument(flag, action=_RefuseTokenArgvAction)
    setup_p.set_defaults(creds_func=run_setup)

    # ── check ─────────────────────────────────────────────────────────
    check_p = sub.add_parser(
        "check",
        help="Verify the namespace's required keys all resolve. Exit 0/2/3.",
    )
    check_p.add_argument("namespace")
    check_p.add_argument("--root", default=".")
    check_p.set_defaults(creds_func=run_check)

    # ── where ─────────────────────────────────────────────────────────
    where_p = sub.add_parser(
        "where",
        help="Print the resolving tier for each required key (no values).",
    )
    where_p.add_argument("namespace")
    where_p.add_argument("--root", default=".")
    where_p.set_defaults(creds_func=run_where)

    # ── rm ────────────────────────────────────────────────────────────
    rm_p = sub.add_parser(
        "rm",
        help="Delete the namespace's keys from every tier that holds them.",
    )
    rm_p.add_argument("namespace")
    rm_p.add_argument("--root", default=".")
    rm_p.set_defaults(creds_func=run_rm)

    # The top-level CLI dispatches on ``args.func``; route every creds
    # subcommand through ``run`` which then reads ``args.creds_func``.
    creds.set_defaults(func=run)
    return creds


# ── Schema + state discovery ──────────────────────────────────────────


_SKILL_MD_RE = re.compile(r"^\.claude/skills/([^/]+)/SKILL\.md$")
_FRONTMATTER_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$")


def _parse_frontmatter(path: pathlib.Path) -> dict[str, str]:
    """Minimal stdlib YAML-subset frontmatter parser for SKILL.md.

    Matches the shape used by ``tools/lint-agent-artifacts.sh`` and
    ``tools/lint-credentialed-skills.sh``: single-line scalars only,
    no nested structures. Returns the empty mapping when the file has
    no frontmatter — the caller treats that as "not credentialed".
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = _FRONTMATTER_RE.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        # Drop surrounding quotes if balanced (allowed by YAML for the
        # 1-line scalar shape).
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in ('"', "'")
        ):
            value = value[1:-1]
        fields[key] = value
    return fields


def _walk_credentialed_skills(
    root: pathlib.Path,
) -> list[tuple[str, pathlib.Path, str, pathlib.Path]]:
    """Walk both scope state files for installed credentialed primitives.

    Returns a list of ``(scope_label, scope_root, skill_name,
    skill_md_path)`` tuples. ``scope_label`` is ``"repo"`` or ``"user"``
    so the CLI can show the user which scope a skill comes from.

    Implements the AC17 dual-scope state walk. The walk uses the
    existing ``PackState.files`` table (no state-schema bump): for each
    ``(pack, relpath)`` whose relpath matches ``^\\.claude/skills/
    [^/]+/SKILL\\.md$``, the CLI opens ``<scope-root>/<relpath>``,
    reads its YAML frontmatter, and includes the skill iff
    ``credentialed: true``.
    """
    from agentbundle import config

    out: list[tuple[str, pathlib.Path, str, pathlib.Path]] = []
    repo_state_path = root / ".agent-ready-state.toml"
    if repo_state_path.exists():
        repo_state = config.load_state(repo_state_path)
        for pack_state in repo_state.packs.values():
            for relpath in pack_state.files:
                m = _SKILL_MD_RE.match(relpath)
                if not m:
                    continue
                skill_md = root / relpath
                fields = _parse_frontmatter(skill_md)
                if fields.get("credentialed") == "true":
                    out.append(("repo", root, m.group(1), skill_md))
    try:
        user_root = pathlib.Path.home()
        user_state_path = user_root / ".agent-ready" / "state.toml"
    except (RuntimeError, OSError):  # pragma: no cover
        user_root = None  # type: ignore[assignment]
        user_state_path = None  # type: ignore[assignment]
    if user_state_path is not None and user_state_path.exists():
        user_state = config.load_state(user_state_path)
        for pack_state in user_state.packs.values():
            for relpath in pack_state.files:
                m = _SKILL_MD_RE.match(relpath)
                if not m:
                    continue
                skill_md = user_root / relpath
                fields = _parse_frontmatter(skill_md)
                if fields.get("credentialed") == "true":
                    out.append(("user", user_root, m.group(1), skill_md))
    return out


def _resolve_schema_for_namespace(
    namespace: str, root: pathlib.Path
) -> tuple["object", pathlib.Path]:
    """Find the schema declaring ``namespace`` across both scope states.

    Returns ``(schema, schema_path)``. Raises ``SchemaError`` if no
    credentialed primitive declares the namespace, or if every
    candidate skill's schema is malformed / missing.

    Convention: a credentialed primitive's namespace is whatever its
    schema's ``[namespace] name`` declares; the skill directory name
    is not constrained to match (though by convention they often do).
    The walk parses every credentialed skill's schema and matches by
    ``schema.namespace``.

    *Related primitive:* ``agentbundle.creds.loader.resolve_schema_path``
    walks the same ``PackState.files`` table per AC24b but looks up by
    *skill name*. This helper looks up by *namespace* — the user types
    ``agentbundle creds <verb> <namespace>``, not the skill name — so
    the two helpers are deliberate twins of the same lookup. Keep the
    canonical-path convention (``<skill-dir>/references/creds-schema.toml``)
    aligned across both.
    """
    from agentbundle.creds.exceptions import SchemaError
    from agentbundle.creds.loader import _parse_schema

    # Track the last parser failure so we can surface the actual root
    # cause if every candidate skill's schema is malformed — without
    # this, the operator sees the generic "no namespace declares..."
    # message and the malformed-TOML diagnostic is lost.
    last_parse_error: SchemaError | None = None
    for scope_label, scope_root, skill_name, skill_md in _walk_credentialed_skills(root):
        schema_path = skill_md.parent / "references" / "creds-schema.toml"
        if not schema_path.is_file():
            continue
        try:
            schema = _parse_schema(schema_path)
        except SchemaError as exc:
            last_parse_error = exc
            continue
        if schema.namespace == namespace:
            return schema, schema_path
    if last_parse_error is not None:
        raise SchemaError(
            f"no credentialed primitive declares namespace {namespace!r} "
            f"in either scope state file; one or more schemas failed to "
            f"parse: {last_parse_error}"
        )
    raise SchemaError(
        f"no credentialed primitive declares namespace {namespace!r} "
        f"in either scope state file"
    )


# ── Tier resolution helpers ───────────────────────────────────────────


def _tier_for_key(namespace: str, key: str) -> str:
    """Return the tier label where ``key`` is currently resolved, or
    ``"missing"`` when no tier holds it.

    Reads each tier in precedence order via the loader's internal
    helpers so the answer matches what ``load_credentials`` would
    return. The value is discarded — only the location matters.

    A ``Tier2HardFailError`` raised by the Tier-2 backend's read is
    **propagated**, not swallowed. AC11 mandates that hard-fail Win32
    error codes (``ERROR_NO_SUCH_LOGON_SESSION``, ``ERROR_INVALID_FLAGS``,
    ``ERROR_LOGON_FAILURE``) and macOS Keychain-locked exits do not
    silently fall through to Tier 3; the Boundaries § Never do clause
    "No silent fallback from hard-fail Win32 error codes" forbids it.
    Callers (``run_check``, ``run_where``, ``run_rm``) already wrap
    this helper in a ``Tier2HardFailError`` handler that returns exit
    3 with stderr.
    """
    from agentbundle.creds import loader

    env_name = f"{namespace.upper()}_{key}"
    env_val = os.environ.get(env_name)
    if env_val:
        return "env"
    if loader._tier2_backend is not None:
        # Tier2HardFailError propagates — see docstring.
        v = loader._tier2_backend.read_credential(namespace, key)
        if v:
            return "keyring"
    v3 = loader._dotfile_read(namespace, key)
    if v3:
        return "dotfile"
    return "missing"


def _tier2_capable() -> bool:
    """Whether the running platform has a Tier-2 backend wired in."""
    from agentbundle.creds import loader

    return loader._tier2_backend is not None


def _tier2_label() -> str:
    """Stderr-facing label naming which Tier-2 backend the platform uses."""
    if sys.platform == "darwin":
        return "macOS Keychain"
    if sys.platform == "win32":
        return "Windows Credential Manager"
    return "none"


# ── Subcommand: setup ─────────────────────────────────────────────────


def _prompt_for_keys(schema, *, tty_ok: bool) -> dict[str, str]:
    """Prompt for each key's value (``getpass`` for secrets; ``input``
    for non-secrets). Returns the ``{key: value}`` mapping.

    The ``tty_ok`` gate is enforced at the call site — this helper
    assumes a tty has already been confirmed for secret keys.
    """
    values: dict[str, str] = {}
    for keydef in schema.keys:
        prompt = f"{keydef.label}: "
        if keydef.secret:
            value = getpass.getpass(prompt)
        else:
            value = input(prompt)
        values[keydef.name] = value
    return values


def run_setup(args: argparse.Namespace) -> int:
    """``creds setup`` — write the namespace's required keys to a tier."""
    from agentbundle.creds.exceptions import (
        PermissiveAclError,
        SchemaError,
        Tier2HardFailError,
    )
    from agentbundle.creds import loader

    root = pathlib.Path(getattr(args, "root", ".")).resolve()
    namespace: str | None = args.namespace

    # AC17: no positional → walk state files, prompt for selection.
    if not namespace:
        candidates = _walk_credentialed_skills(root)
        if not candidates:
            sys.stderr.write(
                "creds setup: no credentialed primitives installed in "
                "either scope state file (run an install first)\n"
            )
            return 3
        if not sys.stdin.isatty():
            sys.stderr.write(
                "creds setup: stdin is not a tty (selection requires "
                "interactive prompt)\n"
            )
            return 3
        sys.stderr.write("Installed credentialed primitives:\n")
        for idx, (scope_label, _, skill_name, _) in enumerate(candidates, start=1):
            sys.stderr.write(f"  [{idx}] {skill_name}  ({scope_label} scope)\n")
        try:
            choice_raw = input("Select primitive [number]: ").strip()
            choice = int(choice_raw)
        except (ValueError, EOFError):
            sys.stderr.write("creds setup: invalid selection\n")
            return 3
        if not (1 <= choice <= len(candidates)):
            sys.stderr.write("creds setup: selection out of range\n")
            return 3
        _, _, skill_name, skill_md = candidates[choice - 1]
        schema_path = skill_md.parent / "references" / "creds-schema.toml"
        try:
            schema = loader._parse_schema(schema_path)
        except SchemaError as exc:
            sys.stderr.write(f"creds setup: {exc}\n")
            return 3
        namespace = schema.namespace
    else:
        try:
            schema, _ = _resolve_schema_for_namespace(namespace, root)
        except SchemaError as exc:
            sys.stderr.write(f"creds setup: {exc}\n")
            return 3

    # Spec § AC23: ``setup`` reads the token only from a tty. Argparse
    # has already rejected argv-borne flags; this guards the stdin pipe
    # path.
    if not sys.stdin.isatty():
        sys.stderr.write("creds setup: stdin is not a tty\n")
        return 3

    values = _prompt_for_keys(schema, tty_ok=True)

    insecure = bool(getattr(args, "allow_insecure_fallback", False))
    permissive = bool(getattr(args, "allow_permissive_acl", False))

    # Tier selection per AC16 + AC22:
    # - Linux: always Tier 3 (Tier 2 deferred to v2 RFC); --allow-
    #   insecure-fallback is a no-op.
    # - Darwin/Windows + --allow-insecure-fallback: Tier 3.
    # - Darwin/Windows default: Tier 2; hard-fail elevates to non-zero.
    if not _tier2_capable():
        return _write_dotfile_announce(
            namespace, values, allow_permissive_acl=permissive,
            stderr_tag="wrote to dotfile (Linux — Tier 2 deferred to v2 RFC)",
        )

    if insecure:
        return _write_dotfile_announce(
            namespace, values, allow_permissive_acl=permissive,
            stderr_tag="wrote to dotfile (insecure fallback)",
        )

    # Default Tier-2 path on Darwin/Windows.
    try:
        for key, value in values.items():
            loader._tier2_backend.write_credential(namespace, key, value)
    except Tier2HardFailError as exc:
        sys.stderr.write(
            f"creds setup: Tier 2 hard fail — {exc}; pass "
            "--allow-insecure-fallback to write to the dotfile instead\n"
        )
        return 3
    except PermissiveAclError as exc:  # pragma: no cover — Windows-only
        sys.stderr.write(f"creds setup: {exc}\n")
        return 3
    sys.stderr.write(f"wrote to keyring ({_tier2_label()})\n")
    return 0


def _write_dotfile_announce(
    namespace: str,
    values: dict[str, str],
    *,
    allow_permissive_acl: bool,
    stderr_tag: str,
) -> int:
    """Write each ``(namespace, key) → value`` to the Tier-3 dotfile and
    print ``stderr_tag``. Surfaces ``PermissiveAclError`` (Windows DACL)
    as exit 3 with the spec's documented stderr text."""
    from agentbundle.creds.exceptions import PermissiveAclError
    from agentbundle.creds import loader

    try:
        for key, value in values.items():
            loader._dotfile_write(
                namespace, key, value,
                allow_permissive_acl=allow_permissive_acl,
            )
    except PermissiveAclError as exc:
        sys.stderr.write(
            f"creds setup: DACL too permissive — {exc}; pass "
            "--allow-permissive-acl to override\n"
        )
        return 3
    if allow_permissive_acl and sys.platform == "win32":  # pragma: no cover
        sys.stderr.write("permissive DACL accepted\n")
    sys.stderr.write(f"{stderr_tag}\n")
    return 0


# ── Subcommand: check ─────────────────────────────────────────────────


def run_check(args: argparse.Namespace) -> int:
    """``creds check`` — verify required keys resolve. Exit 0/2/3."""
    from agentbundle.creds.exceptions import (
        SchemaError,
        Tier2HardFailError,
    )

    root = pathlib.Path(getattr(args, "root", ".")).resolve()
    namespace: str = args.namespace

    try:
        schema, _ = _resolve_schema_for_namespace(namespace, root)
    except SchemaError as exc:
        sys.stderr.write(f"creds check: {exc}\n")
        return 3

    missing: list[str] = []
    try:
        for keydef in schema.keys:
            tier = _tier_for_key(namespace, keydef.name)
            if tier == "missing":
                missing.append(keydef.name)
    except Tier2HardFailError as exc:
        sys.stderr.write(f"creds check: Tier 2 hard fail — {exc}\n")
        return 3
    if missing:
        sys.stderr.write(
            f"creds check: namespace {namespace!r}: missing required "
            f"key(s): {', '.join(missing)}\n"
        )
        return 2
    return 0


# ── Subcommand: where ─────────────────────────────────────────────────


def run_where(args: argparse.Namespace) -> int:
    """``creds where`` — print the resolving tier for each required key."""
    from agentbundle.creds.exceptions import (
        SchemaError,
        Tier2HardFailError,
    )

    root = pathlib.Path(getattr(args, "root", ".")).resolve()
    namespace: str = args.namespace

    try:
        schema, _ = _resolve_schema_for_namespace(namespace, root)
    except SchemaError as exc:
        sys.stderr.write(f"creds where: {exc}\n")
        return 3

    try:
        for keydef in schema.keys:
            tier = _tier_for_key(namespace, keydef.name)
            print(f"{keydef.name}: {tier}")
    except Tier2HardFailError as exc:
        sys.stderr.write(f"creds where: Tier 2 hard fail — {exc}\n")
        return 3
    return 0


# ── Subcommand: rm ────────────────────────────────────────────────────


def run_rm(args: argparse.Namespace) -> int:
    """``creds rm`` — delete the namespace's keys from every tier that
    holds them. Env clears are a no-op the helper documents on stderr.
    """
    from agentbundle.creds.exceptions import (
        SchemaError,
        Tier2HardFailError,
    )
    from agentbundle.creds import loader

    root = pathlib.Path(getattr(args, "root", ".")).resolve()
    namespace: str = args.namespace

    try:
        schema, _ = _resolve_schema_for_namespace(namespace, root)
    except SchemaError as exc:
        sys.stderr.write(f"creds rm: {exc}\n")
        return 3

    any_removed = False
    env_present_keys: list[str] = []
    for keydef in schema.keys:
        env_name = f"{namespace.upper()}_{keydef.name}"
        if os.environ.get(env_name):
            env_present_keys.append(env_name)
        if loader._tier2_backend is not None:
            try:
                if loader._tier2_backend.read_credential(namespace, keydef.name):
                    loader._tier2_backend.delete_credential(namespace, keydef.name)
                    any_removed = True
            except Tier2HardFailError as exc:
                sys.stderr.write(f"creds rm: Tier 2 hard fail — {exc}\n")
                return 3
        if loader._dotfile_read(namespace, keydef.name):
            loader._dotfile_delete(namespace, keydef.name)
            any_removed = True

    if env_present_keys:
        sys.stderr.write(
            "creds rm: env vars cannot be cleared by this helper; unset "
            f"manually: {', '.join(env_present_keys)}\n"
        )

    if not any_removed and not env_present_keys:
        sys.stderr.write(
            f"creds rm: namespace {namespace!r}: no tier holds any of "
            f"the schema's keys; nothing to remove\n"
        )
        return 3

    return 0


# ── CLI entry point (called by ``agentbundle.cli`` dispatcher) ────────


def run(args: argparse.Namespace) -> int:
    """Dispatch to the resolved subcommand. Required by the CLI."""
    func = getattr(args, "creds_func", None)
    if func is None:
        sys.stderr.write(
            "agentbundle creds: a subcommand is required "
            "(setup | check | where | rm)\n"
        )
        return 3
    return int(func(args))
