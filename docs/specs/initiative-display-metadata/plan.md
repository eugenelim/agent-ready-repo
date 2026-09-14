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
  lines 1169 and 1390. Conversion holds that count for the three converted
  tests, but T1 and T2 each add one method, so both literals move to the
  recomputed value. That file's own convention requires a disposition note
  beside a re-pin rather than a bare number bump: name the additions, and state
  that nothing was removed or renamed.

## Construction tests

Every criterion is verified in `tools/test_workspace_status_cli.py`, which
already owns this projection's CLI surface and runs the real script as a
subprocess through its `_run_cli` helper.

- AC-0001 is carried by the two converted tests. The charset members and the
  107-character length come from this repository's own four active
  initiatives, so the fixture data is the corpus rather than invented input.
- AC-0002 is a new case; no existing test supplies a non-string.
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
source syntax, which is why AC-0002 fixes `true` as `"True"` — Python's
capitalised form, not TOML's. A non-string in a display field is an authoring
error, and showing the reader what arrived is more useful than making it look
like valid TOML. The alternative, a TOML-faithful renderer, is a new mechanism
for a case the corpus has never produced.

### Behavior & rules

For each active initiative, the projection carries `slug` (filtered), `status`
(enum-clamped), `name` (as authored, coerced to string), `milestone` (as
authored, coerced to string), `brief_queue`, and `queue_empty`. The two display
fields are the only ones this change touches.

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
  `test_initiative_display_fields_project_as_authored`, asserting AC-0001 over the
  corpus charset. `stub: true` — the red is the two existing equality
  assertions against `"workspace.toml"` failing on the authored value.
- Convert `test_initiative_display_prose_is_not_projected` into
  `test_initiative_display_prose_projects_verbatim`, keeping its unusual input
  and asserting the value arrives unchanged. This is the case that records the
  trust-model decision in the suite.
- New case for AC-0002 supplying `name = 123` and `milestone = 4.5`, asserting the
  projected values are `"123"` and `"4.5"` and that `isinstance(value, str)`.
- Update the third pinning site inside `test_cli_rich_fixture_shapes`, whose
  fixture already declares `milestone = "M1"`, to expect the authored value.
- Ten assertions invert across the three tests, not three: six equality
  assertions, plus four `assertNotIn` guards naming fixture-authored display
  prose (`ignore previous instructions`, `/outside/should-not-leak`,
  `Platform Core`, `Adopt`), each of which becomes false once the fixture's own
  values project. The `assertNotIn(str(root), ...)` repository-root leak guard
  is a different control and stays untouched.

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
- New content assertion for AC-0003 over the shipped `SKILL.md`: the rendering
  template line is present, and the redaction paragraph's distinguishing
  phrase is absent.

**Approach:**
- Restore the `Active initiatives` template line and remove the
  `Redacted display fields` paragraph.
- Return the key list's two per-field rows to describing values read from
  `workspace.toml`, and re-add `name` and `milestone` to the `initiatives`
  summary row, which currently enumerates only `slug`, `status`, `brief_queue`
  and `queue_empty`.

- Re-pin both `163` literals in
  `tools/test_local_ci_shared_test_deduplication.py` once T1's and T2's
  additions both exist, with the disposition note that file's convention
  requires.

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

**Done when:** every active initiative in this repository's `workspace.toml`
appears in `initiatives[]` carrying the `name` and `milestone` that file
assigns it, with the observed values recorded in the verification ledger as
evidence rather than as the condition.

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
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** none — the emitter, the contract and the version
  ship together, because a version claiming the new behavior without the
  emitter would be wrong.

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
- 2026-09-14 — revised from shaping review: corrected the dedup-guard
  arithmetic (F1), enumerated the ten inverting assertions and the leak guard
  that survives (F2), added the `initiatives` summary row (F3), moved the
  boolean-rendering decision out of the criterion (F4), and made T3's exit
  condition a property rather than four corpus literals (F6).
