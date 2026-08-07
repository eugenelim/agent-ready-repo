# The prototype-approach mode

An **explicit, optional, per-intent mode** — `validate-first` ↔ `prototype-led` —
**baked into how the skill works**, not just a described lifecycle. The
reversibility triage *recommends* one; the user can override; choosing it changes
the procedure.

## The two paths

### `validate-first` (default: one-way door / outcome-led)

1. The kill condition is predeclared (it always is).
2. Build the **cheapest probe that tests it** — a fake door, a smoke test, a
   landing page, a mock, a throwaway prototype. Match the probe to the risk.
3. Run it; compare to the kill condition; take the verdict.

The prototype here is a **validator**: it exists to answer the predeclared
question, then it's done.

### `prototype-led` (default: two-way door / taste-led)

1. Build a cheap, real prototype **early** — before fully specifying the intent.
2. Let what it reveals **drive** the intent's refinement: the outcome sharpens,
   new assumptions surface, the opportunity reframes. The **build is the test**.
3. Keep a predeclared bar (qualitative is fine) so "I like it" can't masquerade
   as a pass; iterate build → learn → refine until the bet survives or dies.

The prototype here is a **driver**: it shapes the requirement rather than only
checking it. This is the AI-era path — cheap building makes "learn by building"
the fastest loop.

## What changes across the loop

The choice ripples through all three skills:

| Skill | `validate-first` | `prototype-led` |
| --- | --- | --- |
| `frame-intent` | frame fully before testing | frame thin (outcome + hypothesis); detail deferred |
| `de-risk-intent` | predeclare, then build to test | build early; the build is the test |
| `decompose-intent` | decompose the validated intent | decompose against what the prototype revealed |

## The handoff to the spec

Either way, the prototype carries **behavioral** truth — the *what*, demonstrated.
It does **not** carry the wire contract. The detailed contract (fields, types,
errors) is pinned later, at the spec stage, where the component's full context
lives. The prototype informs the spec's acceptance criteria; it doesn't replace
the spec.
