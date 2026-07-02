"""RFC-0059 / spec catalogue-curation: the first pack-on-a-non-core dependency.

Every other dependency-declaring pack depends only on ``core``.
``catalogue-curation`` requires BOTH ``core`` and ``governance-extras`` (two of
its skills emit RFCs, a governance-extras construct). This is a novel
dependency-graph shape; the RFC claims it resolves *compositionally* under the
existing gate — each pack's install gate enforces its own direct deps, and
``governance-extras`` itself gates ``core``, so the two-hop chain holds with no
new resolver logic. These tests pin that claim.
"""

from __future__ import annotations

import pytest

from agentbundle.config import PackState, State
from agentbundle.commands.install import validate_dependencies_required


def _catalogue_curation() -> dict:
    """Mirrors packs/catalogue-curation/pack.toml's required deps."""
    return {
        "pack": {
            "name": "catalogue-curation",
            "version": "0.1.0",
            "dependencies": {
                "required": [
                    {"catalogue": "agent-ready-repo", "pack": "core", "version": "^0.1"},
                    {"catalogue": "agent-ready-repo", "pack": "governance-extras", "version": "^0.1"},
                ]
            },
        }
    }


def _governance_extras() -> dict:
    return {
        "pack": {
            "name": "governance-extras",
            "version": "0.5.0",
            "dependencies": {
                "required": [
                    {"catalogue": "agent-ready-repo", "pack": "core", "version": "^0.1"}
                ]
            },
        }
    }


def _installed(*names: str) -> State:
    return State(
        packs={
            (n, "claude-code"): PackState(installed_version="0.1.0", scope="repo", adapter="claude-code")
            for n in names
        }
    )


def test_resolves_when_both_deps_present() -> None:
    # Both core and governance-extras installed → the two-hop pack resolves.
    validate_dependencies_required(
        _catalogue_curation(),
        repo_state=_installed("core", "governance-extras"),
        user_state=State(),
    )  # must not raise


def test_fails_without_governance_extras() -> None:
    # core present but governance-extras missing → the novel second dep gates.
    with pytest.raises(RuntimeError) as exc:
        validate_dependencies_required(
            _catalogue_curation(),
            repo_state=_installed("core"),
            user_state=State(),
        )
    assert "governance-extras" in str(exc.value)


def test_fails_without_core() -> None:
    with pytest.raises(RuntimeError) as exc:
        validate_dependencies_required(
            _catalogue_curation(),
            repo_state=_installed("governance-extras"),
            user_state=State(),
        )
    assert "core" in str(exc.value)


def test_two_hop_chain_holds_compositionally() -> None:
    # The chain catalogue-curation -> governance-extras -> core resolves one hop
    # at a time: governance-extras' own gate is satisfied by core alone, and
    # catalogue-curation's gate is satisfied once governance-extras is present.
    validate_dependencies_required(
        _governance_extras(),
        repo_state=_installed("core"),
        user_state=State(),
    )  # governance-extras resolves against core
    validate_dependencies_required(
        _catalogue_curation(),
        repo_state=_installed("core", "governance-extras"),
        user_state=State(),
    )  # then catalogue-curation resolves against both


def test_batch_install_satisfies_by_name() -> None:
    # Installing all three in one batch (a profile) resolves by name at pre-flight.
    validate_dependencies_required(
        _catalogue_curation(),
        repo_state=State(),
        user_state=State(),
        also_installing={"core", "governance-extras"},
    )  # must not raise


def test_dep_satisfied_across_scopes() -> None:
    # union-of-scopes: a dep installed at user scope satisfies a repo-scope pack.
    validate_dependencies_required(
        _catalogue_curation(),
        repo_state=_installed("core"),
        user_state=_installed("governance-extras"),
    )  # must not raise
