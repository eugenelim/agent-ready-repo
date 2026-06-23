---
name: decision-archaeology
description: Reconstruct the rationale for a past decision by walking time-ordered artifacts (commits, PRs, design docs, chat logs, internal memos). Self-contained — does not invoke `/source-map` or other research-pack skills, because the source surface is time-ordered and internal, and authority is established by an artifact's place in the history rather than by external curation. Produces `<topic-slug>-archaeology.md` with chronology, the rationale chain, the alternatives that were considered and rejected, and a revival check flagging rejected alternatives whose original rejection rationale no longer holds. Depth cues — `quickly`, `top three`, `briefly`, `summary only` for the main rationale chain; `comprehensively`, `exhaustively`, `in depth`, `extensive` for branch alternatives and dead ends.
---

# /decision-archaeology

Reconstructs *why* a past decision was made by following its
artifact trail in chronological order.

## When to invoke

- "Why did we choose X over Y?" type questions.
- Pre-refactor work — before changing a decision, understand it.
- Post-incident — the decision predates the people on call.
- Not for forward-looking decisions — those go to
  `/compare-hypotheses`.

## Self-contained orchestration

This skill is **self-contained**. It does not invoke `/source-map` or
any other research-pack skill. The reason is methodological, not
incidental:

- The source surface for archaeology is **time-ordered**: commits,
  PRs, design docs, memos, chat archives, dated incident reports.
- Internal artifacts dominate; external curation is mostly absent.
- Authority is established by an artifact's place in the history (who
  signed off, when, in what context), not by the external-authority
  conventions `/source-map` is built to discover.

The skill `does not invoke` `/source-map` because applying `/source-map`'s
authority-curation discipline to a time-ordered internal trail would
produce miscategorisation: a junior engineer's PR comment can be the
decisive primary source, and a senior architect's design doc can be
the document that the team ignored.

## Methodology

Rationale reconstruction has three converging disciplines:

1. **Chronology** — order the artifacts by timestamp, not by
   importance. The order of events explains the decision; reordering
   by salience loses it.
2. **Rationale chain** — each artifact links to a "because" that
   points back to an earlier artifact or an external constraint. Trace
   the chain.
3. **Alternatives-considered** — record what was rejected, and why,
   from the artifacts. Decisions that don't name their alternatives
   are weaker decisions.

## Procedure

1. **Identify the decision** — the change, the doc, the commit that
   embodies the decision. This is the *terminal* artifact.
2. **Walk backwards** — use Read, Grep, Glob on local artifacts; use
   `source-extractor` subagent on URL-bearing artifacts (linked
   issues, external docs).
3. **Build chronology** — strictly time-ordered list of relevant
   artifacts.
4. **Extract rationale per artifact** — what changed, why, what was
   rejected, who signed.
5. **Surface alternatives-considered** — the rejected branches deserve
   their own section.
6. **Run the revival check** — for each rejected alternative, ask
   whether *the rationale that rejected it still holds today*. A
   rejection is never an unconditional verdict: it was conditional on
   the constraints at decision time (the library didn't exist, the team
   was too small, the latency budget was tighter, the cost was
   prohibitive). When a constraint that drove the rejection has since
   changed, the rejection is **stale** and the alternative is a
   **revival candidate**. See *The revival check* below. This is the
   payoff of recording *why* each alternative was rejected: a rationale
   you can name is a rationale you can later audit against the present.
7. **Write `<topic-slug>-archaeology.md`**. No `<topic-slug>-sources.md` is
   produced. `<topic-slug>` is the kebab-case topic slug; the naming rule lives
   in the `/research` skill body (§ Typed, topic-named artifacts).

## `<topic-slug>-archaeology.md` output schema

```markdown
# Decision archaeology — <decision name>

## Terminal artifact

- <commit / PR / doc> dated <date>. <One-paragraph summary of what it
  embodies>.

## Chronology

1. **<date>** — <artifact>. <One-sentence rationale>. Cited from:
   <path or url>.
2. **<date>** — <artifact>. (same shape).

## Rationale chain

- The decision rests on: <antecedent>.
- Which rested on: <prior antecedent>.
- Which rested on: <external constraint or first cause>.

## Alternatives considered

- **<alternative name>** — rejected at step <N>. Reason: <citation>.
- **<alternative name>** — rejected at step <N>. Reason: <citation>.

## Revival candidates

- **<alternative name>** — rejected because <original rationale>. That
  constraint has changed: <what changed, with a citation or dated
  signal>. The original reason no longer holds, so this is a candidate
  to reconsider. (Not a recommendation to adopt it — only a flag that
  its rejection is stale.)

## Open questions

- <a rationale link the artifact trail does not actually establish>.
```

The revival check is **distinct from** the alternatives-considered
record above it. Alternatives-considered is the *historical* record —
what was rejected and why, as of the decision. The revival check is a
*forward-looking* audit of that record against today's constraints: it
reads each historical rejection rationale and asks whether it survived.
An alternative that was rejected for a reason still true today does
*not* become a revival candidate; only one whose rejection rationale has
been overtaken by a changed constraint does.

## Citation discipline

Every chronology entry carries a citation (the path, the URL, the
commit hash). Inferred rationales — where the artifact does not state
the "because" outright — are marked `[inference]`. Cross-artifact
syntheses are marked `[synthesis]`.

## Depth cues

- `quickly`, `top three`, `briefly`, `summary only` — return the main
  rationale chain only; skip alternatives-considered and the revival
  check.
- `comprehensively`, `exhaustively`, `in depth`, `extensive` — walk
  branch alternatives and dead ends; surface artifacts that
  influenced the decision indirectly; include rejected drafts; run the
  revival check over every rejected alternative.
