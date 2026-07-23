# How to generate solution options

**Use this when:** You hold a confirmed opportunity at initiative or capability scope and need to surface ≥3 structured, comparable options before committing to a direction in `place-bet`.
**Prerequisites:** `product-engineering` pack installed; a confirmed opportunity at initiative or capability altitude — ideally from `identify-opportunities` (feature-scope goes to `explore-options` instead).
**Result:** A structured options artifact with ≥3 spanning options, a recommended selection with a dominant-bet rationale, and retained reasoning for parked and rejected alternatives.

Use `diverge-solutions` when you hold a confirmed opportunity at initiative or
capability scope and need to surface the full option space before committing to
a direction. The skill forces ≥3 structured, comparable options — the discipline
that keeps `place-bet` (step 5) from just ratifying the first idea.

## When to reach for `diverge-solutions` vs `explore-options`

The deciding question is: *do you need structured comparable options, or do you
need to brainstorm freely?*

**Reach for `diverge-solutions` when:**
- You hold an initiative- or capability-scope opportunity (from `identify-opportunities`
  or a clear signal) and want to generate the option space systematically.
- The output needs to be comparable — options must be weighable against one another
  so `place-bet` can reason about which bet to take.
- You want retained rationale for options you park or reject (so they stay revivable).

**Reach for `explore-options` when:**
- The input is feature-scoped (a specific screen, endpoint, or component).
- You want a freeform brainstorm with no minimum option count or forced structure.
- You are in a discovery loop pre-G1.5 and structured comparability is not yet needed.

**Altitude signal — initiative vs capability vs feature:**
- *Initiative:* affects a whole product area or strategic direction (e.g., "how do
  we build durable shaping memory for PEs?").
- *Capability:* affects a cross-cutting system capability (e.g., "how do we handle
  context at session start?").
- *Feature:* affects a specific user interaction or endpoint — send this to
  `explore-options`.

When altitude is genuinely ambiguous, `diverge-solutions` will ask rather than
force a level.

## How to read a step-2 opportunity and generate spanning options

A step-2 artifact from `identify-opportunities` gives you three JTBD layers:
functional (what the user is trying to accomplish), emotional (how they want to
feel doing it), and social (how they want to be seen). Use these layers to stress-
test each option's key bets.

If you don't have a step-2 artifact, `diverge-solutions` will flag the gap and
offer to run `identify-opportunities` first. You can proceed without it —
the skill will include a "Step 2 readiness" note in the artifact — but expect
the key bets to have less JTBD grounding.

**What "spanning" means.** Three options that differ only in implementation detail
don't count. Options must differ in at least one of:
- *Mechanic:* how the opportunity is seized (e.g., structured log vs structured
  data vs active synthesis).
- *Scope:* breadth of what is addressed (per-session vs per-initiative vs
  cross-workspace).
- *Bet:* what must be true for the option to succeed (e.g., "PEs maintain it
  consistently" vs "agents parse it reliably" vs "synthesis quality is high
  enough").

If you find only two distinct approaches coming to mind, name the constraint —
the skill will surface it rather than forcing a third trivial variation.

**The key-bets field** is where the JTBD grounding pays off. A bet like "users
will find this low-friction" is weak. A bet like "PEs already updating the work
queue in TOML will adopt this format without additional training" is grounded in
functional and social job evidence from step 2.

## How to select one option and what makes a sound rationale

`diverge-solutions` recommends one option and leaves final selection to you.
After the session, mark the selected option in the artifact as `selected` — this is the PE's post-emission action; the skill itself never writes `selected`.

**What makes a sound rationale:** The rationale should name the *dominant bet* —
the single assumption whose failure would most threaten the option — and explain
why the team is willing to take it. "It's the best" is not a rationale.

Examples:
- Weak: "Option B is recommended because it is simpler."
- Strong: "Option B — the dominant bet (TOML updates are low-friction for PEs
  already using the work queue) is defensible given the existing adoption. The
  rigidity risk is manageable: the schema can grow incrementally."

**Tagging non-recommended options:**
- `rejected`: definitively out — you have evidence or a constraint that rules it
  out. State the evidence.
- `parked`: revisable — it's a valid approach the team isn't ready to take yet,
  or whose dominant bet is unresolved. Do not delete it; parked options are
  revivable when conditions change.

Retaining rejected and parked options is deliberate — the artifact exists to
prevent myopic commitment to the first idea. A future PE reviewing the artifact
should be able to see *why* other options were set aside.

## What to do with the workspace.toml suggestion

After emitting the artifact, `diverge-solutions` prints a TOML snippet:

```toml
{slug = "<slug>", type = "shape"},
```

Add it to `[ini-NNN.shaping_queue]` in `workspace.toml`. Two ways:

1. **Via `capture-work`:** run `capture-work` and follow the prompts — it writes
   the entry for you.
2. **Manually:** open `workspace.toml`, find the `[ini-NNN.shaping_queue]` section,
   and add the line to the `backlog` array.

**What happens next:** once the option is selected, the next step is validation
(`de-risk-intent`, step 4). Run it on the selected option to pressure-test the
dominant bet before `place-bet` commits the direction.
