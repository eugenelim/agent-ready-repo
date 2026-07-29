"""catalogue-curation 0.2.0: no required dependencies.

``catalogue-curation`` previously required both ``core`` and
``governance-extras`` (RFC-0059 D1). In 0.2.0 those hard deps were removed
— the pack's skills now operate portably against the target catalogue's own
contracts. These tests pin the no-dep guarantee and confirm the install gate
does not reject a clean install.
"""

from __future__ import annotations

from agentbundle.commands.install import validate_dependencies_required
from agentbundle.config import State


def _catalogue_curation() -> dict:
    """Mirrors packs/catalogue-curation/pack.toml 0.2.0 — no required deps."""
    return {
        "pack": {
            "name": "catalogue-curation",
            "version": "0.2.0",
            "dependencies": {},
        }
    }


def test_installs_without_any_deps() -> None:
    # No required deps → resolves against a completely empty state.
    validate_dependencies_required(
        _catalogue_curation(),
        repo_state=State(),
        user_state=State(),
    )  # must not raise


def test_installs_regardless_of_installed_packs() -> None:
    # Having other packs installed does not break the install — dependency
    # resolution is not order-sensitive.
    from agentbundle.config import PackState

    state = State(
        packs={
            ("core", "claude-code"): PackState(
                installed_version="0.1.0", scope="repo", adapter="claude-code"
            ),
            ("governance-extras", "claude-code"): PackState(
                installed_version="0.5.0", scope="repo", adapter="claude-code"
            ),
        }
    )
    validate_dependencies_required(
        _catalogue_curation(),
        repo_state=state,
        user_state=State(),
    )  # must not raise


def test_dep_dict_empty() -> None:
    # The pack.toml carries no [[pack.dependencies.required]] entries.
    pack_data = _catalogue_curation()
    required = pack_data["pack"]["dependencies"].get("required", [])
    assert required == [], f"Expected no required deps; got: {required}"
