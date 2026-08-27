"""Close-work immediate-disposition construction tests."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "close-work"
SCRIPT_PATH = SKILL_ROOT / "scripts" / "close_work.py"
PROJECTED_FILE_SAFETY = SKILL_ROOT / "scripts" / "file_safety.py"
RESOLVER_PATH = (
    PACK_ROOT / ".apm" / "skills" / "work-intake" / "scripts" / "surface_resolver.py"
)


def _load_close_work():
    spec = importlib.util.spec_from_file_location("core_close_work_tests", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _preview(close_work, root: Path, target: Path, **overrides):
    values = {
        "repository_root": root,
        "surface_role": "delivery-contract",
        "logical_locator": "delivery-contract:temporary",
        "targets": (target,),
        "disposition": "delete-before-push",
        "completion_evidence_ref": "evidence:completion",
        "durable_output_evidence_refs": ("evidence:docs",),
        "pushed": False,
        "removal_integrated": False,
        "source_state_evidence_ref": "git-state:preview",
        "source_authority": "repository-origin",
        "source_authority_evidence_ref": "authority:source-preview",
        "write_authority": "repository-maintainer",
        "write_authority_evidence_ref": "authority:write-preview",
        "deletion_authority": "repository-owned",
        "deletion_authority_evidence_ref": "authority:delete-preview",
        "authorized_actor_role": "repository-maintainer",
        "proposer_role": "delivery-agent",
        "proposer_evidence_ref": "workflow:close-work-preview",
        "grant_source": "policy:maintainer-delete",
        "action": "delete-confirmed-file-set",
        "host_session_provenance": "session:current",
    }
    values.update(overrides)
    if "disposition_candidate" not in values:
        values["disposition_candidate"] = close_work.DispositionCandidate(
            lifecycle_outcome="completed",
            persisted=True,
            delivered=False,
            pushed=values["pushed"],
            removal_change=values["disposition"] == "delete-before-merge",
            removal_integrated=values["removal_integrated"],
            lasting_facts_settled=True,
            obligations_settled=True,
            source_authority=values["source_authority"],
            write_authority=values["write_authority"],
            deletion_authority=values["deletion_authority"],
        )
    if "surface_candidates" not in values:
        resolver = close_work.surface_resolver()
        raw_targets = tuple(Path(item) for item in values["targets"])
        boundary = values.get("enumeration_root")
        physical = Path(boundary) if boundary is not None else raw_targets[0]
        if not physical.is_absolute():
            physical = root / physical
        values["surface_candidates"] = (
            resolver.SurfaceCandidate(
                role="delivery-contract",
                logical_locator=values["logical_locator"],
                physical_locator=resolver.Locator(
                    "repository-path", physical.relative_to(root).as_posix()
                ),
                provenance=(
                    resolver.Evidence("explicit", "request:close-work", "explicit"),
                ),
                availability="available",
                writability="writable",
                authority=resolver.Authority(
                    source=resolver.AuthorityFact(
                        "repository-owned", values["source_authority_evidence_ref"]
                    ),
                    write=resolver.AuthorityFact(
                        "delegated", values["write_authority_evidence_ref"]
                    ),
                    delete=resolver.AuthorityFact(
                        "delegated", values["deletion_authority_evidence_ref"]
                    ),
                ),
                revision_or_fingerprint="fixture-revision-v1",
            ),
        )
    if "authority_fact" not in values:
        values["authority_fact"] = close_work.resolve_mutation_authority(
            grant_record={
                "authorized_actor_role": values["authorized_actor_role"],
                "grant_source": values["grant_source"],
                "action": values["action"],
                "resource": values["logical_locator"],
                "evidence_ref": values["deletion_authority_evidence_ref"],
                "host_session_provenance": values["host_session_provenance"],
            },
            authority_evidence_ref="authority:resolved-delete-policy",
        )
    return close_work.preview_deletion(**values)


def _human_confirmation(close_work, preview, confirmation_id: str):
    return close_work.HumanConfirmation(
        confirmation_id=confirmation_id,
        human_evidence_ref=f"human:{confirmation_id}",
        confirmation_challenge=preview.confirmation_challenge,
        enumeration_mode=preview.enumeration_mode,
        surface_role=preview.surface_role,
        logical_locator=preview.logical_locator,
        physical_locator=preview.physical_locator,
        revision_or_fingerprint=preview.revision_or_fingerprint,
        surface_resolution_fingerprint=preview.surface_resolution_fingerprint,
        resource_file_set=tuple(
            target.relative_to(preview.repository_root).as_posix()
            for target in preview.targets
        ),
        target_fingerprints=preview.target_fingerprints,
        target_fingerprint=preview.target_fingerprint,
        disposition=preview.disposition,
        disposition_eligibility_fingerprint=(
            preview.disposition_eligibility_fingerprint
        ),
        completion_evidence_ref=preview.completion_evidence_ref,
        durable_output_evidence_refs=preview.durable_output_evidence_refs,
        pushed=preview.pushed,
        removal_integrated=preview.removal_integrated,
        source_state_evidence_ref=preview.source_state_evidence_ref,
        source_authority=preview.source_authority,
        source_authority_evidence_ref=preview.source_authority_evidence_ref,
        write_authority=preview.write_authority,
        write_authority_evidence_ref=preview.write_authority_evidence_ref,
        deletion_authority=preview.deletion_authority,
        deletion_authority_evidence_ref=preview.deletion_authority_evidence_ref,
        authorized_actor_role=preview.authorized_actor_role,
        proposer_role=preview.proposer_role,
        proposer_evidence_ref=preview.proposer_evidence_ref,
        approver_role="repository-maintainer",
        approver_evidence_ref="human-gate:current",
        grant_source=preview.grant_source,
        action=preview.action,
        host_session_provenance=preview.host_session_provenance,
        authority_resource=preview.authority_resource,
        authority_resolution_evidence_ref=(
            preview.authority_resolution_evidence_ref
        ),
        authority_issue_digest=preview.authority_issue_digest,
        proposed_mutation="ordinary-file-removal",
    )


def _confirmation(close_work, preview, confirmation_id: str):
    return close_work.confirm_deletion(
        preview,
        human_confirmation=_human_confirmation(close_work, preview, confirmation_id),
    )


def _resolved_deletion_authority(close_work, preview, **overrides):
    values = {
        "authorized_actor_role": preview.authorized_actor_role,
        "grant_source": preview.grant_source,
        "action": preview.action,
        "resource": preview.authority_resource,
        "evidence_ref": preview.deletion_authority_evidence_ref,
        "host_session_provenance": preview.host_session_provenance,
    }
    authority_evidence_ref = overrides.pop(
        "authority_evidence_ref", preview.authority_resolution_evidence_ref
    )
    values.update(overrides)
    return close_work.resolve_mutation_authority(
        grant_record=values,
        authority_evidence_ref=authority_evidence_ref,
    )


def _effect_kwargs(close_work, preview) -> dict[str, object]:
    authority_fact = _resolved_deletion_authority(close_work, preview)
    assert authority_fact is not None
    return {
        "current_surface_candidates": preview.surface_candidates,
        "current_disposition_candidate": preview.disposition_candidate,
        "current_source_state": {"pushed": False, "removal_integrated": False},
        "source_state_evidence_ref": "git-state:preview",
        "current_authority_fact": authority_fact,
    }


def test_file_safety_and_resolver_load_from_pack_siblings() -> None:
    """Byte-identity against the agentbundle canonical is a roster check."""
    close_work = _load_close_work()

    assert close_work.file_safety().__file__ == str(PROJECTED_FILE_SAFETY)
    resolver = close_work.surface_resolver()
    assert Path(resolver.__file__).resolve() == RESOLVER_PATH.resolve()
    assert "delivery-contract" in resolver.SURFACE_ROLES


def test_immediate_recommendation_never_mutates_before_confirmation(
    tmp_path: Path,
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")

    preview = _preview(close_work, tmp_path, target)

    assert preview.code == "confirmation-required"
    assert preview.permission_granted is False
    assert preview.mutated == ()
    assert target.read_text(encoding="utf-8") == "temporary\n"


def test_preview_rejects_policy_shaped_strings_without_resolved_authority(
    tmp_path: Path,
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")

    result = _preview(close_work, tmp_path, target, authority_fact=None)

    assert result.code == "authority-unavailable"
    assert result.mutated == ()
    assert target.read_text(encoding="utf-8") == "temporary\n"


def test_effect_rejects_consumed_preview_authority_fact(tmp_path: Path) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    authority_fact = close_work.resolve_mutation_authority(
        grant_record={
            "authorized_actor_role": "repository-maintainer",
            "grant_source": "policy:maintainer-delete",
            "action": "delete-confirmed-file-set",
            "resource": "delivery-contract:temporary",
            "evidence_ref": "authority:delete-preview",
            "host_session_provenance": "session:current",
        },
        authority_evidence_ref="authority:resolved-delete-policy",
    )
    assert authority_fact is not None
    preview = _preview(
        close_work, tmp_path, target, authority_fact=authority_fact
    )
    confirmation = _confirmation(
        close_work, preview, "confirmation:consumed-preview-authority"
    )
    effect = _effect_kwargs(close_work, preview)
    effect["current_authority_fact"] = authority_fact

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **effect,
    )

    assert result.code == "authority-unavailable"
    assert result.mutated == ()
    assert target.exists()


def test_exact_file_preview_ignores_unrelated_sibling_files(tmp_path: Path) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    sibling = tmp_path / "keep.md"
    target.write_text("temporary\n", encoding="utf-8")
    sibling.write_text("durable\n", encoding="utf-8")

    preview = _preview(close_work, tmp_path, target)

    assert preview.code == "confirmation-required"
    assert preview.enumeration_mode == "exact-file"
    assert preview.targets == (target,)
    assert sibling.read_text(encoding="utf-8") == "durable\n"


def test_fresh_exact_confirmation_deletes_once_and_never_rewrites_history(
    tmp_path: Path,
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(close_work, preview, "confirmation:one")

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert result.code == "deleted"
    assert result.mutated == (target,)
    assert not target.exists()
    assert close_work.wave4_capabilities()["history_rewrite"] is False

    target.write_text("replacement\n", encoding="utf-8")
    replay = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )
    assert replay.code == "confirmation-reused"
    assert target.read_text(encoding="utf-8") == "replacement\n"


def _candidate(close_work, **overrides):
    """A DispositionCandidate that classifies as `delete-before-push` by default."""
    values = {
        "lifecycle_outcome": "completed",
        "persisted": True,
        "delivered": False,
        "pushed": False,
        "removal_change": False,
        "removal_integrated": False,
        "lasting_facts_settled": True,
        "obligations_settled": True,
        "source_authority": "repository-origin",
        "write_authority": "repository-maintainer",
        "deletion_authority": "repository-owned",
    }
    values.update(overrides)
    return close_work.DispositionCandidate(**values)


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        # `surface-role-invalid`: only the delivery-contract role may be deleted.
        ({"surface_role": "delivery-residue"}, "surface-role-invalid"),
        # `disposition-eligibility-invalid`: the candidate must be the real type.
        ({"disposition_candidate": None}, "disposition-eligibility-invalid"),
        # `disposition-facts-conflict`: candidate facts must equal the bound
        # scalars. `removal_integrated` differs here while classification is
        # unaffected, so this branch is reached rather than an earlier one.
        (
            {"disposition_candidate": "REMOVAL_INTEGRATED_MISMATCH"},
            "disposition-facts-conflict",
        ),
        # `proposer-role-invalid`: the reachable half of the old
        # `actor-role-invalid` guard. The `actor` half is refused upstream by
        # `_mutation_binding` against the same regex, so the code was renamed
        # to name the one field it can still concern.
        ({"proposer_role": "proposer@example.test"}, "proposer-role-invalid"),
        # `source-state-invalid`: a non-bool `pushed` that still compares equal to
        # the candidate's real bool, so facts-conflict does not fire first.
        ({"disposition_candidate": "NON_BOOL_PUSHED"}, "source-state-invalid"),
        # `source-state-ineligible`: discard-local demands tool-session write
        # authority; a repository-maintainer write reaches this branch.
        ({"disposition_candidate": "DISCARD_LOCAL_WRONG_WRITE"}, "source-state-ineligible"),
    ],
)
def test_pre_effect_refusals_on_the_deletion_path_have_zero_effect(
    tmp_path: Path, overrides: dict[str, object], expected: str
) -> None:
    """Every guard past authority binding refuses with an exact code and no effect."""
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    before = target.read_bytes()

    resolved = dict(overrides)
    sentinel = resolved.get("disposition_candidate")
    if sentinel == "REMOVAL_INTEGRATED_MISMATCH":
        resolved["disposition_candidate"] = _candidate(
            close_work, removal_integrated=True
        )
    elif sentinel == "NON_BOOL_PUSHED":
        resolved["disposition_candidate"] = _candidate(close_work)
        resolved["pushed"] = 0
    elif sentinel == "DISCARD_LOCAL_WRONG_WRITE":
        resolved["disposition_candidate"] = _candidate(
            close_work,
            persisted=False,
            source_authority="tool-session",
            write_authority="repository-maintainer",
            deletion_authority="tool-owned",
        )
        resolved["disposition"] = "discard-local"
        resolved["source_authority"] = "tool-session"
        resolved["deletion_authority"] = "tool-owned"

    result = _preview(close_work, tmp_path, target, **resolved)

    assert result.code == expected
    assert result.mutated == ()
    assert target.read_bytes() == before


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"deletion_authority": ""}, "authority-or-evidence-invalid"),
        ({"grant_source": "self-asserted"}, "authority-unavailable"),
        ({"authorized_actor_role": "person@example.test"}, "authority-unavailable"),
        ({"host_session_provenance": "unknown"}, "authority-unavailable"),
        ({"pushed": True}, "disposition-ineligible"),
        ({"disposition": "cool-30-days"}, "disposition-not-immediate"),
    ],
)
def test_missing_self_asserted_or_ineligible_authority_has_zero_effect(
    tmp_path: Path, overrides: dict[str, object], expected: str
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    before = target.read_bytes()

    result = _preview(close_work, tmp_path, target, **overrides)

    assert result.code == expected
    assert result.mutated == ()
    assert target.read_bytes() == before


def test_confirmation_binds_authority_evidence_locator_and_fingerprint(
    tmp_path: Path,
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(close_work, preview, "confirmation:bound")
    mismatched = replace(confirmation, grant_source="policy:different")

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=mismatched,
        **_effect_kwargs(close_work, preview),
    )

    assert result.code == "confirmation-not-issued"
    assert result.mutated == ()
    assert target.exists()


@pytest.mark.parametrize("drift", ["authority", "session"])
def test_authority_or_session_drift_expires_confirmation(
    tmp_path: Path, drift: str
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(close_work, preview, f"confirmation:{drift}")
    effect = _effect_kwargs(close_work, preview)
    if drift == "authority":
        effect["current_authority_fact"] = _resolved_deletion_authority(
            close_work,
            preview,
            authority_evidence_ref="authority:resolved-delete-policy-drifted",
        )
    else:
        effect["current_authority_fact"] = _resolved_deletion_authority(
            close_work, preview, host_session_provenance="session:different"
        )

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **effect,
    )

    assert result.code == "confirmation-expired"
    assert result.mutated == ()
    assert target.exists()


def test_effect_authority_refusal_happens_before_target_content_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(
        close_work, preview, "confirmation:authority-before-read"
    )
    helper = close_work.file_safety()

    def forbidden_read(*args, **kwargs):
        raise AssertionError("target content read before effect authority refusal")

    monkeypatch.setattr(helper, "read_confined_regular_file", forbidden_read)
    effect = _effect_kwargs(close_work, preview)
    effect["current_authority_fact"] = {
        "authorized_actor_role": "repository-maintainer",
        "grant_source": "policy:maintainer-delete",
        "action": "delete-confirmed-file-set",
    }

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **effect,
    )

    assert result.code == "authority-unavailable"
    assert result.mutated == ()
    assert target.exists()


def test_added_target_and_source_state_drift_expire_confirmation(
    tmp_path: Path,
) -> None:
    close_work = _load_close_work()
    scope = tmp_path / "scope"
    scope.mkdir()
    target = scope / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target, enumeration_root=scope)
    confirmation = _confirmation(close_work, preview, "confirmation:drift")
    added = scope / "added.md"
    added.write_text("new\n", encoding="utf-8")

    target_drift = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )
    assert target_drift.code == "confirmation-expired"
    assert target_drift.mutated == ()
    assert target.exists() and added.exists()

    added.unlink()
    fresh_preview = _preview(close_work, tmp_path, target, enumeration_root=scope)
    fresh_confirmation = _confirmation(
        close_work, fresh_preview, "confirmation:source-drift"
    )
    source_drift_kwargs = _effect_kwargs(close_work, fresh_preview)
    source_drift_kwargs["current_source_state"] = {
        "pushed": True,
        "removal_integrated": False,
    }
    source_drift = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=fresh_preview,
        confirmation=fresh_confirmation,
        **source_drift_kwargs,
    )
    assert source_drift.code == "confirmation-expired"
    assert source_drift.mutated == ()
    assert target.exists()


@pytest.mark.skipif(not hasattr(os, "link"), reason="hard links unavailable")
def test_hard_link_is_refused_without_read_or_mutation(tmp_path: Path) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    alias = tmp_path / "alias.md"
    os.link(target, alias)
    before = hashlib.sha256(target.read_bytes()).hexdigest()

    result = _preview(
        close_work,
        tmp_path,
        target,
        targets=(target,),
    )

    assert result.code == "unsafe-target"
    assert result.mutated == ()
    assert hashlib.sha256(target.read_bytes()).hexdigest() == before


def test_multi_file_preview_requires_one_confirmation_per_file(tmp_path: Path) -> None:
    close_work = _load_close_work()
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    first.write_text("first\n", encoding="utf-8")
    second.write_text("second\n", encoding="utf-8")
    preview = _preview(
        close_work,
        tmp_path,
        first,
        targets=(first, second),
        enumeration_root=tmp_path,
    )
    assert preview.code == "one-file-confirmation-required"
    assert preview.mutated == ()
    assert first.read_text(encoding="utf-8") == "first\n"
    assert second.read_text(encoding="utf-8") == "second\n"
    assert not tuple(tmp_path.glob(".close-work-*.pending"))


def test_forged_multi_file_preview_cannot_receive_confirmation(
    tmp_path: Path,
) -> None:
    close_work = _load_close_work()
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    first.write_text("first\n", encoding="utf-8")
    second.write_text("second\n", encoding="utf-8")
    issued = _preview(close_work, tmp_path, first)
    forged = replace(issued, targets=(first, second))

    with pytest.raises(ValueError, match="issued.*exactly one file"):
        close_work.confirm_deletion(
            forged,
            human_confirmation=_human_confirmation(
                close_work, forged, "confirmation:forged-multi"
            ),
        )

    assert first.read_text(encoding="utf-8") == "first\n"
    assert second.read_text(encoding="utf-8") == "second\n"


def test_enumeration_entry_bound_refuses_an_oversized_tree(tmp_path: Path) -> None:
    """`MAX_ENUMERATION_ENTRIES` had no fixture that breached it.

    Directories are entries and are not files, so a wide directory-only tree
    breaches the entry bound without breaching the file bound. Deleting the
    `entry_count > MAX_ENUMERATION_ENTRIES` check fails this case.

    Scope, recorded deliberately: the three file-count layers
    (`file_count > MAX_TARGETS` in the preflight, `max_files=MAX_TARGETS` on the
    materialising walk, and `len(enumerated) > MAX_TARGETS`) are NOT
    independently observable through this public seam. Declaring one target
    against a 33-file tree refuses on the enumeration mismatch first; declaring
    all 33 refuses on `one-file-confirmation-required` first, because Wave 4
    deletes exactly one file. They cover each other, so no single deletion among
    them changes an observable result. That residual is named in the review
    verdict rather than papered over with a case that would pass for the wrong
    reason.
    """
    close_work = _load_close_work()
    root = tmp_path / "surface"
    root.mkdir()
    for index in range(300):
        (root / f"dir-{index:03d}").mkdir()
    only = root / "residue-000.md"
    only.write_text("x\n", encoding="utf-8")
    before = sorted(path.name for path in root.rglob("*"))

    result = _preview(close_work, tmp_path, only, enumeration_root=root)

    assert result.code == "unsafe-target"
    assert result.mutated == ()
    assert sorted(path.name for path in root.rglob("*")) == before


def test_unverifiable_residue_is_reported_as_unverified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The `unverified` arm of the discriminator, observed rather than assumed.

    `identity-confirmed` and `identity-mismatch` are each asserted elsewhere;
    without this the third vocabulary member appeared only in prose pins, so any
    site could be relabelled to it with every gate green — and `unverified` is
    precisely the value that tells a maintainer NOT to restore.

    Built on the same seam as the rollback-failure case below: the final unlink
    refuses, so rollback runs; inspection then refuses too, so identity cannot be
    established.
    """
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(
        close_work, preview, "confirmation:unverifiable-residue"
    )
    real_unlink = close_work.os.unlink

    def fail_unlink(path, *args, **kwargs):
        if str(path).endswith(".pending"):
            raise PermissionError("simulated unlink refusal")
        return real_unlink(path, *args, **kwargs)

    # `_inspect_fingerprint_at` has two call sites: a pre-effect check at
    # close_work.py:1458 and the rollback inspection at :2140. Refusing the
    # first would abort before any effect, so only the rollback call is failed.
    real_inspect = close_work._inspect_fingerprint_at
    inspections = 0

    def refuse_rollback_inspection(*args, **kwargs):
        nonlocal inspections
        inspections += 1
        if inspections >= 2:
            raise OSError("simulated inspection failure")
        return real_inspect(*args, **kwargs)

    monkeypatch.setattr(close_work.os, "unlink", fail_unlink)
    monkeypatch.setattr(
        close_work, "_inspect_fingerprint_at", refuse_rollback_inspection
    )

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    # Identity could not be established, so the report must say so rather than
    # claim the residue is the confirmed inode.
    assert result.residue_state == "unverified"
    assert result.residual_evidence is None


def test_post_unlink_parent_substitution_reports_no_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The post-unlink parent-path refusal must report no effect, not a failure.

    This is the one behaviour change of the round-57 repair and it had no driving
    case. `_directory_path_matches_fd` is faked to fail only on its post-unlink
    call, so `rollback_staged_link` relinks the original and unlinks staging —
    restoration genuinely succeeds. Reporting `rollback-failed` here would name a
    residue path that was just unlinked, and under a substituted parent that path
    could resolve to foreign content.
    """
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    before = target.read_bytes()
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(
        close_work, preview, "confirmation:post-unlink-parent-swap"
    )
    real_matches = close_work._directory_path_matches_fd
    calls = 0

    def fail_on_the_post_unlink_check(directory: Path, descriptor: int) -> bool:
        nonlocal calls
        calls += 1
        # The pre-unlink checks must pass so the effect proceeds to the staged
        # verification; only the post-unlink call refuses.
        if calls >= 3:
            return False
        return real_matches(directory, descriptor)

    monkeypatch.setattr(
        close_work, "_directory_path_matches_fd", fail_on_the_post_unlink_check
    )

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert result.code == "confirmation-expired"
    assert result.mutated == ()
    assert result.recovery_residue == ()
    assert result.residue_state is None
    # Restoration actually happened: the original is back, byte-for-byte, and no
    # staging residue survives.
    assert target.read_bytes() == before
    assert not tuple(tmp_path.glob(".close-work-*.pending"))


def test_post_stage_identity_mismatch_rolls_back_before_unlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(
        close_work, preview, "confirmation:post-stage-swap"
    )
    real_fingerprint = close_work._fingerprint_at
    calls = 0

    def mismatched_staged_fingerprint(
        descriptor: int, name: str, relative_path: str, **kwargs
    ):
        nonlocal calls
        calls += 1
        value = real_fingerprint(descriptor, name, relative_path, **kwargs)
        if calls == 2:
            return replace(value, sha256="0" * 64)
        return value

    monkeypatch.setattr(close_work, "_fingerprint_at", mismatched_staged_fingerprint)

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert result.code == "confirmation-expired"
    assert result.mutated == ()
    assert target.read_text(encoding="utf-8") == "temporary\n"
    assert not tuple(tmp_path.glob(".close-work-*.pending"))


def test_oversized_target_is_refused_before_hashing(tmp_path: Path) -> None:
    close_work = _load_close_work()
    target = tmp_path / "oversized.bin"
    with target.open("wb") as handle:
        handle.truncate(close_work.MAX_FILE_BYTES + 1)

    result = _preview(close_work, tmp_path, target)

    assert result.code == "unsafe-target"
    assert result.mutated == ()
    assert target.stat().st_size == close_work.MAX_FILE_BYTES + 1


def test_classifier_rejects_self_asserted_authority_strings() -> None:
    close_work = _load_close_work()
    candidate = close_work.DispositionCandidate(
        lifecycle_outcome="completed",
        persisted=True,
        delivered=False,
        pushed=False,
        lasting_facts_settled=True,
        obligations_settled=True,
        source_authority="self-asserted",
        write_authority="repository-maintainer",
        deletion_authority="repository-owned",
    )

    result = close_work.classify_disposition(candidate)

    assert result.disposition is None
    assert result.blocker == "source-authority-invalid"


def test_confirmation_without_fresh_source_state_has_zero_effect(tmp_path: Path) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(
        close_work, preview, "confirmation:no-source-state"
    )
    effect = _effect_kwargs(close_work, preview)
    effect.pop("current_source_state")
    effect.pop("source_state_evidence_ref")

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **effect,
    )

    assert result.code == "source-state-unavailable"
    assert result.mutated == ()
    assert target.exists()


@pytest.mark.parametrize(
    ("field", "malformed", "expected"),
    (
        ("current_source_state", [], "source-state-unavailable"),
        ("current_authority_fact", {}, "authority-unavailable"),
    ),
)
def test_malformed_effect_evidence_refuses_and_consumes_confirmation(
    tmp_path: Path, field: str, malformed: object, expected: str
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(
        close_work, preview, f"confirmation:malformed-{field}"
    )
    effect = _effect_kwargs(close_work, preview)
    effect[field] = malformed

    refused = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **effect,
    )
    replay = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert refused.code == expected
    assert refused.mutated == ()
    assert replay.code == "confirmation-reused"
    assert target.read_text(encoding="utf-8") == "temporary\n"


def test_human_confirmation_must_restate_every_exact_bound_fact(tmp_path: Path) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    supplied = _human_confirmation(close_work, preview, "confirmation:human")

    with pytest.raises(ValueError, match="exactly match"):
        close_work.confirm_deletion(
            preview,
            human_confirmation=replace(
                supplied, resource_file_set=("broader-scope",)
            ),
        )

    assert target.read_text(encoding="utf-8") == "temporary\n"


def test_surface_resolution_drift_expires_confirmation(tmp_path: Path) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(close_work, preview, "confirmation:resolver-drift")
    current_candidates = (
        replace(
            preview.surface_candidates[0],
            revision_or_fingerprint="fixture-revision-v2",
        ),
    )
    effect = _effect_kwargs(close_work, preview)
    effect["current_surface_candidates"] = current_candidates

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **effect,
    )

    assert result.code == "confirmation-expired"
    assert result.mutated == ()
    assert target.exists()


def test_delete_before_merge_integration_drift_expires_confirmation(
    tmp_path: Path,
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    candidate = close_work.DispositionCandidate(
        lifecycle_outcome="abandoned",
        persisted=True,
        delivered=False,
        pushed=True,
        removal_change=True,
        removal_integrated=False,
        lasting_facts_settled=True,
        obligations_settled=True,
        source_authority="repository-origin",
        write_authority="repository-maintainer",
        deletion_authority="repository-owned",
    )
    preview = _preview(
        close_work,
        tmp_path,
        target,
        disposition="delete-before-merge",
        disposition_candidate=candidate,
        pushed=True,
    )
    confirmation = _confirmation(
        close_work, preview, "confirmation:integrated-drift"
    )
    effect = _effect_kwargs(close_work, preview)
    effect["current_disposition_candidate"] = replace(
        candidate, removal_integrated=True
    )
    effect["current_source_state"] = {
        "pushed": True,
        "removal_integrated": True,
    }

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **effect,
    )

    assert result.code == "confirmation-expired"
    assert result.mutated == ()
    assert target.exists()


def test_expired_confirmation_is_terminal_even_after_bytes_are_restored(
    tmp_path: Path,
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(close_work, preview, "confirmation:terminal")
    target.write_text("drifted\n", encoding="utf-8")

    expired = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )
    target.write_text("temporary\n", encoding="utf-8")
    reused = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert expired.code == "confirmation-expired"
    assert reused.code == "confirmation-reused"
    assert target.exists()


def test_unlink_failure_rolls_back_original_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(close_work, preview, "confirmation:unlink-fails")
    real_unlink = close_work.os.unlink
    failed = False

    def fail_pending_once(path, *args, **kwargs):
        nonlocal failed
        if not failed and str(path).endswith(".pending"):
            failed = True
            raise PermissionError("simulated final unlink refusal")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(close_work.os, "unlink", fail_pending_once)

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert result.code == "effect-failed"
    assert result.mutated == ()
    assert target.read_text(encoding="utf-8") == "temporary\n"
    assert not tuple(tmp_path.glob(".close-work-*.pending"))


def test_late_staging_destination_is_not_replaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(
        close_work, preview, "confirmation:staging-no-clobber"
    )
    real_link = close_work.os.link

    def create_destination_then_link(source, destination, *args, **kwargs):
        if str(destination).endswith(".pending"):
            descriptor = os.open(
                destination,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=kwargs["dst_dir_fd"],
            )
            try:
                os.write(descriptor, b"must-stay\n")
            finally:
                os.close(descriptor)
        return real_link(source, destination, *args, **kwargs)

    monkeypatch.setattr(close_work.os, "link", create_destination_then_link)

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    residue = tuple(tmp_path.glob(".close-work-*.pending"))
    assert result.code == "unsafe-target"
    assert result.mutated == ()
    assert target.read_text(encoding="utf-8") == "temporary\n"
    assert len(residue) == 1
    assert residue[0].read_text(encoding="utf-8") == "must-stay\n"


def test_final_unlink_verifies_no_surviving_hard_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(
        close_work, preview, "confirmation:final-link-race"
    )
    survivor = tmp_path / "survivor.md"
    real_link = close_work.os.link
    real_unlink = close_work.os.unlink
    injected = False

    def link_before_final_unlink(path, *args, **kwargs):
        nonlocal injected
        if str(path).endswith(".pending") and not injected:
            injected = True
            real_link(
                path,
                survivor.name,
                src_dir_fd=kwargs["dir_fd"],
                dst_dir_fd=kwargs["dir_fd"],
                follow_symlinks=False,
            )
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(close_work.os, "unlink", link_before_final_unlink)

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert result.code == "residual-hardlink"
    # AC11: the discriminator is what authorises human recovery, so observe
    # the value, not merely that some evidence object exists.
    assert result.residue_state == "identity-confirmed"
    assert result.mutated == (target,)
    assert result.permission_granted is True
    assert result.residual_evidence is not None
    assert (
        result.residual_evidence.confirmed_fingerprint
        == preview.target_fingerprints[0]
    )
    assert result.residual_evidence.observed_link_count == 1
    assert result.residual_evidence.observed_device == survivor.stat().st_dev
    assert result.residual_evidence.observed_inode == survivor.stat().st_ino
    assert not target.exists()
    assert survivor.read_text(encoding="utf-8") == "temporary\n"


def test_locator_unlink_window_reports_surviving_hard_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(
        close_work, preview, "confirmation:locator-link-race"
    )
    survivor = tmp_path / "survivor.md"
    real_link = close_work.os.link
    real_unlink = close_work.os.unlink
    injected = False

    def link_before_locator_unlink(path, *args, **kwargs):
        nonlocal injected
        if path == target.name and not injected:
            injected = True
            real_link(
                path,
                survivor.name,
                src_dir_fd=kwargs["dir_fd"],
                dst_dir_fd=kwargs["dir_fd"],
                follow_symlinks=False,
            )
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(close_work.os, "unlink", link_before_locator_unlink)

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert result.code == "residual-hardlink"
    # AC11: the discriminator is what authorises human recovery, so observe
    # the value, not merely that some evidence object exists.
    assert result.residue_state == "identity-confirmed"
    assert result.mutated == (target,)
    assert result.permission_granted is True
    assert result.residual_evidence is not None
    assert (
        result.residual_evidence.confirmed_fingerprint
        == preview.target_fingerprints[0]
    )
    assert result.residual_evidence.observed_link_count == 1
    assert result.residual_evidence.observed_device == survivor.stat().st_dev
    assert result.residual_evidence.observed_inode == survivor.stat().st_ino
    assert not target.exists()
    assert survivor.read_text(encoding="utf-8") == "temporary\n"
    assert not tuple(tmp_path.glob(".close-work-*.pending"))


def test_failed_final_unlink_with_surviving_link_stays_residual_hardlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(
        close_work, preview, "confirmation:rollback-link-race"
    )
    survivor = tmp_path / "survivor.md"
    real_link = close_work.os.link
    real_unlink = close_work.os.unlink
    injected = False

    def link_then_fail_final_unlink(path, *args, **kwargs):
        nonlocal injected
        if str(path).endswith(".pending") and not injected:
            injected = True
            real_link(
                path,
                survivor.name,
                src_dir_fd=kwargs["dir_fd"],
                dst_dir_fd=kwargs["dir_fd"],
                follow_symlinks=False,
            )
            raise PermissionError("simulated final unlink refusal")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(close_work.os, "unlink", link_then_fail_final_unlink)

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert result.code == "residual-hardlink"
    # AC11: the discriminator is what authorises human recovery, so observe
    # the value, not merely that some evidence object exists.
    assert result.residue_state == "identity-confirmed"
    assert result.mutated == (target,)
    assert result.permission_granted is True
    assert result.residual_evidence is not None
    assert (
        result.residual_evidence.confirmed_fingerprint
        == preview.target_fingerprints[0]
    )
    assert result.residual_evidence.observed_link_count == 2
    assert result.residual_evidence.observed_device == survivor.stat().st_dev
    assert result.residual_evidence.observed_inode == survivor.stat().st_ino
    assert not target.exists()
    assert survivor.read_text(encoding="utf-8") == "temporary\n"
    assert len(result.recovery_residue) == 1
    assert result.recovery_residue[0].exists()


def test_parent_directory_symlink_swap_cannot_redirect_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    scope = tmp_path / "scope"
    scope.mkdir()
    target = scope / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    attacker = tmp_path / "attacker"
    attacker.mkdir()
    attacker_target = attacker / "delivery.md"
    attacker_target.write_text("must-stay\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(close_work, preview, "confirmation:parent-swap")
    original_open = close_work._open_validated_parent
    moved = tmp_path / "scope-moved"

    def swap_before_open(repository_root: Path, directory: Path) -> int:
        directory.rename(moved)
        directory.symlink_to(attacker, target_is_directory=True)
        return original_open(repository_root, directory)

    monkeypatch.setattr(close_work, "_open_validated_parent", swap_before_open)

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert result.code == "confirmation-expired"
    assert result.mutated == ()
    preserved = [
        path
        for path in tmp_path.rglob("delivery.md")
        if path.is_file() and path.read_text(encoding="utf-8") == "temporary\n"
    ]
    assert preserved
    assert attacker_target.read_text(encoding="utf-8") == "must-stay\n"


def test_intermediate_parent_symlink_swap_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    outer = tmp_path / "outer"
    inner = outer / "inner"
    inner.mkdir(parents=True)
    target = inner / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    attacker = tmp_path / "attacker"
    attacker_inner = attacker / "inner"
    attacker_inner.mkdir(parents=True)
    attacker_target = attacker_inner / "delivery.md"
    attacker_target.write_text("must-stay\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(
        close_work, preview, "confirmation:intermediate-swap"
    )
    real_open = close_work.os.open
    moved = tmp_path / "outer-moved"
    swapped = False

    def swap_on_component(path, flags, *args, **kwargs):
        nonlocal swapped
        if str(path) == "outer" and kwargs.get("dir_fd") is not None and not swapped:
            swapped = True
            outer.rename(moved)
            outer.symlink_to(attacker, target_is_directory=True)
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(close_work.os, "open", swap_on_component)

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert result.code == "confirmation-expired"
    assert result.mutated == ()
    assert swapped is True
    preserved = [
        path
        for path in tmp_path.rglob("delivery.md")
        if path.is_file() and path.read_text(encoding="utf-8") == "temporary\n"
    ]
    assert preserved
    assert attacker_target.read_text(encoding="utf-8") == "must-stay\n"


def test_preview_refuses_before_confirmation_when_secure_effect_is_unsupported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    monkeypatch.setattr(close_work, "secure_effect_supported", lambda: False)

    result = _preview(close_work, tmp_path, target)

    assert result.code == "secure-effect-unsupported"
    assert result.mutated == ()
    assert target.exists()


def test_effect_boundary_open_is_nonblocking_without_a_hanging_fifo_oracle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(close_work, preview, "confirmation:open-flags")
    real_open = close_work.os.open
    final_component_flags: list[int] = []

    def recording_open(path, flags, *args, **kwargs):
        if path == target.name and kwargs.get("dir_fd") is not None:
            final_component_flags.append(flags)
            raise OSError("bounded final-component open oracle")
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(close_work.os, "open", recording_open)

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert result.code == "confirmation-expired"
    assert result.mutated == ()
    assert final_component_flags
    assert all(flags & os.O_NONBLOCK for flags in final_component_flags)
    assert target.read_text(encoding="utf-8") == "temporary\n"


def test_secure_effect_refusal_does_not_consume_confirmation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(
        close_work, preview, "confirmation:unsupported-effect"
    )
    real_support_check = close_work.secure_effect_supported
    monkeypatch.setattr(close_work, "secure_effect_supported", lambda: False)

    refused = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert refused.code == "secure-effect-unsupported"
    assert refused.mutated == ()
    assert target.exists()

    monkeypatch.setattr(close_work, "secure_effect_supported", real_support_check)
    applied = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert applied.code == "deleted"
    assert applied.mutated == (target,)
    assert not target.exists()


def test_human_approver_must_differ_from_proposer(tmp_path: Path) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    supplied = _human_confirmation(close_work, preview, "confirmation:self-approve")

    with pytest.raises(ValueError, match="differ from proposer"):
        close_work.confirm_deletion(
            preview,
            human_confirmation=replace(
                supplied, approver_role=preview.proposer_role
            ),
        )

    assert target.exists()


def test_issued_confirmation_cannot_be_forged_or_reissued_with_a_new_id(
    tmp_path: Path,
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    supplied = _human_confirmation(close_work, preview, "confirmation:issued")
    confirmation = close_work.confirm_deletion(
        preview, human_confirmation=supplied
    )

    with pytest.raises(ValueError, match="already issued"):
        close_work.confirm_deletion(
            preview,
            human_confirmation=replace(
                supplied, confirmation_id="confirmation:changed-id"
            ),
        )

    forged = replace(confirmation, confirmation_id="confirmation:forged")
    refused = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=forged,
        **_effect_kwargs(close_work, preview),
    )
    replay = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert refused.code == "confirmation-not-issued"
    assert replay.code == "confirmation-reused"
    assert target.exists()


def test_prior_process_human_proof_cannot_authorize_a_fresh_preview(
    tmp_path: Path,
) -> None:
    first_helper = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    first_preview = _preview(first_helper, tmp_path, target)
    first_human = _human_confirmation(
        first_helper, first_preview, "confirmation:prior-process"
    )

    fresh_helper = _load_close_work()
    fresh_preview = _preview(fresh_helper, tmp_path, target)
    replay = _human_confirmation(
        fresh_helper, fresh_preview, "confirmation:prior-process"
    )

    assert fresh_preview.confirmation_challenge != first_preview.confirmation_challenge
    with pytest.raises(ValueError, match="exactly match preview"):
        fresh_helper.confirm_deletion(
            fresh_preview,
            human_confirmation=replace(
                replay, confirmation_challenge=first_human.confirmation_challenge
            ),
        )


def test_prior_process_issued_confirmation_is_not_live_after_restart(
    tmp_path: Path,
) -> None:
    first_helper = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    first_preview = _preview(first_helper, tmp_path, target)
    first_confirmation = _confirmation(
        first_helper, first_preview, "confirmation:stale-issued"
    )

    fresh_helper = _load_close_work()
    fresh_preview = _preview(fresh_helper, tmp_path, target)
    reconstructed = fresh_helper.DeletionConfirmation(
        **{
            field.name: getattr(first_confirmation, field.name)
            for field in first_helper.dataclasses.fields(first_confirmation)
        }
    )

    refused = fresh_helper.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=fresh_preview,
        confirmation=reconstructed,
        **_effect_kwargs(fresh_helper, fresh_preview),
    )
    replay = fresh_helper.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=fresh_preview,
        confirmation=reconstructed,
        **_effect_kwargs(fresh_helper, fresh_preview),
    )

    assert refused.code == "confirmation-not-issued"
    assert refused.mutated == ()
    assert replay.code == "confirmation-reused"
    assert target.read_text(encoding="utf-8") == "temporary\n"


def test_resolver_authority_refuses_before_target_content_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    resolver = close_work.surface_resolver()
    valid_preview = _preview(close_work, tmp_path, target)
    candidate = valid_preview.surface_candidates[0]
    incompatible = replace(
        candidate,
        authority=resolver.Authority(
            source=candidate.authority.source,
            write=candidate.authority.write,
            delete=resolver.AuthorityFact(
                "external-owned", "authority:delete-preview"
            ),
        ),
    )
    helper = close_work.file_safety()

    def forbidden_read(*args, **kwargs):
        raise AssertionError("target content read before resolver refusal")

    monkeypatch.setattr(helper, "read_confined_regular_file", forbidden_read)

    result = _preview(
        close_work,
        tmp_path,
        target,
        surface_candidates=(incompatible,),
    )

    assert result.code == "surface-resolution-refused"
    assert target.exists()


def test_required_resolver_confirmation_refuses_before_target_content_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    resolver = close_work.surface_resolver()
    valid_preview = _preview(close_work, tmp_path, target)
    candidate = valid_preview.surface_candidates[0]
    requiring_confirmation = replace(
        candidate,
        confirmations=(
            resolver.Confirmation("destination-selection", "required"),
        ),
    )
    helper = close_work.file_safety()

    def forbidden_read(*args, **kwargs):
        raise AssertionError("target content read before resolver confirmation refusal")

    monkeypatch.setattr(helper, "read_confined_regular_file", forbidden_read)

    result = _preview(
        close_work,
        tmp_path,
        target,
        surface_candidates=(requiring_confirmation,),
    )

    assert result.code == "surface-resolution-refused"
    assert result.mutated == ()
    assert target.exists()


def test_effect_required_resolver_confirmation_refuses_before_content_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(
        close_work, preview, "confirmation:effect-resolver-required"
    )
    resolver = close_work.surface_resolver()
    requiring_confirmation = replace(
        preview.surface_candidates[0],
        confirmations=(
            resolver.Confirmation("destination-selection", "required"),
        ),
    )
    helper = close_work.file_safety()

    def forbidden_read(*args, **kwargs):
        raise AssertionError("target content read before effect resolver refusal")

    monkeypatch.setattr(helper, "read_confined_regular_file", forbidden_read)
    effect = _effect_kwargs(close_work, preview)
    effect["current_surface_candidates"] = (requiring_confirmation,)

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **effect,
    )

    assert result.code == "confirmation-expired"
    assert result.mutated == ()
    assert target.exists()


def test_preview_fingerprint_uses_bounded_blessed_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    helper = close_work.file_safety()
    real_read = helper.read_confined_regular_file
    observed: list[int | None] = []

    def bounded_read(root: Path, path: Path, *, max_bytes=None):
        observed.append(max_bytes)
        return real_read(root, path, max_bytes=max_bytes)

    monkeypatch.setattr(helper, "read_confined_regular_file", bounded_read)

    preview = _preview(close_work, tmp_path, target)

    assert preview.code == "confirmation-required"
    assert observed == [close_work.MAX_FILE_BYTES]


def test_rollback_failure_reports_original_move_and_recovery_residue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(close_work, preview, "confirmation:rollback-fails")
    real_link = close_work.os.link
    real_unlink = close_work.os.unlink

    def fail_restore(source, destination, *args, **kwargs):
        if str(source).endswith(".pending") and destination == target.name:
            raise PermissionError("simulated rollback refusal")
        return real_link(source, destination, *args, **kwargs)

    def fail_unlink(path, *args, **kwargs):
        if str(path).endswith(".pending"):
            raise PermissionError("simulated unlink refusal")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(close_work.os, "link", fail_restore)
    monkeypatch.setattr(close_work.os, "unlink", fail_unlink)

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert result.code == "rollback-failed"
    assert result.mutated == (target,)
    assert result.permission_granted is True
    assert len(result.recovery_residue) == 1
    assert result.recovery_residue[0].exists()
    # The descriptor proved the residue is the confirmed inode, so a maintainer
    # may restore it. Bounded inode evidence travels with that claim.
    assert result.residue_state == "identity-confirmed"
    assert result.residual_evidence is not None
    assert result.residual_evidence.confirmed_fingerprint.sha256 == (
        preview.target_fingerprints[0].sha256
    )


def test_rollback_never_restores_a_swapped_staging_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(
        close_work, preview, "confirmation:rollback-stage-swap"
    )
    real_unlink = close_work.os.unlink
    swapped = False

    def swap_pending_then_fail(path, *args, **kwargs):
        nonlocal swapped
        if str(path).endswith(".pending") and not swapped:
            swapped = True
            real_unlink(path, *args, **kwargs)
            descriptor = os.open(
                path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=kwargs["dir_fd"],
            )
            try:
                os.write(descriptor, b"attacker-controlled\n")
            finally:
                os.close(descriptor)
            raise PermissionError("simulated final unlink race")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(close_work.os, "unlink", swap_pending_then_fail)

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )

    assert result.code == "rollback-failed"
    assert result.mutated == (target,)
    assert not target.exists()
    assert len(result.recovery_residue) == 1
    assert result.recovery_residue[0].read_text(encoding="utf-8") == (
        "attacker-controlled\n"
    )
    # This is the discriminating case: the residue survived but the descriptor
    # proved it is NOT the confirmed inode, so the maintainer must not restore
    # it. Without a discriminator this result is shape-identical to the
    # identity-confirmed rollback failure above.
    assert result.residue_state == "identity-mismatch"
    assert result.residual_evidence is not None
    assert result.residual_evidence.observed_inode != (
        preview.target_fingerprints[0].inode
    )


@pytest.mark.parametrize(
    ("dropped", "expected"),
    [
        ("current_disposition_candidate", "disposition-evidence-unavailable"),
        ("current_surface_candidates", "surface-evidence-unavailable"),
    ],
)
def test_post_confirmation_evidence_refusals_consume_the_confirmation(
    tmp_path: Path, dropped: str, expected: str
) -> None:
    """AC11/AC19: the post-confirmation half of the destructive path.

    These two guards sit after the confirmation is consumed, so the contract is
    both a zero-effect refusal AND single-use consumption — a replay must not
    become a second chance. The shared `_effect_kwargs` helper always supplied
    both arguments, so neither guard had ever been driven.
    """
    close_work = _load_close_work()
    target = tmp_path / "delivery.md"
    target.write_text("temporary\n", encoding="utf-8")
    before = target.read_bytes()
    preview = _preview(close_work, tmp_path, target)
    confirmation = _confirmation(close_work, preview, f"confirmation:{dropped}")

    kwargs = _effect_kwargs(close_work, preview)
    kwargs[dropped] = None

    result = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **kwargs,
    )

    assert result.code == expected
    assert result.mutated == ()
    assert target.read_bytes() == before

    # The confirmation was consumed before the guard, so a well-formed retry
    # with the same confirmation must be refused as reused, not honoured.
    replay = close_work.apply_confirmed_deletion(
        repository_root=tmp_path,
        preview=preview,
        confirmation=confirmation,
        **_effect_kwargs(close_work, preview),
    )
    assert replay.code == "confirmation-reused"
    assert target.read_bytes() == before


def test_skill_and_evals_keep_policy_confirmation_and_effect_separate() -> None:
    skill = " ".join((SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8").split())
    for phrase in (
        "A disposition is intent, never deletion permission",
        "Immediate disposal is a default recommendation, never an automatic action",
        "Re-read every affected durable surface as a whole",
        "Confirmation is single-use",
        "Never reset, rebase, filter, force-push",
        "Do not start a timer",
        # AC14's record-field obligations, which otherwise live only as table
        # prose and could be deleted with every gate green.
        "Retain with bounded reason, owner role, and human-supplied review date",
        "Emit a bounded advisory; do not probe or mutate the external system",
        # The residue-identity vocabulary is declared once in code and restated
        # in shipped doctrine; without this pin a rename in one leaves the other
        # silently wrong.
        "identity-confirmed",
        "identity-mismatch",
        "unverified",
    ):
        assert phrase in skill

    evals = json.loads((SKILL_ROOT / "evals/evals.json").read_text(encoding="utf-8"))
    rendered = json.dumps(evals)
    assert "external-advisory" in rendered
    assert "source, write, and deletion authority" in rendered
    assert "refuses to calculate dates" in rendered
