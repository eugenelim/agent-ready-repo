---
name: frame-situation
description: Use when holding a raw signal (market observation, OKR gap, user pain pattern, engineering finding, competitive signal) at initiative or capability level — turning it into a typed finding, a Wardley capability maturity assessment, and an anchor into the PE six-step shaping sequence. Triggers on "frame this situation", "what do we do with this signal", "is this an opportunity or a risk", "where should we start", "map this to the shaping sequence". Do NOT use for a feature-scoped request (use `frame-intent`), testing an assumption (use `de-risk-intent`), or breaking down a shaped intent (use `decompose-intent`).
---

# Skill: frame-situation

Classify a raw signal, assess relevant capability maturities, and anchor the
situation to the PE shaping sequence — so the team knows *what kind of thing
this is* and *where to enter the six-step loop* before any shaping work begins.

## Output rendering

Table — When presenting several items that share the same fields, render a Markdown table. Cap at ~5 columns; beyond that, switch to a per-item detail list. Right-align numeric columns.

## When to invoke

Confirm the signal is **initiative or capability level** (affects a whole
product area or initiative). If it is clearly a single screen or endpoint,
name the altitude mismatch and redirect: *"This looks feature-scoped;
`frame-intent` is the right entry point."*
If altitude is **genuinely ambiguous**, ask — never force one level.
If the signal is **too thin to classify**, elicit more context first.

## Procedure

**1. Intake.** Read the signal. Confirm altitude in one sentence; proceed once confirmed.

**2. Classify.** Choose: `opportunity` | `risk` | `gap` | `threat` |
`emergent-capability`. State type + one-line rationale. If underdetermined,
name the ambiguity and elicit — do not force a type.

**3. Wardley maturity.** Identify up to three implicated capability areas.
For each, place on the four stages — *Genesis* (novel/uncertain; explore);
*Custom-built* (hand-crafted; invest to differentiate); *Product* (widely
available; buy/adopt over build); *Commodity* (utility; competing here wastes
energy) — with evidence and strategic implication. Mark unplaceable capabilities
as residual assumptions. When zero can be placed, emit an all-residual table.

**4. Recommend entry point.** PE six-step sequence: `frame-situation` →
`identify-opportunities` → `diverge-solutions` → validate → `place-bet` →
`map-capabilities`. Recommend where to enter:
- Unknown problem → step 2 (`identify-opportunities`, default).
- Known problem, unknown options → step 3 (`diverge-solutions`).
- Known options, need committed bet → step 5 (`place-bet`).
State the entry point and one-sentence rationale so the PE can override.

**5. Emit `situation-framing.md`.** Resolve `output_dir` via the three-tier
config procedure (repo-scope `agentbundle-layout.toml [product]` → user-scope
→ two-branch elicitation). Realpath-expand; reject `..` and symlinks that exit
the root; surface the resolved path before writing. Write to
`<output_dir>/shaping/<slug>/situation-framing.md`.

**Step 2 readiness:** if `identify-opportunities` is absent from available
skills, note this under a "Step 2 readiness" section and describe what step 2
provides. Do not block artifact emission. Apply the same degrade if
`diverge-solutions` or `place-bet` is the recommended entry and is also absent
— those skills are not yet shipped.

Artifact shape: frontmatter (`type: situation-framing`, `slug`, `signal`, `date`,
`finding-type`, `shaping-entry`), then sections — Signal, Finding, Wardley
Assessment table, Recommended Entry Point, Step 2 readiness (when absent),
Suggested workspace.toml entry (TOML snippet + direction to add via `queue-add`
or manually).

**6. Suggest workspace.toml entry.** Print the `{slug = "<slug>", type = "shape"}`
TOML snippet. Direct the user to add it to `[ini-NNN.shaping_queue]` backlog.
Do **not** write to `workspace.toml`.

## Anti-patterns to refuse

- Writing to `workspace.toml` or a literal hardcoded path.
- Producing a brief (that is `place-bet` + `author-brief`'s job).
- Forcing a Wardley stage when evidence is insufficient — name it as a residual
  assumption instead.
- Forcing an altitude when it is **genuinely ambiguous** — ask instead.
