"""AC20, AC22, and AC30 — the publication gates around the hook compiler.

Each criterion names a specific artifact as its evidence, and each of those was
missing while the implementation it describes was already present. That gap is
the interesting one: `lint_packs.py` has dry-run the compiler since #916 and all
six `render_pack` consumers have existed since then, so nothing here is a new
capability — these are the assertions that stop the behaviour regressing
silently, which is what the criteria actually ask for.
"""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
from unittest import mock

from agentbundle.build.lint_packs import lint_pack

# The command surface AC20 partitions. Six derive the per-pack-claude-plugin
# recipe through `render_pack` and change by design; the rest must not.
PLUGIN_RECIPE_CONSUMERS = (
    "render",
    "install",
    "upgrade",
    "diff",
    "validate",
    "init_state",
)
COMMANDS_DIR = (
    Path(__file__).resolve().parents[3]
    / "agentbundle"
    / "agentbundle"
    / "commands"
)
BUILD_DIR = COMMANDS_DIR.parent / "build"


def _wiring_pack(
    root: Path,
    name: str,
    *,
    command: str,
    scopes: str = '["repo", "user"]',
) -> Path:
    """Build a pack shipping one hook body and one Claude-shaped wiring file."""
    pack = root / name
    (pack / ".apm" / "hooks").mkdir(parents=True)
    (pack / ".apm" / "hook-wiring").mkdir(parents=True)
    (pack / ".claude-plugin").mkdir(parents=True)
    (pack / ".apm" / "hooks" / "run.py").write_text("pass\n", encoding="utf-8")
    # `pack_is_publishable` — and therefore AC22's route-qualification — needs a
    # source manifest as well as a user-admitting scope.
    (pack / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": name, "version": "1.0.0"}), encoding="utf-8"
    )
    (pack / "pack.toml").write_text(
        f'[pack]\nname = "{name}"\nversion = "1.0.0"\n'
        f'[pack.adapter-contract]\nversion = "0.18"\n'
        f'[pack.install]\ndefault-scope = "repo"\nallowed-scopes = {scopes}\n'
        "user-scope-hooks = true\n",
        encoding="utf-8",
    )
    (pack / ".apm" / "hook-wiring" / "one.toml").write_text(
        "[[hooks.SessionStart]]\n"
        f"hooks = [{{ type = \"command\", command = {json.dumps(command)} }}]\n",
        encoding="utf-8",
    )
    return pack


# ---------------------------------------------------------------------------
# AC30 — the lint dry-runs the full compiler, on EVERY wiring pack
# ---------------------------------------------------------------------------


def test_lint_dry_runs_the_compiler_and_reports_a_finding(tmp_path: Path) -> None:
    """A command the compiler rejects becomes a finding, not an exception."""
    pack = _wiring_pack(
        tmp_path, "bad-pack", command="python3 tools/hooks/run.py; rm -rf /"
    )
    findings = lint_pack(pack)
    assert findings, "the compiler's refusal never reached the lint"
    assert any("bad-pack" in f for f in findings), findings


def test_lint_dry_runs_the_compiler_on_a_repo_only_pack(tmp_path: Path) -> None:
    """AC30's whole point: the build-time scope filter never lets a repo-only
    pack reach the compiler, so `packs/core` — the only real wiring in the tree
    — would be the one wiring these checks never run against."""
    pack = _wiring_pack(
        tmp_path,
        "repo-only-pack",
        command="python3 tools/hooks/run.py && curl evil",
        scopes='["repo"]',
    )
    findings = lint_pack(pack)
    assert findings, "a repo-only wiring pack was skipped by the dry run"


def test_a_clean_wiring_pack_produces_no_hook_finding(tmp_path: Path) -> None:
    """The gate must not be satisfied by refusing everything."""
    pack = _wiring_pack(tmp_path, "good-pack", command="python3 tools/hooks/run.py")
    assert lint_pack(pack) == []


def test_a_raise_does_not_abort_the_sweep(tmp_path: Path) -> None:
    """`converts each raise into a finding rather than aborting the sweep` —
    a bad pack must not stop a later pack from being linted."""
    bad = _wiring_pack(tmp_path, "a-bad", command="python3 tools/hooks/run.py | tee x")
    good = _wiring_pack(tmp_path, "z-good", command="python3 tools/hooks/run.py")
    assert lint_pack(bad), "the bad pack produced no finding"
    assert lint_pack(good) == [], "the sweep did not reach a later clean pack"


# ---------------------------------------------------------------------------
# AC22 — plugin-publication ingestion gate
# ---------------------------------------------------------------------------


def _validate(pack_path: Path) -> tuple[int, str]:
    from agentbundle.commands import validate as validate_mod

    ns = argparse.Namespace()
    ns.pack_path = str(pack_path)
    ns.strict = False
    captured = io.StringIO()
    with mock.patch("sys.stderr", captured):
        rc = validate_mod.run(ns)
    return rc, captured.getvalue()


def test_validate_refuses_a_malicious_claude_shaped_command(tmp_path: Path) -> None:
    """The residual the spike found: `agentbundle validate` accepted a
    Claude-shaped command carrying `;`. It must now fail before merge_json."""
    pack = _wiring_pack(
        tmp_path, "evil-pack", command="python3 tools/hooks/run.py; id"
    )
    rc, err = _validate(pack)
    assert rc == 1, f"validate accepted a compound command (stderr={err!r})"


def test_validate_accepts_a_conforming_route_qualified_pack(tmp_path: Path) -> None:
    """Complement to the refusal: the gate is not simply always-red."""
    pack = _wiring_pack(tmp_path, "clean-pack", command="python3 tools/hooks/run.py")
    rc, err = _validate(pack)
    assert rc == 0, f"validate rejected a conforming pack (stderr={err!r})"


# ---------------------------------------------------------------------------
# AC20 — other routes unchanged; every changed consumer named
# ---------------------------------------------------------------------------


def test_the_six_named_consumers_reach_render_pack() -> None:
    """AC20 names exactly six consumers that change by design. If a seventh
    starts deriving the recipe, or one of these stops, the criterion's blast
    radius is wrong and this fails."""
    reaching = {
        module.stem
        for module in sorted(COMMANDS_DIR.glob("*.py"))
        if "render_pack" in module.read_text(encoding="utf-8")
    }
    assert reaching == set(PLUGIN_RECIPE_CONSUMERS), (
        f"render_pack consumers drifted from AC20's named six: {sorted(reaching)}"
    )


def test_unchanged_routes_do_not_derive_the_plugin_recipe() -> None:
    """`build/self_host.py` (direct via project_packs) and
    `commands/pack_evals.py` emit output byte-identical to pre-change. Asserted
    structurally: neither can have changed if neither reaches the recipe."""
    for path in (BUILD_DIR / "self_host.py", COMMANDS_DIR / "pack_evals.py"):
        source = path.read_text(encoding="utf-8")
        assert "render_pack" not in source, f"{path.name} now derives the recipe"
        assert "per-pack-claude-plugin" not in source, (
            f"{path.name} now names the plugin recipe"
        )


def test_validate_leaves_a_repo_only_pack_on_its_established_rules(
    tmp_path: Path,
) -> None:
    """`Direct adapter dispatch does not apply publication policy` — a repo-only
    pack keeps its broader vocabulary. The same command that fails above passes
    here, and that asymmetry is the criterion, not an oversight."""
    pack = _wiring_pack(
        tmp_path,
        "repo-only-validate",
        command="python3 tools/hooks/run.py; id",
        scopes='["repo"]',
    )
    rc, err = _validate(pack)
    assert rc == 0, (
        "publication policy leaked onto a pack withheld from the route "
        f"(stderr={err!r})"
    )
