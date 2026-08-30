# Plan: spec-authoring-discipline

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (§ *Version bump rule*, § *Shipped
  pack content carries no internal-governance citations*, § *Self-hosting
  projection*, and the eval-harness rule under § *Security and authoring
  rules*) and `packs/core/AGENTS.md:7`. Analogous production change:
  `9eb1b83ce` (repository-context anchoring), which added normative guidance to
  `new-spec/SKILL.md` and pinned it with
  `packs/core/tests/skills/new-spec/test_repository_anchors.py`; its sibling
  `test_wave4_durable_outputs.py` is the second instance of the same idiom.
  Named uncertainty: none outstanding on the rule shapes — the corpus probe in T1
  resolved the one open question (whether a numeric size threshold could ship) in
  the negative.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially (a different approach, not just
> a re-ordering), note why in the changelog at the bottom. Once it is `Done`
> and the spec is `Shipped`, the directory freezes as a unit.

## Approach

The rules land as prose in the two files that already own their
neighbours, then get pinned by contract tests, then ship through the normal
projection and release surface. The shape of the change is deliberately boring:
no new file under `packs/`, no new module, no checker, no engine touch, and no
numeric threshold.

The riskiest part is not the prose — it is **ownership**. AC11 requires each rule
to sit in exactly one of the three source files, and both candidate homes already
contain acceptance-criteria guidance: `SKILL.md` step 4 pushes back on criterion
failure modes procedurally, while `assets/spec.md`'s `## Acceptance Criteria`
block owns the *shape* rules an author reads while writing criteria
(output-channel enumeration, UI state as state/trigger/outcome, NFR-with-a-bar).

The split follows that existing grain: **the template owns rules about what a
criterion must look like** (AC1 independence and AC2's examples, AC4/AC5 bound
ledger, AC16 minimality, AC17/AC18 limit discipline, AC19 mechanism give-away),
and **`SKILL.md` owns rules about what the author must do at a step** (AC6's
corpus task at plan time, AC8's ownership discipline at step 8, AC12's deletion
pass at step 6). Every cross-reference points by file and section name, never by
copied sentence.

**Step 4 carries a pointer to every rule that applies while criteria are being
written, whichever file owns it.** This matters because two of the `SKILL.md`
rules bite at step 4 but are stated later in the document — AC8's citation
discipline and AC6's pre-refusal corpus obligation. A pointer is a citation, which
is exactly what AC8 licenses; restating either rule at step 4 would violate AC11.

Order of operations: run the corpus probe first, because it decides whether a
numeric rule is admissible at all; write all the rules in one task, because AC11 is
a cross-file invariant that is violated in any half-state; then pin, then eval,
then release.

## Constraints

- `packs/AGENTS.md` § *Version bump rule* — patch for changed content, minor for
  new primitives. This change adds no primitive, so it is `2.15.3` (a patch on
  `2.15.2`, after a mid-flight rebase onto two further released minors).
- `packs/AGENTS.md` § *Shipped pack content carries no internal-governance
  citations* — the shipped guidance may not cite this catalogue's records,
  acceptance criteria, or repository-only paths. The corpus measurement therefore
  lives in `spec.md`'s Assumptions and in T1 below, never in the skill body. With
  no numeric threshold shipping, no measured figure needs to cross that boundary
  at all.
- `packs/AGENTS.md` § *Self-hosting projection* — `.apm/` is the source; never
  edit the `.claude/` or `.agents/` projections directly.
- `packs/AGENTS.md` § *Security and authoring rules* — a non-cosmetic pack update
  also updates that pack's eval harness (T4).
- `packs/AGENTS.md` § *Writing pack tests* — load a skill's modules under a
  unique name; keep suite cost in assertions rather than processes. T3 reads
  files and asserts on text, spawning nothing.
- `docs/product/changelog.md:11` — a released section is free-standing, directly
  beneath `[Unreleased]`.
- No new dependency, module boundary, abstraction layer, or top-level directory
  (spec Boundaries § *Never do*).

## Construction tests

Per-task tests live under each task below. Cross-cutting:

**Integration tests:** none beyond per-task tests — the change has no runtime
surface to integrate.

**Manual verification:**
1. Portability of added pack prose — `git diff` of `packs/**`, added lines only,
   grepped for `docs/`, `workspace.toml`, `AC<n>`; result recorded.
2. This spec and plan were authored under the rules they introduce; record which
   fired and what each changed. Already observed: AC1's split test forced
   the release-surface criterion out of the spec and into T5 as mechanism; AC8
   caught that `packs/AGENTS.md`, not changelog section headings, owns the version
   decision, changing the deliverable from `2.14.0` to `2.13.1` (later `2.15.3`
   after a rebase onto two further released minors); the same read
   surfaced AC15, an obligation the first draft missed; AC16 deleted the percentile
   citation from AC1; and T1's oracle falsified the numeric threshold outright.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Maintainer authoring procedure — `new-spec/SKILL.md`, `new-spec/assets/spec.md` | T2, T3 | `packs/core/tests/skills/new-spec/` green; recorded mutation per rule | Each rule resolves to one owning file; AC6's absence assertions hold |
| Release history — `docs/product/changelog.md` | T5 | `## [core][2.15.3]` directly beneath `## [Unreleased]`; `pack.toml` and `plugin.json` agree | Version identical in all three files in one commit |
| Reusable learning — `docs/knowledge/` | — (workflow-owned) | Capture receipts at `spec-approved` and `plan-locked` | Receipts distilled at `plan-locked`; journal diff passes a verification barrier |

## Design (LLD)

### Design decisions

- **Two owners, split along the existing grain, with step-4 pointers** — the
  template owns criterion-shape rules; `SKILL.md` owns per-step author
  obligations; and step 4 cites, without restating, every rule that applies while
  criteria are written. Rejected: putting all twelve in `SKILL.md`, which separates
  the shape rules from the template an author is actually filling in; and putting
  all twelve in the template, which leaves AC6's plan-time corpus task and AC12's
  review-time deletion pass with no criterion-shaped home. Traces to: AC1, AC2,
  AC4, AC6, AC8, AC10, AC11, AC12, AC16, AC17, AC18, AC19, AC20, AC21.
- **Criterion independence ships as a structural test with no number, and its
  boundary is fixed by worked examples rather than by prose exceptions** — see
  AC1 and AC2 for the rule and the boundary; this decision does not restate them.
  Three prose formulations of the exceptions failed in succession, the last by
  letting an author reframe any bundle as a single constraint over a domain, so
  the distinctions moved into AC2's normative examples where the smoke set can
  falsify a wording before it is pinned. A clause-level predicate was rejected at
  1 of 3, and a word-count threshold was rejected on corpus portability. T1
  measured that no numeric detector is portable — a 150-word trigger fires on
  0.0% of `ui` criteria and 13.8% of `data` criteria, and 35% of over-150 criteria
  are legitimate enumerations — so any shipped figure would be wrong for some
  stack in one direction and wrong for another stack in the other. Dropping the
  number also removes the recalibration instruction and the internal-citation
  problem that `packs/AGENTS.md` would otherwise force. Traces to: AC1.
- **The bound ledger is a sibling bullet, not an extension of the pass/fail-bar
  bullet** — the existing bullet governs "name a threshold a test or audit can
  check"; the ledger governs which input fires the limit first and what enforces
  that ordering. Those are different facts about the same subject, so two bullets
  is not the one-fact-in-two-places shape AC9 forbids. Traces to: AC4, AC5.
- **No mechanical checker, and no follow-on registered for one** — recorded as an
  explicit non-goal in Boundaries rather than as delivery debt. Traces to: AC1,
  spec Boundaries § *Non-goal*.

### Behavior & rules

The bound ledger (AC4) attaches to a criterion only when that criterion states a
numeric limit, so its blast radius is the 1.8% of criteria that state one; the
two-limits-on-one-quantity clause narrows further, to 0.5%. The rule is therefore
written as a conditional obligation, not a field every criterion must carry.
Traces to: AC4, AC5.

## Tasks

### T1: The corpus oracle decides whether a numeric size rule is admissible

**Verification mode:** goal-based check.

**Depends on:** none

**Tests:**
- Re-running the recorded probe on an unchanged tree reproduces the same figures.
- The figures in `spec.md`'s Assumptions match the probe output exactly.
- The probe's verdict on numeric portability is recorded, whichever way it falls.

**Approach:**
- Collect each `docs/specs/*/spec.md`, isolate its `## Acceptance Criteria`
  section, strip HTML comments so template guidance is not counted, join each
  `- [ ]`/`- [x]` item with its continuation lines, and count words; then repeat
  per `Shape:` header, and repeat for sentence count and distinct-identifier
  count as candidate detectors.
- Recorded result on this tree: 409 specs carry a criteria section; 6,062
  criteria; median 33 words; p95 146; max 1,361. Over 150 words: 283 (4.7%)
  across 96 specs. Criteria stating ≥1 numeric limit: 111 (1.8%); ≥2: 29 (0.5%).
  Criteria already citing an owning identifier: 4,013 (66.2%).
- Recorded verdict — **no numeric detector is portable.** Over-150 firing by
  shape: `ui` 0.0%, `mixed` 2.2%, `integration` 4.5%, `service` 6.2%, `data`
  13.8%. p95 spread across shapes: word count 2.9x, sentence count 3.2x,
  identifier count 2.3x. 35% of over-150 criteria are structural enumerations —
  one contract with many parts. Excluding enumeration items and counting prose
  sentences spreads 2.7x and still fires on `ui` at 9.3%, which is why AC1 ships
  the structural form and no number.
- Do **not** commit the probe as a tool: a checker is an explicit non-goal, and
  `tools/` additions carry a CI-parity obligation this change declines.

**Done when:** the figures are reproduced by re-running the probe, `spec.md`'s
Assumptions cite them without discrepancy, and AC1's shape follows the recorded
verdict.

### T2: The rules land, each in exactly one owning file

**Verification mode:** goal-based check.

**Depends on:** T1

**Touches:** packs/core/.apm/skills/new-spec/SKILL.md, packs/core/.apm/skills/new-spec/assets/spec.md

**Tests:**
- AC1: pin the split test's phrase, the substitution test's phrase, and the
  sentence deferring the boundary to the examples.
- AC22: pin the conjunction cue, scoped to "two different predicates", and the
  clause giving the examples precedence over the cue.
- Deny-list assertion: removed during post-implementation review. It scanned
  the test module's own constants rather than the shipped prose, so it could
  only fail in the commit that introduced an offending pin; retargeting it at
  the shipped files reds on correct text, because `the same constraint` ships
  inside E4 as the phrase being warned against. Recorded as a comment on
  `RULES` and enforced at review.
- AC2: pin each of E1-E5 by identifier plus its verdict string; assert each
  example text occurs exactly once in its owning file.
- AC3: `SKILL.md`'s citation of the independence rule names the owning file and
  the section within it, not merely the file.
- AC4 / AC5: the template requires the firing input and enforcement mechanism per
  limit, with "missing **either** fact", and resolves two limits over one quantity
  by ordering or an explicit non-binding declaration.
- AC17: the template requires a stated limit to name the reference point it is
  measured from, chosen to be invariant under rearrangement of the subject.
- AC18: the template forbids delegating a limit's value to the implementer.
- AC19: pin the criterion-level give-away sentence (function parameters, a
  helper, a call sequence).
- AC16: the template requires deleting a non-establishing claim while keeping the
  only written form of a comparison value, and states the literal test "could a
  wrong implementation now pass this?".
- AC6 / AC7: `SKILL.md` requires the corpus task drafted into the plan's first
  tasks before a refusal criterion is finalised, and an unreachable corpus
  recorded as an Unverified assumption under step 3 — its own pinned sentence,
  not a copy of AC6's.
- AC8 / AC9: step 8 requires citation by document and identifier over
  restatement, and recording the owner when one rule is found twice.
- AC10: step 4 carries pointers to every rule that applies while criteria are
  written, restating none.
- AC12: step 6 requires the deletion pass with its three questions, and cuts
  taken to the human with conformance fixes separated from scope calls.
- AC11: for each rule, the normative sentence appears in its owning file and in
  neither of the other two.
- AC20: step 5 states that the plan carries mechanism and never restates a
  criterion, with the paste test over the whole plan except `## Constraints` and
  the durable-output map.
- AC21: step 6's convergence rule names the plan — persistent under-specification
  findings mean the plan is over-specified and is reduced before the existing
  three-pass escalation, not extended.


**Approach:**
- Template `## Acceptance Criteria` guidance gains these bullets: the one-contract rule with its conjunction cue first (AC1); the five
  worked examples (AC2); the bound ledger as a sibling of the existing
  pass/fail-bar bullet (AC4) with the two-limit resolution (AC5); the limit-origin
  rule (AC17) and the no-delegated-value rule (AC18) beside them; and the
  claim-minimality rule (AC16); and the criterion-level mechanism give-away
  (AC19). AC19 cites the Objective-guidance line and `SKILL.md`'s design-doc
  anti-pattern rather than restating either — that citation is mechanism here,
  not a second obligation in the criterion. Match the surrounding voice.
- The five worked examples are already drafted and smoke-tested against the
  shipped rule wording — 6 of 6, counting two adopter criteria outside the set.
  T2 writes these verbatim and invents none. Cite them as E1-E5 everywhere:
  - **E1 — splits.** "`writer.py` emits `manifest.json` with keys in byte-sorted
    order, and `--dry-run` prints that manifest without writing a file." Two
    different predicates; no single sentence covers both. The base case where the
    conjunction cue and the split test agree.
  - **E2 — stays one.** "no sensitive data reaches stdout, stderr, logs, or skill
    output surfaced to the agent." One predicate substituted at each member of an
    enumerated set, checkable as written at every member. Reuse the channel list
    from the existing output-channel bullet verbatim; do not paraphrase it.
  - **E3 — stays one.** "the digest preimage is the u64be path length, the path
    bytes, the execute byte, the u64be content length, then the content bytes."
    One comparison value expressed in parts — the split test never engages,
    because there is one failure and one remedy.
  - **E4 — splits.** "the same constraint, correctness, holds across stdout and
    the exit code." "X is correct" is not checkable as written: it expands into a
    different check per member. This is the anti-licence against reframing a
    bundle as one constraint over a domain, and without it E2's shape is available
    to any author.
  - **E5 — stays one.** "session cookies are set `Secure` and `HttpOnly`."
    Different failure modes (interception, script access) but one substitutable
    predicate and one remedy. Shows that separate failure modes alone do not
    split when the predicate survives substitution.
- Add AC6's corpus obligation to `SKILL.md` where the plan's task set is
  specified; make step 3's no-corpus case a pointer to it.
- Extend `SKILL.md` step 8 with AC8's ownership discipline, and AC9's duplicate resolution — the step already
  carries "one canonical home per fact", so this widens an existing sentence's
  scope to the acceptance-criteria surface rather than adding a new doctrine.
- Add AC12's deletion pass to `SKILL.md` step 6, after the convergence guidance,
  and extend step 6's convergence rule to name the plan (AC21) — reduce before
  the existing three-pass escalation.
- Add AC20 to `SKILL.md` step 5's push-back list: the plan carries mechanism and
  never restates a criterion, with the paste test over the whole plan bar
  `## Constraints` and the durable-output map.
- Add step-4 pointers: one naming the template's `## Acceptance Criteria` block as
  owner of the criterion-shape rules, one naming step 8 for citation discipline,
  one naming step 5 for the corpus obligation. Pointers only.
- `new-spec/SKILL.md` is 481 lines total (11 of them frontmatter), well under the
  500-line advisory and the 1,000-line `CAT-S003` error ceiling, so there is real
  headroom — unlike `work-loop/SKILL.md`. Keep the net delta modest anyway.

**Done when:** every test above passes as a manual grep, and
`python3 -m agentbundle catalogue lint --root . --deep` reports no new ERROR for
either edited file, run unpiped, against the recorded baseline of 0 ERROR /
68 WARN.

### T3: Contract tests pin each rule and red under mutation

**Verification mode:** goal-based check. No PLAN stub is materialised: the
assertions are greps over document text, not a compressible logic invariant, so
`docs/CONVENTIONS.md`'s TDD stub obligation does not attach.

**Depends on:** T2

**Touches:** packs/core/tests/skills/new-spec/

**Tests:**
- AC2: a presence assertion over E1-E5 and their verdict strings, so deleting
  any example reds a test, plus an exactly-once assertion per example.
- AC13: one assertion per rule (AC1, AC3-AC10, AC12, AC16-AC21) pinning the rule's
  normative phrasing against the whitespace-flattened body of its owning file,
  following the idiom at `test_repository_anchors.py:11`.
- One assertion per rule AND per worked example for AC11: present in the owner,
  absent from the other two source files.
- One assertion that AC7's step-3 sentence is its own text, not a second copy — the
  owning sentence occurs exactly once in `SKILL.md`.
- AC15's structural assertions over the new eval entry (see T4).
- AC2's smoke gate: the shipped wording is run against every example in AC2's
  set and must classify each correctly before it is pinned.
- The AC14 mutation, recorded per rule: delete the phrase from its owner, observe
  the named test fail, restore by editing.

**Approach:**
- Add `packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`,
  resolving paths from `Path(__file__).resolve().parents[3]` as the siblings do.
- Flatten with `" ".join(text.split())` so a pinned phrase may wrap in the source
  without breaking the assertion.
- Choose each pinned phrase to name what the rule *requires*, not where it sits,
  so the pin cannot survive the rule's removal.
- Restore each mutation by editing the text back, never by `git checkout`,
  `reset`, or `stash` — the stash stack is shared across worktrees.

**Done when:** `python3 -m pytest packs/core/tests/skills/new-spec/ -q` is green
(baseline: 10 passed), and each mutation is recorded with the failing node id.

### T4: The eval harness exercises the new rules

**Verification mode:** goal-based check.

**Depends on:** T2

**Touches:** packs/core/.apm/skills/new-spec/evals/evals.json

**Tests:**
- The file parses as JSON.
- A new entry exists, located by its unique `id` — not by array length. The array
  currently holds **seven** entries; an exact-count assertion would be wrong on
  arrival and would break on any later eval addition.
- The new entry's `id` is unique within the array, and it carries `id`, `prompt`,
  `expected_output`, and `assertions`, matching the shape of the existing seven.
- Its assertions require splitting a bundled criterion, demanding the bound
  ledger's two facts, and citing an owning document instead of restating a rule.
- Its `expected_output` describes the correct behaviour — checked by reading it
  against the three rules' owning sentences, and recorded as a manual check.

**Approach:**
- Add one eval whose prompt presents all three defects at once, so a partial
  answer cannot satisfy it.
- Extend T3's test file with these structural assertions rather than adding a
  second test file.
- `spec.md` AC15's "at least one eval" is the single statement of the floor; this
  task asserts the specific entry it adds and does not restate the floor.

**Done when:** the file parses, the structural assertions pass, the `id` is
unique, and the `expected_output` review is recorded.

### T5: Projections, release surface, and spec index are consistent

**Verification mode:** goal-based check.

**Depends on:** T3, T4

**Touches:** .claude/skills/new-spec/, .agents/skills/new-spec/, packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.md, docs/specs/README.md, web/src/lib/now-highlights.generated.json

**Owner: the supervising session, not the headless worker.** Every command in
this task is a form the worker is refused — an env-prefixed target
(`FORCE=1 make …`), a bare interpreter (`python3 tools/build-site.py`), and git
writes. Do not dispatch T5.

**Tests:**
- `diff -rq packs/core/.apm/skills/new-spec .claude/skills/new-spec` and the same
  against `.agents/skills/new-spec` report no differences. Directory-level, not a
  hand-listed file set: the skill ships six files and a listed set has already
  been miscounted twice in this plan's history.
- `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` both read
  `2.15.3`.
- `docs/product/changelog.md` carries a `## [core][2.15.3]` section directly
  beneath `## [Unreleased]` and above `## [core][2.13.0]`.
- `web/src/lib/now-highlights.generated.json` equals a fresh recompute from the
  changelog, per
  `tools/test_build_site_routing.py::test_the_committed_now_projection_matches_the_changelog_source`.
- `catalogue verify --root .` reports zero `CAT-V-014` findings.
- `docs/specs/README.md` carries a row for this spec.

**Approach:**
- Bump the version by hand in `pack.toml` and `.claude-plugin/plugin.json` — the
  self-host projection propagates content, not versions. Core is not listed in the
  root `.claude-plugin/marketplace.json`, so there is no fourth file there.
- Insert the changelog section **immediately below `## [Unreleased]`**, above
  `## [core][2.13.0]`. The file's own rule at `docs/product/changelog.md:11`
  requires a released section to be free-standing directly beneath `[Unreleased]`;
  "above the current topmost heading" would put it above `[Unreleased]` instead,
  and the topmost-`[core]` test passes either way, so nothing else catches this.
- Add the `docs/specs/README.md` row (`new-spec` step 7).
- Then run the **full** regeneration chain, in this order — a partial chain fails
  a gate for a reason that reads as an unrelated regression:
  `FORCE=1 make build-self && rm -rf dist && make build && python3 tools/build-site.py`.
  `build-self` writes only the `.claude/`/`.agents/` projection and refuses a dirty
  tree without `FORCE=1`; `make build` is the only thing that writes `dist/`, which
  otherwise goes stale for every `.apm` source touched and fails `CAT-V-014`; and
  `tools/build-site.py` is the only thing that regenerates
  `web/src/lib/now-highlights.generated.json` from the changelog. Never hand-merge
  that JSON — its gate asserts full equality against a recompute.
- Run `make ci`, not only `make build-check`: the CI job of that name runs steps
  the local target does not, and this change both bumps a version and edits a
  changelog.

**Done when:** both directory diffs are clean, the three version surfaces agree,
`catalogue verify` reports no `CAT-V-014`, and `make ci` exits zero.

## Rollout

- **Delivery:** big bang, fully reversible — guidance prose, tests, a JSON eval
  entry, and a version bump. Rollback is a revert; nothing is irreversible, and
  no data or published event is involved.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** the regeneration chain must follow the source edits,
  and the version bump must land in the same commit as the content change
  (`CAT-V-005` fails a `pack.toml`/`plugin.json` mismatch). No other ordering
  applies.

## Risks

- **The rules are read but not applied.** Guidance prose has no runtime, so the
  contract tests prove only that the sentences exist. The eval in T4 is the only
  behavioural check, and it is model-graded and not run in these gates. Accepted:
  a checker is an explicit non-goal, and the review-time reader question was
  adjudicated as an accepted scoped decision rather than a defect. AC1's
  structural form narrows the exposure, because its test is answerable by a
  reviewer against the criterion itself and AC2's examples calibrate the
  boundary, with no change to the reviewer primitive.
- **A future author satisfies AC8 by copying rather than citing.** This is the
  failure AC11's absence assertions exist to catch, which is why they assert
  absence from the other two files rather than only presence in the owner. The
  intra-file case is covered for AC6 and AC7 specifically, whose fallback is the one place
  this plan deliberately mentions a rule twice.
- **Parallel YAGNI sessions touch the same guidance block.** AC16 lands in the
  template's `## Acceptance Criteria` guidance, which concurrent work on
  acceptance-criterion claim handling will also reach. The owner has accepted that
  those sessions reconcile against AC16's owning location; this plan does not
  serialise against them, and AC11's assertions will surface a duplicate if one
  lands.
- **Tail size.** Well under 2,000 reviewable behaviour and test lines, so no
  WIDE/MIXED/DEEP review-shape declaration is required. Re-check at the
  finish-time tail-triage item rather than assuming it.
- **A partial regeneration chain.** Three generated surfaces sit on three
  different commands, and running one is the easy mistake. Because `dist/` is
  gitignored, a stale one leaves no trace in `git status`, so the failure surfaces
  later as `CAT-V-014` on files this change never touched. T5 runs the whole chain
  in order.
- **Stale `dist/`.** `make pre-pr` aborts on `CAT-V-014` before reaching the
  skill-spec lint, reporting a different failure and hiding this one. Use
  `catalogue lint --deep` directly for T2's check.

## Changelog

- 2026-08-28: round 5 applied. It found the piece four rounds of wording had
  missed: the test that separates a genuine enumerated set from a bundle
  reframed as one existed only inside example prose, so AC1 yielded no verdict
  on ordinary adopter criteria and its own conjunction cue contradicted its own
  example 2. AC1 now carries the substitution test — rewrite the criterion as a
  single predicate with a member substituted in; it stays one only if that
  predicate is checkable as written at every member rather than expanding into a
  different check per member. Verified 6 of 6 against the example set plus the
  two adopter criteria round 5 showed were undecidable. The conjunction cue moved
  to AC22 re-scoped to predicates (it was splitting E2), the no-numeric clause
  left AC1 for Boundaries which already owned it, and a fifth example E5 covers
  the different-failures/shared-remedy quadrant the set had missed. Examples now
  carry stable identifiers E1-E5 after mismatched naming schemes let a
  three-vs-four cardinality drift survive a full sweep.

- 2026-08-28: round 4 applied, adjudicated (15 sustained, 4 refuted, 1
  indeterminate). The independence rule's prose exceptions are gone: three
  successive formulations failed, the last by letting an author reframe a bundle
  as one constraint over a domain, so AC1 now states only the split test and
  AC2's four normative worked examples fix the boundary. A fourth example — a
  bundle framed as a domain that still splits — is load-bearing, not
  illustrative: it is the only thing that stops predicate inflation. AC19 was
  reduced to one contract with its citation moved to T2 as mechanism; AC20's
  paste test was widened to the whole plan bar two sections after it was shown
  to miss `## Design (LLD)` and `## Risks`, where a restatement of AC1 was
  already live. The AC3 cut is deferred to the owner: adjudication established
  it is NOT entailed by AC10, so the reviewer's ground for cutting it fails.
  Method change: repairs are now swept across every co-referencing site and
  verified by a re-runnable checker rather than by eye.

- 2026-08-28: two faulty round-3 repairs corrected before the gate. (i) The
  Objective still enumerated the cut criterion's failure mode and omitted the
  dominated-bound failure behind AC5; both fixed, twelve failures now each map
  to a criterion. (ii) AC19 had been folded into `assets/spec.md`'s
  "Implementation detail belongs in `plan.md`" line, but that line sits inside
  the `## Objective` HTML comment and governs the Objective paragraph, not
  criteria — so the fold put a criterion-shape rule in the wrong section. AC19
  is restored to the `## Acceptance Criteria` guidance and now cites the
  document-level doctrine at its two existing altitudes instead of restating it.
  Process note: round 3's findings were applied without routing them through
  `finding-adjudicator`, unlike rounds 1 and 2. That is what admitted a wrong
  remedy; round 4 is adjudicated.

- 2026-08-28: round 3 applied (16 findings; 15 originated in the 9->22 split or
  the new criteria, which is a referential repair rather than a design round).
  Substantive: the independence rule's carve-outs were given an explicit
  precedence, which round 4 then showed was itself the escape — an author could
  reframe any bundle as one constraint over a domain — so round 4 moved the
  distinctions into AC2's normative examples and reduced AC1 to the split test; the paste test was scoped
  to `Tests:`/`Approach:` bodies after it was shown to delete this plan's own
  template-mandated `## Constraints` entries; the plan-side convergence rule was
  ordered before the three-pass escalation. Deletion pass on the peer-batch
  additions cut one criterion (the freeze-time licence, already covered by
  `SKILL.md`'s "where they're known") and folded another into the template line
  that already owned its doctrine. 22 -> 21 criteria. Every stale AC citation in
  both documents was repaired and re-audited.

- 2026-08-28: absorbed a third batch of peer-session learnings. Adopted: the
  plan-carries-mechanism rule with its paste test, and the plan-side convergence
  rule; the "and" conjunction cue folded into the independence rule rather than
  becoming a second owner of it. The proposed freeze-time licence for incomplete
  task file lists was later cut in round 3 — `SKILL.md`'s specificity rule
  already says "where they're known". Their two 2.3x size ratios were adapted, not shipped: measured
  here 2.3x is the 88th percentile of 358 plan/spec pairs, so the signal is real
  but the constant is tuned to one document; AC20's paste test carries it
  parameter-free. Routed out of scope: the stub-replaces-prose convention (it
  moves `docs/CONVENTIONS.md` and work-loop's tdd-stubs reference) and
  cheapest-disconfirming-evidence-before-review (already routed to the sibling
  spec as measurement-over-review-rounds).

- 2026-08-28: AC1's wording refined after a self-application check: 6 of this
  spec's own 9 criteria exceeded a literal "single sentence" while all 9 passed
  the operative single-closing-observation test, so the rule now leads with the
  two independence tests and names one sentence as the usual shape rather than a
  requirement. A rule its own author breaks two-thirds of the time would be
  ignored; the substance the owner approved — independence, not brevity — is
  unchanged.
- 2026-08-28: **owner amendment — the numeric threshold is dropped.** Criterion
  independence now ships as a structural test (one sentence, partial-credit test,
  enumeration allowed under one lead sentence, one closing observation) with no
  number. Basis: T1's corpus probe measured that no numeric detector is portable
  across spec shapes — a 150-word trigger fires on 0.0% of `ui` criteria and
  13.8% of `data` criteria, and 35% of over-150 criteria are legitimate
  enumerations. This supersedes the earlier "hard number as a review trigger"
  decision and dissolves two review findings (the percentile misstatement and the
  unverifiable portability clause) rather than fixing them. A sixth rule, the
  claim-minimality test, was added in the same amendment; it was absent from
  `docs/CONVENTIONS.md`, every ADR/RFC, and every shipped skill.
- 2026-08-28: applied the sustained findings from spec-review round 1 (16
  sustained, 7 refuted). Plan-side: step-4 trigger pointers for the corpus and citation rules and a
  corrected ownership rationale; explicit verification mode on every task; T4's
  baseline corrected from four eval entries to seven and keyed to a unique `id`;
  T5's changelog placement corrected to directly beneath `[Unreleased]`; T5's
  parity check changed to a directory-level `diff -rq`; `SKILL.md`'s line count
  restated as 481 total.
- 2026-08-28: T5 corrected before approval — its regeneration chain named only
  `build-self`, which would have failed `CAT-V-014` on stale `dist/` and left
  `web/src/lib/now-highlights.generated.json` inconsistent with the new changelog
  entry. T5 now runs the full four-command chain and is marked supervisor-owned.
- 2026-08-28: initial plan. Version target corrected from `2.14.0` to `2.13.1`:
  `packs/AGENTS.md` § *Version bump rule* owns the decision, and this change adds
  no primitive. The eval-harness criterion was added in the same read, when the scoped guidance's
  eval-harness rule surfaced an obligation the first draft missed.
