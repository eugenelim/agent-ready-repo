# Resolve-vs-surface disposition record: pack-test-boundary-remaining-packs

Opened at PLAN (2026-08-06); closed at DECIDE. Records what was resolved by the
loop vs. surfaced to the human, per the work-loop self-coverage gate.

## Resolved by the loop (with authority source)

- **Full mode.** Three risk triggers fire: structural/published-interface (a
  directory contract applied across every remaining pack, changing what each one
  projects into an adopter's tree), multi-feature with dependent tasks, and a
  governance surface — `catalogue-authoring-standards.md` § 4 ships as normative
  MUST-level rules, and the change crosses two guard-protected trees
  (`packages/agentbundle/**`, `packs/credential-brokers/**`). Not the published
  wheel: `pyproject.toml` sets `include = ["agentbundle*"]`, so `tests/` was never
  in it. Authority: the mode-selection rule in `work-loop`.
- **Destination layout and anchor depth.** `packs/<pack>/tests/skills/<skill>/`
  with `parents[3]` is fixed by ADR-0071 and demonstrated by the shipped
  `packs/core/tests/` tree. No judgement left to make.
- **A `conftest.py` supplies the `sys.path` insert and the existence guard —
  nothing more.** Bare sibling imports (`import render`) need the skill's
  `scripts/` on `sys.path`, and a per-directory conftest is the smallest change
  that supplies it with one guard site per skill. It does *not* remove the need
  to edit module-level path expressions: conftest globals are invisible to test
  modules, so roughly half the Python suites still get an edited `HERE` /
  `_SCRIPTS` / `_GROUNDING` / `TESTDATA` line of their own. Authority:
  minimal-diff rule in `CLAUDE.md`.
- **Scope is the repo-wide walk, not the deferral note's `find`.** That `find`
  pattern cannot see `render-proof/test/*.test.js`. The brief explicitly directs
  widening the matcher; a widened matcher that excluded the only files it newly
  catches would be the "widen an AC to match what the code already does"
  anti-pattern the completed spec rails against. Included.
- **The widened guard lands at `tools/lint-pack-test-boundary.py`.** The brief
  says "move it somewhere it isn't core-owned"; § 4 says cross-pack behaviour is
  not pack-owned and that this catalogue keeps it out of pack test trees. `tools/`
  already holds the repo's cross-cutting lints and is pure-stdlib Python per
  `CLAUDE.md`. A repository-root `tests/` is RFC-gated and explicitly excluded.
- **`make test` is not widened to `packs/*/tests/`.** Empirically verified at PLAN
  (pytest 9.0.3, `import file mismatch`): duplicate test basenames make a
  single-process run fail, and duplicate *subject* basenames (`render.py` × 3)
  would silently bind one module for three suites. The existing per-skill process
  topology is preserved. This is a correctness constraint, not a preference.
- **ADR-0071 is not edited at all.** See the erratum entry below for why the
  first draft's header-pointer approach was dropped.

- **Pack version increment is `patch`, not `major`** — the full reasoning is in
  AC13 and not repeated here. Recorded as a *disposition* because it is a
  governance judgement about what `packs/AGENTS.md`'s "major for removals" means
  (removal of a primitive, not of any file), resolved by the loop rather than
  asked.
- **ADR-0071 is left alone; correcting it is deferred as a governance change.**
  Two approaches were considered and both dropped. A header `Related:` pointer
  rested on `docs/CONVENTIONS.md` permitting Status-field changes — that sentence
  permits Status changes specifically, blesses no other header edit, and would
  not fix the stale *path* the ADR names at line 74. A dated `## Errata` entry is
  the repo's documented mechanism for a frozen governance doc, but it is
  RFC-scoped in `new-rfc`; extending it to ADRs means amending
  `new-adr/SKILL.md`, its shipped template (which says only the Status line
  moves), and `CONVENTIONS.md`, plus a `governance-extras` bump — a governance
  change riding inside an implementation PR, which `CLAUDE.md` routes through
  RFC. So the ADR keeps a stale path and a stale "migration is partial"
  paragraph; this spec and `docs/architecture/pack-layout.md` are the live
  record, and the convention gap is filed as `adr-errata-convention`.
- **Suites that have never gated do not gain a runner in this PR.** A
  double-digit number of relocated suites are named by no runner today; the
  runner manifest in `notes/suite-parity.md` is the single enumeration and this
  record does not duplicate it. Newly enabling them inside a mechanical move could
  turn an unrelated red loose. The gap is pre-existing, is recorded per directory
  in the runner manifest, and is not closed here. The suites that *do* gate today
  and would otherwise stop — the trio leaving `packages/agentbundle/tests/`, which
  gates only by residence in a wholesale-run tree — are explicitly rewired.
- **`bandit.yaml` keeps its `*/tests/*` exclusion.** The relocated files drop out
  of the bandit scan they are inside today. That is a real coverage change, and
  it is the consistent one: every other test tree in the repo
  (`packages/*/tests/`, `packages/agentbundle/agentbundle/build/tests/`) is
  already excluded, and re-including only these would be arbitrary. Recorded
  rather than absorbed.

## Surfaced to the human

- **`render-proof`'s JavaScript suites: resolved during EXECUTE, not surfaced.**
  PLAN recorded them as unverifiable because `node_modules` was absent. On the
  user's direction the dependencies were installed locally (`npm install` in the
  skill; `node_modules/` is gitignored, nothing committed), so all three got a
  real before/after run and all three pass. What remains open is a *scope*
  question, not a verification one: they have never had a CI runner, and giving
  them one needs an `npm install` step and a committed lockfile — see below.
- **Should `render-proof`'s JavaScript suites gain a CI runner?** They pass, and
  nothing runs them. Enabling them means an `npm install` step in
  `build-check.yml` and a committed lockfile for nine floating-caret dependencies
  including the `dompurify` the sanitizer assertions test. That is a supply-chain
  and CI-cost decision, not a repoint, so this PR records `none (pre-existing)`
  and leaves it to you.
- **`.gitleaksignore` cannot be settled in advance.** Whether the range scan
  flags the relocated fixtures at their new paths is not knowable here — gitleaks
  is not installed locally. AC16 fixes the policy (keep the historical
  fingerprints, suppress inline if needed); what it cannot fix in advance is
  whether any suppression is needed at all.
- **The lockstep version bump has no working gate** (AC13). The manual equality
  check T9 runs is a workaround; the broken probe belongs to the open
  `version-parity-probes-wrong-path` entry and is not fixed here. Surfaced
  because a manual check is only as good as the person running it.
- **Every touched pack takes a version bump in one PR**, which will conflict with
  any concurrent work on those packs. Kept in a single late commit to make a
  rebase cheap, but worth knowing before parallel work starts.
- **Deferred out of this PR, opened by it:** `adr-errata-convention` (extending
  the RFC errata mechanism to ADRs, so a frozen ADR naming a since-deleted path
  can be corrected) and `test-fixture-domain-normalisation` (registered domains
  in fixtures that now enter the archived test tree; blocked on a byte-compared
  parity baseline and an unrunnable JS suite).
- **Found in review, not fixed here: `spec-ac-heading-casing-silent-gate`.**
  `lint-spec-status.py` matches `^##\s+Acceptance Criteria\b` case-sensitively.
  Eight specs in `docs/specs/` use `## Acceptance criteria` and therefore collect
  zero criteria — their AC-completeness invariant has always passed vacuously,
  including on this spec's own predecessor. Three more carry no
  Acceptance-Criteria heading at all, a different defect the casing fix would not
  close; eleven ungated in total. This spec uses the correct casing. Fixing the
  rest — and deciding whether the matcher should be case-insensitive, or should
  fail loudly when a spec has no criteria section — is a separate change.
- **Deferred out of this PR, pre-existing:** `test-all-dangling-entries`,
  `version-parity-probes-wrong-path`, `package-archive-carries-pycache`, and the
  several relocated suites that have never had a CI runner. This loop documents
  each where it bites rather than closing it — but a reader of the PR should know
  that `tools/test-all.py` is red before this change and after it, and that the
  pack version-parity gate does not work.
- *(further entries appended at DECIDE)*
