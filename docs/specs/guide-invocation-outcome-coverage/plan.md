# Plan: guide invocation and outcome coverage

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `tools/audit-guide-affordances.py`;
  `docs/specs/new-guide-conversation-first/spec.md`; `guides/AGENTS.md`;
  `packs/AGENTS.md`; `docs-site/AGENTS.md`; `docs/CONVENTIONS.md`;
  `guides/architect/how-to/diagram-a-system.md`

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, execution observations belong in
> `notes/verification-ledger.md`.

## Approach

Treat the accepted-base ledger as the closed work queue. Guide additions lift
phrasing or outcomes from current owning sources. Skill-description additions
use the same source-grounded rule, edit only `.apm` sources, and travel with the
pack version, plugin version, changelog, and affected evaluation maintenance
required by repository policy. Run the audit before and after, self-host the
pack projections, generate the site, and record exact target evidence rather
than relying on aggregate percentages.

## Constraints

- The Shipped conversation-first guide spec is the authoring-quality reference;
  its delivery boundary excluded existing guides and is not imported as a
  constraint on this uplift.
- `guides/AGENTS.md` makes `guides/**` the adopter-facing source projected by
  `tools/build-site.py`.
- `packs/AGENTS.md` makes `.apm` canonical and requires version/evaluation and
  self-hosting treatment for non-cosmetic changes.
- The accepted-base exclusions are product boundaries, not optional deferrals.
- A 2026-09-09 pre-review path probe resolved every guide and skill path in the
  accepted-base ledger; it therefore names buildable repository sources rather
  than prospective paths.

## Construction tests

**Integration tests:** fresh before/after affordance ledgers; catalogue
verification; self-host projection; site generation; changed-pack test/eval
sets selected from the owning pack instructions.

**Manual verification:** `author-product-docs` review of every guide delta and a
source-trace review of every skill utterance. Record results per accepted target
in `notes/verification-ledger.md`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Guide invocation/outcome content | T1 | Target-by-target audit and source map | AC1–AC3 result in verification ledger |
| Published skill descriptions | T2 | Source diff, phrase audit, pack gates | AC4–AC11 result in verification ledger |
| Release truth | T2 | Version/plugin/changelog diffs | Close-work checks every changed pack |
| Accepted scope and execution evidence | T1–T3 | Accepted-base and verification ledgers | AC12–AC16 exact membership and gate receipts |

## Design (LLD)

### Design decisions

- The ledger, not a mutable repository total, defines scope. New guides and
  skills do not silently enlarge an approved slice. Traces to AC1–AC9.
- Invocation examples remain routing metadata: they clarify when and how a user
  asks for existing behavior and do not change the skill body. Traces to
  AC4–AC7.
- Generated destinations are verification surfaces only; canonical sources are
  `guides/**` and `packs/*/.apm/**`. Traces to AC8–AC15.

### Dependencies & integration

Guide rendering depends on `tools/build-site.py`. Published skill projections
depend on the repository's pack build/self-host path. Pack and plugin versions
are coupled release metadata and move together when a matching plugin exists.

### Failure, edge cases & resilience

- If an accepted request cannot be grounded in a current source, stop on that
  row and ask rather than inventing behavior.
- If self-hosting changes unexpected source files, preserve unrelated work and
  classify the projection before accepting it.
- If the detector passes weak prose, the source-trace and documentation reviews
  remain the quality backstop.

## Tasks

### T1: Every accepted guide invocation and outcome gap is closed

**Depends on:** none

**Mode:** goal-based check plus documentation review

**Touches:** `guides/catalogue-curation/**`, `guides/core/**`, `guides/credential-brokers/**`, `guides/figma/**`, `guides/frontend-engineering/**`, `guides/iac-terraform/**`, `guides/monorepo-extras/**`, `guides/product-strategy/**`

**Tests:**

- Generate a fresh audit ledger and assert every accepted A/D cell has evidence.
- Record one owning-source citation per added request or outcome.
- Run the `author-product-docs` verification pass over the guide diff.
- Run `python3 tools/validate_guides.py`,
  `python3 tools/check-guide-index.py`, and
  `python3 tools/lint-guide-titles.py`; record each result in the verification
  ledger.

**Approach:**

- Work only the guide table in `notes/accepted-base.md`.
- Lift a literal request or state a concrete result in the guide's existing
  voice and Diataxis form.

**Done when:** every accepted guide cell passes the audit and source/quality
review is recorded.

### T2: Every accepted skill has publishable invocation phrasing

**Depends on:** none

**Mode:** goal-based check plus manual source-trace review

**Touches:** `packs/*/.apm/skills/*/SKILL.md`, `packs/*/.apm/skills/*/evals/**`, `packs/*/pack.toml`, `packs/*/.claude-plugin/plugin.json`, `docs/product/changelog.md`

**Tests:**

- Assert every accepted skill reports quoted-example evidence under the audit
  tool's owned grammar and the exact phrase `Triggers on` in its description.
- Run each affected pack's focused tests/evaluations and catalogue verification.
- Verify pack/plugin version equality for matching plugins.

**Approach:**

- Add one concise, source-grounded quoted request to each target description.
- Add `Triggers on` without altering bodies or authority boundaries.
- Apply required patch-version, changelog, plugin, and eval maintenance per
  affected pack.

**Done when:** all accepted skill rows pass phrase and release-coherence checks.

### T3: Published projections preserve the accepted improvement

**Depends on:** T1, T2

**Mode:** goal-based integration check

**Touches:** `.agents/skills/**`, `.claude/skills/**`, `docs-site/src/content/docs/guides/**`, `docs-site/src/content/docs/packs/**`, `docs/specs/guide-invocation-outcome-coverage/notes/verification-ledger.md`

**Tests:**

- Run the repository self-host command, then `python3 tools/build-site.py`,
  `npm run build --prefix web`, `npm run build --prefix docs-site`, and
  `make site-link-check` in that order.
- Confirm the verification ledger contains successful receipts for all three
  guide-source gates from T1 before declaring generation complete.
- Rerun the affordance audit after generation and compare exact accepted paths.
- Run the targeted build/link checks selected by the touched projections.

**Approach:**

- Generate projections only through repository tooling.
- Record commands, results, before/after present counts, and any accepted
  generated diff in the verification ledger.

**Done when:** generated surfaces, audit evidence, and targeted gates agree with
the canonical sources and AC1–AC16.

## Rollout

One documentation-and-pack release. There is no flag, infrastructure, external
service dependency, or migration. Reverting the source, version, and generated
projection changes together restores the prior state.

## Risks

- A catalogue-wide description pass can become repetitive but semantically wrong;
  the per-row source map prevents phrase invention.
- Multi-pack version churn is easy to make inconsistent; pack/plugin equality
  and catalogue verification are explicit gates.
- Concurrent S1 work may touch generated docs; execution must re-read and
  preserve those changes rather than overwriting them.

## Changelog

- 2026-09-09: initial plan, with fixed accepted-base paths and explicit
  related-intent exclusions.
