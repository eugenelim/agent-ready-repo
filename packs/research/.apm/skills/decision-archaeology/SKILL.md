---
name: decision-archaeology
description: Reconstruct the rationale for a past decision by walking time-ordered artifacts (commits, PRs, design docs, chat logs, internal memos). Self-contained — does not invoke `/source-map` or other research-pack skills, because the source surface is time-ordered and internal, and authority is established by an artifact's place in the history rather than by external curation. Produces `archaeology.md` with chronology, the rationale chain, and the alternatives that were considered and rejected. Depth cues — `quickly`, `top three`, `briefly`, `summary only` for the main rationale chain; `comprehensively`, `exhaustively`, `in depth`, `extensive` for branch alternatives and dead ends.
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
6. **Write `archaeology.md`**. No `sources.md` is produced.

## `archaeology.md` output schema

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

## Open questions

- <a rationale link the artifact trail does not actually establish>.
```

## Citation discipline

Every chronology entry carries a citation (the path, the URL, the
commit hash). Inferred rationales — where the artifact does not state
the "because" outright — are marked `[inference]`. Cross-artifact
syntheses are marked `[synthesis]`.

## Depth cues

- `quickly`, `top three`, `briefly`, `summary only` — return the main
  rationale chain only; skip alternatives-considered.
- `comprehensively`, `exhaustively`, `in depth`, `extensive` — walk
  branch alternatives and dead ends; surface artifacts that
  influenced the decision indirectly; include rejected drafts.
