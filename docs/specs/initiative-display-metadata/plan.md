# Plan: initiative display metadata

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `packs/AGENTS.md` § Version bump rule and
  § Self-hosting projection; `packs/AGENTS.md` § "Shipped pack content carries
  no internal-governance citations" for the SKILL.md wording. Analogous
  implementation: `_repo_backlog_entry_dict` in the same module, which passes
  its display prose through unfiltered under the same trust model, with its
  rationale in its docstring. Its tests are the `RepoBacklogContractTests`
  class in `tools/test_workspace_status_cli.py`.

## Approach

One emitter changes. `_build_json` builds each entry of `initiatives_out` with
two hard-coded literals; both become reads of the parsed initiative, coerced
with `str()` so the projected JSON type is always string regardless of what the
TOML held. Nothing else in the module moves: the sibling `_public_ini_slug`
call on `slug` and the status enum clamp both stay exactly as they are, because
neither field is in scope.

The contract and the tests then follow the behavior. `SKILL.md` loses the
redaction paragraph and regains the rendering template; three test assertions
invert. The adapter projections are regenerated rather than edited.

## Constraints

- `.apm/` is the source of truth; the two adapter copies are generated. Editing
  a projection directly is forbidden, so every change runs through
  `catalogue self-host` and all three copies stay byte-identical.
- Shipped pack content carries no repository-internal citations, so the
  `SKILL.md` wording states the rule directly and names no intent, spec, or
  acceptance criterion.
- `tools/test_local_ci_shared_test_deduplication.py` pins the method count of
  `tools/test_workspace_status_cli.py` as a bare `163` in two assertions, at
  lines 1169 and 1390. T1 and T2 each add one method, so both literals move.
  That file's convention requires a dispositioned re-pin rather than a bare
  bump; T2 owns the exact note.

## Construction tests

Every criterion is verified in `tools/test_workspace_status_cli.py`, which
already owns this projection's CLI surface and runs the real script as a
subprocess through its `_run_cli` helper.

- AC-0001 is carried by the two converted tests. Their fixture values are
  copied from this repository's own active initiatives, so the charset under
  test is the corpus rather than invented input.
- The retired `AC-0002`'s design decision is pinned by one new regression case;
  no existing test supplies a non-string.
- AC-0003 is a content assertion over the shipped `SKILL.md`, placed with the
  existing `SkillWiringTests` class, which already reads that file.
- Determinism is not re-verified here: `test_cli_deterministic` in the same
  file already owns it, and a second assertion would be a second home.

## Durable-output map

| Spec durable output | Task | Evidence at closeout |
| --- | --- | --- |
| User-facing promise (`SKILL.md`) | T2 | AC-0003 content assertion green |
| Release history (`changelog.md`) | T4 | Released `[core]` entry present |
| Interface compatibility (pack version) | T4 | `check-release-impact` passes |

## Design (LLD)

### Design decisions

Coercion happens at the emitter, not at parse time. The parser is shared with
reconciliation and closeout, which compare and route on other fields; changing
what it stores would widen the change past the projection the spec bounds. The
emitter is the last point before the value becomes agent-visible text, which is
the only place the spec makes a claim about.

`str()` rather than a type check with a fallback: a fallback needs a value to
fall back to, and the only candidate is the sentinel the spec forbids
reintroducing.

`str()` reports what the projection received rather than reconstructing the
source syntax. A non-string in a display field is an authoring error, and
showing the reader what arrived is more useful than making it look like valid
TOML. The alternative, a TOML-faithful renderer, is a new mechanism for a case
the corpus has never produced.

**Non-string coercion is a design decision, not a criterion** (`AC-0002`,
retired). Measured through the real script: `123` → `"123"`, `4.5` → `"4.5"`,
`true` → `"True"`, `[1, 2]` → `"[1, 2]"`, `{a = 1}` → `"{'a': 1}"`, and
`1979-05-27T07:32:00Z` → `"1979-05-27 07:32:00+00:00"`. The boolean and
date-time texts differ from what an author would have written, which is the
part worth recording. Its pin is the regression case in T1: the decision is
protected by a test that reds if coercion is removed, not by a checkbox a
completion gate reads. Three date-time forms beyond the offset one are
deliberately unmeasured — no corpus value has any of them, and enumerating
them was the coverage gap that kept this obligation from converging as a
criterion.

### Failure, edge cases & resilience

An absent `name` or `milestone` key already yields `""` from the parser's
default, and `str("")` is `""`, so an initiative that declares neither projects
two empty strings. That is the pre-redaction behavior and needs no new rule.

A newline inside a value would break the single-line rendering template. No
corpus value contains one, the spec's `Ask first` boundary covers adding a
bound, and the sibling `summary` has the same exposure and no bound — so this
is recorded as a known shape, not handled.

## Tasks

### T1: project both display fields instead of the sentinel

**Depends on:** none

**Verification mode:** TDD

**Tests:** (`tools/test_workspace_status_cli.py`)
- Convert `test_benign_initiative_display_fields_are_still_redacted` into
  `test_initiative_display_fields_project_as_authored`, asserting AC-0001. The
  current fixture carries only `·` (its dash is an ASCII hyphen), so the
  charset rider would hold vacuously against it. Replace it with two
  initiatives copied from `workspace.toml`: `ini-002`'s pair, whose milestone
  carries `·` and `–`, and `ini-009`'s pair, whose milestone carries `·`, `—`,
  a semicolon and a straight apostrophe. Their union is all five characters,
  and two initiatives also give the criterion's quantifier something to range
  over. `stub: true` — the red is the equality assertions against
  `"workspace.toml"` failing against those authored values.
- Convert `test_initiative_display_prose_is_not_projected` into
  `test_initiative_display_prose_projects_verbatim`, keeping its unusual input
  and asserting the value arrives unchanged. This is the case that records the
  trust-model decision in the suite.
- One regression case pinning the retired `AC-0002`'s design decision, over
  both `name` and `milestone`: `123` → `"123"`, `true` → `"True"`, and
  `1979-05-27T07:32:00Z` → `"1979-05-27 07:32:00+00:00"`, asserting the
  projected text by equality. Equality, not `isinstance(value, str)` — the
  sentinel this change removes is itself a string, so a type-membership
  assertion passes against the pre-change emitter and pins nothing. Verified:
  run against the unchanged code, a non-string fixture projects
  `'workspace.toml'` for both fields and `isinstance` holds.
- Update the third pinning site inside `test_cli_rich_fixture_shapes`, whose
  fixture already declares `milestone = "M1"`, to expect the authored value.
- Ten assertions invert across the three tests, not three: six equality
  assertions, plus four `assertNotIn` guards naming fixture-authored display
  prose (`ignore previous instructions`, `/outside/should-not-leak`,
  `Platform Core`, `Adopt`), each of which becomes false once the fixture's own
  values project. `/outside/should-not-leak` is among them: the fixture authors
  it into `milestone`, so it is a display-field assertion despite looking like
  a path guard. Only `assertNotIn(str(root), ...)`, which catches a path leaked
  from the running process, survives untouched.

**Approach:**
- Replace the two literals in `_build_json` with `str()` reads of the parsed
  initiative.
- Run `catalogue self-host --write` and confirm all three copies hash equal.

**Done when:** the four cases named in this task's `Tests` are green and
`tools/test_workspace_status_cli.py` passes whole.

### T2: bring the skill contract back in line with the behavior

**Depends on:** T1

**Verification mode:** goal-based check

**Tests:** (`tools/test_workspace_status_cli.py`, `SkillWiringTests`)
- New content assertions for AC-0003 over the shipped `SKILL.md`, one per
  conjunct: `name` and `milestone` both appear in the `initiatives` summary
  row; both per-field rows describe a value read from `workspace.toml` rather
  than a sentinel; the rendering template line is present; and both the
  `Redacted display fields` phrase and the separate "Render the initiative
  slug alone" instruction are absent. The absence conjunct needs both checks —
  those two sentences sit at different lines, so one phrase check passes with
  the instruction still shipped.

**Approach:**
- Restore the `Active initiatives` template line and remove the
  `Redacted display fields` paragraph.
- Return the key list's two per-field rows to describing values read from
  `workspace.toml`, and re-add `name` and `milestone` to the `initiatives`
  summary row, which currently enumerates only `slug`, `status`, `brief_queue`
  and `queue_empty`.

- Re-pin both `163` literals in
  `tools/test_local_ci_shared_test_deduplication.py` to `165` once T1's and
  T2's additions both exist. The note dispositions the actual delta, which
  includes a rename branch the exemplar at that file's lines 89-92 does not
  have: two renames, count-neutral, same bodies with their display assertions
  inverted; two additions, T1's non-string case and T2's contract assertion;
  no removals. The renames are why the pin moves by exactly the number of
  additions. The note also covers the preceding `162 -> 163` re-pin, which
  landed bare, so the contract regains a continuous account rather than a
  number with a gap behind it.

**Done when:** the AC-0003 assertion is green, `catalogue verify` reports `ok`,
and `tools/test_local_ci_shared_test_deduplication.py` passes.

### T3: exercise the real script

**Depends on:** T1, T2

**Verification mode:** visual / manual QA

**Tests:** none — this task's evidence is recorded observation, per the spec's
Testing Strategy.

**Approach:**
- Run the script against this repository's own `workspace.toml` and read the
  four active initiatives' projected values.

**Done when:** AC-0001 is observed against this repository's own
`workspace.toml` rather than a fixture, with the observed values recorded in
the verification ledger as evidence rather than as the condition.

### T4: ship the pack change

**Depends on:** T1, T2

**Verification mode:** goal-based check

**Tests:** none — the release surface is owned by `check-release-impact`; a new
assertion would duplicate an existing gate.

**Approach:**
- Increment `pack.toml` and `.claude-plugin/plugin.json` together.
- Add the released `[core]` changelog entry with one `Highlights` bullet,
  free-standing directly beneath `[Unreleased]`.

**Done when:** `check-release-impact --base origin/main` passes and
`tools/test_build_site_routing.py` is green.

## Rollout

- **Delivery:** big bang, within one pack release. Reversible by restoring the
  two literals; no migration and no persisted state is involved.
- **Deployment sequencing:** the emitter, the contract and the version ship
  together; a version claiming the new behavior without the emitter would be
  wrong. No infrastructure or external-system dependency is involved.

## Risks

- A consumer outside this repository may have come to depend on the sentinel.
  Probed: `workspace-mcp` does not re-emit `initiatives`, and the shipped
  contract told consumers to render the slug alone rather than to read the
  value, so a consumer depending on the literal was depending on text it was
  instructed to ignore.
- The dedup guard's pinned method count reds if the test count changes.
  Mitigated by converting rather than deleting, which holds the count.

## Changelog

- 2026-09-14 — drafted.
- 2026-09-14 — revised from shaping review round 1: corrected the dedup-guard
  arithmetic (F1), enumerated the ten inverting assertions and the leak guard
  that survives (F2), added the `initiatives` summary row (F3), moved the
  boolean-rendering decision out of the criterion (F4), dropped the unframed
  107-character length (F5), and made T3's exit condition a property rather
  than four corpus literals (F6).
- 2026-09-14 — round 3: AC-0002 demoted to a design decision with a regression
  pin, on owner authority. The deletion pass had reshaped it to assert
  `isinstance(value, str)`, which passes against the pre-change emitter because
  the sentinel is itself a string — a criterion that could no longer fail
  (F12). Its quantifier also covered four TOML date-time forms against one
  measurement (F14). Three rounds each landed on it; the state it constrains is
  unreachable through any authoring path this spec permits. Also corrected the
  re-pin note to disposition T1's rename branch (F13) and bound T3 to AC-0001
  by name rather than by restatement (F15).
- 2026-09-14 — deletion pass before approval: cut six Not-applicable durable-
  output rows, the `Behavior & rules` restatement, and three `none` rollout
  lines; reshaped AC-0002 from six enumerated texts to one substitutable
  predicate over the closed type set with the two decision-bearing texts kept.
- 2026-09-14 — revised from round 2, which was four-fifths consequences of
  round 1's own repairs: narrowed the leak-guard carve-out that had forbidden
  T1 (F7), gave every AC-0002 class a measured projected text and a case (F8),
  split AC-0003's four conjuncts into four assertions (F9), replaced the
  fixture so AC-0001's charset rider cannot hold vacuously (F10), and swept
  F5's leftovers out of the plan and Assumptions (F11).
