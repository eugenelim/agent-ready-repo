# Plan: architect-platform-grounding

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change has three strands that all ride the **already-shipped** RFC-0042 dual-consumed routing axis — none of them is a new mechanism:

1. **Back the lens (S).** Author `lens-serverless.md` once as canonical content — the five concern-grouped sections spanning the whole serverless class, cloud-agnostic, structured like `lens-genai-agentic.md` — then mirror it byte-for-byte into both skill copies (modulo each copy's duplication note). The design side gains the new value on its existing workload-class axis; the review side gains it by repointing the serverless route the rubric **already names** (`rubric-well-architected.md:17`) at the new file. The serverless lens owns the sync-vs-async **mechanics**.
2. **Ground the contract, dual-consumed (C).** Extend `architect-design`'s knowledge-surface discipline (`SKILL.md` Step 2) with a platform-service-contract clause (by construction), and add the independent re-check to `architect-review` WA mode (review re-derives, doesn't trust the design's assertion).
3. **Check viability, dual-consumed (V).** Add the latency-budget-vs-binding-timeout check at design (the lens mechanics + the design-doc rubric's cross-cutting prompt) and at review (the WA Performance pillar check + the review-side design-doc rubric), plus a **one-line** cross-reference from the agentic lens (both copies) into the serverless gate.

The riskiest parts are **altitude** (the grounding / viability disciplines must name boundaries and force questions without sliding into control-level prescriptions or a per-vendor recitation) and **cloud-agnosticism** (the lens must converge the three vendors, not paraphrase AWS). Those are the focus of the design-reviewer / adversarial passes and the K-decision check. Order: author the lens (T1), mirror it (T2), repoint the review route (T3), wire C (T4), wire V (T5), update the backlog (T6), bump + changelog (T7), then dogfood (T8).

This plan describes the **implementing PR**. The governance PR that introduces ADR-0035 and this spec/plan **does not execute it** (no lens authored, no skill / rubric edited, no pack version bumped there).

## Constraints

- **ADR-0035** — the load-bearing decisions: prose on the existing axis (second backed lens), dual-consumed lifecycle (design grounds + review independently re-checks), grounding evidence from authoritative prose at design time (the carve vs RFC-0044's oracles), cloud-agnostic concern-grouped whole-class taxonomy, version-facts-route-to-platform-skills, no new skill / reviewer / tooling.
- **RFC-0045** — D1–D6 and the two resolved open-question defaults (viability mechanics in the serverless lens + one-line agentic cross-reference; field note promoted).
- **RFC-0042 + ADR-0032** — the dual-consumed routing axis this is a *second consumer* of; the axis is not re-authored.
- **CHARTER Principles 1, 2 & 3** — no per-vendor enumeration (cloud-agnostic lens; numbers route to platform skills), no duplication (no new skill; cross-reference not a copied concern), habit not infrastructure (no executable tooling / calculator / fetcher).
- **ADR-0023** — the three-reviewer ceiling (no fourth reviewer; the existing `architect-review` / `design-reviewer` carry the re-checks).
- **The pack's per-skill duplication shape** — both lens copies stand alone, each with a duplication note (`architect/README.md`).
- **`AGENTS.local.md` adopter-clean rule** — no internal RFC / ADR / spec-path / backlog anchor in shipped `.apm/**` content.

## Construction tests

Most verification is per-task below. Cross-cutting checks that span tasks:

**Integration / cross-cutting checks:**
- **Both-copies-identical:** `diff` the two `lens-serverless.md` files with their duplication-note lines normalised — they are otherwise byte-identical.
- **Cloud-agnostic / no per-vendor numbers in the lens:** a reviewer-checked read confirms the lens carries durable rules + "confirm current specifics with the provider"-flagged illustrative examples, and no bundled binding number (no specific timeout-seconds, NCU/OCU/ACU floor, or payload/duration limit asserted as fact); the three-vendor convergence is visible, not an AWS paraphrase.
- **No duplicated viability mechanics:** `grep` confirms the sync-vs-async **mechanics** live only in `lens-serverless.md`; `lens-genai-agentic.md` carries a single cross-reference line, not a copy.
- **Adopter-clean:** `grep` confirms no `RFC-`, `ADR-`, `docs/specs/`, or backlog anchor string appears in any edited `.apm/**` file.

**Manual verification:**
- Dogfood `architect-design` and `architect-review` end-to-end on a serverless concept with a synchronous long-running path; record what loads, what the viability gate and grounding clause produce, and the review-side findings (T8).

## Tasks

### T1: Author the serverless lens (canonical content)

**Depends on:** none

**Tests:**
- `grep` confirms the five concern headings are present: execution & throughput limits + sync-vs-async gate; cold-start & readiness; scale-to-zero economics / capacity floors / cost cliffs; statelessness, idempotency & delivery semantics; private-serverless network reachability (AC: five durable concerns).
- `grep` confirms the lens names the **four serverless entity types** (compute, data, search/analytics, event glue/messaging) and applies concerns across the class, not functions alone (AC: whole serverless class).
- `grep`/read confirms the sync-vs-async gate names the documented options (stream / 202-accept-then-poll / fire-and-forget+callback / deliberate pre-warm) and the delivery-semantics concern names at-least-once → idempotent consumers + DLQ + FIFO-for-ordering (AC: concerns).
- `grep`/read confirms the cost concern distinguishes components that reach zero from those that floor at a minimum capacity unit, and names both the standing-floor and per-request/per-byte-scanned cliffs (AC: scale-to-zero economics).
- Read confirms cloud-agnostic framing: durable rules + "confirm current specifics with the provider"; no bundled binding number (cross-cutting cloud-agnostic check); the three-vendor convergence is visible.
- `grep` confirms the route-to-`security-reviewer` boundary (where a security boundary is crossed) and the apply-what-bites / "use, don't recite" instruction are present (AC: altitude).
- `grep` confirms no internal RFC/ADR/spec-path/backlog anchor (cross-cutting adopter-clean check).

**Approach:**
- Start from the structure of `lens-genai-agentic.md` (intro, distinct-from-diagram-refs note, the progressive/apply-what-bites framing, the routes-into-security-boundary section, the use-don't-recite close) and write the five concern-grouped sections per the spec's concern AC, each naming which serverless entity types it bites.
- Converge each concern from the three hyperscalers' guidance (AWS Serverless Applications Lens; Azure Functions WAF service guide; GCP Cloud Run best practices); carry illustrative examples flagged "confirm current specifics with the provider", never a bundled number.

**Done when:** the canonical lens text exists and all T1 greps pass against it.

### T2: Mirror the lens into both skill copies identically

**Depends on:** T1

**Tests:**
- `diff` of the two `lens-serverless.md` copies (duplication-note lines normalised) is empty (AC: both copies identical).
- `grep` confirms each copy carries its own one-line duplication note pointing at the sibling skill (AC: per-skill duplication preserved).

**Approach:**
- Write the canonical content into `architect-design/references/lens-serverless.md` and `architect-review/references/lens-serverless.md`, each with the per-skill duplication note in the sibling lenses' style.

**Done when:** the both-copies-identical cross-cutting check passes.

### T3: Repoint the review-side serverless route + confirm ML/SaaS unchanged

**Depends on:** T2

**Tests:**
- `grep` confirms `rubric-well-architected.md:17` now loads `lens-serverless.md` for the serverless class (mirroring the GenAI/agentic route's "load `lens-genai-agentic.md`"), with the concern-lens × workload-class axes (`:11-19`) otherwise intact (AC: rubric serverless route resolves to the lens).
- `grep` confirms ML and SaaS are still named as workload-class lenses with **no** backing file (AC: ML/SaaS remain named-but-unbacked, the status-quo half).

**Approach:**
- Add the "For serverless, load `lens-serverless.md`." pointer alongside the existing GenAI/agentic pointer in the workload-class lens bullet; leave ML/SaaS named without backing files; change nothing else in the rubric's selection model (the Ask-first gate at `spec.md` Ask-first applies to any broader rubric change).

**Done when:** the serverless route resolves to the lens and ML/SaaS are confirmed unchanged.

### T4: Wire the platform-contract grounding discipline (C), dual-consumed

**Depends on:** T1

**Tests:**
- `grep`/read confirms `architect-design/SKILL.md` Step 2 (the "never fabricate" knowledge-surface clause) gains the platform-service-contract clause: for every managed service on a critical path, ground its binding contract in an authoritative source (platform skill / docs / `research`), carry source + confidence, lower-confidence-and-flag an ungrounded load-bearing claim, never assert from memory; scoped to load-bearing critical-path claims (AC: C by construction).
- `grep`/read confirms `rubric-well-architected.md` WA mode gains a check that a load-bearing managed-service claim with no visible grounding is a finding, with the reviewer re-deriving rather than trusting the design's assertion, tagged 🔧/🧭 (AC: C independently re-checked).
- `grep` confirms the clause names no framework and no per-vendor number, and carries no internal anchor (cross-cutting altitude + adopter-clean checks).

**Approach:**
- Extend the existing Step 2 degrade-and-lower-confidence prose with the platform-service-contract clause (an in-procedure paragraph; a separate short reference is an option the spec leaves open if the clause grows past a paragraph).
- Add the review-side finding to the rubric's pillar checks (Security / Performance / Provider-fit region, wherever the binding contract is established), framed as re-derive-don't-trust.

**Done when:** both halves are wired and the C greps pass.

### T5: Wire the synchronous-path viability check (V), dual-consumed

**Depends on:** T1, T2

**Tests:**
- `grep`/read confirms the serverless lens's execution-limits concern carries the **viability mechanics** — sum worst-case latency across every hop, compare to the binding front-door timeout, fire the sync-vs-async gate for a long-running operation (AC: V mechanics home).
- `grep` confirms `architect-design/references/design-doc-rubric.md` cross-cutting prompt (`:76-78`, Performance/scale line) carries the viability check (AC: V by construction at design).
- `grep` confirms `rubric-well-architected.md` Performance pillar check (`:36`) gains the binding-constraint framing — an unbudgeted synchronous long-operation path is a finding, 🟥 blocker when structurally impossible — and the review-side `rubric-design-doc.md` cross-cutting (`:66-68`) carries the same prompt (AC: V independently re-checked).
- `grep` confirms `lens-genai-agentic.md` (both copies) carries a **single** cross-reference line into the serverless gate and **no** copy of the mechanics (AC: agentic one-line cross-reference; cross-cutting no-duplicated-mechanics check).

**Approach:**
- Put the latency-budget-vs-binding-timeout mechanics in the serverless lens's execution-limits concern (T1 may already carry them; this task confirms / completes them).
- Add the design-side cross-cutting prompt, the review-side Performance check + cross-cutting prompt, and the one-line agentic cross-reference, mirroring it into both agentic-lens copies (re-run the both-copies-identical check for the agentic lens after this edit).

**Done when:** all V greps pass and the agentic-lens cross-reference is one line in both copies.

### T6: Update the backlog register — serverless resolved

**Depends on:** none

**Tests:**
- `grep` confirms `docs/backlog.md`'s `ml-saas-serverless-workload-class-lenses` entry records **serverless resolved by RFC-0045 / ADR-0035 / this spec**, with ML / SaaS still deferred and the unblock condition retained for them (AC: ML/SaaS deferred, serverless resolved — a *met* criterion of this PR, not a deferred AC).

**Approach:**
- Edit the backlog entry: move serverless out of the deferred set, cite RFC-0045 / ADR-0035 / this spec as the resolver, keep ML / SaaS named-but-unbacked with their unblock condition.

**Done when:** the backlog entry reflects the split (serverless resolved; ML / SaaS deferred), satisfying the spec's final met-criterion AC.

### T7e: Update eval coverage for both touched skills (standing rule)

**Depends on:** T1, T2, T3, T4, T5

**Tests:**
- `grep`/read confirms `architect-design/evals/eval_queries.json` and `architect-review/evals/eval_queries.json` each gain a serverless / synchronous-long-running **should-trigger** query (AC: eval coverage updated).
- `grep`/read confirms each skill's `evals/evals.json` Tier-4 rubric gains an assertion rewarding the new doctrine — design: the latency-budget-vs-binding-timeout viability gate fires and the binding platform contract is grounded with source + confidence; review: an unbudgeted synchronous long-operation path is raised as a finding (AC: eval coverage updated).
- `python3 -m json.tool` confirms each edited eval file is still valid JSON.

**Approach:**
- Add one should-trigger query per skill (serverless API with a long-running synchronous path); extend each skill's Tier-4 `evals.json` assertions. The standing `AGENTS.local.md` rule ("eval coverage is part of pack work") mandates this for a non-cosmetic pack update; the spec under-specified it, so it rides the rule rather than expanding scope.

**Done when:** both skills' eval queries + Tier-4 rubrics reflect the new doctrine and the JSON validates.

### T7: Bump the `architect` pack version + changelog

**Depends on:** T1, T2, T3, T4, T5, T6, T7e

**Tests:**
- `grep`/build confirms `packs/architect/pack.toml` `[pack].version` and `packs/architect/.claude-plugin/plugin.json` `version` are bumped in lockstep (from `0.8.1`) and the top-level `.claude-plugin/marketplace.json` re-aggregates the new version drift-clean (AC: version bump). The lens is pure markdown — **no** `[pack.adapter-contract]` bump. `architect` is a user-scope-default pack with **no** `.claude/` self-host projection. **Erratum:** the all-packs `marketplace.json` aggregation is regenerated by the composite-marketplace step inside **`make build-self FORCE=1`**, *not* plain `make build` (which only writes `dist/`); since `architect` isn't projected, `build-self`'s only working-tree drift is the `marketplace.json` version line.
- `grep` confirms the `[Unreleased] → Added` changelog entry is present (`docs/product/changelog.md`) (AC: changelog).

**Approach:**
- Bump both pack files in lockstep; run `make build` to re-aggregate `marketplace.json`; confirm `git status` shows only the expected `marketplace.json` version line drift. Add the changelog entry.

**Done when:** the version is bumped in both pack files, `marketplace.json` is drift-clean, and the changelog carries the entry.

### T8: Dogfood the lens + disciplines end-to-end

**Depends on:** T3, T4, T5, T7

**Tests:**
- Manual QA: run `architect-design` on a serverless concept with a synchronous long-running path (the field report's agent-behind-a-sync-front-door shape) — record that the workload-class branch loads `lens-serverless.md`, the viability check sums the latency budget against the binding ceiling and fires the sync-vs-async gate, and the grounding clause forces the binding contract into view with source + confidence.
- Manual QA: run `architect-review` WA mode on a design that omits the grounding and the latency budget — record that it raises the ungrounded-load-bearing-claim finding and the unbudgeted-synchronous-long-operation finding (the latter a blocker when structurally impossible).

**Approach:**
- Exercise the built skills the way a user would; capture the observed behaviour in the PR description.

**Done when:** both runs are recorded and show the lens loads, the viability gate fires, the grounding clause forces the contract into view, and the review independently raises the findings.

## Rollout

Pure skill-prose / reference-content change. **Delivery:** ships with the next `architect` pack release (version bumped in T7); reversible by reverting the lens, the routing pointer, the grounding clause, and the viability-check edits. No infrastructure, no external-system integration, no deployment sequencing. **Irreversible:** none. Adopters pick up the serverless lens + grounding disciplines on pack upgrade.

## Risks

- **The lens drifts into per-vendor recitation that rots.** Mitigation: the K decision routes all version-specific numbers to curated platform skills; the lens carries durable rules + "confirm with the provider"; the cloud-agnostic cross-cutting check and the design-reviewer pass guard it.
- **Box-ticking** — "contract grounded: yes" / "viability: ok" with no substance. Mitigation: C's output is a *cited contract slice with confidence*, V's is a *summed latency budget vs. a named ceiling*, and the review re-check re-derives rather than trusting the design's assertion.
- **The grounding discipline over-fires**, demanding a citation for every trivial managed-service use. Mitigation: scoped to load-bearing critical-path claims (a binding limit the design depends on), the apply-what-bites altitude.
- **Lens / agentic-lens duplication of the latency concern.** Mitigation: the serverless lens owns the mechanics; the agentic lens carries a one-line cross-reference only (the no-duplicated-mechanics cross-cutting check).
- **The two copies (serverless, and agentic after the cross-reference) drift** during authoring. Mitigation: the both-copies-identical cross-cutting check, re-run after the T5 agentic-lens edit; a possible follow-up governance lint (noted in ADR-0035, not required here).

## Changelog

- 2026-06-24: initial plan (governance PR — ADR-0035 + this spec/plan). Implementation deferred to a separate PR.
- 2026-06-24: spec-stage review refinements (no approach change): the final ML/SaaS AC was reframed as a *met* criterion (the backlog update is an in-PR action, not a deferral) and its `(deferred:)` marker dropped; the V agentic cross-reference AC clarified to carry the *trigger* and keep the gate reachable for an agentic-but-non-serverless design; T7's `Depends on:` expanded from a range to explicit IDs for the scheduler.
- 2026-06-24: implementing PR. Added T7e (eval coverage) per the standing `AGENTS.local.md` rule, which the spec under-specified. Corrected a T7 erratum: the all-packs `marketplace.json` aggregation is regenerated by `make build-self FORCE=1` (the composite-marketplace step), not plain `make build`. Applied two 🔧-mechanical design-reviewer findings (lens now carries the grounding discipline; "front door" glossed for the non-AWS reader) plus three minors (throttled-downstream hop, pre-warm demoted to a caveat, "model round" glossed). Spec flipped to `Shipped`, all ACs checked.
