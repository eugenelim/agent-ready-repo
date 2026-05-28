# Confidence schema

Every finding in a `/research` standard or deep artifact carries a
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

Every finding line in `research.md` ends with a literal tag from the
closed set, in square brackets:

```
- Finding: X is the way Y is typically configured in Z deployments. [high]
- Finding: X performs Y% better than W on benchmark Z. [moderate]
  Downgrade: single source.
- Finding: X is the most adopted approach in 2026. [low]
  Downgrade: vendor-blogged; no peer review.
```

## Worked example: `/devils-advocate` proposing a downgrade

Suppose `research.md` contains:

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

`/devils-advocate` proposes the downgrade in `counterpoints.md`:

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
