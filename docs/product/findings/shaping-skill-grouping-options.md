# Shaping-skill grouping: options for the nine longer-route skills

> Discipline: applied (practitioner-pattern survey)

Surveyed 2026-10-13; updated 2026-10-14 after option C shipped. Scope: how the
`product-engineering` pack should group its nine longer-route and supervised shaping
skills now that folding them into verb modes has failed twice. The nine are
`frame-situation`, `identify-opportunities`, `diverge-solutions`, `explore-options`,
`plan-validation`, `place-bet`, `map-capabilities`, `frame-domain`, and `lean-canvas`.

## Answer

Keep the nine skills narrow. Their descriptions now lead with the words users say
(option C, shipped in `product-engineering` 1.0.4). Treat what is left of listing cost
as a catalogue problem, not a problem inside this pack.

- **Keep them narrow (option A as the structure).** Every fold lost activation. The
  only thing a fold fixed was listing cost, and that cost is catalogue-wide anyway.
- **Option C has shipped.** Each description opens with the artifact or outcome in the
  user's words, not "Step 5 of the PE six-step shaping sequence". The nine went from
  5,059 to 2,801 characters, a 45% cut, and the pack's listing from 8,670 to 6,412.
  - Against the committed eval files, the rewrite holds: 40 of 46 queries pass, against
    41 of 46 before, with no false triggers.
  - A cold probe routes all 72 runs to the right skill.
  - The owner shipped it without the held-out run, so whether it *raises* activation on
    paraphrased requests is still unmeasured. Experiment 1 now checks that after the
    fact. See [What the shipped rewrite shows](#what-the-shipped-rewrite-shows).
- **If Experiment 1 shows a loss, revert the skills that lost and cut listing cost
  another way.** Use option D (move the nine to an optional pack) or option I (make rare
  steps callable by name only).
- **Treat listing cost as a catalogue rule (option E).** Set a per-description length
  budget and size each install profile against the host budgets. Core alone (10,671
  characters today) is already over Codex's 8,000-character fallback, so no change inside
  this pack can fix that. A cap alone is not enough either: a profile fits 8,000
  characters only at about 20 skills of 350 characters each.
- **Raise D's priority only if Experiment 2 shows that removing the nine raises
  activation of the skills that stay.**
- **Do not fold again (options B and F),** and do not rely on Claude-Code-only fields
  or hooks (options G and H).

The open question is now **C as shipped** against **D** (move the skills out of the
default install). Three experiments on the existing harness settle it. They take 1,242
headless sessions, or up to about 1,640 with the conditional re-runs. See
[Experiments](#experiments-that-remain).

## Terms used here

- **Activation:** the host's model chooses to load a skill on its own, with no slash
  command. The repository measures it as the *positive trigger rate*: the share of runs
  in which the expected skill fired for a query that should trigger it.
- **Listing:** the name and description of every installed skill. The host puts it in
  the model's context on every turn so the model can pick a skill.
- **Fold:** turning separate skills into modes of one skill. One description then stands
  for all of them.
- **Cold probe:** a forced-choice test. The model sees only names and descriptions and
  must pick a skill and mode. It measures routing, not activation.

## Findings

Confidence follows the GRADE-style set `[high]`, `[moderate]`, `[low]`, `[uncertain]`,
with the applied-mode overlay. Every downgrade names its reason.

### How hosts choose a skill

- **[high]** All five hosts put only the name and description of each skill in the
  model's context, and the model decides when to load one. No host documents keyword or
  embedding matching. Cursor's `paths` field is the one non-model gate: it hides a skill
  unless the agent is working on matching files. Sources:
  [agentskills.io spec](https://agentskills.io/specification),
  [Claude Code skills](https://code.claude.com/docs/en/skills),
  [Codex skills](https://learn.chatgpt.com/docs/build-skills),
  [Cursor skills](https://cursor.com/docs/context/skills),
  [VS Code agent skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills),
  [Gemini CLI skills](https://geminicli.com/docs/cli/skills/).
- **[high]** Two hosts publish a total listing budget, and both shrink the listing
  when it overflows. Claude Code does it without a visible warning:

  | Host | Total budget | What overflow does |
  | --- | --- | --- |
  | Claude Code | 1% of the context window; tunable with `skillListingBudgetFraction` or `SLASH_COMMAND_TOOL_CHAR_BUDGET` | Drops descriptions, starting with the least-invoked skills; names stay. A warning appears only in `--debug` output. |
  | Codex | 2% of the context window, or 8,000 characters when the window is unknown; up to 10,000 tokens via `skills.max_context_tokens` | Shortens descriptions first, then may omit skills and show a warning. |
  | Cursor, Copilot, Gemini CLI | None documented | Unknown. |

  Claude Code also cuts each entry's `description` plus `when_to_use` at 1,536
  characters. The open standard caps `description` at 1,024. Sources:
  [Claude Code skills](https://code.claude.com/docs/en/skills),
  [Codex skills](https://learn.chatgpt.com/docs/build-skills),
  [agentskills.io spec](https://agentskills.io/specification).
  Each figure comes from one primary source, the host's own documentation.
- **[high]** Four hosts can keep a skill out of the listing while it stays callable by
  name. Claude Code, Cursor, and Copilot read `disable-model-invocation: true`. Codex
  reads `allow_implicit_invocation: false` in `agents/openai.yaml`. Gemini CLI can
  disable a skill only per user, with `/skills disable`. Such a skill never activates on
  its own. Sources: as above, plus
  [GitHub about agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills).
- **[moderate]** Only Claude Code reads `when_to_use`. Its text counts against the same
  1,536-character entry cap and the same total budget. Other hosts ignore the field, so
  trigger text placed there is invisible to four of the five hosts. Source:
  [Claude Code skills](https://code.claude.com/docs/en/skills). Downgraded: single
  vendor. The other hosts' silence is read from their field lists.

### What fails: activation, not routing

- **[high]** In this repository, a skill that does not fire is the dominant miss. A
  wrong skill firing is rare. In the first ten-mode run, 49 of 49 missed runs fired no
  skill at all. In the two-skill run, 90 of 97 did. In every fold, the cold probe routed
  every case to the right skill and mode (24 of 24 before the fold, 72 of 72 after).
  Sources: [verification ledger](../../specs/intent-longer-and-supervised-verbs/notes/verification-ledger.md),
  [routing evidence](../../specs/intent-longer-and-supervised-verbs/notes/routing-classification-evidence.md).
- **[moderate]** The same pattern shows outside this repository. Anthropic's
  skill-creator says Claude tends to "undertrigger" skills and advises "a little bit
  pushy" descriptions. One independent sandboxed eval of the real `claude -p` binary
  found about 50% baseline activation. When a skill did fire, it was the right one in
  every configuration. Sources:
  [skill-creator SKILL.md](https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md),
  [independent sandboxed evals (2026-02-08)](https://scottspence.com/posts/measuring-claude-code-skill-activation-with-sandboxed-evals).
  Downgraded: one vendor plus one small independent study (22 prompts, two runs, one
  model).
- **[high]** Name collisions are not the problem. The `frame-situation` / `frame-domain` pair and the
  `explore-options` / `diverge-solutions` pair routed 24 of 24 at high confidence in the
  pre-fold probe. Source:
  [routing evidence § Pre-fold world](../../specs/intent-longer-and-supervised-verbs/notes/routing-classification-evidence.md).

### What a fold does to activation

- **[high]** For this pack, on Claude Code, one broad description loads less often than
  narrow ones, even when it routes correctly:

  | Fold | Pre-fold rate | Fold rate | Floor | Query set |
  | --- | ---: | ---: | ---: | --- |
  | One `intent` skill, ten modes (attempt 2) | 0.856 | 0.728 | 0.826 | 2026-10-11 |
  | One `intent` skill, ten modes (attempt 3) | 0.856 | 0.739 | 0.826 | 2026-10-11 |
  | `intent` plus `initiative` | 0.600 | 0.461 | 0.570 | 2026-10-13 |

  A repeated pre-fold run gave 0.856 again. The standard error of the aggregate
  difference is about 0.019, so each drop of 0.12 to 0.14 is six to seven standard
  errors. Sources: [verification ledger](../../specs/intent-longer-and-supervised-verbs/notes/verification-ledger.md),
  [RFC-0107 § Errata](../../rfc/0107-verb-mode-shaping-and-intake-with-slice-handover.md),
  [ADR-0145](../../adr/0145-shaping-entry-points-intent-and-initiative.md).
  Kept at high for this pack and host only. It says nothing yet about other hosts.
- **[moderate]** Steps that users name with a distinctive noun survive a fold.
  Paraphrased steps collapse. Under `initiative`, canvas went from 1.00 to 0.93 and find
  from 0.73 to 0.80. Situate went from 0.47 to 0.00, diverge shapes from 0.67 to 0.20,
  and ground (in `intent`) from 0.67 to 0.40. The validation plan fell from 0.87 to 0.27
  in the one-skill fold. Source: [verification ledger](../../specs/intent-longer-and-supervised-verbs/notes/verification-ledger.md).
  Downgraded: five queries per group, and identical runs moved single groups by up to
  0.20.
- **[moderate]** The short-route fold that shipped passed, but one mode lost ground.
  Overall it went from 0.70 to 0.711, which is 0.011 above the pre-fold rate and 0.041
  above its 0.67 bound. `de-risk` alone fell from 0.70 to 0.53, about five of its 30
  runs. Source:
  [slice 1 verification ledger](../../specs/intent-short-route/notes/verification-ledger.md).
  Downgraded: one run per world.
- **[low]** Tool-selection studies agree that more tools in context means worse
  selection, and that retrieval or deferral helps:
  - LongFuncEval reports drops of 7% to 85% as the tool count grows.
  - RAG-MCP reports 43% selection accuracy with retrieval against 14% with every tool
    in the prompt.
  - Anthropic's Tool Search raised accuracy from 49% to 74% on Opus 4.
  - OpenAI advises "fewer than 20 functions available at the start of a turn".
  - Anthropic and OpenAI both suggest grouping related tools under shared prefixes or
    namespaces.

  Sources: [LongFuncEval](https://arxiv.org/abs/2505.10570),
  [RAG-MCP](https://arxiv.org/abs/2505.03275),
  [Anthropic, advanced tool use](https://www.anthropic.com/engineering/advanced-tool-use),
  [Anthropic, writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents),
  [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling).
  Downgraded to low for this question: these studies measure full tool schemas, and
  this pack's misses are no-fires, not wrong picks. None of them tests a mode skill
  against narrow skills. Only community posts claim that "I do everything" descriptions
  are ignored, and none of those was fetched.

### What the narrow descriptions got wrong before C

This section diagnoses the descriptions as they stood before 1.0.4, at commit
`d5e916d7c`. Option C replaced them.

- **[moderate]** The nine narrow skills fired far less on the fresher query set.
  Averaged over the nine groups, the pre-fold rate was 0.93 on the 2026-10-11 set and
  0.57 on the 2026-10-13 set. That gap is larger than any fold's loss, so every
  comparison must be paired on one set. Source:
  [verification ledger](../../specs/intent-longer-and-supervised-verbs/notes/verification-ledger.md).
  Downgraded: the two worlds also differed in their listings. The 2026-10-13 world
  listed `navigate-intents`, which the 2026-10-11 world did not, and either world may
  have overflowed the listing budget. The newer queries look less like the skills' own
  words, but that is a reading of the queries, not a measured property.
- **[low]** The weakest skills open with internal sequence vocabulary, while the
  strongest name an artifact the user would say:

  | Skill | Opening words of the description | 10-11 set | 10-13 set |
  | --- | --- | ---: | ---: |
  | `lean-canvas` | "…an initiative brief through an adapted Lean Canvas…" | 1.00 | 1.00 |
  | `identify-opportunities` | "Use at step 2 of the PE shaping sequence…" (then "JTBD jobs") | 1.00 | 0.73 |
  | `frame-domain` | "…grounding a product in the real-world activity…" | 1.00 | 0.67 |
  | `explore-options` | "…generate multiple candidate product shapes…" | 1.00 | 0.67 |
  | `map-capabilities` | "Step 6 (terminal) of the PE six-step shaping sequence." | 0.80 | 0.67 |
  | `frame-situation` | "…holding a raw signal (market observation, OKR gap…)" | 1.00 | 0.47 |
  | `plan-validation` | "…turn a converged product's load-bearing assumptions into a validation plan…" | 0.87 | 0.40 |
  | `diverge-solutions` | "Use at step 3 of the PE shaping sequence…" | 1.00 | 0.33 |
  | `place-bet` | "Step 5 of the PE six-step shaping sequence — the bet-commitment gate." | 0.67 | 0.20 |

  `place-bet` and `diverge-solutions` carried no trigger phrases at all. The held-out bet
  queries say "make the call", "choose between", "commit… fund", and "write the decision
  record". None of those phrasings appeared in the old `place-bet` description. [synthesis,
  local descriptions and queries] Downgraded: nine skills, five queries each, and no
  controlled test of wording.
- **[high]** Vendor guidance agrees on the fix in principle. Say what the skill does and
  when to use it. Put the key use case first. Use the words users would say. Anthropic
  adds that "even small refinements to tool descriptions can yield dramatic
  improvements". Sources:
  [Claude best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices),
  [Claude Code skills](https://code.claude.com/docs/en/skills),
  [Codex skills](https://learn.chatgpt.com/docs/build-skills),
  [Gemini best practices](https://geminicli.com/docs/cli/skills-best-practices/),
  [Anthropic, writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents).
  The advice is high. No source measures how much it gains, so the size of the gain is
  `[uncertain]`.

### What the shipped rewrite shows

Option C shipped on 2026-10-14 in `product-engineering` 1.0.4
([PR #1559](https://github.com/eugenelim/agent-ready-repo/pull/1559)). The evidence
below was gathered on the shipped text.

- **[moderate]** On the three skills that have committed eval files, the rewrite holds
  activation. Each query ran three times in each version, with zero errored runs:

  | Skill | Queries passed, before → after | Positive rate, before → after | False triggers |
  | --- | ---: | ---: | ---: |
  | `explore-options` | 12/14 → 12/14 | 0.714 → 0.667 | 0 → 0 |
  | `frame-domain` | 16/17 → 15/17 | 0.852 → 0.815 | 0 → 0 |
  | `plan-validation` | 13/15 → 13/15 | 0.750 → 0.750 | 0 → 0 |

  Each remaining drop is one query moving one run of three. Downgraded: 46 queries, and
  the eval files were written against the old descriptions' trigger phrases, so they
  favour the old wording. They cannot show a gain on paraphrased requests.
- **[moderate]** The rewrite created no wrong picks among the probe's cases. The
  24-case cold probe routed 72 of 72 runs to the right skill, with every case at high
  confidence in at least two of three runs. Downgraded: the probe is forced choice, so
  it measures routing, not activation, and it has no negative cases.
- **[moderate]** A trigger phrase is also fencing. A first draft of `plan-validation`
  added "write an interview guide". That made "Design the research study for customer
  interviews", a query the skill should not take, fire it in 3 of 3 runs. Removing the
  phrase brought it back to 0 of 3. The eval file's negatives caught this; the probe has
  no such case and did not. Six of the nine skills have no eval file, so nothing would
  catch the same slip in them. Downgraded: one observed case.

### What listing cost really is

- **[high]** Listing cost is catalogue-wide. Description characters, as parsed
  description text:

  | Surface | Skills | Before C (2026-10-13) | After C (2026-10-14) |
  | --- | ---: | ---: | ---: |
  | Core | 21 | 10,552 | 10,671 |
  | `experience-design` | 12 | 9,534 | — |
  | `desk-research` | 12 | 8,901 | — |
  | `product-engineering` | 13 | 8,654 (8,670 just before C) | 6,412 |
  | The nine longer-route skills | 9 | 5,059 | 2,801 |
  | Whole catalogue | 132 | 73,412 | about 71,300 |

  Core grew between the two dates through its own releases, and two `product-engineering`
  releases added 16 characters before C; the other packs were not re-measured. Before C, the nine were 58% of this pack and 6.9% of the catalogue. C
  saved 2,258 characters, about 3% of the catalogue. Core alone is 33% over Codex's
  8,000-character fallback. Sources: the
  [routing survey](pe-skill-routing-survey.md) for Codex's budget; local measurement for
  the counts. [synthesis]
- **[moderate]** A length cap alone cannot fit a profile into Codex's fallback. At 8,000
  characters, a profile holds about 20 skills at 350 characters each, after names.
  Core plus this pack is 34 skills, which would need about 210 characters each.
  Fitting Codex's fallback therefore means smaller profiles, or adopters raising
  `skills.max_context_tokens`. [inference, from the counts above]
- **[uncertain]** The activation harness may itself overflow Claude Code's listing. The
  slice 1b three-pack world's pack descriptions totalled about 22,360 characters (Core
  10,552, `product-engineering` 8,654, `architect` 3,154), before the host's built-in
  skills. Today's projection is about 20,240 (Core 10,671, `product-engineering` 6,412,
  `architect` 3,154).
  The open variable is the harness model's context window, which no record names. At
  1% of 200,000 tokens, the budget is about 2,000 tokens, or roughly 8,000 characters,
  and the listing overflows. At 1% of 1,000,000 tokens, it is about 40,000 characters,
  and it does not. The recorded skill lists hold names only. [inference]
  - If overflow happened, it biased against the narrow skills. The pre-fold worlds
    listed 53 to 54 skills; the fold worlds listed 44 to 46. So the measured fold losses are,
    if anything, understated.
  - Experiment 0 closes this.

## Options

"Listing cost" counts description characters for the nine skills, or what replaces
them. "Churn" means renames, retired names, or install changes that adopters see.

| Option | Activation evidence | Collisions | Listing cost | Adopter churn | Host coverage |
| --- | --- | --- | --- | --- | --- |
| **A. The pre-1.0.4 baseline:** `intent` for the short route, nine narrow skills with the old descriptions | Measured baseline: 0.93 / 0.57 on the two sets for the nine groups | None measured (24 of 24 probe) | 5,059 | None | All five |
| **B. Thin router `intent`, every step narrow again** (re-split `frame`, `de-risk`, `decompose`) | Untested. Might recover `de-risk` (0.70 → 0.53), but slice 1 passed overall | Low. The router overlaps every step's triggers | About +800 more (three descriptions back, smaller router) [inference] | High: re-adds names that slice 1 just retired, with no aliases (ADR-0054) | All five |
| **C. Shorter narrow descriptions** (shipped in 1.0.4): artifact noun and user words first, minimal fencing | Eval files: 40 of 46 pass, against 41 of 46 before. Held-out effect unmeasured (Experiment 1) | None: probe 72 of 72. One new trigger phrase pulled a neighbour's request until it was removed | 2,801 (−2,258, −45%) | None: names unchanged | All five |
| **D. Move the nine to an optional pack, or into `product-strategy`** | Same per-skill activation where installed. Zero where not installed | None new | 0 for adopters who skip the pack; 2,801 where installed | Medium: a pack split, a profile change, and cross-pack hand-offs | All five |
| **E. Catalogue-wide description budget and install profiles** | No direct effect. Indirect if overflow is dropping descriptions | None | Catalogue-wide. A 350-character cap holds a 20-skill profile near 8,000 | Low per pack, but every pack is touched | All five. Profiles are pack-grained today (`profiles/*.toml`) |
| **F. Fold only distinctive-noun steps** (for example `canvas` and `find` into `intent`) | Partly measured: canvas 1.00 → 0.93, find 0.73 → 0.80 | Low | Saves at most 959. But `intent` is at about 1,000 of 1,024 characters, so its description has no room to name more modes | Medium: two retired names | All five |
| **G. Claude Code's `when_to_use` for extra trigger text** | Untested here. Adds text, not reach | None | Adds characters on Claude Code only | None | One host |
| **H. A forced-evaluation prompt hook** (a hook that tells the model to check every skill before answering) | One independent study (the sandboxed-evals post): about 50% → 100% on 22 prompts, but more false triggers on no-skill prompts | Raises the false-trigger risk | 0 in the listing; the hook text costs context on every turn | None | Claude Code only (hooks are host-specific) |
| **I. Explicit-only for rare steps** (`disable-model-invocation` or Codex's `allow_implicit_invocation: false`), reached through the `intent` route hand-off | Activation goes to zero by design. Reach depends on the route mode naming the step | None | Saves each hidden skill's characters | Low: names unchanged, behavior changes | Four hosts. Gemini CLI disables only per user |

### Why C came first, and why D is the runner-up

- C targets the measured failure: a skill that should fire stays silent. The fresher
  set's rate of 0.57 leaves the most room to gain, and C costs adopters nothing.
- C saved about 3% of the catalogue listing. It cannot bring any profile under Codex's
  fallback on its own. E sets the rule for that across packs, but only smaller profiles
  or a raised Codex budget actually fit.
- D is the clean answer if removing the nine raises activation of the skills that stay,
  or if a profile must fit 8,000 characters. It costs a pack split and cross-pack
  hand-offs, and it removes the longer route from the default install.
- B and F reopen folds the evidence has already priced. G and H reach one host. I gives
  up natural-language reach for the steps it hides.

## Experiments that remain

Experiment 1 checks whether shipped C kept or raised activation on paraphrased
requests. Experiment 2 decides whether D is worth its churn. Experiment 0 sets the
listing budget both of them run under.

### The harness

The driver is the slice 1b scratch driver. It is not committed, so this is its
contract, enough to rebuild it:

- It calls `pack_evals.run_eval` (in `packages/agentbundle/agentbundle/commands/pack_evals.py`)
  unchanged, with a subclass of `ClaudeCodeDetector`.
- The subclass runs `claude -p <query> --output-format stream-json --verbose
  --allowed-tools Skill --setting-sources project,local`, parses the result with
  `pack_evals.parse_activation`, and logs every fired skill per run.
- The packs are projected into OS temporary directories outside every repository. Each
  parallel job gets its own copy of the projection.
- Each query runs three times. Scored records hold zero errored runs: a query with any
  errored run is re-run whole. Host usage limits forced such re-runs in slice 1b.

The rules from slice 1b carry over:

- Record every candidate description's SHA-256 before writing the held-out set.
- Write a fresh held-out set that matches no earlier set, eval file, or probe case.
- Make sure no five-word run from any query appears in a description.

### Experiment 0: does the harness listing overflow? (one session, run first)

1. Build the three-pack projection (`product-engineering`, Core, `architect`).
2. Run one `claude -p --debug` session in it, and record the model and its context
   window from the session's init event.
3. Read the debug log for the listing-overflow warning, and count the entries that kept
   their description.

- **No overflow:** Experiments 1 and 2 run at the host default.
- **Overflow:** Experiment 1 runs with `skillListingBudgetFraction` raised until no
  description drops, so it measures wording, not truncation. Experiment 2 still runs at
  the host default, because truncation is part of what D changes for adopters. Earlier
  absolute rates are then known to be measured under truncation.

### Noise, measured inside each experiment

The 0.019 standard error from slice 1b came from a set where the rate was 0.856 and only
4 of 60 positives changed between runs. A set near 0.57 has many more mixed queries, and
its standard error is probably 0.04 to 0.05. So each experiment measures its own:

- Run the control arm twice.
- Take the per-query difference between the two control runs. Its standard deviation
  divided by the square root of the positive count is the standard error, called SE
  below.
- State every result in SE units, with an absolute floor so a lucky quiet run cannot
  set a tiny bar.

### Experiment 1: did the shipped rewrite hold activation? (keeps or reverts C)

- **Arms:** A (the nine descriptions before 1.0.4, at commit `d5e916d7c`), A again (for
  SE), and C (as shipped in 1.0.4). Same projection and model, paired on one query set.
- **Set:** 66 fresh queries.
  - 54 positives, six per skill, written as a user would ask, without the skill's own
    nouns.
  - 12 negatives, two each owned by `intent`, `discovery-loop`, `intake-intent`,
    `new-spec`, `work-intake`, and `architect-design`. All six are in the three-pack
    projection.
- **False trigger:** a run on a negative query in which any of the nine skills fires.
  The bound is at most 1 of 36 negative runs (0.03).
- **Probe:** already passed for C. 24 cases × 3 cold runs routed 72 of 72 right, every
  case at least two of three runs at high confidence.
- **Cost:** 66 queries × 3 runs × 3 arms = 594 headless sessions.

Let D1 = C's positive rate minus the mean of the two A runs. SE is computed against that
same mean. C is held to the loss limit that rejected the folds: 0.03.

| Outcome | Bound | Reading |
| --- | --- | --- |
| C wins | D1 ≥ max(0.06, 3 SE), false triggers ≤ 1 of 36 | Keep C. Apply the same rewrite rules under E. |
| C holds | D1 − 2 SE > −0.03, false triggers ≤ 1 of 36 | Keep C for the 45% listing cut. Activation is neutral. |
| C fails | D1 ≤ −0.03, or false triggers > 1 of 36 | Revert the flagged skills below. Get listing savings from D or I instead. |
| Inconclusive | D1 > −0.03 but D1 − 2 SE ≤ −0.03 | The noise is too wide to rule out a loss past the limit. Double the positives to 108 and re-run all three arms. |

At an SE near 0.045, "C holds" needs D1 above about 0.06, so a neutral C will often read
as inconclusive on 54 positives. Sizing the set at 108 positives from the start avoids
one round. [inference]

Each skill is also checked on its own, against its own control spread. For each skill,
take the larger of 0.17 (one query's worth) and twice the gap between its two A runs. A
skill is flagged when its C rate falls below its mean A rate by more than that, or falls
to 0 from a non-zero A rate. A flagged skill goes back to its old description. The mixed
set is then run once more as its own arm (198 sessions) and must meet "C holds".

### Experiment 2: does removing the nine raise activation of the skills that stay? (decides D)

D's benefit, if any, goes to the skills that remain installed. So this experiment
removes exactly the nine and measures the rest.

- **Arms:** the three-pack world as today, run twice (for SE), and the same world with
  the nine removed. All arms run at the host default budget.
- **Set:** 66 fresh queries. 54 positives for skills that stay under D: 18 for `intent`
  (six per mode), and six each for `discovery-loop`, `intake-intent`, `work-intake`,
  `new-spec`, `bug-fix`, and `architect-design`. 12 negatives that no skill in either arm
  owns, so neither the nine nor the remaining skills should fire.
- **False trigger:** a run on a negative query in which any skill fires. Both arms must
  stay at or below 1 of 36 negative runs.
- **Cost:** 66 queries × 3 runs × 3 arms = 594 headless sessions.

Let D2 = the rate with the nine removed minus the mean of the two runs today.

| Outcome | Bound | Reading |
| --- | --- | --- |
| Removal helps | D2 ≥ max(0.06, 3 SE) | The nine's listing silences other skills. Raise D, and E's profile sizing, to the next change. |
| No effect | D2 < max(0.04, 2 SE) | The nine cost budget only. Keep C and pursue E. D stays in reserve for profiles that must fit 8,000 characters. |
| Unclear | max(0.04, 2 SE) ≤ D2 < max(0.06, 3 SE) | Repeat the removal arm once before deciding. |

## Known unknowns

- **Known-unknown:** whether the slice 1b harness listing overflowed Claude Code's budget.
  Would be closed by: Experiment 0.
- **Known-unknown:** whether shipped C raised or lowered activation on paraphrased
  requests. Would be closed by: Experiment 1.
- **Known-unknown:** how the six skills with no eval file behave after C:
  `frame-situation`, `identify-opportunities`, `diverge-solutions`, `place-bet`,
  `map-capabilities`, and `lean-canvas`. Would be closed by: an eval file for each,
  including negatives owned by its nearest neighbour.
- **Known-unknown:** activation on Codex, Cursor, Copilot, and Gemini CLI. Every rate
  here is Claude Code only. Would be closed by: a headless run of the same held-out set
  on each host, which needs a detector per host in `pack_evals`.
- **Known-unknown:** whether Cursor, Copilot, and Gemini CLI cap the listing. Their docs
  state no limit. Would be closed by: installing the full catalogue on each host and
  inspecting what the model sees.
- **Known-unknown:** Codex's exact overflow order: which descriptions it shortens first,
  and by how much. Would be closed by: reading the Codex source or a Codex listing test.
- **Known-unknown:** whether a pushy or directive description ("Use whenever…") raises
  activation without raising false triggers. One unfetched community post claims 100%
  against 37%. Would be closed by: a fourth arm in Experiment 1.
- **Unknowable:** whether these results hold on the next model release. Why not:
  activation baselines move with each release, and the measured runs pin one model at
  one time. Re-run the harness after a model change instead.

## Sources

Primary (vendor documentation, fetched 2026-10-13):
[agentskills.io spec](https://agentskills.io/specification) ·
[Claude Code skills](https://code.claude.com/docs/en/skills) ·
[Claude best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) ·
[skill-creator SKILL.md](https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md) ·
[Codex skills](https://learn.chatgpt.com/docs/build-skills) ·
[Cursor skills](https://cursor.com/docs/context/skills) ·
[VS Code agent skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills) ·
[GitHub about agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) ·
[Gemini CLI skills](https://geminicli.com/docs/cli/skills/) ·
[Anthropic, writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) ·
[Anthropic, advanced tool use](https://www.anthropic.com/engineering/advanced-tool-use) ·
[OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling).
The Codex page is where `developers.openai.com/codex/skills` redirects. The Gemini best-practices page is cited through the
[routing survey](pe-skill-routing-survey.md).

Academic preprints (abstracts only):
[LongFuncEval](https://arxiv.org/abs/2505.10570) ·
[RAG-MCP](https://arxiv.org/abs/2505.03275).

Practitioner, fetched, counted as one independent source because both posts share one
author:
[sandboxed activation evals](https://scottspence.com/posts/measuring-claude-code-skill-activation-with-sandboxed-evals) ·
[making skills activate](https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably).

Not fetched, cited only as a claim: the community post behind the "100% against 37%"
figure in Known unknowns.

Local evidence:
[slice 1b verification ledger](../../specs/intent-longer-and-supervised-verbs/notes/verification-ledger.md) ·
[routing evidence](../../specs/intent-longer-and-supervised-verbs/notes/routing-classification-evidence.md) ·
[slice 1 verification ledger](../../specs/intent-short-route/notes/verification-ledger.md) ·
[RFC-0107](../../rfc/0107-verb-mode-shaping-and-intake-with-slice-handover.md) ·
[ADR-0145](../../adr/0145-shaping-entry-points-intent-and-initiative.md) ·
[routing survey](pe-skill-routing-survey.md).
