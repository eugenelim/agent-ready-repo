# How to record a decision (ADR)

You made an architectural call — a database choice, a process commitment, a structural rule the team will live with — and the next person to ask "why did we do it this way?" deserves an answer in writing. The `new-adr` skill drafts an Architecture Decision Record in `docs/adr/` from the bundled template, with the next sequential number, and pushes back on hand-wavy sections before you commit.

This guide is task-oriented; for the *why* of ADRs (immutable history vs. living docs), read [`docs/CONVENTIONS.md` § ADR](../../../CONVENTIONS.md#2-adr--architecture-decision-records--docsadr). For where ADRs sit in the wider doc system, see [the core pack as a system](../../core/explanation/core-pack.md).

## ADR or RFC?

The two skills look adjacent and confuse readers regularly. The split is about *time*, not topic:

| Property | ADR (`new-adr`) | RFC (`new-rfc`) |
| --- | --- | --- |
| Direction in time | Backward-looking record | Forward-looking proposal |
| State of the decision | Made (or about to be made) | Under debate; may be rejected |
| After acceptance | Body frozen at acceptance; `Status:` header still mutable | Body frozen at acceptance (status field mutable); spawns ADRs, specs, convention edits |
| Change mechanism | New ADR that *supersedes* the old; status of the old flips, body stays | Normal revision until accepted, frozen thereafter |

If the call is already made (or you're recording one made in a meeting yesterday), it's an ADR. If you want a debate, it's an RFC — and the *accepted* RFC then produces one or more ADRs as follow-on. See [how to propose a change (RFC)](new-rfc.md) for the inverse view.

## Prerequisites

> **Pack:** `governance-extras`. `new-adr` does not ship in `core`. Verify with `ls .claude/skills/new-adr/` (or the equivalent skill registry in your IDE — Claude Code's `/agents`, Cursor's Composer, etc.). If the directory is missing, install or enable `governance-extras` first.

- A `docs/adr/` directory at the repo root. The skill creates it on first use if absent; the repo's seed `docs/adr/README.md` is fine to leave in place.
- A decision that genuinely warrants an ADR — the entry-point prose below covers the test.

## When is `new-adr` the right call?

Three conditions, all must hold:

1. **The decision is about architecture or shared infrastructure**, not one feature's internals. ("We use Postgres for the primary store" is an ADR; "the saved-filters chip uses URL state, not local storage" is a spec.)
2. **The decision has been made** (or is being formally proposed for acceptance). ADRs are not the venue for open-ended discussion — that debate belongs in an RFC.
3. **There is a concrete tradeoff.** At least one viable alternative was considered. If only one option exists ("we use UTF-8"), you don't need an ADR.

If any of these fails, push back rather than writing an ADR that future readers will discount. The skill checks them at invocation time.

> **Invoke skills by name.** Claude Code's description-based auto-discovery is best-effort — natural phrasings like "let's ADR this" usually fire the right skill, but not always. **Naming the skill in your request guarantees it fires.** Use `use the new-adr skill to …` whenever you want the discipline, including on edges where description matching wouldn't pick it up.

## Step 1 — Invoke the skill

Two worked invocations that genuinely differ:

```
use the new-adr skill to record our choice of Postgres over DynamoDB
for the user-activity store
```
(technology choice — the alternatives section will weigh DynamoDB, SQLite, and a managed warehouse against the team's Postgres familiarity.)

```
use the new-adr skill to record our decision to use trunk-based
development with short-lived feature branches
```
(process choice — the alternatives section will weigh GitFlow and release-branch models against the team's deploy cadence.)

Natural phrasings (`let's ADR this`, `write an ADR for X`, `record this decision`) match the skill's description and often trigger it, but description matching isn't guaranteed. Lead with `use the new-adr skill to …` whenever you want the discipline to fire reliably.

## Step 2 — Confirm the three preconditions

Before the skill scaffolds anything, it asks (explicitly or implicitly) about architecture-not-feature, decided-not-debated, and real-tradeoff. If you can't answer cleanly, the skill pushes back. Two common redirects:

- **"This is still being debated."** → open an RFC instead. The accepted RFC then produces the ADR as follow-on.
- **"This is about a single feature's internals."** → write a spec (`new-spec`), not an ADR.

## Step 3 — Find the next ordinal and scaffold the file

The skill runs its bundled `scripts/next-ordinal.py` helper (the path is skill-relative; the skill resolves it for you). It prints the next 4-digit ordinal — `0001` if `docs/adr/` is empty, max-plus-one otherwise. Numbers are sequential and never reused. The helper parses the full digit prefix, so transitions like `0099` → `0100` work correctly without manual zero-padding.

The skill then picks a short kebab-case filename from your description (`0007-primary-store-postgres-over-dynamodb.md`, not `0007-decision-about-the-database.md`), copies its bundled `assets/adr.md` into `docs/adr/`, and renames. The H1 title inside names the problem and the chosen solution together (keeping the `ADR-NNNN` ordinal), so the decision reads clearly from the index. The skill keeps it **short** — the title *identifies* the decision rather than encoding the whole rationale (that lives in the Decision section); a title that compresses the whole argument into a clause makes the index hard to scan.

## Step 4 — Fill in frontmatter

Status starts as `Proposed`. Today's date. `Decision-makers` are the GitHub handles of the people who own the call; add `Consulted` (whose input was sought, two-way) and `Informed` (who is kept up to date, one-way) when the decision was run past others, and delete those two lines otherwise. `Supersedes:` is `none` for a greenfield ADR; otherwise the ADR number being replaced (see Variations). Keep `Consulted` and `Related` **pointer-like** — short lists of handles and ADR/RFC/spec references, not prose; if a relationship needs explaining, that explanation goes in Context or References, not the frontmatter.

## Step 5 — Draft the body sections

If your request arrives tangled — rationale, history, and several sub-decisions in one breath — the skill first reflects back a short **decision frame** (the decision in a sentence, the problem it resolves, the alternatives, the winning driver, what you're giving up) to isolate the call before drafting; when the decision is already crisp it skips the frame and drafts straight away. It then walks you through Context, Decision, Consequences, and Alternatives, and offers two optional sections — **Decision drivers** (the criteria the choice was judged against, so each alternative is rejected against a stated criterion) and **Confirmation** (how conformance with the decision will be verified) — which it includes when they earn their place and drops otherwise. It pushes back on hand-wavy sections rather than accepting them:

- **Context with no listed constraints** → the skill asks what's actually constraining the choice. "We need a database" isn't context; "~10M records, query by `user_id` and time range, team of two who know Postgres" is.
- **Decision without a single declarative sentence at the top** → the skill asks you to write one. ("We will use Postgres as the primary data store for user activity.")
- **Consequences with only positives** → the skill asks what you're giving up. Honest negatives are what save the next person from re-litigating the choice.
- **Alternatives without rejection reasons** → the skill asks why each was rejected. One sentence each is enough; the point is to show future readers you *considered* the option they're about to suggest.

## Step 6 — Update the ADR index

The skill adds a row to `docs/adr/README.md` so the new ADR appears in the table.

## Step 7 — Get sign-off, then mark Accepted (or Rejected)

The skill leaves status as `Proposed` and tells you to flip it to `Accepted` once the decision-makers have signed off — usually in the same PR, sometimes in a follow-up commit. If the proposal is declined, mark it `Rejected` and keep the file: a recorded rejection stops the same option being re-proposed later. Once Accepted, the body is frozen. See the immutability mechanic below.

## The immutability principle

ADRs differ from wiki-style docs in one load-bearing way: **once accepted, the body is never edited.** This is what makes ADRs a durable record rather than a moving target.

The status field can move: `Proposed` → `Accepted` or `Rejected`, and an Accepted ADR later to `Deprecated` (the decision no longer applies and nothing replaces it) or `Superseded by ADR-NNNN` (a specific later ADR replaces it). The body text stays put. If the decision is reversed or revised, you write a *new* ADR that supersedes the old one, with explicit cross-references in both directions, and update the old ADR's `Status:` header — *header only, body untouched*. The old text remains visible as historical record; the new ADR carries the current reasoning.

This is the difference between an ADR and documentation. Documentation should match present truth; ADRs preserve why we *got here*.

## Variations

### Recording a decision made just now (the common case)

You're capturing the call before the details fade. The decision is fresh in everyone's head; the skill's pushback on hand-wavy sections costs the least here. Invoke right after the meeting where the choice landed.

### Recording a decision made months ago

A maintainer joins, asks "why are we doing it this way?" and there's no good answer in writing. Open an ADR now anyway — backfilling is fine. Reconstruct Context from memory and Git history; list the `Decision-makers` as the people who actually decided (not you, unless you were in the room); note in `References` that the ADR is being backfilled. The content matters more than the freshness.

### Superseding an existing ADR

A previously-accepted ADR no longer reflects the team's call. You do *not* edit the old ADR's body. Instead:

1. Run `new-adr` for the new decision. In Context, name the prior ADR you're superseding and what changed since it was written.
2. Set the new ADR's frontmatter `Supersedes:` to the old ADR's number.
3. After the new ADR is Accepted, update the old ADR's frontmatter `Status:` from `Accepted` to `Superseded by ADR-<NNNN>` — with the actual four-digit number of the new ADR substituted in (e.g. `Superseded by ADR-0023`). Leave the old body alone — it's history.

If the reversal is contested or non-obvious, the reversal should go through an RFC first; the accepted RFC then produces this superseding ADR as follow-on. See [`docs/CONVENTIONS.md` § RFC](../../../CONVENTIONS.md#3-rfc--request-for-comments--docsrfc) for the trigger conditions.

### Originating from an accepted RFC

The RFC carried the debate; its accepted outcome lists "one or more ADRs to record the architectural decisions" as follow-on artifacts. Run `new-adr` per architectural decision named, cite the RFC in `Related:`, and let the RFC carry the prior-art and alternatives weight — the ADR's `Alternatives considered` can be terse when the RFC already exhausted them.

## Pitfalls

> **Treating an ADR as the place to debate.** ADRs are not the venue for open discussion — that's an RFC. If you find yourself writing "we should probably …" or "options to consider …", you wanted an RFC. Stop, open one, let it carry the debate.

> **Editing an accepted ADR's body.** The body is frozen at acceptance. Status-only changes (`Accepted` → `Deprecated` | `Superseded by ADR-NNNN`) are the only edits permitted. Anything else is a *new* ADR that supersedes.

> **Hand-wavy Alternatives.** "We considered other options but chose this" tells future readers nothing. One sentence per alternative with the actual rejection reason — that's the section that prevents the same option being re-proposed in six months.

> **Consequences with only positives.** Every decision has tradeoffs; an ADR that lists only upside isn't honest, and the next person will discount it. Push for at least one real negative or "to revisit" item.

> **An ADR for a single feature's internals.** That's a spec (`docs/specs/<feature>/`), not an ADR. ADRs are for cross-cutting architectural and infrastructural calls.

> **Packing several decisions into one ADR.** If a record carries three or more load-bearing sub-decisions, it's an umbrella — the skill pushes back and asks whether it should be an RFC that spawns several smaller ADRs. One ADR, one durable decision; *complete* is not *exhaustive*.

## When not to use this workflow

- **The decision is still being debated.** Use `new-rfc` — RFCs carry the debate; ADRs record the outcome. The accepted RFC then produces the ADR.
- **The decision is about a single feature's internals.** Use `new-spec` — feature-internal choices live in `docs/specs/<feature>/spec.md` under Boundaries or Testing Strategy.
- **The decision is trivial or has only one sensible option.** ("We use UTF-8.") No ADR needed. Don't manufacture decisions to document.
- **Documenting how something works today.** That's `docs/architecture/`, not `docs/adr/`. ADRs are *why* we made the call; `architecture/` is *what* the code looks like now.

## Related

- [How to propose a change (RFC)](new-rfc.md) — the inverse: when the decision isn't yet made, open an RFC.
- [How to plan and execute non-trivial work](../../core/how-to/plan-and-execute-non-trivial-work.md) — the spec/loop workflow for feature-shaped changes that aren't ADRs.
- [The core pack as a system](../../core/explanation/core-pack.md) — where ADRs sit in the wider doc hierarchy.
- [`new-adr` skill](../../../../packs/governance-extras/.apm/skills/new-adr/SKILL.md) — authoritative procedure (preconditions, template, pushback rules).
- [`new-rfc` skill](../../../../packs/governance-extras/.apm/skills/new-rfc/SKILL.md) — authoritative procedure for the proposal skill.
- [`docs/CONVENTIONS.md` § ADR](../../../CONVENTIONS.md#2-adr--architecture-decision-records--docsadr) — the immutability rule, status values, when-to-write tests.
- [`docs/CONVENTIONS.md` § Document lifecycle](../../../CONVENTIONS.md#document-lifecycle) — living vs. frozen vs. governance; ADRs are why the living layer can stay honest about the present.
