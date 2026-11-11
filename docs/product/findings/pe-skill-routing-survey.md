# Product-engineering skill routing: one intent skill with verb modes

> Discipline: applied (practitioner-pattern survey)

Surveyed 2026-10-10. Scope: agent-skill authoring and verb design practice, router
patterns, the role `discovery-loop` plays today, the *Shape it* stage of the operating
model, and whether the 15 `product-engineering` skills should become one `intent` skill
with verb modes loaded by progressive disclosure.

## Answer

Consolidate, but not into `discovery-loop`.

- Make one `intent` skill the front door for the whole *Shape it* stage. Its default mode
  is a read-only router that picks the short, longer, or supervised route. Each verb is a
  mode whose procedure lives in `references/<verb>.md` and loads only when chosen.
- Keep `discovery-loop` as a separate skill. It becomes the supervised route the router
  hands to, not the router. It is a 422-line, stateful, gated loop run by an agent. Loading
  it to answer "should this be the short route?" pays its full cost for the commonest case.
- Keep `align-value-stream` as its own skill. It coordinates delivery across repositories,
  which is not shaping, and the probe below lost most of its queries when it was a mode.
- Move `ux-writing` to `experience-design`.
- The pack's listing falls from 15 skills and 9,373 description characters to 4 skills and
  3,226, a 66% cut. Selection accuracy held in a probe on Opus and Sonnet.

The change is cross-cutting and retires 12 skill names, so it needs an RFC before a spec.

## Findings

### Skill-listing budget is a real constraint, and this pack is a large share of it

- **[high]** Every host preloads only `name` + `description` and loads the body on
  activation. Sources: [agentskills.io spec](https://agentskills.io/specification),
  [Gemini CLI skills](https://geminicli.com/docs/cli/skills/),
  [Cursor skills](https://cursor.com/docs/context/skills),
  [Codex skills](https://learn.chatgpt.com/docs/build-skills).
- **[high]** The listing is capped. Codex allows 2% of the context window, or 8,000
  characters when the window is unknown, then shortens descriptions and drops skills.
  Claude Code caps `description` + `when_to_use` at 1,536 characters per skill and cuts the
  tail. The spec caps `description` at 1,024. Sources:
  [Codex skills](https://learn.chatgpt.com/docs/build-skills),
  [Claude Code skills](https://code.claude.com/docs/en/skills),
  [agentskills.io spec](https://agentskills.io/specification).
- **[high]** Measured in this repository on 2026-10-10, the 15 `product-engineering`
  descriptions total about 9,400 characters. That alone exceeds Codex's 8,000-character
  fallback, before any other pack loads. The 28 skills self-hosted in `.claude/skills/`
  total about 13,000. [synthesis, local measurement]
- **[moderate]** The commonest activation failure is invoking no skill, not invoking the
  wrong one. Practitioner evals report about 55% baseline activation on one model, and an
  agent skipping an available skill in 56% of cases. When a skill did fire, it was usually
  the right one. Sources:
  [Scott Spence](https://scottspence.com/posts/measuring-claude-code-skill-activation-with-sandboxed-evals),
  [Codeminer42 citing Vercel](https://blog.codeminer42.com/stop-putting-best-practices-in-skills/),
  [mcp.directory](https://mcp.directory/blog/why-your-claude-skill-isnt-activating-2026-fixes).
  Downgraded: small samples, older models, read through summaries.

### Names and descriptions

- **[high]** A description must say what the skill does and when to use it, with the
  trigger words up front. Sources:
  [Claude best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices),
  [Codex skills](https://learn.chatgpt.com/docs/build-skills),
  [Gemini best practices](https://geminicli.com/docs/cli/skills-best-practices/).
- **[moderate]** State when the skill should *not* trigger. Codex says so directly.
  Anthropic's page does not. This repository already requires it
  (`guides/_shared/how-to/author-a-skill.md`). Sources:
  [Codex skills](https://learn.chatgpt.com/docs/build-skills),
  [codemyspec rubric](https://codemyspec.com/blog/skill-description-rubric).
- **[moderate]** Name form is a style choice, not a trigger factor. Anthropic suggests
  gerunds but accepts noun phrases and verb-noun names, and asks for consistency within a
  collection. No source shows one form triggering better. Source:
  [Claude best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).
  Downgraded: single vendor.
- **[high]** Distinct descriptions matter more than count. Gemini asks for descriptions
  distinct from each other. An anecdote reports seven modules sharing one description being
  picked at random. The repository's own reference says "overlapping mode names make
  routing arbitrary". Sources:
  [Gemini best practices](https://geminicli.com/docs/cli/skills-best-practices/),
  [codemyspec rubric](https://codemyspec.com/blog/skill-description-rubric),
  `ase-okf-reference/.../activation-discoverability-and-mode-wayfinding.md`.

### Modes and routers

- **[high]** Routing suits distinct categories that can be classified accurately, and the
  mechanism should stay light: a classifier step or a handoff, not a standing controller.
  Sources: [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents),
  [OpenAI Agents SDK handoffs](https://openai.github.io/openai-agents-python/handoffs/),
  [LangChain router](https://docs.langchain.com/oss/python/langchain/multi-agent/router).
- **[moderate]** A multi-mode skill should name the modes and their differences in the
  description, give each mode an entry condition, default to a read-only framing mode, and
  require an explicit step before any write. Source: this repository's
  `activation-discoverability-and-mode-wayfinding` reference, observed over 137 skills.
  Downgraded: one population, no external replication.
- **[moderate]** Route on observable signals, not the model's own confidence. One paper
  found 64% of wrong answers still self-labelled "high" confidence. A clarifying question is
  a valid fallback. Sources: [arXiv 2606.10457](https://arxiv.org/pdf/2606.10457),
  [mejba.me](https://www.mejba.me/concepts/llm-routing-and-fallbacks). Downgraded: one
  paper, vendor concept page.
- **[low]** The repository already ships a mode-based skill:
  `author-delivery-brief` takes an explicit `create` or `continue` mode. One precedent.

### Where `discovery-loop` sits today

- **[high]** `discovery-loop` is one of three routes, not a router. The operating model
  (`guides/_shared/explanation/the-operating-model.md:36-56`) names the short route (default,
  about three hours), the longer route (six steps), and the supervised loop.
  `docs/architecture/lifecycle-flow.md` says the short and longer routes are not supervised
  by `discovery-lead`.
- **[high]** No skill routes between the three at run time. The only statement of the
  choice is prose in `frame-intent` `## Pick a route`, pinned by
  `tests/pack/test_intent_triad_execution_wiring.py` (AC11–13). `work-intake` sends
  product-shaping requests straight to `frame-intent` and has no shaping branch.
- **[high]** Five statements are stale or inconsistent:
  1. The `discovery-loop` description says it hands off to `work-loop` at G3. The body and
     `discovery-lead` hand off through `work-intake`.
  2. `frame-domain/SKILL.md:72` calls the loop "unbuilt", but the pack ships it
     (`packs/product-engineering/pack.toml:43`).
  3. The skill seeds requirements with `author-delivery-brief continue`;
     `guides/product-engineering/how-to/run-a-discovery.md:66` says `create`.
  4. `guides/product-engineering/how-to/frame-the-intent.md:37` says the loop needs "an
     approved intent". It starts from a raw idea and runs `frame-intent` itself at G0.
  5. The route choice is stated in five places with nothing enforcing agreement: the
     `frame-intent` menu, the operating-model guide, `guides/README.md` P2/P2b,
     `tools/render-lifecycle-graphics.py`, and `lifecycle-flow.md`.

### The pack's verbs collide today

- **[high]** Three skills share the verb *frame*: `frame-intent`, `frame-situation`,
  `frame-domain`. Two are near-duplicates split by altitude: `explore-options` and
  `diverge-solutions`. Each description spends characters fencing off its neighbours.
  [synthesis, local descriptions]
- **[moderate]** `ux-writing` is a design discipline sitting in this pack. `content-design`
  in `experience-design` already defers final UI strings to it. [inference]

## Proposed shape

### One skill, verb modes, routes as the default mode

`/intent` with no verb runs `route`: read-only, it reads observable signals, names one
route and its first verb, and asks one question when the signals conflict.

| Signal | Route | First verb |
| --- | --- | --- |
| You can name the outcome; one bet | Short (default) | `frame` |
| You can't yet say what the problem is, or the bet needs recorded reasoning | Longer | `situate` |
| A raw idea for a new product area | Supervised | hand to `discovery-loop` |
| A defect, an already-shaped feature, an architecture choice | Out of stage | `bug-fix`, `work-intake`, `architect-design` |

Verb modes, each with one entry condition and one `references/<verb>.md`:

| Mode | Replaces | Used on |
| --- | --- | --- |
| `frame` | `frame-intent` | short; supervised G0 |
| `situate` | `frame-situation` | longer, step 1 |
| `find` | `identify-opportunities` | longer, step 2 |
| `diverge` | `diverge-solutions`, `explore-options` | longer, step 3; supervised divergence |
| `de-risk` | `de-risk-intent`, `plan-validation` | all routes; supervised validation slot |
| `bet` | `place-bet` | longer, step 5 |
| `map` | `map-capabilities` | longer, step 6 |
| `decompose` | `decompose-intent` | short; supervised G3 |
| `ground` | `frame-domain` | supervised G1.5 |
| `canvas` | `lean-canvas` | positioning aid, off the drawn routes |

Users say "validate" when they mean de-risk, so a separate `validate` mode pulled de-risk
queries in the probe. Planning validation is the second half of `de-risk`.

Each retired skill's body moves to `intent/references/<verb>.md`. Its trigger phrases move
into the mode table in the `intent` body, and its eval queries merge into one `intent` eval
file that also asserts the mode. The directory is deleted with no alias.

`discovery-loop`, `align-value-stream`, and `ux-writing` (moving to `experience-design`)
stay separate skills. `discovery-loop` calls `intent` modes at its gates instead of
separate skills.

### What it buys

- The pack's listing falls from 9,373 to 3,226 characters: `intent` (1,016),
  `discovery-loop` trimmed to 474, `align-value-stream`, and `ux-writing`. [local
  measurement]
- One strong description for the whole stage, which targets the measured failure
  (under-triggering) instead of the rare one (mis-picking). [inference]
- The route choice gets one owner that runs, replacing five prose copies. [synthesis]
- Each verb is unique, so `frame` / `situate` / `ground` stop colliding. [synthesis]

### What it costs

- **Trigger coverage.** Nine skills' trigger phrases cannot fit in 1,024 characters. The
  description must carry the stage outcome and the verb names; the rest moves to the body.
  Re-run the union of the nine existing `evals/eval_queries.json` files against `intent`,
  and add a mode assertion to each.
- **A second routing step.** The model picks `intent`, then the skill picks a mode. Keep
  the mode table in the SKILL.md body, never only in references.
- **Breaking rename.** ADR-0054 retires renamed skills without aliases, and an alias skill
  would cost the listing budget this change exists to save. This is a major version of the
  pack.
- **Callers to update.** `discovery-lead`, `work-intake`'s explicit-owner list, cross-pack
  mentions in `experience-design`, `architect`, and `desk-research` (`frame-domain`'s wrapped
  `applied` call), the operating-model guide, the render script, and the tests that pin
  descriptions.
- **Name collision.** `intent` sits close to Core's `intake-intent`. Folding
  `intake-intent` into `work-intake` as an `intent` mode removes the clash. That reverses
  ADR-0098, which split intake routing from intent authorship, so it needs a superseding
  ADR.
- **Host variance.** Passing a mode as an argument (`/intent de-risk`) works where the host
  forwards arguments. Elsewhere the mode is read from the prose request, which the router
  already handles.

## Probe: broad versus narrow descriptions

Run 2026-10-10 with subagents. Each run saw a full skill listing: the pack's skills plus 40
skills from other packs, names and descriptions only. It picked one skill and mode, or
none, for each of 146 queries. Those are the distinct queries in the pack's nine
`evals/eval_queries.json` files, which hold 153 entries with 7 repeated across files.

- 77 queries are should-trigger for some skill, and that skill is the expected answer.
- The other 69 are should-not-trigger everywhere. Each was labelled by hand with the
  pack skill that should own it, or with no pack skill.

Correct means the right skill and, for `intent`, the right mode.

| Listing | Opus | Sonnet | Sonnet repeat |
| --- | ---: | ---: | ---: |
| A. Today: 15 narrow skills | 98% | 99% | 99% |
| B. `intent` with 12 modes, incl. `align` and `validate` | 94% | 88% | — |
| C. `intent` with 10 modes; `align-value-stream` separate; `validate` folded into `de-risk` | 99% | 98% | 98% |

- **[moderate]** On listing B, Sonnet missed 11 queries whose expected answer was
  `align-value-stream`: 9 from its eval file and 2 hand-labelled. Requests like
  "set up a value-stream meta-repo" or "roll up delivery status across repos" did not read
  as shaping, so the model chose no skill. It also confused `validate` with `de-risk`.
- **[moderate]** Listing C matches today's accuracy within one query per model.
  Downgraded: forced-choice selection, not spontaneous activation; listing C was revised on
  the same queries it was scored on; one or two runs per cell.
- **[high]** Six retired skills ship no eval queries: `frame-situation`,
  `identify-opportunities`, `diverge-solutions`, `place-bet`, `map-capabilities`, and
  `lean-canvas`. The probe says nothing about `situate`, `find`, `bet`, `map`, or
  `canvas`.

## Known unknowns

- **Known-unknown:** Does one broad `intent` description trigger as often as nine narrow
  ones when nothing forces the model to pick? Would be closed by: a headless activation
  run with installed stub skills on each supported host, using held-out queries plus new
  queries for the six untested modes.
- **Known-unknown:** Claude Code's total listing budget across all skills. Reported figures
  conflict (1% to 2% of context). Would be closed by: reading `/context` output on a loaded
  session.
- **Known-unknown:** Whether Copilot caps the listing. Its docs state no limit. Would be
  closed by: a Copilot listing test with this pack installed.
- **Known-unknown:** Where `lean-canvas` sits on a route. The operating model does not
  draw it. Would be closed by: the pack owner placing it, or folding it into `situate`.
- **Unknowable:** Whether verb-mode skills beat separate skills in general. Why not: no
  controlled comparison exists, and results shift with each model release.
