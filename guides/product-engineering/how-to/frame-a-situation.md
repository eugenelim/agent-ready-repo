---
title: How to frame a situation
summary: Classify a raw signal, assess capability maturity, and select the correct entry point into product shaping.
pack: product-engineering
kind: how-to
---

# How to frame a situation

**Use this when:** You hold a raw signal — market observation, OKR gap, user pain, or engineering finding — and need to classify it and find the right PE-sequence entry point before committing to any solution.
**Prerequisites:** `product-engineering` pack installed; a signal with a subject, an observation, and a symptom or consequence (no prior shaping artifacts required).
**Result:** A classified signal with a Wardley capability assessment, a recommended shaping-sequence entry point, and a `workspace.toml` snippet to queue the item for the next step.

**Goal:** You have a raw signal — a market observation, an OKR gap, user pain
patterns, an engineering finding — and you need to decide what kind of thing
it is and where to take it next.

**Skill:** `frame-situation` (PE pack, user scope)

```text
Frame this situation: three teams hand-roll export retention rules, so compliance reviews take weeks and produce inconsistent results.
```

This guide belongs to the [robust shaping path](../explanation/the-intent-tree.md#light-and-robust-shaping-paths).

---

## When to use `frame-situation` vs `frame-intent`

| Question | Answer | Skill |
|---|---|---|
| Is this affecting a whole capability area or initiative? | Yes | `frame-situation` |
| Is this a specific feature or screen request? | Yes | `frame-intent` |
| Do I know what outcome I want, just not how? | Yes | `frame-intent` |
| Do I have a signal but not yet know what to do with it? | Yes | `frame-situation` |
| Am I unsure of the altitude? | Ambiguous | Ask the skill — it will prompt you |

**Rule of thumb:** if you can write "I want to build X so that Y" immediately,
that is `frame-intent` territory. If you are holding an observation that
something is wrong or an opportunity is emerging and you do not yet know how to
respond — that is `frame-situation`.

---

## What makes a well-formed signal

A well-formed signal gives the skill enough to classify. It has:

- **A subject** — what domain or capability area the observation concerns.
- **An observation** — something measured, seen, or reported (not a proposed solution).
- **A symptom or consequence** — why it matters; what is happening because of it.

**Good:** "Three teams hand-roll their own skill discovery mechanism. No shared
standard is emerging. Onboarding takes longer each quarter as a result."

**Too thin:** "Skill discovery is a problem." (No subject specificity, no
consequence.) → The skill will ask for more detail.

**Pre-solved:** "We should build a skill registry." → This is already a solution;
frame-situation cannot classify a solution. Describe the underlying observation instead.

---

## How to use the Wardley assessment to choose your entry point

The Wardley capability maturity table tells you how evolved each relevant
capability area is. Use it to calibrate where to enter the PE six-step sequence:

| What the assessment shows | Recommended entry |
|---|---|
| Capability is Genesis or early Custom-built; problem space not well-documented | Step 2 — `identify-opportunities` (map the jobs first) |
| Capability is mid Custom-built; problem is understood; solution options unexplored | Step 3 — `diverge-solutions` |
| Capability is late Custom-built or Product; options are known; need a committed bet | Step 5 — `place-bet` |

**When to override:** The entry point is a recommendation, not a lock. If your
team has already done extensive job-mapping on this problem area (it is documented
somewhere), you may enter at step 3 or later. State why when you do.

**When capabilities land as residual assumptions:** If the agent cannot confidently
place a capability on the curve, it flags it as a residual assumption. Before
entering the shaping sequence, consider a quick spike (a `desk-research` run or
team knowledge session) to ground the placement — a misread maturity can lead to
over-investing in a capability already commoditized, or under-investing in one that
is differentiating.

---

## What to do with the workspace.toml suggestion

After `frame-situation` completes, the skill prints a TOML snippet. A
dispatchable entry carries the five canonical fields — `path`, `kind`, `source`,
`summary`, and `needs`:

```toml
{path = "docs/product/intents/agent-skill-discovery-gap.md", kind = "intent", source = {mode = "repo-origin"}, summary = "Agents cannot discover which skill fits the work in front of them", needs = []},
```

Add this to your active initiative's `[shaping_queue]` backlog in
`workspace.toml`. Two ways:

1. **Ask the agent** — it routes through `work-intake`, which writes the
   canonical artifact and registers the entry for you:

   ```text
   Remember the situation finding for agent skill discovery as shaping work.
   ```

2. **Manual edit** — open `workspace.toml`, find `["ini-NNN".shaping_queue]`, and
   add the entry to the `backlog` array.

A short `{slug = "...", type = "shape"}` entry is the legacy shape. It still
reads during the compatibility window but is **never dispatchable**, so
`workspace-status` cannot offer it as work.

Once added, `workspace-status` will surface it as a ready `shape`-typed item and
suggest running `identify-opportunities` (or the appropriate entry-point skill).

---

## See also

- `frame-intent` — for feature-scoped or known-outcome work
- `identify-opportunities` — step 2 of the shaping sequence
- `work-intake` — the front door for registering an entry in
  `workspace.toml [shaping_queue]`

## What you have now

- A classified signal with a Wardley capability assessment and a recommended entry point into the shaping sequence.
- Register its canonical artifact through `work-intake`, then follow the recommended next shaping skill.
