# Plan: Discovery-producer traceability markers

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn.

## Approach

Five prompt-only markdown producers each gain the exact bold-body marker its
node type's lint recognizer reads. The shape of the change is identical per
producer: add one additive, comment-annotated marker line to the skill's artifact
**template** (the schema the skill ships), and add a one-line instruction in the
SKILL.md procedure step that writes the artifact so the agent fills it. No engine,
no logic, no change to the lint or CONVENTIONS. The riskiest part is getting the
on-disk form exactly right — the lint matches `**Label:**` (bold body), not a
frontmatter key — so each task's verification builds a fixture artifact in the
form the edited template emits and runs the lint as an oracle.

The declined-pattern register: tempted to (a) repurpose the screen brief's
frontmatter `type: screen-flow-brief` into `screen-brief` — declining, it is a
documented brief-internal non-anchor; a separate bold-body `Type:` marker is
correct and non-colliding. (b) "fix" CONVENTIONS § 4's "frontmatter `type:`"
wording to say "bold-body field" — declining, the task scopes me to producer
skills and forbids doctrine edits; the drift is real but belongs to its owner (I
surface it). (c) add a Kind/Level engine or validation to the intent skills —
declining, prompt-only is the charter rule.

## Constraints

RFC-0053 (AC36 scopes discovery-loop as the *consumer*; DRIFT-G added the § 4
grammar), RFC-0048 note 04 (the ladder tags outcome/opportunity *kinds* across
levels, so `capability` is a Level while outcome/opportunity are Kinds). Charter
Principle 3 (prompt-only — no engine behind a skill). `frame-domain` is the marker
precedent.

## Construction tests

**Integration tests:** one fixture per producer + one wired-chain fixture, all run
through `lint-traceability.py --root <fixture>` (see per-task Tests). The lint's
own `test-lint-traceability.py` is the regression floor and must stay green
unchanged.
**Manual verification:** read the lint stdout to confirm the expected node ids
appear and no false `ORPHAN` is attributable to a missing marker.

## Tasks

### T1: screen brief emits `**Type:** screen-brief`

**Depends on:** none

**Tests:**
- Fixture: write `docs/product/screens/home.md` (flat — where the lint's default
  base globs) carrying a bold-body `- **Type:** screen-brief` line (as the edited
  template now shows). Run the lint; assert stdout names the exact id `screen:home`.
  Verifies AC1 (the marker *form*; the nested-path gap is the surfaced follow-up,
  not this fixture's claim).

**Approach:**
- Add a bold-body `- **Type:** screen-brief` marker to
  `map-screen-flow/assets/screen-brief-template.md` (in `## Place in the whole`,
  the traceability section), with an HTML-comment line above it explaining it is
  the structural-orphan lint's chain marker. Leave frontmatter `type: screen-flow-brief`.
- Add a half-sentence to `map-screen-flow/SKILL.md` step 5 so the per-screen brief
  carries the marker.

**Done when:** the lint recognizes a fixture screen brief as `screen:<stem>`.

### T2: journey emits `**Action:** <slug>` per frontstage action

**Depends on:** none

**Tests:**
- Fixture: write `docs/product/journeys/j.md` carrying `- **Action:** checkout`.
  Run the lint; assert stdout names `action:checkout`. Verifies AC2.

**Approach:**
- Add a `## Frontstage actions` markers block to
  `map-customer-journey/assets/journey-map-template.md` — one
  `- **Action:** <action-slug>` per distinct frontstage action, comment-annotated as
  the traceability marker the lint reads as an `action` node.
- Add a half-sentence to `map-customer-journey/SKILL.md` step 5 (the four-rows
  step) so the markers are emitted.

**Done when:** the lint recognizes a fixture journey's `action:<slug>` node(s).

### T3: blueprint emits `**Service:** <slug>` per backstage service

**Depends on:** none

**Tests:**
- Fixture: write `docs/product/blueprints/bp.md` carrying `- **Service:** payments`.
  Run the lint; assert stdout names `service:payments`. Verifies AC3.

**Approach:**
- Add a `## Service markers` block (or fold into `## Named backstage services`) to
  `blueprint-service/assets/service-blueprint-template.md` — one
  `- **Service:** <service-slug>` per backstage service, comment-annotated.
- Add a half-sentence to `blueprint-service/SKILL.md` step 4/6 so the markers are
  emitted.

**Done when:** the lint recognizes a fixture blueprint's `service:<slug>` node(s).

### T4: intent emits `**Kind:** outcome|opportunity`

**Depends on:** none

**Tests:**
- Fixture: write three intents under `docs/product/intents/` carrying
  `- **Kind:** outcome`, `- **Kind:** opportunity`, and `- **Level:** capability`.
  Run the lint; assert stdout names `outcome:`, `opportunity:`, `capability:`
  nodes. Verifies AC4.

**Approach:**
- Add an additive `- **Kind:** <outcome | opportunity>` field to
  `frame-intent/assets/intent-template.md`, directly beneath `Level:`,
  comment-annotated as the discovery-traceability chain rung (distinct from
  `Level:`, the altitude; `Level: capability` places the capability rung).
- Add a half-sentence to `frame-intent/SKILL.md` (step 3, picking the altitude, or
  step 7, hand-off) tying the Kind tag to the chain.

**Done when:** the lint recognizes fixture intents by Kind/Level.

### T5: `decompose-intent` carries the Kind/Level marker on child intents

**Depends on:** T4

**Tests:**
- Own fixture: write an intent in the exact form the edited `decompose-intent` step
  describes (a child intent carrying `- **Kind:** opportunity` + `- **Parent intent:**`).
  Run the lint; assert the `opportunity:<slug>` id appears. Verifies AC5
  independently of T6 (so a dropped instruction fails a check).

**Approach:**
- Update `decompose-intent/SKILL.md` step 1 (produce child intents) so each child
  carries the `Kind:` (and `Level:`) marker alongside the existing `Parent intent:`
  back-link.

**Done when:** the step names the Kind/Level marker on emitted child intents.

### T6: wired-chain fixture recognizes every node with no false orphan

**Depends on:** T1-T5

**Tests:**
- Build a fully-wired fixture: intent ladder (outcome→opportunity→capability via
  `Parent intent:`) → screen (`Type:`) → journey action → blueprint service → a spec
  parented via `Discovery:`, in the exact marker forms the edited templates emit.
  Run the lint; assert each producer node appears **by its exact id**
  (`outcome:…`, `opportunity:…`, `capability:…`, `screen:…`, `action:…`,
  `service:…`) and that no `ORPHAN`/`DANGLING` fires on the wired nodes. Verifies AC6.
- Run `test-lint-traceability.py`; assert it passes unchanged. Verifies AC7.

**Approach:**
- Mirror the lint's own `case_container_and_file_recognition` structure with the
  template-emitted marker text.

**Done when:** all producer nodes recognized; the lint self-test is green.

### T7: version bump + marketplace.json + changelog + backlog close

**Depends on:** T1-T6

**Tests:**
- `make build-self` regenerates `marketplace.json` cleanly (no other drift).
  Verifies AC8.
- `lint-spec-status.py` clean; backlog anchor resolves. Verifies AC9.

**Approach:**
- Bump `experience` 0.2.0 → 0.3.0 and `product-engineering` 0.9.0 → 0.10.0 — the
  **top-level pack `version`** in `pack.toml` (line 3, NOT the `[contract] version`)
  and the `version` in `.claude-plugin/plugin.json`; run `make build-self` to
  regenerate `marketplace.json` (no other drift).
- Add a `docs/product/changelog.md` `[Unreleased]` entry.
- Close `docs/backlog.md#discovery-loop-type-marker-producers` (mark resolved,
  retain the anchor — the discovery-loop spec's AC36 links it). Add a new backlog
  follow-up for the screen-glob↔nested-path gap (the surfaced out-of-scope item).

**Done when:** versions bumped, marketplace.json regenerated, changelog + backlog updated.

## Risks

- Path-layout mismatch (out of scope): `recognize_screens` globs `screens/*.md`
  non-recursively, but per-screen briefs land at `screens/<slug>/<screen>.md`
  (nested). Emitting the marker is necessary but not sufficient for the default
  base to find a nested brief — adopters set the base via `agentbundle-layout.toml`,
  and the marker-not-path contract is the lint's stated posture. Surfaced as a
  follow-up, not fixed here (the task scopes me to the marker).

## Changelog

- 2026-06-30: initial plan.
