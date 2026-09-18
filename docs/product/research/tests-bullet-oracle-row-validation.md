# Tests-bullet oracle row — pre-change validation

Investigation only; the one change it recommends landed in the same commit as
this record. Every measurement and line number below describes the **parent
tree**, before that change. Two rules carry the argument, and their opening
words are stable where line numbers are not: the bolded **A claim about what a
check proves** (cited below as `:531`, now `:532`) and the plain-prose bullet
beginning "Carry mechanism, never a restatement of a criterion" (`:480`).
Adding the seam clause to that bullet shifted every later line down one.
This record exists so the next session does not re-derive it.

**Proposal under test.** Add one row to the pre-review walk at
`packs/core/.apm/skills/new-spec/SKILL.md:537`: *each `Tests:` bullet names the
production seam it exercises and the property it asserts, rather than a proxy
for it.*

**Verdict: split. Ship the seam half only; do not ship the property half.**

## Stage 0 — route check: (b), a downstream route exists

The premise "nothing today crosses a `Tests:` bullet against what its assertion
establishes" is false. Three routes exist, two of them at authoring time inside
the same numbered step (`5. Fill in the plan second`, lines 457-556) that the
walk belongs to.

| Route | Location | Fires at | Covers |
| --- | --- | --- | --- |
| Oracle-vs-proxy labelling | `packs/core/.apm/skills/new-spec/SKILL.md:531` | Authoring | The property half |
| Mechanism naming | `packs/core/.apm/skills/new-spec/SKILL.md:480` | Authoring | Suite, location, fixture, moved assertion — **not** the production seam |
| Test-strength judgement | `packs/core/.apm/agents/quality-engineer.md:164` | Review | Tautology, mock shape, mirrors, whether a test can fail |

The `:480` row is the gap this commit closes: the rule beginning "Carry
mechanism, never a restatement of a criterion" now names the production seam
too, so the row records the problem, not the shipped state.

Line 531 reads: "A claim about what a check proves names the comparison its
oracle performs. Where the oracle cannot perform it, name the proxy instead of
claiming the stronger property." It was added 2026-09-11 in
`95754ea45` (#1274) — **after** the 2026-08-11 spec whose review rounds supplied
the motivating findings. The repository already shipped a repair for this class.

`packs/core/.apm/agents/quality-engineer.md:164` and
`packs/core/.apm/agents/adversarial-reviewer.md:194,320` both state that
quality-engineer **exclusively** owns test strength. A property-strength row on
the authoring walk would create a second owner for a judgement the core pack
twice assigns exclusively.

## Challenge set correction — 2 of 4, not 4 of 4

Only two of the four cited findings are test-oracle defects:

- **Are.** Round 3 "safe-path tests assert quote shape instead of argv
  preservation" (weak assertion). Round 4 "hostile-path test bypasses the
  production dependency-hint builder" (bypassed production seam).
- **Are not.** Round 3 "dependency remediation still shell-interpolates the
  resolved install path" is a production security defect in
  `packs/converters/.apm/skills/markdown-to-html/scripts/render.js`. Round 5
  "evals still positively require bare `npm install`" is a shipped-artifact
  inconsistency plus a too-narrow regex. No `Tests:`-bullet row reaches either.

The churn argument for this row therefore rests on two findings, not four.

## Stage 1 — corpus calibration: the mechanizable half is not lintable

Measured over 434 plans under `docs/specs/*/plan.md`: 2,511 tasks, 2,146
`Tests:` fields, 6,965 `Tests:` bullets. (The handover's 431/2,485/2,252 predate
recent merges; the drift is immaterial.)

Predicate: does the bullet cite a *production* path, module, or symbol in
backticks — distinguished from the test's own path, which line 480 already
obliges?

| Class | Bullets | Share |
| --- | --- | --- |
| Names a production seam | 2,941 | 42.2% |
| Backticked non-seam only | 1,771 | 25.4% |
| No code reference | 1,714 | 24.6% |
| Test path only | 539 | 7.7% |
| **Raw fail** | **4,024** | **57.8%** |

The 4,024 failures span 300 of those 434 plans; 15 were drawn at random from
the failures, so the sampling frame is failing bullets, not plans. All 15 are
dispositioned: **8** are strong oracles that name their property precisely but
carry no backticked production token — false positives; **3** are genuinely
weak; **2** are manual-QA or judgement records that no mechanical predicate
governs; and **2** are thin but precise, defensible either way.

So 3 of 15 are clear true positives and 4 more are arguable. Counting only the
3 gives 20% precision; counting the 4 arguable items in as well gives 47%. That
**20-47%** spread is the strict-versus-lenient disposition of these same 15
items — it is not a confidence interval, and it does not bound true precision,
which a 15-item sample cannot pin down. The corresponding genuine failure rate
is 12% to 27% of all bullets on the same two counting rules.

The most precise oracle bullet in the sample fails the predicate. It reads: "the
oracle is that git is never invoked, not that the result is empty, since an
empty result..." — an explicit oracle statement that rejects its own proxy.

**Consequence: do not build a lint for this.** It would fire on 4,024 bullets,
and on both counting rules above most of those are false positives. As a walk
row phrased mechanically it would be the noise authors learn to ignore.

## Stage 2 — void as designed; replaced with a premise audit

The paired ablation cannot run as specified. Arm A was to carry "the current
walk text verbatim" with a mechanical check that the brief contains none of the
new row's distinctive wording. That check fails at dispatch: line 531 sits in
the same step as line 537, so the control arm already contains an oracle route —
the exact condition that produced the previous null result.

Substituted a two-worker audit of the load-bearing premise, asking whether 480
and 531 already oblige what the row would add. Briefs identical; foreground;
stdin closed; both reports verified non-empty.

- `gpt-5.6-sol` (high): "Neither reaches F2. R531 governs what an oracle proves,
  R480 governs what test mechanism the plan records; neither requires exercising
  the production seam." Verdict GENUINE ADDITION.
- `claude-opus-5`: "Neither reaches it... R480 names fixture identity but never
  requires the fixture to enter through the production seam." Verdict PARTIALLY
  REDUNDANT — "trim the row to the seam obligation and let R531 keep the
  property side."

Both premises were re-read against the source text before adoption. Confirmed:
480 names suite, location, fixture, and moved assertion, and never a production
seam; 531 is conditional on a volunteered claim and permits an honestly-labelled
proxy.

## What follows

1. **Seam half — genuine gap.** No authoring-time rule obliges a `Tests:` bullet
   to name the production seam the check drives. This is the round-4
   defect class. It is mechanism naming, so its natural home is line 480, which
   already owns the mechanism list, rather than a new row on the walk.
2. **Property half — do not ship.** Line 531 owns it, and duplicating it
   contradicts both 480's own anti-duplication clause and the walk's "no
   condition has two homes".
3. **No lint.** Stage 1 settles this: a gate would fire on 4,024 bullets, and
   on both of Stage 1's counting rules most of those are false positives. The
   judgement half is not mechanizable at all.
