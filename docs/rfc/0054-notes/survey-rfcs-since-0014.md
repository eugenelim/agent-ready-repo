# Survey: how RFCs have read since RFC-0014

> Promoted research backing RFC-0054. This is the audit trail; the RFC body
> carries only the conclusions. RFC-0014 made a falsifiable bet — "watch the
> next 2–3 real RFCs and cut what reads as ceremony" — so the case for
> reopening its cuts has to be *evidence*, not re-litigation. This file is that
> evidence.

Scope: RFCs ~0034–0053 in `docs/rfc/`, plus `docs/rfc/README.md` as a
standalone exhibit. All citations `file:line` relative to `docs/rfc/`.

## Exhibit 0 — the index itself

`docs/rfc/README.md` is the most direct evidence. The title cells for RFCs
0048–0053 are each a full paragraph (0048's runs the better part of a screen).
The index that was supposed to be *scannable* is not. A reader cannot run their
eye down the Title column and learn what each RFC proposes; the title has become
the abstract.

## Q1 — titles that carry the whole abstract

Reading the `# RFC-NNNN: <title>` line of each RFC in range:

- **Short identifiers (good):** 0035 ("SSO-cookie auth for the atlassian pack"),
  0036 ("Markdown → Office publishing skills…"), 0038 ("Align the ADR template
  with MADR conventions"), 0046 ("Convenient install defaults…"), 0052
  ("Shared-prefix-aware multi-adapter install").
- **Abstract-carrying (the RFC-0014 anti-pattern — em-dash subtitle or `(… + …)`
  cramming 2–4 sub-claims into the title):** 0037, 0039, 0040, 0042, 0043, 0045,
  0048, 0049, 0050, 0051, 0053. Examples:
  - `0043:1` — "A product rung — two product-shaping altitudes above capability,
    and Level decoupled from Scale" (two distinct decisions in the title).
  - `0048:1` — "The autonomous product-team operating model — gate doctrine, the
    `experience` pack, and a child-effort roadmap" (three things).
  - `0053:1` — "the coordinator contract — `discovery-lead`, the typed sidecar,
    and the no-engine framing, confirmed by prototype" (four clauses).

Roughly **11 of 21** titles are abstract-carrying, and the pattern intensifies
in the later, larger RFCs (0048–0053 are uniformly multi-clause). The
short-title rule shipped in PR #423 (B-narrow) addresses the *guidance*; the
survey shows the *pull* toward abstract-carrying titles is strong enough that
guidance alone has not held.

## Q2 — decisions buried in prose, no reviewer orientation

Every standard-spine RFC puts decisions under `## The ask` as a numbered prose
list, inheriting RFC-0014's shape. The problem is not the numbering — it is that
each item is a dense paragraph mixing the decision, the recommendation, the
rationale, the decide-by, and the default, so a reviewer cannot scan
"what / recommended / what-changes / how-reversible" off the first screen.

Worst offenders:

1. **RFC-0040** (`0040-consolidated-pack-layout-config.md:28-60`) — **nine**
   decisions, several wrapping 4–6 lines; decision 7 (`:45-51`) is a single
   7-line sentence. No reversibility signal anywhere; "default if no objection:
   yes" repeated nine times is the only orientation cue.
2. **RFC-0048** (`0048-…:51-79`) — decision 1 (`:53-67`) runs ~15 lines and
   itself contains four sub-decisions before the `· decide-by` marker. A reviewer
   cannot tell where one decision ends and the next begins.
3. **RFC-0034** (`0034-pack-profiles.md:18-26`) — six decisions; decision 1
   (`:20`) buries the single call the author flags as "the proposal's weakest
   pillar" mid-paragraph behind the BLUF and a full SCQA block.

Contrast — the closest thing to a per-decision weight marker today is *ad-hoc
bold prose*: RFC-0052 (`0052:17`) — "**This one supersedes three Accepted ADRs,
so it needs an explicit Approver yes — it does not adopt by silence** (unlike
Decisions 1–2, 4–8)." It works, but it is improvised at an arbitrary location,
not a field a reader can rely on finding.

## Q3 — does every RFC read foundation-sized?

RFC-0014 promised the template would be "lighter for small, reversible RFCs." In
practice almost every standard-spine RFC carries the full heavy section set
regardless of stakes.

- **RFC-0038** ("Align the ADR template with MADR conventions") is a low-stakes,
  reversible field rename — the author says so (`0038:109-110`: the optional
  sections are deletable, "the only forced change is the status enum and the
  field rename"). Yet it carries a 3-row Options table *with a do-nothing row*
  (`:90-94`), a multi-bullet pre-mortem + falsifiable-assumption + drawback
  (`:100-112`), and an Evidence section (`:114-122`): **130 lines for a field
  rename.** Sections do not collapse to one-liners.
- **Only one RFC in range actually goes light:** RFC-0047-default
  (`0047-default-source-on-discovery-verbs.md`), **42 lines**, dropping the heavy
  spine for a bespoke lean set (`## The ask` → `## Decision` → `## Why this is
  safe` → `## Residual / accepted` → `## Scope` → `## Supersedes-in-part`). It
  proves the lean shape is achievable — and that it currently requires the
  author to **hand-improvise** it rather than the template offering it.

Line-count spread for reference: 0047-default 42 · 0038 130 · 0046 162 · 0052
183 · 0034 237 · 0043 360 · 0040 405 · 0053 574 · 0048 925.

## Q4 — reversibility / weight signals

No RFC signals its *own* stakes or reversibility as a structured field. Where
reversibility language appears it is either (a) the subject matter of the RFC
(0049's minimum-regret deploy carve; 0053 even *proposes* a `reversibility-class`
enumeration `reversible / costly-to-reverse / one-way-door` at `0053:357-359` —
for the runtime coordinator artifact, not the RFC template), or (b) ad-hoc bold
prose (0052:17; 0034:20). The vocabulary a weight/door field would need already
exists in-repo, fully specified — just not wired into the RFC template.

## What the survey supports

1. The short-title rule (shipped) is necessary but not sufficient — titles still
   carry the abstract under pressure.
2. Decisions are routinely un-scannable in the first screen → a reviewer brief
   and a decisions table earn their place on the heavy RFCs.
3. RFC-0014's "plain right-sizing guidance" bet did not hold: 1 of 21 RFCs went
   light, by hand-improvising. A structural weight signal that *licenses* the
   collapse is the missing mechanism.
