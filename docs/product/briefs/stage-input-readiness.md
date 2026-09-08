# Brief: no stage starts on input it cannot work from

- **Slug:** `stage-input-readiness`
- **Received:** 2026-09-02
- **Owner:** Repository maintainers (`ini-002`)
- **Status:** Draft

## Outcome

At each point where authoring hands work to the next stage, the stage that must
do the work asks whether it can, and the answer is recorded rather than
inferred. **No handoff asks this on the consumer's side today**: a contract can
be opened over an undefined outcome with no upstream and no registration and
nothing objects.

### Existing gates

No handoff asks on the consumer's side. As measured 2026-09-02,
`author-delivery-brief`'s canonical Ready gate checks six semantic fields,
requires an independent cold shaping
review, and requires human confirmation before a brief transitions
(SKILL.md:124) — that is considerably more than section presence. `new-spec`
verifies assumptions against repository evidence and waits (SKILL.md:72), and
step 4d runs a UI design-readiness check (SKILL.md:359). What none of them is,
is **consumer-side**: every one of those gates is run by the stage *producing*
the artifact, certifying its own output. Measured 2026-09-02 across skills,
`.agents/rules/`, and `docs/specs/`, **no shared predicate exists that lets the
receiving stage ask whether it can work from what it was handed** — and this
brief must add one that coexists with those gates rather than replacing them.

The finding and its exhibit are owned by
[`agent-authoring-input-quality.md`](agent-authoring-input-quality.md)
§ "What actually works, and what does not".

The question belongs to the consumer, not the producer — is this brief
spec-authoring ready, is `new-spec`'s input spec-authoring ready, is this spec
and plan implementable. A developer accepting a user story already asks the
third.

## Success metrics

- A contract whose upstream is missing or unready is redirected **before its
  body is written**, and the redirect is recorded rather than inferred.
- Each readiness check can be shown to have fired at least once on an artifact
  an author wrote. A check with no firing is withdrawn, not re-worded.
- A readiness answer is refused when it is merely satisfied. The cited exhibit
  sets that failure shape; a check that can be closed that way scores as a
  failure here, not a pass.

## Scope / Non-goals

**In scope**

- **The pre-creation pressure test**, and its redirect to
  `author-delivery-brief create` on a gap.
- **Its two dispositions for an open unknown**: a bounded spike that closes it,
  or the redirect.
- **The consumer-side readiness check at two further handoffs**: `new-spec`'s
  input, and a spec and plan handed to an implementer.
- **Review sequencing** — putting a readiness gate ahead of the review round it
  exists to prevent.

**Non-goals**

- The rubric, the authoring instructions, the delegation anchor, the ownership
  survey, and the `new-spec` step-5a widening. Those are
  [`agent-authoring-input-quality.md`](agent-authoring-input-quality.md).
- Whether written guidance activates at all. That is
  [`guidance-activation-measurement.md`](guidance-activation-measurement.md),
  and the prose half of this brief waits on its report.
- The review lens itself and how findings are adjudicated. *Sequencing* a
  readiness gate before review is in scope because the gate's value is being
  ahead of the findings it
  prevents. What a reviewer looks for once it runs, and the adjudicator's
  contract, stay out.
- What a loop does once it has discovered the contract above it is wrong —
  [`agent-loop-escalation-recovery.md`](../intents/agent-loop-escalation-recovery.md).
- **Sizing discipline.** This brief consumes the sizing signal as a stall
  condition; the band and its derivation stay with
  `agent-authoring-input-quality.md`.

## Constraints / Appetite

The gate half is mechanical by construction and does not wait on the activation
measurement: it asserts declared shape only, and lint precedent for exactly
that shape already exists in `lint-brief-coverage.py` and
`lint-spec-status.py`. It is unblocked and depends on no sibling slice.

The routing-ask half is prose in a routing surface — the class the activation
measurement exists to test — and waits on that report.

### B2 activation verdict

The verdict B2 reads is a named rule. "Prose in a routing surface" is a
class, not something a report can return a verdict for. The owner accepted
`work-intake`'s public routing precedence — an explicit status request routes
straight to `workspace-status` — as the representative, on 2026-09-02. It is in
[`guidance-activation-measurement.md`](guidance-activation-measurement.md)'s
local corpus floor, so B2 has a resolving line. Only the *local* stratum gates
B2; that brief's portability stratum is additive and B2 does not wait on it.

Every check this brief ships carries the activation contract owned by
[`guidance-activation-measurement.md`](guidance-activation-measurement.md)
§ "Constraints / Appetite".

## What nothing checks today

Nothing tests whether a spec should exist. `new-spec` elicits well — it
surfaces an Unverified list and waits — but that defends the spec's *content*.
Its triggers are a disjunction in which "the user explicitly requests a spec"
is sufficient; `Brief:` is stamped only when arriving from a confirmed slice,
nothing checks it resolves, and `none` is accepted almost everywhere. The one
detector that would notice, `unregistered_work`, fires at **dispatch**.

The cited abandonment demonstration establishes this gap.

So a test before any body is written: is there a defined outcome or is this
still shaping; what upstream does it descend from and is that upstream live;
are load-bearing unknowns still open; and if there is no upstream, is direct
authoring justified against the durability triggers and recorded rather than
assumed. **On a gap, redirect rather than refuse** — an agent told no finds
another route, and `author-delivery-brief` already refuses to invent missing
content.

### Redirects

The redirect is a set of four, each selected by a condition. A single target
does not work: `author-delivery-brief create`
refuses a single direct-light change and routes it back to `new-spec`
(SKILL.md:76–80), so a one-change request with no upstream and no justification
would have bounced between the two forever.

| Condition at the gap | Redirect to |
| --- | --- |
| No defined outcome — still shaping | `intake-intent` |
| A defined outcome spanning multiple slices or repositories | `author-delivery-brief create` |
| A defined outcome, one direct-light change | `new-spec`, proceeding with the justification recorded |
| Trivial or cosmetic, below a contract | the direct-light owner |
| A claimed upstream that does not resolve | back to the author to fix the reference; not a redirect |
| A claimed upstream that resolves but is `Draft` | `author-delivery-brief continue` on that upstream — it is unfinished, not absent |
| A claimed upstream that is `Withdrawn` or `Cancelled` | treat as no upstream and re-enter this table at the top |
| A load-bearing unknown is still open | a bounded spike that closes it, or the redirect above if it cannot be bounded |

`intake-intent` is Core's owner for admitting a repository intent.
`frame-intent` ships in the product-engineering pack, which Core does not
depend on, so a Core-owned gate routes to `intake-intent`; an installation
carrying `frame-intent` may route there instead.

The set is now exhaustive over the gate's own branches, which is what makes
B2b's dispositions closeable: a gap either has a defined outcome or does not; a
defined outcome is multi-slice, single-change, or below a contract; and a
claimed upstream either resolves and is live, resolves and is not, or does not
resolve.

### Firing point

As of 2026-09-02, the ask fires at the routing decision, before `new-spec` is
entered, and its answer is recorded. A gate then
asserts declared shape only — a claimed upstream resolves and is live — while a
named human owns whether the answer is true. Naming an upstream cannot
discharge it, because that upstream must exist.

### Upstream predicate

The predicate is "resolves, and is not `Draft`, `Withdrawn` or `Cancelled`".
Measured on the tree on 2026-09-02: 203 of 425 specs carry a `Brief:`
header, 188 of them `none`, and 15 name a brief path — 9 to
`tech-site-completion` (`Shipped`) and 6 to `agent-skill-engineering` and
`distribution-routes-programme` (both `Executing`). **Not one resolves to a
`Ready` brief.** A "must be `Ready`" check would fail all 15 while
`lint-brief-coverage.py` simultaneously requires the
`Executing` transition that causes those failures. The amended predicate fails
none of the 15 and admits `Ready` and `Executing` alike, so it survives the
upstream's lifecycle instead of fighting the lint that enforces it.

Rejected: a diff-triggered check that preserves the earlier "must be `Ready`" wording. It inherits the path-gated-diff failure mode — passing locally while missing in CI unless an explicit base revision is supplied.

### Rule home

The ask lives in a root `AGENT_RULES.md` `always` row. As of 2026-09-02,
the alternatives do not satisfy its firing-point constraints:

- **`work-intake` cannot host it.** Its own § "Public routing precedence" step 2
  routes a request that explicitly names `new-spec` straight to `new-spec`,
  bypassing `work-intake` entirely — and "the user explicitly requests a spec"
  is the sufficient trigger this brief already identifies as dominant. An ask
  placed there would never fire for the case it exists to catch.
- **Amending that precedence is an RFC amendment, not a lint.**
  `docs/specs/core-guidance-artifact-routing/spec.md:105` AC2 is a **ticked
  `Shipped`** criterion pinning `work-intake` to "the RFC-0099 precedence
  exactly", and it separately ticks that direct `new-spec` requests acquire no
  second public answer. Inserting a pressure test on that route contradicts
  both ticks, so it needs an RFC-0099 amendment before B2 could be specced.
- **Inside `new-spec` contradicts the firing point above**, which places the ask
  before `new-spec` is entered, and it collides with B3's owning surface.

An `always` row fires before any routing — `AGENT_RULES.md` instructs an agent
to read every `always` row *before responding or doing unrelated work* — so it
reaches the explicit route without touching a shipped contract. **The cost is
named, not hidden:** the only existing `always` row is `cognitive-load.md`,
which [`guidance-activation-measurement.md`](guidance-activation-measurement.md)
records as a measured non-activation instance. That is a reason B2 waits on M's
report, not a reason to prefer a home the dominant trigger never reaches: M
tests exactly this surface class, and if the verdict is that root-context prose
does not bind, B2's conversion is the same one the routing ask already owes.

### Step 5a and the routing spike

The spike is a different invocation from `new-spec` step 5a. It reuses 5a's
*shape* — cheapest disconfirming evidence, one fixture or measurement or
read-only probe, uncommitted — but not its position. Step 5a is a numbered step
inside `new-spec`, and this fires before `new-spec` is entered, against a risk
unknown rather than a draft criterion. Killing the step-5a widening in
`agent-authoring-input-quality.md` leaves this spike intact, and the reverse
also holds. Keep the two consistent in shape when either is specified; never
cut them as one slice.

## Proposed slices

None is confirmed and no spec is authored. Slice sizes use the targets owned by
[`agent-authoring-input-quality.md`](agent-authoring-input-quality.md)
§ "Sizing discipline".

| # | Slice | Owning surface | Verification | Guide | AC ceiling | Gating |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | The declared-shape gate — a standing check of **`Brief:` resolution only** | a lint over the existing `Brief:` field | the lint fails a spec whose non-`none` `Brief:` does not resolve or is `Draft`/`Withdrawn`/`Cancelled`, and passes all current back-links | `guides/core/reference/product-brief-fields.md` | 7 | **none — unblocked** |
| B2a | The record field for the ask's answer and the direct-authoring justification | the spec template, `new-spec`'s stamping instruction, and `docs/CONVENTIONS.md` § Spec metadata contract | a spec stamped with a justification that cites no durability trigger fails the check | `guides/core/reference/product-brief-fields.md` | 7 | after M reports |
| B2b | The routing ask and its spike-or-redirect disposition | a guard on `loop-engine init` — see § "B2b is one surface: the init guard" | the guard refuses initialisation for a spec whose routing answer is absent from B2a's field, and admits one whose answer is present | `guides/core/reference/work-intake-routing-and-lifecycle.md` | 10 | after B2a |
| B3 | Readiness of `new-spec`'s input — **owns the readiness predicate** | `packs/core/.apm/skills/new-spec/SKILL.md` | the predicate fires on an artifact an author wrote, and a recorded answer that names no durability trigger fails | `guides/core/how-to/receive-a-product-brief-and-decompose-it-into-specs.md` | 6 | none |
| B4 | Readiness of a spec and plan handed to an implementer | `packs/core/.apm/agents/implementer.md`, which cites B3's predicate | a dispatch whose spec or plan fails B3's predicate returns `blocked` before work starts | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | 6 | after B3 |
| B5 | Review sequencing | the pre-EXECUTE review round in `work-loop` | the readiness gate is observably evaluated before the review round runs | none — re-sequences an existing round | 6 | after B4 |

### Readiness predicate

B3 owns the readiness predicate. B4 and B5 cite it.

**The predicate is derived from each consumer's already-declared inputs** (owner
decision, 2026-09-02), so it is read off the repository rather than invented.
Its shape is constant — *every declared input resolves, and the answer is
recorded* — and each consumer instantiates it from its own declaration.

**B4's instance derives cleanly, because `implementer.md` declares its inputs in
order** (`packs/core/.apm/agents/implementer.md:19`): project `AGENTS.md` and
`docs/CONVENTIONS.md`, the targeted spec, the targeted plan focused on the one
assigned task, any files the task body cites, and conditionally an inlined
module. The predicate is therefore: every one of those paths resolves; **the
assigned task body declares its verification mode and its tests**, which that
declaration requires of it; and every file the task cites resolves. Its negative
disposition already exists — the implementer returns `blocked` — so B4 moves an
existing reactive check to before dispatch rather than inventing an outcome.

**B3's instance does not derive symmetrically, and that asymmetry is the finding
rather than a gap.** `new-spec` declares *triggers*, not inputs — its "When to
invoke" is a disjunction in which an explicit user request suffices — so there is
no input list to resolve against. B3's predicate is therefore stated over the
routing decision's own subject: there is a defined outcome rather than open
shaping; a claimed upstream resolves and is not `Draft`, `Withdrawn` or
`Cancelled`; no load-bearing unknown is still open; and where there is no
upstream, the direct-authoring justification cites a named durability trigger.
**The answer is recorded in B2a's field in every branch**, which is what makes
the predicate checkable rather than merely asked; B4 and B5 read that same
field.
The negative disposition is the redirect table above.

**B5 cites B4's instance, not a third one.** It sequences the pre-EXECUTE review
round, whose input is the spec and plan pair B4 already governs.

The ceiling semantics come from that same sizing section.

They ask the same question at three consumers, and an obligation restated per consumer is the
top-ranked category of
[`agent-authoring-input-quality.md`](agent-authoring-input-quality.md)'s
rubric — the one no criterion craft rescues. One home, two citers. This is the
pattern
[`guidance-activation-measurement.md`](guidance-activation-measurement.md) uses
for the activation contract.

### B2 seam

B2's ask and its dispositions are one moment on one decision. Splitting the
ask from its two dispositions would put a question and its answers in different
contracts, so that seam stays closed.

B2 carries two surfaces and must split at that seam when it is specced. The
record field gives it the routing rule *and*
the spec metadata contract, and this brief's own bound is one primary surface
per slice. The split follows the sizing section cited above; it is a sizing
consequence rather than a scope change:

- **B2a — the record field.** The named field for the ask's answer and the
  direct-authoring justification: the spec template, `new-spec`'s stamping
  instruction, and `docs/CONVENTIONS.md` § Spec metadata contract. It ships
  first, because the ask has nowhere to write its answer until it exists.
- **B2b — the routing ask and its dispositions.** The `always` row, its rule
  file, and the spike-or-redirect disposition, writing into B2a's field.

### B2b no longer waits on the activation report

**A deterministic guard does not need to know whether prose binds.** B2b was
gated on M's report while the ask was prose in a routing surface, and M's local
floor still carries `work-intake`'s public routing precedence as the
representative for that class. As a `loop-engine init` guard, B2b asserts a
recorded field and refuses initialisation, so no activation verdict changes what
it does. The dependency is withdrawn; only B2a remains upstream.

**M's floor row is unaffected.** That rule stays in the corpus on its own merits
as a routing-surface representative; it simply no longer has B2b as a consumer.

### B2b is one surface: the init guard

B2b adds a guard to `loop-engine init`, so its primary surface is that verb.
The answer it reads lives in B2a's recorded field, which makes B2a a
prerequisite rather than a second surface — the same owner-and-citer shape B3
uses with B4.

Rejected: a root `AGENT_RULES.md` `always` row. It cost five surfaces — the row,
its rule file, both `packs/core/seeds/` copies since core sets
`lint-seeds = true`, and a registration in
`_SEEDS_REQUIRED_PLACEHOLDERS`, without which `CAT-L029` fails
`agent-rules-read-target-invalid` — and nothing mechanically proves an `always`
row is followed, which is the class of failure this brief's parent exists to
remove.

### Activation limit

Nothing mechanically proves a new `always` row is followed. The router lint
verifies the table's shape, that paths are literal and confined, and that
targets are declared; it cannot show an agent obeyed the rule. That is exactly
the gap M measures, and it is why B2b waits on M's report.

Both remain gated on M's report, and B1 is unblocked because it
checks only the pre-existing `Brief:` field and needs neither half.

### Remaining dependencies

- **B3 and B4 are separate.** Each carries its own surface, verification, and
  guide. The sizing reason for the split is the same one cited above.

- **B5 follows B4, not B1.** It sequences the pre-EXECUTE review round, whose
  readiness gate is B4's. A gate at spec creation already runs ahead of
  `new-spec`'s own shaping and adversarial reviews, so B1 leaves B5 nothing to
  sequence.

## Assumptions / Risks

- **The pressure test is discharged rather than answered.** The existing
  exhibit shows that a gate at creation can fail the same way, so the
  declared-shape gate is deliberately narrow and a named human owns soundness.
- **The routing ask never fires.** Its stated failure mode: the gate then
  catches a claimed upstream that does not resolve, but never a resolvable one
  nobody considered. That is the whole reason the ask half waits on the
  activation report.
- **The spike becomes the work.** An unbounded probe is shaping under another
  name.
- **B3 and B4 carry a prose component whose activation is unmeasured.** The
  routing ask alone is gated on the activation report, so these two proceed
  without it. If the report
  says prose in a stage surface does not bind, B3 and B4 need the same
  conversion the routing ask does.
- **Three checks around one authoring act is real ceremony** and the per-spec
  cost is unmeasured. If written steps do fire, most of this collapses into
  widening rules that already exist.

## B1 decisions

- **The predicate survives the upstream's lifecycle.** The upstream resolves
  and is not `Draft`, `Withdrawn` or `Cancelled`, with the arithmetic in
  § "What nothing checks today". `Ready` is defined as a brief with no
  `Implementing` or `Shipped`
  child (`author-delivery-brief` SKILL.md:221, enforced by
  `lint-brief-coverage.py:_brief_lifecycle_is_valid`), so the moment a derived
  spec starts implementing, its upstream must become `Executing`.
- **B1 does not create the record field; B2a does.** `Brief:`
  is stamped only on arrival from `author-delivery-brief continue`, is
  additive, and accepts `none` (`new-spec` SKILL.md:188–194), which
  `lint-brief-coverage.py` treats as no back-link. A named field means the spec
  template, `new-spec`'s stamping instruction and `docs/CONVENTIONS.md`
  § Spec metadata contract — three surfaces beyond "a lint", which would have
  made B1 a four-file slice against a one-surface bound. **B1 is therefore
  narrowed to checking that the existing `Brief:` field resolves**, which keeps
  it at one surface and preserves its parallel start with M.
- **The direct-authoring branch belongs to B2a with an external binding.** It
  travels with the field that holds it. **The justification must cite a
  named durability trigger, which the check resolves against the trigger list**
  rather than merely confirming prose is present.
- **B1 is a hard check because its reference class is clean.**
  `lint-spec-status.py` invariant (iii) is warn-only and its
  promotion "stays deferred pending the observed warn rate"
  (`docs/specs/spec-code-ref-lint/spec.md:51`); measured 2026-09-02 it emits
  **183 warnings across 425 specs**, which is why that deferral holds for the
  broad dangling-reference class. B1's class is narrower by construction —
  non-`none` `Brief:` values only — and **all 15 of them resolve today**, so a
  hard check of exactly that class starts at zero violations and owes no
  warn-rate evidence. It must stay scoped to that class; widening it to
  arbitrary references would pull the deferral back in.

## Ready gaps (Draft only)

- **Settled — B2b fires as a `loop-engine init` guard** (owner decision,
  2026-09-03). The routing decision is the only point in the lifecycle with no
  dispatched agent, so B2b cannot use the parent's inlining mechanism and must
  not stay prose in a rule file, which the parent records as the mechanism that
  does not bind. It uses the established dispatcher instead: `work-loop` owns
  routing and agent dispatch, and `loop-engine` already owns legal phase
  ordering and guard enforcement, exposing `init` ("initialise
  engine-state.json; output run_id") and `transition` ("fire an FSM event;
  enforce guards"). **A loop cannot be initialised for a spec whose routing
  answer is not recorded.** That is deterministic, needs no agent, hook or rule
  row, and fires *before* a body is written, which the first success metric
  requires. A guard on a transition would not: `SPEC-PLAN-DRAFTING` is the first
  legal state with `last_event: null`, so there is no transition into it, and
  guarding `spec-ready` would fire after the body exists.

  **`init` guards entry to delivery, not file creation.** A spec file can be
  written without initialising a loop, so B1's standing lint remains the other
  half: the guard catches a spec entering the work-loop, the lint catches a spec
  whose `Brief:` does not resolve. Neither subsumes the other.
- **Settled — B's slices take their activation contract from M, not from the
  registry.** Every check here is mechanical: B1 is a standing lint, B2a is a
  spec metadata field, B2b is a `loop-engine init` guard, and B3, B4 and B5 are
  readiness predicates over declared inputs. None consumes a policy family, so
  none waits on `phase-scoped-policy-delivery` or `policy-arrival-validator`.
  The three-part activation contract they each carry is
  [`guidance-activation-measurement.md`](guidance-activation-measurement.md)'s,
  and the earlier broader claim of a registry upstream is withdrawn.
- Ready needs a revision-bound clean shaping review of this brief plus the
  owner's explicit confirmation. Both remain outstanding.
- **Open — B1's activation is unmeasured but it does not wait.** B1 is
  mechanical, so it carries no prose-activation risk. The asymmetry with B2b is
  deliberate.

## Rabbit holes

- **Do not mechanize a judgment.** "Is this criterion well-founded?" is not a
  predicate. Where the same gate is defeated twice by different surfaces, split
  it — as the ask/gate division above does.
- **Do not verify a readiness rule by parsing the rule.** A check that a
  sentence exists in a file proves presence, which is the thing already known.
- **Do not let a readiness check become a section-presence check.** That is the
  defect this brief exists to remove, and it is the cheapest thing to
  accidentally ship.

## Spec map

| Spec | Status |
| --- | --- |
|  |  |

## Provenance

- Source: repository origin. The split provenance is owned by
  [`agent-authoring-input-quality.md`](agent-authoring-input-quality.md)
  § "Provenance".
