"""`agentbundle validate` subcommand.

Validates a pack directory's ``pack.toml`` against ``pack.schema.json``,
enforces the six-recipe enumeration, and applies the spec-version gate.
With ``--strict``, runs conformance fixtures via the F-build render
pipeline when they are present; warns and exits 0 when absent (v1 ship
state — F-conformance deferred to v1.1 per RFC-0003).

Exit codes:
  0 — pack is schema-valid (and conformance fixtures pass if --strict).
  1 — any schema error, unknown recipe, version mismatch, or conformance
      failure; one-line stderr reason printed for each failure.

Usage (wired by cli.py):
    args.pack_path  — path to a pack directory containing pack.toml.
    args.strict     — bool; run conformance fixtures when present.
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

from agentbundle.commands._common import check_spec_version_gate

# Stdlib only — no third-party deps.

# Six-recipe enumerated set from the sibling distribution-adapters spec.
VALID_RECIPES: frozenset[str] = frozenset(
    {
        "per-pack-claude-plugin",
        "per-pack-apm-package",
        "marketplace",
        "per-pack-overlay",
        "composite-agents-md",
        "composite-marketplace",
    }
)

# Location of pack.schema.json relative to the repo root.  The schema is
# bundled in docs/contracts/ and is also bundled at
# agentbundle/_data/pack.schema.json for zipapp use.
_HERE = Path(__file__).resolve().parent


def _schema_path() -> Path:
    """Locate pack.schema.json — bundled copy preferred, dev fallback."""
    bundled = _HERE.parent / "_data" / "pack.schema.json"
    if bundled.exists():
        return bundled
    # Dev fallback: walk up from agentbundle/ package to repo root.
    repo_root = _HERE.parent.parent.parent.parent
    return repo_root / "docs" / "contracts" / "pack.schema.json"


def _conformance_fixtures_dir() -> Path:
    """Return the expected path for conformance fixtures."""
    # packages/agentbundle/tests/fixtures/conformance/
    pkg_root = _HERE.parent.parent.parent
    return pkg_root / "tests" / "fixtures" / "conformance"


def run(args) -> int:
    """Entry point called by the CLI dispatcher. Returns exit code."""
    pack_path = Path(args.pack_path)
    strict: bool = getattr(args, "strict", False)

    # ── 1. Locate and load pack.toml ──────────────────────────────────────
    pack_toml_path = pack_path / "pack.toml"
    if not pack_toml_path.exists():
        print(
            f"validate: pack.toml not found at {pack_toml_path}",
            file=sys.stderr,
        )
        return 1

    try:
        raw_toml = pack_toml_path.read_text(encoding="utf-8")
        pack_data = tomllib.loads(raw_toml)
    except tomllib.TOMLDecodeError as exc:
        print(
            f"validate: pack.toml is not valid TOML: {exc}",
            file=sys.stderr,
        )
        return 1

    # ── 2. Spec-version gate ──────────────────────────────────────────────
    gate = check_spec_version_gate(pack_data)
    if gate is not None:
        return gate

    # ── 3. Schema validation ──────────────────────────────────────────────
    schema_path = _schema_path()
    if not schema_path.exists():
        print(
            f"validate: pack.schema.json not found at {schema_path}",
            file=sys.stderr,
        )
        return 1

    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    # Import validate_instance from F-build (library-first).
    from agentbundle.build.validate import validate as validate_instance

    errors = validate_instance(pack_data, schema)
    if errors:
        # RFC-0004 § *Install-scope dimension* names a specific stderr
        # text for the cross-field invariant: `pack <name>: default-scope
        # '<requested>' not in allowed-scopes <declared-set>`. The
        # schema's `contains` failure on `$.pack.install.allowed-scopes`
        # is the structural form of that violation; surface it with the
        # spec-named text instead of the generic schema message so
        # adopters get the actionable line.
        if _is_default_scope_invariant_violation(pack_data, errors[0]):
            pack_name = pack_data.get("pack", {}).get("name", pack_path.name)
            install = pack_data.get("pack", {}).get("install", {})
            requested = install.get("default-scope")
            allowed = install.get("allowed-scopes", [])
            print(
                f"validate: pack {pack_name}: default-scope {requested!r} "
                f"not in allowed-scopes {allowed}",
                file=sys.stderr,
            )
            return 1
        # One-line stderr: first error only (spec says "one-line reason").
        print(
            f"validate: schema error — {errors[0]}",
            file=sys.stderr,
        )
        return 1

    # ── 4. Recipe gate ────────────────────────────────────────────────────
    recipes = _extract_recipes(pack_data)
    for recipe in recipes:
        if recipe not in VALID_RECIPES:
            print(
                f"validate: unknown recipe {recipe!r}; "
                f"valid recipes are {sorted(VALID_RECIPES)}",
                file=sys.stderr,
            )
            return 1

    # ── 4b. User-scope refusal rails (RFC-0004 A/B/C) ─────────────────────
    # Rails fire only when the pack declares "user" ∈ allowed-scopes. The
    # rails run *after* schema validation so we know `[pack.install]`'s
    # shape (when present) is well-formed before we read it. v0.1 packs
    # have implied `allowed-scopes = ["repo"]`, so the rails are
    # vacuously satisfied — `_allowed_scopes` returns `["repo"]` for
    # them.
    from agentbundle.build.scope_rails import run_all as run_scope_rails

    allowed = _allowed_scopes(pack_data)
    user_scope_hooks = _user_scope_hooks_opt_in(pack_data)
    rail_refusal = run_scope_rails(pack_path, allowed, user_scope_hooks)
    if rail_refusal is not None:
        pack_name = (
            pack_data.get("pack", {}).get("name") or pack_path.name
        )
        print(
            f"validate: {pack_name}: {rail_refusal}",
            file=sys.stderr,
        )
        return 1

    # ── 4c. Kiro hook-wiring `attach-to-agent` rail (RFC-0005, T2) ────────
    # Fires when the pack is v0.3-bound AND ships *both* `.apm/agents/`
    # (Kiro requires an agent to attach to) AND `.apm/hook-wiring/`
    # (the wiring being validated). Pack-side `allowed-adapters` is a
    # future RFC; the both-dirs heuristic is the proxy for "this pack
    # would project to kiro." A Claude-Code-only v0.3 pack that ships
    # wiring but no agents has no kiro projection target — the rail is
    # a no-op for it (AC6: "field is ignored, not refused").
    from agentbundle.build.scope_rails import (
        check_kiro_event_vocabulary,
        check_kiro_wiring,
    )

    target_adapters = _kiro_target_adapters(pack_data, pack_path)
    pack_name = pack_data.get("pack", {}).get("name") or pack_path.name
    kiro_refusal = check_kiro_wiring(pack_path, pack_name, target_adapters)
    if kiro_refusal is not None:
        print(f"validate: {kiro_refusal}", file=sys.stderr)
        return 1

    # ── 4d. Kiro per-adapter event-vocabulary rail (RFC-0005, T6) ─────────
    # AC17 / AC17b: a wiring TOML naming an event outside the resolved
    # target adapter's `agent-event-vocabulary` is refused. Claude Code's
    # projection declares no vocabulary, so its packs pass through;
    # Kiro's vocabulary is loaded from the v0.3 adapter contract.
    if "kiro" in target_adapters:
        kiro_vocab = _kiro_event_vocabulary()
        kiro_wiring_tomls = _load_pack_wiring_tomls(pack_path)
        vocab_refusal = check_kiro_event_vocabulary(
            pack_name=pack_name,
            wiring_tomls=kiro_wiring_tomls,
            vocabulary=kiro_vocab,
            target_adapters=target_adapters,
            adapter_name="kiro",
        )
        if vocab_refusal is not None:
            print(f"validate: {vocab_refusal}", file=sys.stderr)
            return 1

    # ── 4e. kiro-ide-hook validate rail (RFC-0005 v0.4, T-C2) ────────────
    # Fires whenever the pack ships `.apm/kiro-ide-hooks/` content. The
    # rail's `target_adapters` heuristic differs from `_kiro_target_adapters`
    # — kiro-ide-hook needs no agent (file-event triggers fire
    # independent of agent runtime; cf. § Pack-side schema), so a
    # pack with kiro-ide-hooks but no `.apm/agents/` still targets
    # kiro. Cheapest heuristic: presence of the source directory with
    # at least one *.kiro.hook file.
    if _dir_has_any_kiro_ide_hook(pack_path / ".apm" / "kiro-ide-hooks"):
        from agentbundle.build.scope_rails import check_kiro_ide_hook

        ide_event_vocab, ide_action_vocab = _kiro_ide_hook_vocabularies()
        ide_hook_refusal = check_kiro_ide_hook(
            pack_path=pack_path,
            pack_name=pack_name,
            target_adapters=("kiro",),
            ide_event_vocabulary=ide_event_vocab,
            ide_action_vocabulary=ide_action_vocab,
        )
        if ide_hook_refusal is not None:
            print(f"validate: {ide_hook_refusal}", file=sys.stderr)
            return 1

    # ── 5. Strict / conformance mode ─────────────────────────────────────
    if strict:
        conformance_dir = _conformance_fixtures_dir()
        if not conformance_dir.exists():
            print(
                "--strict conformance fixtures not present — skipping",
                file=sys.stderr,
            )
            # Exit 0 on schema portion (v1 carve-out).
            return 0
        # Conformance fixtures present — run them.
        rc = _run_conformance(pack_path, conformance_dir)
        if rc != 0:
            return rc

    return 0


def _is_default_scope_invariant_violation(pack_data: dict, first_error: str) -> bool:
    """Return True when the first schema error is the cross-field invariant.

    The schema's `if`/`then` block for `default-scope ∈ allowed-scopes`
    surfaces as a `contains` failure on `$.pack.install.allowed-scopes`.
    We also confirm the pack actually has the shape that triggered the
    error (default-scope declared, allowed-scopes declared, default not
    in allowed) so we don't mis-attribute an unrelated `contains`
    failure to this rule.
    """
    install = pack_data.get("pack", {}).get("install")
    if not isinstance(install, dict):
        return False
    default = install.get("default-scope")
    allowed = install.get("allowed-scopes")
    if not isinstance(default, str) or not isinstance(allowed, list):
        return False
    if default in allowed:
        return False
    # Match the validator's error path heuristically.
    return (
        "pack.install.allowed-scopes" in first_error
        or "allowed-scopes" in first_error
    )


def _user_scope_hooks_opt_in(pack_data: dict) -> bool:
    """Return True iff the pack declares ``[pack.install] user-scope-hooks = true``.

    RFC-0005 § Rail B — user-scope lift: the flag is the consent
    gesture that lets a pack ship hook-shaped primitives at user scope.
    Absent or non-boolean → False (rail still refuses the pack).
    """
    pack = pack_data.get("pack", {})
    if not isinstance(pack, dict):
        return False
    install = pack.get("install", {})
    if not isinstance(install, dict):
        return False
    flag = install.get("user-scope-hooks")
    return flag is True


def _kiro_event_vocabulary() -> list[str] | None:
    """Resolve Kiro's ``agent-event-vocabulary`` from the v0.3 contract.

    Returns the list when the contract declares it (the post-T1 v0.3
    state); returns None when the field is absent (the rail is then a
    no-op per AC17b). Looked up on every call to keep the
    contract-file the source of truth — no module-level cache so a
    test-time contract swap is visible.
    """
    from agentbundle.build.contract import load as load_contract

    here = Path(__file__).resolve().parent
    bundled = here.parent / "_data" / "adapter.toml"
    if bundled.exists():
        contract_path = bundled
    else:
        # Dev-checkout fallback: the package lives at
        # packages/agentbundle/agentbundle/commands/, so four `.parent`
        # hops land at the repo root. Installed layouts (site-packages
        # via pip) will always have the bundled `_data/adapter.toml`
        # above, so this branch only fires when running from a working
        # tree that excludes the bundle. Returning None on miss keeps
        # the rail a no-op rather than crashing.
        contract_path = here.parent.parent.parent.parent / "docs" / "contracts" / "adapter.toml"
        if not contract_path.exists():
            return None
    contract = load_contract(contract_path)
    kiro = contract.get("adapter", {}).get("kiro", {})
    projections = kiro.get("projections", {}) if isinstance(kiro, dict) else {}
    hook_wiring = projections.get("hook-wiring", {}) if isinstance(projections, dict) else {}
    vocab = hook_wiring.get("agent-event-vocabulary") if isinstance(hook_wiring, dict) else None
    if isinstance(vocab, list):
        return [str(v) for v in vocab if isinstance(v, str)]
    return None


def _load_pack_wiring_tomls(pack_path: Path) -> dict[str, dict]:
    """Parse every ``.apm/hook-wiring/*.toml`` under *pack_path*.

    Mirrors the in-memory shape ``check_kiro_event_vocabulary``
    consumes. A malformed wiring TOML would already have been refused
    by ``check_kiro_wiring`` earlier in the validate pipeline, so this
    helper silently skips parse errors.
    """
    import tomllib

    out: dict[str, dict] = {}
    wiring_dir = pack_path / ".apm" / "hook-wiring"
    if not wiring_dir.exists():
        return out
    for entry in sorted(wiring_dir.iterdir()):
        if not entry.is_file() or entry.suffix != ".toml":
            continue
        try:
            out[entry.stem] = tomllib.loads(entry.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError):
            continue
    return out


def _kiro_target_adapters(pack_data: dict, pack_path: Path) -> set[str]:
    """Resolve the target-adapter set for the kiro hook-wiring rail (T2).

    Pack-side ``allowed-adapters`` does not exist yet (a future RFC).
    The rail's purpose is to refuse hook-wiring that *would* project to
    kiro but lacks the required ``attach-to-agent`` field. Without an
    explicit declaration, we infer kiro-targeting from on-disk evidence:

      - Pack declares the v0.3 adapter contract (the version that
        introduced ``merge-into-agent-json`` for kiro hook-wiring).
      - Pack ships **both** ``.apm/agents/`` content (Kiro's projection
        target — an agent JSON to attach into) **and**
        ``.apm/hook-wiring/`` content (the wiring this rail validates).

    A Claude-Code-only v0.3 pack that ships wiring without agents
    cannot project to kiro by construction (no agent file to merge
    into) and the rail is a no-op for it. v0.1 / v0.2 packs pre-date
    the requirement.

    Returns ``{"kiro"}`` when the heuristic fires; empty set
    (rail no-op) otherwise.
    """
    pack = pack_data.get("pack", {})
    if not isinstance(pack, dict):
        return set()
    contract = pack.get("adapter-contract")
    if not isinstance(contract, dict):
        return set()
    if contract.get("version") != "0.3":
        return set()
    # Heuristic: kiro projection requires a same-pack agent. A pack
    # with wiring but no agents has nothing to attach to.
    agents_dir = pack_path / ".apm" / "agents"
    wiring_dir = pack_path / ".apm" / "hook-wiring"
    if not _dir_has_any_file(agents_dir, ".md"):
        return set()
    if not _dir_has_any_file(wiring_dir, ".toml"):
        return set()
    return {"kiro"}


def _dir_has_any_file(directory: Path, suffix: str) -> bool:
    """Return True if *directory* exists and contains at least one file
    with *suffix*. Symlinks are ignored — the kiro rail consumes them
    through `check_kiro_wiring`, which mirrors rail C's symlink refusal."""
    if not directory.exists():
        return False
    for entry in directory.iterdir():
        if entry.is_file() and entry.suffix == suffix:
            return True
    return False


def _dir_has_any_kiro_ide_hook(directory: Path) -> bool:
    """``.kiro.hook`` is a compound extension; ``Path.suffix`` only
    returns ``.hook``, so the generic helper above misses it. A
    dedicated check keeps the call site readable and pins the
    compound-extension assumption in one place."""
    if not directory.exists():
        return False
    for entry in directory.iterdir():
        if entry.is_file() and entry.name.endswith(".kiro.hook"):
            return True
    return False


def _kiro_ide_hook_vocabularies() -> tuple[list[str] | None, list[str] | None]:
    """Resolve the kiro adapter's ``ide-event-vocabulary`` and
    ``ide-action-vocabulary`` from the bundled contract.

    Returns (None, None) when the contract pre-dates v0.4 (the
    ``[adapter.kiro.projections.kiro-ide-hook]`` table doesn't exist),
    which makes checks 2 and 3 of the validate rail no-ops — the
    rail's checks 1 / 4 / 5 (required fields, malformed placeholder,
    unresolvable placeholder) still fire because they're vocabulary-
    independent.

    Same load-at-call-time discipline as ``_kiro_event_vocabulary`` —
    the contract file is the source of truth; no module-level cache
    so a test-time swap is visible immediately.
    """
    from agentbundle.build.contract import load as load_contract

    here = Path(__file__).resolve().parent
    bundled = here.parent / "_data" / "adapter.toml"
    if bundled.exists():
        contract_path = bundled
    else:
        contract_path = here.parent.parent.parent.parent / "docs" / "contracts" / "adapter.toml"
        if not contract_path.exists():
            return None, None
    contract = load_contract(contract_path)
    kiro = contract.get("adapter", {}).get("kiro", {})
    projections = kiro.get("projections", {}) if isinstance(kiro, dict) else {}
    rule = projections.get("kiro-ide-hook", {}) if isinstance(projections, dict) else {}

    def _as_string_list(value: object) -> list[str] | None:
        if isinstance(value, list):
            return [str(v) for v in value if isinstance(v, str)]
        return None

    return (
        _as_string_list(rule.get("ide-event-vocabulary")) if isinstance(rule, dict) else None,
        _as_string_list(rule.get("ide-action-vocabulary")) if isinstance(rule, dict) else None,
    )


def _allowed_scopes(pack_data: dict) -> list[str]:
    """Return the pack's resolved allowed-scopes list.

    Resolution mirrors RFC-0004 § *v0.1 vs v0.2 contract acceptance*:

      - v0.1 packs (declared version "0.1", or no `[pack.adapter-contract]`)
        get the implied `["repo"]`. Any stray `[pack.install]` table is
        ignored.
      - v0.2 packs read `[pack.install].allowed-scopes` when present; when
        only `default-scope` is declared, the implied default is
        `[default-scope]`.

    The cross-field `default-scope ∈ allowed-scopes` invariant is owned
    by the schema; we trust the schema's verdict here and only resolve
    the list.
    """
    pack = pack_data.get("pack", {})
    if not isinstance(pack, dict):
        return ["repo"]
    contract_version = (
        pack.get("adapter-contract", {}).get("version")
        if isinstance(pack.get("adapter-contract"), dict)
        else None
    )
    # v0.2 introduced `[pack.install]`; v0.3 added `user-scope-hooks`;
    # v0.6 added `allowed-adapters`. Treat any contract version >= 0.2
    # as carrying the install table. The legacy v0.1 path (and any pack
    # without an adapter-contract declaration) stays repo-only.
    if contract_version is None or contract_version == "0.1":
        return ["repo"]
    install = pack.get("install", {})
    if not isinstance(install, dict):
        return ["repo"]
    allowed = install.get("allowed-scopes")
    if isinstance(allowed, list) and allowed:
        return [s for s in allowed if isinstance(s, str)]
    default = install.get("default-scope")
    if isinstance(default, str):
        return [default]
    return ["repo"]


def _extract_recipes(pack_data: dict) -> list[str]:
    """Return the list of recipe names the pack declares, if any.

    The schema allows a pack to declare recipes at ``[pack].recipes``
    (a list of strings).  Returns an empty list if the field is absent or
    the pack table is missing.
    """
    pack_table = pack_data.get("pack", {})
    if not isinstance(pack_table, dict):
        return []
    recipes = pack_table.get("recipes", [])
    if not isinstance(recipes, list):
        return []
    return [str(r) for r in recipes if isinstance(r, str)]


def _run_conformance(pack_path: Path, conformance_dir: Path) -> int:
    """Run each conformance fixture and assert the expected output tree.

    Each fixture is a subdirectory under ``conformance_dir`` containing:
      - ``expected/``  — the expected rendered output tree.

    We call ``render.render_pack_to_dir`` and compare file trees.
    Returns 0 if all fixtures pass; 1 on first mismatch (with stderr).
    """
    import tempfile

    from agentbundle.render import render_pack_to_dir

    fixture_dirs = sorted(
        d for d in conformance_dir.iterdir() if d.is_dir()
    )
    if not fixture_dirs:
        print(
            "--strict: conformance directory present but empty — skipping",
            file=sys.stderr,
        )
        return 0

    for fixture in fixture_dirs:
        expected_dir = fixture / "expected"
        if not expected_dir.exists():
            print(
                f"--strict: fixture {fixture.name!r} has no expected/ tree; skipping",
                file=sys.stderr,
            )
            continue

        with tempfile.TemporaryDirectory() as raw:
            actual_dir = Path(raw)
            try:
                render_pack_to_dir(pack_path, actual_dir)
            except Exception as exc:
                print(
                    f"--strict: render failed for fixture {fixture.name!r}: {exc}",
                    file=sys.stderr,
                )
                return 1

            mismatch = _diff_trees(expected_dir, actual_dir)
            if mismatch:
                print(
                    f"--strict: conformance failure in fixture {fixture.name!r}: "
                    + mismatch,
                    file=sys.stderr,
                )
                return 1

    return 0


def _diff_trees(expected: Path, actual: Path) -> str:
    """Return a one-line description of the first difference, or '' if identical."""
    expected_files = _tree_files(expected)
    actual_files = _tree_files(actual)

    only_in_expected = expected_files.keys() - actual_files.keys()
    if only_in_expected:
        first = sorted(only_in_expected)[0]
        return f"file missing from actual: {first}"

    only_in_actual = actual_files.keys() - expected_files.keys()
    if only_in_actual:
        first = sorted(only_in_actual)[0]
        return f"unexpected file in actual: {first}"

    for relpath in sorted(expected_files):
        if expected_files[relpath] != actual_files[relpath]:
            return f"content differs: {relpath}"

    return ""


def _tree_files(root: Path) -> dict[str, bytes]:
    """Return all files under ``root`` as a dict of relpath → bytes."""
    out: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            relpath = path.relative_to(root).as_posix()
            out[relpath] = path.read_bytes()
    return out
