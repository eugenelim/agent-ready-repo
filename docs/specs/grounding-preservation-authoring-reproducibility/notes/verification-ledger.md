# Verification ledger: reproducible preservation authoring on the shared-graph case

## Dispatch, 2026-10-29

The owner (Platform Core) directed the controller to implement T1–T4 itself;
each task's dispatch receipt is recorded as `human-directed`.

## T1 — reference edits and content pins, 2026-10-29

- Red: the four new `RULES` phrases in
  `packs/core/tests/skills/new-spec/test_shared_substrate_preservation.py`
  failed on the unedited reference (4 failed, 11 passed).
- Green: after Edits 1–3, `packs/core/tests/skills/new-spec/` and
  `packs/core/tests/skills/work-loop/test_preservation_evidence_reference.py`
  pass (297 passed, 82 subtests, 77 s).

## T2 — release, projection, and registration, 2026-10-29

- Core is 3.1.39 in `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json`, one patch above 3.1.38 at the base
  `b1be32193`; fragment `docs/product/changelog.d/ae86168c-4ce0-444b-929b-12c0020ce909.md`
  names `core` 3.1.39.
- `agentbundle catalogue self-host --root . --write --force` re-run leaves no
  diff; the reference's two projections changed.
- `git diff --exit-code <base> HEAD -- packs/core/.apm/skills/new-spec/evals/`
  exits 0; the only path under `packs/core/.apm/` and `contracts/` in the diff
  is the reference.
- `tests/roster/test_workspace_retirement_inventory.py`: 127 passed (136 s).
  `lint-brief-coverage.py`: 26 briefs checked, exit 0.
- `tools/check-core-release.py --base origin/main` fails with "/now/ payload
  bullets differ from the core 3.1.39 changelog entry". The same command fails
  for 3.1.38 on `main` at `b1be32193`, so it is pre-existing and outside this
  diff; captured as `docs/product/captured/pre-existing-check-core-release-now-anchor.md`
  and treated as a known skip. No CI workflow or Makefile target runs it.

## T3 — graded runs, 2026-10-29

**Method.** Each run is one fresh `general-purpose` subagent given only
`notes/graded-runs/run-brief-template.txt` filled with its directories and the
case prompt. Graders are separate `general-purpose` subagents. The first
grading pass (`<run>-grade.md`, briefs `grader-pos.txt` and `grader-neg.txt`)
also showed the grader the case prompt, which the spec's graded-run term does
not allow; every counted run was therefore regraded by a fresh grader that read
only the output file and the case assertions (`<run>-grade-r2.md`, briefs
`grader-pos-r2.txt` and `grader-neg-r2.txt`). The r2 grades are the counted
ones. Run copies are built
by `notes/graded-runs/mkrun.py`: `git archive <rev> .claude/skills
.claude/agents`, keeping only skill directories with a
`packs/core/.apm/skills/<name>/SKILL.md` and agent files under
`packs/core/.apm/agents/` at that revision, then deleting `adapt-to-project`
and every `evals/` directory.

**Tool set (AC-0006).** Run agents were the `general-purpose` subagent type,
which carries this session's standard tool set (Bash, Read, Edit, Write, Glob,
Grep, web and skill tools); the brief forbade the Skill tool and any read
outside the copy. The session exposes no Pi tool and no code-intelligence
capability, so neither was available to any run.

**Copy contents (AC-0005).** Every final-projection run copy held exactly the
Core entries at revision `b45be95c4` (Core 3.1.39) less `adapt-to-project`:

- skills (20): author-brief author-delivery-brief bug-fix close-work contract-acquisition explain-diff init-project intake-intent navigate-intents new-spec operational-safety project-knowledge receive-brief repository-exploration repository-grounding security-checklists security-checklists-reference work-intake work-loop workspace-status
- agents (6): adversarial-reviewer.md finding-adjudicator.md implementer.md quality-engineer.md security-reviewer.md shaping-reviewer.md

`mkrun.py` compared both lists with the `packs/core/.apm/` listing at that
revision (`skills==core-less-adapt: True; agents==core: True` for all four
copies), and `find <copy> -type d -name evals` printed nothing for each; the
per-copy output is `notes/graded-runs/head-isolation.txt`.

### Results

| Run | Projection | Case | Score (grading pass, role) |
| --- | --- | --- | ---: |
| `pos-head1` | final, `b45be95c4`, Core 3.1.39 | positive | 6/6 (r2, counted) |
| `pos-head2` | final, `b45be95c4`, Core 3.1.39 | positive | 6/6 (r2, counted) |
| `pos-head3` | final, `b45be95c4`, Core 3.1.39 | positive | 6/6 (r2, counted) |
| `neg-head1` | final, `b45be95c4`, Core 3.1.39 | negative | 4/4 (r2, counted) |
| `pos-base` | base, `b1be32193`, Core 3.1.38 | positive | 5/6 (first pass, baseline) |
| `neg-base` | base, `b1be32193`, Core 3.1.38 | negative | 4/4 (first pass, baseline) |
| `pos-spike` | spike, Edits 1–2 on a `/tmp` copy of 3.1.38 | positive | 5/6 (first pass, design) |
| `pos-spike2` | spike, Edits 1–3 on a `/tmp` copy of 3.1.38 | positive | 6/6 (first pass, design) |
| `pos-spike3` | spike, Edits 1–3 on a `/tmp` copy of 3.1.38 | positive | 6/6 (first pass, design) |

These nine are every graded run made under this spec. Outputs and grades are
`notes/graded-runs/<run>.md` and `<run>-grade.md`, plus `<run>-grade-r2.md` for
the four counted runs. The first-pass grades of the counted runs matched the r2
grades exactly (6/6, 6/6, 6/6, 4/4). Base and spike runs keep their first-pass
grades only; they are baselines and design evidence, not counted runs.

- **Base positive** missed assertion 5 only: the map was never called
  disposable. Its invalidation criterion held this time.
- **Spike 1** stated disposability and bounded `invalidated_files`, but
  checked the full and incremental builds each against its own golden; that
  miss produced Edit 3.
- **Every final-projection positive run** opened its consumer map with the
  working-material sentence, wrote an `invalidated_files` criterion with the
  absent `dependencies` producer recorded as a bounded assumption, and wrote a
  criterion comparing full and incremental builds with each other.
- Base and spike copies were built the same way (spike copies from the working
  tree's `.claude/`), and `find` found no `evals` directory in any of them.

## T4 — closeout registration, 2026-10-29

- `docs/product/captured/new-spec-positive-case-reproducibility.md` reads
  `Status: Closed`, `Resolution: fixed`, with its detail pointing at this ledger.
- `[backlog].open` has no entry for it; this spec's entry sits in
  `["ini-002".work].shipped`; its inventory row is `historical`.
- The brief's C3 "Pass the integrated positive fixture" bullet links this ledger.
- `lint-spec-status.py --root .`: clean. `workspace_status.py reconcile` reports
  one finding for this spec, `impossible_transition` (shipped membership while
  `spec.md` reads `Implementing`), which the REVIEW-stage `Status: Shipped`
  write clears.

## REVIEW, 2026-10-29

- `adversarial-reviewer`, code stage: round 1 sustained one Concern (grader
  input) and refuted four; round 2 sustained one Nit (table labels); round 3
  clean. `security-reviewer`: not warranted — the edit changes authoring prose,
  not a tool surface, authority, untrusted-input handling, or data flow.
  `quality-engineer`: not warranted — no operational-safety module, no
  structural change, not requested. `experience-reviewer` and
  `frontend-reviewer`: not warranted — no rendered or reader-facing surface.
- At HEAD, AC-0007 to AC-0010 re-checked against base `b1be32193`
  (`origin/main` unchanged): evals diff empty; Core 3.1.38 → 3.1.39 in both
  manifests; fragment `ae86168c-…` names `core` 3.1.39; the only
  `packs/core/.apm/` path is the reference, none under `contracts/`.
- With `Status: Shipped`, `workspace_status.py reconcile` reports no finding for
  this spec, and `lint-spec-status.py --root .` is clean.
