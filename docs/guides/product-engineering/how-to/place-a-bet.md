# How to place a bet

**Use this when:** You have evaluated your solution options and are ready to commit the team to a chosen direction and produce the `bet.md` artifact that `map-capabilities` will reason against.
**Prerequisites:** `product-engineering` pack installed; a solutions artifact from `diverge-solutions` or `explore-options` (recommended); `validation-notes.md` from `de-risk-intent` (optional but folds kill conditions in automatically).
**Result:** A committed `bet.md` at `<output_dir>/shaping/<slug>/bet.md` recording the chosen option, confidence, appetite, rationale, accepted risks, and assumptions — ready to anchor step 6.

**Goal:** You have evaluated options and completed (or deliberately skipped)
validation. You are ready to commit the team to a chosen direction and produce
the artifact `map-capabilities` will reason against.

**Skill:** `place-bet` (PE pack, user scope)

---

## When to use `place-bet` vs `de-risk-intent`

`de-risk-intent` (step 3.5) and `place-bet` (step 5) are sequential, not
alternatives. Run both when the bet rests on a fragile assumption worth testing
first; skip `de-risk-intent` when the risk is accepted rather than worth
investigating.

| Step | Skill | Purpose |
|---|---|---|
| 3 | `diverge-solutions` | Generate structured comparable options |
| 3.5 | `de-risk-intent` | Validate the riskiest assumption *before* committing |
| 5 | `place-bet` | Commit the chosen direction; produce `bet.md` |
| 6 | `map-capabilities` | Use `bet.md` as the anchor for capability mapping |

**Rule of thumb:** if you can articulate your chosen direction and name the
risks you are accepting, `place-bet` is ready. If a core assumption has not
been tested and the cost of a wrong bet is high, run `de-risk-intent` first.

---

## What inputs `place-bet` needs

The skill reads what it finds and accepts free-form otherwise:

1. **A solutions artifact** (optional but recommended) — any `*solution*` or
   `*options*` file under `<output_dir>/shaping/<slug>/`. This is typically
   the output of `diverge-solutions` or `explore-options`. If absent, the skill
   offers to run `diverge-solutions` and degrades to free-form if you decline.
2. **`validation-notes.md`** (optional) — the output of `de-risk-intent`, if
   you ran it. Read if present; never required. Kill conditions and risks found
   there are folded into the betting table automatically.

You do not need to have run `diverge-solutions` specifically. The skill accepts
options from any prior source — external research, workshop notes, informal
comparison, or an `explore-options` run.

---

## How to fill each betting table field

**option** — the chosen direction in one line. Name it specifically.
"Direct download with streaming" is better than "probably the streaming one."

**option-source** — where the option came from. A file path when the options
came from a structured artifact; `free-form` when you described them informally.
This is your traceability anchor: `map-capabilities` can trace back to the
options that were considered.

**confidence** — your honest confidence that this option will pay off: `high`,
`medium`, or `low`. A low-confidence bet with explicit risks-accepted is better
than a high-confidence bet that papers over uncertainty.

**appetite** — the time budget the team is willing to commit before reassessing.
Name a number rather than "open" when possible: "3 weeks" creates a forcing
function; "open" doesn't. Appetite is not an estimate — it is the boundary you
are placing on the bet.

**rationale** — why this option over the alternatives you considered. Reference
the options by name. One short paragraph is enough.

**risks-accepted** — an explicit list of known risks you are taking on. Fold in
anything from `validation-notes.md`. The point is not to eliminate risk — it is
to name it so it can be tracked and revisited.

**assumptions** — what must be true for this bet to pay off. A bet with clear
assumptions is easier to reassess when conditions change.

**kill-condition** (optional) — the signal that would reverse this decision.
Pull from `de-risk-intent` output when available. If not, leave it blank — the
field is optional. A kill condition is most valuable when confidence is medium
or low.

---

## How to hand the bet to `map-capabilities`

When `bet.md` is written, the skill prints a `workspace.toml` transition
suggestion — a TOML snippet you apply via `capture-work` or manual edit.

To hand off: run `map-capabilities` and point it to the committed bet at
`<output_dir>/shaping/<slug>/bet.md`. It will use the option, assumptions,
and next-step pointer as its anchor for the capability map.

---

## What happens if no solutions artifact exists

If no `*solution*` or `*options*` file is found at the shaping slug path, the
skill offers to run `diverge-solutions` first and names the impact: without
structured comparable options, the rationale and risks-accepted in the betting
table are less defensible.

You can decline and proceed with a free-form description of the options you
considered. The resulting `bet.md` will record `option-source: free-form` so
the absence of a structured artifact is visible in the audit trail.


---

## How to define a thin slice

The `thin-slice` field is required in `bet.md`. It is the minimum shippable
proof that the bet can be validated end-to-end — not a product tour, and not
"the happy path."

A valid thin slice has four components:

1. **One user** — a single, specific persona (not "users in general"). The
   more specific, the sharper the slice: "a first-time user on mobile" is
   better than "users."

2. **One real task** — a task the user genuinely needs to do, not a demo flow.
   "Complete a payment for the first time" is a real task; "explore the
   dashboard" is a tour.

3. **One meaningful result** — the outcome the user can see or has when the
   task succeeds. "A confirmation email arrives and the balance updates" is
   observable; "the user is happy with the experience" is not.

4. **One material failure + recovery** — name the failure that matters most
   (the one that happens most often or costs the most when it does) and how
   the user recovers from it. A thin slice with no failure path is incomplete.

5. **Instrumentation** — one named event that fires when the success condition
   is met. Not "we'll add analytics later" — name the event now.

### Example: weak thin slice

> "Users can create an account and see the dashboard."

This fails: it describes a product tour (create account → see dashboard),
names no failure scenario, and has no instrumentation event.

### Example: strong thin slice

> **User:** First-time user on mobile (iOS Safari).
> **Task:** Joins a workspace by accepting an email invite.
> **Result:** Lands on a workspace home screen with at least one channel visible.
> **Failure + recovery:** Invite link expired → lands on the "request a new invite" screen and can send the request without signing in first.
> **Instrumentation:** `workspace_joined` event fires on successful acceptance.

This passes: it names a specific user, a real task with a clear result, a
realistic failure scenario with a recovery path, and a named event.

---

## How to fill the new required fields

**thin-slice** — use the five-component format above. Name the user, the task,
the result, the failure + recovery, and the instrumentation event. If you can't
name the instrumentation event, the slice isn't ready.

**first-success-event** — the specific behavior you would accept as proof that
one user "got value" from the bet, 30 days out. Not "user engagement increases";
name the observable action: "completes a second session without a support
touchpoint" or "shares the feature with a colleague." Two people reading this
should agree whether it happened.

**specialist-lenses** — the team disciplines that will review the bet before
it commits. Default: `product, experience, architecture, safety`. Add `security`
for auth or data surfaces; `data` for instrumentation-first bets; `compliance`
for regulated markets. Don't skip the default set without naming why.

**learning-contract** — three things:
1. The signals that confirm or refute the bet (named metrics or behavioral
   markers, not "we'll look at analytics").
2. The review date or milestone.
3. The specific condition that would change the direction ("pivot if fewer than
   30% of first-week users complete the thin-slice task").


## See also

- `de-risk-intent` — step 3.5; validates the riskiest assumption before committing
- `diverge-solutions` — step 3; generates structured comparable options
- `explore-options` — an alternative way to surface options for the betting table
- `map-capabilities` — step 6; uses `bet.md` as the anchor for capability mapping
- `capture-work` — applies the `workspace.toml` transition the skill suggests
