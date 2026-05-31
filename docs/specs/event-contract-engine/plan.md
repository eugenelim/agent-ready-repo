# Plan: event-contract-engine

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is **almost entirely additive content authoring** in the shape
`api-contract` already proves. We build the standard bundle bottom-up — manifest
skeleton first (it names every other file), then the Zalando-events rule files,
the CloudEvents envelope component, and the quality gates — then write the
`SKILL.md` method that reads them, then the validated `golden-example.yaml` and
`evals.json`. Only after the skill exists do we touch `core` (fill the seam row +
add the D8 producer/consumer refinement) and finalize (pack bump → `build-self`
refreshes `marketplace.json`, RFC-0018 Errata, specs README, adopter-clean
scrub). The riskiest part is the **golden example** — it is the single objective
gate that the AsyncAPI 3.1.0 + CloudEvents composition the whole bundle assumes
actually validates; the RFC's spike de-risked the *pattern*, but the shipped
example must validate on its own. Files moved: a new skill directory under
`packs/contracts/.apm/skills/event-contract/`; one `core` reference edit; the
`contracts` pack-version files; `marketplace.json` (regenerated);
`docs/rfc/0018-…md` (Errata); `docs/specs/README.md`. One PR (additive,
RFC-0004-coherent).

## Constraints

- **RFC-0018** (Accepted 2026-05-31) — D1–D8 are the design; this plan
  implements them. Open Q1 resolved per its recommended default.
- **ADR-0008** — `core` composes around `contracts`; new contract types plug in
  as `contracts/<type>/` rows + roster entries with no `core` code dependency.
- **RFC-0017 D4** — the deferral this work closes; its non-goal pins Zalando's
  event rules inside `api-contract`'s OpenAPI bundle (→ D6, `events.md` untouched).
- **CONVENTIONS § 4 Contracts** — `contracts/asyncapi/` location, `x-spec`
  backward traceability, per-domain naming/versioning. No CONVENTIONS change.

## Construction tests

Per-task checks live under each task. Cross-cutting:

**Integration tests:** none beyond per-task checks — no code ships.
**Manual verification:**
- Walk the `standards-authoring` worked example end-to-end: confirm an org delta
  that `extends: zalando-events` + `adds` two rules + overrides the envelope key
  resolves to the stated effective standard by reading alone (no resolver).
- Walk the seam's three producer/consumer outcomes (D8) and the non-event path
  against the updated `contract-types.md` + `SKILL.md`.

## Tasks

### T1: Standard-bundle skeleton — manifest + authoring guide

**Depends on:** none

**Tests:**
- `references/standards-manifest-zalando-events.yaml` parses as YAML and carries
  `name: zalando-events`, `version`, `title`, `attribution` (Zalando, CC-BY-4.0),
  `extends: null`, `rule_files` (phase keys), `quality_gates`, `example`,
  `components`, **and the reserved `components.envelope` key** naming the
  CloudEvents component (AC2).
- `references/standards-authoring.md` documents base+delta on **both axes** with
  a worked org delta (`extends: zalando-events`, `adds:`, envelope-key override)
  and states resolution is by reading + Class 2 `.upstream` delivery (AC6).
- Grep: no catalogue RFC/ADR number in either file (AC17).

**Approach:**
- Copy the structure of `api-contract/references/standards-manifest-zalando.yaml`
  and `standards-authoring.md`; retarget to events; add the Axis-B envelope as the
  reserved key **`components.envelope`** (a member of the `components:` map,
  distinct from the reusable-schema members like `money`/`problem`) pointing at
  the CloudEvents component file T3 will create. This is the single key an org
  overrides to swap the envelope.
- Phase keys for `rule_files`: `naming`, `categories`, `schema_design`,
  `ordering_and_partitioning`, `metadata`, `compatibility`.

**Done when:** the manifest parses, names all phase rule files + the envelope key,
and `standards-authoring.md` shows the two-axis worked delta; grep finds no
catalogue RFC number. (goal-based)

**Touches:** packs/contracts/.apm/skills/event-contract/references/standards-manifest-zalando-events.yaml, packs/contracts/.apm/skills/event-contract/references/standards-authoring.md

### T2: Zalando-events phase rule files (Axis A)

**Depends on:** T1

**Tests:**
- One markdown rule file per `rule_files` phase key from T1, each present and
  non-empty (AC3).
- Every Zalando ch. 19–21 rule restated for AsyncAPI output is anchored on its
  `[#NNN]` token (grep: each rule heading carries a `[#NNN]`) (AC3, Open Q1).
- The ~24 rules from `api-contract/references/events.md` are all represented by
  number (diff-by-number: every `[#NNN]` in `events.md` ch. 19–21 appears in the
  event-contract rule files) (Open Q1 anchor).

**Approach:**
- Source the rule set from `api-contract/references/events.md` (ch. 19–21); do
  **not** edit that file (AC14). Restate each rule in **AsyncAPI 3.1** terms
  (channels/operations/messages/schemas) rather than OpenAPI-Schema-Object terms.
- Group (numbers below are **illustrative** — the authoritative set is the
  by-number diff against `events.md` ch. 19–21, not this partial list): naming
  (`[#213]` …), categories (`[#198]`/`#201`/`#202` …), schema design
  (`[#196]`/`#199`/`#200`/`#205`/`#210` …), ordering/partitioning
  (`[#203]`/`#242`/`#204` …), metadata (`[#211]`/`#247` …), compatibility
  (`[#209]`/`#245`/`#246` …).

**Done when:** every phase file exists, each rule carries its `[#NNN]`, and a
by-number diff against `events.md` ch. 19–21 shows full coverage. (goal-based)

**Touches:** packs/contracts/.apm/skills/event-contract/references/*.md

### T3: CloudEvents 1.0.2 envelope component (Axis B)

**Depends on:** T1

**Tests:**
- The envelope component file the manifest's envelope key names exists and is
  valid YAML (AC4).
- It documents **structured mode** (CE attributes as payload schema, business
  payload under `data`) and **binary mode** (CE attributes as message headers via
  a message trait), with default content type `application/cloudevents+json`
  (AC4).
- It carries CloudEvents 1.0.2 attribution; no catalogue RFC number (AC17).

**Approach:**
- Author a reusable AsyncAPI-composable schema/trait for the CloudEvents 1.0.2
  context attributes (`specversion`, `id`, `source`, `type`, `time`,
  `datacontenttype`, `subject`, `data`, …), modelled for both content modes.
- Mirror the component-file convention of `api-contract/references/money-1.0.0.yaml`
  / `problem-1.0.1.yaml` (versioned filename).

**Done when:** the component file is valid YAML, covers both content modes, and
is the file the manifest envelope key resolves to. (goal-based)

**Touches:** packs/contracts/.apm/skills/event-contract/references/cloudevents-1.0.2.yaml

### T4: Quality-gate checklist + Open-Q1 drift-by-number gate

**Depends on:** T2

**Tests:**
- `references/standards-quality-gates-zalando-events.md` exists with
  machine-checkable MUST/MUST-NOT items grouped for AsyncAPI output (structural
  validity, naming, categories, schema design, ordering, metadata, compatibility)
  (AC8).
- The checklist includes the **drift-by-number** item: every enforced rule traces
  to its shared Zalando `[#NNN]` anchor so divergence from `api-contract`'s
  `events.md` is diffable by number (AC8, Open Q1).
- The manifest's `quality_gates` key resolves to this file (AC2).

**Approach:**
- Model on `api-contract/references/standards-quality-gates-zalando.md`; retarget
  the gate items to AsyncAPI structures and the event rules from T2.

**Done when:** the checklist exists, the manifest points at it, and the
drift-by-number item is present. (goal-based)

**Touches:** packs/contracts/.apm/skills/event-contract/references/standards-quality-gates-zalando-events.md

### T5: `SKILL.md` — the standard-agnostic event-design method

**Depends on:** T1, T3

**Tests:**
- `SKILL.md` has frontmatter (`name: event-contract`, a `description`) and the
  ordered phases: model domain → name types → categories → design envelope →
  payload schemas → ordering/partitioning → compatibility/versioning → quality
  gates → emit AsyncAPI 3.1.0 (AC1).
- Negative greps prove standard-agnosticism: the method body does **not**
  hardcode the AsyncAPI version, the CloudEvents version, or specific Zalando
  rule numbers as rails — it directs the reader to the active manifest (AC1, AC5).
- The "active standard" section documents reading the manifest, loading phase
  rule files, resolving base+delta, and **composing whatever envelope the
  manifest names** into `components.messages` (AC5).
- The skill restates the D8 three-outcome producer/consumer table (AC11 cross-ref).
- The emit phase documents that **authored output** carries the `x-spec`
  backward-traceability extension (`x-spec: [docs/specs/<feature>/]`) — distinct
  from the bundled golden example, which carries none (AC9).
- No catalogue RFC/ADR number anywhere in the file (AC17).

**Approach:**
- Mirror `api-contract/SKILL.md`'s "Standard-driven" framing, "active standard"
  resolution section, phase structure, design-discipline + rationalizations
  table, quality-gates pointer, and reference-file index — retargeted to events
  and AsyncAPI output.

**Done when:** all phase headings + the active-standard section + the envelope-
composition prose + the D8 table are present and the negative greps pass.
(goal-based)

**Touches:** packs/contracts/.apm/skills/event-contract/SKILL.md

### T6: Validated golden example — AsyncAPI 3.1.0 + CloudEvents structured mode

**Depends on:** T2, T3, T5

**Tests:**
- `references/golden-example.yaml` is a complete AsyncAPI 3.1.0 document using
  `channels`/`operations`/`components.messages`/`components.schemas` with a
  CloudEvents 1.0.2 **structured-mode** envelope (business payload under `data`)
  (AC7).
- Every design decision cites a `[#NNN]` (grep) (AC7).
- It carries **no** `x-spec` extension — it is a teaching artifact, not authored
  against a real spec; the `x-spec` shape is documented in `SKILL.md`'s emit phase
  (T5), not demonstrated here, so no dangling intra-repo reference ships (AC9).
- **It validates:** `npx @asyncapi/cli validate references/golden-example.yaml`
  exits clean (AC7). If the toolchain is unavailable, surface — do not mark green.

**Approach:**
- Author a small, realistic domain (e.g. order events) reflecting the T2 rules
  and the T3 envelope; cite rules inline; run the validator and paste its output
  into the PR description.

**Done when:** the validator reports the document valid **and its output is
captured in the PR description**, the `[#NNN]` grep passes, and the `x-spec`
*absence* grep passes (the example carries none). A missing toolchain blocks
merge (surface, don't mark green). (goal-based)

**Touches:** packs/contracts/.apm/skills/event-contract/references/golden-example.yaml

### T7: `evals.json` for `event-contract`

**Depends on:** T5

**Tests:**
- `evals/evals.json` is valid JSON with `skill_name: event-contract` and an
  `evals` array; each eval has `prompt`, `expected_output`, and `assertions`
  targeting AsyncAPI 3.1.0 + CloudEvents + Zalando-event-rule outcomes (AC10).

**Approach:**
- Mirror `api-contract/evals/evals.json`; write event-authoring prompts (a
  producer event stream; a data-change event with ordering) and assert on
  AsyncAPI validity, `[#NNN]`-rule conformance, and CloudEvents envelope shape.

**Done when:** the file is valid JSON in parity shape with the assertions above.
(goal-based)

**Touches:** packs/contracts/.apm/skills/event-contract/evals/evals.json

### T8: Seam wiring — fill the `asyncapi` row + D8 producer/consumer refinement

**Depends on:** none — the row value is the fixed string `event-contract` (RFC
D-decision 2), and the D8 note is self-contained detection prose; neither needs
`SKILL.md` (T5) to exist. (The skill-side restatement of the D8 table is T5's;
this task is the `core`-side note only.)

**Tests:**
- `core`'s `new-spec/references/contract-types.md` `asyncapi` row skill column is
  `event-contract` (was the `—` stub) (AC11).
- The file gains the producer-vs-consumer refinement: produces/owns → author;
  consumes in-repo contract → reference (set `Contract:` header, no `x-spec`
  back-pointer, point plan tests at it); consumes external → no contract (AC12).
- Grep proves `core` still imports no code from `contracts` (AC13).
- Manual QA: reason the three outcomes + a non-event feature against the updated
  text — each routes correctly (AC12 behaviour).

**Approach:**
- Edit the one table row; append a short "events: produce vs consume" note (or a
  compact 3-row table) below the existing "How the seam uses it" section. Keep
  the refinement detection-only — no new core mechanism.

**Done when:** the row is filled, the D8 note is present, the import grep is
clean, and the manual walk-through routes all four cases correctly.
(goal-based + manual QA)

**Touches:** packs/core/.apm/skills/new-spec/references/contract-types.md

### T9: Finalize — pack bump, projection, RFC Errata, README, adopter-clean

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T8

**Tests:**
- `packs/contracts/pack.toml` + `.claude-plugin/plugin.json` both read
  `0.3.0` (AC16).
- `make build-self` runs clean and refreshes top-level `marketplace.json` to the
  new contracts version; `event-contract` is **absent** from `.claude/skills/`
  (contracts not in `SELF_HOST_PACKS`) (AC16).
- `make lint-packs` and the projected-artifact lint (`tools/lint-agent-artifacts.py`
  / `pre-pr`, for the projected `core` edit) pass (AC16).
- RFC-0018 has an Approver-signed `## Errata` with **both** clauses: the
  not-self-host-projected correction, and D7's "entire core change" reconciled to
  row-fill **plus** the D8 detection note (AC18).
- `docs/specs/README.md` lists `event-contract-engine` active (the README
  Acceptance Criterion).
- Repo-wide grep: no catalogue RFC/ADR number under
  `packs/contracts/.apm/skills/event-contract/` (AC17).

**Approach:**
- Bump both version files; run `make build-self`; verify `git status` shows the
  expected `marketplace.json` regen and no projected `event-contract`; add the
  RFC Errata; add the README row; run both lint surfaces; run the work-loop's
  `scripts/lint-spec-status.py` for doc-drift invariants.

**Done when:** versions bumped, `build-self` clean with `marketplace.json`
refreshed and no projected skill, both lints green, two-clause Errata + README
present.
(goal-based)

**Touches:** packs/contracts/pack.toml, packs/contracts/.claude-plugin/plugin.json, marketplace.json, docs/rfc/0018-event-asyncapi-authoring-engine.md, docs/specs/README.md

## Rollout

Additive and reversible. The skill ships in the `contracts` pack (user-scope
default); adopters who install `contracts` get `event-contract` alongside
`api-contract`. Existing `api-contract` invocations are untouched. The `core`
seam upgrade is graceful both ways: the row delegates to `event-contract` when
`contracts` is installed and falls back to direct-edit + note when it isn't
(ADR-0008 two-layer discovery). Nothing in this repo authors a contract, so
there is no runtime behaviour change here — only the projected `core` seam text
and the regenerated `marketplace.json`.

## Risks

- **Golden example fails validation** (toolchain or composition surprise). The
  RFC spike validated the pattern; if the shipped example fails, fix the example
  — never weaken the gate. If `npx`/Node is unavailable in the impl environment,
  surface rather than marking T6 green.
- **`build-self` reverts a projection-only edit** or drifts unexpectedly — check
  `git status` after `build-self` (repo memory: build-self undoes projection-only
  edits). The only expected regen is `marketplace.json`; anything else is a flag.
- **Accidental `events.md` edit** breaks D6 byte-identical guarantee — T2 sources
  from it read-only; verify with `git diff -- …/events.md` (empty) before PR.
- **Rule restatement drifts from `events.md`** over time (Open Q1) — mitigated by
  the by-number anchor + the drift-by-number quality-gate item (T4); not a
  one-time check but a standing gate.

## Changelog

- 2026-05-31: initial plan (RFC-0018 follow-on; Open Q1 resolved per its default).
