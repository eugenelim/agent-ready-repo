"""_supervisor_readiness — readiness derived from durable facts.

A run is ready when the current approval pair matches the working envelope and
terminal intent, every acceptance criterion is supported by fresh admissible
evidence, and the shared review readiness says the subject is acceptance
eligible. Nothing here reads a stored verdict or readiness answer: criteria
verdicts are evaluated from receipts on every call, and review readiness is
computed from the durable review records.

Freshness is exact-subject over the product: every file outside the spec
directory in the result commit the run's authority reads (the product ref's
commit, or HEAD under the reversal setting), so a supervisor step that appends only
``delivery/`` records never stales evidence.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent


def _supervisor(filename: str) -> ModuleType:
    """Load a supervisor module once per process, shared by every supervisor module.

    Registered under a name unique to this scripts directory, so two installed
    copies of the skill never share an instance.
    """
    tag = hashlib.sha256(str(_SCRIPTS_DIR).encode("utf-8")).hexdigest()[:12]
    alias = f"_work_supervisor_{tag}_" + filename.removesuffix(".py").strip("_").replace("-", "_")
    module = sys.modules.get(alias)
    if module is not None:
        return module
    path = _SCRIPTS_DIR / filename
    if not stat.S_ISREG(os.lstat(path).st_mode):
        raise ImportError(f"{path.name} is not a regular file")
    spec = importlib.util.spec_from_file_location(alias, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.modules[alias] = module
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(alias, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


_loop = _supervisor("_supervisor_loop.py")
_projector = _supervisor("_supervisor_projector.py")
_review = _supervisor("_supervisor_review.py")
_admission = _supervisor("_supervisor_admission.py")
_tiers = _supervisor("_review_tiers.py")
sibling = _loop.sibling
Refusal = _loop.Refusal

__all__ = [
    "changed_files",
    "commit_carries",
    "open_finding_pairs",
    "review_flow",
    "run_base",
    "criteria",
    "current_selection_key",
    "delivery_subject",
    "readiness",
    "readiness_action",
    "report_readiness",
    "review_subject",
]

EVIDENCE_POLICY = "work-supervisor:criteria:v1"
GATES_RUN = "run:gates"
_CRITERION_RE = re.compile(r"^\s*[-*]\s*\[[ xX]\]\s*\*\*(AC-\d{4})\b", re.MULTILINE)


def criteria(ws: Any) -> list[str]:
    """Acceptance criterion ids in the working spec's Acceptance Criteria section."""
    sections = _projector._find_sections(ws.spec_text(), "Acceptance Criteria")
    found = _CRITERION_RE.findall(sections[0]) if sections else []
    return list(dict.fromkeys(found))


def result_lineage(ws: Any, state: Any) -> tuple[str, str, str]:
    """``(provider, result commit, projection version)`` the run's authority reads.

    Under ``protected-product-ref`` the result is the commit the run store recorded for
    the product ref, so history on ``HEAD`` the owner has not adopted changes nothing;
    a run with no recorded ref (steps committed while an attempt was open) reads ``HEAD``.
    Under ``legacy-worktree`` the result is ``HEAD``.

    The run's supervisor commits (``state.commits``, which feed the reanchor salt and the
    changed paths' first touch) are always read from ``HEAD``'s history. Every verb that acts
    refuses a diverged ``HEAD`` before it reads the subject, so only ``status`` can show a
    subject computed while foreign history sits on ``HEAD``, and it is display only.
    """
    if ws.policy["result_authority"] == "protected-product-ref":
        record = ws.git.product_record(state.run_id)
        return "protected-product-ref", (record.recorded if record else state.head), "1"
    return "work-supervisor", state.head, "1"


def delivery_subject(ws: Any, state: Any) -> dict[str, Any]:
    """The ``delivery-subject.v1`` for the product the run's authority reads."""
    prefix = ws.spec_rel + "/"
    provider, result, version = result_lineage(ws, state)
    manifest = tuple(
        sorted((p, oid) for p, oid in ws.git.tree_entries(result) if not p.startswith(prefix))
    )
    spec_fingerprint = state.latest["envelope"]["envelope_fingerprint"]
    for commit in reversed(state.commits):
        if commit.operation == "reanchor" and commit.trailers.get(
            "Supervisor-Reanchor-Changed", "none"
        ) != "none":
            # An adopted change to the product or the spec directory starts the
            # evidence over: nothing recorded before it counts.
            spec_fingerprint = hashlib.sha256(
                f"{spec_fingerprint}\0{commit.sha}".encode()
            ).hexdigest()
            break
    return sibling("_subject_projection.py").project_delivery_subject(
        subject_id=state.run_id,
        base_ref=state.base,
        result_ref=result,
        spec_path=f"{ws.spec_rel}/spec.md",
        spec_fingerprint=spec_fingerprint,
        evidence_policy_ref=EVIDENCE_POLICY,
        exclusions=(prefix,),
        provider=provider,
        projection_version=version,
        manifest_pairs=manifest,
    )


def changed_files(ws: Any, state: Any) -> list[dict[str, str]]:
    """The product paths the run's own commits changed, each with its status.

    Read from the run's ``stub`` and ``implement`` commits, so a rebase onto new
    upstream work never makes that work part of the run's review.
    """
    prefix = ws.spec_rel + "/"
    result = result_lineage(ws, state)[1]
    first_touch: dict[str, str] = {}
    for commit in state.commits:
        if commit.operation in ("stub", "implement"):
            for path in ws.git.touched_paths(commit.sha):
                if not path.startswith(prefix):
                    first_touch.setdefault(path, commit.sha)
    changes = []
    for path, sha in sorted(first_touch.items()):
        if ws.git.show(path, result) is None:
            status = "deleted"
        elif ws.git.show(path, f"{sha}^") is None:
            status = "added"
        else:
            status = "modified"
        changes.append({"path": path, "status": status})
    return changes


def current_selection_key(ws: Any, state: Any) -> str:
    """The key of the run's current reviewer selection."""
    subject = delivery_subject(ws, state)
    changes = changed_files(ws, state)
    return _review.selection_key(subject["acceptance_fingerprint"], [c["path"] for c in changes])


def review_subject(
    ws: Any,
    state: Any,
    subject: dict[str, Any],
    policy: dict[str, Any] | None = None,
    changes: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """The ``review-subject.v1`` over the changed product paths and the resolved policy.

    The policy comes from the run's selection record (``current_policy``), so it
    refuses when no valid record exists.
    """
    if changes is None:
        changes = changed_files(ws, state)
    if policy is None:
        paths = [c["path"] for c in changes]
        key = _review.selection_key(subject["acceptance_fingerprint"], paths)
        policy = _review.current_policy(ws, state, key)
    return sibling("_review_selection.py").project_review_subject(
        subject,
        changed_paths=changes,
        review_policy_fingerprint=policy["review_policy_fingerprint"],
    )


def _properties(state: Any, ids: list[str]) -> list[dict[str, Any]]:
    authority = state.latest["approval"]["approval_id"]
    return [
        {
            "schema_version": 1,
            "property_id": ac,
            "spec_ref": "spec.md",
            "authority_ref": authority,
            "subject_selector": {"paths_or_artifacts": ["."], "fingerprint_algorithm": "sha256"},
            "required_observations": [
                {
                    "term": f"criterion:{ac}",
                    "observation_type": "gate",
                    "producer_class": _loop.PRODUCER_CLASS,
                    "outcomes": ["pass"],
                }
            ],
            "freshness_scope": "exact-subject",
            "satisfaction_rule": {"expression": "any"},
            "contradiction_rule": {"expression": f"criterion-fail:{ac}"},
            "policy_version": EVIDENCE_POLICY,
        }
        for ac in ids
    ]


# ── the review flow: tier, protection, rounds, and carries ──────────────────


def run_base_checked(ws: Any, state: Any, result: str) -> tuple[str | None, str]:
    """``(run base, why)``: the parent of the run's earliest ``stub`` or ``implement`` commit.

    Defined only when every commit between that parent and *result* is a commit of this
    run, so a foreign commit in the middle of the history leaves it undefined. *why* is
    empty for a defined base and names the failed condition otherwise. The rev-list read is
    bounded by the classifier's read limit.
    """
    first = next((c for c in state.commits if c.operation in ("stub", "implement")), None)
    if first is None:
        return None, "the run has no stub or implement commit"
    try:
        base = ws.git.resolve(f"{first.sha}^")
        if not base:
            return None, "the run's first commit has no parent"
        between = ws.git.rev_list(base, result, limit=_tiers.READ_LIMIT)
    except Exception as exc:  # noqa: BLE001 - an undefined run base only lowers what a tier can save
        code = getattr(exc, "code", None)
        return None, f"the run base could not be read: {type(exc).__name__}" + (
            f" ({code})" if code else ""
        )
    mine = {c.sha for c in state.commits}
    if all(sha in mine for sha in between):
        return base, ""
    return None, "a commit that is not the run's lies between the run base and the result"


def run_base(ws: Any, state: Any, result: str) -> str | None:
    """The run base, or ``None`` when it is undefined (see ``run_base_checked``)."""
    return run_base_checked(ws, state, result)[0]


def _memoized(ws: Any, key: tuple[Any, ...], make: Callable[[], Any]) -> Any:
    """One classifier input or answer per key for the life of the workspace object.

    Every key names commits by id, so a cached answer never goes stale.
    """
    memo = ws.__dict__.setdefault("_review_memo", {})
    if key not in memo:
        memo[key] = make()
    return memo[key]


def _reanchors_since(state: Any, subject_fingerprint: str) -> tuple[bool, bool]:
    """Whether a reanchor changed the product, and the spec directory, since a reviewed subject.

    The subject's last review or carry step is the last commit whose step id names it; with
    no such step the answer is ``(False, False)``, so no rebase is called. The flow asks about
    the subject reviewed just before the current one: a reanchor that an earlier subject
    already carried through review does not make a later repair a reanchor subject.
    """
    span = _subject_span(state.commits, subject_fingerprint)
    if span is None:
        return False, False
    product = spec = False
    for commit in state.commits[span[1] + 1 :]:
        if commit.operation == "reanchor":
            changed = commit.trailers.get("Supervisor-Reanchor-Changed", "none")
            product = product or "product" in changed
            spec = spec or "spec" in changed
    return product, spec


def _report_subjects(reports: list[dict[str, Any]], run_id: str) -> list[dict[str, str]]:
    """The review subjects of this run that hold a report, in order of their first report."""
    found: dict[str, dict[str, str]] = {}
    for report in reports:
        subject = report.get("subject", {})
        ref = subject.get("delivery_subject_ref", {})
        fp = subject.get("review_subject_fingerprint")
        if fp and ref.get("subject_id") == run_id and fp not in found:
            found[fp] = {"fp": fp, "acceptance": str(ref.get("acceptance_fingerprint", ""))}
    return list(found.values())


def _raised(store: Any, reports: list[dict[str, Any]], fp: str) -> list[dict[str, str]]:
    """Supported material findings in each role's tip report on subject *fp*, not accepted.

    A finding a later fresh report closes with ``fixed-by`` is still listed: the tier a
    subject earns must not change as the reports on that subject arrive.
    """
    tips: dict[str, dict[str, Any]] = {}
    for report in reports:
        if report["subject"]["review_subject_fingerprint"] != fp:
            continue
        held = tips.get(report["role"])
        if held is None or report["lineage"]["sequence"] >= held["lineage"]["sequence"]:
            tips[report["role"]] = report
    if not tips:
        return []
    current = store.current_finding_assessments(fp)
    dispositions = store.get_semantic_records("finding-disposition.v1")
    raised = []
    for role, tip in sorted(tips.items()):
        for finding in tip["findings"]:
            entry = current.get((tip["report_id"], finding["finding_id"]))
            if not finding.get("material", False) or entry is None:
                continue
            assessment = entry["assessment"]
            if assessment["assessment"] != "supported":
                continue
            if any(
                d["assessment_id"] == assessment["assessment_id"]
                and d["disposition"] == "accept-risk"
                and store.disposition_closes(d["disposition_id"], tip["subject"])
                for d in dispositions
            ):
                continue
            raised.append(
                {"role": role, "report_id": tip["report_id"], "finding_id": finding["finding_id"]}
            )
    return raised


def _subject_span(commits: list[Any], fp: str) -> tuple[int, int] | None:
    """The first and last position of a commit that records review work on subject *fp*."""
    tag = f":{fp[-24:]}:"
    marks = [
        number
        for number, commit in enumerate(commits)
        if commit.operation == "review"
        and commit.step.startswith(("review:", "carry:"))
        and tag in commit.step
    ]
    return (marks[0], marks[-1]) if marks else None


def _implemented_between(commits: list[Any], earlier: str, later: str | None) -> bool:
    """Whether the run's own implement or stub commits changed the product between two subjects.

    A reanchor adopts upstream history and is not the run's own change. A subject whose commits
    cannot be located counts as changed, so the cap errs towards asking.
    """
    before = _subject_span(commits, earlier)
    after = _subject_span(commits, later) if later is not None else (len(commits), len(commits))
    if before is None or after is None:
        return True
    return any(
        commit.operation in ("stub", "implement") for commit in commits[before[1] + 1 : after[0]]
    )


def _rounds(
    store: Any,
    reports: list[dict[str, Any]],
    subjects: list[dict[str, str]],
    current: dict[str, str],
    commits: list[Any],
) -> tuple[int, bool]:
    """``(rounds among the reviewed subjects, whether the current subject is a round)``.

    A subject is a round when it is the unit's first, or the run's own implement step changed
    the product after a subject whose supported findings were not accepted. A selection alone
    changes the review subject and not the product, a rebase or a wording-only subject follows
    no such findings, and a product change that only a reanchor adopted is not the run's own
    repair, so none of them is a round.
    """
    reviewed = {s["fp"] for s in subjects}
    ordered = subjects if current["fp"] in reviewed else [*subjects, current]
    count = 0
    is_round = False
    previous: dict[str, str] | None = None
    for subject in ordered:
        counts = previous is None or (
            subject["acceptance"] != previous["acceptance"]
            and bool(_raised(store, reports, previous["fp"]))
            and _implemented_between(
                commits, previous["fp"], subject["fp"] if subject["fp"] in reviewed else None
            )
        )
        if subject["fp"] == current["fp"]:
            is_round = counts
        if counts and subject["fp"] in reviewed:
            count += 1
        previous = subject
    return count, is_round


def _unit_protection(
    rules: dict[str, Any], selection: Any, roles: set[str]
) -> tuple[bool, list[str], frozenset[str]]:
    """``(protection unknown, declared classes, protected roles)`` over the unit's selections."""
    unknown = False
    classes: set[str] = set()
    protected: set[str] = set()
    for record in selection.unit:
        found = _review.protection(rules, record)
        if found.unknown:
            unknown = True
            continue
        classes |= set(found.classes or ())
        protected |= found.roles
    return unknown, sorted(classes), frozenset(protected & roles)


def review_flow(
    ws: Any,
    state: Any,
    store: Any,
    rules: dict[str, Any],
    selection: Any,
    policy: dict[str, Any],
    review: dict[str, Any],
    subject: dict[str, Any],
    changes: list[dict[str, str]],
) -> dict[str, Any]:
    """The tier the current review subject earns, who is asked, who is carried, the rounds.

    Pure over the committed records and Git reads. Protected roles are never excused, and
    a unit that reads a selection with no ``protected_classes`` is protected and ``full``.
    """
    fp = review["review_subject_fingerprint"]
    roles = [r["role"] for r in policy["roles"]]
    unknown, classes, protected = _unit_protection(rules, selection, set(roles))
    reports = store.get_semantic_records("review-report.v1")
    subjects = _report_subjects(reports, state.run_id)
    previous = next((s for s in reversed(subjects) if s["fp"] != fp), None)
    raised = _raised(store, reports, previous["fp"]) if previous else []
    anchors = _review.anchor_records(ws)
    answers = _review.cap_answers(ws)
    line = anchors[-1] if anchors else None
    result = result_lineage(ws, state)[1]
    changed = [c["path"] for c in changes]
    tier_name, reason = _tiers.FULL, "no anchor facts"
    if unknown:
        reason = "protection is unknown for a selection that predates protected classes"
    elif line is not None and line["review_subject_fingerprint"] == fp:
        reason = "the subject is the anchor round"
    elif line is not None:
        product, spec = _reanchors_since(
            state, previous["fp"] if previous else line["review_subject_fingerprint"]
        )
        facts = _review.anchor_facts(line)
        base, base_why = (
            _memoized(
                ws,
                ("run-base", result, len(state.commits)),
                lambda: run_base_checked(ws, state, result),
            )
            if product
            else (None, "")
        )
        inputs = {
            "current": result,
            "changed": changed,
            "run_base": base,
            "open_findings": bool(raised),
            "adopted_reanchor": product,
            "spec_dir_changed": spec,
            "selection_changed": line["review_policy_fingerprint"]
            != review["review_policy_fingerprint"],
            "review_tier": selection.latest.get("review_tier"),
        }
        key = (
            "tier",
            rules["rules_version"],
            json.dumps(line, sort_keys=True),
            result,
            base,
            tuple(sorted(changed)),
            bool(raised),
            product,
            spec,
            inputs["selection_changed"],
            inputs["review_tier"],
        )
        found = _memoized(
            ws, key, lambda: _tiers.classify(ws.git, rules, facts, **inputs)
        )
        tier_name, reason = found.name, found.reason
        if base_why and tier_name == _tiers.FULL:
            reason = f"{reason} ({base_why})"
    if line is None and reason == "no anchor facts":
        skipped = next(
            (
                c.trailers["Supervisor-Anchor-Skipped"]
                for c in reversed(state.commits)
                if "Supervisor-Anchor-Skipped" in c.trailers
            ),
            None,
        )
        if skipped:
            reason = f"no anchor facts: {skipped}"
    plain = [r for r in roles if r not in protected]
    delta: dict[str, list[str]] = {}
    if tier_name == _tiers.WORDING_ONLY:
        asked: list[str] = []
    elif tier_name == _tiers.REBASE:
        asked = [r for r in plain if r == "adversarial-reviewer"]
        delta = {r: [] for r in asked}
    elif tier_name == _tiers.MINOR_FIX:
        asked = [r for r in plain if any(f["role"] == r for f in raised)]
        delta = {r: sorted(f["finding_id"] for f in raised if f["role"] == r) for r in asked}
    else:
        asked = list(plain)
    digest = None
    if line is not None:
        body = _admission.canonical_line(line)
        digest = hashlib.sha256(
            body + b"\0" + subject["acceptance_fingerprint"].encode() + b"\0"
            + rules["rules_version"].encode()
        ).hexdigest()
    current = {"fp": fp, "acceptance": subject["acceptance_fingerprint"]}
    count, is_round = _rounds(store, reports, subjects, current, state.commits)
    reported = fp in {s["fp"] for s in subjects}
    extensions = sum(1 for d in answers if d["decision"] == "extend-review")
    return {
        "tier": tier_name,
        "reason": reason,
        "roles": roles,
        "protection_unknown": unknown,
        "protected_classes": classes,
        "protected_roles": sorted(protected),
        "asked_roles": asked,
        "excused_roles": [] if tier_name == _tiers.FULL else [r for r in plain if r not in asked],
        "delta": delta,
        "delta_base": line["anchor_result"] if line is not None else None,
        "anchor_round": line["round"] if line is not None else None,
        "classifier_digest": digest,
        "round_count": count,
        "rounds_with_current": count + (0 if reported or not is_round else 1),
        "current_is_round": is_round,
        "round_cap": int(rules["code_review_round_cap"]) + extensions,
        "answered_caps": len(answers),
    }


def open_finding_pairs(ws: Any, view: dict[str, Any]) -> list[dict[str, str]]:
    """The open findings of the current subject as ``role``, ``report_id``, ``finding_id`` rows."""
    review = view["review_subject"]
    if review is None:
        return []
    store = ws.open_evidence()
    reports = store.get_semantic_records("review-report.v1")
    open_keys = {(f["role"], f["finding_id"]) for f in view["review"]["open_findings"]}
    return [
        row
        for row in _raised(store, reports, review["review_subject_fingerprint"])
        if (row["role"], row["finding_id"]) in open_keys
    ]


def _report_positions(ws: Any) -> dict[str, int]:
    """Each report's position (frame number) in the evidence log, derived by the supervisor."""
    es = sibling("_evidence_store.py")
    raw = ws.evidence_bytes()
    replay = es.replay_admitted_frames(raw[: raw.rfind(b"\n") + 1])
    found: dict[str, int] = {}
    for number, (_tx, records) in enumerate(replay["frames"]):
        for record in records:
            if isinstance(record, dict) and "report_id" in record and "findings" in record:
                found.setdefault(str(record["report_id"]), number)
    return found


def _build_carry(
    role: str,
    *,
    flow: dict[str, Any],
    review: dict[str, Any],
    policy: dict[str, Any],
    reports: list[dict[str, Any]],
    carries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """The ``review-carry.v1`` that stands in for *role*'s latest report, or ``None``.

    Tries a carry of the role's latest report, then of its latest carry, and keeps the
    first one the carry resolver would count; with neither, the role is asked instead.
    """
    contracts = sibling("_review_contracts.py")
    selection = sibling("_review_selection.py")
    fp = review["review_subject_fingerprint"]
    earlier = [
        c
        for c in carries
        if contracts.validate_review_carry_dict(c)[0]
        and c["role"] == role
        and c["review_subject_fingerprint"] != fp
    ]
    held = [
        r
        for r in reports
        if r.get("role") == role and r["subject"]["review_subject_fingerprint"] != fp
    ]
    if not held:
        return None
    sources = [{"from_report_id": held[-1]["report_id"]}]
    if earlier:
        sources.append({"from_carry_id": earlier[-1]["carry_id"]})
    for source in sources:
        record: dict[str, Any] = {
            "schema_version": 1,
            "role": role,
            "review_subject_fingerprint": fp,
            "review_policy_fingerprint": review["review_policy_fingerprint"],
            "tier": flow["tier"],
            "anchor_round": flow["anchor_round"],
            **source,
            "classifier_digest": flow["classifier_digest"],
        }
        record["carry_id"] = contracts.carry_id_of(record)
        carried, _why = selection.resolve_carried_report(
            role,
            review_subject=review,
            policy=policy,
            reports=reports,
            carries=[*carries, record],
            expected_tier=flow["tier"],
            expected_classifier_digest=flow["classifier_digest"],
            protected_roles=frozenset(flow["protected_roles"]),
        )
        if carried is not None:
            return record
    return None


def _carries_to_write(ws: Any, state: Any, view: dict[str, Any]) -> list[dict[str, Any]]:
    """The carries the current subject still needs: one per excused role with no carry yet."""
    flow, review = view["flow"], view["review_subject"]
    if flow is None or review is None or not flow["excused_roles"] or flow["anchor_round"] is None:
        return []
    store = ws.open_evidence()
    reports = store.get_semantic_records("review-report.v1")
    carries = store.get_semantic_records("review-carry.v1")
    policy = _review.current_policy(ws, state, view["selection"]["key"])
    fp = review["review_subject_fingerprint"]
    have = {c["role"] for c in carries if c.get("review_subject_fingerprint") == fp}
    pending = {
        d["role"]
        for d in view["review"]["obligations"]
        if d["decision"] == "mandatory-report-unsatisfied"
    }
    records = []
    for role in flow["excused_roles"]:
        if role not in pending or role in have or role in flow["protected_roles"]:
            continue
        record = _build_carry(
            role, flow=flow, review=review, policy=policy, reports=reports, carries=carries
        )
        if record is not None:
            records.append(record)
    return records


def commit_carries(ws: Any, state: Any) -> None:
    """Write one ``review-carry.v1`` per excused role as one supervisor ``review`` step."""
    view = readiness(ws, state)
    records = _carries_to_write(ws, state, view)
    if not records:
        raise Refusal("no-progress", "skill maintainer", "no review carry is due")
    review = view["review_subject"]
    fingerprint = review["delivery_subject_ref"]["acceptance_fingerprint"]
    ids = hashlib.sha256("\0".join(sorted(r["carry_id"] for r in records)).encode()).hexdigest()
    step = f"carry:{review['review_subject_fingerprint'][-24:]}:{ids[:16]}"

    def write(store: Any, issuer: Any, grant: Any, sink: Any) -> None:
        for record in records:
            store.append_semantic_records(
                [record],
                transaction_id=f"tx:{step}:{record['role']}",
                acceptance_fingerprint=fingerprint,
                issuer=issuer,
                grant=grant,
                audit_sink=sink,
            )

    try:
        evidence = ws.evidence_append(writer=write)
    except Exception as exc:  # noqa: BLE001 - every review-record refusal names its own code
        code = getattr(exc, "denial_code", None) or type(exc).__name__
        raise Refusal("review-record-refused", "controller", str(code)) from exc
    ws.git.build_commit(
        run_id=state.run_id,
        step=step,
        operation="review",
        appends={"evidence.jsonl": evidence},
        summary="record review carries",
        known_steps=state.steps,
    )


def readiness(ws: Any, state: Any) -> dict[str, Any]:
    """Readiness from the approval pair, criteria verdicts, and review readiness."""
    subject = delivery_subject(ws, state)
    fingerprint = subject["acceptance_fingerprint"]
    ids = criteria(ws)
    store = ws.open_evidence()
    verdicts = store.evaluate_verdicts(
        _properties(state, ids), fingerprint, sibling("_acceptance.py")
    )
    by_criterion = {ac: v["verdict"] for ac, v in zip(ids, verdicts, strict=True)}
    gated = any(
        r["acceptance_fingerprint"] == fingerprint and r["observation"]["type"] == "gate"
        for r in state.receipts
    )
    gates_failed = any(
        r["acceptance_fingerprint"] == fingerprint and r["lineage"]["criterion_ref"] == GATES_RUN
        for r in state.receipts
    )
    changes = changed_files(ws, state)
    rules = _review.load_rules()
    selection = _review.selection_status(
        ws,
        rules,
        _review.selection_key(subject["acceptance_fingerprint"], [c["path"] for c in changes]),
    )
    review: dict[str, Any] | None
    flow: dict[str, Any] | None = None
    if selection.required:
        # No usable record: nothing is eligible until the controller selects.
        review = None
        review_state: dict[str, Any] = {
            "acceptance_eligible": False,
            "obligations": [],
            "open_findings": [],
        }
    else:
        policy = _review.resolve_policy(rules, selection.latest)
        review = review_subject(ws, state, subject, policy, changes)
        flow = review_flow(ws, state, store, rules, selection, policy, review, subject, changes)
        carrying = bool(flow["excused_roles"]) and flow["classifier_digest"] is not None
        review_state = sibling("_review_disposition.py").review_readiness(
            store,
            review_subject=review,
            review_policy=policy,
            carry_tier=flow["tier"] if carrying else None,
            classifier_digest=flow["classifier_digest"] if carrying else None,
            protected_roles=frozenset(flow["protected_roles"]),
        )
    supported = all(v == "supported" for v in by_criterion.values())
    return {
        "ready": supported and not gates_failed and bool(review_state["acceptance_eligible"]),
        "gates_failed": gates_failed,
        "acceptance_fingerprint": fingerprint,
        "criteria": by_criterion,
        "gates_ran_for_subject": gated,
        "review_subject": review,
        "review": review_state,
        "flow": flow,
        "selection": {
            "key": selection.key,
            "required": selection.required,
            "sequence": selection.sequence,
            "candidates": _review.candidates(rules),
            "changed_files": changes,
        },
    }


def readiness_action(ws: Any, state: Any) -> Any:
    """Evidence, review, or repair work while the run is not ready; None when ready."""
    view = readiness(ws, state)
    if view["ready"]:
        return None
    fingerprint = view["acceptance_fingerprint"]
    if view["gates_failed"]:
        return _loop.Action(
            "request",
            _loop.human_decision(
                ws,
                state,
                "gates-failed",
                "Gates failed on this product without naming a criterion. Replan repair work.",
                key=fingerprint,
            ),
        )
    unsupported = sorted(ac for ac, v in view["criteria"].items() if v != "supported")
    if unsupported:
        if not view["gates_ran_for_subject"]:
            return _loop.Action(
                "request",
                _loop.make_request(
                    ws,
                    state,
                    "run-gates",
                    f"gates:{fingerprint[:24]}",
                    acceptance_fingerprint=fingerprint,
                    criteria=list(view["criteria"]),
                ),
            )
        return _loop.Action(
            "request",
            _loop.human_decision(
                ws,
                state,
                "criteria-unsupported",
                "Gates ran on this product and these criteria are not supported: "
                + ", ".join(unsupported)
                + ". Replan repair work or amend the spec.",
                key=fingerprint,
            ),
        )
    selection = view["selection"]
    if selection["required"]:
        return _loop.Action("request", _selection_request(ws, state, view))
    review = view["review_subject"]
    subject_fp = review["review_subject_fingerprint"]
    reports = ws.open_evidence().get_semantic_records("review-report.v1")
    flow = view["flow"]
    if _carries_to_write(ws, state, view):
        # The supervisor writes the carries itself before it asks anyone for anything.
        return _loop.Action("review-carry")
    for decision in view["review"]["obligations"]:
        role = decision["role"]
        if decision["decision"] == "mandatory-report-unsatisfied":
            sequence = 1 + sum(
                1
                for r in reports
                if r["role"] == role and r["subject"]["review_subject_fingerprint"] == subject_fp
            )
            # A delta pass names the anchor result and the role's open findings; a protected
            # role and every role under `full` is asked for the whole change.
            delta: dict[str, Any] = {}
            if role in flow["delta"] and role not in flow["protected_roles"]:
                delta = {
                    "delta_base": flow["delta_base"],
                    "repair_finding_ids": flow["delta"][role],
                }
            return _loop.Action(
                "request",
                _loop.make_request(
                    ws,
                    state,
                    "review-role",
                    f"review:{role}:{subject_fp[-24:]}:{sequence}",
                    role=role,
                    review_subject_fingerprint=subject_fp,
                    review_subject=review,
                    **delta,
                ),
            )
        if decision["decision"] == "finding-assessment-required":
            assessed = {
                (a["report_id"], a["finding_id"])
                for a in ws.open_evidence().get_semantic_records("finding-assessment.v1")
                if a["assessment"] != "indeterminate"
            }
            current = _current_report(reports, role, subject_fp)
            for finding in current["findings"] if current else []:
                if (current["report_id"], finding["finding_id"]) not in assessed:
                    return _loop.Action(
                        "request",
                        _loop.make_request(
                            ws,
                            state,
                            "assess-finding",
                            f"assess:{current['report_id']}:{finding['finding_id']}",
                            role=role,
                            review_subject_fingerprint=subject_fp,
                            report_id=current["report_id"],
                            finding_id=finding["finding_id"],
                        ),
                    )
    capped = _cap_action(ws, state, view)
    if capped is not None:
        return capped
    open_ids = sorted({f["finding_id"] for f in view["review"]["open_findings"]})
    return _loop.Action(
        "request",
        _loop.human_decision(
            ws,
            state,
            "review-not-eligible",
            "Review readiness is not acceptance eligible: a supported finding is open or an "
            "obligation cannot be decided"
            + (f" (open findings: {', '.join(open_ids)})" if open_ids else "")
            + ". Replan repair work, answer accept-risk with a risk-owner authority "
            "reference and the finding ids to accept, or answer reselect-review with an "
            "owner authority reference to choose the reviewers again.",
            key=subject_fp,
            selection_key=selection["key"],
        ),
    )


def _cap_action(ws: Any, state: Any, view: dict[str, Any]) -> Any:
    """The ``review-cap`` decision, or ``None`` when the cap does not apply or cannot be shown.

    It applies to an unprotected unit whose round count reached the cap with a supported
    material finding still open. Findings show only as supervisor-derived references; when
    two share one, or one cannot be tied to its report, nothing is shown and the caller
    issues ``review-not-eligible`` with every finding left open.
    """
    flow = view["flow"]
    if flow["protection_unknown"] or flow["protected_classes"]:
        return None
    if not view["review"]["open_findings"] or flow["round_count"] < flow["round_cap"]:
        return None
    pairs = open_finding_pairs(ws, view)
    refs = [_review.cap_ref(p["report_id"], p["finding_id"]) for p in pairs]
    if (
        not pairs
        or len(pairs) < len(view["review"]["open_findings"])
        or len(set(refs)) != len(refs)
        or any(p["role"] not in flow["roles"] for p in pairs)
    ):
        return None
    positions = _report_positions(ws)
    entries = [
        {"cap_ref": ref, "role": p["role"], "evidence_sequence": positions[p["report_id"]]}
        for ref, p in zip(refs, pairs, strict=True)
    ]
    question = (
        f"The review ran {flow['round_count']} rounds and the cap is {flow['round_cap']}, "
        f"with {len(entries)} supported material findings still open; open_findings lists "
        "each by its reference, role, and evidence-log position. Answer accept-risk with a "
        "risk-owner authority reference and the references to accept, extend-review with an "
        "owner authority reference to allow one more round, or reselect-review with an owner "
        "authority reference and the selection key to choose the reviewers again."
    )
    return _loop.Action(
        "request",
        _loop.review_cap_decision(
            ws,
            state,
            question,
            round_count=flow["round_count"],
            selection_key=view["selection"]["key"],
            answered=flow["answered_caps"],
            open_findings=entries,
        ),
    )


def _trailer_text(text: str) -> str:
    """*text* as one safe trailer value: printable ASCII, no leading space, bounded."""
    return re.sub(r"[^\x20-\x7e]", "?", text).strip()[:200]


def _anchor_line(
    ws: Any, state: Any, view: dict[str, Any], role: str, report: dict[str, Any]
) -> tuple[dict[str, Any] | None, str]:
    """``(anchor-facts line, why none)`` for the line this report completes.

    An anchor round is a round on whose subject every selected role has returned a report.
    A line is returned only when ``parse_anchors`` accepts it, so a line the parser would
    refuse never reaches the ledger. A failure to build or validate the facts records no
    line, so the next subject classifies ``full``, and *why* names the failure; the caller
    carries it as a trailer for ``status`` to show. A round that is not an anchor round
    returns an empty *why*.
    """
    flow, review = view["flow"], view["review_subject"]
    fp = review["review_subject_fingerprint"]
    unusable = ("unable", "indeterminate")
    if flow is None or not flow["current_is_round"] or report.get("terminal_status") in unusable:
        return None, ""
    if any(a["review_subject_fingerprint"] == fp for a in _review.anchor_records(ws)):
        return None, ""
    reported = {
        r["role"]
        for r in ws.open_evidence().get_semantic_records("review-report.v1")
        if r["subject"]["review_subject_fingerprint"] == fp
        and r.get("terminal_status") not in unusable
    } | {role}
    if not set(flow["roles"]) <= reported:
        return None, ""
    result = result_lineage(ws, state)[1]
    try:
        line = _review.anchor_record(
            ws.git,
            run_id=state.run_id,
            round_number=flow["rounds_with_current"],
            review_subject_fingerprint=fp,
            review_policy_fingerprint=review["review_policy_fingerprint"],
            anchor_result=result,
            run_base=run_base(ws, state, result),
            changed_paths=[c["path"] for c in view["selection"]["changed_files"]],
        )
        _review.parse_anchors(_admission.canonical_line(line))
    except Exception as exc:  # noqa: BLE001 - no anchor line only lowers what a later tier can save
        code = getattr(exc, "code", None) or getattr(exc, "detail", None)
        note = f" ({code})" if code else ""
        return None, _trailer_text(f"the anchor line was not recorded: {type(exc).__name__}{note}")
    return line, ""


def _selection_request(ws: Any, state: Any, view: dict[str, Any]) -> dict[str, Any]:
    """The ``review-role`` request asking the controller to select reviewers."""
    selection = view["selection"]
    # The subject lists the changed paths the controller selects from; its policy
    # fingerprint is a placeholder until a selection resolves one.
    pending = sibling("_review_selection.py").project_review_subject(
        delivery_subject(ws, state),
        changed_paths=selection["changed_files"],
        review_policy_fingerprint="review-selection-pending",
    )
    return _loop.make_request(
        ws,
        state,
        "review-role",
        f"select:{selection['key'][:24]}:{selection['sequence']}",
        candidates=selection["candidates"],
        selection_key=selection["key"],
        review_subject_fingerprint=pending["review_subject_fingerprint"],
        review_subject=pending,
    )


def _current_report(
    reports: list[dict[str, Any]], role: str, subject_fp: str
) -> dict[str, Any] | None:
    matching = [
        r
        for r in reports
        if r["role"] == role and r["subject"]["review_subject_fingerprint"] == subject_fp
    ]
    return max(matching, key=lambda r: r["lineage"]["sequence"]) if matching else None


def report_readiness(ws: Any, state: Any, request: dict[str, Any], result: dict[str, Any]) -> str:
    """Admit a run-gates, review-role, or assess-finding result as one supervisor step."""
    step = request["request_id"]
    view = readiness(ws, state)
    fingerprint = view["acceptance_fingerprint"]
    if request["kind"] == "run-gates":
        gate = result.get("gate")
        rows = result.get("criteria")
        if (
            not isinstance(gate, dict)
            or not isinstance(gate.get("passed"), bool)
            or not isinstance(rows, list)
        ):
            raise Refusal(
                "invalid-result", "controller", "a run-gates result needs gate and criteria"
            )
        unattributed = not gate["passed"] and all(
            isinstance(row, dict) and row.get("outcome") == "pass" for row in rows
        )
        wanted = set(request["criteria"])
        receipts = []
        for row in rows:
            if (
                not isinstance(row, dict)
                or row.get("criterion_ref") not in wanted
                or row.get("outcome") not in ("pass", "fail")
            ):
                raise Refusal("invalid-result", "controller", "a criterion row is malformed")
            ac, outcome = row["criterion_ref"], row["outcome"]
            term = f"criterion:{ac}" if outcome == "pass" else f"criterion-fail:{ac}"
            receipts.append(
                _loop.receipt(
                    state,
                    step,
                    criterion=ac,
                    term=term,
                    observation="gate",
                    outcome=outcome,
                    fingerprint=fingerprint,
                )
            )
        if unattributed:
            # Gates failed without naming a criterion (a lint or typecheck, say):
            # recorded for the run so readiness asks for repair work.
            receipts.append(
                _loop.receipt(
                    state,
                    step,
                    criterion=GATES_RUN,
                    term="gates-failed",
                    observation="gate",
                    outcome="fail",
                    fingerprint=fingerprint,
                )
            )
        if not receipts:
            raise Refusal("invalid-result", "controller", "a run-gates result names no criterion")
        evidence = ws.evidence_append(receipts)
        ws.git.build_commit(
            run_id=state.run_id,
            step=step,
            operation="evidence",
            appends={"evidence.jsonl": evidence},
            summary="record gate evidence",
            known_steps=state.steps,
        )
        return "evidence"
    if request["kind"] == "review-role" and "candidates" in request:
        return _report_selection(ws, state, request, result, view)
    persistence = sibling("_review_persistence.py")
    bridge = sibling("_review_bridge.py")
    if request["kind"] == "review-role":
        if "selection" in result:
            raise Refusal(
                "invalid-result", "controller", "this request takes a report, not a selection"
            )
        report = result.get("report")
        if not isinstance(report, dict) or report.get("role") != request["role"]:
            raise Refusal(
                "invalid-result", "controller", "the report is not for the requested role"
            )

        def write_report(store: Any, issuer: Any, grant: Any, sink: Any) -> None:
            persistence.append_current_review_report(
                store,
                report,
                transaction_id=f"tx:{step}",
                expected_subject=view["review_subject"],
                issuer=issuer,
                grant=grant,
                audit_sink=sink,
            )
            _review.record_dispositions(
                ws, state, store, issuer, sink, subject=view["review_subject"], step=step
            )

        writer = write_report
    else:
        assessment = result.get("assessment")
        if (
            not isinstance(assessment, dict)
            or assessment.get("report_id") != request["report_id"]
            or assessment.get("finding_id") != request["finding_id"]
        ):
            raise Refusal("invalid-result", "controller", "the assessment is not for the request")
        denial = sibling("_review_assessment.py").check_proof_by_run(
            assessment, result_lineage(ws, state)[1]
        )
        if denial is not None:
            raise Refusal("review-record-refused", "controller", denial)
        reports = ws.open_evidence().get_semantic_records("review-report.v1")
        source = next(r for r in reports if r["report_id"] == request["report_id"])
        finding = next(f for f in source["findings"] if f["finding_id"] == request["finding_id"])

        def write_assessment(store: Any, issuer: Any, grant: Any, sink: Any) -> None:
            bridge.append_finding_assessment_bridge(
                store,
                assessment,
                report_id=request["report_id"],
                finding=finding,
                affected_criteria=list(finding.get("affected_acceptance_criteria", [])),
                transaction_id=f"tx:{step}",
                acceptance_fingerprint=fingerprint,
                issuer=issuer,
                grant=grant,
                audit_sink=sink,
            )
            _review.record_dispositions(
                ws, state, store, issuer, sink, subject=view["review_subject"], step=step
            )

        writer = write_assessment
    try:
        evidence = ws.evidence_append(writer=writer)
    except Exception as exc:  # noqa: BLE001 - every review-record refusal names its own code
        code = getattr(exc, "denial_code", None) or type(exc).__name__
        raise Refusal("review-record-refused", "controller", str(code)) from exc
    appends = {"evidence.jsonl": evidence}
    trailers: dict[str, str] = {}
    if request["kind"] == "review-role":
        line, skipped = _anchor_line(ws, state, view, request["role"], report)
        if line is not None:
            appends[_review.ANCHORS_FILE] = _admission.canonical_line(line)
        elif skipped:
            trailers["Supervisor-Anchor-Skipped"] = skipped
    ws.git.build_commit(
        run_id=state.run_id,
        step=step,
        operation="review",
        trailers=trailers or None,
        appends=appends,
        summary=f"record {request['kind']}",
        known_steps=state.steps,
    )
    return "review"


def _report_selection(
    ws: Any, state: Any, request: dict[str, Any], result: dict[str, Any], view: dict[str, Any]
) -> str:
    """Admit a selection result as one ``review`` step appending ``review-selections.jsonl``."""
    if "report" in result or not isinstance(result.get("selection"), dict):
        raise Refusal("invalid-result", "controller", "a selection request takes a selection")
    rules = _review.load_rules()
    status = _review.selection_status(ws, rules, request["selection_key"])
    record = _review.admit_selection(rules, status, result["selection"])
    ws.git.build_commit(
        run_id=state.run_id,
        step=request["request_id"],
        operation="review",
        appends={_review.SELECTIONS_FILE: _admission.canonical_line(record)},
        summary="record review selection",
        known_steps=state.steps,
    )
    return "review"
