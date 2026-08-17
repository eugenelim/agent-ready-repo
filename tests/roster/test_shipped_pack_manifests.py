"""Schema-validation pins for shipped packs.

`make build-self` already invokes ``validate_pack_metadata`` per pack at
build time, so a malformed shipped manifest breaks CI. These pytests
pin the *positive* shape — the repo-only packs declare the v0.8
contract metadata and the addon packs carry the required-dep on
``core`` — so a silent metadata removal (or a botched bump) trips a
test rather than slipping through.

``product-documentation`` is separate: it allows user + repo scope and
carries no ``core`` dependency; it has its own assertions below.
``user-guide-diataxis`` (0.3.0) is a deprecated compat shim that
requires ``product-documentation`` (not ``core``); it has its own
assertion below.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKS_DIR = REPO_ROOT / "packs"

# Repo-only packs (allowed-scopes = ["repo"]) with adapter-contract v0.8
# (core is v0.12 — bumped by copilot-full-parity / copilot-skills-and-web).
REPO_ONLY_PACKS = ("core", "governance-extras", "user-guide-diataxis", "monorepo-extras")
# Addon packs that declare a required dep on core ^0.1.
CORE_DEP_PACKS = ("governance-extras", "monorepo-extras")

# Every pack shipping a `credentialed: true` skill declares a required dep on
# `credential-brokers` — the pack that ships the `credbroker` floor and the
# `sso-broker.py` engine. Ranges differ by need: `atlassian` needs the exit-4
# `refresh` contract that landed in 0.3.0. Zero-major caret ranges do not cross
# a minor boundary, so every current consumer must declare the shipped 0.3 line.
# `credential-brokers` itself is absent because it ships
# `credential-setup` (`credentialed: true`) and cannot depend on itself, and
# `github` because it shells out to `gh`, which owns its own credential chain.
CREDENTIALED_PACK_BROKER_RANGE = {
    "atlassian": "^0.3",
    "figma": "^0.3",
    "linear": "^0.3",
}


def _load(pack_name: str) -> dict:
    path = PACKS_DIR / pack_name / "pack.toml"
    assert path.exists(), f"shipped pack {pack_name!r} missing pack.toml at {path}"
    return tomllib.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("pack_name", CORE_DEP_PACKS)
def test_addon_manifests_carry_required_dependency(pack_name):
    """Addon packs (governance-extras, monorepo-extras) declare
    `[[pack.dependencies.required]]` against `core` with the `^2.0`
    caret-minor range (bumped from ^0.1 → ^1.0 when core
    hit 1.0.0, then ^1.0 → ^2.0 when core hit 2.0.0).

    user-guide-diataxis (0.3.0) is a deprecated shim that depends on
    product-documentation instead of core; its dep is pinned separately.
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
        and e.get("version") == "^2.0"
    ]
    assert matches, (
        f"{pack_name}: required-dep entry "
        '{catalogue="agent-ready-repo", pack="core", version="^2.0"} not found; '
        f"got {required!r}"
    )


@pytest.mark.parametrize(
    ("pack_name", "expected_range"), sorted(CREDENTIALED_PACK_BROKER_RANGE.items())
)
def test_credentialed_packs_require_credential_brokers(pack_name, expected_range):
    """A credentialed pack declares the broker layer it cannot run without.

    `install.py` gates required dependencies before any write, resolving against
    the union of repo + user state. Without the declaration
    `agentbundle install <pack> --scope user` succeeds while the `credbroker`
    floor and `sso-broker.py` are absent, and the skill fails at runtime with no
    remediation.
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
        and e.get("pack") == "credential-brokers"
        and e.get("version") == expected_range
    ]
    assert matches, (
        f"{pack_name}: required-dep entry {{catalogue=\"agent-ready-repo\", "
        f"pack=\"credential-brokers\", version=\"{expected_range}\"}} not found; "
        f"got {required!r}"
    )


@pytest.mark.parametrize("pack_name", sorted(CREDENTIALED_PACK_BROKER_RANGE))
def test_the_install_gate_refuses_without_the_broker_and_admits_it_with(pack_name):
    """Drive the real resolver, not a second implementation of its rules.

    Every credentialed consumer declares the shipped 0.3 broker line, and the
    real install resolver must admit that installed broker version. Re-deriving
    caret-minor semantics here would be a second copy of the rule this test
    exists to protect, free to drift from the resolver without either side
    going red.
    """
    from agentbundle.commands.install import validate_dependencies_required
    from agentbundle.config import PackState, State

    manifest = _load(pack_name)
    shipped = _load("credential-brokers")["pack"]["version"]
    empty = State()
    with_broker = State(
        packs={
            ("credential-brokers", "claude-code"): PackState(
                installed_version=shipped
            )
        }
    )

    with pytest.raises(RuntimeError) as exc:
        validate_dependencies_required(
            manifest, repo_state=empty, user_state=State()
        )
    assert "credential-brokers" in str(exc.value), exc.value

    # And the declared range admits the version the pack actually ships.
    validate_dependencies_required(
        manifest, repo_state=empty, user_state=with_broker
    )


def test_shim_requires_product_documentation():
    """user-guide-diataxis (0.3.0) is a deprecated compat shim.
    It must declare a required dep on product-documentation ^0.1 so the
    resolver errors when the canonical pack is absent.
    """
    data = _load("user-guide-diataxis")
    required = data.get("pack", {}).get("dependencies", {}).get("required")
    assert isinstance(required, list) and required, (
        "user-guide-diataxis: expected non-empty [[pack.dependencies.required]] list"
    )
    matches = [
        e for e in required
        if isinstance(e, dict)
        and e.get("catalogue") == "agent-ready-repo"
        and e.get("pack") == "product-documentation"
        and e.get("version") == "^0.1"
    ]
    assert matches, (
        "user-guide-diataxis: required-dep entry "
        '{catalogue="agent-ready-repo", pack="product-documentation", version="^0.1"} not found; '
        f"got {required!r}"
    )


@pytest.mark.parametrize("pack_name", REPO_ONLY_PACKS)
def test_repo_only_packs_declare_install_table(pack_name):
    """Repo-only shipped packs declare the current contract + the
    `[pack.install]` table with `default-scope = "repo"` and
    `allowed-scopes = ["repo"]`. All four repo-only packs are repo-only by
    content (core
    ships hooks, addons scaffold project directories). v0.7 bumps
    the four repo-only packs from v0.2 to v0.7 (Drawback #7 mitigation —
    required for the resolver to route them to codex/copilot via the
    no-flag default at repo scope).
    """
    data = _load(pack_name)
    contract = data.get("pack", {}).get("adapter-contract", {})
    # Dropped-primitives coverage bumped the four repo-only
    # packs from v0.7 → v0.8 (codex agent + hook-wiring move from
    # `dropped` to first-class projections at v0.8). Copilot full
    # parity bumped `core` to v0.10, and copilot skills and web bumps
    # `core` to v0.12 (its skills now project as first-class Copilot Agent
    # Skills); the other three stay at v0.8.
    expected_version = "0.12" if pack_name == "core" else "0.8"
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


def test_shim_has_no_seeds():
    """T-D3: user-guide-diataxis 0.3.0 is a deprecated compat shim.
    It must have no seeds/ directory; a re-added scaffold would silently
    project quadrant directories into adopter repos.
    """
    seeds = PACKS_DIR / "user-guide-diataxis" / "seeds"
    assert not seeds.exists(), (
        f"user-guide-diataxis: seeds/ directory must not exist in compat shim; found {seeds}"
    )


def test_canonical_has_no_quadrant_seeds():
    """T-D4: product-documentation installs no directory scaffold.
    Assert the four Diátaxis quadrant paths are absent under seeds/.
    """
    seeds = PACKS_DIR / "product-documentation" / "seeds"
    if not seeds.exists():
        return  # no seeds at all — trivially passes
    for quadrant in ("tutorials", "how-to", "reference", "explanation"):
        path = seeds / "guides" / quadrant
        assert not path.exists(), (
            f"product-documentation: seeds/guides/{quadrant}/ must not exist "
            "(Diátaxis is a page contract, not a directory scaffold)"
        )


def test_product_documentation_install_table():
    """product-documentation allows both user and repo scope (no core dep).
    Pins the install-table shape so a silent scope restriction regresses.
    """
    data = _load("product-documentation")
    contract = data.get("pack", {}).get("adapter-contract", {})
    assert contract.get("version") == "0.8", (
        f"product-documentation: adapter-contract.version must be \"0.8\"; got {contract!r}"
    )
    install = data.get("pack", {}).get("install")
    assert isinstance(install, dict), "product-documentation: [pack.install] table missing"
    assert install.get("default-scope") == "repo", (
        f"product-documentation: default-scope must be \"repo\"; got {install!r}"
    )
    assert install.get("allowed-scopes") == ["repo", "user"], (
        f"product-documentation: allowed-scopes must be [\"repo\", \"user\"]; got {install!r}"
    )
    assert not data.get("pack", {}).get("dependencies"), (
        "product-documentation: must have no core dependency (user scope requires it)"
    )
