# Plan: new-rfc follow-on queue-write guard

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially,
> note why in the changelog at the bottom.

## Approach

Two targeted prose changes to `packs/governance-extras/.apm/skills/new-rfc/SKILL.md`:

1. **Trigger description** (frontmatter): extend the `description` field to also
   match "generate follow-on specs/ADRs for an Accepted RFC" invocations —
   making `## After acceptance` reachable from a follow-on session.

2. **Session-fragmentation guard** (`## After acceptance`): insert a guard
   clause at the top of the section that fires when the RFC is already
   `Accepted` at invocation time. The guard checks `workspace.toml` (both
   bare-string and inline-object entry forms; all active-initiative sections),
   re-surfaces the queue-write prompt if paths are absent, and skips silently
   otherwise. The existing prompt block below is unchanged.

After editing the seed: run `FORCE=1 make build-self` to regenerate the
projection, then `make build-check` to confirm zero drift. Bump the pack
version in `pack.toml` (line 3, `[pack]` table only) and `plugin.json`.

Riskiest part: the trigger description update must be specific enough not to
fire on unrelated `new-spec`/`new-adr` requests, while being broad enough to
cover the "implement follow-on work from an Accepted RFC" pattern.

## Constraints

- Edit the seed (`packs/governance-extras/.apm/skills/new-rfc/SKILL.md`),
  not the projection (`.claude/skills/new-rfc/SKILL.md`).
- No internal-governance citations in shipped skill prose (AGENTS.local.md rule).
- Pack version bump: `0.7.0` → `0.8.0`. Scope the edit to line 3 of `pack.toml`
  (the `[pack]` table `version` field); line 19 (`[pack.adapter-contract]
  version = "0.8"`) is a different field and must not be changed.

## Construction tests

**Manual verification (all five scenarios):**
- Scenario A — in-session acceptance: RFC just transitioned to Accepted; guard
  fires (status Accepted, paths absent); single prompt fires once; after paths
  added, subsequent call in same session skips (paths present). No double-prompt.
- Scenario B — follow-on session, Accepted RFC, workspace.toml exists, paths
  absent: guard fires, prompt re-surfaced.
- Scenario C — follow-on session, workspace.toml absent: guard skips silently.
- Scenario D — follow-on session, paths already in `[work].active` or
  `[work].shipped`: guard skips silently.
- Scenario E — trigger boundary: positive queries ("RFC-0067 was accepted —
  create the follow-on specs") route to `new-rfc`; negative queries ("Write a
  spec for the CSV export feature") do not. Cross-pack check: also read the
  `new-spec` (core) and `new-adr` descriptions against the positive queries
  and record that neither fires — the activation harness is same-pack-only
  and cannot cover this; manual trace required.
- Scenario F — partial queuing: workspace.toml has one spec path queued and
  one absent; guard fires over the missing path only; the already-queued path
  is not re-prompted.

**Goal-based check:** `make build-check` exits 0 after `FORCE=1 make build-self`.

## Tasks

### T1: Write spec.md and plan.md

**Depends on:** none

**Tests:**
- Spec has Status: Approved, all ten ACs including AC1 covering the trigger
  description update, and assumptions.
- Plan has approach, constraints, and tasks with Tests/Approach/Done-when.

**Approach:**
- Create `docs/specs/new-rfc-followon-queue-write/` directory.
- Write `spec.md` using new-spec full-mode template (done).
- Write `plan.md` (this file, done).

**Done when:** both files exist, spec Status is Approved, and adversarial
pre-EXECUTE review passes.

---

### T2: Extend the trigger description in new-rfc SKILL.md

**Depends on:** none

**Tests:**
- The frontmatter `description` field now includes a trigger for "generate
  follow-on specs/ADRs for an Accepted RFC."
- The existing trigger phrases ("RFC", "propose a change to...", etc.) are
  preserved.
- Both Do NOT halves disambiguated at trigger level (AC10): "already-decided
  things → new-adr" scoped to standalone decision recording; "single-feature
  specs → new-spec" scoped to authoring a spec without an Accepted RFC context.
  A query like "create the follow-on specs for RFC-0067" routes to `new-rfc`.
- Description remains trigger-shaped and under 1024 characters (Kiro cap);
  any longer framing moves to the skill body, not the description field.

**Approach:**
- Edit `packs/governance-extras/.apm/skills/new-rfc/SKILL.md`.
- In the YAML frontmatter `description` value, append (after the existing
  final sentence) a clause covering the follow-on case, e.g.: "Also triggers
  on 'generate follow-on specs for RFC-NNNN', 'create ADRs for an accepted
  RFC', 'implement the follow-on work from an RFC'."

**Done when:** the frontmatter description covers the follow-on invocation
pattern and the existing triggers are unchanged.

---

### T3: Add session-fragmentation guard to ## After acceptance

**Depends on:** T2

**Tests:**
- Manual scenarios A–D and F read correctly through the prose.
- No internal-governance citations (RFC/ADR/spec numbers) appear in the new
  prose.
- The existing "Prompt the user: 'Add implementation specs to workspace.toml
  queue?'" block is minimally edited or unchanged below the guard.
- Both bare-string and inline-object workspace.toml entry forms are addressed
  in the guard.
- Multi-initiative handling matches the existing write-path's >1-active
  tie-break.
- Guard scope is limited to `spec/<path>` entries (the only queueable form);
  ADRs and CONVENTIONS edits are not checked and remain in the follow-on list.

**Approach:**
- Insert a guard clause immediately before the existing "When the RFC moves to
  Accepted, first offer to queue..." sentence in `## After acceptance`.
- Guard structure:
  - **When it fires:** `workspace.toml` is present AND any of the `spec/<path>`
    artifacts the agent is about to generate are absent from all active
    initiatives' three arrays. ADRs and CONVENTIONS edits are not checkable
    (not a queue-path form) and are excluded from the guard's loop; they stay
    in the follow-on artifact list that runs after the queue-write step. The
    guard collects absent spec paths; if any are absent, it fires the prompt
    over the missing subset. Partial presence (some spec paths queued, some
    absent) fires over the missing ones — not a skip. All-present → skip.
    Both the in-session and follow-on cases reach this same guard.
  - **Entry-form matching:** checks both `"spec/foo"` (bare string) and
    `{path = "spec/foo", ...}` (inline object) entries.
  - **Multi-initiative:** scans all `status = "active"` sections; if >1 active,
    reuses the existing tie-break (ask which initiative).
  - **Skip conditions:** workspace.toml absent → skip; paths already present
    in any of the three arrays → skip. After the prompt completes and paths
    are added, any subsequent call to `## After acceptance` in the same session
    finds the paths present and skips — preventing double-prompt.
  - **Action when fires:** route into the single shared prompt block below (the
    guard is a gating check, not a second prompt invocation).

**Done when:** the seed contains the guard clause; scenarios A–D and F trace
correctly; no governance citations in the new prose.

---

### T4: Bump pack version

**Depends on:** T3

**Tests:**
- The `[pack]` table `version` field in `pack.toml` reads `"0.8.0"`.
- The `[pack.adapter-contract]` `version` field in `pack.toml` is still
  `"0.8"` (unchanged).
- `plugin.json` `"version"` field reads `"0.8.0"`.

**Approach:**
- Edit `packs/governance-extras/pack.toml`: change `version = "0.7.0"` (the
  `[pack]` table `version` field, currently `"0.7.0"`) to `version = "0.8.0"`.
  The `version = "0.8"` line under `[pack.adapter-contract]` must not change.
- Edit `packs/governance-extras/.claude-plugin/plugin.json`: change
  `"version": "0.7.0"` to `"version": "0.8.0"`.

**Done when:** both files show `0.8.0`; adapter-contract version is untouched.

---

### T5: Update eval_queries.json for the trigger-description change

**Depends on:** T2

**Tests:**
- File contains at least three new `should_trigger: true` entries covering
  "follow-on specs/ADRs for an Accepted RFC" phrasing.
- File contains at least two new `should_trigger: false` entries that pin the
  boundary (spec/ADR requests with no RFC follow-on context).
- Existing false entries ("Write a spec for the CSV export feature", etc.)
  are intact and still false.

**Approach:**
- Edit `packs/governance-extras/.apm/skills/new-rfc/evals/eval_queries.json`.
- Add positive entries:
  - `"RFC-0067 was accepted — create the follow-on implementation specs"`
  - `"Generate the follow-on ADRs for that accepted RFC"`
  - `"The RFC was just accepted; now draft the follow-on specs for it"`
- Add negative entries that pin the boundary:
  - `"Create a spec for the dashboard feature"` (no RFC context)
  - `"Write the ADR for our database choice — we've already decided"`

**Done when:** eval_queries.json contains the new entries; existing entries
are intact.

---

### T6: Add changelog entry

**Depends on:** T4

**Tests:**
- `docs/product/changelog.md` `[Unreleased]` section contains an entry for
  governance-extras 0.8.0 describing the session-fragmentation guard.

**Approach:**
- Edit `docs/product/changelog.md`.
- Add a new bullet under `## [Unreleased]` → `### Fixed` (the
  session-fragmentation drop is a bug fix; place before the existing
  `desk-research-project-start` entry) describing the guard in
  `governance-extras 0.8.0`.

**Done when:** changelog has the 0.8.0 entry under `[Unreleased]`.

---

### T7: Run build-self and build-check

**Depends on:** T5, T6

**Tests:**
- `FORCE=1 make build-self` exits 0.
- `make build-check` exits 0.
- `.claude/skills/new-rfc/SKILL.md` contains the guard clause (grep confirms).

**Approach:**
- Run `FORCE=1 make build-self`.
- Run `make build-check`.
- Grep projection for guard prose to confirm propagation.

**Done when:** both commands exit 0; projection contains the guard clause.

---

### T8: Update workspace.toml and close the spec

**Depends on:** T7

**Tests:**
- `"spec/new-rfc-followon-queue-write"` is in `["ini-002".work].shipped`.
- It is absent from `["ini-002".work].queue`.
- `spec.md` Status is `Shipped` and all ten AC boxes are `[x]`.

**Approach:**
- Edit `workspace.toml`: move `"spec/new-rfc-followon-queue-write"` from
  `queue` to `shipped`. Use a targeted edit that preserves surrounding comments.
- Edit `spec.md`: change Status from `Approved` to `Shipped`; check all AC
  boxes (`- [ ]` → `- [x]`).

**Done when:** workspace.toml shows the spec in shipped; spec Status is Shipped;
all ACs checked.

---

## Rollout

Skill prose change in a pack that ships to adopters. No infra, no migration, no
deployment sequencing. The change is live for any adopter who refreshes their
pack after version `0.8.0` ships.

## Risks

- **Trigger over-fire**: if the description extension is too broad, `new-rfc`
  fires on unrelated requests that should go to `new-spec`. Mitigated by
  phrasing that explicitly names the Accepted-RFC follow-on context.
- **build-self side effects**: build-self can silently revert non-seed edits;
  run it AFTER all edits are applied and verify with `git status`.
- **pack.toml second version field**: the `[pack.adapter-contract] version`
  field (line 19) must not be changed. Mitigated by scoping the edit to line 3
  by literal value (`0.7.0` under `[pack]`).

## Changelog

- 2026-07-20: initial plan
- 2026-07-20: added trigger-description update (T2) after pre-EXECUTE
  adversarial review round 1 found the guard was unreachable without it;
  fixed entry-form and multi-initiative handling in AC2/AC4; added AC-close
  step to T6.
- 2026-07-20: added T5 (eval_queries.json) and T6 (changelog) after round 2
  found AC1's trigger change was untested and changelog entry was missing;
  relaxed AC5 to permit minimal lead-sentence framing edit; replaced line-
  number assertions in T4 with table+literal form; renumbered T5→T7, T6→T8.
- 2026-07-20: added scenario E to verify trigger boundary; clarified T3 guard
  design — single shared prompt block, no double-prompt; fixed T1 AC count
  (seven→nine); fixed T6 changelog placement to `### Fixed` subsection.
- 2026-07-20: added AC10 (description/Do-NOT disambiguation) and T2 constraint
  relaxation after round 4 found the extended trigger contradicts the existing
  Do NOT clause; added eval-harness goal-based check (report-only) to Testing
  Strategy; updated T8 AC count to ten.
- 2026-07-20: fixed T1 AC count (nine→ten); added decline-path re-prompt
  clarification to AC2 and scenario A after round 5 found the behavior was
  unstated; design decision: re-prompting after decline is intentional.
- 2026-07-20: changed AC2/AC4 from all-absent-fire/any-present-skip to
  per-artifact checking (absent-subset fires, all-present skips) after round 6
  found partial queuing silently dropped missing paths; added scenario F for
  partial queuing; updated T3 guard design accordingly.
- 2026-07-20: scoped guard to spec/<path> only (ADRs/CONVENTIONS not queueable)
  after round 7 found AC2 included un-representable artifact types; updated
  AC2, AC4, T3 tests, T3 done-when accordingly.
- 2026-07-20: rewrote AC10 from routing/orchestration framing to trigger-
  disambiguation-only after round 8 found the "follow-on routing" phrasing
  implied a wired hand-off the unchanged skill body does not implement; updated
  T2 test to match.
- 2026-07-20: added 1024-char Kiro cap constraint to AC10 and T2 after round 9
  confirmed round-8 fix and flagged the missing character bound.
- 2026-07-20: extended scenario E with cross-pack competitive check (new-spec
  + new-adr vs. positive queries) after round 11 found the activation harness
  is same-pack-only and cannot cover cross-pack exclusivity.
