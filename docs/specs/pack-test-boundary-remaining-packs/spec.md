# Spec: pack-test-boundary-remaining-packs

- **Status:** Shipped (superseded in part by ADR-0085 — `git check-ignore` is now invoked over NUL-delimited stdin, so AC10a's `--` argv terminator no longer applies; everything else stands) <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0071, `guides/_shared/reference/catalogue-authoring-standards.md` § 4
- **Completes:** `docs/specs/pack-test-boundary/spec.md` (Shipped; migrated `core` and
  `product-documentation` only)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

ADR-0071 decided three boundaries: the **pack** owns and runs its tests, `.apm/`
is the **runtime export** boundary, and a **skill** is the **evaluation-fixture**
boundary. `guides/_shared/reference/catalogue-authoring-standards.md` § 4 ships
those rules to adopters in its *Normative summary* — a list of MUST, MUST NOT,
MAY and SHOULD statements including *"Ordinary tests **MUST NOT** live under
`.apm/`."*

Two packs obey it. Seven do not, and the engine's own suite still owns
pack-subject tests. The gap is not cosmetic:

**1 — We ship a rule we do not follow, and adopters pay for it.** Projection
adapters copy `.apm/skills/<skill>/` wholesale. An adopter who installs
`converters` today gets our pytest suites written into their skills tree. That is
the exact failure ADR-0071 exists to prevent, live in seven packs.

**2 — Nothing stops a new pack regressing.** `packs/core/tests/pack/test-runtime-boundary.py`
is deliberately core-scoped so it fails on regressions rather than on deferred
work. That scoping was correct while the work was deferred and is the reason no
check fires today for the other packs. Widening it is the point of this change,
not a nicety attached to it.

**3 — The guard's own matcher is narrower than the rule.** `_TEST_FILE` matches
`test[-_]*.{py,sh,js,ts}` and `*[-_]test.*`; `_TEST_DIR` matches only `tests`.
Between them they miss `conftest.py`, `*.spec.ts`, `*_test.go`, `.ps1`, and —
demonstrated by this change — `*.test.js` inside a `test/` (singular) directory:
`packs/converters/.apm/skills/render-proof/test/` holds three such files and no
`find` in the deferral note ever saw them.

**4 — Pack-subject suites still red the published package.** AC13 of the
completed spec names two and defers them:
`packages/agentbundle/tests/unit/test_research_retrievers_conformance.py`
(subject: the `desk-research` pack) and `.../test_credential_setup_skill.py`
(subject: the `credential-brokers` pack). Re-deriving the set found a third,
`test_desk_research_project_start_elicitation.py`, which asserts only on a
`SKILL.md`'s prose. Renaming a private helper inside a pack must not turn
`agentbundle`'s suite red; it already did once.

The canonical scope enumeration is the task list in [`plan.md`](plan.md). It is
stated there once and not restated here.

## Acceptance Criteria

<!-- Casing is load-bearing: lint-spec-status.py matches `^##\s+Acceptance
     Criteria\b` case-sensitively, so a lowercase `criteria` heading collects
     zero criteria and invariant (ii) passes vacuously. Eight specs in this repo
     — including this spec's predecessor — carry the lowercase form; three more
     carry no Acceptance-Criteria heading at all, which the casing fix would not
     close. Eleven ungated in total. Filed as
     `spec-ac-heading-casing-silent-gate`. -->

### Workstream A — relocate

- [x] **AC1** — No pack carries a test file under any `.apm/` path. Verified by a
      repo-wide walk using the widened matcher from AC8, not by the deferral
      note's `find` pattern — the widened matcher is what makes
      `render-proof/test/*.test.js` visible in the first place.
- [x] **AC2** — Every relocated **Python** suite lives at
      `packs/<pack>/tests/skills/<skill>/` and resolves its subject through
      `parents[3] / ".apm" / "skills" / "<skill>"` — the **skill root**, not
      `scripts/`. Two skills have no `scripts/` directory to anchor on:
      `architect-diagram`'s contains nothing but the test and its fixtures and is
      deleted, and `jira-team-status` never had one and reads a *sibling* skill
      (`jira-story-triage`). A `conftest.py` carrying the anchor, the `sys.path`
      insert, and `raise SystemExit(...)` on a missing skill root is added to
      each destination directory **holding a suite that uses bare sibling
      imports** — not universally: `test_research_retrievers_conformance.py`
      loads its subjects through `importlib.util` with explicit paths and needs
      none. **Every suite that does not itself load a conftest carries the guard
      inline** — the condition is per-file, not per-directory. The standalone
      `__main__` harnesses (`test_exit_codes.py`, `test_next_ordinal.py`) run
      under `python <file>`, never load a conftest even when one sits beside
      them, and build paths a wrong depth breaks
      (`CLI = HERE / "jira.py"`), so they get their own guard regardless of what
      their directory holds. A wrong `parents[]` depth must fail loudly, never
      present as a silently-skipped suite.
- [x] **AC2a** — The relocated **JavaScript** suites keep resolving what they
      resolve today, and only the one that needs a `node_modules` rebind gets
      one. `render-proof.js` — which does not move — holds every third-party
      `require` (`markdown-it`, `jsdom`, `dompurify`, `shiki`, `react`) behind
      lazy call-site requires, so it continues resolving them from its own
      location no matter where the test lives:
      - **All three** suites get every `require('../scripts/render-proof.js')`
        occurrence repointed — module level *and* in-function; `renderer.test.js`
        carries two, the other two one each.
      - For `renderer.test.js` that is **all** — every third-party module it
        reaches is required from inside `render-proof.js`, which does not move,
        so it keeps resolving them from its own location. Verified: it passes
        from the new home with no `module.paths` manipulation.
      - `security.test.js` needs one more change. It resolves
        `evals/files/fixture.md` against `process.cwd()` to prove that a valid
        path inside the confinement root is accepted — a lookup that only worked
        because the suite ran from the skill directory. It now creates and
        removes its own file inside the root instead. An eval fixture is
        skill-local runtime content, not test material (ADR-0071), so a suite in
        the pack's test tree should not reach across that boundary for one.
      - `pipeline.test.js` *additionally* requires `@a2ui/react/v0_9` and
        `@a2ui/web_core/v0_9` directly, so it also needs
        `module.paths.unshift(<skill>/node_modules)` —
        preceded by an `fs.existsSync` check that `throw`s. `unshift` of a
        missing directory is a silent no-op: Node falls through to the ancestor
        chain, `$NODE_PATH` and `$HOME/node_modules`, and a wrong depth would
        bind some other copy rather than failing.

      Each file's stale `// run with: …` header comment is corrected.
- [x] **AC3** — Test-only support files move with the suites they serve:
      `scripts/testdata/` (architect-diagram, msg-to-markdown) and
      `scripts/msg_fixtures.py` (msg-to-markdown). The msg-to-markdown three are
      named as test material in that skill's `## Scripts` bullet;
      architect-diagram's `testdata/` is named only in the test that reads it.
      AC8's matcher does not match any of
      them, so this AC carries its own oracle rather than delegating to AC1:
      `packs/architect/.apm/skills/architect-diagram/scripts/` and
      `packs/converters/.apm/skills/msg-to-markdown/scripts/testdata/` no longer
      exist, and `msg_fixtures.py` is absent from
      `msg-to-markdown/scripts/`. Every surface naming an old path is updated.
- [x] **AC4** — Every pack-subject suite leaves `packages/agentbundle/tests/unit/`.
      The deferral note named two; a third has the same shape and moves with them:
      - `test_research_retrievers_conformance.py` →
        `packs/desk-research/tests/skills/desk-research/`
      - `test_credential_setup_skill.py` →
        `packs/credential-brokers/tests/skills/credential-setup/`
      - `test_desk_research_project_start_elicitation.py` →
        `packs/desk-research/tests/skills/desk-research-project-start/` — it
        anchors on that skill's `SKILL.md` and asserts only on its prose, with no
        engine code in the subject at all.

      No suite left in the engine's tree takes pack content as its subject —
      re-derived by reading each remaining unit test's subject, not by grepping
      for `packs/`. Suites that merely use a pack as fixture data stay.
- [x] **AC5** — `evals/` is untouched. `.apm/skills/<skill>/evals/` still holds
      every eval fixture, `git diff --stat origin/main -- 'packs/*/.apm/skills/*/evals/**'`
      is empty, and `catalogue verify`'s eval linter is green. Checked at the
      close of the sweep (T6), not assumed.
- [x] **AC5a** — Fixture material entering the archived test tree carries no
      credential, no secret, and no real personal data — reviewed file by file,
      since § 4 requires archived fixtures to be synthetic. Several fixtures use
      fabricated addresses at *registered* domains (`corp.com`, `x.com`,
      `evil.com`) and two SSO fixtures name `.doubleclick.net` and
      `jira.evil.net` deliberately, as the third-party domain a cookie must not
      leak to. These are **not** normalised here: `corp.com` appears in both
      `msg_fixtures.py` and the byte-compared `msgreader_baseline.json` that
      `test_parity.py` asserts against, and `evil.com` sits inside CSS-escape
      bypass assertions in a JavaScript suite this environment cannot run.
      Editing security-assertion payloads unverified, to satisfy a placeholder
      convention, is not a mechanical ride-along. Deferred as
      `test-fixture-domain-normalisation` — `corp.com` is the load-bearing case,
      since the same strings are byte-compared against `msgreader_baseline.json`;
      `evil.com` and `jira.evil.net` are synthetic attack payloads inside
      sanitizer and off-domain-refusal assertions, which is what they should be.
      The review is recorded — one line per moved fixture file or directory — in
      a third section of `notes/suite-parity.md`, so "reviewed" is a written
      finding, not a claim.

### Workstream B — keep every suite running

- [x] **AC6** — Every relocated suite's before/after result is recorded, one row
      per suite, in `notes/suite-parity.md` under this spec. The row schema
      accommodates all three suite shapes this migration actually moves: pytest
      modules record collected and passed counts; the standalone harnesses —
      every `test_exit_codes.py` and `test_next_ordinal.py`, identified by
      carrying an `if __name__ == "__main__":` entry point and being invoked as
      `python <file>` rather than under pytest, *not* by the absence of `test_*`
      functions (the `test_exit_codes.py` files define nine each and still run as
      harnesses) — record exit code and assertion count; the JavaScript suites
      record exit code. A
      suite whose dependency or external binary is absent here is recorded
      not-run with the reason, never reported as passing — but the bar is to make
      it runnable first. `mmdc` is installed and `npm install` in the
      `render-proof` skill is a local, gitignored step, so **every** relocated
      suite gets a real before/after run.
- [x] **AC6a** — Every consumer points at the new location, and the list is
      **re-derived by `git grep -F` over every moving basename** immediately
      before the sweep is declared done rather than trusted from this text. Known
      members: `.github/workflows/build-check.yml` (the
      `working-directory:`-plus-bare-filename steps),
      `.github/workflows/docs.yml` (its guard run step),
      `packages/agentbundle/agentbundle/catalogue_tooling/self_host_windows.py`,
      `tools/test-all.py`, `tools/test-lint-sso-config.py`
      (`_DUPLICATED` — the pin lives here, *not* in `tools/lint-sso-config.py`),
      `tools/check-atlassian-phase3-readiness.py` (it invokes pytest on
      `jira-team-status/tests/test_contract.py` by absolute path and returns
      `status="fail"` if the file is missing),
      `packages/agentbundle/tests/unit/test_self_host_windows.py` (it builds a
      fixture tree at the two atlassian `scripts/` dirs and asserts each is a
      step cwd — a basename grep misses it because the paths are assembled from
      multi-line `Path` parts, so the re-derivation also runs
      `git grep -n '"packs"' packages/agentbundle/tests/`), `.gitleaksignore`, and
      `bandit.yaml`. The last two are **reviewed, not repointed** — see AC16 for
      the decision recorded on each. `Makefile` and
      `.github/workflows/catalogue-tooling-ci-gates.yml` need **no repoint**:
      neither names a moving path (their pack-test lines name `core` and
      `product-documentation`). Each gains one new `packs/desk-research/tests/`
      invocation under AC6c, and the `Makefile` also takes T1's comment edit.
      One consumer is **shipped content**:
      `packs/desk-research/.apm/skills/desk-research/SKILL.md` single-sources its
      closed cue tuples from `packages/agentbundle/tests/unit/test_research_retrievers_conformance.py`,
      which AC4 moves — leaving a dangling path inside adopter-installed skill
      text. Because `packs/<pack>/tests/` is no more present in an adopter's tree
      than `tools/` is, that reference is **removed**, not repointed; the same
      applies to `msg-to-markdown/SKILL.md`'s `## Scripts` bullet, whose files
      leave the skill entirely.
      Zero surviving occurrences of any **old path** — not of any basename, since
      the repointed `build-check.yml` steps keep their bare filenames by design —
      **excluding historical-record files by kind**: `docs/adr/`, `docs/rfc/`,
      `docs/specs/`, `docs/product/changelog.md`,
      `packages/agentbundle/CHANGELOG.md`, and `.gitleaksignore` (whose entries
      AC16 retains). `workspace.toml` is **not** excluded wholesale: its still-open
      backlog entry names two old engine-tree paths, in the comment block above
      the `{slug = ...}` line rather than in the entry itself. AC12's retirement
      therefore removes the comment block with the entry, and happens *in* the
      sweep task so the assertion can hold when it runs — relying on the line wrap
      to hide the hit is exactly the wrapped-phrase trap the Boundaries forbid.
      The one carve-out is a backlog entry whose *subject is the deletion*: the
      `adr-errata-convention` entry has to name the file ADR-0071 now stales, or
      it is not cold-start-sufficient. A path named as "this no longer exists" is
      a record, not a dangling reference. Everything in the excluded set records
      what *was* true and is not swept.
- [x] **AC6b** — Suites keep the process isolation they have today, and the
      constraint is recorded where a future author would try to consolidate.
      Same-named test modules and same-named *subject* modules make a single
      `pytest packs/*/tests/` process incorrect, not merely inconvenient: pytest
      refuses duplicate test basenames outright, and `sys.path`-based sibling
      imports would silently bind the first `render` module for all three
      renderers. The colliding sets are **derived mechanically**, not typed —
      `git ls-files ':(glob)packs/*/.apm/skills/*/scripts/*.py' | xargs -n1
      basename | sort | uniq -d` returns both the colliding subject modules and
      the colliding test modules pre-migration; the same derivation restricted to
      `test_*.py` over the destination tree returns the colliding test modules
      afterwards (unrestricted it also returns `conftest.py`, which AC2 puts in
      most destination directories by design).
      **The assertion is about runners, not about the tree.** Overlapping
      basenames *across* destination directories are the expected end state, so a
      lint that reds on them would red on a correct implementation.
      `tools/lint-pack-test-boundary.py` instead parses the runner call sites —
      `Makefile` pytest lines, CI `run:` blocks, `tools/test-all.py` entries,
      `self_host_windows.py` steps — and fails when a single invocation covers
      two colliding destination directories. **Both kinds of collision**:
      duplicate *test* basenames, which pytest refuses loudly, and duplicate
      *subject* modules, which is the silent one — a `sys.path` sibling import
      binds one skill's `render.py` for both suites and everything passes green.
      Checking only the first would guard the failure that announces itself and
      miss the one that does not. Two parsing details are load-bearing:
      `self_host_windows.py` builds its paths from `Path` parts, so a
      substring match alone cannot see it; and comment lines are skipped,
      because prose explaining this constraint naturally quotes the very
      invocation it forbids. AC7's task owns the assertion; no other task may
      claim it.
- [x] **AC6c** — No suite loses its runner, and no *control* suite can pass
      vacuously. The manifest below records the state at ship time;
      `tools/lint-pack-test-boundary.py` is what keeps it true afterwards, by
      failing on any skill test directory that no runner names and that carries
      no declared reason. A spec note freezes when the spec ships, so it cannot
      be the only home for "which suites actually run" — the next pack's test
      directory would be unrun by default with nothing saying so.
      - A runner-coverage manifest in `notes/suite-parity.md`. **Schema, stated
        once:** one row per destination directory naming the runner that executes
        it, **plus** a per-suite row for any suite that runner does not name. A
        row may name more than one runner — the two atlassian SSO directories are
        covered by both `build-check.yml` and `self_host_windows.py`. Each named
        runner may carry an `(unprobed)` annotation where it cannot detect a
        total skip. The permitted forms are: one or more runner names, each
        optionally `(unprobed)`; `none (pre-existing)` where the suite has never
        gated; or `deps absent in CI: <names>` where a runner cannot satisfy its
        self-skips. Every suite with a runner before has one after; all three
        suites moving out of
        `packages/agentbundle/tests/` (AC4) are explicitly rewired, since they
        gate today only by living inside a wholesale-run package tree.
      - Every directory-scoped *invocation* this change creates or repoints
        carries a minimum-collected assertion, not only the catalogue-curation
        pair. Appending `packs/desk-research/tests/` to a command that already collects
        from two other pack trees would leave the count obviously non-zero even
        if nothing from `desk-research` landed, so that tree gets its own
        invocation — which also keeps AC6b's one-invocation/one-basename-set rule
        trivially satisfied.
      - **Every** relocated suite that self-skips is dispositioned — none is left
        to pass vacuously unrecorded. The set is **derived**
        (`grep -ln 'importorskip\|skipif' <moving suites>`), not typed, because
        the obvious membership guess is wrong in both directions:
        `test_setup_sso.py` is in both SSO trios and does *not* self-skip, while
        `test_auth_selector.py` does and has no runner at all, and
        `file-to-markdown`'s `test_convert.py` / `test_split_image.py` skip
        *in-function* on `docx` / `openpyxl` / `pptx` / `PIL.Image`. Each derived
        file gets one of:
        - a hard import in the same `run:` block as its runner, naming that
          suite's *actual* dependencies: `credbroker` and `httpx` for the two
          atlassian SSO steps; `credbroker`, `cryptography` and `argon2` for
          credential-setup — **not** `httpx`, which `test_setup.py` never imports
          and which `build-check.yml` installs eleven lines *below* that step, so
          probing for it would fail the step deterministically; and
          `docx`, `openpyxl`, `pptx`, `PIL.Image` for the file-to-markdown
          extraction step, whose preceding RFC-0036 install does satisfy them
          (single job, install above the step, `python-pptx` brings `Pillow`) —
          the probe is what stops a future reorder from silently un-satisfying
          them.
        - or a manifest row recording the gap honestly: `none (pre-existing)`
          where the suite has no runner, or `deps absent in CI: <names>` where it
          has one that cannot satisfy them. No suite in this migration currently
          takes the second form; it exists because the derivation is re-run at
          implementation time and may surface one.

        A missing dependency makes pytest exit 0 with the file wholly skipped and
        every other AC still passing. The in-step import is what survives a
        future step reorder; a comment is not.
      - **`self_host_windows.py` is a runner too**, and its `_step` checks only
        the return code, so a Windows machine without `credbroker` skips both SSO
        trios and reports pass. It gets the same probe as a preceding step, or its
        name in those two rows carries `(unprobed)`. Naming it as a runner for
        those directories with no annotation, while it cannot detect a total skip,
        would record coverage it does not deliver.
      - The catalogue-curation suites do not self-skip — they import only stdlib,
        `pytest`, and their sibling module — so they need no hard import. Their
        exposure is different: one step carries two `cd`-scoped `pytest -q`
        invocations with no filenames, so a file that fails to land reduces the
        collected count and still exits 0. One minimum-collected assertion per
        invocation; one env site for the step's `PYTHONDONTWRITEBYTECODE`.
- [x] **AC6d** — The cache hardening survives at every site, each with the reason
      that is actually true there. All three are justified in-comment today by the
      self-host drift gate, and the move does **not** invalidate that reason
      uniformly:
      - **catalogue-curation's CI step** (`PYTHONDONTWRITEBYTECODE=1`, one env
        site; `-p no:cacheprovider`, both invocations) — the drift-gate reason
        does evaporate: pytest now writes its cache under `packs/*/tests/`, not
        under `.apm/`. The replacement reason is that `package.py`'s `packs/**`
        walk applies no deny-list, so `__pycache__` there reaches the archive.
      - **`new-adr` / `new-rfc`'s in-file `sys.dont_write_bytecode = True`** — the
        drift-gate reason **stands**. Those harnesses `exec_module` the script
        under test *from* `.apm/skills/<skill>/scripts/`, so the `.pyc` still
        lands inside the runtime payload. Restating it as the archive-walk reason
        would have been wrong; the comment says why the original reason survives
        the move instead.

      The guard does **not** assert the absence of cache directories:
      `Makefile`'s pack-test line runs without `-B`, so `__pycache__` exists under
      `packs/*/tests/` on any machine that ran `make test`. The packaging half —
      those caches reaching the archive — is fixed in this PR rather than
      deferred, since the release was already being cut: see AC17.

### Workstream C — widen and rehome the guard

- [x] **AC7** — The runtime-boundary guard covers **every** pack, not `core`
      alone, and lives outside any pack's test tree — cross-pack behaviour is not
      pack-owned (§ 4, *Repository-root tests*). `packs/core/tests/pack/test-runtime-boundary.py`
      no longer exists at that path. It is gated by a CI job that actually runs:
      `docs.yml` executes it today but is path-filtered, so its `paths:` list gains
      the guard and its self-test, its existing run step is repointed, **and a
      second run step is added for the self-test** — otherwise AC9's permanent
      falsification cases are gated by nothing. `tools/test-all.py`
      is a path *trigger* in `docs.yml` and is executed by no workflow — wiring the
      self-test there adds local coverage and no CI coverage, and the AC says so
      rather than implying otherwise.
- [x] **AC8** — `_TEST_FILE` **and** `_TEST_DIR` are widened to the shapes this
      repo can grow — a strict **superset** of what it matches today, never a
      re-cut: files matching `conftest.py`, `*.test.*`, `*.spec.*`,
      `*[-_]test.*` (the existing shape; writing `*_test.*` would drop
      hyphenated `foo-test.js`, and AC9 would then pin the regression with a
      passing test), `test[-_]*` across `py|sh|js|ts|tsx|mjs|cjs|go|ps1|rb`, and
      directories named `tests`, `test`, `__tests__`, `spec`. The singular `test/`
      is the shape this change itself discovered. Every remaining narrowing is
      documented in the source with the reason it is deliberate.
- [x] **AC9** — The guard is falsified in both directions, and the falsification
      lives in `tools/test-lint-pack-test-boundary.py` as a permanent case rather
      than in the PR body: planting a test file under a non-`core` pack's `.apm/`
      makes the guard fail; removing the plant makes it pass. Each newly-claimed
      matcher shape is asserted to match and each documented non-match asserted
      not to.
- [x] **AC10** — The projection half survives the rehome and is not vacuous.
      `packages/agentbundle/agentbundle/build/recipes/self-host.toml`'s
      `[recipe.packs].include` is the authority for which packs this repo
      projects; only those can be checked here. The guard asserts,
      **per pack in that list**, that at least one of its skills is projected and
      that no projected skill carries test content — so a pack silently dropping
      out of the projection fails rather than passing on an empty iteration. The
      global "must not pass vacuously" refusal is retained. Packs outside the
      include list are named as out of scope for the projection half, with the
      `.apm/` half still covering them.
- [x] **AC10a** — The guard walks with `os.walk(root, followlinks=False)` and an
      explicit symlink prune, matching `package.py`'s archive walk, rather than
      `Path.rglob("*")`. Two divergent definitions of "pack content" between the
      guard and the walker that decides what actually ships is the defect;
      `rglob`'s symlink behaviour also changed across the 3.12/3.13 boundary.
      `git check-ignore` is invoked with a `--` terminator.
- [x] **AC10b** — The guard's positive half — "the pack's tests exist at the new
      home" — is restated for a per-pack iteration and drops the hardcoded
      `len(suites) < 10` floor: for each pack, if `.apm/` is clean and the pack
      owns any test, `packs/<pack>/tests/` is non-empty. Packs that own no tests
      pass without assertion.

### Workstream D — record, bump, release

- [x] **AC11** — `docs/architecture/pack-layout.md` describes the completed state
      and names the guard's new path. `packs/AGENTS.md` is at 149 lines against a
      hard 150-line cap, so it gets a **replacement**, not an addition: the
      existing test-boundary line is rewritten to the shipped state and points at
      `pack-layout.md` for detail.
      `guides/_shared/reference/catalogue-authoring-standards.md` § 4 gets the
      one-process-per-skill constraint and a correction to its *Repository-root
      tests* paragraph, which currently asserts this catalogue keeps such checks
      in the engine's suite — the rehome to `tools/` makes that false. § 4 states
      the rule at pattern level and **must not name `tools/lint-pack-test-boundary.py`**:
      shipped content cannot reference `tools/`, which does not exist in an
      adopter's tree (`packs/AGENTS.local.md`). `packs/AGENTS.md` stays under 150
      lines. `sync_authoring_scaffold.py --write` runs if `packs/AGENTS.md`,
      `packs/README.md`, or the authoring standards changes.
- [x] **AC12** — The deferral is retired coherently and `workspace.toml` is left
      consistent. The retirement happens **in the sweep task**, not after it: its
      backlog comment is one of the old-path occurrences AC6a sweeps for.
      `pack-test-boundary-remaining-packs` is removed from
      `[backlog].open` **together with the comment block above it**, which is
      where the two old engine-tree paths actually live; the deferral marker
      naming this slug on AC13 of
      `docs/specs/pack-test-boundary/spec.md` is resolved in the same commit
      as the backlog removal
      (spelled out here it would itself be a live anchor —
      `lint-spec-status.py`'s scanner has no code-span exclusion, so writing the
      parenthesised form in this file would make *this* spec red the build the
      moment the backlog entry goes), and `spec/pack-test-boundary-remaining-packs`
      moves from
      `["ini-007".work].active` to `.shipped` — **in the final commit, beside the
      `Shipped` flip**, because `workspace_status_engine.py` reports a
      "prematurely shipped" finding for a `shipped` entry whose spec still reads
      `Implementing`, and moving it earlier opens exactly that window. Its
      block comment collapses to an inline `# <version> — <summary>` on the new
      `shipped` entry, matching the ones already there. The three deferrals this
      loop opens — `adr-errata-convention`, `test-fixture-domain-normalisation`,
      `spec-ac-heading-casing-silent-gate` — are added to `[backlog].open` with
      cold-start-sufficient comments. `lint-spec-status.py` treats an
      unresolvable anchor as a *hard* failure and runs inside
      `build_gate_chain.py`, so removing the backlog entry without the marker
      reds `make build-check`; and `workspace_status_engine.py` reads the work
      lists, so a stale `active` misreports the workspace indefinitely.
      This spec's own status moves twice, and neither move is in the
      backlog-retirement commit above: `Draft → Implementing` before the first
      file moves (`docs/CONVENTIONS.md` requires it before code changes begin),
      and `Implementing → Shipped` in the **final** commit of the loop, after
      AC13 and AC14 land, together with `Status: Done` in `plan.md` and every AC
      above `[x]` or carrying a deferral marker that resolves in
      `[backlog].open`. The second transition is what makes
      `lint-spec-status.py`'s AC-completeness invariant fire, so it must come
      after the work, not before it.
- [x] **AC13** — Every pack whose **`.apm/` content** changes is bumped and
      re-projected: `pack.toml` `[pack] version` **and**
      `.claude-plugin/plugin.json` `"version"` in lockstep, a
      `## [<pack>][<version>] — <date>` section in `docs/product/changelog.md`,
      and `FORCE=1 make build-self` to re-aggregate `marketplace.json` and delete
      the now-stale projected test files.
      - **The set is defined by the rule, not enumerated**: a bump is owed where
        the projected/installed surface changes. `core` therefore does not bump —
        this change touches only its `tests/` tree, which is never projected.
      - The increment is **patch** for each: no primitive is removed, and the
        change is to pack content layout. Reasoning recorded in
        `disposition-record.md`, because `packs/AGENTS.md` says *major for
        removals* and what counts as a removal is a judgement call.
      - **Nothing gates the lockstep.** `verify.py` and `lint.py` both probe
        `pack_dir / "plugin.json"`, not `pack_dir / ".claude-plugin/plugin.json"`,
        so the parity step silently no-ops — the open
        `version-parity-probes-wrong-path` backlog entry. Bumping every touched
        pack across two files with no enforcement is the highest-probability
        silent defect here, so this AC requires an explicit per-pack equality
        check, run and its output recorded in the PR.
- [x] **AC14** — The `agentbundle` release happens because T6 edits
      `packages/agentbundle/agentbundle/catalogue_tooling/self_host_windows.py`,
      which `check_release_impact.py` lists as release-impacting. (AC4's file
      removal is *not* the trigger: `pyproject.toml` sets
      `include = ["agentbundle*"]`, and the three suites AC4 moves lived in
      `packages/agentbundle/tests/`, a sibling of the package — so they were
      never in the wheel. `agentbundle/build/tests/` *is* inside the package and
      does ship; nothing moved out of it.)
      `pyproject.toml` and the hardcoded `CLI_VERSION` twin in `version.py` are
      bumped together, `packages/agentbundle/CHANGELOG.md` **and**
      `docs/product/changelog.md` each carry an entry (the latter is what
      `check_release_impact.py` accepts as a release indicator), and
      `README-pypi.md` is corrected if it asserts the migration is partial.
- [x] **AC15** — The `Engine-Change-RFC:` trailer is present on every commit that
      needs it, across **two** protected trees, not one:
      `packages/agentbundle/**` outside the `/tests/` and `build/recipes/`
      carve-outs — T6 edits `self_host_windows.py`, T8's
      `sync_authoring_scaffold.py --write` writes under
      `agentbundle/_data/catalogue-scaffold/`, and T9 edits the package metadata
      — and `packs/credential-brokers/**` in its entirety, which
      `lint-catalogue-curation-guard.py` protects with **no `/tests/`
      carve-out**, so creating `packs/credential-brokers/tests/` trips it. The
      gate is changeset-scoped, so one trailer in the PR satisfies it; the trailer
      goes on each of those commits anyway, so a later rebase or cherry-pick does
      not silently drop it.
- [x] **AC17** — `catalogue package` stops collecting build residue. Both
      packaging flavours walk `packs/**` recursively and the deny-set intended to
      prevent this (`_IMPLICIT_DENY_DIRS`) was referenced nowhere, so every
      `__pycache__` and any `node_modules` under a pack reached the archive — 104
      files on this catalogue. Added late and deliberately: the relocation moved
      pytest suites *into* `packs/`, which turns an occasional leak into one that
      happens on every `make test`, and § 4 tells adopters caches are "neither
      committed nor packaged". The fix rides this PR because the agentbundle
      release was already being cut for AC14.
      - The old set could not be applied as written. It also named `.git`,
        `tools`, `packages` and `dist` — *repository-root* names already excluded
        by the include allowlist — and pruning those at every level would have
        silently dropped real content. `packs/monorepo-extras/seeds/packages/` is
        the live instance, and it has a regression test.
      - Both flavours are covered, with an archive-contents assertion each,
        falsified by neutering the prune and confirming both fail.
- [x] **AC16** — The two SAST/secret-scanning coverage changes this move causes
      are decided explicitly rather than absorbed.
      - `bandit.yaml`'s `*/tests/*` exclusion drops the relocated files out of
        the bandit scan they are inside today. Retained, because every other test
        tree in the repo is already excluded; recorded, because it is a real
        coverage change.
      - `.gitleaksignore`'s five fingerprints for `test_exit_codes.py` files are
        `<historical-commit-sha>:<old-path>:<rule>:<line>` and are **kept**:
        `ci-security.yml` falls back to a full-history scan when `BASE_SHA` is
        absent or zeroed, and those historical commits still carry the old paths.
        If the range scan flags the relocated fixtures at their new paths, they
        are suppressed with path- and sha-independent `# gitleaks:allow` inline
        comments — a fingerprint minted against a PR-branch commit dies on
        squash-merge and is unstable by construction.

## Boundaries

### Always do

- Pair every relocation with its runner in the task that moves it — each pack's
  `build-check.yml` steps belong to that pack's relocation task, not to the sweep.
  A suite that moves and loses its runner fails nothing and is invisible; that is
  the dominant risk here, as it was in the predecessor loop. The sweep is the
  backstop, not the mechanism.
- Carry the existence guard into every relocated suite whose resolution can fail
  *quietly*: `raise SystemExit` for Python, and `fs.existsSync` + `throw` for
  `pipeline.test.js`, whose `module.paths.unshift` of a missing directory is a
  no-op with silent ancestor fallback. The other two JavaScript suites need no
  added guard — a `require()` of a wrong-depth relative path already fails loudly
  with `MODULE_NOT_FOUND`. A wrong `parents[]` depth reds a whole Python suite
  while `make build-check` stays green, because `build-check` runs no pytest.
- Grep with **short byte substrings**, never a wrapped phrase. A phrase that
  wraps across two lines returns zero hits and reads as "my edit vanished".
- Derive enumerations from a command and cite the command. Typed lists of
  filenames and counts drift the moment scope shifts.

### Ask first

- Adding a new top-level directory. A repository-root `tests/` is RFC-gated by
  `CLAUDE.md`, and § 4 already records that this catalogue keeps cross-cutting
  tests out of pack trees.
- Newly enabling a suite that has never gated. Several relocated suites have no
  runner today; giving them one can turn an unrelated red loose inside a
  mechanical move. The gap is recorded in the manifest, not closed here.

### Never do

- **Never relocate `evals/`.** They are skill-local runtime content at
  `.apm/skills/<skill>/evals/`, projected with the skill, and the linter enforces
  that placement. An earlier draft of this policy moved them and was wrong
  (ADR-0071).
- **Never create a repository-root `tests/`.**
- **Never merge the relocated suites into one pytest process.** See AC6b: it is
  incorrect, not just slower.
- **Never widen the guard's matcher to match only what already passes.** AC9's
  falsification exists because a matcher tuned to the current tree proves
  nothing about the next pack.
- **Never name a `tools/` path in shipped content.** § 4, `guides/_shared/**`,
  and `packs/**/.apm/**` all ship; `tools/` does not exist in an adopter's tree.
- **Never edit ADR-0071.** No mechanism exists to. `docs/CONVENTIONS.md` freezes
  the body, the shipped `new-adr` template says only the Status line moves, and
  the `## Errata` convention that would allow a dated correction is RFC-scoped in
  `new-rfc`. Extending it to ADRs means amending that skill, its template, and
  CONVENTIONS — a governance change, deferred as `adr-errata-convention`. So the
  ADR keeps a stale path at line 74 and a stale "migration is partial"
  paragraph, and so do the predecessor spec and plan, which name the guard's old
  path in prose. ADR-0071 additionally says the work is "tracked as
  `pack-test-boundary-remaining-packs` in `workspace.toml [backlog].open`" and
  the predecessor plan carries the bare slug — an entry AC12 removes, so those go
  stale too.
  `lint-spec-status.py`'s dangling-reference invariant is warn-only, so these
  become permanent warnings on `make build-check` rather than failures. Recorded,
  not hidden.

  This is *not* in tension with AC12 editing the predecessor spec's body. That
  edit resolves a `(deferred:)` marker, which `lint-spec-status.py` treats as a
  **hard** failure while it dangles — the linter requires the edit, so the
  deferral token is a sanctioned metadata field, not frozen prose. ADR-0071 has
  no equivalent sanction and no linter demanding the change.

## Assumptions

- **`parents[3]` is the uniform anchor.** From
  `packs/<pack>/tests/skills/<skill>/test_x.py`, `parents[3]` is `packs/<pack>`.
  Every relocated suite lands at the same depth, so every suite uses the same
  arithmetic. Suites needing the scripts directory on `sys.path` get it from a
  sibling `conftest.py` rather than edited module headers.
- **Bare sibling imports are load-bearing.** `import render`, `import _sso_config`,
  `import ssrf_check` work today only because pytest's `prepend` import mode
  inserts the test file's own directory into `sys.path`. After the move that
  directory is the test tree, not the scripts tree, so the insert becomes
  explicit. This is the mechanical cause of most of the diff.
- **Each module-level `Path(__file__)` expression is repointed to whatever it
  actually denotes**, which varies by file and sometimes within a directory —
  the skill's `scripts/`, a sibling of it, the skill root, the repo root, or the
  test's own directory. The full shape table is in the plan's uniform recipe.
  There is no single rule, and assuming one reds suites in both directions:
  `test_parity.py`'s `HERE / "testdata"` means the *test's* directory once AC3
  moves `testdata/` alongside it, while `test_drift.py` and `test_security.py` in
  the same destination mean `scripts/`. Repointing is per-expression, not
  per-file: `test_convert.py` carries two module-level anchors, `test_tier3.py`
  defines no `HERE` at all and names its anchor `_GROUNDING`, and `test_setup.py`
  performs its own `sys.path.insert`. Enumerate with
  `grep -n 'Path(__file__)'`; a `HERE`-only grep misses several.
- **CI's per-suite dependency installs stay attached to their suites**, and the
  coupling is not always adjacent: `credbroker[crypto]` is installed under the
  *credbroker package* concern and the SSO and credential-setup steps depend on
  it a dozen-plus lines later. Repointing a `working-directory:` must not invite
  regrouping the steps above that install.
- **`make test` deliberately excludes dependency-heavy pack suites** and says so.
  Widening it to `packs/*/tests/` would both collide (AC6b) and demand every
  optional dependency locally, so it is not widened *that* way. The single
  exception is the additive `packs/desk-research/tests/` line AC6c requires:
  stdlib-only, its own invocation, no collision with the two trees the existing
  line collects.

## Testing strategy

Four layers, because a mechanical move can pass silently in every way that
matters:

- **Per-suite, before and after.** Each relocated suite is its own oracle. Run it
  from its current home, record collected/passed; run it from the new home,
  record the same; compare in `notes/suite-parity.md`. A suite that cannot run
  here is recorded not-run with the reason — never inferred green.
- **Runner reachability, not suite health.** After the sweep, `git grep` every
  moved filename repo-wide, unfiltered. `build-check.yml` passes bare filenames
  relative to a `working-directory` this change invalidates; a stale one fails
  nothing, so *absence of the old path* is the assertion. Paired with the
  positive manifest in AC6c, because absence alone cannot prove a new tree is
  reachable.
- **Skip-detection on control suites.** Several suites gate themselves —
  at module scope, per test, or in-function; derive the set with
  `grep -ln 'importorskip\|skipif'`. Green locally proves nothing about CI, where
  the dependency may be absent — hence the in-step hard import and the
  minimum-count assertion in AC6c.
- **Guard falsification in both directions**, as a permanent self-test case
  (AC9), not a one-off performed during the loop.

`make build-check` runs no pytest and therefore proves nothing about any of the
above. Verification runs `make ci` without `SKIP_SAST=1`,
`tools/lint-catalogue-curation-guard.py --root . --base origin/main`, the full
`agentbundle` suite, and every moved suite from its new home.

`tools/test-all.py` is run **for a green aggregate**. That changed mid-loop:
this spec was written when two of its entries named files that did not exist, so
the runner had reported permanent failures and only its individual entries could
be asserted. #874 retired those entries upstream and closed
`test-all-dangling-entries`, so after the rebase the whole runner is green —
including this change's two new entries, `pack-test-boundary` and
`pack-test-boundary-self-test`. Verified: `TESTALL_EXIT=0`, nine checks.
