# Confidence schema

Every finding in a `/desk-research` standard or deep artifact carries a
confidence rating from the closed set below. Ratings are not asserted
— they are computed against named downgrade factors, in the GRADE
tradition.

## Levels

| Level | Meaning |
|---|---|
| `high` | Multiple independent primary sources converge. No substantive contradicting evidence. The finding is the way authoritative material describes the topic. |
| `moderate` | Independent sources converge but at least one downgrade factor applies. The finding is well-supported but contested or partially-sourced. |
| `low` | Single source, or multiple non-independent sources, or substantive contradicting evidence. The finding is plausible but should be treated with caution. |
| `uncertain` | Evidence is thin, conflicted, or absent. The finding may be inference from adjacent material; no defensible rating above this level is available. |

## Downgrade factors

A `high` rating downgrades by one level for each of the following that
applies. Downgrade factors are **named explicitly** in the finding's
artifact entry; a silent downgrade is a defect.

| Factor | Meaning |
|---|---|
| `single source` | The claim rests on one citation, even if that citation is primary. |
| `no peer review` | The claim's sources are not peer-reviewed (preprints, blog posts, internal memos) and the field has peer-reviewed alternatives. |
| `vendor-blogged` | The claim's sources are vendor blog posts or marketing material about the vendor's own product. |
| `contested-in-field` | The claim is actively contested by credible counter-positions; `/devils-advocate` surfaced substantive evidence-against. |
| `heterogeneity` | The cited sources do not agree with each other on the claim's specifics, even if they agree on the headline. |
| `indirectness` | The cited sources do not address the exact question; they address an adjacent question and the finding extrapolates. |

A finding that would otherwise rate `high` but has one downgrade
factor lands at `moderate`. Two factors → `low`. Three or more → 
`uncertain`.

## Tagging in artifacts

Every finding line in `<topic-slug>-survey.md` ends with a literal tag from the
closed set, in square brackets:

```
- Finding: X is the way Y is typically configured in Z deployments. [high]
- Finding: X performs Y% better than W on benchmark Z. [moderate]
  Downgrade: single source.
- Finding: X is the most adopted approach in 2026. [low]
  Downgrade: vendor-blogged; no peer review.
```

## Worked example: `/devils-advocate` proposing a downgrade

Suppose `<topic-slug>-survey.md` contains:

```
- Finding: vector databases outperform traditional databases for
  similarity search at scale. [high]
  Sources: [peer-reviewed VLDB paper], [SIGIR benchmark paper],
  [conference talk from an independent practitioner].
```

`/devils-advocate` runs against this artifact. It retrieves
counter-evidence:

- A discussion in the SIGMOD community where two authors disagree on
  what "at scale" means — surfacing the `contested-in-field` factor
  the original analysis did not account for.

`/devils-advocate` proposes the downgrade in `<topic-slug>-counterpoints.md`:

```
## Finding: vector databases outperform traditional databases for
similarity search at scale.

- **Counter-position:** "at scale" is contested in the field; the
  SIGMOD discussion thread surfaces credible disagreement.
- **Counter-evidence:** [SIGMOD discussion].
- **Proposed rating change:** `[high]` → `[moderate]`.
  Reason: `contested-in-field`.
```

Applying the rule mechanically: one new downgrade factor
(`contested-in-field`) steps the rating one level down, from `[high]`
to `[moderate]`. If a follow-up pass surfaced a second factor (e.g.,
`heterogeneity` between the cited benchmarks on what "at scale"
measures), the rating would step down another level to `[low]`,
matching the rule's "two factors → `low`" arithmetic.

This is the discipline GRADE encodes: ratings are computed, not
asserted, and a downgrade names its reasons.

## Applied-mode overlay

The base schema above is calibrated for academic / primary-source
research. When `/desk-research` runs in **applied mode** (prior-art /
best-practice surveys across practitioner grey literature — blogs,
conference talks, vendor case studies, community threads), the
discipline is different: there is no peer-reviewed alternative by
construction, so applying `no peer review` as a downgrade factor
would poison every finding to `[low]` for the wrong reason. The
applied-mode overlay amends the base schema specifically for these
invocations.

### Selector contract

The `mode` parameter is the load-bearing selector. When `/desk-research`
is invoked with `mode: applied` (per its SKILL.md), the overlay below
applies at confidence-rating time — and `/desk-research` writes the
canonical discipline marker `> Discipline: applied (practitioner-
pattern survey)` as the first non-heading line of `<topic-slug>-survey.md`. The
marker is the **post-condition audit signal** recording that the
overlay fired into the produced artifact; it is NOT the precondition
selector. **Manually adding the marker to an existing standard-mode
artifact does not retroactively re-rate findings under the overlay** —
the overlay applies at write time, not at read time. The mode
parameter is the selector; the marker is the audit signal; the two
are not interchangeable.

### Amendments to the base schema

The overlay applies two amendments:

1. **`no peer review` is NOT a downgrade factor in applied mode.** The
   practitioner / grey-literature domain has no peer-reviewed
   alternative by construction (blogs, vendor docs, conference talks,
   community threads). The factor is dropped from the closed
   downgrade-factor set when the overlay is selected. Note that the
   base schema still names `no peer review` (above) for standard /
   deep mode — only applied mode drops it.

2. **Two new downgrade factors join the closed set in applied mode:**
   - `survivorship bias` — only the successes get blogged. Failed
     adopters of a pattern rarely write post-mortems; the cited
     practitioner literature systematically under-represents the
     failure stories. Apply this factor when the cited evidence is
     entirely "what worked" with no post-mortem / retro / "we tried
     this and it broke" balance.
   - `stale prior art` — a pattern from >5 years ago in a fast-moving
     domain (LLM tooling, frontend frameworks, observability stacks)
     may have been superseded. Apply this factor when the cited
     evidence's most-recent primary source predates the current
     generation of tools by enough that the practice the field
     follows today is materially different. Slower-moving domains
     (compiler theory, database fundamentals) carry no such penalty.

The step-down arithmetic is unchanged: one factor → one level down
from `[high]`. Two factors → two levels. Three or more → `[uncertain]`.

### Worked example: `/devils-advocate` flagging `survivorship bias` against an applied-mode finding

Suppose an applied-mode `<topic-slug>-survey.md` for "best practices for
warehouse picking optimisation" contains:

```
> Discipline: applied (practitioner-pattern survey)

# Best practices for warehouse picking optimisation

## Findings

- Finding: cluster picking with handheld voice-direction improves
  pick rate by 30-50% versus paper pick lists in mid-size DCs. [high]
  Sources: [vendor case study A], [logistics blog B], [conference
  talk C — all reporting successful adoptions].
```

`/devils-advocate` runs against this applied-mode artifact. It
retrieves counter-evidence:

- A r/logistics thread of post-mortems from adopters who reverted
  voice-direction back to paper pick lists after the productivity
  numbers didn't survive the second quarter.
- A Modern Materials Handling retrospective on failed RF / voice-
  picking rollouts.

`/devils-advocate` proposes the downgrade in `<topic-slug>-counterpoints.md`:

```
## Finding: cluster picking with handheld voice-direction improves
pick rate by 30-50% versus paper pick lists in mid-size DCs.

- **Counter-position:** the cited sources are all successful-adoption
  stories. Failed adopters exist, in volume, with the productivity
  gain failing to survive past the implementation honeymoon.
- **Counter-evidence:** [r/logistics post-mortem thread], [Modern
  Materials Handling retrospective on failed rollouts].
- **Proposed rating change:** `[high]` → `[moderate]`.
  Reason: `survivorship bias` (no post-mortem / failed-adopter
  evidence cited in the original synthesis).
```

The downgrade is `[high]` → `[moderate]` — one applied-mode overlay
factor (`survivorship bias`) takes the rating one level down. The
overlay's worked example demonstrates the discipline GRADE encodes
(ratings are computed, downgrades name their reasons) applied to the
practitioner-pattern surface where it matters most: the cited
literature systematically over-represents successes.
