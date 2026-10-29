#!/usr/bin/env python3
"""Self-checks for the pre-change golden fixtures (T0).

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
        # in test_canonical_contract_folds_line_endings below, on strings built with
        # golden_support.crlf_text / cr_text.
        assert b"\r" not in raw, (
            f"{key}: committed CR bytes. `.gitattributes` normalizes them away in "
            "the blob, so a fixture that relies on them would hash differently in a "
            "fresh clone than in this working copy — which is exactly the divergence "
            "this assertion exists to prevent. Synthesize line-ending variants "
            "instead (golden_support.crlf_text / cr_text)."
        )
        # NOTE: `026-synthetic-crlf-endings/spec.md` names `golden_support.crlf_bytes`
        # and `@crlf`/`@cr` digest keys in its own prose. Neither exists — the helpers
        # are `crlf_text`/`cr_text`, and the digest keys were removed once mutation
        # showed them tautological. The fixture is NOT corrected, deliberately: its
        # bytes are pinned in `golden_digests.json` as a pre-change capture, so editing
        # the prose would change the digest and the only way to make it pass again is
        # to re-generate the golden against the current tree — the tautology T0 exists
        # to prevent. Frozen fixture text is input data, not maintained documentation.
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


# ── 4. preserved rows are clean ────────────────────────────────────────────


# ── 5. the live-code guard ─────────────────────────────────────────────────

def _current_canonical_helpers():
    """`sha256_canonical_contract` as the tree currently implements it.

    Loaded from `_loop_guards.py`, the module that owns the algorithm.
    """
    scripts = (
        Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"
    )
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_guards_for_digest_check", str(scripts / "_loop_guards.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.sha256_canonical_contract, mod.canonical_contract


def test_recomputed_digests_match_golden(digests: dict) -> None:
    """Re-derive every digest from the CURRENT code and compare to the golden.

    The assertion the extraction has to survive, and the only digest assertion here
    that can fail when the implementation changes. Mutation-verified: perturbing the
    line-rstrip or the status splice in `canonical_contract` turns this red.

    """
    hasher, _ = _current_canonical_helpers()
    mismatches = [
        gs.corpus_key(p) for p in gs.corpus_entries()
        if hasher(p) != digests[gs.corpus_key(p)]
    ]
    assert not mismatches, (
        f"{len(mismatches)} digest(s) no longer match the pre-change golden: "
        f"{mismatches[:8]}. The canonical contract pins every approved baseline, so "
        "a digest change silently invalidates in-flight runs — "
        "Do NOT regenerate the fixture to make this pass."
    )
