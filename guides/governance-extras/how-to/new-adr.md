---
title: "How to record a decision with an ADR"
summary: "Record an architectural decision with a durable tradeoff, sequential identifier, and index entry."
pack: governance-extras
kind: how-to
---

# How to record a decision with an ADR

**Use this when:** You've made (or are formally proposing) an architectural decision with a concrete tradeoff and need it durably recorded in the repository's decision-record surface.
**Prerequisites:** `governance-extras` pack installed and a decision that is architectural in scope, made, and has a real tradeoff — see [Prerequisites](#prerequisites) below.
**Result:** A confirmed ADR file in the resolved decision-record destination with its row added to that destination's index, ready for sign-off and acceptance.

You made an architectural call — a database choice, a process commitment, a structural rule the team will live with — and the next person to ask "why did we do it this way?" deserves an answer in writing. The `new-adr` skill first resolves the portable `decision-record` destination, then drafts an Architecture Decision Record there from the bundled template with that destination's next sequential number. It pushes back on hand-wavy sections before you commit.

```text
Use the new-adr skill to write an ADR for choosing PostgreSQL for the order service.
```

This guide is task-oriented; for the *why* of ADRs (immutable history vs. living docs), read [§ What an ADR records](#what-an-adr-records). For where ADRs sit in the wider doc system, see [the core pack as a system](../../core/explanation/core-pack.md).

## ADR or RFC?

The two skills look adjacent and confuse readers regularly. The split is about *time*, not topic:

| Property | ADR (`new-adr`) | RFC (`new-rfc`) |
| --- | --- | --- |
| Direction in time | Backward-looking record | Forward-looking proposal |
| State of the decision | Made (or about to be made) | Under debate; may be rejected |
| After acceptance | Prose frozen at acceptance; `Status`, the supersession fields, and `Areas` stay open (see [the mutability zones](#the-mutability-zones)) | Body frozen at acceptance (status field mutable); spawns ADRs, specs, convention edits |
| Change mechanism | New ADR that *supersedes* the old; status of the old flips, body stays | Normal revision until accepted, frozen thereafter |

If the call is already made (or you're recording one made in a meeting yesterday), it's an ADR. If you want a debate, it's an RFC — and the *accepted* RFC then produces one or more ADRs as follow-on. See [how to propose a change (RFC)](new-rfc.md) for the inverse view.

## Prerequisites

:::note
**Pack:** `governance-extras`. `new-adr` does not ship in `core`. Verify with `ls .claude/skills/new-adr/` (or the equivalent skill registry in your IDE — Claude Code's `/agents`, Cursor's Composer, etc.). If the directory is missing, install or enable `governance-extras` first.
:::

- A repository destination that Core can resolve for `decision-record`,
  including an explicit policy-permitted destination supplied as resolver
  evidence. Existing custom locations win; `docs/adr/` is a fallback offer and
  is never created silently. Without compatible Core, the skill returns a
  zero-write handoff even when you confirm its evidence.
- A decision that genuinely warrants an ADR — the entry-point prose below covers the test.

## What to bring

Bring the upstream material that informed the decision: a shaped intent from
`docs/product/intents/`, a decision brief, a research survey or brief, or an
architecture concept or reference architecture. Cite that artifact in the ADR;
the citation is what makes the decision traceable later.

## When is `new-adr` the right call?

Three conditions, all must hold:

1. **The decision is about architecture or shared infrastructure**, not one feature's internals. ("We use Postgres for the primary store" is an ADR; "the saved-filters chip uses URL state, not local storage" is a spec.)
2. **The decision has been made** (or is being formally proposed for acceptance). ADRs are not the venue for open-ended discussion — that debate belongs in an RFC.
3. **There is a concrete tradeoff.** At least one viable alternative was considered. If only one option exists ("we use UTF-8"), you don't need an ADR.

If any of these fails, push back rather than writing an ADR that future readers will discount. The skill checks them at invocation time.

:::tip
**Invoke skills by name.** Claude Code's description-based auto-discovery is best-effort — natural phrasings like "let's ADR this" usually fire the right skill, but not always. **Naming the skill in your request guarantees it fires.** Use `use the new-adr skill to …` whenever you want the discipline, including on edges where description matching wouldn't pick it up.
:::

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

## Step 3 — Resolve the destination, then find its next ordinal

Before it reads an ADR directory or chooses identity, the skill asks compatible
Core for `semantic-surface-resolution.v1` with role `decision-record`. The
resolver honors an explicit permitted destination, repository policy or
configuration, established repository convention, and established external
destination—in that order—then stops for ambiguity or offers selection/creation
on absence. Mandatory policy rejects a conflicting explicit path. One example
does not establish a convention, and no terminal result creates a directory,
index, or configuration.

Only after a confined repository destination resolves does the skill run its
bundled `scripts/next-ordinal.py` helper against that directory. It prints the
next 4-digit ordinal—`0001` if the destination has no ADRs, max-plus-one
otherwise. Numbers are sequential within the resolved destination and never
reused. The helper parses the full digit prefix, so transitions like `0099` →
`0100` work correctly without manual zero-padding. When the destination sits in
a Git repository, the helper also counts ordinals already on the remote default
branch, so a long-lived branch stops proposing a number that merged upstream
while it waited. If Git is unavailable or the remote has not been fetched, it
falls back to the working tree alone rather than failing.

That number is a snapshot, not a reservation. Re-derive it immediately before
opening your pull request rather than when the branch starts: a collision with
a record someone else merged exists only against the default branch, so nothing
inside your branch — including review — can see it. The companion check reports
a directory where two records already share an ordinal:

```bash
python3 scripts/next-ordinal.py --check docs/adr
```

It exits non-zero on a collision, and also when it cannot inspect the directory,
so a mistyped path never reports clean. A `NNNN-notes/` folder or a
`NNNN-<slug>-research.md` sibling is a companion and shares its record's ordinal
by design, so neither is reported. Running this check wherever your project
gates a merge is what actually keeps ordinals unique. External destinations remain
external; without an authorized write adapter, the skill returns a portable
handoff instead of probing or writing them.

The skill then picks a short kebab-case filename from your description (`0007-primary-store-postgres-over-dynamodb.md`, not `0007-decision-about-the-database.md`). It **does not create the file yet**: it drafts the ADR, shows you a preview, and waits for your confirmation before writing anything (see [Preview and confirm](#preview-and-confirm) below). The H1 title inside names the problem and the chosen solution together (keeping the `ADR-NNNN` ordinal), so the decision reads clearly from the index. The skill keeps it **short** — the title *identifies* the decision rather than encoding the whole rationale (that lives in the Decision section); a title that compresses the whole argument into a clause makes the index hard to scan.

## Step 4 — Fill in frontmatter

Status starts as `Proposed`. Today's date. `Decision-makers` are the people who own the call, identified however your team does — a name, a GitHub handle, or an email (don't assume GitHub handles unless your conventions require them); add `Consulted` (whose input was sought, two-way) and `Informed` (who is kept up to date, one-way) when the decision was run past others, and delete those two lines otherwise. `Supersedes:` is `none` for a greenfield ADR; otherwise the ADR number being replaced (see Variations). Keep `Consulted` and `Related` **pointer-like** — short lists of handles and ADR/RFC/spec references. A `Related` entry takes a brief parenthetical saying what the relationship *is* (see the shape below); what it must not take is the argument for that relationship. A clause fits; a paragraph belongs in Context or References.

`Related:` is suggested, not checked: entries separated by `;`, each a bare ordinal or a `/`-joined pair — never a Markdown link — followed by a parenthetical gloss naming the relationship, with an em dash before a secondary clause, and no trailing period. For example: `RFC-NNNN` (the proposal this records); `ADR-NNNN` (the gate it rests on — the motivating evidence, and the split between what a scanner catches and what a reviewer catches); `ADR-NNNN / RFC-NNNN` (the modes this reuses).

## Step 5 — Draft the body sections

If your request arrives tangled — rationale, history, and several sub-decisions in one breath — the skill first reflects back a short **decision frame** (the decision in a sentence, the problem it resolves, the alternatives, the winning driver, what you're giving up) to isolate the call before drafting; when the decision is already crisp it skips the frame and drafts straight away. It then walks you through Context, Decision, Consequences, and Alternatives, and offers several optional fields — included when they earn their place, dropped otherwise:

- **Decision summary** — a first-screen TL;DR (Decision / Because / Applies to / Tradeoff accepted / Revisit if) placed before Context. The skill offers it once the ADR is long enough that the decision isn't visible on the first screen — a multi-line title, a paragraph of metadata, or a long Context push it down — and skips it on a short ADR, where the five restated lines would be pure redundancy. Every line restates the body, so it never carries new reasoning; when it's present, its `Revisit if:` restates the Consequences line verbatim.
- **Revisit if** — a named trigger in Consequences for when the decision should be reconsidered (a new constraint, a failed confirmation, a scale threshold). This is its canonical home, so it survives deletion of the optional summary; the skill recommends it for any decision likely to age, and writes the explicit `Revisit if: stable — no foreseeable trigger` for one that genuinely won't, rather than dropping the line.
- **Decision drivers** — the criteria the choice was judged against, so each alternative is rejected against a stated criterion rather than an ad-hoc reason.
- **Confirmation** — how conformance with the decision will be verified, structured as `Mode` / `Signal` / `Owner` (with `Mode` one of `reviewer-checked | lint/CI | architecture fitness test | periodic audit | none`). Where you'd plausibly expect a conformance mechanism, the skill prefers an explicit `Mode: none` with a one-line reason over silently deleting the section — a non-checkable residual stays visible — and drops the section only for trivial decisions where no one would expect a check.

None of these is mandatory. The skill pushes back on hand-wavy *required* sections rather than accepting them:

- **Context with no listed constraints** → the skill asks what's actually constraining the choice. "We need a database" isn't context; "~10M records, query by `user_id` and time range, team of two who know Postgres" is.
- **Decision without a single declarative sentence at the top** → the skill asks you to write one. ("We will use Postgres as the primary data store for user activity.")
- **Consequences with only positives** → the skill asks what you're giving up. Honest negatives are what save the next person from re-litigating the choice.
- **Alternatives without rejection reasons** → the skill asks why each was rejected. One sentence each is enough; the point is to show future readers you *considered* the option they're about to suggest.

## Step 6 — Update the ADR index

The skill regenerates the resolved destination's sibling index so the new ADR
appears in it, by running the bundled generator over that directory:

```bash
python3 "$SKILL/scripts/index-records.py" <adr-dir>
```

The index is derived from the records themselves, so it cannot drift from them.
Run the same command with `--check` to find out whether it would change.

## Step 7 — Get sign-off, then mark Accepted (or Rejected)

The skill leaves status as `Proposed` and tells you to flip it to `Accepted` once the decision-makers have signed off — usually in the same PR, sometimes in a follow-up commit. If the proposal is declined, mark it `Rejected` and keep the file: a recorded rejection stops the same option being re-proposed later. Once Accepted, four zones govern what can still change — see [the mutability zones](#the-mutability-zones) below.

## Preview and confirm

`new-adr` never writes silently. Before it creates the ADR file or touches the index, it shows you a preview — the proposed **identifier** (`ADR-NNNN`), the **status** (`Proposed`), the **target path** (absolute and repo-relative), the **index path** it will update, and the **drafted content** — and waits for your explicit confirmation. Nothing lands on disk until you approve. After it writes, it hands back a short **completion receipt**: the identifier, the file path, the index path, the status, the files changed, the owner (the decision-maker), and the next step — get sign-off, then flip to `Accepted`.

## The mutability zones

ADRs differ from wiki-style docs in one load-bearing way: **once accepted, the prose is frozen.** This is what makes an ADR a durable record rather than a moving target. Four zones divide a record by content, not by lifecycle — all four apply to every accepted ADR at once:

- **Live** — `Status`, the supersession fields (`Supersedes`, `Supersedes in part`, `Superseded by`, `Superseded in part`), and `Areas`. Lists gain entries and keep every entry they already had; `Status` is a state rather than a list, so it's replaced in place — `Proposed` to `Accepted` or `Rejected`, and later to `Deprecated` or `Superseded`.
- **Attested** — `Date`, `Decision-makers`, and `Reversibility`. Frozen: they record who decided what, when, and how they judged it at the time, so rewriting them falsifies the record instead of correcting it.
- **Frozen** — every prose section except `## Errata`.
- **Append-only** — `## Errata`. Entries may be added; an entry already present may not be removed or rewritten.

`Consulted` and `Informed` sit in no zone. The template lets you delete them when empty, and a field that may be absent can't be append-only — re-adding it later is exactly the line addition the sentinel values exist to avoid. So the four zones divide everything the record always carries, not literally every line in it.

If the decision is reversed or revised, you write a *new* ADR that supersedes the old one: set the new record's `Supersedes:` to the old one's number, and the old record's `Status:` to `Superseded` with its `Superseded by:` naming the new one — two mirrored fields, not a compound value on one line. The old prose stays untouched; the new ADR carries the current reasoning.

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
3. After the new ADR is Accepted, update the old ADR's frontmatter: set `Status:` to `Superseded`, and `Superseded by:` to the new ADR's number — with the actual four-digit ordinal substituted in. Leave the old body alone — it's history.

If the reversal is contested or non-obvious, the reversal should go through an RFC first; the accepted RFC then produces this superseding ADR as follow-on. See [`new-rfc.md` § The RFC lifecycle](new-rfc.md#the-rfc-lifecycle) for the trigger conditions.

### Originating from an accepted RFC

The RFC carried the debate; its accepted outcome lists "one or more ADRs to record the architectural decisions" as follow-on artifacts. Run `new-adr` per architectural decision named, cite the RFC in `Related:`, and let the RFC carry the prior-art and alternatives weight — the ADR's `Alternatives considered` can be terse when the RFC already exhausted them.

## Pitfalls

:::caution
**Treating an ADR as the place to debate.** ADRs are not the venue for open discussion — that's an RFC. If you find yourself writing "we should probably …" or "options to consider …", you wanted an RFC. Stop, open one, let it carry the debate.
:::

:::caution
**Editing an accepted ADR's prose.** The prose is frozen at acceptance — see [the mutability zones](#the-mutability-zones). Only `Status`, the supersession fields, and `Areas` stay open: `Status` is replaced in place (`Accepted` → `Deprecated` or `Superseded`, the latter paired with a `Superseded by:` entry). Anything else is a *new* ADR that supersedes.
:::

:::caution
**Hand-wavy Alternatives.** "We considered other options but chose this" tells future readers nothing. One sentence per alternative with the actual rejection reason — that's the section that prevents the same option being re-proposed in six months.
:::

:::caution
**Consequences with only positives.** Every decision has tradeoffs; an ADR that lists only upside isn't honest, and the next person will discount it. Push for at least one real negative or "to revisit" item.
:::

:::caution
**An ADR for a single feature's internals.** That's a spec (`docs/specs/<feature>/`), not an ADR. ADRs are for cross-cutting architectural and infrastructural calls.
:::

:::caution
**Packing several decisions into one ADR.** If a record carries three or more load-bearing sub-decisions, it's an umbrella — the skill pushes back and asks whether it should be an RFC that spawns several smaller ADRs. One ADR, one durable decision; *complete* is not *exhaustive*.
:::

## When not to use this workflow

- **The decision is still being debated.** Use `new-rfc` — RFCs carry the debate; ADRs record the outcome. The accepted RFC then produces the ADR.
- **The decision is about a single feature's internals.** Use `new-spec` — feature-internal choices live in `docs/specs/<feature>/spec.md` under Boundaries or Testing Strategy.
- **The decision is trivial or has only one sensible option.** ("We use UTF-8.") No ADR needed. Don't manufacture decisions to document.
- **Documenting how something works today.** That's the repository's resolved `current-architecture` surface, not its `decision-record` surface. ADRs are *why* we made the call; current architecture is *what* the implemented system looks like now.

## What you have now

You have a confirmed ADR in the resolved decision-record destination and a row
in its index. Seek acceptance for the record, then create a superseding ADR if
the durable decision changes.

## Related

- [How to propose a change (RFC)](new-rfc.md) — the inverse: when the decision isn't yet made, open an RFC.
- [How to plan and execute non-trivial work](../../core/how-to/plan-and-execute-non-trivial-work.md) — the spec/loop workflow for feature-shaped changes that aren't ADRs.
- [The core pack as a system](../../core/explanation/core-pack.md) — where ADRs sit in the wider doc hierarchy.
- [`new-adr` skill](../../../packs/governance-extras/.apm/skills/new-adr/SKILL.md) — authoritative procedure (preconditions, template, pushback rules).
- [`new-rfc` skill](../../../packs/governance-extras/.apm/skills/new-rfc/SKILL.md) — authoritative procedure for the proposal skill.
- [§ What an ADR records](#what-an-adr-records) — the mutability zones, status values, when-to-write tests.
- [`docs/README.md` § The three lifecycle classes](../../../docs/README.md#the-three-lifecycle-classes) — living vs. frozen vs. governance; ADRs are why the living layer can stay honest about the present.

## What an ADR records

> The `adr/README.md` index is generated from the records themselves, so it
> cannot disagree with them. Regenerate it rather than editing a row.

**What:** a record of a decision and the context that produced it, whose prose is
frozen after acceptance (see [the mutability zones](#the-mutability-zones)).
"We chose Postgres over DynamoDB because <reasons>, accepting <tradeoffs>."

**The key property of an ADR is that its prose is never edited after
acceptance.** `Status`, the supersession fields, and `Areas` can still change
— see [the mutability zones](#the-mutability-zones). If a decision is reversed
or revised, you write a new ADR that supersedes the old one: the old record's
`Status` becomes `Superseded` and its `Superseded by:` names the new one. The
old prose stays. This is the difference between an ADR and documentation: ADRs
are history.

**Filename:** `NNNN-kebab-case-title.md`, e.g. `0007-use-postgres-for-primary-store.md`.
Numbers are sequential and never reused.

**Status values:** `Proposed` → `Accepted` or `Rejected`. An `Accepted` ADR may
later become `Deprecated` (the decision no longer applies and nothing replaces
it) or `Superseded` (a specific later ADR replaces it, named in that record's
`Superseded by:` field). A `Rejected` ADR is kept as a record, never deleted.

**Template:** `assets/adr.md` in the `new-adr` skill that creates ADRs from it.

**When to write an ADR:**

- You're choosing between two or more reasonable options and the choice will
  be expensive to reverse.
- The reasoning involves tradeoffs a future maintainer (or agent) won't be able
  to reconstruct from the code alone.
- Someone asks "why did we do it this way?" and there's no good answer in
  writing.

**When NOT to write an ADR:**

- The decision is trivial or has only one sensible option ("we use UTF-8").
- The decision is about a single feature's internals — that's a spec, not an ADR.
- You're documenting how something works today — that's `architecture/`.

**Rule of thumb:** if you'd be annoyed to discover the decision was made without
discussion, write an ADR. If you'd shrug, don't.
