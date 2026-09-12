# Spec: Intent review mandate split

- **Status:** Implementing
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0109, RFC-0099
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **An open amendment reverts this status.** While a controlled amendment is
> open, this spec reads `Draft` and its plan reads `Drafting`, which is what the
> work-loop's amendment path instructs. It does not mean the implementation is
> unwritten — committed tasks stay committed, and their sections cannot be
> edited. Both statuses return to `Implementing` and `Approved` when the
> amended baseline is sealed, before the change ships.

## Objective

An author shaping an intent gets two narrow reviews instead of one broad one. The
`shaping-reviewer` `intent` mode answers a mechanical question — is this artifact
well-formed enough to shape further — and answers it in a vocabulary that cannot
express a rewrite: one `MALFORMED(<field>)` token per failed condition, or no output
at all. A target that is not an intent draws a refusal, which is not a result and is
the mode's only other output. The `adversarial-reviewer` `intent` mode answers the
other question — is the
bet risky in a way nobody has named — and may return only an open question with a
named decider or a validation hook, or nothing. The lifecycle owner keeps every
decision: the Callers-and-lifecycle criteria below are the single home of the
`Accepted` gate's mechanics, and `frame-intent` keeps revision and status
authority over both reviews. Success is that an author gets a
short, decidable list of malformations where they used to get spec-grade craft
findings on a thin artifact, and that neither reviewer can propose a different bet.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable; the split reverses part of an accepted design | `docs/adr/0109-intent-review-splits-well-formedness-from-assumption-attack.md` | maintainer | ADR Accepted, indexed in `docs/adr/README.md` | ADR exists and this spec cites it |
| User-facing promise | Applicable; three guide passages state a vocabulary this change moves | `guides/product-engineering/how-to/shape-a-feature-intent.md`, `guides/core/how-to/start-or-remember-work.md`, `guides/core/explanation/core-pack.md` | maintainer | a read of each changed passage plus an absence check for the retired vocabulary; the per-guide split of the adversarial output types is owned by the criteria | every changed passage reads true against the shipped agents |
| Interface compatibility | Applicable; the intent review is a declared cross-pack integration | `packs/product-engineering/pack.toml` `core-intent-shaping-review` entry | pack maintainer | integration entry and its pack test agree on the new vocabulary | entry names no `Clean` for intent mode |
| Release history | Applicable; both packs ship a consumer-visible contract change | `docs/product/changelog.md`, and `web/src/lib/now-highlights.generated.json` when a `Highlights` block ships | pack maintainer | one free-standing entry per pack with an explicit `Highlights` disposition, plus the regenerated public projection | entries exist at `##` level with the shipped versions, and the committed projection matches the changelog source |
| Frozen-record navigation | Applicable; a reader starting at the superseded records must reach the new rule | `docs/specs/shaping-review-contracts/spec.md`, its `plan.md`, `docs/rfc/0099-cut-before-adding-and-artifact-shaping.md` | maintainer | one-way `Status`-line pointer to ADR-0109 naming the superseded part | pointers present, bodies unedited |
| Current architecture | Not applicable | — | — | — | the change adds no module, boundary, or dependency; the reviewer roster and its ownership split are unchanged |
| Operations | Not applicable | — | — | — | no runtime, deployment, or operational surface is involved |
| Reusable learning | Not applicable | — | — | — | the only generalizable material is the ADR's own rationale |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep each mode's rubric readable on its own, so a reader inside one mode never
  has to decide whether another mode's rule reaches them.
- Reference the source that owns a rule instead of restating it, so no fact
  gains a second home that can drift. One bounded exception: a rule the reviewer
  applies must be decidable from the body and the supplied packet, because the
  reviewer preloads and retrieves nothing, so the recognized level ordering is
  stated in the body. The exception covers the ordering alone, cites no internal
  record, and leaves the open set open.
- Say what a rule's failing state is. A rule with no failing state is guidance,
  and belongs in the plan or a guide rather than in this contract.

### Ask first

- Any change to the `delivery-brief` or `spec` rubric, or to a row of the
  failure-mode table those two modes keep.
- Any change that makes the adversarial `intent` mode gate a lifecycle
  transition.
- Any edit to a frozen record beyond its `Status` line.

### Never do

- Never add a fourth `shaping-reviewer` mode, a new agent, or a new skill.
- Never edit an adapter projection directly; `.apm/` is the only source.
- Never grant either reviewer authority beyond what it holds today. The
  adversarial reviewer's code-facing and RFC modes read the guidance chain and
  the diff, and keep doing so; `shaping-reviewer` keeps exactly
  `Read, Grep, Glob` and retrieves nothing beyond the supplied packet.
- Never let `de-risk-intent` dispatch `adversarial-reviewer`.
- Never edit the body of the shipped `shaping-review-contracts` spec or plan,
  and never untick one of its acceptance criteria.

## Testing Strategy

- **Changed contract prose — TDD.** The three agent bodies — both reviewers and
  the adjudicator that owns the predicates — the two caller skills, the
  `de-risk-intent` boundary, and the integration entry are the product here, so
  every criterion whose bytes change is asserted by a pack test that fails
  against today's bytes before its edit lands.
- **Preserved contract prose — standing controls.** The criteria that require
  something to stay true — the reviewer's tools, boundary, preload set, and
  authority rules; `Result values: Clean | Findings` for the other two modes;
  the other adversarial modes' severity grouping and `Clean — ready to commit.`
  sentinel; the caller-owned `BLOCKED:` receipt — are asserted by tests that
  pass before and after. A preservation control asserted to fail first is a
  control someone weakens until it does, so the two obligations are declared
  apart. Every criterion in the three contract-prose groups carries exactly one
  of these two modes.
- **Release and projection parity — goal-based check.** Version parity, the
  regenerated marketplace manifest, and projection freshness against `.apm/` are
  one-liners with an observable pass, not behaviors needing a test double.
- **Eval harnesses — goal-based check.** A grep over the three harnesses:
  no intent-mode `Clean` expectation survives in the two dispatching callers,
  and `de-risk-intent`'s carries its boundary and no intent vocabulary.
- **Governing-record correction — goal-based check.** ADR-0109 is this spec's
  `Constrained by:` record and is corrected in body, not by a `Status` pointer,
  because it is branch-local and has never shipped. The check is a read of
  decision item 1 against the criteria it governs; a record that still states a
  superseded trigger fails it.
- **Frozen-record pointers — goal-based check.** `git diff` over the three
  records shows only `Status` lines changed, and the spec-status lint accepts the
  annotated tokens.
- **Changelog entries — goal-based check.** Each entry's heading level is read
  directly, because a versioned entry nested under `[Unreleased]` passes every
  other gate and still never publishes. The `/now/` projection has its own
  shipped suite; it is run, not written.
- **Reviewer behavior end to end — visual / manual QA.** Both intent modes are
  agents a user invokes, so a passing prose assertion is not sufficient evidence
  that the contract produces the intended output. Each mode is exercised against a
  real intent and the observed output recorded.
- **Guide prose — goal-based check.** The repository's shaping-review
  documentation suite plus a read of the two changed passages.

## Acceptance Criteria

### Well-formedness mode

- [ ] `shaping-reviewer` `intent` mode states exactly six well-formedness
  conditions: the statement is an outcome and not a solution; non-goals are
  present; the riskiest assumption is named; altitude is consistent with the
  parent it names; the decomposition partitions the artifact's own outcome with
  no overlap and no gap; the owner is the artifact's own.
- [ ] The failure-mode table states the modes it governs, and `intent` is not
  among them.
- [ ] The `intent` mode section contains no row title from that table and no
  text from its `Tell` or `Fix shape` columns.
- [ ] Each piece of mode-agnostic prose in the failure-mode section has one
  named home: the ownership-precedence passage governs all three modes and keeps
  its current scope, so `delivery-brief` and `spec` lose nothing; the
  restated-guidance-is-degraded rule and the emphasis-density routing are scoped
  to `delivery-brief` and `spec`, which are the modes that can express them.
- [ ] The `intent` mode section states no precedence sentence of its own,
  because the `MALFORMED(owner)` suppression rule already carries the
  intent-mode consequence and a second statement would be a second home.
- [ ] For an in-scope intent target, `intent` mode's only result values are
  `MALFORMED(statement)`,
  `MALFORMED(non-goals)`, `MALFORMED(riskiest-assumption)`,
  `MALFORMED(altitude)`, `MALFORMED(children)`, and `MALFORMED(owner)`, one per
  failed condition.
- [ ] `MALFORMED(owner)` is emitted alone and suppresses the other five tokens.
- [ ] A condition the supplied packet cannot settle emits its own token, so an
  intent that names a parent the packet does not supply cannot pass the altitude
  condition by default.
- [ ] Condition 4 applies only to an intent that names a parent. A parent is an
  optional attribution, so an intent naming none is not malformed for it at any
  level, and the condition has nothing to measure against. An intent that names
  one the packet does not supply still emits `MALFORMED(altitude)`.
- [ ] Condition 5 measures a declared set, not the presence of one. Where the
  artifact lists a decomposition, both halves — no overlap and no gap — are
  settled from those members against the artifact's own outcome, so the
  children's own packets are not required and their absence emits no token.
- [ ] Where the artifact lists no decomposition, condition 5 emits
  `MALFORMED(children)` only when the artifact declares a level above the leaf
  of the recognized set and a status of `Accepted`. Below that, an empty
  decomposition is a lifecycle stage rather than a malformation: framing
  precedes de-risking, which precedes decomposition, so an intent is childless
  when it is framed whatever its level, and the review runs at framing.
- [ ] A level the mode cannot place in the recognized set — declared outside it,
  or not declared at all — suppresses only that absence branch, and emits no
  token of its own. The result set stays at six, so no unplaceable level is
  reported as if it were a failed altitude or children condition, and a listed
  decomposition is still measured for overlap and gap.
- [ ] The body states the level ordering it keys on — `product-vision ›
  product-strategy › capability › feature` — so applicability is decidable from
  the body and the supplied packet alone. The reviewer preloads nothing and
  retrieves nothing, so a rule keyed on a ladder stated only elsewhere is
  undecidable at the moment it is applied. Stating it here is a deliberate
  second statement of an ordering core already seeds, accepted because the
  alternative is a rule the reviewer cannot resolve; it names the ordering only,
  cites no internal record, and leaves the open set open.
- [ ] `intent` mode emits no severity label, no `Fix:` line, and no `Clean`
  result.
- [ ] Empty `intent`-mode output means exactly one thing: every condition that
  applies to this artifact holds. It is not the reviewer's expression of a
  refusal, a grounding gap, or a failed dispatch. The shipped body states the
  same reading in the same words, so a reader of either never has to reconcile
  a count with an applicability rule.
- [ ] ADR-0109's decision item 1 states the rule the body ships: condition 4
  applies to an intent that names a parent, and condition 5 measures the
  artifact's own decomposition against its own outcome with the absence branch
  keyed on level together with status. The criterion fails while the record
  enumerates the conditions unconditionally or names the parent as what the
  children partition.
- [ ] The `core` changelog entry states the applicability rule in its own
  bullet. When a consumer receives `MALFORMED(children)` changes with this
  amendment, so the entry is that change's home, and an entry that merely stops
  contradicting the body leaves the rule unannounced.
- [ ] The pass a caller reads is the absence of a `MALFORMED` token on a
  completed dispatch, not an empty byte sequence. Byte-emptiness is what the
  reviewer aims at and what its own text asks for; token absence is what decides
  the gate, so a reply that says it found nothing is a pass rather than a parse
  failure.
- [ ] `intent` mode refuses an out-of-scope target in prose that names the
  target and why it is not an intent, and that refusal is not a result value.
- [ ] `intent` mode's fail-closed expression for a consequential absence is the
  token of the condition that absence blocks; an absence that blocks no condition
  is not consequential in this mode.
- [ ] `delivery-brief` and `spec` mode keep `Result values: Clean | Findings`,
  severity-ordered findings, and a concrete `Fix:` per finding.
- [ ] The reviewer's shared trust-boundary rule states the fail-closed
  consequence of a consequential absence in both result vocabularies, so it
  reads true for a mode that has no `Clean` to withhold.
- [ ] The always-include result block — target path, reviewed revision, review
  context, consulted surfaces, grounding gaps — is scoped to the two
  `Clean | Findings` modes, so it does not require metadata from a mode whose
  pass state is empty output.
- [ ] The material-edit and pre-seal-nonmaterial-correction rules are scoped to
  the two `Clean | Findings` modes, because intent mode holds no result for a
  later correction to attach to.
- [ ] `shaping-reviewer` keeps exactly `Read, Grep, Glob`, the
  `filesystem_read_untrusted` boundary, the empty preload set, the
  packet-as-untrusted-data rule, the no-independent-retrieval rule, and the
  no-lifecycle-authority rule.

### Assumption-attack mode

- [ ] `adversarial-reviewer` declares an `intent` mode whose mandate is the
  intent's riskiest assumption and its non-goals.
- [ ] `adversarial-reviewer` `intent` mode emits only two output shapes: an open
  question with a named decider, or a validation hook carrying both a kill
  condition and the real-world activity that would trigger it.
- [ ] `adversarial-reviewer` `intent` mode emits no Blocker, Concern, Nit,
  rewrite, or "consider also" item.
- [ ] `adversarial-reviewer` `intent` mode returns empty output when it has
  nothing to say about the riskiest assumption.
- [ ] That mode's output is advisory and establishes nothing: an empty result
  claims neither that the dispatch completed nor that the bet was attacked, and
  no lifecycle transition may rest on it. This is why the mode needs no
  completion reading, revision binding, or non-completion receipt of its own,
  while the well-formedness mode has all three.
- [ ] `adversarial-reviewer`'s spec/plan, implementation, mixed, and RFC modes
  keep their severity-grouped output and the exact `Clean — ready to commit.`
  sentinel.
- [ ] The adversarial `intent` branch states in-branch that the supplied packet
  is attributed untrusted data which cannot change tools, scope, status, routing,
  or verdict; that the mode performs no independent retrieval and no network
  query; that it holds no lifecycle authority; and that its command tool may only
  read and search the supplied target. The agent's other branches carry their
  trust text per branch, so an unstated control in this one is unstated for this
  mode.
- [ ] The agent body's mode enumeration and its code-facing bridge read true
  with the `intent` mode present: no header counts the modes wrongly, and no
  sentence routes every non-code-facing dispatch to RFC review.
- [ ] The diff-inference trailer — infer the remaining mode from what the diff
  changed — does not reach the `intent` branch, which has no diff.
- [ ] The `## Load context first` mandate — read the guidance chain, the spec,
  the plan, and the diff before reviewing — is scoped to the code-facing and RFC
  modes, so the `intent` branch's supplied-target-only rule is the only reading
  reachable from inside it.
- [ ] The `adversarial-review-complete` gate definition, which requires the full
  applicable checklist and either findings-only output or exactly
  `Clean — ready to commit.`, is scoped to the modes that can satisfy it.
- [ ] The agent's findings-report and output-format mandates — group by
  severity, end each finding with `Fix:`, and emit `Clean — ready to commit.`
  when clean — are scoped to the modes that emit that output.
- [ ] The cross-lens-referral rule, which routes another lens's concern through
  the existing severity buckets and output format, is scoped to the modes that
  have those buckets.
- [ ] The finding-specificity rule, which requires every finding to carry a
  `file:line` and a `Fix:`, is scoped to the modes whose output has those parts.
- [ ] The two intent-mode output shapes are the only output rule reachable from
  inside the `intent` branch: a reader there encounters no instruction to group
  by severity, to append a `Fix:`, or to emit the clean sentinel.
- [ ] `adversarial-reviewer`'s `description` names the `intent` mode alongside
  the spec, plan, and implementation targets it already names.
- [ ] The `description`'s instruction to re-run until the agent reports
  `Clean — ready to commit.` is scoped to the modes that emit that sentinel, so a
  caller routing on the frontmatter cannot loop forever on an `intent` dispatch.
- [ ] Both intent modes require the adjudicator-owned six-predicate self-check
  before emission, by reference to its owning source. Neither mode reproduces a
  predicate's definition or the list as an authoritative set; naming a predicate
  is permitted only where stating its binding requires it.
- [ ] Each intent mode states how all six predicates bind in its own
  vocabulary, so none of them holds vacuously by accident, and each binding is a
  reading the owning source supports rather than a narrowing of its text.
  Observation and authority bind unchanged. Reachability binds to the artifact
  rather than to an implementation: the condition or assumption must be locatable
  in the supplied intent. Existing handling binds to the artifact's own text: a
  condition the intent already satisfies elsewhere, or an assumption it already
  records as accepted or deferred, is handled. Proposed mechanism binds to the
  validation hook in the adversarial mode, and in the well-formedness mode takes
  the owning source's existing `absent` outcome, which is what that source
  already records for an emission proposing no mechanism.
- [ ] The owning source states the consequence predicate in a form that holds
  for a vocabulary carrying no severity, so neither intent mode has to narrow it
  from the consumer side.

### Callers and lifecycle

- [ ] `intake-intent` records the intent revision it dispatched and owns the
  binding, because an empty intent-mode result carries no target or revision of
  its own.
- [ ] `intake-intent` establishes that a dispatch completed from the host's
  dispatch outcome rather than from the reviewer's output, because the pass state
  carries no bytes, and treats only a completed dispatch with no `MALFORMED`
  token as the pass.
- [ ] `intake-intent` emits its own receipt naming a dispatch that did not
  complete, distinct from its receipt for an unavailable independent route.
- [ ] `intake-intent` sets `Status: Accepted` only after a completed,
  revision-bound `intent`-mode dispatch carrying no `MALFORMED` token, plus
  explicit human confirmation.
- [ ] `intake-intent` returns every `MALFORMED` token to its own revision step
  and keeps the intent at `Draft` while one is unresolved.
- [ ] `frame-intent` records the intent revision it dispatched and establishes
  completion from the host's dispatch outcome, on the same terms as
  `intake-intent`.
- [ ] `frame-intent` emits its own receipt naming a dispatch that did not
  complete, distinct from `Optional Core intent shaping review: unavailable`.
- [ ] An unresolved `MALFORMED` token blocks a `frame-intent` reviewed handoff
  and keeps the intent with its author for revision.
- [ ] `frame-intent` may dispatch `adversarial-reviewer` `intent` mode as a
  second optional review and returns its open questions and validation hooks to
  the author with no lifecycle effect.
- [ ] `frame-intent` reports `Optional Core intent shaping review: unavailable`
  when no independent route exists, and claims no review result in that case.
- [ ] The `core-intent-shaping-review` integration entry in
  `packs/product-engineering/pack.toml` describes the `MALFORMED`-or-nothing
  vocabulary, and its fallback text claims no `Clean`.
- [ ] `BLOCKED: intent shaping review — independent route unavailable` remains a
  caller-owned lifecycle receipt and is not a reviewer result.
- [ ] `de-risk-intent` states that it never dispatches `adversarial-reviewer`.

### Records, release, and projection

- [ ] `docs/specs/shaping-review-contracts/spec.md`, its `plan.md`, and
  `docs/rfc/0099-cut-before-adding-and-artifact-shaping.md` each carry a one-way
  `Status`-line pointer to ADR-0109 naming the superseded intent part, with no
  other line changed.
- [ ] `core` and `product-engineering` each ship the bump level the owning
  version-bump rule yields for changed pack content, matched between `pack.toml`
  and `.claude-plugin/plugin.json`, and the regenerated marketplace manifest
  carries both.
- [ ] The `intake-intent` and `frame-intent` eval harnesses state the shipped
  intent-review vocabulary, and no eval expectation in either names a `Clean`
  result for intent mode.
- [ ] The `de-risk-intent` eval harness covers its no-dispatch boundary and
  states no intent-review vocabulary, which it never consumes.
- [ ] `docs/product/changelog.md` carries one free-standing `##` entry per
  released pack, each with an explicit `Highlights` disposition.
- [ ] When an entry ships a `Highlights` block, the committed public `/now/`
  projection matches the changelog source, so the release does not land with a
  stale projection.
- [ ] Every adapter projection of the three changed agent bodies — both
  reviewers and the adjudicator whose consequence predicate this change restates
  — and of the three changed skills matches its `.apm/` source.
- [ ] `guides/product-engineering/how-to/shape-a-feature-intent.md` and
  `guides/core/how-to/start-or-remember-work.md` each describe the intent-mode
  `MALFORMED`-or-nothing contract.
- [ ] `guides/product-engineering/how-to/shape-a-feature-intent.md` names the
  two adversarial intent output types, and `start-or-remember-work.md` does not,
  because the skill it documents never dispatches that mode.
- [ ] `guides/core/explanation/core-pack.md`'s description of
  `adversarial-reviewer` reads true for every mode it now has: its
  severity-labeled-findings claim and its cannot-be-skipped claim are scoped to
  the modes where they hold, since the `intent` mode is optional and emits no
  severity label.

### Observed behavior

- [ ] A recorded manual-QA run dispatches `shaping-reviewer` `intent` mode
  against one intent that violates at least two conditions and observes exactly
  the matching `MALFORMED` tokens.
- [ ] A recorded manual-QA run dispatches `shaping-reviewer` `intent` mode
  against one well-formed intent and observes empty output.
- [ ] A recorded manual-QA run dispatches `adversarial-reviewer` `intent` mode
  against one intent whose riskiest assumption is named but untested, and
  observes at least one open question with a named decider or one validation
  hook carrying both a kill condition and its triggering activity.
- [ ] A recorded manual-QA run observes that the same mode emits no Blocker,
  Concern, Nit, rewrite, or "consider also" item on that dispatch.
- [ ] A recorded manual-QA run dispatches three intents against the rebuilt
  projection, each carrying no decomposition, and observes that only the third
  emits `MALFORMED(children)`: one at the leaf level, one above the leaf at
  `Draft`, and one above the leaf at `Accepted`. The first two are the states
  the authoring pipeline produces and must pass; the third is the condition's
  reachable failing state. A run whose cases produce the same output settles
  nothing, because the repair is the difference between them.
- [ ] A recorded manual-QA run observes the unplaceable-level cases against
  fixtures that satisfy every other trigger of the absence branch — no listed
  decomposition, and `Status: Accepted` — one declaring no level and one
  declaring a level outside the recognized set. Neither emits
  `MALFORMED(children)`, and because each fixture differs from the firing case
  in the level alone, the missing token is attributable to the suppression and
  to nothing else. A fixture that would pass with the suppression removed does
  not close this criterion.

## Follow-ons

<!-- none at authoring time -->

## Assumptions

- Technical: the failure-mode table is a single mode-agnostic Markdown table in
  the reviewer body, so scoping it is a heading-context edit rather than a
  rewrite (source: `packs/core/.apm/agents/shaping-reviewer.md:65-82`).
- Technical: the six-predicate self-check already exists as prose delegating its
  predicate list to the adjudicator, so intent mode reuses a mechanism rather
  than introducing one (source:
  `packs/core/.apm/agents/adversarial-reviewer.md:278-286`).
- Technical: `de-risk-intent` dispatches no reviewer today, so its boundary is a
  new explicit statement and not a removal (source: `grep -rn reviewer
  packs/product-engineering/.apm/skills/de-risk-intent/` returns nothing).
- Technical: the old intent-mode vocabulary is pinned in three pytest suites and
  two eval harnesses, all of which move with the contract (source:
  `packs/core/tests/pack/test_shaping_review_contract.py:109-159`,
  `packs/core/tests/skills/intake-intent/test_intent_shaping_review.py:38-62`,
  `packs/product-engineering/tests/pack/test_frame_intent_shaping_review.py:36-85`,
  `packs/core/.apm/skills/intake-intent/evals/evals.json:28-62`,
  `packs/product-engineering/.apm/skills/frame-intent/evals/evals.json:34-37`).
  The eval harnesses are non-waivable under `packs/AGENTS.md` § Security and
  authoring rules.
- Technical: neither reviewer agent carries an eval surface of its own, so the
  eval obligation lands on the three changed skills (source: `packs/core/.apm/agents/`
  holds six `.md` files and no eval directory).
- Technical: three guide passages state a vocabulary this change moves. Two name
  the intent-mode result vocabulary (source: `grep -rn '`Clean`' guides/`), and
  `guides/core/explanation/core-pack.md:69` describes `adversarial-reviewer` as
  returning severity-labeled findings and being unskippable — claims a search for
  `Clean` cannot surface, because the adversarial half of this change retires
  neither word (source: a search for adversarial-mode descriptions across
  `guides/`, which is the evidence the `Clean` grep could not reach).
- Technical: no agentbundle engine coupling exists, because the authoring
  scaffold holds no core or product-engineering pack content — only
  `packs/AGENTS.md`, `_example`, guides, profiles, and tests (source: `find
  packages/agentbundle/agentbundle/_data/catalogue-scaffold -type f`).
- Process: shipped pack content may not cite this repository's governance
  records, so the agent bodies state the rules directly (source:
  `packs/AGENTS.local.md:47-60`).
- Process: `packs/AGENTS.local.md:26-42` owns the pack release pipeline,
  including the changelog entry's level and its `Highlights` decision (source:
  that file).
- Product: `frame-intent` is the one optional caller of the adversarial `intent`
  mode; `de-risk-intent` is excluded and still authors its own kill condition
  (source: user confirmation 2026-09-11).
- Product: `Accepted` is gated by an empty well-formedness result plus human
  confirmation, and the adversarial pass never gates a transition (source: user
  confirmation 2026-09-11).
- Product: a caller reads completion from the host's dispatch outcome, and an
  out-of-scope target draws a prose refusal rather than silence, so empty output
  is reserved for the well-formed case alone (source: user confirmation
  2026-09-11).
- Process: the `MALFORMED` field tokens are a closed set, extended from five to
  six so a wrong owner surfaces as `MALFORMED(owner)` rather than as prose
  (source: user confirmation 2026-09-11; ADR-0109 decision item 1).
