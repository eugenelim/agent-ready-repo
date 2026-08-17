# Plan: pack-test-boundary-remaining-packs

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done (superseded in part by ADR-0085 — `git check-ignore` is now invoked over NUL-delimited stdin, so AC10a's `--` argv terminator no longer applies; everything else stands) <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The completed `pack-test-boundary` loop proved the shape on two packs. This is
the same move applied seven more times, and the risk profile is the same: **the
relocation is trivial, the sweep is not.** Nothing in `make build-check` runs a
pytest suite, so a suite that loses its runner, resolves its subject one
directory too high, or skips itself on a missing dependency is invisible to the
aggregate gate.

Four things make this loop harder than the last rather than merely longer.

**Sibling imports.** Core's suites mostly resolved their subject explicitly.
These do not: `import render`, `import _sso_config`, `import ssrf_check` work
only because pytest's `prepend` import mode puts the test file's own directory on
`sys.path`. After the move that directory is the test tree. A `conftest.py` per
destination directory supplies the insert and the existence guard for the suites
that load one — but the guard obligation is **per file, not per directory**: the
`__main__` harnesses run under `python <file>` and never load a conftest even
when one sits beside them, so they carry the guard inline.

**Same-named modules.** Derive the set, don't read it:
`git ls-files ':(glob)packs/*/.apm/skills/*/scripts/*.py' | xargs -n1 basename |
sort | uniq -d` — subject-module basenames repeat across skills, three
`render.py` and a byte-identical `ssrf_check.py`/`write_jail.py` pair among them.
Their test modules collide by basename too. A single `pytest packs/*/tests/`
process is therefore *incorrect* —
pytest refuses the duplicate basenames, and if it did not, the first `render`
imported would serve all three renderers. The existing one-process-per-skill
topology is preserved exactly; only the directory each step points at changes.

**Self-skipping control suites.** Several relocated suites gate themselves —
at module scope (`pytest.importorskip("credbroker")`), per test
(`@requires_crypto`), or in-function (`importorskip("docx")`). Derive the set —
`grep -ln 'importorskip\|skipif'` over
the moving files — because the obvious guess is wrong: `test_setup_sso.py` is in
both SSO trios and does *not* self-skip, while `test_auth_selector.py` does and
has no runner at all. If a repoint detaches a step from the
`pip install credbroker[crypto]` twenty lines above it, pytest exits 0 with the
file wholly skipped and every acceptance criterion still passes. The mitigation
is an in-step hard import naming each real dependency, not a comment.

**Two protected trees, not one.** `lint-catalogue-curation-guard.py` protects
`packs/credential-brokers/` with no `/tests/` carve-out. Creating
`packs/credential-brokers/tests/` trips it exactly as an engine edit would.

Order: pin the constraints, relocate pack by pack, sweep, then widen the guard.
The guard goes last on purpose — widening it before the moves land would red the
tree for the duration.

## Constraints

- `.apm/` is the runtime export boundary. Nothing that isn't installable goes
  there, regardless of what the current installer ignores.
- No repository-root `tests/` — RFC-gated by `CLAUDE.md`.
- `evals/` never moves.
- `packs/AGENTS.md` has a hard 150-line CI cap.
- `Engine-Change-RFC:` trailer on any commit touching `packages/agentbundle/**`
  outside `/tests/` **or** `packs/credential-brokers/**` at all.
- Every non-cosmetic pack-content change bumps `pack.toml` **and**
  `.claude-plugin/plugin.json` in lockstep, adds a `docs/product/changelog.md`
  section, and re-runs `FORCE=1 make build-self` (`packs/AGENTS.md`,
  `packs/AGENTS.local.md`).
- Shipped content — `packs/**/.apm/**`, `packs/**/seeds/**`, `guides/_shared/**`
  — cannot reference `tools/`, `make build-self`, `docs/specs/`, or
  `.github/workflows/`.
- ADR bodies are frozen. ADR-0071's Consequences prose is not edited.

## The uniform relocation recipe

Applied identically in T2–T5; stated once so each task names only its deviations.

**Destination.** `packs/<pack>/.apm/skills/<skill>/scripts/test_*.py`
→ `packs/<pack>/tests/skills/<skill>/test_*.py`, via `git mv` so history follows.

**Anchor.** From `packs/<pack>/tests/skills/<skill>/`, `parents[3]` is
`packs/<pack>`. A `conftest.py` anchored on the **skill root** — so the skills
with no `scripts/` directory use the same shape — goes in each
destination directory holding a suite that uses bare sibling imports. It buys
exactly two things: the `sys.path` insert and the existence guard. It does **not**
supply module-level constants; conftest globals are invisible to test modules, so
roughly half the Python suites still get an edited path expression of their own.

```python
"""Resolve <skill>'s runtime tree for the tests that exercise it.

Tests live outside the runtime payload (ADR-0071); the modules they exercise
live under .apm/. Nothing here is projected into an installed environment.
"""
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "<skill>"
if not SKILL.is_dir():                        # wrong parents[] depth after a move
    raise SystemExit(f"skill root not found at {SKILL}")
if (SKILL / "scripts").is_dir():
    sys.path.insert(0, str(SKILL / "scripts"))
```

**The guard obligation is per file, not per directory.** A conftest only guards
the suites that *load* it. Three kinds of file do not, and each carries the
`raise SystemExit` check inline:

- the `__main__` harnesses — every `test_exit_codes.py` and `test_next_ordinal.py`
  — which run under `python <file>` and never load a conftest even when one sits
  beside them in the same destination (`packs/atlassian/tests/skills/jira/` holds
  both kinds). `test_exit_codes.py`'s `CLI = HERE / "jira.py"` is exactly what a
  wrong depth breaks, silently;
- `pipeline.test.js`, whose equivalent is an `fs.existsSync` + `throw` before its
  `module.paths.unshift` (AC2a). Its two siblings need nothing: a `require()` of
  a wrong-depth relative path already fails loudly with `MODULE_NOT_FOUND`;
- any suite in a destination that gets no conftest at all, because nothing there
  uses a bare sibling import. Derive them, don't assume the list is short —
  today it is `test_research_retrievers_conformance.py` (loads its subjects via
  `importlib.util` with explicit paths),
  `test_desk_research_project_start_elicitation.py` (reads a `SKILL.md` as text),
  `jira-team-status/test_contract.py` (stdlib only, reads two skills' files), and
  `architect-diagram/test_fixtures.py` (stdlib only, globs its own `testdata/`).
  The last is the sharpest case: its `sorted(TESTDATA.glob("*.mmd")) if
  TESTDATA.is_dir() else []` degrades to one skipped `no-fixtures` param and
  exits 0 on a wrong path — a silent pass, not a red suite. None needs the
  `sys.path` insert; all need the depth guard.

**Every module-level path expression, and each to its own destination.** There
is no uniform rule. Enumerate the sites first —
`grep -n 'Path(__file__)\|sys\.path' <moving files>` — then classify each against
the shapes below and repoint accordingly:

| The anchor denotes | Shape | Examples |
|---|---|---|
| the skill's `scripts/` | `HERE = Path(__file__).resolve().parent`, used for sibling scripts | `jira/test_exit_codes.py`'s `CLI = HERE / "jira.py"`; `msg-to-markdown/test_drift.py`'s `HERE` **and** its `HERE.parent.parent / "file-to-markdown" / "scripts"`; `test_security.py`; the three `markdown-to-*/test_render.py` |
| a *sibling of* `scripts/`, **derived from `HERE`** | the same `HERE`, then `.parent / "<dir>"` | `test_reconcile.py`'s `REF = HERE.parent / "references"`; `test_convert.py`'s `SAMPLE_DOCX = HERE.parent / "evals" / …` — these resolve correctly once `HERE` points at `scripts/`, so they need no separate edit |
| a *sibling of* `scripts/`, **independent of `HERE`** | its own `Path(__file__)` chain | `test_tier3.py`'s `_GROUNDING = Path(__file__).resolve().parent.parent / "references" / …` — that file defines **no** `HERE`, so it inherits nothing and must be repointed to `parents[3] / ".apm" / "skills" / "file-to-markdown" / "references"` on its own. Enumerating by `grep -n 'Path(__file__)'` rather than by `HERE` is what catches it |
| the skill root | `_SKILL_DIR = Path(__file__).parent.parent` | `jira-team-status/test_contract.py`, which then reaches the sibling `jira-story-triage` |
| the **repo root** | `parents[4]` | all three engine-tree suites in T5 — `test_research_retrievers_conformance.py`, `test_credential_setup_skill.py`, `test_desk_research_project_start_elicitation.py`. Re-anchor each to `parents[3]` (the pack) and drop the repo-root hop, since every target is inside the pack |
| **the test's own directory** | `HERE / "testdata"` | `msg-to-markdown/test_parity.py`; `architect-diagram/test_fixtures.py` — because AC3 moves `testdata/` beside them |

The last row is the trap: `test_parity.py` sits in the same destination as
`test_drift.py`, `test_convert.py`, and `test_security.py`, which mean the
opposite. Applying one rule to the directory reds two suites.

The per-suite checklist item is "every module-level `Path(__file__)` expression
and every in-test `sys.path` mutation", not "the `HERE` line" —
`file-to-markdown/test_convert.py` has two module-level anchors (`HERE`,
`_SCRIPTS`), `test_tier3.py` names its third `_GROUNDING`, and
`credential-setup/test_setup.py` performs its own `sys.path.insert` which must be
removed in favour of the conftest.

**Test-only support files move too** — `msg_fixtures.py`, `scripts/testdata/`.
Their consumers address them relative to the test file, so they land beside it.

**Runner** repointed by the task that moves the suite, so a suite and its runner
never separate. Ownership:

| Owner | Consumers |
|---|---|
| T2, T3, T4 | that pack's own `build-check.yml` steps — `working-directory:`, bare filenames, the in-step hard imports and minimum-collected assertions AC6c requires, and AC6d's cache-hardening restatement. T3 also repoints `tools/check-atlassian-phase3-readiness.py` (it invokes one of its suites by absolute path) and splits `tools/test-lint-sso-config.py`'s `_DUPLICATED` tuple |
| T5 | the two *additive* invocations for `packs/desk-research/tests/` — one `Makefile` line, one command line in the CI pack-tests step's `run:` block. Additive, so no other task's edit is disturbed |
| T6 | `self_host_windows.py` (and its test), the `workspace.toml` backlog retirement + the predecessor spec's deferral marker, and the `tools/test-all.py` addition of `tools/test-lint-sso-config.py`. **Verification only** for `Makefile` (T1's comment, T5's line), `catalogue-tooling-ci-gates.yml` (T5's line), `docs.yml` (T7's), `tools/test-lint-sso-config.py` (T3's), `check-atlassian-phase3-readiness.py` (T3's), `bandit.yaml` and `.gitleaksignore` (AC16 — recorded, not edited), and every `build-check.yml` step T2–T4 repointed. Plus two sanctioned deferrals: the credential-setup step's argument list for `test_credential_setup_skill.py`, and `self_host_windows.py`'s atlassian cwds (protected engine tree — trailer + release batching) |
| T7 | `tools/test-all.py`'s `pack-runtime-boundary` entry and `docs.yml`'s guard steps, because the guard's path moves in T7 |

**Fixture review (AC5a).** Every task reviews the fixture material it moves for
credentials, secrets, and real personal data, and records the result in
`notes/suite-parity.md`. Registered-but-fabricated domains are noted, not
rewritten — that is the deferred `test-fixture-domain-normalisation`.

**Verification per suite.** Run at the old path, record collected/passed; run at
the new path, record the same; write the row to `notes/suite-parity.md`. A suite
whose dependency is absent here is recorded not-run with the reason.

## Tasks

### T1 — Pin the constraints before anything moves

**Depends on:** none

**Tests:** goal-based. The empirical basis is already gathered (pytest 9.0.3
errors `import file mismatch` on two same-named test modules in one run); this
task records it where a reader would try to consolidate.

**Approach:** Two things a future author cannot re-derive from the result:
AC6b's collision constraint and AC6c's runner manifest. Add the constraint as a
comment at `Makefile`'s `test` target (the single place consolidation is
tempting) and scaffold `notes/suite-parity.md` with its two tables — per-suite
before/after, and runner coverage keyed by **destination directory or suite**
(AC6c's schema: a directory row per destination, plus a suite row for anything
that directory's runner does not name) — plus a third section for AC5a's
fixture review, one line per moved fixture file or directory.
Drop the stale "(38 suites)" parenthetical from the `Makefile` comment. The
mechanical assertion of the constraint belongs to T7's self-test and the § 4
prose to T8; T1 does not claim them.

Also flip `spec.md` to `Status: Implementing` here, before any file moves —
`docs/CONVENTIONS.md` requires it before code changes begin, and T9 owns the
later flip to `Shipped`.

**Done when:** the `Makefile` comment states the constraint and no longer names a
suite count; `notes/suite-parity.md` exists with its three sections headed and empty;
`spec.md` reads `Status: Implementing`.

### T2 — converters

**Depends on:** T1

**Tests:** each suite is its own oracle; before/after recorded.

**Approach:** Recipe for `file-to-markdown`, `markdown-to-docx`,
`markdown-to-pptx`, `markdown-to-xlsx`, `msg-to-markdown` (plus
`msg_fixtures.py` and `testdata/`).

**Runners, in this task's commits.** Five `build-check.yml` steps address these
suites by `working-directory:` plus bare filename — the three `markdown-to-*`
renderer steps, the `file-to-markdown` extraction step
(`test_contract.py test_safe_io.py test_convert.py test_reconcile.py`), and the
`msg-to-markdown` step. Repoint each `working-directory:` and leave the filenames,
the preceding `pip install` pin, and the step order alone.

`test_convert.py` self-skips in-function on the office libraries, and its runner
**can** satisfy them: `build-check.yml` is a single job, and the RFC-0036 step
installs `python-pptx`, `docxtpl`, `openpyxl` and `python-docx` twenty lines
above the file-to-markdown step, and `python-pptx==1.0.2` declares
`Pillow>=3.3.2`, so `PIL` arrives transitively. That makes it AC6c's *first*
case, not its second: add the in-step probe
`python -c "import docx, openpyxl, pptx, PIL.Image"` to that step's `run:` block,
because the coupling is exactly the reorder-fragile kind AC6c guards — move the
RFC-0036 install below this step and those cases skip silently.

`test_split_image.py` self-skips on `PIL.Image` and is named by **no** runner
anywhere, so it takes a per-suite `none (pre-existing)` row — as do
`test_rasterize_pdf.py`, `test_text_crosscheck.py` and `test_tier3.py`, which
that step also does not name.

`render-proof/test/*.test.js` is the deviation, and it splits three ways. Node
resolves `node_modules` by walking up from the *requiring* file — but every
third-party `require` in this skill lives inside `scripts/render-proof.js`,
behind lazy call-site requires, and that file does not move. So it keeps
resolving `markdown-it`, `jsdom`, `dompurify`, `shiki` and `react` from its own
location regardless of where the test sits.

Repoint **every** require of the skill's own script in **all three** files,
module-level and in-function — `renderer.test.js` carries two (module scope and
inside the `renderProof` case), `security.test.js` and `pipeline.test.js` one
each — so a first-match edit ships a half-broken suite with no oracle. Count the
*target*, not the old prefix: `grep -c "require(.*render-proof\.js"` — no
trailing `)`, since a quote sits between `.js` and `)` in the source and the
closing paren makes the pattern match nothing, giving a vacuous `0 == 0`.
Verified counts today: `pipeline` 1, `renderer` 2, `security` 1. Capture those
numbers and compare them explicitly after the edit rather than reading grep's
exit status (`grep -c` exits 1 on zero matches). Then assert
`! grep -q "'\.\./scripts/" <file>` on each, since the new path is
`../../../.apm/skills/render-proof/scripts/…`.

- `renderer.test.js` — repoint both occurrences, correct the `run with:` header,
  nothing more. Its deps are all inside the non-moving module; a `node_modules`
  guard would gate on something it never needs.
- `security.test.js` — repoint plus **one behavioural change**. It proves that a
  valid path inside the confinement root is accepted by resolving
  `evals/files/fixture.md` against `process.cwd()`, which worked only while the
  suite ran from the skill directory. Have it create and remove its own file in
  the root instead: an eval fixture is skill-local *runtime* content (ADR-0071),
  so a suite in the pack's test tree reaching across that boundary for one is the
  same coupling this whole change removes. The assertion's meaning is unchanged —
  an existing path inside the root is accepted.
- `pipeline.test.js` — the only file that requires `@a2ui/*` **directly**, so on
  top of its own `render-proof.js` repoint it also
  gets `module.paths.unshift(path.join(SKILL, 'node_modules'))`, preceded by an
  `fs.existsSync` throw: `unshift` of a missing directory is a silent no-op and
  Node falls through to the ancestor chain, `$NODE_PATH` and
  `$HOME/node_modules`, so a wrong depth would bind some other copy rather than
  failing. `npm install` in the skill directory makes this a real green run
  rather than a resolution-mechanism argument — `node_modules/` is gitignored, so
  nothing is committed. Verified: `renderer.test.js` and `security.test.js` pass
  from the new home *without* the `unshift`, which is the evidence that scoping
  it to `pipeline.test.js` is right rather than merely convenient.

Fixture domains are reviewed, not rewritten (AC5a): `corp.com` is coupled across
`msg_fixtures.py` and the byte-compared `msgreader_baseline.json`, and
`evil.com` sits inside `renderer.test.js`'s CSS-escape bypass assertions, which
cannot be run here. Deferred as `test-fixture-domain-normalisation`.

**Done when:** `packs/converters/.apm` carries no test-shaped file or directory;
`msg-to-markdown/scripts/testdata/` no longer exists and `msg_fixtures.py` is
absent from that `scripts/` dir (AC3's own oracle — the boundary matcher matches
neither, so AC1 cannot see them); the file-to-markdown extraction step carries
`python -c "import docx, openpyxl, pptx, PIL.Image"`; each relocated JS suite's
`grep -c "require(.*render-proof\.js"` still returns its captured before-count
(1 / 2 / 1) and no `'../scripts/` string survives in it; all three
`// run with: …` headers are corrected; every Python suite matches its
before/after row; every fixture this task moves has an AC5a review line in
`notes/suite-parity.md`.

**Touches:** `packs/converters/tests/skills/**` (new), the moved sources,
`packs/converters/.apm/skills/msg-to-markdown/SKILL.md` — its `## Scripts` list
names `scripts/msg_fixtures.py`, `scripts/test_*.py`, `scripts/testdata/`, and
that bullet is **deleted**, not repointed: those files leave the skill, and
`packs/<pack>/tests/` is no more present in an adopter's tree than `tools/` is.

### T3 — atlassian

**Depends on:** T1

**Tests:** as T2. The SSO suites need `httpx` and `credbroker`; both installable
here, and both must be *present* for the run to mean anything — a skipped
`importorskip` is recorded as not-run, never as a pass.

**Approach:** Recipe for `jira`, `confluence-crawler`, `confluence-publisher`,
`jira-align`. `jira-team-status/tests/test_contract.py` is already in a `tests/`
directory but under `.apm/`; it resolves `_SKILL_DIR = parent.parent` and reaches
a *sibling* skill (`jira-story-triage`), so its anchor becomes the **skill root**
— `parents[3] / ".apm" / "skills" / "jira-team-status"`, reaching the sibling via
`.parent` — not a scripts dir.

**Runners, in this task's commits.** Two `build-check.yml` steps run the SSO
trios by `working-directory:` plus bare filenames. Repoint both, leave the
preceding `pip install 'httpx>=0.27'` and the step order alone, and add the
in-step probe `python -c "import credbroker, httpx"` — both trios self-skip on a
missing `credbroker` and would exit 0 wholly skipped. `test_auth_selector.py`
also self-skips and has no runner at all: `none (pre-existing)` in the manifest,
not a silent omission.

`tools/check-atlassian-phase3-readiness.py` invokes pytest on
`jira-team-status/tests/test_contract.py` by absolute path and returns
`status="fail"` with `MISSING: …` if the file is not there — repoint it here, in
the same commit as the move.

`tools/test-lint-sso-config.py`'s `_DUPLICATED` tuple (at that file — **not**
`tools/lint-sso-config.py`, which references no moving path) pins five files
byte-identical across `jira` and `confluence-crawler`. The tuple **splits**: two
runtime files (`_sso_config.py`, `setup_sso.py`) stay under `.apm/.../scripts/`,
three test files move. Two path bases, both parity checks retained. Treating it
as a single repoint breaks the pin — loudly, since `_parity_failures` reports
`missing duplicated file`, but breaks it.

**Done when:** every relocated suite in this task matches its before/after row —
not just the SSO trios, but the four `test_exit_codes.py`, both
`test_auth_selector.py`, and `jira-team-status/test_contract.py`;
`packs/atlassian/.apm` carries no test-shaped file or directory; both SSO trios
pass with `credbroker` and `httpx` genuinely importable, and both repointed steps
carry `python -c "import credbroker, httpx"` in the same `run:` block;
`tools/test-lint-sso-config.py` green;
`tools/check-atlassian-phase3-readiness.py`'s `atlassian-deterministic-tests`
check passes.

Note `tools/test-lint-sso-config.py` is executed by no workflow and appears in no
`Makefile` target or `tools/test-all.py` entry — the pin it guards is the most
breakable thing in this task and is ungated. T6 wires it into `tools/test-all.py`
and records it in the runner manifest either way.

### T4 — catalogue-curation, governance-extras, figma, credential-brokers, architect

**Depends on:** T1

**Tests:** each suite is its own oracle; before/after recorded. `architect`'s
suite needs the Mermaid CLI (`mmdc`) and is recorded not-run if absent — its CI
status is unchanged either way.

**Approach:** Recipe for `assimilate-primitive`, `assimilate-repo`, `new-adr`,
`new-rfc` (same basename `test_next_ordinal.py` in two skills → two directories,
two processes), `figma`, `credential-setup`, `architect-diagram` (plus
`testdata/`).

`architect-diagram/scripts/` holds nothing but the test and its fixtures, so the
directory is removed, not emptied — confirm no SKILL.md, manifest, or projection
recipe references it first.

**Runners, in this task's commits.** Two `build-check.yml` surfaces: the
credential-setup step (`working-directory:` plus `test_setup.py`), which also
gets the probe `python -c "import credbroker, cryptography, argon2"` — *not*
`httpx`, which that suite never imports and which CI installs eleven lines below
this step; and the catalogue-curation step, one step with two `cd`-scoped
`pytest -q` invocations, which gets both directories repointed, a
minimum-collected assertion per invocation, and AC6d's corrected reason on its
`PYTHONDONTWRITEBYTECODE` env and `-p no:cacheprovider` flags. `figma`,
`architect-diagram` and both `new-*` ordinal suites have no runner: manifest rows,
not silence.

`new-adr`/`new-rfc`'s `test_next_ordinal.py` carry an in-file
`sys.dont_write_bytecode = True` justified in-comment by the self-host drift gate
— the same reason AC6d retires. Restate it (the unfiltered `packs/**` archive
walk, not the drift gate); keep the hardening.

`credential-brokers` is a fully-protected tree with no `/tests/` carve-out in
`lint-catalogue-curation-guard.py`, so this commit carries
`Engine-Change-RFC: n/a — test relocation under ADR-0071; no credential-broker
behaviour or interface change`.

`catalogue-curation` and `governance-extras` are among the packs this repo
projects (`self-host.toml [recipe.packs].include`), so their relocated test files
have tracked twins under `.claude/skills/` and `.agents/skills/` — enumerate with
`git ls-files '.claude/skills/**' '.agents/skills/**' | grep -E '/test_[^/]*\.py$'`.
`FORCE=1 make build-self` deletes them; without it `catalogue verify`'s
self-host drift gate reds and AC10 cannot pass.

**Done when:** the five packs' suites match before/after; none of the five packs'
`.apm/` trees carries a test-shaped file or directory; the credential-setup step
carries `python -c "import credbroker, cryptography, argon2"` and **not** `httpx`;
the catalogue-curation step's two invocations each carry a minimum-collected
assertion and AC6d's corrected reason;
`packs/architect/.apm/skills/architect-diagram/scripts` no longer exists; and
`! git ls-files '.claude/skills/**' '.agents/skills/**' | grep -Eq '/test_[^/]*\.py$'`
succeeds **after staging** — `build-self` deletes the twins from the working tree
but `git ls-files` keeps reporting them until the deletions are in the index.

### T5 — the pack-subject suites in the engine's tree

**Depends on:** T1, T4 (its destination directory and conftest come from T4)

**Tests:** run under the engine's pytest before the move (they are in
`testpaths`), and from the new home after.

**Approach:** Three suites, not two — `test_desk_research_project_start_elicitation.py`
has the same shape as the pair the deferral note named (it anchors on
`desk-research-project-start/SKILL.md` and asserts only on that prose) and moves
to `packs/desk-research/tests/skills/desk-research-project-start/`. Finding it
mid-EXECUTE via T5's own "re-derive by reading each remaining unit test's
subject" step would force a scope call; it is in scope now.

`test_research_retrievers_conformance.py` →
`packs/desk-research/tests/skills/desk-research/`;
`test_credential_setup_skill.py` →
`packs/credential-brokers/tests/skills/credential-setup/`, beside `test_setup.py`
from T4 — which puts it under an existing build-check step with
`credbroker[crypto]` already installed, but does **not** make it run: that step
is `python -m pytest test_setup.py`, a bare filename. T6 extends that argument
list to name it. Landing next to a runner is not the same as having one.

`desk-research` has no runner at all and its two suites would silently stop
gating: all three suites in this task gate today only by sitting inside a package
tree that CI runs wholesale (`catalogue-tooling-ci-gates.yml`,
`release-agentbundle.yml`, `Makefile`). So `packs/desk-research/tests/` gets its
**own** invocation in this same commit — a separate
`$(PYTHON) -m pytest packs/desk-research/tests/ -q` line in the `Makefile` `test`
target, and in `catalogue-tooling-ci-gates.yml` a second command line inside the
pack-tests step's `run:` block (a step has one `run:` key), leaving the existing shared
`packs/core/tests/ packs/product-documentation/tests/` invocation untouched.
Appending to that shared invocation would leave the collected count obviously
non-zero even if nothing from `desk-research` landed, which is the vacuous pass
this spec's own risk register names — and a separate invocation also keeps
AC6b's one-invocation/one-basename-set rule trivially satisfied — the only
collision that matters for a separate `pytest packs/desk-research/tests/` run is
between that tree's own two suites, and their basenames differ.
`test_research_retrievers_conformance.py`
loads its subjects through `importlib.util` with explicit paths and needs **no**
conftest — adding one would insert a scripts dir at `sys.path[0]` for the whole
invocation. All three suites re-anchor from `parents[4]` (repo root) to
`parents[3]` (the pack), including `test_credential_setup_skill.py`.

Both new invocations carry a minimum-collected assertion (AC6c).

`packs/desk-research/.apm/skills/desk-research/SKILL.md` names the old path as
the single source of its closed cue tuples — shipped content with a dangling
reference the moment this lands. **Drop the path**, don't repoint it: neither
`packages/agentbundle/tests/` nor `packs/<pack>/tests/` exists in an adopter's
tree, so naming the new location reproduces the defect. Keep the provenance
sentence pointing at "the pack's conformance tests" without a path, or inline
the tuples.

The move itself is inside `packages/agentbundle/tests/`, which the engine guard
carves out — but the `packs/credential-brokers/` destination is not carved out,
so this commit carries the trailer too. Confirm the full agentbundle suite is
still green after the removal: that is the AC13 failure mode from the previous
loop, in reverse.

**Done when:** `pytest packages/agentbundle/` green; all three suites —
`test_research_retrievers_conformance.py`, `test_credential_setup_skill.py`,
`test_desk_research_project_start_elicitation.py` — green from their new homes;
both desk-research suites collected by the directory-scoped invocation this task
adds, and that invocation carrying its minimum-collected assertion
(`test_credential_setup_skill.py`'s runner is T6's, which extends the
credential-setup step's argument list, so its runner clause belongs to T6's
Done-when, not this one); no pack-subject suite remains in the engine's
tree, re-derived by reading each remaining unit test's subject.

### T6 — sweep every consumer

**Depends on:** T2, T3, T4, T5

**Tests:** goal-based, two-sided. Negative: `git grep -F` over every moving
**basename** to re-derive the consumer set, then assert zero surviving
occurrences of any **old path**, excluding AC6a's historical-record kinds. Not
zero occurrences of the basenames — the repointed `build-check.yml` steps
deliberately keep their bare filenames, `regen_msgreader_baseline.py` names
`test_parity.py` in prose and moves with it, and shipped-spec comments and RFCs
name same-basename engine tests. Positive: derive the destination
set from the *tree*, restricted to what this change added —
`git diff --name-only --diff-filter=A origin/main -- ':(glob)packs/*/tests/**'`
— `:(glob)` because a plain pathspec's `*` crosses `/` and would sweep in
`packs/atlassian/.apm/skills/jira-team-status/tests/`, and `--diff-filter=A`
because `--name-only` otherwise lists deletions and modifications, none of which
is a destination of this change. Filter the added paths through AC8's widened
shapes **as written in `spec.md`** — the prose, not `tools/lint-pack-test-boundary.py`,
which does not exist until T7 and whose predecessor's narrow matcher cannot see
`*.test.js`, so filtering through code here would drop
`packs/converters/tests/skills/render-proof/` out of the derived set entirely.
Filter before reducing to directory names, or the two relocated `testdata/`
fixture directories (AC3) come through as destinations that cannot name a runner. Then assert each directory appears in the runner
manifest carrying one of AC6c's permitted forms.
Deriving the set from the manifest would be circular:
a directory that lands on disk and never gets a row would be undetectable, which
is the dominant risk. A bare `packs/*/tests/skills/*/` glob is also wrong — it
matches core's four pre-existing skill test directories.

**Approach:** T2–T4 have already repointed their own `build-check.yml` steps; this
task verifies them and owns everything cross-cutting.

**Verify** T2–T4's `build-check.yml` work: every repointed step kept its
preceding `pip install`, its bare filenames, and its
position — nothing regrouped into one block, since `credbroker[crypto]` is
installed under a different concern and the SSO and credential-setup steps sit
below it. Confirm each in-step probe names that step's *real* dependencies and
that the credential-setup probe does **not** name `httpx` (that suite never
imports it and CI installs it eleven lines below the step, so the probe would
fail deterministically). The cache hardening lives at three sites only — the
catalogue-curation step's `PYTHONDONTWRITEBYTECODE` env plus `-p no:cacheprovider`
on both its invocations, and the two in-file `sys.dont_write_bytecode` lines in
`new-adr`/`new-rfc` — so verify AC6d's restated reason there, not on the eight
`working-directory:` steps, which never carried it.

**Own** the two deferred runner edits. First: extend the credential-setup step's
argument list to name `test_credential_setup_skill.py`, which T5 lands in that
directory with no runner of its own. Second: `self_host_windows.py`'s two
atlassian SSO cwds. That one is deferred from T3 deliberately — the file is in
the protected engine tree, so its commit needs the `Engine-Change-RFC:` trailer
and is batched with T9's release; the cost is that the SSO trios have no Windows
runner between T3 and T6, inside a single PR.

`self_host_windows.py` carries the atlassian SSO pair with the scripts dir as
cwd — repoint both, and add a preceding SSO dependency-probe step
(`python -c "import credbroker, httpx"`) or record that runner as unprobed in the
manifest: its `_step` checks only the return code, so a Windows machine without
`credbroker` skips both trios and reports pass. Its own test is updated alongside
it:
`packages/agentbundle/tests/unit/test_self_host_windows.py` builds a fixture tree
at those two `scripts/` dirs and asserts each is a step cwd. A basename grep
misses it (the paths are assembled from multi-line `Path` parts), so the
re-derivation also runs `git grep -n '"packs"' packages/agentbundle/tests/`.
`self_host_windows.py` is under `catalogue_tooling/`, which
`check_release_impact.py` lists as release-impacting, so this commit carries the
`Engine-Change-RFC:` trailer and T9's release must be in the same PR.

Then `tools/test-all.py` — add `tools/test-lint-sso-config.py`, which no runner
executes today; the `pack-runtime-boundary` entry is T7's, since the guard has
not moved yet at this point.

**Retire the backlog deferral here, not in T8.** Remove
`pack-test-boundary-remaining-packs` from `workspace.toml [backlog].open`
**together with the comment block above it** — that comment, not the
`{slug = ...}` line, is where the two old engine-tree paths live, and this task's
own assertion is that no old path survives. Resolve the deferral marker naming
that slug on AC13 of `docs/specs/pack-test-boundary/spec.md` in the **same
commit**: `lint-spec-status.py` treats an unresolvable anchor as a hard failure
inside `build_gate_chain.py`. Of the other two `workspace.toml` edits — neither
of which names an old path — T8 adds the new deferrals and T9 makes the
`active` → `shipped` move.

Verification only, no edit: `Makefile` and `catalogue-tooling-ci-gates.yml`
(T5's additive invocation and T1's comment are their whole involvement — neither
file names a moving path; their existing pack-test lines name core and
product-documentation), `docs.yml` (its `packs/**` trigger already covers the
moving files; the only reference to a moving path is the guard run step, which is
T7's), `tools/test-lint-sso-config.py` (T3 owns the `_DUPLICATED` two-base split;
confirm it still holds), and `tools/check-atlassian-phase3-readiness.py` (T3's
repoint), and `bandit.yaml` — whose `*/tests/*` glob already covers
`packs/*/tests/**`, so the relocated files drop out of the bandit scan with no
edit at all. That is the coverage change AC16 retains: nothing to change,
something to write down.

`.gitleaksignore` needs no edit up front: its five fingerprints are anchored to
*historical* commits that still carry the old paths, and `ci-security.yml` falls
back to a full-history scan when `BASE_SHA` is absent, so they must be **kept**.
If the range scan flags the relocated fixtures at their new paths, suppress with
inline `# gitleaks:allow` — a fingerprint minted on a PR-branch commit dies at
squash-merge.

**Done when:** both sides of the assertion hold, with the backlog retirement in
this task's commits so the old-path half can hold; the predecessor spec's
deferral marker is resolved in that same commit and
`python3 packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py --root .`
reports no hard failure — the pair is what keeps `make build-check` green, and
splitting it across tasks reds it; `test_credential_setup_skill.py`
is named by the credential-setup build-check step; AC6d's corrected reason is
present at all three cache-hardening sites and nowhere else was given one it
never had; AC5's two evals checks pass
(`git diff --stat origin/main -- 'packs/*/.apm/skills/*/evals/**'` empty and
`catalogue verify`'s eval linter green); `tools/test-all.py`'s
`tools/test-all.py` is green as a whole. When this plan was written it was not —
two entries named files that did not exist — so it only claimed the individual
entries. #874 retired those upstream and closed `test-all-dangling-entries`
before this branch rebased, so the aggregate is now a real assertion.

### T7 — widen the guard and move it out of `core`

**Depends on:** T6

**Tests:** TDD, both directions, as permanent cases in the new self-test.

**Approach:** `packs/core/tests/pack/test-runtime-boundary.py` →
`tools/lint-pack-test-boundary.py`. `tools/` is where this repo's cross-cutting
lints already live, it is pure-stdlib Python per `CLAUDE.md`, and it is not
pack-owned — which § 4 requires for behaviour no single pack owns. Add
`tools/test-lint-pack-test-boundary.py` beside it, matching the
`tools/test-lint-*.py` convention.

Five changes beyond the pack iteration:

- Rewrite the module docstring's scope paragraph. It says the other packs "still
  hold tests under `.apm/skills/*/scripts/` — tracked in
  `workspace.toml [backlog].open` as `pack-test-boundary-remaining-packs`", and
  explains the core-only scoping. Both are false after this PR, the entry is gone
  by T6, and nothing gates it: `lint-spec-status.py` scans `docs/specs/` only and
  T6's sweep runs first. Unlike ADR-0071 and the predecessor spec, this file is
  not a frozen record — it is being rewritten here anyway.
- Assert AC6b mechanically, **against the runners, not the tree**. Overlapping
  basenames across destination directories are the expected end state — a lint
  that reds on them reds on a correct implementation. So the self-test derives
  the per-directory basename sets, parses the runner call sites (`Makefile`
  pytest lines, CI `run:` blocks, `tools/test-all.py` entries,
  `self_host_windows.py` steps), and fails when one invocation covers two
  directories whose sets intersect. No other task claims this; T1 only records
  the constraint in prose.

- Widen `_TEST_FILE` **and** `_TEST_DIR` (AC8). The singular `test/` is the shape
  this change discovered; `tests` alone would have stayed blind to it.
- Replace `Path.rglob("*")` with `os.walk(root, followlinks=False)` plus an
  explicit `dirnames[:]` symlink prune, matching `package.py`'s archive walk —
  the guard and the walker that decides what ships must not disagree about what
  pack content is. Add the `--` terminator to `git check-ignore` and batch paths
  over stdin rather than one subprocess per file.
- Make the projection half per-pack against `self-host.toml`'s
  `[recipe.packs].include` (AC10). A single global `checked` counter is satisfied
  by core alone, so a pack dropping out of the projection would pass silently.
- Restate the positive half per-pack and drop the hardcoded `len(suites) < 10`
  (AC10b), which fails for every pack that owns no tests.

Keep the deliberate non-matches and say why in the source: `evals/` is
runtime-adjacent by decision; a bare `test` substring would false-positive on
reference material *about* testing; `__pycache__`/`.pytest_cache` are gitignored
residue, and since 0.29.5 the archive walk prunes it too.

Repoint `tools/test-all.py`'s `pack-runtime-boundary` entry — the path moves in
*this* task, so this is where it changes, or the runner gains a third dangling
entry — and add the self-test beside it (local only; no workflow executes
`test-all.py`). The projection half reads
`packages/agentbundle/agentbundle/build/recipes/self-host.toml`'s
`[recipe.packs].include`. Add both files to `docs.yml`'s `paths:`, repoint its existing run
step, and **add a second run step for the self-test** — `docs.yml` is the job
that actually gates the guard, and without that step AC9's permanent
falsification cases execute nowhere. Say which is which rather than implying
`test-all.py` gates anything in CI.

**Done when:** `python3 tools/lint-pack-test-boundary.py` **exits 0 against the
working tree** — the only assertion that closes AC1, since T2–T4 could only check
their packs with the narrow pre-widening matcher, which cannot see
`render-proof/test/*.test.js`; the guard covers every pack; both falsifications
are permanent cases; the guard's docstring names neither the retired backlog slug
nor a core-only scope; the self-test fails when a single runner invocation covers
two destination directories whose test basenames intersect (AC6b's assertion,
owned here and nowhere else); every matcher shape AC8 claims has a positive case
and every documented non-match a negative one; `docs.yml` triggers on and runs
both files;
`tools/test-all.py` names neither an old path nor a missing file it did not
already name.

### T8 — record the completed state

**Depends on:** T7

**Tests:** goal-based — `lint-agents-md.py` green; the standards guide still
renders in the doc-site index; `sync_authoring_scaffold.py --write` leaves no
diff on a second run; `lint-spec-status.py --root .` reports no *hard* failure
(this spec is not yet `Shipped` at T8, so invariant (ii) does not fire yet).

**Approach:** § 4 of `catalogue-authoring-standards.md` gains the
one-process-per-skill constraint at pattern level and a correction to its
*Repository-root tests* paragraph, which asserts this catalogue keeps such checks
in the engine's suite — the rehome makes that false. § 4 **must not name**
`tools/lint-pack-test-boundary.py`; shipped content cannot reference `tools/`.
`docs/architecture/pack-layout.md` may, and does, and carries the detail.
`packs/AGENTS.md` is at 149 lines against a hard 150 cap, so its existing
test-boundary line is *rewritten* to the shipped state with a pointer to
`pack-layout.md` — a replacement, not an addition.

Run `sync_authoring_scaffold.py --write` — `make build-check` misses that drift
and the agentbundle suite catches it.

Add the `adr-errata-convention`,
`test-fixture-domain-normalisation`, and `spec-ac-heading-casing-silent-gate`
deferrals to `[backlog].open` with cold-start-sufficient comments.

Two neighbouring `workspace.toml` edits are **not** T8's. The backlog
*retirement* is T6's — its comment block names old engine-tree paths, so it has
to be gone before T6's sweep asserts their absence (AC12). The
`["ini-007".work].active` → `.shipped` move is **T9's**, beside the `Shipped`
status flip: `workspace_status_engine.py` reports a "prematurely shipped" finding
for a `shipped` entry whose spec still reads `Implementing`, and a T8 move would
open exactly that window. When T9 makes the move, the block comment
above `active` collapses into an inline `# <version> — <summary>` comment on the
new `shipped` entry, matching the two entries already there.

ADR-0071 names `packs/core/tests/pack/test-runtime-boundary.py` at line 74 and
asserts the migration is partial. **It is not edited.** Its body is frozen, the
shipped `new-adr` template says only the Status line moves, and
`docs/CONVENTIONS.md` documents no errata concept for ADRs — the `## Errata`
mechanism is RFC-scoped in `new-rfc`. Extending it to ADRs would mean amending
`new-adr/SKILL.md`, its template, and CONVENTIONS.md, and bumping
`governance-extras` for the pack-content change: a governance change riding
inside an implementation PR, which `CLAUDE.md` routes through RFC. Deferred as
`adr-errata-convention`; this spec and `pack-layout.md` are the live record
meanwhile.

This spec's own `Status` and AC checkboxes are **not** touched here — it reads
`Implementing` from T1 onward and T9's final step flips it to `Shipped`.
`lint-spec-status.py`'s AC-completeness invariant is diff-triggered on the
transition into `Shipped`, and T9 still has the pack bumps (AC13) and the engine
release (AC14) to do, so flipping the status at T8 would either red the linter or
force ticking two ACs before their work exists.

`sync_authoring_scaffold.py --write` writes under
`packages/agentbundle/agentbundle/_data/catalogue-scaffold/`, inside the
protected engine tree and outside its carve-outs, so this commit carries the
`Engine-Change-RFC:` trailer too.

**Done when:** all surfaces describe the shipped state; `packs/AGENTS.md` < 150
lines; no scaffold drift;
`python3 packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py --root .`
reports no hard failure.

### T9 — bump the packs, release the engine

**Depends on:** T5, T6, T8

**Tests:** goal-based — `test_cli_version_matches_pyproject` passes; full package
suite green; `FORCE=1 make build-self` clean; `check_release_impact.py` green.

**Approach:** Two release surfaces.

The rules — which packs bump, why the increment is `patch`, why the lockstep has
no working gate, and why the engine release is triggered by T6 rather than T5 —
are stated once, in AC13 and AC14. This task is the mechanics.

*Packs.* Bump `pack.toml` + `.claude-plugin/plugin.json` together for each pack
in AC13's set, add its dated `docs/product/changelog.md` section, run the
per-pack version-equality check AC13 requires and capture the output, then
`FORCE=1 make build-self` to re-aggregate `marketplace.json`.

*Engine.* Bump `pyproject.toml` and `version.py`'s `CLI_VERSION` together
(0.29.4 → 0.29.5; they drift independently), add entries to
`packages/agentbundle/CHANGELOG.md` and `docs/product/changelog.md`, and check
`README-pypi.md` for a claim that the migration is partial. Trailer:
`Engine-Change-RFC: n/a — test relocation under ADR-0071; no engine behaviour or
public API change`.

*Then, and only then, close this spec.* The final commit sets `Status: Shipped`
in `spec.md` and `Status: Done` in `plan.md` and ticks every AC — atomically,
because `lint-spec-status.py`'s AC-completeness invariant fires on that
transition and every AC's work now exists. Any AC that did not land carries a
deferral marker resolving in `[backlog].open` instead. The
`["ini-007".work].active` → `.shipped` move happens in this same commit, with its
block comment collapsed to an inline `# <version> — <summary>`.

**Done when:** the per-pack version-parity check passes and its output is in the
PR; every touched pack has a dated changelog section; the engine's two version
sites agree; `marketplace.json` regenerated; `spec.md` is `Shipped`, `plan.md` is
`Done`, and `lint-spec-status.py --root .` is green with the transition in the
diff.

## Risks

- **Silent CI coverage loss.** The dominant risk, unchanged from the previous
  loop and broader here: eight `build-check.yml` steps address suites by bare
  filename relative to a directory this change invalidates, one runs a directory
  with no filenames at all, and the three engine-tree suites gate only by
  residence.
  Mitigated by T6 asserting both sides — zero hits on old paths *and* a positive
  runner manifest.
- **A control suite that skips instead of failing.** Several relocated suites
  self-skip — at module scope, per test, or in-function. A repoint that detaches a step from its install
  turns cookie-confinement and no-token-to-stdout assertions off while CI stays
  green. Mitigated by the in-step hard import (AC6c), which is the only mitigation
  that survives a future step reorder — and by deriving the self-skipping set
  rather than guessing it.
- **Wrong `parents[]` depth reads as green.** `make build-check` runs no pytest.
  Mitigated by the `raise SystemExit` / `throw` guard in every relocated *suite*
  — via its conftest where it loads one, inline where it does not — and by
  before/after counts per suite.
- **Same-named modules bound to the wrong subject.** If a future consolidation
  merges these into one pytest process, `import render` silently serves one
  skill's module to three suites, and `ssrf_check` / `write_jail` — pinned
  byte-identical across two catalogue-curation skills — are the worst case.
  Mitigated by T1's comment, T7's mechanical assertion, and T8's § 4 prose.
- **`render-proof`'s JavaScript suites are unverifiable here.** Dependencies are
  not installed and nothing runs them in CI. The move is mechanically correct and
  the resolution fix is testable against a planted stub, but a green run is not
  available; recorded rather than papered over.
- **Widening the guard before the tree is clean.** T7 is ordered last so the
  guard never reds work in progress. If a pack is dropped from scope mid-loop,
  the guard must be narrowed *by explicit exclusion with a reason*, never by
  quietly reverting the matcher.
- **Every pack this PR touches takes a version bump.** `packs/AGENTS.md` warns
  against riding an unreleased version from another in-flight PR; concurrent work
  on any of them will conflict, and the lockstep between `pack.toml` and
  `.claude-plugin/plugin.json` has no working gate. Mitigated by keeping the
  bumps in a single late commit (T9) so a rebase touches one commit, and by the
  explicit parity check T9 runs.

## Changelog

- Scoped in PLAN from the deferral note's `find` result to a repo-wide walk with
  the widened matcher, which surfaced `render-proof/test/*.test.js`. Including
  them is the point of AC8 — a matcher tuned to what the old `find` found would
  prove nothing.
- AC6b (process isolation) is net-new against the previous loop's plan,
  discovered empirically at PLAN time: core and product-documentation had no
  same-named suites, so a single-process run was safe there and is not here.
- Rewritten after the round-1 pre-EXECUTE adversarial and security passes. The
  material additions were the runner manifest and in-step dependency imports
  (control suites that would have gone silently green on a missing
  `importorskip`), the pack version-bump / `build-self` / marketplace surface
  (absent entirely from the first draft), the second protected tree
  (`packs/credential-brokers/`), the deferral-anchor coupling that would have
  redded `build-check`, the `tools/` reference ban in shipped § 4 content, and
  the anchor correction from `scripts/` to the skill root for the two skills with
  no `scripts/` directory.
- Converged over rounds 4–8, which were consistency work rather than design
  change: each round's surgical edits left stale counts or a spec/plan divergence
  for the next round to catch. Three findings did change the implementation. The
  `## Acceptance criteria` heading was lowercase, so `lint-spec-status.py` — which
  matches case-sensitively — collected zero criteria and the whole
  status-transition gate was vacuous (eight other specs carry the lowercase form,
  including this one's predecessor, and three more carry no criteria heading at
  all — eleven ungated in total; filed). Re-deriving the
  engine-tree set found a third pack-subject suite the deferral note never named.
  And the credential-setup dependency probe originally listed `httpx`, which that
  suite does not import and which CI installs *below* the step — it would have
  failed deterministically, and both obvious repairs would have removed a control
  guarantee.
- Revised after round 3, which caught four defects introduced by round 2's own
  surgical edits: the collision lint had inverted polarity (overlapping basenames
  across destinations are the *intended* end state, so the assertion had to move
  from the tree to the runner call sites); "zero hits for any old path"
  contradicted deliberately-retained historical records; `test_credential_setup_skill.py`
  was said to "inherit" a runner that names a bare filename; and the
  `pack-runtime-boundary` repoint was assigned to a task that runs before the
  path moves. AC5a's fixture-domain normalisation was also withdrawn — it couples
  a byte-compared parity baseline to an unrunnable JS suite's security
  assertions, which is not a mechanical ride-along.
- Revised after round 2. The corrections that changed the shape of the
  work: two more consumers, one of them *shipped* content
  (`desk-research/SKILL.md` single-sources its cue tuples from the engine test
  path being moved) and one that invokes pytest by absolute path
  (`check-atlassian-phase3-readiness.py`); the discovery that `testdata/`-reading
  suites mean the *test's* directory while their siblings in the same destination
  mean `scripts/`, so there is no uniform anchor rule; three assertions that were
  unsatisfiable against known-broken gates (`test-all.py` aggregate, the
  `plugin.json` parity probe, a no-`__pycache__` claim) rewritten to assert what
  can actually hold; and the ADR erratum dropped as a governance change that
  needs its own PR rather than a ride-along.
