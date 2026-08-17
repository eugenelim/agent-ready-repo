#!/usr/bin/env python3
"""Self-checks for the pre-change golden fixtures (spec/work-loop-in-process-guards T0).

These do not test the guard extraction — T1a/T1b/T6 do that. They test the
*fixtures*, because a golden that is stale, self-contradicting, or silently
relaxed is worse than no golden: it reads as coverage while asserting nothing.

Four properties, each guarding a specific way this apparatus could rot:

1. **The corpus still covers the shapes it was chosen for.** `canonical_contract`'s
   own comments name the cases that historically broke it, and three are
   near-unique in the repository (one odd-fence file, two bold-lead-in specs,
   four checkbox plans) and one — a lowercase-`c` heading — does not occur at all
   and is hand-authored. A corpus that quietly loses one stops exercising the
   normalization. Line endings are NOT a corpus shape: see
   `test_canonical_contract_folds_line_endings` for why a committed CRLF fixture
   is both impossible here and unable to fail.

2. **The normalizer is idempotent.** A non-idempotent normalizer would mask a real
   difference on the second pass.

3. **`after` is present iff a `change_reason` is declared, from a closed set.**
   This is what stops a future failure being "fixed" by pasting a new expected
   value into the golden.

4. **Preserved-behavior rows really are clean.** One line of stderr, no traceback,
   no non-zero exit with an empty message. A row whose *verdict is changing* is
   exempt — that is the point of `change_reason` — so this cannot enshrine a
   pre-existing traceback as expected behavior, which the exemption would
   otherwise permit.

Run with pytest.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import golden_support as gs
import pytest

# ── loading ────────────────────────────────────────────────────────────────


def _load(path: Path) -> dict:
    if not path.is_file():
        pytest.fail(
            f"{path.name} is missing. It is generated once, before the guard "
            "extraction, by docs/specs/work-loop-in-process-guards/notes/"
            "generate_goldens.py — and deliberately never regenerated after."
        )
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def digests() -> dict:
    return _load(gs.GOLDEN_DIGESTS)["digests"]


@pytest.fixture(scope="module")
def rows() -> list[dict]:
    return _load(gs.GOLDEN_CLI_STREAMS)["rows"]


# ── 1. corpus shape coverage ───────────────────────────────────────────────

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def test_corpus_is_present_and_named_for_the_hashing_split() -> None:
    """Entries keep `spec.md` / `plan.md` filenames, because the hash depends on them.

    `sha256_canonical_contract` selects `ac_section_only=(path.name != "plan.md")`,
    so flattening the corpus to `001-foo.md` would silently hash every plan as if
    it were a spec — the fixture would still be self-consistent and would still be
    testing the wrong thing.
    """
    entries = gs.corpus_entries()
    assert entries, f"no corpus artifacts under {gs.CORPUS}"
    assert {p.name for p in entries} <= {"spec.md", "plan.md"}
    assert sum(1 for p in entries if p.name == "spec.md") >= 20
    assert sum(1 for p in entries if p.name == "plan.md") >= 15


def test_corpus_covers_every_shape_canonical_contract_calls_out() -> None:
    """Each shape `canonical_contract`'s comments name is present at least once."""
    found: dict[str, list[str]] = {k: [] for k in (
        "odd-fence", "ac-bold-lead", "lowercase-ac-heading", "plan-checkbox",
        "multiline-html-comment", "no-status-line", "status-with-free-text",
        "checkbox-outside-ac-section",
    )}
    for path in gs.corpus_entries():
        key = gs.corpus_key(path)
        raw = path.read_bytes()
        text = _read(path)
        if sum(1 for line in text.split("\n") if line.lstrip().startswith("```")) % 2:
            found["odd-fence"].append(key)
        if re.search(r"^ {0,3}\*\*Acceptance", text, re.M):
            found["ac-bold-lead"].append(key)
        if re.search(r"^#{2,3} +acceptance criteria", text, re.M):
            found["lowercase-ac-heading"].append(key)
        if path.name == "plan.md" and re.search(r"^\s*- \[[ x]\]", text, re.M):
            found["plan-checkbox"].append(key)
        if re.search(r"<!--[^>]*\n", text):
            found["multiline-html-comment"].append(key)
        if "**Status:**" not in text:
            found["no-status-line"].append(key)
        if re.search(r"\*\*Status:\*\*\s*\w+\s+—", text):
            found["status-with-free-text"].append(key)
        # No `crlf-endings` probe on committed bytes: `.gitattributes` pins
        # `* text=auto eol=lf`, so committed CR bytes do not survive the blob.
        # The line-ending path is covered by the synthesized @crlf/@cr digests
        # in test_line_ending_variants_fold_to_the_same_digest below.
        assert b"\r" not in raw, (
            f"{key}: committed CR bytes. `.gitattributes` normalizes them away in "
            "the blob, so a fixture that relies on them would hash differently in a "
            "fresh clone than in this working copy — which is exactly the divergence "
            "this assertion exists to prevent. Synthesize line-ending variants "
            "instead (golden_support.crlf_bytes)."
        )
        if re.search(r"^### Never do\s*\n\s*\n\s*- \[", text, re.M):
            found["checkbox-outside-ac-section"].append(key)

    missing = sorted(k for k, v in found.items() if not v)
    assert not missing, (
        "the frozen corpus no longer covers: " + ", ".join(missing) + ". These are "
        "the shapes canonical_contract's own comments name as historical breakages; "
        "three are near-unique in the tree and two are hand-authored, so they "
        "cannot be recovered by resampling."
    )


def test_every_corpus_artifact_has_a_recorded_digest(digests: dict) -> None:
    keys = {gs.corpus_key(p) for p in gs.corpus_entries()}
    assert keys == set(digests), (
        "corpus and digest fixture disagree; added/removed: "
        f"{sorted(keys ^ set(digests))}"
    )
    for key, value in digests.items():
        assert re.fullmatch(r"[0-9a-f]{64}", value), f"{key}: not a sha256"


def test_canonical_contract_folds_line_endings() -> None:
    """The CRLF/CR fold, tested where it is actually reachable: on strings.

    A digest-level version of this assertion CANNOT FAIL, and that was found by
    mutation rather than by reading. Two independent reasons:

      * `Path.read_text()` decodes with universal newlines, so a CRLF-on-disk
        artifact is already LF by the time `canonical_contract` sees it.
      * `.gitattributes` pins `eol=lf`, so a CRLF fixture cannot even be committed.

    Calling `canonical_contract` directly with CR-bearing text is the only route
    that exercises the fold — and it matters after this change, because
    `read_managed_text` will decode bytes itself rather than going through
    `read_text`, making the fold load-bearing where it is currently redundant.

    Mutation-verified: removing the fold turns this red.
    """
    hasher, canonical = _current_canonical_helpers()
    lf = (
        "# Spec: fold\n\n- **Status:** Shipped\n\n"
        "## Acceptance Criteria\n\n- [x] one\n- [ ] two\n"
    )
    assert canonical(gs.crlf_text(lf)) == canonical(lf), "CRLF is not folded to LF"
    assert canonical(gs.cr_text(lf)) == canonical(lf), "bare CR is not folded to LF"
    # And the fold is not vacuous on the input: the variants really do differ.
    assert gs.crlf_text(lf) != lf and gs.cr_text(lf) != lf


# ── 2. normalizer ──────────────────────────────────────────────────────────

def test_normalize_is_idempotent(rows: list[dict]) -> None:
    for row in rows:
        for stream in ("stdout", "stderr"):
            once = row["before"][stream]
            assert gs.normalize(once) == once, (
                f"{row['key']}/{stream}: normalize is not idempotent, so a second "
                "pass could mask a real difference"
            )


def test_normalize_preserves_distinct_values() -> None:
    """Two different run ids must not collapse to one token.

    A flat `<RUN_ID>` would make `stored='a', expected='b'` byte-identical to a
    message where they matched, so the golden would stop proving the mismatch.
    """
    a, b = "11111111-2222-3333-4444-555555555555", "99999999-8888-7777-6666-555555555555"
    out = gs.normalize(f"stored='{a}', expected='{b}'")
    assert out == "stored='<RUN_ID_1>', expected='<RUN_ID_2>'"
    same = gs.normalize(f"stored='{a}', expected='{a}'")
    assert same == "stored='<RUN_ID_1>', expected='<RUN_ID_1>'"
    assert out != same


def test_normalize_strips_absolute_paths(tmp_path: Path) -> None:
    d = tmp_path / "spec"
    d.mkdir()
    out = gs.normalize(f"cannot read {d}/spec.md", spec_dir=d)
    assert str(d) not in out and out == "cannot read <SPEC_DIR>/spec.md"


# ── 3. the change-reason contract ──────────────────────────────────────────

def test_after_present_iff_change_reason_declared(rows: list[dict]) -> None:
    for row in rows:
        has_after = "after" in row
        has_reason = "change_reason" in row
        assert has_after == has_reason, (
            f"{row['key']}: `after` and `change_reason` must appear together. "
            "An `after` without a declared reason is how a golden gets relaxed to "
            "make a failure go away."
        )
        if has_reason:
            assert row["change_reason"] in gs.CHANGE_REASONS, (
                f"{row['key']}: change_reason {row['change_reason']!r} is not in the "
                f"closed set {sorted(gs.CHANGE_REASONS)}"
            )


def test_declared_change_reasons_are_all_exercised(rows: list[dict]) -> None:
    """Every reason in the closed set is used, and none outside it appears.

    A reason that stops being used means the behavior change it described was
    dropped — which should be a deliberate edit to the set, not silent drift.
    """
    observed = {r["change_reason"] for r in rows if "change_reason" in r}
    assert observed <= gs.CHANGE_REASONS
    unexercised = sorted(gs.CHANGE_REASONS - observed)
    assert not unexercised, (
        f"declared but unexercised change reasons: {unexercised}. Either add rows "
        "for them or remove them from golden_support.CHANGE_REASONS."
    )


def test_changed_rows_flip_a_verdict(rows: list[dict]) -> None:
    """An `after` must actually differ from `before` on the pass/fail verdict."""
    for row in (r for r in rows if "after" in r):
        before_ok = row["before"]["returncode"] == 0
        after_ok = row["after"]["returncode"] == 0
        assert before_ok != after_ok, (
            f"{row['key']}: declares change_reason {row['change_reason']!r} but the "
            "verdict is unchanged — it belongs in the preserved set"
        )


# ── 4. preserved rows are clean ────────────────────────────────────────────

def test_preserved_rows_have_one_line_no_traceback_stderr(rows: list[dict]) -> None:
    """The CLI contract, asserted on the capture itself.

    Rows declaring a `change_reason` are exempt: their pre-change behavior is what
    this change is fixing, so requiring it to be clean would either block the fix
    or force the traceback to be enshrined as expected.
    """
    for row in rows:
        if "change_reason" in row:
            continue
        before = row["before"]
        combined = before["stdout"] + "\n" + before["stderr"]
        assert "Traceback" not in combined, (
            f"{row['key']}: the pre-change CLI produced a traceback. Do not record "
            "it as expected behavior — surface it as a defect, or classify the row "
            "with a change_reason if this change fixes it."
        )
        if before["returncode"] != 0:
            assert before["stderr"], f"{row['key']}: non-zero exit with empty stderr"
            assert len(before["stderr"].split("\n")) == 1, (
                f"{row['key']}: stderr is {len(before['stderr'].split(chr(10)))} lines; "
                "the CLI contract is one line"
            )


def test_all_six_read_only_verbs_are_covered(rows: list[dict]) -> None:
    """Every verb being converted to an adapter has recorded failure branches."""
    prefixes = {
        "identity/": 3,
        "plan-check-current/": 6,
        "schedule-check-current/": 4,
        "check/": 6,
        "wave-check/": 4,
        "check-spec-status/": 5,
    }
    for prefix, minimum in prefixes.items():
        n = sum(1 for r in rows if r["key"].startswith(prefix))
        assert n >= minimum, f"{prefix}: only {n} rows, expected at least {minimum}"
    # Both outcomes for every verb, so no verb is recorded as refuse-only.
    for prefix in prefixes:
        codes = {r["before"]["returncode"] == 0 for r in rows if r["key"].startswith(prefix)}
        assert codes == {True, False}, (
            f"{prefix}: recorded only {'passes' if True in codes else 'refusals'}; "
            "a verb needs both to pin its contract"
        )


def test_the_unprefixed_refusal_is_recorded(rows: list[dict]) -> None:
    """`plan_review_status: pending` carries no verb prefix and is easy to lose."""
    row = next((r for r in rows if r["key"] == "plan-check-current/pending"), None)
    assert row is not None
    assert row["before"]["returncode"] != 0
    assert row["before"]["stderr"] == "loop-cohort: stop — plan_review_status: pending"


# ── 5. the live-code guard ─────────────────────────────────────────────────

def _current_canonical_helpers():
    """`sha256_canonical_contract` as the tree currently implements it.

    Deliberately loaded from `loop-cohort.py` rather than from `_loop_guards.py`:
    that name stays a valid `loop-cohort` module attribute across the extraction
    (T1a re-binds every relocated name), so this test keeps pointing at whatever
    module actually owns the algorithm and needs no edit when it moves. Pointing it
    at the new module instead would make it silently stop covering the old path
    during the transition.
    """
    scripts = (
        Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"
    )
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_cohort_for_digest_check", str(scripts / "loop-cohort.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.sha256_canonical_contract, mod.canonical_contract


def test_recomputed_digests_match_golden(digests: dict) -> None:
    """Re-derive every digest from the CURRENT code and compare to the golden.

    The assertion the extraction has to survive, and the only digest assertion here
    that can fail when the implementation changes. Mutation-verified: perturbing the
    line-rstrip or the status splice in `canonical_contract` turns this red.

    Loaded from `loop-cohort.py` rather than `_loop_guards.py` on purpose — that name
    stays a valid `loop-cohort` module attribute across the extraction, so this test
    keeps pointing at whatever module owns the algorithm and needs no edit when it
    moves.
    """
    hasher, _ = _current_canonical_helpers()
    mismatches = [
        gs.corpus_key(p) for p in gs.corpus_entries()
        if hasher(p) != digests[gs.corpus_key(p)]
    ]
    assert not mismatches, (
        f"{len(mismatches)} digest(s) no longer match the pre-change golden: "
        f"{mismatches[:8]}. The canonical contract pins every approved baseline, so "
        "a digest change silently invalidates in-flight runs — including this spec's "
        "own state.json. Do NOT regenerate the fixture to make this pass."
    )
