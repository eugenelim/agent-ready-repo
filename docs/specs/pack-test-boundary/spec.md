# Spec: pack-test-boundary

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0071

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Four knowledge entries appended to `docs/knowledge/patterns.jsonl` by the
work-loop's Capture-learnings step failed CI on PR #870, each missing the
required `source` key. Diagnosing the miss surfaced a structural cause behind
the immediate one, and closing that cause exposed a third.

**1 — The guidance named no keys.** `work-loop` § Capture learnings said
"promote to `docs/knowledge/patterns.jsonl` (schema: `docs/knowledge/README.md`)".
A pointer, not a shape. The author wrote entries from memory.

**2 — Verification was unspecified, so it was improvised.** The entries were
checked with `python tools/lint-knowledge.py 2>&1 | tail -2`, which reports
*tail's* exit status — always 0 — and truncates exactly the `✖ <file>:<line>:`
lines naming the fault. The file read clean locally and failed in CI.

**3 — The gate never reached the people who need it.** `lint-knowledge.py`
lived in `tools/`, which is catalogue-local, while `docs/knowledge/` is seeded
into every adopter's repo. The seeded README told adopters to run a script they
had never been given, and nothing validated a file we hand them.

Fixing (3) meant moving a test into the pack, which exposed that the repo had
no boundary between a pack's runtime payload and its tests: every core-pack
test lived under `.apm/`, the runtime export directory, surviving only because
the installer happens to ignore those paths. That implicit exclusion is the
real defect — a future adapter that projects `.apm/**` wholesale would ship our
test suite into adopter trees.

## Acceptance criteria

### Workstream A — knowledge-capture guidance

- [x] **AC1** — The work-loop's Capture-learnings step states all six required
      keys (`id`, `kind`, `scope`, `title`, `body`, `source`) and the optional
      `tier` inline, with a one-line example entry, so a writer never opens a
      second file to get the shape right.
- [x] **AC2** — The skill, `docs/knowledge/README.md`, and its seed each
      instruct the writer to run the gate **unfiltered** and read its exit code,
      and state why `tail`/`grep` destroys that judgement. The two READMEs'
      "Verify before committing" sections are byte-identical.
- [x] **AC3** — "Never judge a gate through `tail` or `grep`" exists as a
      general work-loop anti-pattern, not only knowledge-specific advice.
- [x] **AC4** — `lint-knowledge.py` ships with the `core` pack and projects into
      an adopter's tree like `loop-cohort.py`.
- [x] **AC5** — The shipped `pre-pr.py` runs it over
      `docs/knowledge/patterns.jsonl` automatically; adopters wire nothing. It
      skips cleanly when the file or the skill is absent.
- [x] **AC6** — No shipped surface (`packs/**/.apm/**`, `packs/**/seeds/**`)
      references `tools/lint-*` or any path absent from an adopter's tree.
- [x] **AC7** — A drift guard fails when any surface telling a writer to author
      an entry omits a required key from its inline list, or carries an example
      that does not lint clean. Falsified in both directions before landing.

### Workstream B — pack test boundary

- [x] **AC8** — `.apm/` contains only runtime-projectable content. No core-pack
      test remains under any `.apm/` path.
- [x] **AC9** — Core-pack tests live under `packs/core/tests/`, laid out
      `tests/skills/<skill>/` and `tests/hooks/`, and execute the real
      implementation under `.apm/` rather than a duplicated copy.
- [x] **AC10** — No **core-owned** skill in the projected tree (`.claude/`,
      `.agents/`) carries a test file, verified positively by
      `packs/core/tests/pack/test-runtime-boundary.py` rather than assumed from
      the installer's current behaviour. Scoped to core because the other packs'
      tests are deferred; a repo-wide assertion would fail on deferred work
      rather than on a regression.
- [x] **AC11** — Every moved suite passes from its new home, resolving its
      subject against the pack source.
- [x] **AC12** — Every consumer — CI workflows, `Makefile`, `tools/test-all.py`,
      `tools/repo/build_gate_chain.py`, `tools/test_build_gate_chain.py`,
      `self_host_windows.py`, `tools/hooks/README.md` — points at the new
      locations. No dangling reference remains in operative code.
- [x] **AC13** — Every `core` and `product-documentation` suite whose *subject*
      was pack content moved out of `packages/agentbundle/tests/` to the owning
      pack's `tests/` tree. The distinction is subject, not mention: engine
      tests that use a pack as fixture data stay. Renaming a private helper in
      a pack must not turn the published package's suite red, which is exactly
      what happened during this change.
      `test_research_retrievers_conformance.py` (desk-research) and
      `test_credential_setup_skill.py` (credential-brokers) are the same shape
      and remain, with the rest of the per-pack migration
      (deferred: pack-test-boundary-remaining-packs).

- [x] **AC14** — The boundary is mechanically enforced: a regression test fails
      when test content appears under `packs/core/.apm/` or in a projected core
      skill, falsified by planting a file under `.apm/`.
- [x] **AC15** — The policy is encoded where authors will meet it: the shipped
      `catalogue-authoring-standards.md` (normative, travels with a catalogue
      and renders on the doc site), `docs/architecture/pack-layout.md` (the
      repo-internal shape), `guides/_shared/how-to/author-a-skill.md` (the
      point of authoring), and `packs/AGENTS.md` (the agent-facing rule).
- [x] **AC16** — The `agentbundle` release surface is updated for the removal:
      version bumped in `pyproject.toml` and the hardcoded `CLI_VERSION` twin,
      a `CHANGELOG.md` entry, and `README-pypi.md` — the page adopters read on
      PyPI — documenting the `tests/` tree and the three boundaries.


## Boundaries

### Always do

- State the required-key set inline wherever a writer is told to author an entry,
  and derive it from the linter, never from a second document.
- Move a core-pack test out of `.apm/` and repoint it at the pack source in the
  same commit that moves it.
- Pair every relocation with its CI wiring — a suite that moves and loses its
  runner fails nothing and is invisible.

### Ask first

- Widening the migration past `core`. The other packs hold roughly 100 test files
  under `.apm/skills/*/scripts/`; migrating them is a separate decision.
- Changing what `catalogue package` includes. Tests reaching the archive is
  intended; suppressing them is an agentbundle change with a release implication.

### Never do

- **Never relocate `evals/`.** They are skill-local runtime content at
  `.apm/skills/<skill>/evals/`, projected with the skill, and the linter enforces
  that placement. An earlier draft of this policy moved them to a pack-root
  directory; that was wrong for the current contract (ADR-0071).
- **Never infer the boundary holds from the installer's behaviour.** Assert the
  projection is clean directly. The implicit exclusion is what let the violation
  persist.
- **Never widen an acceptance criterion to match what the code already does.**
  AC10 was narrowed to core-owned skills because the deferred packs make a
  repo-wide claim false — narrowing the scope is honest, relaxing the check is not.

## Assumptions

- Catalogue archives may carry `tests/`; `package.py` walks `packs/**` wholesale
  while the installer reads only `seeds/` and `.apm/`. Confirmed as intended:
  tests are visible in the catalogue and never installed.
- Evals are **not** relocated. `.apm/skills/<skill>/evals/` is the enforced
  layout — the linter requires `eval_queries.json` there for every skill named
  in `[pack.evals].skills`, and the adapters project the skill directory
  wholesale. Recorded in ADR-0071.
- Nothing in `catalogue verify` enumerates or rejects unknown pack subtrees.
  `lint_packs._PACK_SUBTREES` walks only `seeds/` and `.apm/`;
  `_step_primitive_layout` returns no diagnostics. `packs/_example/evals/` is
  existing precedent for a non-`.apm` pack subtree.
- Moved tests target the pack source rather than the projection. Projection
  fidelity is separately gated by the self-host drift check.

## Testing strategy

Each moved suite is its own oracle and must pass from its new home. Beyond
that, two checks exist because this change could otherwise pass silently:

- A **positive** assertion that the projected tree contains no test file —
  absence inferred from "the installer ignores it" is what created the defect.
- The **guidance-drift** layer in `test-lint-knowledge.py`, falsified in both
  directions: remove a required key from a surface's inline list, and remove
  `source` from a documented example; both must fail, and pass once restored.

`build-check` does not cover the hook pytest suites. Running the full set
matters: an intermediate state had `build-check` green while all 30 hook tests
were broken by a wrong `parents[]` depth.
