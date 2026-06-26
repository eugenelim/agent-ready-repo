"""T3 (pack-profiles AC7): batch-aware required-dependency gate.

``validate_dependencies_required`` gains an optional ``also_installing`` set so
a pack's required dep can be satisfied by another pack *in the same batch*
(profile install). Name-membership satisfies at pre-flight; the version range is
enforced for real at write time against actual state (deps-first order) and by
the lint at author-time. The default call (no ``also_installing``) is unchanged.
"""

from __future__ import annotations

import pytest

from agentbundle.config import PackState, State
from agentbundle.commands.install import validate_dependencies_required


def _pack_requiring_core() -> dict:
    return {
        "pack": {
            "name": "governance-extras",
            "version": "0.1.2",
            "dependencies": {
                "required": [
                    {"catalogue": "agent-ready-repo", "pack": "core", "version": "^0.1"}
                ]
            },
        }
    }


def _empty() -> State:
    return State()


def test_dep_in_batch_satisfies_when_not_in_state():
    # core is not installed, but it is being installed in this batch.
    validate_dependencies_required(
        _pack_requiring_core(),
        repo_state=_empty(),
        user_state=_empty(),
        also_installing={"core"},
    )  # must not raise


def test_dep_missing_from_state_and_batch_still_fails():
    with pytest.raises(RuntimeError) as exc:
        validate_dependencies_required(
            _pack_requiring_core(),
            repo_state=_empty(),
            user_state=_empty(),
            also_installing={"some-other-pack"},
        )
    assert "core" in str(exc.value)


def test_default_call_without_batch_is_unchanged_behavior():
    # No also_installing → existing single-pack behavior: core absent → fail.
    with pytest.raises(RuntimeError) as exc:
        validate_dependencies_required(
            _pack_requiring_core(),
            repo_state=_empty(),
            user_state=_empty(),
        )
    assert "install core first" in str(exc.value)


def test_dep_in_state_still_satisfies_with_batch_param():
    state = State(packs={("core", "claude-code"): PackState(installed_version="0.4.9", scope="repo", adapter="claude-code")})
    validate_dependencies_required(
        _pack_requiring_core(),
        repo_state=state,
        user_state=_empty(),
        also_installing={"governance-extras"},
    )  # must not raise


def test_dep_on_disk_at_unsatisfying_version_fails_even_if_in_batch():
    # core is pre-installed at 0.0.1 (does NOT satisfy ^0.1) AND named in the
    # batch. Name-membership must not bypass the version check for an on-disk
    # dep — the write-time gate stays real (pack-profiles AC7).
    state = State(packs={("core", "claude-code"): PackState(installed_version="0.0.1", scope="repo", adapter="claude-code")})
    with pytest.raises(RuntimeError) as exc:
        validate_dependencies_required(
            _pack_requiring_core(),
            repo_state=state,
            user_state=_empty(),
            also_installing={"core", "governance-extras"},
        )
    assert "core" in str(exc.value)


def test_batch_param_does_not_bypass_grammar_check():
    # A malformed range must still raise even if the dep name is in the batch.
    bad = {
        "pack": {
            "name": "x",
            "version": "0.1.0",
            "dependencies": {
                "required": [
                    {"catalogue": "agent-ready-repo", "pack": "core", "version": "0.1"}
                ]
            },
        }
    }
    with pytest.raises(RuntimeError) as exc:
        validate_dependencies_required(
            bad, repo_state=_empty(), user_state=_empty(), also_installing={"core"}
        )
    assert "unsupported version range" in str(exc.value)
