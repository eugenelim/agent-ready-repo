# How to map capabilities

**Goal:** You have a committed bet and need to enumerate all the capability areas
the initiative implies — what to build, what to buy or adopt, and in what order
to build — before any spec or brief is written.

**Skill:** `map-capabilities` (PE pack, user scope)

---

## When to run `map-capabilities`

Run `map-capabilities` after `place-bet` and before `lean-canvas` / `author-brief`.
It is step 6 — the terminal step — of the PE six-step shaping sequence:

```
frame-situation → identify-opportunities → diverge-solutions
  → validate → place-bet → map-capabilities
```

You need a committed bet before running this skill. The bet provides the option,
appetite, and rationale that anchor the capability domains the skill proposes.
If you do not yet have a bet, run `place-bet` first.

**Not the right skill if:**

- You are working on a single feature or screen → use `frame-intent`.
- You want to author the initiative brief → use `lean-canvas` or `author-brief`
  (run those after this skill, not instead of it).

---

## How to read the Wardley and strategic-criticality annotations

Each capability entry in the map carries two annotations — Wardley stage and
strategic criticality — that together tell you how mature the capability is and
how much to invest in it.

### Wardley stage

The Wardley stage describes how evolved a capability is in the market:

| Stage | What it means | Typical implication |
|-------|--------------|---------------------|
| **Genesis** | Novel; no standard approach exists yet | Explore; expect high uncertainty and iteration |
| **Custom-built** | Better understood but still bespoke | Build if differentiating; invest carefully |
| **Product** | Standardised solutions exist | Buy or adopt unless you have a specific differentiating reason to build |
| **Commodity** | Utility-grade; interchangeable suppliers | Adopt or outsource; competing here wastes energy |

### Strategic criticality

Strategic criticality describes how much competitive weight the capability carries:

| Criticality | What it means | Typical implication |
|-------------|--------------|---------------------|
| **Differentiating** | Creates or sustains competitive advantage | Prioritise for Build; invest to lead |
| **Parity** | Must match market standard to be credible | Meet the bar; don't over-invest |
| **Utility** | Necessary overhead with no competitive value | Minimise cost; prefer Adopt or Buy |

### Reading them together

The combination tells you the most important strategic signals:

- **Custom-built + Differentiating** → your highest-value Build candidates; these go to the top of the build sequence.
- **Commodity + Utility** → adopt or outsource; never build these from scratch.
- **Commodity + Differentiating** → a *strategic tension*. The skill will flag this and ask for your acknowledgement before finalising the entry. Either your differentiation claim is wrong (the market has commoditised it) or you have a genuine reason to own the commodity (rare — name it explicitly).
- **Product + Parity** → the default Buy zone; a commercial solution handles it adequately.

---

## How to use the suggested build sequence to seed M3–M6

The suggested build sequence at the bottom of the capability map lists
**Build-disposition capabilities only**, ordered dependency-first then by
Wardley maturity (Genesis / Differentiating capabilities first).

It is a **recommendation, not a mandate** — the product team holds final
sequencing authority.

### Translating the sequence to your spec queue

Each position in the build sequence corresponds to a future spec:

1. Open `workspace.toml`.
2. For each capability in the build sequence, add an entry to the active
   initiative's `["ini-NNN".work].queue`:
   ```toml
   {path = "spec/<capability-id>-<short-name>", needs = "work:spec/<prior-capability-id>"}
   ```
3. Run `workspace-status` to confirm the entries are surfaced correctly and
   dependencies are resolved in the right order.

**Non-Build capabilities (Buy / Partner / Adopt)** appear in the domain tables
but are excluded from the build sequence — their disposition *is* the action.
Add procurement decisions to your team's acquisition plan, not the spec queue.

### What comes next

After the capability map is committed:

1. Run `lean-canvas` to author the initiative brief (maps the bet and capability
   map to a structured business brief).
2. Or run `author-brief` directly if you are working from an externally sourced brief.
3. Use the build sequence to seed `workspace.toml [work].queue` for M3–M6 spec-writing.

---

## See also

- `place-bet` — step 5; produces the `bet.md` this skill reads
- `lean-canvas` — brief-authoring from a committed bet and capability map
- `frame-situation` — step 1; provides Wardley capability assessments the map reads opportunistically
- `de-risk-intent` — step 4 (validate); runs assumption tests before the bet is placed
- `workspace-status` — surfaces the spec queue after you seed it from the build sequence
