# Reversibility triage — one-way vs two-way door

The first move of `de-risk-intent`. It classifies the bet by **cost of being
wrong**, which sets the default prototype-approach. It is a per-intent judgment,
not a global mode.

## The two doors

- **One-way door** — expensive or irreversible to undo. A published API or event
  contract, a data migration, a pricing change, a capability many teams will
  build on. Being wrong is costly and sticky.
- **Two-way door** — cheap to walk back. Behind a feature flag, a small cohort, a
  throwaway prototype, a reversible config. Being wrong costs little.

## What it decides

| Door | Default approach | Why |
| --- | --- | --- |
| one-way | `validate-first` | the cost of wrong is high, so predeclare a kill condition and test *before* committing |
| two-way | `prototype-led` | reversal is cheap, so the fastest learning is to build a probe and let it drive — the build *is* the test |

The default is **overridable** — a taste-led team may choose `prototype-led` on a
somewhat-reversible one-way-ish bet; a cautious team may `validate-first` a
two-way bet they want hard evidence on. The triage *recommends*; the human (or
the explicit mode choice) decides.

## The AI-era shift

When building is near-free, the rational move for a reversible bet is often to
**build the probe instead of running a separate experiment** — the prototype both
tests the assumption and carries behavioral detail forward. This is why
`prototype-led` exists as a first-class path, not a fallback. But cheap-to-build
raises a new risk: the *wrong* prototype can cost more than the wrong roadmap, and
a prototype that validates desirability still doesn't carry the precision a build
needs. So reversibility sets the approach; it never removes the kill condition.

## Output

A door classification + the recommended approach, recorded on the intent so the
verdict step (and a later reader) can see why this bet was tested the way it was.
