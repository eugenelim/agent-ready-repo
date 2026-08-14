# Plan: m6-live-demo-guide

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as the implementation learns. Substantial
> changes are recorded in the changelog.

## Approach

Author one facilitator-facing Core how-to with a common 4/7/6/9/4-minute
presentation frame and three distinct canonical journey scripts. Implement the
technical script as Core direct-to-`new-spec`, the enterprise script as Core
`receive-brief`-to-`new-spec`, and the non-technical script as Product
Engineering `frame-intent`/`de-risk-intent`/`decompose-intent` handing a leaf
brief to Core. Pin the pack, scope, entry skill, artifacts, actual human
controls, and exclusions in a focused source test. Validate each script with an
independent cold walkthrough, then register and publish the guide. Use
`author-product-docs` during execution because the deliverable is adopter-facing
documentation.

## Constraints

- RFC-0064 P5 requires at least three representative team types, a pre-flight
  checklist, the adopting organization's repository, shaping → brief → spec
  narration, and a run no longer than 30 minutes.
- Adopter-persona research requires participant-verifiable first tasks, explicit
  human controls, peer-champion facilitation, distinct trust barriers, and value
  framed at a shareable artifact.
- Canonical pack contracts fix the routing: Core is repo-only; Product
  Engineering defaults to user scope and hands app-scale feature leaves to
  Core; `author-brief` writes work intake and is excluded from this demo.
- `governance-extras`, `product-strategy`, and Experience Design are not
  baseline workflow owners. The guide may identify them only as conditional
  producers of different artifacts or optional evidence.
- The mid-market enterprise path remains unresolved. The guide names that gap
  and makes no reliability claim for it.
- `guides/AGENTS.md` governs frontmatter, publication, generated navigation, and
  validation. The guide is a how-to, not a tutorial or explanation.
- The plan has no task or workspace dependency on
  `rendered-site-link-debt`; it does not modify `ini-008`, `workspace.toml`, or
  any other work-intake artifact.

## Construction tests

**Integration tests:** `python3 tools/validate_guides.py` validates frontmatter
and routes; `python3 tools/check-guide-index.py` preserves guide-home coverage;
`python3 tools/test_live_demo_guide.py` checks stage arithmetic, the exact
Core/Core/Product Engineering routing, install scopes, skill sequences,
pack-specific outputs and decisions, explicit exclusions, and receipt fields;
site construction checks confirm generated navigation and local-link closure.

**Manual verification:** a facilitator who did not author the guide performs
one cold walkthrough per track in an isolated disposable repo scenario. Each
record captures the exact prompt, installed packs/scopes, input evidence, stage
times, real skill verdicts, changed paths/statuses, provenance links,
track-specific proof, one recovery probe, external-mutation statement,
recipient, and safe-stop or success outcome. A run that exceeds 30 minutes or
cannot reach its required artifact is a failed walkthrough, not an edited
timestamp.

## Design (LLD)

### Design decisions

- The guide lives in Core because it is a cross-journey adoption runbook, two
  tracks are wholly Core-owned, and the third explicitly hands off to Core.
  Traces to: AC1, AC3, AC6–AC10.
- The five shared timeboxes are presentation beats, not shared workflow states.
  This retains one teachable runbook without inventing Product Engineering
  gates inside Core. Traces to: AC2, AC5, AC9.
- The technical path omits a brief because Core documents `new-spec` as the
  direct single-feature entry. The enterprise path begins from an existing
  structured brief because `receive-brief` owns external multi-feature handoff.
  Traces to: AC6–AC7.
- The non-technical path begins in user-scoped Product Engineering at feature
  level and app scale, then crosses the documented leaf-brief seam into
  repo-scoped Core. It does not pretend to compress the full 60–120 minute
  `discovery-loop` into the demo. Traces to: AC8–AC9.
- `author-brief` is excluded because queueing its result would violate the
  no-work-intake boundary. `governance-extras` and `product-strategy` create
  different-altitude artifacts, so neither is added for persona flavor.
  Traces to: AC4, AC10.
- Every path stops with one Draft spec/plan pair. Formal approvals and
  implementation are next actions, not stage props. Traces to: AC11, AC13–AC14.

### Component / module decomposition

`guides/core/how-to/run-a-live-demo.md` contains:

1. `Use this when`, `Prerequisites`, and `Result` entry contract.
2. A choose-your-track map with owning journey, install scope, input shape,
   exact skill sequence, intermediate artifacts, end state, and wrong-pack
   exclusions.
3. The 4/7/6/9/4-minute presentation frame. Each beat uses `Say`, `Reads`,
   `Writes`, `You see`, `You decide`, `Narrate`, and `Stop if`.
4. A Core direct-feature script proving baseline → Draft AC → verification
   command → owner-file trace without creating a brief.
5. A Core structured-handoff script proving policy/control → Ready brief →
   chosen slice → Draft AC/plan evidence trace without queue registration.
6. A Product Engineering-to-Core script proving source correction → intent →
   assumption verdict/validation hook → leaf brief → Draft spec provenance.
7. Formal-gate separation, pack-aware recovery, completion receipt, canonical
   workflow links, and the likely next request.

`guides/core/README.md` adds one How-to entry. Generated navigation remains
owned by `tools/build-site.py`; no sidebar file is hand-edited.
`tools/test_live_demo_guide.py` reads the guide source and asserts the
contract-bearing headings, mappings, prompts, time values, controls, artifacts,
and exclusions without depending on rendered output. Traces to: AC1–AC17.

### State & control flow

Pre-flight starts the timer only after the selected packs/scopes and read/write
card pass. The technical path enters `new-spec`, waits for its assumption and
boundary confirmation, then drafts. The enterprise path enters
`receive-brief`, waits for missing-field resolution and decomposition
confirmation, marks the unqueued brief Ready only when its DoR passes, and
chains one slice through `new-spec`. The non-technical path waits at
`frame-intent` G0, records `de-risk-intent`'s predeclared kill condition and
survive/kill verdict, confirms `decompose-intent`'s leaf, then crosses to Core
`receive-brief` and `new-spec`. A killed non-technical assumption stops before
decomposition. All paths verify and receipt their artifacts, then stop before
formal approvals, queue mutation, or `work-loop` execution. Traces to: AC2–AC9,
AC11, AC13–AC14.

### Behavior & rules

- Track selection changes the journey, scope, entry artifact, invoked skills,
  decisions, intermediate artifacts, proof, narration, recovery, and recipient.
- The repository and problem belong to the adopting organization.
- Each decision callout uses the selected skill's own vocabulary and waits.
- A successful demo requires the complete canonical path, verified artifacts,
  and a named recipient within the timebox.
- No external mutation or work-intake registration is the default and required
  baseline.
- Mid-market applicability remains unknown.

Traces to: AC3–AC15.

### Failure, edge cases & resilience

The guide stops for missing packs/scopes, unsafe input, no suitable familiar
problem, dirty or unintended write scope, declined decisions, timer expiry,
and output participants cannot verify. Track-specific stops cover a technical
request that is not feature-sized or reproducible, an enterprise brief whose
control owner or Ready fields are missing, and a non-technical intent whose
assumption is killed or whose synthesis is generic. The receipt distinguishes a
safe stop from success. Traces to: AC4, AC6–AC8, AC13–AC15.

### Quality attributes (NFRs)

The guide is executable within 30 minutes, understandable by a role-proximate
facilitator without pack-routing improvisation, honest about mutations and
unknowns, accessible through generated navigation, and maintainable through
links to canonical procedures. Traces to: AC1–AC18.

### Dependencies & integration

The guide consumes already-shipped Core and Product Engineering capabilities
and their documentation. It adds no runtime dependency, pack, skill, external
service, cross-spec sequencing edge, or work-intake write. Traces to: AC3–AC4,
AC10, AC16–AC17.

## Tasks

### T1: The guide establishes the pack map and presentation frame

**Depends on:** none

**Touches:** guides/core/how-to/run-a-live-demo.md, tools/test_live_demo_guide.py

**Verification mode:** goal-based check + visual/manual QA

**Stub:** no stub (goal-based and manual QA)

**Tests:**

- The focused test parses the five beat labels and exact minute values and
  asserts their total is 30. Traces to: AC2.
- The focused test pins Technical = Core/repo/`new-spec`, Enterprise =
  Core/repo/`receive-brief` → `new-spec`, and Non-technical = Product
  Engineering/user → Core/repo with the full required skill sequence. Traces
  to: AC3, AC6–AC10.
- It requires `Say`, `Reads`, `Writes`, `You see`, `You decide`, `Narrate`, and
  `Stop if` for every beat plus the pre-flight and receipt fields. Traces to:
  AC4–AC5, AC13–AC14.

**Approach:**

- Use `author-product-docs` to draft the how-to at the canonical Core path.
- Put the copyable track-selection request and expected result in the first 120
  words, followed by the write and external-mutation boundary.
- Write the map, wrong-pack exclusions, five-beat skeleton, shared recovery,
  and receipt before track detail.
- Link to canonical journey and how-to depth; do not reproduce full skills.

**Done when:** a cold reader can choose the right pack path from the input
shape and the focused test rejects any collapsed one-flow presentation.

### T2: The technical script demonstrates Core's direct-feature path

**Depends on:** T1

**Touches:** guides/core/how-to/run-a-live-demo.md, tools/test_live_demo_guide.py

**Verification mode:** goal-based check + visual/manual QA

**Stub:** no stub (goal-based and manual QA)

**Tests:**

- The focused test pins the technical prompt, Core repo scope, direct
  `new-spec` entry, explicit no-brief result, actual assumption/boundary
  decision, command-to-AC and file-to-task proof, recipient, and recovery.
  Traces to: AC6, AC9, AC11–AC14.
- Manual QA confirms the example is one independently testable feature and its
  success command is trusted. Traces to: AC6.

**Approach:**

- Show one real baseline and its trace to the Draft spec and plan.
- Explain why feature sizing permits direct entry without inventing a brief or
  Product Engineering gates.
- Stop at ready-to-circulate Drafts.

**Done when:** the script needs no invented scenario, gate, proof, or recipient.

### T3: The enterprise script demonstrates Core's structured-handoff path

**Depends on:** T1

**Touches:** guides/core/how-to/run-a-live-demo.md, tools/test_live_demo_guide.py

**Verification mode:** goal-based check + visual/manual QA

**Stub:** no stub (goal-based and manual QA)

**Tests:**

- The focused test requires an existing unqueued structured brief,
  `receive-brief`, decomposition confirmation, one selected `new-spec` slice,
  policy/control evidence, owner, success/stop/rollback measures, brief/spec
  provenance, governed recipient, safe stops, and mid-market disclaimer.
  Traces to: AC7, AC9–AC15.
- Manual QA confirms neither `author-brief`, `governance-extras`, unsupported
  compliance/ROI claims, nor a `workspace.toml` write appears. Traces to: AC4,
  AC7, AC10, AC15.

**Approach:**

- Start from a prepared sanitized Draft brief so the demo exercises handoff,
  not work intake.
- Trace claims only to supplied policy/control sources and make the accountable
  owner and residual-risk recipient explicit.
- Scaffold only the selected slice and leave remaining decomposition visible in
  the brief.

**Done when:** the script produces a defensible governed-pilot handoff through
Core without persona-driven pack substitution.

### T4: The non-technical script demonstrates Product Engineering into Core

**Depends on:** T1

**Touches:** guides/core/how-to/run-a-live-demo.md, tools/test_live_demo_guide.py

**Verification mode:** goal-based check + visual/manual QA

**Stub:** no stub (goal-based and manual QA)

**Tests:**

- The focused test pins user-scope Product Engineering, repo-scope Core,
  feature/app-scale intake, the exact `frame-intent` → `de-risk-intent` →
  `decompose-intent` → `receive-brief` → `new-spec` chain, G0, kill condition,
  validation hook, leaf brief, its Outcome/Appetite/Rabbit-hole/one-row-Spec-map
  Ready gate, provenance, participant correction, human-authorship narration,
  recipient, and recovery. Traces to: AC8–AC14.
- The test rejects claims that the run executes full `discovery-loop` G1.5/G2
  or uses Product Strategy as the workflow owner. Traces to: AC9–AC10.
- Manual QA confirms one participant correction propagates through the intent
  chain, desk grounding stays `to-validate`, and Core does not mark the leaf
  brief `Ready` until all four Ready-gate fields are visible. Traces to: AC8.

**Approach:**

- Use familiar outcome language before naming pack primitives.
- Keep the intent at feature level/app scale so decomposition reaches one Core
  brief rather than opening a longer discovery tree.
- Show the user-scope → repo-scope seam and preserve participant ownership of
  interpretation, vocabulary, and craft bar.

**Done when:** the script proves a traceable shaping-to-delivery handoff within
the timebox without misrepresenting full discovery.

### T5: Three cold walkthroughs prove the canonical paths are runnable

**Depends on:** T2, T3, T4

**Touches:** docs/specs/m6-live-demo-guide/notes/walkthroughs.md

**Verification mode:** visual/manual QA

**Stub:** no stub (manual QA)

**Tests:**

- A facilitator who did not author the guide runs each track in an isolated
  disposable scenario and records the required evidence. Traces to: AC18.
- Each run completes its exact pack path and Draft spec/plan within 30 minutes,
  or fails honestly; no run fires formal approval, execution, external
  mutation, or work-intake registration. Traces to: AC2, AC11, AC14, AC18.
- The enterprise and non-technical records show Outcome, Appetite, at least one
  Rabbit hole, and a Spec map row before their source brief reaches `Ready`.
  Traces to: AC7–AC8, AC11, AC18.

**Approach:**

- Exercise the happy path plus each track's primary safe-stop condition.
- Record observed results only; do not convert a desk read or partial path into
  a claimed successful walkthrough.
- Revise wording that forces the cold facilitator to invent pack routing.

**Done when:** all three evidence records satisfy AC18 and no script relies on
unstated pack knowledge.

### T6: The guide is registered, published, and reviewable

**Depends on:** T1, T2, T3, T4, T5

**Touches:** guides/core/README.md, tools/test_documentation_entry_links.py, docs/specs/m6-live-demo-guide/notes/**

**Verification mode:** goal-based check + visual/manual QA

**Stub:** no stub (goal-based and manual QA)

**Tests:**

- `python3 tools/test_live_demo_guide.py`,
  `python3 tools/validate_guides.py`, and
  `python3 tools/check-guide-index.py` pass. Traces to: AC1–AC17.
- Relevant build-site navigation checks and
  `python3 tools/test_documentation_entry_links.py` pass independently of any
  rendered-site checker. Traces to: AC16–AC17.
- `git diff --check` and the spec-status lint pass. Traces to: AC18.

**Approach:**

- Add one How-to entry to `guides/core/README.md`.
- Extend the source-backed route inventory while preserving independence from
  `rendered-site-link-debt`.
- Generate or dry-run supported navigation; do not hand-edit sidebar config.
- Run adversarial and documentation-quality review against the walkthrough
  evidence and canonical pack contracts.

**Done when:** the guide is reachable, all validation passes, and reviewers
report no unresolved blocker or major finding.

## Rollout

- **Delivery:** one documentation change containing the guide, Core index
  entry, walkthrough evidence, and spec lifecycle updates.
- **Infrastructure:** none.
- **External-system integration:** none; every baseline script reports
  `No external systems changed`.
- **Deployment sequencing:** author map/frame, implement the three scripts, run
  cold walkthroughs, then register and publish. Approval and implementation of
  any demo-created spec happen later in the normal Core work loop.

## Risks

- The Product Engineering-to-Core path is the longest and may not fit 30
  minutes. The scenario is fixed at feature level/app scale, but the cold run
  must fail honestly if that still exceeds the cap; the guide cannot edit away
  the result.
- A common presentation frame can still be mistaken for one workflow. Pack,
  scope, actual skill controls, and intermediate artifacts are test-pinned per
  track.
- Enterprise language can invite `governance-extras` by association. The guide
  distinguishes evidence depth from RFC/ADR production and names the latter as
  a different task.
- A facilitator may continue after Draft artifacts. The receipt makes the stop
  explicit and routes approval/implementation to a later Core work loop.

## Changelog

- 2026-08-13: Initial Draft plan.
- 2026-08-13: Replaced the generic three-track matrix with six implementation
  tasks and exact technical, enterprise, and non-technical script contracts
  after human review found the first outline too vague.
- 2026-08-13: Reframed the scripts around canonical pack journeys: Core direct
  feature, Core structured handoff, and user-scoped Product Engineering into
  Core; removed the fictitious shared gate sequence and documented why adjacent
  packs are not baseline dependencies.
