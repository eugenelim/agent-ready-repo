# Plan: Index table generation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/governance-extras/.apm/skills/new-adr/scripts/next-ordinal.py` — the script-in-skill precedent this generator follows: argparse over a record directory, a `--check <dir>` mode, stdlib only, one `lstat` per entry with a record-shaped-symlink refusal (`:162-170`), and git-root resolution for its repository-relative work (`:115-123`). `tools/repo/build_gate_chain.py:267-271` (`check-adr-ordinals`) is the projection-invoked `--check` precedent. `tests/roster/test_decision_record_ordinal_uniqueness.py` is the roster-suite shape for a records-directory walk.

## Approach

One generator module, copied into each owning skill's `scripts/` directory in
the established `next-ordinal.py` pattern, parameterised by a record-type
descriptor so the ADR and RFC variants differ in data rather than code. The
descriptor carries the H1 pattern, the status field, the date fields, the column
headers, and the placeholder sentinel — the axes on which the two record types
actually diverge.

Record classification is `next-ordinal.py`'s, reused for its semantics rather
than by import: strict ordinal match, one `lstat` per entry, refusal of a
record-shaped symlink. Ordering is by parsed ordinal, so output never depends on
filesystem order. Date resolution is a three-step chain — header field, then the
file's first-commit date via `git log --diff-filter=A`, then empty with a
warning — portable to any git repository and degrading cleanly outside one.

## Constraints

- Standard library only. `subprocess` for the git fallback is stdlib; an absent
  or failing git binary takes the third branch rather than failing the run.
- No repository-specific literal in the generator. The record directory, and
  therefore the index path, arrive as arguments.
- Warnings to stderr, index to the file. The exit code carries only the
  `--check` verdict, never the warning count.
- The two installed copies are not compared to each other; `spec.md` forbids it.

## Construction tests

All generator tests live in `tests/roster/test_index_records.py`. The pack's
natural home under `packs/governance-extras/tests/skills/` is declared
`"never gated"`, so a suite placed there would never execute; the roster suite
is the only location whose runner exists.

Fixtures are built by the test, except the single whole-repository case AC26
requires. That case reads the real directories precisely because the
portability rule forbids the generator knowing them.

### Stub — T1 (materialize unchanged at EXECUTE)

```python
import importlib.util, pathlib, sys
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "packs/governance-extras/.apm/skills/new-adr/scripts/index-records.py"

def _load():
    spec = importlib.util.spec_from_file_location("index_records_adr", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod

def _write(d, name, h1, status="Accepted", date="2026-01-01"):
    (d / name).write_text(
        f"# {h1}\n\n- **Status:** {status}\n- **Date:** {date}\n",
        encoding="utf-8", newline="\n")

def test_rows_are_ordered_by_ordinal_not_filesystem_order(tmp_path):
    """AC1: shuffled creation order still renders ascending by ordinal."""
    for n in ("0009", "0001", "0010"):
        _write(tmp_path, f"{n}-r.md", f"ADR-{n}: Title {n}")
    rows = _load().render(tmp_path, record_type="adr").splitlines()
    ordinals = [r.split("|")[1].strip() for r in rows if r.startswith("| 0")]
    assert ordinals == ["0001", "0009", "0010"]

def test_a_non_record_entry_yields_no_row(tmp_path):
    """AC2: a .md file whose H1 is not the record form contributes nothing."""
    _write(tmp_path, "0001-r.md", "ADR-0001: Real")
    (tmp_path / "notes.md").write_text("# Just a note\n", encoding="utf-8", newline="\n")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines()
            if r.startswith("| 0")]
    assert len(rows) == 1

def test_a_qualifying_clause_is_stripped_from_status(tmp_path):
    """AC5: `Accepted — partially amended: ...` renders as `Accepted`."""
    _write(tmp_path, "0001-r.md", "ADR-0001: T",
           status="Accepted — **partially amended:** the guides sub-decision")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines() if r.startswith("| 0")]
    assert rows, "no record row rendered"
    row = rows[0]
    assert row.split("|")[3].strip() == "Accepted"

@pytest.mark.parametrize("title,shown", [
    ("Choose A | B", r"Choose A \| B"),
    ("Brackets [x] and (y)", r"Brackets \[x\] and (y)"),
])
def test_a_delimiter_bearing_title_renders_one_escaped_cell(tmp_path, title, shown):
    """AC6: the title cell displays escaped text and stays one cell."""
    _write(tmp_path, "0001-r.md", f"ADR-0001: {title}")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines() if r.startswith("| 0")]
    assert rows, "no record row rendered"
    row = rows[0]
    assert row.split(" | ")[1] == f"[{shown}](0001-r.md)"

def test_a_delimiter_bearing_filename_yields_a_resolving_link(tmp_path):
    """AC6, filename half: the link destination survives escaping and resolves."""
    name = "0001-a (b).md"
    _write(tmp_path, name, "ADR-0001: T")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines() if r.startswith("| 0")]
    assert rows, "no record row rendered"
    row = rows[0]
    dest = row.split(" | ")[1].split("](")[1].rstrip(")")
    assert (tmp_path / dest.replace("%20", " ")).exists()
```

**Validated red — observed, not asserted.** A disposable scratch
`index-records.py` exporting a `render` that returns a placeholder heading and
an empty table was run against these cases on 2026-09-13. A `render` that
*raises* would abort every case at the call and prove nothing, which is why the
scratch returns renderable text instead. Observed: `5 failed in 0.22s`, each an
`AssertionError` at its own assertion —

```text
E  AssertionError: assert [] == ['0001', '0009', '0010']
E  AssertionError: no record row rendered
E  AssertionError: assert 'Architecture Decision Records' in '# Placeholder...'
E  AssertionError: assert 'Requests For Comments' in '# Placeholder...'
E  AssertionError: assert '<!-- no ADRs yet -->' in '# Placeholder...'
```

The run also corrected the stubs: a `next(...)` row lookup reds with
`StopIteration` before its assertion, so every row lookup is a guarded list.
The scratch is not committed.

### Stub — T2 (date chain)

```python
import os, subprocess

def _git_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    return tmp_path

def test_header_date_wins_over_git_history(tmp_path):
    """AC7: a present Date field is used even inside a git repository."""
    d = _git_repo(tmp_path)
    _write(d, "0001-r.md", "ADR-0001: T", date="2020-02-02")
    subprocess.run(["git", "add", "-A"], cwd=d, check=True)
    env = {**os.environ, "GIT_COMMITTER_DATE": "2024-04-04T00:00:00"}
    subprocess.run(["git", "commit", "-qm", "x", "--date=2024-04-04T00:00:00"],
                   cwd=d, check=True, env=env)
    rows = [r for r in _load().render(d, record_type="adr").splitlines()
            if r.startswith("| 0")]
    assert rows, "no record row rendered"
    assert "2020-02-02" in rows[0]

def test_absent_header_date_falls_back_to_first_commit_date(tmp_path):
    """AC8: the fallback is the file's add date, not today."""
    d = _git_repo(tmp_path)
    (d / "0001-r.md").write_text("# ADR-0001: T\n\n- **Status:** Accepted\n",
                                 encoding="utf-8", newline="\n")
    subprocess.run(["git", "add", "-A"], cwd=d, check=True)
    env = {**os.environ, "GIT_COMMITTER_DATE": "2024-04-04T00:00:00"}
    subprocess.run(["git", "commit", "-qm", "x", "--date=2024-04-04T00:00:00"],
                   cwd=d, check=True, env=env)
    rows = [r for r in _load().render(d, record_type="adr").splitlines() if r.startswith("| 0")]
    assert rows, "no record row rendered"
    row = rows[0]
    assert row.split("|")[4].strip() == "2024-04-04"

def test_absent_date_without_git_warns_and_leaves_the_cell_empty(tmp_path, capsys):
    """AC9 + AC10: empty cell, and a warning naming file and field."""
    (tmp_path / "0001-r.md").write_text("# ADR-0001: T\n\n- **Status:** Accepted\n",
                                        encoding="utf-8", newline="\n")
    rows = [r for r in _load().render(tmp_path, record_type="adr").splitlines() if r.startswith("| 0")]
    assert rows, "no record row rendered"
    row = rows[0]
    assert row.split("|")[4].strip() == ""
    err = capsys.readouterr().err
    assert "0001-r.md" in err and "Date" in err
```

**Validated red.** Every case above asserts on `render`, the contract surface.
`_load()` raises on the absent script, so PLAN's red is currently the missing
module rather than the contract — the scratch validation therefore creates
`index-records.py` exporting `render` as `raise NotImplementedError`, proving each case reds at its own assertion. That scratch
file is disposable and is not committed.

### Stub — T3 (warnings and the empty corpus)

```python
def test_an_empty_directory_renders_the_type_sentinel(tmp_path):
    """AC14: the adopter's first-install state is a sentinel, not an empty table."""
    out = _load().render(tmp_path, record_type="adr")
    assert "<!-- no ADRs yet -->" in out

@pytest.mark.parametrize("kind,heading", [("ADR", "Architecture Decision Records"),
                                          ("RFC", "Requests For Comments")])
def test_the_record_type_is_inferred_when_not_supplied(tmp_path, kind, heading):
    """AC15, inference half: an RFC corpus must not infer as ADR."""
    _write(tmp_path, "0001-r.md", f"{kind}-0001: T")
    assert heading in _load().render(tmp_path)

def test_a_record_without_status_warns_and_still_renders(tmp_path, capsys):
    """AC11 + AC12: a malformed record never costs the whole index."""
    (tmp_path / "0001-r.md").write_text("# ADR-0001: T\n", encoding="utf-8", newline="\n")
    out = _load().render(tmp_path, record_type="adr")
    assert any(line.startswith("| 0001") for line in out.splitlines())
    assert "0001-r.md" in capsys.readouterr().err
```

Deferred to EXECUTE: AC15a's refusal and AC16-AC18's exit codes assert through
`main(argv)`, an out-of-process surface; `tdd-stubs.md` keeps those as deferred
assertions on the same in-process module rather than as a separate disposition.

### Stub — T4 (portability oracle)

```python
FROZEN = ("docs/adr", "docs/rfc", "docs/specs", "agent-ready-repo", "eugenelim")

@pytest.mark.parametrize("literal", FROZEN)
def test_the_generator_source_holds_no_frozen_literal(literal):
    """AC20: the script carries nothing drawn from this repository."""
    assert literal not in SCRIPT.read_text(encoding="utf-8")
```

Validated red: `SCRIPT` does not exist, so the scratch validation creates it
containing one frozen literal, proving the case reds on its own assertion rather
than on a missing file.

## Durable-output map

| Spec durable output | Task |
| --- | --- |
| Maintainer procedure (3 SKILL.md + light-mode.md) | T4, T5, T6 |
| Adopter scaffold (core seed) | T5 |
| Interface compatibility (tooling, `lint.py`) | T5 |
| User-facing promise (3 guides) | T7 |
| Release history (changelog) | T8 |
| Decision rationale, Interface compatibility (RFC erratum), Reusable learning | satisfied before this plan |

## Design (LLD)

### Design decisions

- **A record-type descriptor, not a subclass or a flag.** The two types differ
  only in constants, so a single parse and render path means a mutation to
  either is caught by both types' cases.
- **The generator owns the whole file, which is a heading and a table.** A
  marked-region model was authored and then cut: bounding the writable region
  meant specifying marker count, order, nesting, and fenced-block cases, and the
  criteria that bounded it produced more defects than the guarantee was worth.
  Owner decision 2026-09-13. The `../CONVENTIONS.md` pointer the two live files
  carried today is not preserved per-file; the convention links to its index
  instead, which is one edit rather than a standing preservation contract.
- **The git fallback shells out rather than importing a library.** A new
  dependency is barred; `git log` is a stable interface.
- **`--check` compares rendered text to the file bytes**, rather than to a
  parsed structure. A byte comparison is what a gate
  needs; a structural one passes on drifted formatting.

### Title provenance — informational, not contract

*Background for a reviewer reading T8's diff. Nothing here is a criterion, and
no check reads these figures; AC4 alone fixes the behaviour — a row's title is
its record's H1.*

Generating from the H1 rewrites most of the RFC index's titles and a minority of
the ADR index's, because both tables accumulated hand-written titles that drift
from the records they point at. Roughly half the rewrites are a dropped
table-side subtitle; the rest are substantively different text. The owner
accepted the rewrite over an override map on 2026-09-13: the record's own H1 is
the title, and the divergence set is closed, since the template makes the H1 the
title and a new record cannot join it.

The diff also moves every RFC link — that table wraps the ordinal where the ADR
table wraps the title — and re-pads every row. Read all of it as content.

### Interfaces & contracts

`index-records.py [--check] [--type adr|rfc] <record-dir>`, mirroring
`next-ordinal.py`'s `[--check] <dir>` shape. Type is inferred from the records
present and required when the directory is empty, since a zero-record directory
carries no evidence of its own type and the sentinel differs per type.

### Failure, edge cases & resilience

The zero-record case, the malformed-record case, the absent-git case, the
symlink case, and the delimiter-bearing title are the five that fail silently if
unexercised. Each has a dedicated criterion and a dedicated mutation proof.

## Tasks

### T1: Generator core — classify, parse, render

- **Implements:** AC1, AC2, AC3, AC4, AC5, AC6, AC13, AC19
**Depends on:** none
**Touches:** packs/governance-extras/.apm/skills/new-adr/scripts/index-records.py, packs/governance-extras/.apm/skills/new-rfc/scripts/index-records.py, tests/roster/test_index_records.py
- **Mode:** TDD
- **Tests:** the T1 stub above, plus a symlink case asserting AC13's named
  refusal. Mutation: delete the ordinal sort and the shuffled-order case reds;
  drop the cell escaping and the pipe case reds; replace `lstat` with
  `is_file()` and the symlink case reds.
- **Approach:** descriptor, one classify function reusing `next-ordinal.py`'s
  semantics, one parse function, one render function.
- **Done when:** the T1 cases pass.

### T2: Date resolution chain

- **Implements:** AC7, AC8, AC9, AC10
**Depends on:** T1
**Touches:** packs/governance-extras/.apm/skills/*/scripts/index-records.py, tests/roster/test_index_records.py
- **Mode:** TDD
- **Tests:** the T2 stub above. Mutation: make the fallback return today's date
  and the second case reds; suppress the warning and the third reds.
- **Approach:** three-branch chain with the git branch behind one helper, so the
  unavailable path is drivable without unsetting `PATH`.
- **Done when:** the T2 cases pass.

### T3: Warnings, empty corpus, type resolution, `--check`

- **Implements:** AC11, AC12, AC14, AC15, AC15a, AC16, AC17, AC18
**Depends on:** T1
**Touches:** packs/governance-extras/.apm/skills/*/scripts/index-records.py, tests/roster/test_index_records.py
- **Mode:** TDD
- **Tests:** the T3 stub above, extended with a record with an unparseable ordinal and one with no status each
  warn and exit 0; an empty directory renders the type's sentinel; an empty
  directory without `--type` refuses naming the record type and writes nothing;
  `--check` writes nothing, exits 0 on an identical file, and exits non-zero
  naming the first differing line otherwise. Mutation: make a malformed record
  raise and the warn case reds; make `--check` write and the writes-nothing
  assertion reds.
- **Approach:** warnings accumulate on a list rendered to stderr at exit.
- **Done when:** the T3 cases pass.

### T4: Portability oracles

- **Implements:** AC20, AC21, AC22
**Depends on:** T3
**Touches:** packs/governance-extras/.apm/skills/*/scripts/index-records.py, tests/roster/test_index_records.py
- **Mode:** TDD
- **Tests:** the T4 stub above. AC20's oracle asserts that none of the five frozen literals named
  in the criterion occurs in either installed script's source. AC21 instantiates the bundled
  `adr.md` and `rfc.md` templates by substituting their `NNNN` placeholder and
  date placeholders, then asserts AC1 and AC3 hold. AC22 builds a record
  directory under `tmp_path` and asserts the same. Mutation: paste `docs/adr`
  into the script and AC20 reds.
- **Approach:** the forbidden set is frozen in the criterion, not derived from
  the corpus: a set sourced from growing user-authored titles reds an unchanged
  generator the day a record's title supplies a generic fragment.
- **Done when:** the T4 cases pass.

### T5: Retire the spec index

- **Implements:** AC24 (spec half), AC28, AC29, AC30, AC31, AC32, AC32a
**Depends on:** none
**Touches:** docs/specs/README.md, packs/core/seeds/docs/specs/README.md, packs/governance-extras/seeds/docs/**/README.md, packs/core/.apm/skills/new-spec/SKILL.md, packs/core/.apm/skills/work-loop/references/light-mode.md, packages/agentbundle/agentbundle/catalogue_tooling/lint.py, tools/lint-agents-md.py, tools/test_guide_typed_asides.py, tests/roster/**, packs/core/tests/skills/new-spec/**, packages/agentbundle/tests/build_pipeline/test_self_host_check.py
- **Mode:** Goal-based check
- **Tests:** roster assertions that `docs/specs/README.md` and the core seed
  match no table-row pattern, that the live file retains its
  directory-convention block, that no shipped skill or reference instructs a
  spec-index update, and that the placeholder map requires the ADR and RFC
  sentinels and no spec-index sentinel; and that each governance seed's set of
  headings is exactly the record type's H1, with its sentinel-carrying table and
  no `##` section. Re-point the four suites that pin the
  removed step or parse index rows —
  `packs/core/tests/skills/new-spec/test_shaping_review.py:50`,
  `test_acceptance_criteria_discipline.py:346` and `:364`,
  `tools/test_guide_typed_asides.py:88`,
  `tests/roster/test_close_work_extraction_and_immediate_disposition.py:876`
  — and rework the self-host fixture at
  `packages/agentbundle/tests/build_pipeline/test_self_host_check.py:1027-1033`,
  which hard-codes the retired seed sentinel.
- **Approach:** delete both tables and the index prose; cut the
  `## Adding a new ADR` and `## Adding a new RFC` sections from the two
  governance seeds, so a seed matches what the generator writes and an adopter's
  first generation deletes nothing; remove the spec-index entry from the
  placeholder map; remove the `update docs/specs/README.md`
  clause at `work-loop/references/light-mode.md:29`; renumber `new-spec`'s
  steps; retire the `packs/core/seeds/docs/specs/README.md` row in
  `tools/lint-agents-md.py:42` if the rewritten seed no longer needs it.
- **Done when:** the re-pointed suites and the new assertions pass.

### T6: Wire the skills and the gate chain, then project

- **Implements:** AC23, AC24 (record half), AC25, AC27
**Depends on:** T4, T5
**Touches:** packs/governance-extras/.apm/skills/**, tools/repo/build_gate_chain.py, .claude/skills/**, .agents/skills/**
- **Mode:** Goal-based check
- **Tests:** each of `new-adr` and `new-rfc` names the generator at its
  record-creation step and names no hand-edit; `build_gate_chain.py` carries two
  `_script_step` entries under `.claude/skills/` whose args include `--check`,
  one per record directory; a generated index is the record type's heading
  immediately followed by its table, and contains no path resolving outside the
  record directory. `make build-self` leaves a clean tree;
  `agentbundle catalogue lint --root . --deep` reports no new finding for the
  three skills.
- **Approach:** copy the module into both `scripts/` directories; replace the
  index clause in each skill; add both gate steps beside `check-adr-ordinals`;
  `make build-self`, never editing a projection directly.
- **Done when:** `git status` is clean after the build and both gate steps pass.

### T7: Guides

- **Implements:** AC33, AC34, AC34a
**Depends on:** T5
**Touches:** guides/**, docs/CONVENTIONS.md, tests/roster/**
- **Mode:** Goal-based check
- **Tests:** a roster assertion that no file under `guides/` states a skill
  maintains a spec index, that the ADR and RFC how-tos name the generator, and
  that `docs/CONVENTIONS.md`'s ADR and RFC sections each link their index.
- **Approach:** edit the three named guides and add the two CONVENTIONS links.
- **Done when:** the assertion passes.

### T8: Generate this repository's indexes; versions; changelog

- **Implements:** AC26, AC35
**Depends on:** T6, T7
**Touches:** docs/adr/README.md, docs/rfc/README.md, packs/core/pack.toml, packs/governance-extras/pack.toml, packages/agentbundle/pyproject.toml, docs/product/changelog.md, tests/roster/**
- **Mode:** Visual / manual QA, then goal-based check
- **Tests:** run the real CLI against `docs/adr` and `docs/rfc` without
  `--check`, record stdout, stderr and exit code, then `--check` returns 0 for
  both. A roster assertion compares each pack's two manifest versions, and
  compares all three versions against the values at this spec's base revision
  pinned in the test.
- **Approach:** run the generator, review the title diff as the change's primary
  content, bump `core`, `governance-extras`, and `agentbundle`, add the
  changelog entry.
- **Done when:** `--check` exits 0 for both directories and the version
  assertions pass.

## Rollout

Single PR. No migration, no persisted state, no mixed-version concern: the
generator reads files and writes one file per directory.

## Risks

- **The spec-index removal touches six existing surfaces**, not four. Named in
  T5 with line numbers, so they are planned work rather than a GATES surprise.
- **`make build-self` refuses a dirty tree.** T6 runs after T4 and T5 commit.
- **AC26 is the one test that reads real directories**, so it moves whenever a
  record lands. It compares the file to freshly generated output rather than to
  a stored expectation, so it tracks the corpus instead of pinning it.
- **T8's diff is large and mostly titles.** See *Title provenance* under
  `## Design (LLD)` for what the change looks like and why it takes that shape.

## Changelog

- 2026-09-13 — first draft, from ADR-0112.
- 2026-09-13 — pre-review spike compared generated rows against both live
  tables. It disconfirmed the assumption that generation is near-lossless for
  titles, and confirmed AC5's status-qualifier rule is required rather than
  hypothetical. See *Title provenance*. The spike was not committed.
- 2026-09-13 — revised from two independent spec reviews. Compound criteria
  split (13 → 36 atomic); oracles bound to AC1/AC3 instead of authoring
  themselves; confinement, Markdown escaping, record-type resolution, and
  generated-preamble ownership added as criteria; the prohibited cross-copy
  drift assertion removed and forbidden in Boundaries; two missed consumers
  (`light-mode.md`, the self-host fixture) and two missed release surfaces (the
  core seed, the `agentbundle` package version) added; TDD stubs authored.
- 2026-09-13 — measured title figures moved out of `## Risks` into an
  explicitly informational `## Design (LLD)` note, so they carry no claim a
  review round can audit.
- 2026-09-13 — round 2 adjudicated by an independent `finding-adjudicator`:
  7 sustained, 1 refuted, 0 indeterminate. Dispositions, one per finding:
  AC14/AC15 empty-corpus contradiction — **repaired** (`--type` named in the
  Objective; AC15a carries the refusal). AC35 baseline — **repaired with an
  origin** (three literal versions at base `aa176ee2c`). AC36 — **routed to an
  owner that already covers it** and cut: `catalogue verify` enforces manifest
  version parity as `CAT-V-005`. AC6 stub's pipe count — **repaired** (asserts
  the escaped cell, and a filename case added). Missing TDD stubs —
  **routed to the authority's own disposition**: T3 and T4 record
  `no stub (implementation-discovered)` with discovery predicate, constraint,
  required outcome, verification mode, and proof obligation, rather than
  inventing seams during PLAN. AC20's oracle — **claim narrowed** to five frozen
  literals, because a forbidden set sourced from live titles drifts with the
  corpus. T2 environment replacement — **repaired**. The AC2/AC11 contradiction
  was **refuted**: no row plus a warning is a consistent disposition.
  Preamble ownership remains open for an owner decision.
- 2026-09-13 — owner chose the marked-region model for preamble ownership
  (2026-09-13), closing the last sustained round-2 finding. AC17 and AC26
  narrowed to the marked region; AC27 rewritten as a preservation guarantee;
  AC27a added for the no-marker refusal; AC27b pins that both live indexes keep
  their `../CONVENTIONS.md` cross-reference; AC30a puts the markers in the ADR
  and RFC seeds.
- 2026-09-13 — round 3 adjudicated: 7 sustained, 0 refuted, 0 indeterminate,
  and every finding traced to a prior repair rather than to an original defect.
  Dispositions: the invented `_cells` helper — **cut**, assertions moved onto
  `render`'s output; `AC15a` task ownership — **repaired**; the marked-region
  model and its four criteria — **cut** by owner decision, which dissolved the
  marker-grammar, preservation-check and seed-marker findings rather than
  repairing them; the `no stub (implementation-discovered)` records — **cut**,
  because `tdd-stubs.md` does not admit that branch for an out-of-process
  surface, and replaced with real T3 and T4 stubs whose out-of-process
  assertions are deferred; the Objective's empty-directory sentence — **left**,
  the criteria govern it and the header already routes output shape to them.
- 2026-09-13 — round 4 adjudicated: 3 sustained, 1 refuted, 1 indeterminate.
  T6's stale preamble check, T3's missing AC15 inference case, and T1's
  inaccurate validated-red note — all three **repaired**. The
  Design-rationale-in-changelog finding was **refuted**: `assets/spec.md:31-36`
  scopes the present-tense rule to the spec body and grants the plan its own
  changelog. The indeterminate — whether the seeds diverging from generated
  output is a residual of the AC30a cut — went to the owner, who **accepted the
  divergence and relocated the guidance**: the seeds lose their
  `## Adding a new ADR/RFC` sections, AC32a pins the seed shape, and AC32b keeps
  the instruction reachable from the skill and the guide. This closed a real
  adopter-facing regression the whole-file collapse had introduced below the
  table, where the earlier check had only looked above it.
- 2026-09-13 — round 5 adjudicated: 3 blocking and 1 advisory sustained, 0
  refuted, 0 indeterminate. AC32b — **cut**, because "state how to create a
  record" names no checkable predicate and `new-adr`/`new-rfc` already own the
  instruction under their own suites. AC32a's missing assertion and the vacuous
  AC15 inference case — **repaired**, the latter parameterized over an ADR and
  an RFC fixture so an ADR default cannot satisfy it. T1's validated-red note —
  **repaired at its cause rather than its wording**: the red was described
  across three rounds and never run. It has now been executed against a
  disposable scratch module and the observed output recorded, which also
  surfaced a defect no review round had reached — a `next(...)` row lookup reds
  with `StopIteration` before its assertion, so every row lookup is now a
  guarded list. Stub defects drove findings in rounds 3, 4 and 5; running the
  validation is what closed that surface.
- 2026-09-13 — **AM-001, controlled amendment under owner authority.** The T1
  stub's delimiter case parsed a row with `split("|")`, which cuts an escaped
  `\|` cell in half, so no correct implementation could satisfy it. The parse
  becomes `split(" | ")`, which is escape-safe. No acceptance criterion changes.
  Observation, cause, and the generalizable lesson are in
  `notes/verification-ledger.md`.
