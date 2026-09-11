#!/usr/bin/env python3
"""Pytest coverage for the grounding explorer.

Runs the explorer as a subprocess against fixture trees, following the precedent
in `packs/core/tests/skills/author-delivery-brief/test_lint_brief_coverage.py`.

Three cases carry the design rather than a feature, and each exists because a
prototype failed at it first:

  * `test_portability_fixture_with_foreign_top_levels` builds a repository whose
    top-level names share nothing with this catalogue's. The prototype hardcoded
    an allowlist of top-level directories, and a seeded reference under a name it
    omitted returned zero findings and read as clean. A suite that only ever runs
    against this repository's shape would have passed on that.

  * `test_co_change_reports_unavailable_without_history` covers the outcome that
    is neither found nor none. The work-loop is used on repositories before git
    is initialised, and a probe that returns empty when its input is missing is
    indistinguishable from a clean result.

  * `test_boilerplate_phrase_is_excluded` carries the calibration. Uncalibrated,
    this probe returned every skill in the catalogue because they share a shipped
    rendering block. Its mutation proof is in the assertion: the same phrase in
    few files must still be reported, so a probe that simply stopped reporting
    phrases would fail the sibling case.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "new-spec"
EXPLORER = _SKILL_DIR / "scripts" / "explore-grounding.py"
if not EXPLORER.is_file():  # wrong parents[] depth after a move
    raise SystemExit(f"subject not found at {EXPLORER} — check the parents[] depth")

LONG = "The seed file states a rule long enough to be distinctive when quoted elsewhere."


def _run(root: Path, *seeds: str, extra: list[str] | None = None) -> str:
    result = subprocess.run(
        [sys.executable, str(EXPLORER), "--root", str(root), *(extra or []), *seeds],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, f"explorer must report, never decide:\n{result.stdout}\n{result.stderr}"
    return result.stdout


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True)


@pytest.fixture()
def root():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


def _seeded(root: Path, top: str = "lib") -> str:
    """A tree whose top-level name is a parameter, so the suite cannot assume ours."""
    (root / top).mkdir(parents=True)
    (root / top / "seed.md").write_text(f"# Seed\n\n{LONG}\n", encoding="utf-8")
    (root / top / "AGENTS.md").write_text("scoped guidance\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("root guidance\n", encoding="utf-8")
    (root / "consumer.md").write_text(f"We depend on {top}/seed.md for this.\n", encoding="utf-8")
    (root / "Makefile").write_text(f"check:\n\tpytest {top}/seed.md\n", encoding="utf-8")
    return f"{top}/seed.md"


def test_portability_fixture_with_foreign_top_levels(root):
    """Top-level names are derived, not declared.

    `app/` appears in no allowlist this catalogue could ship. A hardcoded list
    finds nothing here and reports it as a clean run.
    """
    seed = _seeded(root, top="app")
    out = _run(root, seed)
    assert "consumer.md" in out, out
    assert "app/AGENTS.md" in out and "AGENTS.md" in out, out


def test_scoped_rules_walks_to_the_root_not_to_the_nearest(root):
    seed = _seeded(root)
    out = _run(root, seed)
    block = out.split("scoped rules", 1)[1]
    assert "lib/AGENTS.md" in block and "\n      AGENTS.md" in block, out


def test_a_tree_with_no_runner_reports_unavailable_not_unreached(root):
    """The branch every other fixture makes unreachable.

    `_seeded` always writes a root Makefile, so `runners` was never empty in any
    case and the repair could be deleted with the suite still green. With no
    runner file at all, "nothing runs this path" is missing input, not the
    probe's positive finding.
    """
    seed = _seeded(root)
    (root / "Makefile").unlink()
    out = _run(root, seed)
    # Target the gates *line*: the phase-probes header also contains the word.
    line = next((l for l in out.splitlines() if l.strip().startswith("gates")), "")
    assert "unavailable" in line, f"no runner exists:\n{out}"
    assert "UNREACHED" not in out, "missing input must not read as the positive finding"


def test_gate_reachability_reports_unreached_as_the_finding(root):
    """A seed no runner names is the finding, not the absence of one."""
    seed = _seeded(root)
    (root / "Makefile").write_text("check:\n\techo nothing\n", encoding="utf-8")
    out = _run(root, seed)
    assert "UNREACHED — no runner names this path" in out, out
    assert "considered" in out, "the report must name how many runners it looked at"


def test_gate_reachability_finds_a_runner_that_names_the_seed(root):
    seed = _seeded(root)
    out = _run(root, seed)
    assert "UNREACHED" not in out, out
    assert "Makefile" in out, out


def test_boilerplate_phrase_is_excluded_but_a_real_pin_is_kept(root):
    """The cutoff, and the proof it did not simply stop reporting phrases."""
    seed = _seeded(root)
    for index in range(6):
        (root / f"boiler{index}.md").write_text(LONG + "\n", encoding="utf-8")
    (root / "pinner.md").write_text(f"quoting: {LONG}\n", encoding="utf-8")
    out = _run(root, seed)
    assert "boiler0.md" not in out, "a phrase in many files is boilerplate, not a pin"

    for index in range(6):
        (root / f"boiler{index}.md").unlink()
    kept = _run(root, seed)
    assert "pinner.md" in kept, "with the boilerplate gone the same phrase must be reported"


def test_co_change_reports_unavailable_without_history(root):
    """Neither found nor none: the input is missing and the output must say so."""
    seed = _seeded(root)
    out = _run(root, seed)
    assert "unavailable — input missing" in out, out
    assert "not a clean result" in out, out


def test_co_change_finds_a_partner_from_history(root):
    seed = _seeded(root)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "t")
    partner = root / "lib" / "partner.md"
    for index in range(4):
        (root / seed).write_text(f"# Seed {index}\n\n{LONG}\n", encoding="utf-8")
        partner.write_text(f"partner {index}\n", encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", f"c{index}")
    out = _run(root, seed)
    assert "lib/partner.md" in out, out
    assert "confidence" in out, "a raw count without its ratio is not calibrated"


def test_result_cap_reports_an_exact_remainder(root):
    seed = _seeded(root)
    for index in range(9):
        (root / f"ref{index}.md").write_text(f"see lib/seed.md\n", encoding="utf-8")
    out = _run(root, seed, extra=["--cap", "3"])
    assert "capped at 3" in out, out
    # The remainder must be exact, not approximate: derive it from the reported
    # total rather than hardcoding, so the case survives a fixture change.
    total = int(re.search(r"path refs\s+(\d+)", out).group(1))
    assert f"and {total - 3} more" in out, f"remainder must be exact:\n{out}"


def test_a_copy_of_the_seed_is_not_a_pin_on_it(root):
    """A pin quotes one thing; a copy quotes everything.

    Content decides, so this needs no knowledge of where a repository puts its
    projections. The floor matters as much as the ratio: with few sampled
    phrases, half of them is one, and a single quotation is what a pin looks
    like — without a floor every pin is misread as a copy.
    """
    seed = _seeded(root)
    body = (root / seed).read_text(encoding="utf-8")
    for index in range(6):
        (root / "lib" / f"line{index}.md").write_text(
            f"A distinctive sentence number {index} that is comfortably long enough to sample.\n",
            encoding="utf-8")
        body += f"A distinctive sentence number {index} that is comfortably long enough to sample.\n"
    (root / seed).write_text(body, encoding="utf-8")
    (root / "mirror.md").write_text(body, encoding="utf-8")     # a projection
    (root / "pinner.md").write_text(f"quoting one line: {LONG}\n", encoding="utf-8")
    out = _run(root, seed)
    assert "copies of seed" in out and "mirror.md" in out, out
    pins = out.split("phrase pins", 1)[1].split("copies of seed", 1)[0]
    assert "mirror.md" not in pins, "a whole-file copy must not be reported as a pin"


def test_phase_selects_the_probe_set(root):
    """One script, directed by stage: at discovery a dead-reference scan is a
    reassuring empty result, because nothing has been authored yet."""
    seed = _seeded(root)
    discovery = _run(root, seed, extra=["--phase", "discovery"])
    assert "grounding surfaces:" in discovery, discovery
    assert "dead refs" not in discovery, "discovery runs before anything is authored"
    review = _run(root, seed, extra=["--phase", "review"])
    assert "dead refs" in review, review
    assert "scoped rules" not in review, "review does not re-ask what governs the surface"


def test_a_near_miss_path_is_not_a_reference_and_the_seed_is_not_its_own(root):
    """Two negatives the probe must hold: a similar path, and the seed itself."""
    seed = _seeded(root)
    (root / "near.md").write_text("we use lib/seed.markdown, a different file\n", encoding="utf-8")
    out = _run(root, seed)
    refs = out.split("path refs", 1)[1].split("phrase pins", 1)[0]
    assert "near.md" not in refs, "a near-miss path must not count as a reference"
    assert "lib/seed.md\n" not in refs, "the seed must be excluded from its own references"


def test_calibration_differs_by_repository_and_names_its_basis(root):
    """The live-calibration claim, tested by making two repositories disagree."""
    seed = _seeded(root)
    thin = _run(root, seed)
    assert "sweep-commit threshold" in thin and "default (no history)" in thin, thin

    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "t")
    for index in range(24):
        (root / f"f{index}.md").write_text(f"body {index}\n", encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", f"c{index}")
    rich = _run(root, seed)
    assert "p90 of" in rich, "with history the threshold must derive from this repository"
    assert "default (no history)" not in rich


def test_an_ambiguous_reference_is_named_with_its_candidate(root):
    """A path resolving under another root is a scope question, not a dead link."""
    seed = _seeded(root)
    # Ambiguity is decided against the tracked set, so the fixture needs history:
    # `vendor/thing.md` must be absent at the root and present under another one.
    (root / "vendor").mkdir()
    (root / "vendor" / "other.md").write_text("x\n", encoding="utf-8")
    (root / "lib" / "vendor").mkdir()
    (root / "lib" / "vendor" / "thing.md").write_text("x\n", encoding="utf-8")
    (root / seed).write_text(
        f"# Seed\n\n{LONG}\n\nSee vendor/thing.md for detail.\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "t")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seed")
    out = _run(root, seed, extra=["--phase", "review"])
    assert "ambiguous refs" in out and "resolves at" in out, out
    assert "lib/vendor/thing.md" in out, "the candidate resolution must be named"


def test_a_symlinked_file_pointing_out_of_the_root_is_refused(root):
    """The guard that actually refuses, exercised.

    A symlinked *directory* proves nothing: `os.walk` defaults to
    followlinks=False, so the directory filter cannot change the outcome and the
    case stays green with the filter deleted. The refusal that does the work is
    the lstat/S_ISREG check, and only a symlinked *file* reaches it.
    """
    seed = _seeded(root)
    outside = root.parent / f"outside-{root.name}.md"
    outside.write_text(f"secret quoting: {LONG}\n", encoding="utf-8")
    try:
        (root / "linked.md").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks unavailable")
    try:
        out = _run(root, seed)
        assert "linked.md" not in out, f"a symlinked file must be refused:\n{out}"
    finally:
        outside.unlink(missing_ok=True)


def test_confinement_holds_on_the_tracked_set_branch(root):
    """Every real repository takes the git branch, so the fixture must too.

    Without history `confined_files` walks the filesystem; with it, the
    tracked-set path runs instead. A confinement case that only ever exercises
    the walk says nothing about the branch production uses.
    """
    seed = _seeded(root)
    outside = root.parent / f"tracked-outside-{root.name}.md"
    outside.write_text(f"secret quoting: {LONG}\n", encoding="utf-8")
    try:
        (root / "linked.md").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks unavailable")
    try:
        _git(root, "init", "-q")
        _git(root, "config", "user.email", "t@example.invalid")
        _git(root, "config", "user.name", "t")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "seed")
        out = _run(root, seed)
        assert "git unavailable" not in out, "this case must take the tracked-set branch"
        assert "linked.md" not in out, f"the tracked-set branch must refuse it too:\n{out}"
    finally:
        outside.unlink(missing_ok=True)


def test_the_phrase_cutoff_reports_a_derived_basis(root):
    """The other half of AC-0035's derive-rather-than-fix claim.

    Only `calibrate_sweep`'s p90 branch had a case; `calibrate_cutoff` could
    return its default unconditionally with the suite still green, so one of the
    two thresholds the criterion names was unverified. The fixture is sized to
    enter the branch: 50+ scanned files and 8+ matched phrases.
    """
    seed = _seeded(root)
    lines = [f"A sampled sentence number {i} that is comfortably long enough to matter."
             for i in range(14)]
    (root / seed).write_text("# Seed\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    for index in range(60):
        (root / f"n{index}.md").write_text("\n".join(lines[: 1 + index % 12]) + "\n",
                                           encoding="utf-8")
    out = _run(root, seed)
    line = next((l for l in out.splitlines() if "cutoff" in l), "")
    assert "p75 of" in line, f"the cutoff must report a derived basis:\n{out}"


def test_the_co_occurrence_minimum_is_reported_in_every_phase(root):
    """A bound that filters results names itself even where nothing consumes it."""
    seed = _seeded(root)
    for phase in ("discovery", "task", "review", "all"):
        out = _run(root, seed, extra=["--phase", phase])
        assert "minimum co-occurrences" in out, f"{phase} omits the filtering bound:\n{out}"


def test_calibration_does_not_carry_between_seeds(root):
    """Regression: the cutoff was reassigned inside the per-seed loop.

    Seed N's derived value entered seed N+1 as its default, so the printed value
    was order-dependent and a thin second seed reported the first seed's number
    under the basis "default". Running the same pair in both orders must give
    each seed the same value and basis either way.
    """
    first = _seeded(root)
    # The calibration branch needs real signal to enter at all: at least 50
    # scanned files and 8 matched phrases. A small fixture returns the default
    # for both seeds, so the orders agree and the case passes with the bug
    # present -- which is what the first version of this test did.
    lines = [f"A sampled sentence number {i} that is comfortably long enough to matter."
             for i in range(14)]
    (root / first).write_text("# Seed\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    (root / "lib" / "second.md").write_text("# Second\n\nshort\n", encoding="utf-8")
    second = "lib/second.md"
    for index in range(60):
        (root / f"noise{index}.md").write_text("\n".join(lines[: 1 + index % 12]) + "\n",
                                               encoding="utf-8")

    def cutoffs(out: str) -> list[str]:
        return [line.strip() for line in out.splitlines() if "cutoff" in line]

    forward = cutoffs(_run(root, first, second))
    backward = cutoffs(_run(root, second, first))
    assert forward and backward, "both orders must report a cutoff per seed"
    assert sorted(forward) == sorted(backward), (
        f"calibration must not depend on seed order:\n{forward}\n{backward}")


def test_a_seed_that_does_not_exist_is_reported_not_crashed(root):
    """An author names a file the delivery will create; that must not be fatal."""
    _seeded(root)
    out = _run(root, "lib/not-yet-written.md")
    assert "lib/not-yet-written.md" in out, out
    assert "Traceback" not in out


def test_an_empty_seed_file_yields_no_phantom_phrases(root):
    seed = _seeded(root)
    (root / seed).write_text("", encoding="utf-8")
    out = _run(root, seed)
    pins = [l for l in out.splitlines() if "phrase pins" in l]
    assert pins and "none found" in pins[0], f"an empty seed samples no phrases:\n{out}"


def test_a_directory_seed_gets_its_own_governing_file(root):
    """Every plan `Touches` field names directories, and a directory governs itself.

    The walk began at the seed's parent — correct only for a file — so a
    directory seed silently lost the most governing file for its own surface.
    """
    _seeded(root, top="app")
    out = _run(root, "app")
    block = out.split("scoped rules", 1)[1]
    assert "app/AGENTS.md" in block, f"a directory seed must include its own:\n{out}"


def test_a_non_prose_seed_reports_unavailable_not_empty(root):
    """A seed with nothing to sample is unavailable input, not a clean result."""
    _seeded(root)
    (root / "lib" / "data.json").write_text('{"a": 1}\n', encoding="utf-8")
    out = _run(root, "lib/data.json")
    pins = [line for line in out.splitlines() if "phrase pins" in line]
    assert pins and "unavailable" in pins[0], f"non-prose seed:\n{out}"


def test_an_absent_seed_reports_unavailable_not_empty(root):
    """The normal discovery seed: a destination the delivery will create."""
    _seeded(root)
    out = _run(root, "lib/not-yet.md")
    pins = [line for line in out.splitlines() if "phrase pins" in line]
    assert pins and "unavailable" in pins[0], f"absent seed:\n{out}"


def test_scanned_suffixes_follow_the_repository_not_a_builtin_list(root):
    """The portability case that varies file *types*, not just directory names.

    A hardcoded allowlist makes every probe silently empty on an adopter whose
    sources are TypeScript or Go. The earlier portability case varied only the
    top-level name, so nothing reached this.
    """
    seed = _seeded(root)
    (root / "app.ts").write_text("import x from 'lib/seed.md';\n", encoding="utf-8")
    (root / "svc.go").write_text('// see lib/seed.md\n', encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "t")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seed")
    out = _run(root, seed)
    assert "scanned suffixes" in out, "the considered set must be named"
    refs = out.split("path refs", 1)[1].split("phrase pins", 1)[0]
    assert "app.ts" in refs and "svc.go" in refs, f"non-Markdown sources unscanned:\n{out}"


def test_a_file_past_the_size_bound_is_counted_not_silently_empty(root):
    """A large file's references must not vanish into "none found"."""
    seed = _seeded(root)
    (root / "huge.md").write_text("x" * 2_100_000, encoding="utf-8")
    out = _run(root, seed)
    assert "past the size bound" in out, f"the omission must be visible:\n{out}"


def test_the_co_change_minimum_is_reported(root):
    """A bound that filters results must name itself, like the other two."""
    seed = _seeded(root)
    out = _run(root, seed)
    assert "minimum co-occurrences" in out, out


def test_sweep_is_not_derived_when_no_probe_consumes_it(root):
    """One git call per commit, for a value the discovery phase never reads."""
    seed = _seeded(root)
    out = _run(root, seed, extra=["--phase", "discovery"])
    assert "co-change" not in out.split("phase probes")[1].split("\n")[0]


def test_seed_outside_the_root_is_refused(root):
    result = subprocess.run(
        [sys.executable, str(EXPLORER), "--root", str(root), "../escape.md"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 2, result.stdout
    assert "refusing seed outside root" in result.stdout


def test_missing_git_is_announced_not_hidden(root):
    seed = _seeded(root)
    out = _run(root, seed)
    assert "git unavailable" in out, "a degraded run must say it degraded"
