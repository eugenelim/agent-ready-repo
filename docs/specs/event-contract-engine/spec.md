# Spec: event-contract-engine

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0018, ADR-0008
- **Contract:** none — this catalogue ships the *mechanism* (a skill + standard bundle) and authors no event contract of its own; no event-contract tree is created in this repo (mechanism only, mirroring `spec-contract-seam`).

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A team can author an **AsyncAPI 3.1.0** event contract from requirements, under
an enforced, swappable event-design standard, into `contracts/asyncapi/` — the
same authoring rigour `api-contract` gives REST. We ship `event-contract`, a
**second skill in the `contracts` pack**, built as a **standard-driven engine**
in `api-contract`'s method+data shape: the skill carries the event-design
*method*; the rules it enforces are *swappable data* across **two axes** — (A)
the event-design ruleset (Zalando ch. 19–21 as the bundled default) and (B) the
message envelope/schema format (CloudEvents 1.0.2 as the bundled default,
swappable for AWS-native / Avro / bare JSON Schema). The skill emits a single
valid AsyncAPI 3.1.0 document with CloudEvents composed into its messages. It
wires into the spec loop by filling the one stub `asyncapi` row in `core`'s
`new-spec` seam and adding a producer-vs-consumer detection refinement, so the
event path stops degrading to hand-editing. `core` gains no dependency on
`contracts` — the integration is the seam only. **This catalogue ships the
mechanism; it authors no event contract and creates no `contracts/` tree here.**

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit **source** under `packs/contracts/.apm/skills/event-contract/…` and the
  `core` seam reference `packs/core/.apm/skills/new-spec/references/contract-types.md`.
  The `contracts` skill is **not** projected (user-scope-default, excluded from
  `SELF_HOST_PACKS`); the `core` edit **is** projected. After edits run
  `make build-self` (refreshes top-level `marketplace.json` from the pack bump)
  and **both** lint surfaces — `make lint-packs` (source) and the
  projected-artifact lint (`tools/lint-agent-artifacts.py` / `pre-pr`, for the
  projected `core` edit).
- Mirror `api-contract`'s **method+data split** exactly: the method lives in
  `SKILL.md`; the standard is swappable data — a manifest naming phase-grouped
  rule files, a quality-gate checklist, a reusable envelope component, a
  `standards-authoring.md` base+delta guide, and a validated `golden-example.yaml`.
- Keep the **envelope (Axis B) swappable via a single manifest key**; CloudEvents
  1.0.2 is the bundled default *data*, never baked into the method.
- Anchor every event rule on its shared Zalando **`[#NNN]`** number, so a
  reviewer can diff `event-contract`'s rules against `api-contract`'s `events.md`
  by number (the Open-Q1 drift control).
- Travel attribution + licence in the manifest (Zalando CC-BY-4.0; CloudEvents
  source), as the REST bundle does.

### Ask first

- Re-homing, merging, or editing `api-contract`'s `events.md` (D6 keeps it put).
- Adding a protocol-binding catalogue (Kafka / AMQP / MQTT) beyond the
  structured/binary envelope content modes.
- Pre-authoring a vendor envelope bundle (AWS EventBridge-native, Avro) beyond
  documenting the manifest-key swap mechanism.

### Never do

- Make `core` **import from or depend on** `contracts` (compose-around-core
  invariant, ADR-0008 / `docs/architecture/overview.md`) — integration is the
  seam only.
- Create a `contracts/asyncapi/` tree, or any `contracts/` content, in **this**
  repo — mechanism only, exactly as `spec-contract-seam` did.
- Add a `contracts/cloudevents/` **peer contract type or row** — CloudEvents is
  an envelope composed into AsyncAPI messages, not a peer (RFC-0018 non-goal).
- **Hardcode** the envelope, the AsyncAPI version, or the CloudEvents version
  into the method (`SKILL.md`) — versions live in the manifest (data).
- Bundle a validator, or any codegen / mock / SDK generation (non-goals).
- Add a **new third-party dependency** or a **new runtime resolver** (base+delta
  is resolved by agent-reading, like the REST bundle).
- Author a contract for a **consumer-only** feature (D8).
- Put a **catalogue RFC/ADR number** in adopter-facing skill or bundle content
  (adopters don't have our RFCs); provenance lives in RFC-0018 + this spec. Real
  external standard refs (CloudEvents, AsyncAPI, Zalando) are fine.

## Testing Strategy

The bundle is **agent-read — no program parses the manifest** (the Stage-1
`pluggable-api-standards` precedent: base+delta is resolved by reading, not by
code), so there are **no TDD tasks**: standard resolution is verified by reading.
The deliverable is skill/bundle prose, one `core` markdown edit, and a mechanical
pack bump. The **single executable gate** is the golden example's validity
(`npx @asyncapi/cli validate`); everything else is structural presence or
agent-executed prose, verified the way `spec-contract-seam` verified its skill
edits.

- **Skill + bundle presence & shape** (SKILL.md phases; manifest keys incl. the
  envelope swap key; phase rule files; quality gates; golden example; evals) —
  *goal-based check.* Grep for the structural elements. *Why:* skill prose is
  verified by presence, not a unit test.
- **Golden-example validity** (the bundled AsyncAPI 3.1.0 + CloudEvents
  structured-mode document validates) — *goal-based check:*
  `npx @asyncapi/cli validate <golden-example>` exits clean, **with the validator
  output captured in the PR description** (as the RFC-0018 spike did). *Why:* a
  single objective command proves the riskiest claim (3.1.0 + CloudEvents
  compose) and guarantees the shipped example actually validates. The toolchain
  being absent is a **blocker on merge**, not a skippable note — if it can't run,
  T6 surfaces and the PR does not merge until the validation is captured.
- **Standard-swap resolution** (base+delta by reading: the Zalando-events base;
  an org delta that `extends` + `adds` Axis-A rules + optionally overrides the
  Axis-B envelope key resolves correctly) — *manual QA.* Reason through the
  worked example in `standards-authoring` against the manifest. *Why:*
  agent-executed prose; the contract is "the docs resolve the way they claim."
- **Seam behaviour** (producer/owner → author; consumer of an in-repo contract →
  reference, no authoring; consumer of an external stream → no contract; a
  non-event feature runs untouched) — *manual QA.* Reason through each outcome
  against the seam body. *Why:* agent-executed detection prose.
- **Seam wiring + projection** (filled `asyncapi` row; producer/consumer note;
  `make build-self` clean; both lint surfaces green; `marketplace.json`
  refreshed by the pack bump) — *goal-based check.* Grep + build + lint.
- **Drift-by-number quality gate** (Open Q1) — *goal-based check.* Grep the
  quality-gate checklist for the rule-number-trace item.

## Acceptance Criteria

- [ ] `packs/contracts/.apm/skills/event-contract/SKILL.md` carries the
  event-design **method as ordered phases** (model the event domain → name event
  types → choose categories → design the message envelope → design payload
  schemas → ordering/partitioning → compatibility/versioning → quality gates →
  emit AsyncAPI 3.1.0), **standard-agnostic** — no hardcoded ruleset, envelope,
  or version in the method body (D2 method).
- [ ] `references/standards-manifest-zalando-events.yaml` exists with
  `name`/`version`/`title`/`attribution` (Zalando CC-BY-4.0)/`extends: null`/
  `rule_files` (phase-grouped)/`quality_gates`/`example`/`components`, **and** the
  swappable Axis-B envelope binding as a **single reserved key
  `components.envelope`** (a member of the `components:` map, distinct from the
  reusable-schema members) naming the bundled CloudEvents component — this is the
  one key an org overrides to swap the envelope (D2 Axis A+B, D4, D5).
- [ ] Phase-grouped event rule files express the Zalando ch. 19–21 (~24) rules
  for **AsyncAPI output** — naming, categories, schema design,
  ordering/partitioning, metadata, compatibility/versioning — each rule anchored
  on its `[#NNN]` token (D2, D5 Axis A, Open Q1 anchor).
- [ ] The **CloudEvents 1.0.2 envelope** ships as a reusable component the
  manifest names, documenting **structured mode** (CE attributes as the message
  payload, business payload under `data`) and **binary mode** (CE attributes as
  message headers via an AsyncAPI message trait); default content type
  `application/cloudevents+json` (D4).
- [ ] The method **composes whatever envelope the manifest's envelope key names**
  into AsyncAPI `components.messages` — the envelope is data; an org swaps to
  AWS-native / Avro / bare JSON Schema by overriding the one key, with no method
  edit and no runtime resolver (D2 Axis B, D5 Axis E).
- [ ] `references/standards-authoring.md` (event variant) documents base+delta on
  **both axes**: a worked org delta that `extends: zalando-events`, `adds` house
  rules (Axis A), and optionally overrides the envelope key (Axis B); resolution
  is by reading; delivery reuses `adapt-to-project`'s Class 2 `.upstream`
  companion-merge — no new mechanism (D5).
- [ ] `references/golden-example.yaml` is a **complete, valid AsyncAPI 3.1.0
  document** using `channels`/`operations`/`components.messages`/
  `components.schemas` with a **CloudEvents 1.0.2 structured-mode** envelope,
  every design decision citing a `[#NNN]`, and **validates** under
  `npx @asyncapi/cli validate` **with the validator output captured in the PR
  description**; absent toolchain blocks merge (D3, RFC-0018 § Evidence spike).
- [ ] `references/standards-quality-gates-zalando-events.md` is a
  machine-checkable MUST/MUST-NOT checklist for AsyncAPI output that **includes
  the Open-Q1 drift-by-number gate** — an item asserting every rule traces to its
  shared Zalando `[#NNN]` anchor, so divergence from `api-contract`'s `events.md`
  is diffable by number (Open Q1 resolution).
- [ ] Output target is AsyncAPI **3.1.0**; the `SKILL.md` emit phase documents
  that **authored output** carries the backward spec→contract `x-spec` extension
  the seam mandates (`x-spec: [docs/specs/<feature>/]`, CONVENTIONS § 4). The
  bundled `golden-example.yaml` is a teaching artifact, **not** authored against a
  real spec, so it carries **no** `x-spec` (parity with `api-contract`'s example;
  avoids a dangling intra-repo reference) (D3).
- [ ] `evals/evals.json` for `event-contract` carries event-authoring prompts +
  assertions, in parity shape with `api-contract`'s evals.
- [ ] `core`'s `new-spec/references/contract-types.md` `asyncapi` row skill column
  is filled `event-contract` (D7).
- [ ] `contract-types.md` gains the **producer-vs-consumer detection refinement**
  (D8): produces/owns → author or modify the AsyncAPI contract; consumes an
  in-repo contract → **reference** it (set the spec's `- **Contract:**` header to
  the producer contract, add **no** `x-spec` back-pointer, point the plan's tests
  at it); consumes an external stream → **no contract**, optional upstream note.
  The `event-contract` skill restates the full three-outcome table.
- [ ] `core` imports no code from `contracts` (convention/seam coupling only) —
  verified by grep, as the compose-around-core invariant requires.
- [ ] `api-contract`'s `references/events.md` is **byte-identical** to its
  pre-PR state (D6 leaves it put).
- [ ] **Non-goals hold:** no `contracts/cloudevents/` peer row/type; no
  `contracts/asyncapi/` tree (or any `contracts/` content) created in this repo;
  no validator / codegen / mock / SDK bundled; no new dependency; no runtime
  resolver.
- [ ] `packs/contracts/pack.toml` + `.claude-plugin/plugin.json` bump
  `0.2.0 → 0.3.0`; `event-contract` is **not** projected to `.claude/skills/`
  (contracts is user-scope, excluded from `SELF_HOST_PACKS`); `make build-self`
  refreshes top-level `marketplace.json`; `make lint-packs` and the
  projected-artifact lint (for the `core` edit) pass.
- [ ] Adopter-facing skill/bundle content (`SKILL.md`, manifest, rule files,
  quality gates, golden example, evals, authoring guide) carries **no catalogue
  RFC/ADR numbers**; provenance is RFC-0018 + this spec. External standard refs
  (CloudEvents, AsyncAPI, Zalando) are unaffected.
- [ ] RFC-0018 gains an **Approver-signed `## Errata`** with two clauses: (a) the
  Migration-path correction — the `event-contract` skill is user-scope and is
  **not** self-host-projected into `.claude/skills/` (only the `core` seam edit
  projects); and (b) D7's "that is the entire `core` change" should read as **two
  parts** — fill the `asyncapi` row *and* add the D8 producer-vs-consumer
  detection note — since D8 adds detection prose to the same `core` file (no new
  mechanism, per the confirmed decision).
- [ ] `docs/specs/README.md` lists `event-contract-engine` in the active set.

## Assumptions

- Technical: `event-contract` mirrors `api-contract`'s layout — `SKILL.md` +
  `references/{standards-manifest-*.yaml, phase rule files,
  standards-quality-gates-*.md, standards-authoring.md, golden-example.yaml,
  envelope component}` + `evals/evals.json` (source:
  `packs/contracts/.apm/skills/api-contract/` tree read).
- Technical: AsyncAPI 3.1.0 + CloudEvents 1.0.2 compose into one valid document
  (source: RFC-0018 § Evidence spike — `npx @asyncapi/cli@6.0.0 validate`).
- Technical: AsyncAPI `x-spec` backward traceability is
  `x-spec: [docs/specs/<feature>/]`; forward is the spec `- **Contract:**` header
  (source: `docs/CONVENTIONS.md:336–341`).
- Technical: the `asyncapi` route + `contracts/asyncapi/` location already exist
  in `core`'s seam; only the skill column is a stub (source:
  `packs/core/.apm/skills/new-spec/references/contract-types.md:13`).
- Technical: `contracts` is **not** in `SELF_HOST_PACKS` (user-scope-default,
  deliberately excluded), so `event-contract` is **not** projected to
  `.claude/skills/`; only the `core` seam edit projects. The RFC-0018 Migration
  claim to the contrary is wrong → § Errata (source: `self_host.py:78–97`;
  `.claude/skills/` has no contract skill).
- Technical: bumping `contracts` `pack.toml` + `plugin.json` drifts top-level
  `marketplace.json` (all-packs aggregation), refreshed by `make build-self`
  (source: `self_host.py:83–97` `_aggregate_marketplace`; prior pack-bump
  experience).
- Process: RFC-0018 Accepted 2026-05-31; this is its named follow-on spec
  `docs/specs/event-contract-engine/` (source: RFC-0018 status + § Follow-on;
  commit `548822a`).
- Process: no `docs/CONVENTIONS.md` change needed — `contracts/<type>/`,
  `asyncapi`, and bidirectional traceability already landed (source:
  `docs/CONVENTIONS.md:304–353`; RFC-0018 § Follow-on).
- Process: adopter-facing skill content carries no catalogue RFC numbers,
  enforced by `lint-packs`/`lint-seeds`; provenance goes in spec/RFC (source:
  `spec-contract-seam/spec.md` Boundaries; repo memory).
- Decision: the D8 producer-vs-consumer rule lives as a note on the `asyncapi`
  row in `core`'s `contract-types.md` (detection is the seam's job) **plus** the
  full three-outcome table in the `event-contract` skill — an honest second
  `core` edit, but no new mechanism (source: user confirmation 2026-05-31).
- Decision: no new ADR — RFC-0018 + this spec are the record; ADR-0008 already
  covers "other types plug in as new rows + roster entries" (source: user
  confirmation 2026-05-31).
- Decision: Open Q1 resolved by anchoring both rule copies on `[#NNN]` + a
  drift-by-number quality-gate item; no cross-skill file dependency (source: user
  confirmation 2026-05-31; RFC-0018 Open Q1 default).
- Decision: ship `golden-example.yaml` + `evals.json` for parity with
  `api-contract` (source: user confirmation 2026-05-31).
- Decision: record the Migration-path correction as an Approver-signed RFC-0018
  `## Errata` line (source: user confirmation 2026-05-31; frozen-RFC-divergence
  governance rule).
