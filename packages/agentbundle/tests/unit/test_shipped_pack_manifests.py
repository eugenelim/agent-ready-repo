"""AC18 schema-validation pins for shipped packs.

`make build-self` already invokes ``validate_pack_metadata`` per pack at
build time, so a malformed shipped manifest breaks CI. These pytests
pin the *positive* shape — the four shipped packs declare the v0.2
contract metadata and the three addon packs carry the required-dep on
``core`` — so a silent metadata removal (or a botched bump) trips a
test rather than slipping through.

Scope is deliberately narrow: enumerate the four shipped packs by
name. Three addons / four total is small enough not to warrant a
helper.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[4]
PACKS_DIR = REPO_ROOT / "packs"

ALL_SHIPPED_PACKS = ("core", "governance-extras", "user-guide-diataxis", "monorepo-extras")
ADDON_PACKS = ("governance-extras", "user-guide-diataxis", "monorepo-extras")


def _load(pack_name: str) -> dict:
    path = PACKS_DIR / pack_name / "pack.toml"
    assert path.exists(), f"shipped pack {pack_name!r} missing pack.toml at {path}"
    return tomllib.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("pack_name", ADDON_PACKS)
def test_addon_manifests_carry_required_dependency(pack_name):
    """Every addon pack declares `[[pack.dependencies.required]]` against
    `core` with the `^0.1` caret-minor range (adapt-to-project AC18).

    Scope: this test pins the *manifest shape*. The install-time gate
    behavior (refusing an addon install when core is absent from the
    union of repo+user state) is covered separately by
    `test_install_dependencies_gate.py`.
    """
    data = _load(pack_name)
    required = data.get("pack", {}).get("dependencies", {}).get("required")
    assert isinstance(required, list) and required, (
        f"{pack_name}: expected non-empty [[pack.dependencies.required]] list"
    )
    matches = [
        e for e in required
        if isinstance(e, dict)
        and e.get("catalogue") == "agent-ready-repo"
        and e.get("pack") == "core"
        and e.get("version") == "^0.1"
    ]
    assert matches, (
        f"{pack_name}: required-dep entry "
        '{catalogue="agent-ready-repo", pack="core", version="^0.1"} not found; '
        f"got {required!r}"
    )


@pytest.mark.parametrize("pack_name", ALL_SHIPPED_PACKS)
def test_all_packs_declare_install_table(pack_name):
    """Every shipped pack declares the current contract + the
    `[pack.install]` table with `default-scope = "repo"` and
    `allowed-scopes = ["repo"]`. RFC-0004 sets the install-scope
    dimension; all four shipped packs are repo-only by content (core
    ships hooks, addons scaffold project directories) so the four
    packs land in lockstep with the contract. RFC-0012 bumps the
    four repo-only packs from v0.2 to v0.7 (Drawback #7 mitigation —
    required for the resolver to route them to codex/copilot via the
    no-flag default at repo scope).
    """
    data = _load(pack_name)
    contract = data.get("pack", {}).get("adapter-contract", {})
    # docs/specs/dropped-primitives-coverage T7 bumped the four repo-only
    # packs from v0.7 → v0.8 (codex agent + hook-wiring move from
    # `dropped` to first-class projections at v0.8). docs/specs/copilot-full-
    # parity bumps `core` again to v0.10 (its subagents + hook-wiring now
    # project to copilot); the other three stay at v0.8.
    expected_version = "0.10" if pack_name == "core" else "0.8"
    assert contract.get("version") == expected_version, (
        f"{pack_name}: [pack.adapter-contract] version must be "
        f"\"{expected_version}\"; got {contract!r}"
    )
    install = data.get("pack", {}).get("install")
    assert isinstance(install, dict), (
        f"{pack_name}: [pack.install] table missing"
    )
    assert install.get("default-scope") == "repo", (
        f"{pack_name}: [pack.install] default-scope must be \"repo\"; "
        f"got {install!r}"
    )
    assert install.get("allowed-scopes") == ["repo"], (
        f"{pack_name}: [pack.install] allowed-scopes must be [\"repo\"]; "
        f"got {install!r}"
    )
