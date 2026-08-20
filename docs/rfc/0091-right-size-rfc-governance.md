# RFC-0091: Right-size RFC governance

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** @eugenelim
- **Date opened:** 2026-08-19
- **Date closed:** 2026-08-19
- **Decision weight:** heavy
- **Related:** RFC-0014, RFC-0054, RFC-0055; `docs/specs/new-rfc-two-humans/spec.md`; `docs/specs/new-rfc-fresh-context/spec.md`; `docs/specs/rfc-correction-convention/spec.md`

## Reviewer brief

| Item | Orientation |
| --- | --- |
| Decision | Replace proxy RFC triggers, set proportional review obligations, and simplify the adopter-facing workflow. |
| Recommended outcome | Adopt the four decisions below as one coherent governance model. |
| Change if accepted | - Reserve RFCs for unresolved consequential direction and four protected semantic categories.<br>- Route settled choices to ADRs and routine work to PRs/specs.<br>- Retire `update-conventions`; reduce duplicated `new-rfc` prose without weakening its security or correction contracts. |
| Affected surface | Core CONVENTIONS seed; governance-extras RFC skills, template, evals, guides, pack metadata, and generated projections. |
| Stakes | Heavy: this changes a shipped adopter-facing governance interface, retires a public skill, and resolves a conflict between accepted authorities. It is itself a reserved governance-model change, so it would require an RFC under the proposed rule. |
| Review focus | Whether the consensus-plus-reserved-list model protects consequential disagreement without proxy taxes; whether the light gate correctly resolves the RFC-0054/spec conflict; whether a `core`-only installation (without governance-extras) receives a usable route. |
| Not in scope | Redesigning `work-loop`, light-work specs, `work-intake`, ADR lifecycle, `workspace.toml`, architecture docs, historical RFC bodies, or adding governance configuration/dependencies. |

## The ask

**Recommendation.** Adopt P2 (the consensus test plus a short reserved list, defined below), semantic conventions classification, proportional decision weights, and a smaller RFC workflow. It reserves RFCs for decisions that need discussion before implementation while protecting governance, trust, compatibility, and hard-to-reverse commitments.

**Why now.** The canonical trigger treats proxy facts as sufficient: package count, external visibility, top-level location, and convention edits. Of 91 RFCs, 88 are Accepted and none are Rejected or Withdrawn. This is consistent with an inference that the process documents decisions more often than it rejects proposals, though the status count alone does not prove why. Only three RFCs use `light`, because it currently changes draft length but still imposes six mandatory checks. Meanwhile, an adopter that installs only the `core` pack is told to run an RFC workflow that core does not ship.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | What opens an RFC? | Adopt P2. | It eliminates all false routes in this proposal's routing spike. | Acceptance | Confirm the semantic trigger and reserved list. |
| D2 | How do artifacts and core-only installs route? | Use semantic PR/spec/ADR/RFC/experiment routing that remains usable without an RFC process. | Settled choices and routine work need records appropriate to their purpose. | Acceptance | Confirm routes and fallback record. |
| D3 | What does decision weight change? | Make obligations proportional; light follows RFC-0054 D1. | Resolves the live accepted-authority conflict and makes light usable. | Acceptance | Rule on the proposed conflict resolution. |
| D4 | Keep `update-conventions` and duplicated RFC workflow prose? | Retire the skill; absorb activation phrasing into `new-rfc`; compress/delegate only work owned elsewhere. | The skill has no remaining independent contract after P2. | Acceptance | Confirm removal and bounded prose plan. |

## Problem & goals

The current process mistakes blast radius for consensus need. A cross-package refactor, public bug fix, top-level rename, or clarified convention can be forced into an RFC despite having no open direction. Conversely, one package with several independent stakeholders can evade the RFC path. A settled ADR replacement can be delayed by the act of reversal.

The present weight model does not correct this cost. RFC-0054 introduced `light | standard | heavy`, but its implementation requires all five RFC-0014 checks and a later sixth fresh-context readability check at every tier. Light is therefore practically unused.

Core additionally seeds `docs/CONVENTIONS.md`, including RFC lifecycle and skill-template path references, while shipping neither RFC/ADR skills nor `docs/rfc/`. A core-only installation receives a governance demand without a mechanism.

Goals are to route by decision meaning, make review proportional, preserve protected decisions, and reduce default-loaded governance prose without transferring it to another Markdown file.

**Non-goals.** This RFC deliberately does not create a universal coordination process for large adopters; they may set stricter local rules. It does not make RFCs a product-discovery workflow, impose an optional pack, or redesign document correction policy.

## Proposal

### D1 — Reserve RFCs for unresolved consequential direction

Open an RFC when the direction is unresolved **and** more than one owner must agree, or when a user explicitly asks to circulate an RFC. The reserved list always requires the strongest route the adopter has—an RFC where a process exists and an explicit recorded owner decision otherwise—for: charter mission, scope, or foundational principles; maintainer authority, approval process, or governance model; a security **trust model**; and withdrawal or breaking change to a stable published compatibility promise.

Package count, file count, public visibility, top-level location, a prior ADR, and a conventions pathname become evidence of review depth only. They never alone select the artifact. Behavior preservation, reversibility, compatibility scope, affected maintainers, trust boundary, and precedent remain relevant to the appropriate review depth.

### D2 — Route by the job of the artifact

| Situation | Route |
| --- | --- |
| Routine implementation, bug fix, behavior-preserving refactor, clarification without changed obligation, or accepted-decision implementation | PR, citing the prior decision where useful. |
| Bounded feature or concrete behavior whose direction is settled | Issue or spec; use a spec when acceptance criteria or behavior need definition. |
| Settled durable architectural choice, including a settled replacement for a prior ADR | ADR; write a superseding ADR where needed. |
| Unresolved P2 decision | RFC, followed by ADRs/specs only when acceptance calls for them. |
| User explicitly asks to circulate a proposal | RFC, even when the direction is settled; the request establishes the process, creating `docs/rfc/` and its index if absent. |
| Reversible, time-bounded trial with exit criteria | Normal implementation review; promote to RFC only when permanent adoption is a contested consequential direction. |

Conventions and charter text follow the same semantics. Typos, links, formatting, reorganization, deduplication, clarification, and implementation of an accepted decision are PR maintenance. A changed contributor obligation uses P2 if direction is unresolved; a settled durable governance rationale may be recorded in an ADR. Mission, scope, foundational principles, authority, and governance-model changes are reserved; follow D1.

Core sections 1 and 3 must describe this route without presupposing governance-extras. Where an adopter has an RFC process, reserved and P2 decisions use it. Where no RFC process exists, reserved categories and unresolved multi-owner decisions alike require the owners to reach and retain an explicit recorded decision before implementation; that record may be the adopter's existing decision mechanism and is not a required file, pack, or configuration. Generalise or remove core seed references to a `new-rfc` template path.

### D3 — Give weight different obligations

At every tier, citation-integrity (references are checked to contain their cited claims) and verify-before-you-assert (checkable repository claims are checked against the artifact) apply to citations and claims actually made; neither requires manufactured research or citations.

| Weight | Obligations |
| --- | --- |
| light | One focused decision and compact rationale; completeness checklist; one adversarial pass; no automatic fresh-reader readability check. |
| standard | Full decision argument, proportionate research, decision-by-decision backing, completeness checklist, and adversarial review re-run until clean. |
| heavy | Standard obligations plus explicit reversal, compatibility, or trust-model analysis where applicable; security review when a security boundary or trust model is involved; validation planning where uncertainty is empirical. |

This resolves a live conflict, not merely an implementation detail. RFC-0054, later than RFC-0014 and explicitly superseding it in part, says light uses “completeness checklist + one adversarial pass”; its lines 74 and 147 defer the detailed per-weight obligations. The shipped `new-rfc-two-humans` spec AC5/AC6 instead prohibits tiered gate trimming. This RFC chooses RFC-0054 D1 and defines its proportional form. It requires RFC-level resolution because it reconciles accepted RFC-0014 and RFC-0054, not just their implementation. The fresh-reader readability review is spec-level: it runs only when the proposal introduces coined vocabulary, relies on cross-references to sibling proposals a reader may not have read, or is written for adopters or contributors who did not take part in drafting it; otherwise it does not run.

### D4 — Retire `update-conventions` and narrow `new-rfc`

Retire `update-conventions`. Its routing rule moves to CONVENTIONS section 3; its commit footer belongs in CONVENTIONS commits guidance; its typo exemption is covered by semantic routing; and “err toward RFC” is removed because it is the ceremony tax. Add its convention/charter trigger phrases to `new-rfc`'s description so users still reach the classifier.

Remove `update-conventions` from the pack manifest and eval allowlist, delete its eval files, and migrate pack design/readme/journey/docs surfaces, both source guides and their skill counts, web surfaces, and agentbundle fixture rosters; the hand-authored web pack page requires its owning lane and the journey page regenerates from `JOURNEY.md`.

Compress `new-rfc` by deleting duplicated drafting guidance and its separate workspace queue implementation (`docs/specs/new-rfc-followon-queue-write/spec.md`), delegating queue handling to core's `work-intake` and `workspace-status` skills. Compress the project-knowledge gate while retaining the security/privacy contract substrings enforced by `packs/governance-extras/tests/skills/new-rfc/test_project_knowledge_handoff.py`; update its ordering assertions if surrounding steps are renumbered. Retain RFC-0055 Errata/Amendments in `new-rfc`; reduce its rules and replace the template's long duplicated commented scaffold with a short conditional stub pointing to the skill.

## Options considered

Axis: when a proposal artifact is justified—proxy scope, unresolved consensus need, protected semantic commitment, or broad coordination visibility.

| Option | Result | Spike result |
| --- | --- | --- |
| P0 — current | RFC on package/public/path/convention proxies. | 14 false positives, 1 false negative, 2 ambiguous. |
| P1 — pure consensus | RFC only for unresolved multi-owner direction or explicit request. | 0 false positives, but 2 false negatives: lone-owner charter and authority changes. |
| P2 — consensus plus reserved list | P1 plus the four protected semantic categories. | 0 false positives, 0 false negatives, 0 ambiguous. |
| P3 — cheapen and apply broadly | RFC default for non-trivial work. | 13 false positives, 0 false negatives, 2 ambiguous. |

P0 is the do-nothing option. P1 has an unacceptable single-owner loophole. P3 can suit a large multi-group adopter but is not this pack's default. P2 is the smallest rule covering all 24 scenarios; adopters can choose P3 locally.

## Risks & what would make this wrong

- **Under-routing hidden disagreement.** If owners label a contested choice “settled,” an RFC may be skipped. Mitigation: ask who must agree and preserve explicit circulation; falsifier: contested one-package work routes to PR/spec.
- **Reserved list gaps.** Mitigation: retain the unresolved-direction test rather than expanding a pathname list; falsifier: repeated escalation of a predictably one-way-door category.
- **Light becomes careless.** Mitigation: claim-specific integrity and verification remain; standard/heavy retain iterative review; falsifier: light drafts contain unverified claims.
- **Core fallback becomes vague.** Require an owner and explicit retained record; falsifier: a core-only reserved change proceeds without either.
- **Skill retirement loses discoverability.** Falsifier: the activation evaluation (a test that wording invokes the intended skill) fails for “amend the charter” or “update the rules.”

Drawbacks are real: P2 requires judgment about whether direction is settled, and retirement is a public-surface removal that requires coordinated documentation and eval migration.

## Evidence & prior art

Repository evidence: `packs/core/seeds/docs/CONVENTIONS.md` §1 and §3 contain the canonical broad triggers; `packs/governance-extras/.apm/skills/new-adr/SKILL.md:22-26` distinguishes settled ADR decisions from open RFC discussion. This proposal's 24-scenario routing spike provides the P0–P3 scores; its corpus survey records the 91-RFC outcome and light-tier usage.

Authority evidence: RFC-0014 mandates five gates; RFC-0054 lines 21, 58, 72, 74, and 147 establish partial supersession, the light gate, and deferred per-weight obligations. `docs/specs/new-rfc-two-humans/spec.md` AC5/AC6 and `docs/specs/new-rfc-fresh-context/spec.md` create the conflicting all-tier rules. RFC-0055 and its shipped correction spec make `new-rfc` the sole corrections home.

[Rust's RFC process](https://github.com/rust-lang/rfcs) needs no RFC for “changing shape does not change meaning.” [Go's proposal process](https://github.com/golang/proposal) says “some (but not all) proposals need to be elaborated in a design document.” [Swift's evolution process](https://github.com/swiftlang/swift-evolution/blob/main/process.md) applies to feature design, not implementation or user documentation, and excludes experimental features. [PEP 1](https://peps.python.org/pep-0001/) assigns authors responsibility for building consensus and says most enhancements and bug fixes do not need a PEP. These support semantic qualification and promotion rather than package-count routing. [Kubernetes' KEP guidance](https://github.com/kubernetes/enhancements/tree/master/keps) instead says KEPs should be light enough to be the default for most non-trivial changes—the legitimate stricter-local counter-posture.

## Open questions

*At acceptance (2026-08-19) both recommended defaults are adopted as the
direction; their final form is settled in the implementing spec.*

1. **Is `light|standard|heavy` enforced structurally or by eval/rubric?** Recommended default: constrain the template and evals to those values; do not rewrite metadata of the 91 historical RFCs. Owner: @eugenelim. Decide by: implementation-spec approval.
2. **How does an adopter declare stricter local policy?** Recommended default: free-form—honour and surface any explicit local policy the workflow can read, without mandating a convention or file format. Owner: @eugenelim. Decide by: implementation-spec approval.

## Follow-on artifacts

- An implementation spec for P2 routing, the core-only route, skill retirement, migration, and prose reduction.
- Amend `docs/specs/new-rfc-two-humans/spec.md` to implement the RFC-0054 D1 conflict resolution.
- Amend `docs/specs/new-rfc-fresh-context/spec.md` to make fresh-reader readability review conditional on the stated reader-context properties.
- Retire `update-conventions`, migrate its evaluation/public surfaces, and update `new-rfc` activation wording.
- Regenerate `docs/CONVENTIONS.md`, installed skill projections, and distribution output from changed sources; do not hand-edit projections.

## Errata

- **2026-08-19 — Follow-on mechanism corrected: an ADR, not spec amendments.** The
  *Follow-on artifacts* list above says to amend `docs/specs/new-rfc-two-humans/spec.md`
  and `docs/specs/new-rfc-fresh-context/spec.md`. Both are `Shipped`, which
  `docs/CONVENTIONS.md` § Document lifecycle classes as **Frozen** — status fields may
  change, bodies may not — so amending them is not available. The correct mechanism is
  `docs/CONVENTIONS.md` § Superseding a frozen document: record the decision in an ADR and
  put a scoped pointer in each spec's `Status` field, and only there. Implemented as
  [ADR-0089](../adr/0089-decision-weight-trims-the-rfc-gate.md), which supersedes AC5/AC6 of the first spec and the all-tier scope of the second's
  refinement 3, with both specs annotated in their `Status` line. No spec body was edited.
