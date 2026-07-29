"""`agentbundle` CLI dispatcher — argparse over the F-cli subcommands.

Subcommand order on the parser matches the canonical install-workflow order
from the spec (discovery-first): `list-packs`, `list-profiles`, `list-targets`,
`scaffold`, `install`, `validate`, `render`, `adapt`, `diff`, `upgrade`,
`uninstall`, `init-state`, `config`, `reconcile`, `package-catalogue`.
`list-profiles` (RFC-0034) lists the catalogue's curated single-scope install
profiles; `install --profile <name>` installs one.

Each subcommand's `run(args) -> int` lives under `agentbundle.commands.*`;
this module wires `argparse` and prints `--version`. No business logic here.

RFC-0004 surface additions:
  - `--scope {repo,user}` on install, uninstall, upgrade, diff, init-state
    (the spec § *Install-scope dimension* subcommands). The original RFC-0004
    set also listed `list-targets`, and `reconcile` carried a single-value
    `--scope user`; both were dead (parsed-but-never-read / only-legal-value-
    equals-default) and dropped in the CLI-hygiene sweep, so passing `--scope`
    to either now surfaces `unknown flag for <verb>: --scope`.
  - `--force` on install only (cross-scope conflict bypass; see
    spec § *Dual-scope install conflict*).
  - Forbidden flags on the five excluded subcommands surface with the
    spec's exact stderr contract: `unknown flag for <verb>: <flag>`.
    `argparse`'s default text (`error: unrecognized arguments:`) omits
    the verb and shapes the prefix differently, so a custom subclass
    over `error()` rewrites the message before exiting.
"""

from __future__ import annotations

import argparse
import re
import sys
from typing import Sequence

from agentbundle.version import CLI_VERSION, SPEC_VERSION

# Path-bearing argparse-attribute names. The set is curated rather than
# "every string attribute" so a future flag carrying a content string
# with a literal backslash (a regex fragment, a message body) is not
# silently mangled. Update this list — and the corresponding test in
# `tests/unit/test_cli_path_normalisation.py` — when adding a new
# path-bearing flag.
_PATH_BEARING_ATTRS = frozenset(
    {
        "output",
        "output_dir",
        "root",
        "pack_path",
        "packs_dir",
        "catalogue",
        "values_from",
        # `path` is the validate-subcommand positional in the sibling
        # `agentbundle.build` parser; it points at adapter.toml / a
        # contract file. Both entry points run the same normaliser
        # over the same allow-list so a backslash works equally on
        # `agentbundle render packs\core` and `python -m
        # agentbundle.build validate docs\contracts\adapter.toml`.
        "path",
        # `target` is the catalogue-init positional: the directory to initialize.
        "target",
        # `source` is the catalogue-init --source flag: path to source catalogue root.
        "source",
    }
)


# Flags the spec's stderr contract names by hand. `error()` re-emits
# any "unrecognized arguments: --scope[=value]" or "--force" mention
# from argparse with the documented `unknown flag for <verb>: <flag>`
# shape. Other unrecognised flags keep argparse's default text so we
# don't accidentally swallow typos.
_REWRITE_FLAGS = ("--scope", "--force", "--force-merge")


class _VerbAwareParser(argparse.ArgumentParser):
    """An ArgumentParser that knows its verb and rewrites the
    "unrecognized arguments" error for `--scope` / `--force` to match
    the spec's exact stderr contract.

    `prog` carries the verb name on subparsers (parent argparse sets
    `prog = "<parent-prog> <subcommand>"`), so the verb is the last
    whitespace-delimited token. The rewrite captures the bare flag
    (stripping any `=value` suffix that argparse merged into one token
    when the user wrote `--scope=user`) and emits the documented
    `unknown flag for <verb>: <flag>` line.

    On the *subparser*, `error()` is called from
    `_VerbAwareSubParsersAction.__call__` when extras with spec flags
    are detected — the override here picks up the verb from
    `self.prog`. On the main parser, `error()` is reached only when
    none of the extras matched a spec flag (subparser-level interception
    already covered those), so the override falls through to argparse's
    default behaviour.
    """

    def error(self, message: str) -> None:  # type: ignore[override]
        match = re.match(r"^unrecognized arguments: (\S+)", message)
        if match is not None:
            token = match.group(1)
            bare = token.split("=", 1)[0]
            if bare in _REWRITE_FLAGS and " " in self.prog:
                # On subparsers, prog is "<parent> <verb>" — extract verb.
                verb = self.prog.rsplit(" ", 1)[-1]
                sys.stderr.write(f"unknown flag for {verb}: {bare}\n")
                raise SystemExit(2)
        super().error(message)


class _VerbAwareSubParsersAction(argparse._SubParsersAction):
    """Hijack subparser dispatch to surface spec-flag refusals at the
    *subparser* level so the verb in the stderr message is correct.

    Default `_SubParsersAction.__call__` parses the subcommand's args
    with `parse_known_args` and stores extras on the main namespace;
    the main parser then surfaces "unrecognized arguments" later, with
    its own `prog` (no verb). By calling `subparser.error()` ourselves
    when extras include `--scope` or `--force`, the error path
    inherits the subparser's prog (`agentbundle list-packs`), and
    `_VerbAwareParser.error` rewrites it to the documented contract.

    Non-spec-flag extras propagate normally — we only intercept the
    two flags the spec names byte-for-byte.
    """

    def __call__(self, parser, namespace, values, option_string=None):  # type: ignore[override]
        parser_name = values[0]
        arg_strings = values[1:]
        if parser_name not in self._name_parser_map:
            return super().__call__(parser, namespace, values, option_string)
        subparser = self._name_parser_map[parser_name]
        subnamespace, extras = subparser.parse_known_args(arg_strings, None)
        # Copy parsed attrs into the main namespace as argparse would.
        for key, value in vars(subnamespace).items():
            setattr(namespace, key, value)
        # Intercept spec-flag extras at the subparser level.
        for token in extras:
            bare = token.split("=", 1)[0]
            if bare in _REWRITE_FLAGS:
                # Calls _VerbAwareParser.error on the subparser; that
                # path rewrites to the spec's stderr contract.
                subparser.error(f"unrecognized arguments: {bare}")
                return None  # unreachable — error() raises SystemExit
        # No spec-flag extras — re-propagate everything for argparse's
        # default unrecognised-args path on the main parser.
        if extras:
            vars(namespace).setdefault("_unrecognized_args", [])
            namespace._unrecognized_args.extend(extras)
        return None


def _version_string() -> str:
    return f"agentbundle {CLI_VERSION} (spec {SPEC_VERSION})"


def _shipped_adapters_choices() -> tuple[str, ...]:
    """Derive argparse `--adapter` `choices=` from the live contract.

    Every shipped adapter (not just user-scope-capable ones), per
    RFC-0011 AC11: the handler issues the pinned refuse-and-explain
    when an adopter passes a shipped-but-not-user-scope-capable adapter
    (e.g. `--adapter copilot`), and argparse must accept the value
    first for the handler to be reached.
    """
    from agentbundle.scope import shipped_adapters_from_contract

    return shipped_adapters_from_contract()


def _build_parser() -> argparse.ArgumentParser:
    parser = _VerbAwareParser(
        prog="agentbundle",
        description=(
            "Reference CLI for the agent-ready-repo adapter contract. "
            "Library-first counterpart to the `adapt-to-project` LLM skill."
        ),
    )
    # Replace argparse's default _SubParsersAction with the verb-aware
    # subclass that surfaces --scope / --force refusals on the
    # subparser (correct verb in the stderr message).
    parser.register("action", "parsers", _VerbAwareSubParsersAction)
    parser.add_argument(
        "--version",
        action="version",
        version=_version_string(),
    )

    # Use _VerbAwareParser for every subparser so the forbidden-flag
    # error message names the verb correctly.
    subparsers = parser.add_subparsers(
        dest="command",
        metavar="<command>",
        parser_class=_VerbAwareParser,
    )

    # --- list-packs --- (no --scope; catalogue query, scope unbound)
    sp = subparsers.add_parser(
        "list-packs",
        help="List packs available in a catalogue URI (local path or git+https).",
    )
    sp.add_argument(
        "catalogue",
        nargs="?",
        default=None,
        help=(
            "Catalogue URI (local path or git+https://...). Optional: when "
            "omitted, the source is resolved from your config, an editable "
            "clone, or the packaged default (RFC-0047)."
        ),
    )
    sp.set_defaults(func=_lazy("list_packs"))

    # --- list-profiles --- (catalogue query; profiles declare their own scope)
    sp = subparsers.add_parser(
        "list-profiles",
        help="List curated install profiles available in a catalogue URI.",
    )
    sp.add_argument(
        "catalogue",
        nargs="?",
        default=None,
        help=(
            "Catalogue URI (local path or git+https://...). Optional: when "
            "omitted, the source is resolved from your config, an editable "
            "clone, or the packaged default (RFC-0047)."
        ),
    )
    sp.set_defaults(func=_lazy("list_profiles"))

    # --- list-targets --- (no flags; queries the adapter registry)
    sp = subparsers.add_parser(
        "list-targets",
        help=(
            "List adapter targets the CLI supports "
            "(claude-code, kiro-ide, kiro-cli, kiro (deprecated → kiro-ide), copilot, codex)."
        ),
    )
    sp.set_defaults(func=_lazy("list_targets"))

    # --- list-installed --- (state-file reader; both scopes by default)
    sp = subparsers.add_parser(
        "list-installed",
        help=(
            "List installed packs across user and repo scope with version and "
            "up-to-date status (vs. a catalogue). Read-only."
        ),
    )
    sp.add_argument(
        "catalogue",
        nargs="?",
        default=None,
        help=(
            "[Deprecated] Catalogue URI -- now ignored; rows are resolved against "
            "their recorded provenance. Use --no-check to skip catalogue resolution "
            "entirely."
        ),
    )
    sp.add_argument("--root", default=".")
    sp.add_argument(
        "--scope",
        choices=("repo", "user"),
        help="Limit the listing to one scope. Default: both user and repo.",
    )
    sp.add_argument(
        "--no-check",
        "--offline",
        dest="no_check",
        action="store_true",
        help=(
            "Skip the catalogue up-to-date check (no network): print only "
            "pack/adapter/scope/installed, omitting LATEST and STATUS."
        ),
    )
    sp.add_argument(
        "--check-drift",
        action="store_true",
        help=(
            "Add a DRIFT column counting installed files locally edited since "
            "install (on-disk SHA differs from the recorded SHA)."
        ),
    )
    sp.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format: table (default) or json.",
    )
    sp.add_argument(
        "--updates-only",
        action="store_true",
        default=False,
        help=(
            "Show only rows needing attention (upgrade-available, ahead, unknown). "
            "Summary counts always reflect the full set. No effect under --no-check."
        ),
    )
    sp.set_defaults(func=_lazy("list_installed"))

    # --- show --- (catalogue query; walks a pack's .apm/ tree live)
    sp = subparsers.add_parser(
        "show",
        help=(
            "Show a pack's skills and agents, derived live from its .apm/ tree. "
            "Falls back to the install state when the catalogue is unresolvable."
        ),
    )
    sp.add_argument("pack", help="Pack name to inspect (e.g. core).")
    sp.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table).",
    )
    sp.add_argument(
        "--root",
        default=".",
        help=(
            "Repo root used to locate the repo-scope install-state file for the "
            "catalogue-unresolvable fallback. Default: current directory."
        ),
    )
    sp.set_defaults(func=_lazy("show"))

    # --- docs --- (catalogue query; reads packs/<pack>/docs/)
    sp = subparsers.add_parser(
        "docs",
        help=(
            "Read pack documentation from the catalogue source. "
            "Displays index.md by default; use --list to enumerate files."
        ),
    )
    sp.add_argument("pack", help="Pack name to read docs for (e.g. core).")
    sp.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Documentation file stem to display (e.g. 'concept'). Default: index.",
    )
    sp.add_argument(
        "--list",
        action="store_true",
        dest="list_docs",
        help="List available documentation files for the pack.",
    )
    sp.set_defaults(func=_lazy("docs"))

    # --- scaffold --- (no --scope; always repo-targeted)
    sp = subparsers.add_parser(
        "scaffold",
        help="Drop a pack's seeds/ into --output, honouring Tier-1/2/3 file-safety.",
    )
    sp.add_argument("--pack", default="core")
    sp.add_argument("--packs-dir", default="packs")
    sp.add_argument("--output", required=True)
    sp.set_defaults(func=_lazy("scaffold"))

    # --- install --- (--scope override + --force cross-scope bypass)
    sp = subparsers.add_parser(
        "install",
        help="Install a pack from a catalogue URI into the adopter repo.",
    )
    # pack-profiles: `--pack` and `--profile` are a required mutually-exclusive
    # group. `--pack` was a bare `required=True` arg; making it a member of a
    # required mutex group keeps "exactly one of pack/profile" without losing
    # the requiredness. `--scope` with `--profile` is rejected at the handler
    # (a profile declares its own scope); argparse can't express that mutex
    # because `--scope` is valid alongside `--pack`.
    _pack_or_profile = sp.add_mutually_exclusive_group(required=True)
    _pack_or_profile.add_argument("--pack")
    _pack_or_profile.add_argument(
        "--profile",
        help=(
            "Install a curated single-scope set of packs from "
            "<catalogue>/profiles/<name>.toml in one command (RFC-0034). "
            "Mutually exclusive with --pack; --scope is not allowed (the "
            "profile declares its own scope)."
        ),
    )
    sp.add_argument(
        "catalogue",
        nargs="?",
        default=None,
        help=(
            "Catalogue URI (local path or git+https://...). Optional: when "
            "omitted, the source is resolved from your config, an editable "
            "clone, or the packaged default (RFC-0046)."
        ),
    )
    sp.add_argument("--output", default=".")
    sp.add_argument("--scope", choices=("repo", "user"))
    sp.add_argument(
        "--force",
        action="store_true",
        help=(
            "RFC-0004: bypass the cross-scope-conflict refusal — install at "
            "the requested scope even when the pack is already installed at "
            "the other scope. Also REMOVES on-disk files at the pack's "
            "projection paths that the current version does not ship "
            "(unrecognized leftovers from an older or interrupted install) "
            "before reinstalling. Does *not* override the in-place re-install "
            "refusal; use `upgrade` for that."
        ),
    )
    sp.add_argument(
        "--force-merge",
        action="store_true",
        help=(
            "RFC-0005: adopt an adopter-hand-authored entry under "
            "`~/.claude/settings.json` whose `command` collides with the "
            "pack's hook. Bound to `install --scope user` against a "
            "Claude-Code-targeted pack only; original command preserved "
            "in the state-file snapshot."
        ),
    )
    # RFC-0011 / pack-allowed-adapters AC11: optional `--adapter`
    # override at install time. choices=every-shipped-adapter (not
    # just user-scope-capable) so the handler-level user-scope check
    # can issue the pinned refuse-and-explain for copilot rather than
    # argparse's stock "invalid choice" error.
    _shipped_for_cli = _shipped_adapters_choices()
    sp.add_argument(
        "--adapter",
        choices=_shipped_for_cli,
        help=(
            "Override the auto-detected adapter. Admitted at both "
            "install scopes (RFC-0012). Must be in the pack's "
            "`allowed-adapters` set when declared (legacy packs apply "
            "the user-scope-capable / shipped-adapter subset by scope). "
            "Mutually exclusive with --emit-install-routes at --scope "
            f"repo. Shipped adapters: {', '.join(_shipped_for_cli)}."
        ),
    )
    sp.add_argument(
        "--emit-install-routes",
        action="store_true",
        help=(
            "RFC-0012: catalogue-publishing opt-in — emit the legacy "
            "dist-tree shape (`<repo>/claude-plugins/<pack>/`, "
            "`<repo>/apm/<pack>/`) at `--scope repo` instead of the "
            "default per-IDE projection. Bound to `--scope repo`; "
            "mutually exclusive with `--adapter` at that scope."
        ),
    )
    sp.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Preview the per-file plan (action + tier + target path) without "
            "writing anything — no projected file, companion, state, or install "
            "marker, and no chained adapt. Refused with --force (its destructive "
            "cleanup is incompatible with a read-only preview). Exits 0 on a "
            "successful preview, even with Tier-2 collisions present."
        ),
    )
    sp.add_argument(
        "--yes",
        action="store_true",
        help=(
            "Answer yes to install's interactive confirmations: the --force "
            "destructive-cleanup prompt (removing leftover files), and the "
            "offer to upgrade a pack already installed at the requested scope. "
            "Required for non-interactive use of those paths; without it they "
            "prompt on a TTY and refuse rather than block on a non-TTY."
        ),
    )
    sp.set_defaults(func=_lazy("install"))

    # --- validate --- (no --scope; schema + rails A/B/C)
    sp = subparsers.add_parser(
        "validate",
        help="Validate a pack's pack.toml against the schemas; --strict for conformance.",
    )
    sp.add_argument("pack_path", help="Path to a pack directory containing pack.toml.")
    sp.add_argument("--strict", action="store_true")
    sp.set_defaults(func=_lazy("validate"))

    # --- render ---
    sp = subparsers.add_parser(
        "render",
        help=(
            "Render a pack to --output via the F-build pipeline "
            "(byte-identical to `make build`)."
        ),
    )
    sp.add_argument("pack_path", help="Path to a pack directory.")
    sp.add_argument("--output", required=True)
    sp.add_argument(
        "--target",
        help=(
            "Optional adapter target (claude-code, kiro-ide, kiro-cli, "
            "kiro (deprecated → kiro-ide), copilot, codex); "
            "underscore form also accepted (claude_code); default: all."
        ),
    )
    sp.add_argument(
        "--self-host",
        action="store_true",
        help=(
            "Treat --output as an adopter root: honour Tier-2 paths (write "
            ".upstream.<ext> companions on collision rather than overwriting). "
            "Requires a .agentbundle-state.toml at --output. Default: off "
            "(wholesale rewrite, matching `make build` dist/ semantics)."
        ),
    )
    sp.set_defaults(func=_lazy("render"))

    # --- adapt ---
    sp = subparsers.add_parser(
        "adapt",
        help="Resolve <adapt:NAME> markers in projected files; report .upstream.* companions.",
    )
    sp.add_argument("--values-from", help="TOML file with marker values.")
    sp.add_argument("--ci", action="store_true",
                    help="Exit non-zero if any .upstream.<ext> companion remains on disk.")
    sp.add_argument("--root", default=".")
    sp.set_defaults(func=_lazy("adapt"))

    # --- diff --- (--scope disambiguator)
    sp = subparsers.add_parser(
        "diff",
        help="Diff the on-disk projection against a fresh render; non-zero on drift.",
    )
    sp.add_argument("pack_path", help="Path to the pack to diff against.")
    sp.add_argument("--root", default=".")
    sp.add_argument("--scope", choices=("repo", "user"))
    sp.add_argument(
        "--adapter",
        choices=_shipped_adapters_choices(),
        help=(
            "Disambiguate when the pack is installed for multiple adapters at "
            "the resolved scope (RFC-0052). Inferred when the pack has a single "
            "adapter row; required when it has more than one."
        ),
    )
    sp.set_defaults(func=_lazy("diff"))

    # --- upgrade --- (--scope disambiguator)
    sp = subparsers.add_parser(
        "upgrade",
        help="Upgrade a pack or a single primitive within a pack.",
    )
    # --pack and --all are mutually exclusive; exactly one is required (AC1).
    mode_group = sp.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--pack",
        help="Upgrade a single named pack (whole-pack or per-primitive).",
    )
    mode_group.add_argument(
        "--all",
        action="store_true",
        dest="all",
        default=False,
        help=(
            "Upgrade all installed packs at the given --scope. "
            "Requires --scope repo|user. Rejects --adapter and positional "
            "<catalogue>. Uses each row's recorded provenance for source "
            "resolution."
        ),
    )
    # The five per-primitive flags are mutually exclusive: a pack-version
    # upgrade is for the whole pack or exactly one named primitive, never two
    # at once. Grouping them lets argparse reject `--skill a --agent b` rather
    # than silently upgrading only the first.
    prim_group = sp.add_mutually_exclusive_group()
    prim_group.add_argument("--skill")
    prim_group.add_argument("--agent")
    prim_group.add_argument("--hook")
    prim_group.add_argument("--seed")
    prim_group.add_argument("--command")
    sp.add_argument(
        "catalogue",
        nargs="?",
        default=None,
        help=(
            "Catalogue URI to fetch the new version from. Optional: when "
            "omitted, the source is resolved from your config, an editable "
            "clone, or the packaged default (RFC-0046). Rejected with --all."
        ),
    )
    sp.add_argument("--root", default=".")
    sp.add_argument("--scope", choices=("repo", "user"))
    sp.add_argument(
        "--adapter",
        choices=_shipped_adapters_choices(),
        help=(
            "Disambiguate when the pack is installed for multiple adapters at "
            "the resolved scope (RFC-0052). Inferred when the pack has a single "
            "adapter row; required when it has more than one. Rejected with --all."
        ),
    )
    sp.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help=(
            "Output format. 'table' (default) prints a human-readable plan "
            "table. 'json' emits a machine-readable JSON document to stdout "
            "(requires --yes for non-dry-run applies; not yet supported with "
            "--pack)."
        ),
    )
    sp.add_argument(
        "--yes",
        action="store_true",
        help=(
            "Skip the upgrade confirmation prompt. Required for non-interactive "
            "use (CI, pipes); without it the upgrade asks before writing, and "
            "refuses rather than blocking when stdin is not a TTY. Required for "
            "--format json with --all (non-dry-run)."
        ),
    )
    sp.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Preview the per-file plan (action + tier + target path) without "
            "writing anything — no projected file, companion, or state change. "
            "Exits 0 on a successful preview, even with Tier-2 collisions present."
        ),
    )
    sp.set_defaults(func=_lazy("upgrade"))

    # --- uninstall --- (--scope disambiguator)
    sp = subparsers.add_parser(
        "uninstall",
        help="Uninstall a pack; remove Tier-1 files; preserve Tier-2 and Tier-3.",
    )
    sp.add_argument("--pack", required=True)
    sp.add_argument("--root", default=".")
    sp.add_argument("--scope", choices=("repo", "user"))
    sp.add_argument(
        "--adapter",
        choices=_shipped_adapters_choices(),
        help=(
            "Disambiguate when the pack is installed for multiple adapters at "
            "the resolved scope (RFC-0052). Inferred when the pack has a single "
            "adapter row; required when it has more than one. Only the named "
            "adapter row is uninstalled; shared files survive while a sibling "
            "row still owns them."
        ),
    )
    sp.add_argument(
        "--yes",
        action="store_true",
        help=(
            "Skip the uninstall confirmation prompt. Required for non-interactive "
            "use (CI, pipes); without it the uninstall asks before removing any "
            "file, and refuses rather than blocking when stdin is not a TTY."
        ),
    )
    sp.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Preview the per-file plan (remove tier-1 / keep tier-2) without "
            "removing anything — no file removed, no hook-wiring unproject, no "
            "state change. Exits 0."
        ),
    )
    sp.set_defaults(func=_lazy("uninstall"))

    # --- init-state --- (--scope selector; --migrate flag)
    sp = subparsers.add_parser(
        "init-state",
        help="Hash an existing projection into .agentbundle-state.toml.",
    )
    # `--pack` is required for the hash-from-projection mode but not for
    # `--migrate` (which is a whole-file rewrite); the handler enforces
    # the relationship instead of argparse.
    sp.add_argument("--pack")
    sp.add_argument("--packs-dir", default="packs")
    sp.add_argument("--root", default=".")
    sp.add_argument(
        "--migrate",
        action="store_true",
        help="Rewrite a v0.1 state file to v0.2 (RFC-0004). Idempotent.",
    )
    sp.add_argument("--scope", choices=("repo", "user"))
    sp.set_defaults(func=_lazy("init_state"))

    # --- config --- (post-pip-install user-scope settings)
    sp = subparsers.add_parser(
        "config",
        help="Get or set adapter-scoped user settings.",
        epilog=(
            "User-config overrides scope.DEFAULT_ADAPTER on fresh "
            "installs. CLI flags (e.g. install --adapter) and existing "
            "install state still take precedence."
        ),
    )
    sp.add_argument(
        "config_action",
        choices=("get", "set", "unset", "path"),
        help="Action: get / set / unset / path.",
    )
    sp.add_argument("key", nargs="?", help="Setting key (e.g. adapter).")
    sp.add_argument(
        "value", nargs="?", help="Setting value (set only)."
    )
    sp.set_defaults(func=_lazy("config"))

    # --- reconcile --- (read-only orphan reporter, RFC-0005 / T9)
    # No --apply flag — the subcommand is report-only by design.
    # `argparse`'s default "unrecognized argument" rejects --apply.
    sp = subparsers.add_parser(
        "reconcile",
        help=(
            "RFC-0005: read-only orphan reporter — walks Claude Code "
            "settings.json and Kiro agent JSONs named in user-scope state, "
            "reports entries the file/state pair disagrees on. Read-only; "
            "no --apply flag. User-scope only; no --scope flag."
        ),
    )
    sp.set_defaults(func=_lazy("reconcile"))

    # --- package-catalogue --- (maintainer/CI only; RFC-0072 D1/D5)
    sp = subparsers.add_parser(
        "package-catalogue",
        help=(
            "Package a catalogue repository into an Artifactory artifact layout "
            "(maintainer/CI only)."
        ),
    )
    sp.add_argument("--root", required=True, help="Catalogue repository root directory.")
    sp.add_argument("--bundle", required=True, help="Bundle name (e.g. engineering).")
    sp.add_argument("--release", required=True, help="Release tag (e.g. 0.13.0).")
    sp.add_argument("--channel", required=True, help="Channel name (e.g. stable).")
    sp.add_argument("--output", required=True, help="Output root directory.")
    sp.add_argument(
        "--source-revision",
        default=None,
        help="Git commit or tag (CI supplies this; no git shell-out).",
    )
    sp.add_argument(
        "--minimum-agentbundle-version",
        default=None,
        help="Minimum agentbundle version for the channel descriptor.",
    )
    sp.add_argument(
        "--published-at",
        default=None,
        help="Publication timestamp for the channel descriptor (ISO-8601).",
    )
    sp.set_defaults(func=_lazy("package_catalogue"))

    # --- catalogue <sub> --- (Wave 2-4; lint/sync-defaults/build/self-host/init implemented)
    cat_parser = subparsers.add_parser(
        "catalogue",
        help="Portable catalogue engine commands.",
    )
    cat_subs = cat_parser.add_subparsers(dest="catalogue_sub", metavar="<sub>")

    # catalogue lint
    _lint_p = cat_subs.add_parser(
        "lint",
        help=(
            "Lint catalogue packs (profiles, seeds, first-value contract, "
            "credentialed-skill conventions)."
        ),
    )
    _lint_p.add_argument("--root", default=".", help="Catalogue root directory.")
    _lint_p.add_argument("--pack", default=None, help="Limit to a single pack name.")
    _lint_p.add_argument(
        "--format", choices=("table", "json"), default="table", help="Output format."
    )
    _lint_p.add_argument(
        "--deep",
        action="store_true",
        default=False,
        help=(
            "Run full agentskills.io spec-compliance lint "
            "(requires PyYAML: pip install 'agentbundle[lint]')."
        ),
    )
    _lint_p.set_defaults(func=_lazy("catalogue_lint"))

    # catalogue verify
    _ver_p = cat_subs.add_parser(
        "verify",
        help=(
            "Verify catalogue against contracts (18-step pipeline, including "
            "agent-artifact lint and plugin manifest validation)."
        ),
    )
    _ver_p.add_argument("--root", default=".", help="Catalogue root directory.")
    _ver_p.add_argument("--pack", default=None, help="Limit to a single pack name.")
    _ver_p.add_argument(
        "--archive",
        default=None,
        help="Verify a packaged .tar.gz archive instead of source tree.",
    )
    _ver_p.add_argument(
        "--sha256-file",
        default=None,
        dest="sha256_file",
        help="SHA-256 sidecar file for archive verification.",
    )
    _ver_p.add_argument(
        "--format", choices=("table", "json"), default="table", help="Output format."
    )
    _ver_p.set_defaults(func=_lazy("catalogue_verify"))

    # catalogue build
    _build_p = cat_subs.add_parser("build", help="Build catalogue dist tree.")
    _build_p.add_argument("--root", default=".", help="Catalogue root directory.")
    _build_p.add_argument(
        "--output", default=None, help="Output directory (overrides catalogue.toml)."
    )
    _build_p.add_argument("--pack", default=None, help="Limit to a single pack name.")
    _build_p.add_argument("--recipe", default=None, help="Recipe name or .toml path.")
    _build_p.add_argument(
        "--format", choices=("table", "json"), default="table", help="Output format."
    )
    _build_p.set_defaults(func=_lazy("catalogue_build"))

    # catalogue self-host
    _sh_p = cat_subs.add_parser("self-host", help="Manage self-host projection.")
    _sh_p.add_argument("--root", default=".", help="Catalogue root directory.")
    _sh_excl = _sh_p.add_mutually_exclusive_group()
    _sh_excl.add_argument(
        "--check", action="store_true", default=False, help="Dry-run check (read-only)."
    )
    _sh_excl.add_argument(
        "--write", action="store_true", default=False, help="Write self-host projection."
    )
    _sh_p.add_argument(
        "--force", action="store_true", default=False, help="Force write even on dirty tree."
    )
    _sh_p.add_argument(
        "--windows",
        action="store_true",
        default=False,
        help=(
            "With --check: run the Windows-portability compat suite instead of the "
            "standard drift-only check. Drives the bundler build, self-host drift "
            "gates, and the path-sensitive pytest suite used in the Windows CI job. "
            "Rejected without --check."
        ),
    )
    _sh_p.add_argument(
        "--format", choices=("table", "json"), default="table", help="Output format."
    )
    _sh_p.set_defaults(func=_lazy("catalogue_self_host"))

    # catalogue package
    _pkg_p = cat_subs.add_parser("package", help="Package catalogue into a distributable archive.")
    _pkg_p.add_argument("--root", default=".", help="Catalogue root directory.")
    _pkg_p.add_argument("--bundle", required=True, help="Bundle/product identifier.")
    _pkg_p.add_argument("--release", required=True, help="Release version string.")
    _pkg_p.add_argument("--channel", required=True, help="Channel name (e.g. 'stable').")
    _pkg_p.add_argument("--output", required=True, help="Output directory for Artifactory layout.")
    _pkg_p.add_argument(
        "--source-revision", default=None, dest="source_revision", help="VCS revision."
    )
    _pkg_p.add_argument(
        "--minimum-agentbundle-version",
        default=None,
        dest="minimum_agentbundle_version",
        help="Minimum agentbundle version required.",
    )
    _pkg_p.add_argument(
        "--published-at",
        default=None,
        dest="published_at",
        help="Published-at timestamp (ISO-8601).",
    )
    _pkg_p.add_argument(
        "--flavor",
        choices=("runtime", "source"),
        default="runtime",
        help=(
            "Package flavor. 'runtime' (default): standard distributable runtime archive. "
            "'source': source distribution for self-hosted enterprise catalogues — includes "
            "catalogue.toml, packs/, profiles/, and guides/_shared/; produces a "
            "self-hosted-source-manifest.json alongside the archive."
        ),
    )
    _pkg_p.set_defaults(func=_lazy("catalogue_package"))

    # catalogue sync-defaults
    _sd_p = cat_subs.add_parser("sync-defaults", help="Sync install-defaults from catalogue.toml.")
    _sd_p.add_argument("--root", default=".", help="Catalogue root directory.")
    _sd_excl = _sd_p.add_mutually_exclusive_group()
    _sd_excl.add_argument(
        "--check", action="store_true", default=False, help="Check for drift (read-only)."
    )
    _sd_excl.add_argument(
        "--write",
        action="store_true",
        default=False,
        help="Regenerate install-defaults.toml.",
    )
    _sd_p.set_defaults(func=_lazy("catalogue_sync_defaults"))

    # catalogue init
    _init_p = cat_subs.add_parser(
        "init",
        help="Initialize a new catalogue directory with scaffold files.",
    )
    _init_p.add_argument(
        "target",
        nargs="?",
        default=".",
        help=(
            "Target directory to initialize. Created if it does not exist. "
            "Defaults to the current directory."
        ),
    )
    _init_p.add_argument(
        "--name",
        default=None,
        help=(
            "Catalogue name (letters, digits, hyphens, underscores; starts with "
            "letter or digit). Default: derived from the target directory basename."
        ),
    )
    _init_p.add_argument(
        "--display-name",
        default=None,
        dest="display_name",
        help="Human-readable catalogue name. Default: title-cased from --name.",
    )
    _init_p.add_argument(
        "--description",
        default=None,
        help="One-sentence catalogue description. Default: auto-generated from --name.",
    )
    _init_p.add_argument(
        "--owner-name",
        default=None,
        dest="owner_name",
        help="Catalogue owner name. Default: same as --display-name.",
    )
    _init_p.add_argument(
        "--preferred-adapter",
        default=None,
        dest="preferred_adapter",
        help=(
            "Preferred adapter identifier (e.g. claude-code, kiro-ide). "
            "Default: from install-defaults.toml, or 'claude-code'."
        ),
    )
    _init_p.add_argument(
        "--preset",
        choices=("self-hosted",),
        default=None,
        help=(
            "Initialization preset. 'self-hosted' creates an enterprise-derived catalogue "
            "from an existing source catalogue. Requires --source."
        ),
    )
    _init_p.add_argument(
        "--tooling",
        choices=("external", "vendored"),
        default=None,
        dest="tooling",
        help=(
            "Self-hosted tooling mode (requires --preset self-hosted). "
            "'external': catalogue-curation is installed repo-scope from PyPI/registry. "
            "'vendored': agentbundle source and curation are copied into the target."
        ),
    )
    _init_p.add_argument(
        "--source",
        default=None,
        help=(
            "Path to the source catalogue root (requires --preset self-hosted). "
            "The directory containing catalogue.toml, packs/, profiles/, etc."
        ),
    )
    _init_p.add_argument(
        "--adapter",
        action="append",
        dest="adapters",
        default=None,
        metavar="ADAPTER",
        help=(
            "Adapter to include (repeatable). Self-hosted preset only. "
            "Default: all adapters from the source catalogue."
        ),
    )
    _init_p.add_argument(
        "--pack",
        action="append",
        dest="packs",
        default=None,
        metavar="PACK",
        help=(
            "Pack to include in the target (repeatable). Self-hosted preset only. "
            "Default: all packs except catalogue-curation."
        ),
    )
    _init_p.add_argument(
        "--profile",
        action="append",
        dest="profiles",
        default=None,
        metavar="PROFILE",
        help=(
            "Profile to include in the target (repeatable). Self-hosted preset only. "
            "Default: all profiles from the source catalogue."
        ),
    )
    _init_p.add_argument(
        "--guides",
        choices=("none", "selected"),
        default=None,
        help=(
            "Guide inclusion mode (self-hosted preset only). "
            "'none': no guides copied. 'selected': guides/_shared/ copied."
        ),
    )
    _init_p.add_argument(
        "--attribution",
        choices=("white-label", "attributed"),
        default=None,
        help=(
            "Identity mode for the self-hosted catalogue. "
            "'white-label': zero upstream trace in the output. "
            "'attributed': upstream declared in designated attribution surfaces only."
        ),
    )
    _init_p.add_argument(
        "--repository-url",
        default=None,
        dest="repository_url",
        help="Repository URL for the self-hosted catalogue (e.g. https://example.com/my-catalogue).",
    )
    _init_p.add_argument(
        "--owner-email",
        default=None,
        dest="owner_email",
        help="Maintainer e-mail address for the self-hosted catalogue.",
    )
    _init_p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        dest="dry_run",
        help="Show what would be created without writing any files.",
    )
    _init_p.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format: table (default, human-readable) or json (machine-readable).",
    )
    _init_p.set_defaults(func=_lazy("catalogue_init"))

    # --- lint packs --- (Wave 2; implemented)
    lint_parser = subparsers.add_parser(
        "lint",
        help="Lint commands.",
    )
    lint_subs = lint_parser.add_subparsers(dest="lint_sub", metavar="<sub>")
    packs_p = lint_subs.add_parser(
        "packs",
        help="Lint catalogue packs (alias for 'agentbundle catalogue lint').",
    )
    packs_p.add_argument("--root", default=".", help="Catalogue root directory.")
    packs_p.add_argument("--pack", default=None, help="Limit to a single pack name.")
    packs_p.add_argument(
        "--format", choices=("table", "json"), default="table", help="Output format."
    )
    packs_p.add_argument(
        "--deep",
        action="store_true",
        default=False,
        help=(
            "Run full agentskills.io spec-compliance lint "
            "(requires PyYAML: pip install 'agentbundle[lint]')."
        ),
    )
    packs_p.set_defaults(func=_lazy("catalogue_lint"))

    # --- pack <sub> --- (pack evals run)
    pack_parser = subparsers.add_parser(
        "pack",
        help="Pack-level commands (evals, etc.).",
    )
    pack_subs = pack_parser.add_subparsers(dest="pack_sub", metavar="<sub>")

    pack_evals_p = pack_subs.add_parser("evals", help="Pack evaluation commands.")
    pack_evals_subs = pack_evals_p.add_subparsers(dest="pack_evals_sub", metavar="<sub>")

    evals_run_p = pack_evals_subs.add_parser(
        "run",
        help="Run Tier-A activation evals for a pack (report-only).",
    )
    evals_run_p.add_argument("--pack", required=True, help="Pack name under packs/.")
    evals_run_p.add_argument(
        "--catalogue-root", default=".", dest="catalogue_root",
        help="Catalogue repository root (default: current directory).",
    )
    evals_run_p.add_argument("--runs", type=int, default=3, help="Runs per query (default 3).")
    evals_run_p.add_argument(
        "--adapter", default="claude-code",
        help="Detector adapter (only claude-code ships in the first cut).",
    )
    evals_run_p.add_argument(
        "--timeout", type=int, default=180,
        help="Per-run wall-clock timeout in seconds (default 180).",
    )
    evals_run_p.add_argument(
        "--mode", choices=("headless", "in-harness", "judge"), default="headless",
        help="Eval mode: headless (default), in-harness, or judge.",
    )
    evals_run_p.add_argument(
        "--judge-adapter", default="claude-code", dest="judge_adapter",
        help="Judge backend (claude-code or codex). Use with --mode judge.",
    )
    evals_run_p.add_argument("--model", default=None, help="Model the judge uses.")
    evals_run_p.add_argument("--judge-config", default=None, dest="judge_config",
                              help="TOML file with [judge.<name>] backend definitions.")
    evals_run_p.add_argument("--artifacts", default=None,
                              help="JSON path for --mode judge.")
    evals_run_p.add_argument(
        "--check", choices=("activation", "behavior"), default="activation",
        help="In-harness check type: activation (default) or behavior.",
    )
    evals_run_p.add_argument("--prepare-workspace", default=None, dest="prepare_workspace",
                              metavar="SKILL/EVAL_ID",
                              help="Seed a per-eval working dir and print its path.")
    evals_run_p.add_argument("--reports", default=None,
                              help="JSON path for --mode in-harness.")
    evals_run_p.set_defaults(func=_lazy("pack_evals"))

    # --- pack-config --- (RFC-0074: per-pack configuration)
    pc_parser = subparsers.add_parser(
        "pack-config",
        help="Per-pack configuration (get, set, unset, show).",
    )
    pc_subs = pc_parser.add_subparsers(dest="pack_config_sub", metavar="<sub>")

    pc_get = pc_subs.add_parser("get", help="Print the effective value for a key.")
    pc_get.add_argument("pack", help="Pack name.")
    pc_get.add_argument("key", help="Configuration key.")
    pc_get.set_defaults(func=_lazy("pack_config_cmd"))

    pc_set = pc_subs.add_parser("set", help="Write a key to user config.toml.")
    pc_set.add_argument("pack", help="Pack name.")
    pc_set.add_argument("key", help="Configuration key.")
    pc_set.add_argument("value", help="Value to set.")
    pc_set.set_defaults(func=_lazy("pack_config_cmd"))

    pc_unset = pc_subs.add_parser("unset", help="Remove a key from user config.toml.")
    pc_unset.add_argument("pack", help="Pack name.")
    pc_unset.add_argument("key", help="Configuration key.")
    pc_unset.set_defaults(func=_lazy("pack_config_cmd"))

    pc_show = pc_subs.add_parser(
        "show", help="Show all keys with (baked default) / (user override) labels."
    )
    pc_show.add_argument("pack", help="Pack name.")
    pc_show.set_defaults(func=_lazy("pack_config_cmd"))

    pc_parser.set_defaults(func=_lazy("pack_config_cmd"))

    # --- oplog --- (RFC-0074: operation log)
    ol_parser = subparsers.add_parser(
        "oplog",
        help="Pack operation log (show, clear).",
    )
    ol_subs = ol_parser.add_subparsers(dest="oplog_sub", metavar="<sub>")

    ol_show = ol_subs.add_parser(
        "show", help="Print the last 50 entries from a pack's ops.jsonl."
    )
    ol_show.add_argument("pack", help="Pack name.")
    ol_show.add_argument(
        "--since",
        default=None,
        help="ISO-8601 timestamp; only entries at or after this time are printed.",
    )
    ol_show.set_defaults(func=_lazy("oplog_cmd"))

    ol_clear = ol_subs.add_parser("clear", help="Truncate a pack's ops.jsonl.")
    ol_clear.add_argument("pack", help="Pack name.")
    ol_clear.add_argument(
        "--yes",
        action="store_true",
        default=False,
        help="Required: confirm you want to clear the log.",
    )
    ol_clear.set_defaults(func=_lazy("oplog_cmd"))

    ol_parser.set_defaults(func=_lazy("oplog_cmd"))

    return parser


def _lazy(module_name: str):
    """Lazy import of `agentbundle.commands.<module_name>:run`.

    Lets `agentbundle --version` and `--help` run before any command module
    is imported — important because some command modules (e.g. `install`)
    pull in `urllib.request`, `tarfile`, etc. that we don't want loaded for
    a `--version` print. Also keeps unit-test import paths cheap.
    """

    def _runner(args: argparse.Namespace) -> int:
        import importlib

        mod = importlib.import_module(f"agentbundle.commands.{module_name}")
        return int(mod.run(args))

    return _runner


def _normalise_path_separators(args: argparse.Namespace) -> None:
    """Rewrite backslashes to forward slashes on path-bearing
    string attributes of the parsed namespace.

    Done at the CLI boundary so a Windows operator typing
    `agentbundle scaffold --output=packs\\core\\seeds` lands in the
    same place as `--output=packs/core/seeds`. The path-jail check
    and the Windows reserved-name guard both run on the normalised
    form, so the two inputs share a single code path inside the CLI.

    Only attribute names listed in `_PATH_BEARING_ATTRS` are touched —
    that keeps a future content-string flag (regex, message body) from
    being silently mangled. URI-shaped values (`git+https://…`) are
    detected by `://` and left alone even when their attribute is in
    the allow-list, because the same flag (`catalogue`) accepts both
    local paths and URIs.
    """
    for key in _PATH_BEARING_ATTRS:
        value = getattr(args, key, None)
        if not isinstance(value, str):
            continue
        if "\\" not in value:
            continue
        if "://" in value:
            continue
        setattr(args, key, value.replace("\\", "/"))


def main(argv: Sequence[str] | None = None) -> int:
    # Windows cp1252 consoles can't represent non-ASCII chars (⚠, →, etc.).
    # Reconfigure to UTF-8 with backslash-escape fallback so the process
    # never crashes on non-ASCII output regardless of console code page.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    _normalise_path_separators(args)
    # Load the user-scope config once at dispatch start and attach to
    # `args._user_config`. Handlers that consume it read
    # `getattr(args, "_user_config", None)` — see install.run / upgrade.run.
    # `load_user_config()` is fail-soft (T1 contract): a malformed
    # file emits a stderr warning and returns UserConfig(adapter=None)
    # without raising, so `--help`, `config path`, and `config unset`
    # all keep working when the file is broken.
    from agentbundle.user_config import load_user_config

    args._user_config = load_user_config()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
