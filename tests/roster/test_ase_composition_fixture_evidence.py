"""The composition-fixture grading evidence agrees with what it was taken from.

Repository-level rather than pack-level on purpose. These guards read three
things outside `packs/agent-skill-engineering`: the frozen spec and its
verification ledger under `docs/specs/`, the retained graded transcripts beside
them, and the eval declarations as they stood at the slice's base commit, which
means running `git show` from the repository root. The pack-test boundary lint
refuses a pack test that reaches outside its own pack, and it is right to —
`packs/.../tests/skills/author_or_update/test_contract.py` keeps every path it
opens statically confined to its own pack, and these guards cannot.

That confinement rule is also why the declaration-driven payload checks live
here. They join a path read from `evals.json` at runtime, so no static reading
can prove the result stays inside the pack; the join is checked for containment
at runtime instead, which is a repository-level guarantee rather than a
pack-local one.

What stays in the pack suite is everything answerable from pack-local literals.
The split is by what a guard has to read, not by which acceptance criterion it
serves — several criteria are covered from both sides.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACK_ROOT = ROOT / "packs" / "agent-skill-engineering"
AUTHOR_ROOT = PACK_ROOT / ".apm" / "skills" / "author-or-update-agent-skill"
AUTHOR_DECL_REPO_PATH = (
    "packs/agent-skill-engineering/.apm/skills/author-or-update-agent-skill"
    "/evals/evals.json"
)
SPEC_DIR = ROOT / "docs" / "specs" / "agent-skill-engineering-composition-fixtures"
TRANSCRIPT_ROOT = SPEC_DIR / "notes" / "transcripts"
BASE_COMMIT = "d44484b29d1ba0f56cb0baf42fd79b1348e26a58"
COMPOSITION_CASES = ("subagent-composition", "hook-plugin-design")
# The inherited case whose shape the two new ones share: read-only framing over
# a payload the case supplies. Its marker set is what they must equal.
MARKER_SIBLING = "pytest-suite"


def _declared_cases() -> dict[str, dict]:
    payload = json.loads(
        (AUTHOR_ROOT / "evals" / "evals.json").read_text(encoding="utf-8")
    )
    return {case["id"]: case for case in payload["evals"]}


def _authoring_records() -> dict[str, dict]:
    """Authoring records by id, with duplicate ids refused before collapsing.

    Indexing by `eval_id` is last-wins, so without this a repeated id hides the
    shadowed record from every per-record guard here while an id-set equality
    stays green, because it compares keys. The reachable path is a re-measured
    round appended rather than replacing its predecessor.

    The admitted id set is derived from the declarations rather than restated:
    a second hand-written copy of the pack suite's pinned enumeration is a
    thing that can drift away from it silently.
    """
    declared = set(_declared_cases())
    evidence = json.loads(
        (PACK_ROOT / "tests" / "fixtures" / "behavior-results.json").read_text(
            encoding="utf-8"
        )
    )
    rows = [r for r in evidence["results"] if r["eval_id"] in declared]
    ids = [r["eval_id"] for r in rows]
    assert len(ids) == len(set(ids)), sorted(
        i for i in set(ids) if ids.count(i) > 1
    )
    return {r["eval_id"]: r for r in rows}


def _at_base(repo_relative_path: str) -> str:
    """Read a tracked file as of the slice's base commit.

    The seam in front of git: one subprocess per path, so the suite's cost stays
    in assertions rather than processes, and no test shells out ad hoc.
    """
    return subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{repo_relative_path}"],
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    ).stdout


def _base_cases() -> dict[str, dict]:
    payload = json.loads(_at_base(AUTHOR_DECL_REPO_PATH))
    return {case["id"]: case for case in payload["evals"]}


def test_the_base_commit_matches_the_one_the_ledger_records() -> None:
    """`BASE_COMMIT` is bound to the recorded base, not merely declared.

    Three guards read their comparison set from this commit — the declared-case
    set, the sibling marker set, and the base payload digests. Point it at HEAD
    and none of them reddens: the case-set equality becomes `current == current`
    plus the two new ids, the sibling is compared with itself, and the payload
    digests are the ones the change under test just wrote. Every "before this
    slice" comparison silently becomes a current-tree comparison.

    That is not a sabotage path, it is the cheap repair: the next slice to add
    an eval case reddens the case-set equality, and bumping this constant is the
    first thing that makes it green again. Binding it to the ledger means doing
    so also has to move the recorded base, which is a visible act.
    """
    ledger = (SPEC_DIR / "notes" / "verification-ledger.md").read_text(encoding="utf-8")
    recorded = re.search(r"\*\*Base commit:\*\*\s*`([0-9a-f]{40})`", ledger)
    assert recorded, "the verification ledger records no base commit"
    assert BASE_COMMIT == recorded.group(1), (
        f"BASE_COMMIT is {BASE_COMMIT} but the ledger records "
        f"{recorded.group(1)}. Moving the base is a re-measurement, not a "
        "constant bump: change the ledger's recorded base and re-take the "
        "comparisons, or leave both alone."
    )


def test_the_marker_sibling_is_the_one_ac5_names() -> None:
    """`MARKER_SIBLING` is bound to AC5's text, not merely declared.

    AC5 does not say "compare with some inherited sibling", it names one. Both
    limbs of the guard read through this constant, so the constant decides what
    the criterion enforces. Five inherited cases declare the identical marker
    pair today, which is what makes the cheap repair cheap: when a later slice
    moves `pytest-suite`'s declared markers, the guard reddens on its own
    sibling-unmoved limb, and retargeting this one token to any of those five
    turns it green while AC5's second limb goes unenforced.

    Binding it to the frozen criterion means that repair has to move a shipped
    acceptance criterion instead, which is a visible act — the same reason
    `BASE_COMMIT` is bound to the ledger.
    """
    spec = (SPEC_DIR / "spec.md").read_text(encoding="utf-8")
    block = re.search(
        r"\*\*AC5 —.*?(?=\n- \[[ x]\] \*\*AC6 —)", spec, re.DOTALL
    )
    assert block, "spec.md has no AC5 block to read the sibling from"
    # Filtered against the live declarations rather than a restated id set:
    # a second hand-written copy of the pack suite's pinned enumeration is a
    # thing that can drift away from it silently.
    declared = set(_declared_cases())
    named = {
        token
        for token in re.findall(r"`([^`]+)`", block.group(0))
        if token in declared
    }
    assert named == {MARKER_SIBLING}, (
        f"MARKER_SIBLING is {MARKER_SIBLING!r} but AC5 names {sorted(named)}. "
        "Retargeting the comparison sibling is a change to a shipped "
        "criterion: move AC5 and re-take the comparison, or leave both alone."
    )


def test_the_declared_case_set_gains_exactly_the_two_new_ids() -> None:
    """AC3: the set is the base set plus these two, with nothing else moved."""
    assert set(_declared_cases()) == set(_base_cases()) | set(COMPOSITION_CASES)


def test_composition_cases_reuse_the_sibling_marker_set() -> None:
    """AC5: equality with one named sibling, read at base, sibling unmoved.

    Containment in the union of base declarations is the weaker check this
    replaces: that union spans modes and authorization states, so it admits
    `Mode: knowledge-provider` and `Write status: awaiting explicit
    authorization`, neither of which a read-only framing case produces.
    """
    cases = _declared_cases()
    base = _base_cases()
    sibling = set(base[MARKER_SIBLING]["expect"]["output_contains"])
    assert set(cases[MARKER_SIBLING]["expect"]["output_contains"]) == sibling
    for case_id in COMPOSITION_CASES:
        assert set(cases[case_id]["expect"]["output_contains"]) == sibling, case_id


def test_each_composition_case_names_its_own_payload() -> None:
    """AC2: each new case's payloads resolve, and no other case shares them.

    Scoped to the two new cases, which is what the criterion constrains. Global
    pairwise distinctness would be wrong: `update-existing-skill` and
    `cross-session-resumption` deliberately share one inherited payload, and
    this slice does not own that decision.
    """
    cases = _declared_cases()
    root = AUTHOR_ROOT.resolve()
    others = {
        (AUTHOR_ROOT / declared).resolve()
        for case_id, case in cases.items()
        if case_id not in COMPOSITION_CASES
        for declared in case.get("files") or ()
    }
    claimed: dict[Path, str] = {}
    for case_id in COMPOSITION_CASES:
        for declared in cases[case_id]["files"]:
            resolved = (AUTHOR_ROOT / declared).resolve()
            assert resolved.is_file(), (case_id, declared)
            # Canonical containment, not string prefixing: `..` rejection does
            # not stop an in-boundary symlink escape.
            assert root in resolved.parents, (case_id, declared)
            assert resolved not in others, (case_id, declared)
            assert resolved not in claimed, (case_id, claimed.get(resolved))
            claimed[resolved] = case_id


def test_composition_payloads_are_distinct_non_empty_drafts() -> None:
    """AC8: neither payload is empty, a copy of the other, or a base payload."""
    # Derived from the base declarations, not a hand-written name list. The
    # tuple that used to sit here was an unpinned anchor of the same class as
    # `BASE_COMMIT`: empty it and this set is empty, so the "not a copy of a
    # base payload" limb below is vacuously true and a new payload could
    # duplicate an inherited one undetected. `_base_cases()` reads the
    # declarations at the base commit, so the membership list can no longer be
    # narrowed from the working tree.
    skill_root_at_base = AUTHOR_DECL_REPO_PATH.rsplit("/", 2)[0]
    base_payload_paths = {
        declared
        for case in _base_cases().values()
        for declared in (case.get("files") or ())
    }
    assert base_payload_paths, "the base declarations name no payloads"
    base_payloads = {
        hashlib.sha256(
            _at_base(f"{skill_root_at_base}/{declared}").encode("utf-8")
        ).hexdigest()
        for declared in base_payload_paths
    }
    digests = {}
    cases = _declared_cases()
    for case_id in COMPOSITION_CASES:
        # From the declaration the case actually carries. Deriving the path from
        # the case id instead lets the two `files` values be swapped while this
        # guard goes on hashing the by-name files and stays green.
        declared = cases[case_id]["files"]
        assert len(declared) == 1, (case_id, declared)
        path = AUTHOR_ROOT / declared[0]
        raw = path.read_bytes()
        assert raw.strip(), case_id
        digest = hashlib.sha256(raw).hexdigest()
        assert digest not in base_payloads, case_id
        assert digest not in digests, (case_id, digests.get(digest))
        digests[digest] = case_id


def test_every_verdict_is_readable_against_its_own_transcript() -> None:
    """AC9: the transcript is the falsifier, not the record's own account.

    Comparing `actual_markers` to the declaration is a mirror — both sides come
    from the same file. This binds each record to bytes in the tree: the digest
    must recompute, and every declared marker must occur in the response those
    bytes hold. A fabricated record has to produce a transcript that satisfies
    both.
    """
    cases = _declared_cases()
    for eval_id, record in _authoring_records().items():
        transcript = SPEC_DIR / record["transcript"]
        resolved = transcript.resolve()
        assert resolved.is_file(), (eval_id, record["transcript"])
        # Deliberately narrower than AC9, which admits any path under the
        # spec's `notes/`. This guard and the AC17 scrub root both enforce
        # `notes/transcripts/`, so every cited transcript stays inside the only
        # root that scrubs it. The narrowing is fail-closed — it can reject a
        # conforming transcript, never admit a non-conforming one — and it is
        # recorded as a divergence in the slice's verification ledger under
        # "Recorded divergence — the transcript boundary". Do not read this as
        # the three naming one directory; that claim was withdrawn there.
        assert TRANSCRIPT_ROOT.resolve() in resolved.parents, (
            eval_id,
            record["transcript"],
            "transcripts must live under notes/transcripts/",
        )
        digest = "sha256:" + hashlib.sha256(resolved.read_bytes()).hexdigest()
        assert digest == record["captured_response_sha256"], eval_id
        body = resolved.read_text(encoding="utf-8")
        for marker in cases[eval_id]["expect"]["output_contains"]:
            assert marker in body, (eval_id, marker)


def test_authoring_transcripts_are_one_per_record() -> None:
    """AC9: no two records may rest on one transcript.

    Compared on resolved canonical targets rather than on the recorded strings,
    because two distinct paths under `notes/` — one a symlink — satisfy a string
    comparison while a single transcript backs both records.
    """
    records = _authoring_records()
    resolved = {
        eval_id: (SPEC_DIR / r["transcript"]).resolve()
        for eval_id, r in records.items()
    }
    assert len(set(resolved.values())) == len(resolved), sorted(resolved.items())


def _host_identifying_patterns() -> tuple[re.Pattern[str], ...]:
    """The pack suite's host-identity patterns, loaded from their one home.

    Restated here the patterns would be a second copy that drifts: the pack
    scan could gain a form and this one would keep passing the transcripts
    against the old list. Loading the module under a unique name is the
    repository's idiom for reading a suite's constants from another tree, and
    it keeps the pattern set single-sourced.
    """
    path = PACK_ROOT / "tests" / "pack" / "test_corpus_admission.py"
    spec = importlib.util.spec_from_file_location(
        "ase_pack_corpus_admission_for_roster", path
    )
    assert spec and spec.loader, path
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    patterns = tuple(
        re.compile(pattern, re.IGNORECASE)
        for pattern in module.HOST_IDENTIFYING_PATTERN_STRINGS
    )
    assert patterns, "the pack suite declares no host-identifying patterns"
    return patterns


def test_retained_transcripts_carry_no_host_identifying_data() -> None:
    """AC17: raw captured output holds no absolute path, host name or account.

    This root moved out of the pack suite's six-root scan when the pack-test
    boundary lint refused it: the transcripts are slice evidence under
    `docs/specs/`, not pack content, so a pack test may not reach them. The
    property is unchanged and so are the patterns, which are read from the
    pack suite rather than restated.

    Every regular file, not `*.md`. The evidence guard admits any regular file
    under this root, so a suffix filter would leave a `.txt` transcript cited
    as evidence and never scanned while the ten Markdown fixtures keep the
    floor green.
    """
    patterns = _host_identifying_patterns()
    paths = sorted(path for path in TRANSCRIPT_ROOT.rglob("*") if path.is_file())
    # A floor, so a repointed or emptied root fails instead of passing on an
    # empty walk, and an independently written expected location, so the walk
    # and its containment check are not one constant.
    assert len(paths) >= 10, len(paths)
    expected_root = SPEC_DIR.joinpath("notes/transcripts").resolve(strict=True)
    for path in paths:
        # Canonical containment before the read, and the read on the resolved
        # path. `rglob` selects with `is_file()`, which follows links, so a
        # symlink committed here would otherwise pass a lexical parent check
        # while the scan reads a file outside the root entirely -- and the
        # bytes actually committed, the link target, would never be scanned.
        assert not path.is_symlink(), (str(path), "symlink")
        resolved = path.resolve(strict=True)
        assert resolved.is_file(), (str(path), "not a regular file")
        assert expected_root in resolved.parents, (str(path), str(resolved))
        text = resolved.read_text(encoding="utf-8", errors="strict")
        for pattern in patterns:
            hit = pattern.search(text)
            assert hit is None, (str(path), pattern.pattern, hit.group(0))
