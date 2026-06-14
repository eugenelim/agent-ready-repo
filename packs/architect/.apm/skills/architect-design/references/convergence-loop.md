# Convergence loop — converge a design against review, in conversation

After the full design doc is drafted, `architect-design` does not stop at a
one-shot draft. It *converges* the doc: obtain a review pass, fix the mechanical
findings itself, re-review, repeat — then surface only the real decisions to the
human. This is a **pure-prose, in-conversation procedure**. There is **no
script, no state file, no `loop-cohort`** — the loop is bounded by these
instructions and stasis-checked by the agent re-reading its own prior findings.
A script would forfeit the pack's pure-markdown, zero-config, portable property.

## The cycle

1. **Review.** Obtain review findings against the drafted doc (see *Where the
   review comes from* and *Reviewer independence* below). Each finding is tagged
   **mechanical** or **judgment** (the taxonomy lives in `architect-review`'s
   `rubric-well-architected.md`; when reviewing against the embedded self-check,
   apply the same test — see below).
2. **Auto-resolve the mechanical findings.** A mechanical finding has a fix fully
   determined by the pillar spine or a stated constraint, with no business-value
   or risk-acceptance choice. Revise the doc to fix every mechanical finding
   **without asking** — labelling an unlabeled trust boundary, adding a missing
   response-measure that a stated SLO determines, naming an undocumented but
   already-decided tradeoff.
3. **Re-review.** Run the review pass again on the revised doc.
4. **Repeat** until no mechanical findings remain *or* the pass cap is reached.
5. **Surface the judgment findings** to the human as an explicit decision list —
   never resolve them silently.

## Never auto-resolve a judgment finding

A **judgment** finding requires choosing between defensible options — a tradeoff,
a risk acceptance, or an assumption resting on low-confidence / leading-edge
evidence. The loop **never** auto-resolves one. It collects them and presents
them to the human as a decision list ("here are the calls only you can make:
self-host inference vs. external LLM API; how much availability before launch;
…"). Auto-"fixing" a judgment finding by silently picking a side is the single
worst failure this loop can have — it hides the real architecture in a diff.

## Termination — the loop must stop

Two independent guards, both required:

- **Pass cap.** A fixed maximum of review passes (default **three**). When the
  cap is hit, stop looping and surface whatever remains as decisions — do not
  keep grinding.
- **Stasis escape.** If a finding tagged *mechanical* **survives a pass** —
  i.e. the same mechanical finding reappears after you tried to resolve it — the
  rubric could not determinately fix it. Stop trying: **escalate it to the human
  as a judgment finding** rather than looping on it indefinitely. A mechanical
  finding that won't resolve is, in practice, a judgment call in disguise.

To check stasis you re-read your own prior findings: compare this pass's findings
to the last pass's. A finding present in both, after a fix attempt, trips the
escape — **but first confirm the fix was actually applied to the doc**. A finding
that re-surfaces only because the reviewer re-flagged something already resolved
(not because its value is underivable) is dropped, not escalated; this matters
most on the degraded path, where the same self-check both produces and re-checks.
(This is the prose analogue of fingerprint stasis — done by reading, not by a
state file.)

## Reviewer independence

A review of your own fresh draft, in the same context that authored it, marks its
own homework — `architect-review`'s standing anti-pattern. Honor it with an
isolation ladder, strongest first:

1. **Fresh context (preferred).** The architect pack's `design-reviewer`
   subagent where installed, a new session, or the harness's review subagent
   where it has one. The reviewer has not seen the authoring.
2. **Cold re-read (floor).** Where fresh context is unavailable, do a disciplined
   cold re-read that **sets aside the authoring rationale** and reads the
   artifact as if encountering it for the first time. This is **explicitly weaker
   isolation** than a fresh context — name that it's the floor, not parity.

In **every** case, seed the reviewer with the **artifact + the agreed concept +
the constraints** — never the authoring chain-of-thought. Independence must not
mean reviewing blind: the reviewer needs the concept and constraints to judge
fit, but not the narrative of how the draft was reached (that narrative is what
biases it toward agreeing).

## Where the review comes from — degrade gracefully

- **`design-reviewer` subagent installed (preferred)** → dispatch it as a
  forked-context review — rung 1 of *Reviewer independence* above — seeded with
  the artifact + concept + constraints (never the authoring chain-of-thought).
  It returns the verdict + severity- *and* mechanical/judgment-tagged findings
  this loop consumes, in genuine isolation from the context that authored the
  draft. This is the strongest source; prefer it when available.
- **`architect-review` installed** → obtain the review from its well-architected
  / lens mode (it returns severity- *and* mechanical/judgment-tagged findings —
  the signal this loop consumes). Same rubric as the subagent, but in-thread —
  use the strongest isolation available per the ladder above.
- **`architect-review` not installed** → loop against `architect-design`'s own
  **embedded rubric self-check**: walk `design-doc-rubric.md` and
  `nfr-checklist.md`, plus the WA references (`well-architected-pillars.md`,
  `tradeoffs-and-sensitivity.md`, `quality-attribute-scenarios.md`), and apply
  the same mechanical-vs-judgment test to each gap you find. The loop is **never
  a hard dependency** on the second skill — it does not error or require it, it
  degrades.

The mechanical-vs-judgment test, restated for the degraded path: a gap is
**mechanical** when its fix is fully determined by the spine or a stated
constraint with no business/risk choice; **judgment** when resolving it needs a
choice between defensible options. Auto-resolve the former; surface the latter.

## Use, don't recite

Run the loop as far as it converges — often one or two passes is enough. Don't
manufacture findings to justify a third pass, and don't skip surfacing the
judgment decisions because the doc "looks done." The decisions are the point.
