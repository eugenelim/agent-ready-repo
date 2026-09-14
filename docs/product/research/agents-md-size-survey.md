# Survey: does root `AGENTS.md` size and ordering change whether rules are followed?

- **Mode:** desk-research `deep` (academic / primary-source discipline)
- **Run date:** 2026-09-13
- **Companion:** [`agents-md-size-counterpoints.md`](agents-md-size-counterpoints.md)

> **Read the counterpoints before acting on this file.** The adversarial pass
> retracted Finding 7 outright, downgraded Findings 1, 6 and 8, returned a
> do-not-resolve verdict on Finding 2, and flagged eight figures below as
> sourced from retriever characterisation rather than from an abstract this
> author read. Ratings in this document are pre-review.

## The question, and the decision it feeds

This repository ships a root `AGENTS.md` of ~6,700 characters (~920 words,
~1,600 tokens) that hosts load on their own. It points at `AGENT_RULES.md`,
which points at `.agents/rules/cognitive-load.md`. Those last two hops are
model-directed tool calls, and they were skipped for a whole session — the
agent never read either file and breached the rule throughout.

Three other carriers were ruled out before this research started: per-prompt
hook injection (context cost, and unconfirmed per-prompt firing across five
adapters), `SessionStart` hooks (inconsistent across adapters, gitignored and
absent in practice), and per-adapter rule files (assumes every adapter behaves
alike). The root file is the only portable carrier left.

So the proposal is to inline ~535 tokens of cognitive-load rules into root
`AGENTS.md`, front and center, taking it from ~1,600 to ~2,150 tokens and from
~40–50 distinct normative statements to roughly 60.

Three questions decide it:

1. Does a root instruction file lose adherence as it grows, and is ~2,150
   tokens anywhere near the point where that starts?
2. Is ordering inside the file a real lever, or folklore?
3. Does promoting one rule cost adherence for what it displaces?

## Method and its limits

Retrievers used: `WebSearch` and `WebFetch` via five parallel
`evidence-retriever` subagents, one per sub-question. The bundled
`arxiv-retriever.py` was **unavailable** — the arXiv API returned HTTP 429 on
every attempt across three direct probes, so the structured arXiv path was
lost. Web search still reached arXiv abstract pages, so coverage was preserved
by a slower route.

**Every arXiv citation below was independently verified** by fetching
`arxiv.org/abs/<id>` and reading the `citation_title` and `citation_date`
metadata. Sixteen of sixteen resolved with matching titles. This check was run
because the retrievers returned several 2026-dated identifiers and marked
authorship "not extracted" on six of them. One attribution error was caught and
corrected this way (see Finding 1).

## Findings

### Finding 1 — File size does not detectably change adherence, and that null is affirmatively supported `[moderate]`

The only controlled study of this exact question is McMillan, *Instruction
Adherence in Coding Agent Configuration Files: A Factorial Study of Four
File-Structure Variables* (arXiv:2605.10039, 2026-05-11). It manipulated four
variables — file size, instruction position, file architecture (inline vs.
pointer), and contradictions in adjacent files — across **1,650 Claude Code CLI
sessions and 16,050 function-level observations**, on two TypeScript codebases,
three frontier models (primarily Sonnet 4.6, with Opus 4.6 as a CLI-matched
cross-model check and Opus 4.7 descriptive under a CLI-version confound), and
five coding tasks. Analysis used mixed-effects models with a Bayesian
companion.

Result: no structural variable and no two-way interaction produced a detectable
contrast after multiple-testing correction.

**The nulls are not equal, and this is the single most important nuance in the
survey.** Quoting the abstract directly:

> Size and conflict nulls are supported by affirmative-null Bayes factors
> (BF10 between 0.05 and 0.10); position and architecture nulls are failures to
> reject without Bayes-factor support.

So size has *affirmative evidence of no effect*. Position and architecture are
merely **unproven in either direction** — the study could not detect an effect,
and could not support its absence either. Any claim that this paper licenses
"position doesn't matter" is misreading it.

Confidence is `[moderate]`, not `[high]`, on three named downgrades: it is a
single study (triangulation fails — no independent replication exists); it is an
arXiv preprint, not peer-reviewed; and its compliance target was "a trivial
target annotation", which may be easier to comply with than a prose style rule.

*Correction to the retrieved record:* this paper was returned attributed to
"Lester et al." and described as peer-reviewed. Verified authorship is **Damon
McMillan**, single author, and arXiv preprints carry no peer review.

### Finding 2 — Vendor guidance says the opposite of Finding 1, and cites nothing `[high]`

Anthropic's Claude Code memory documentation states plainly:

> target under 200 lines per CLAUDE.md file. Longer files consume more context
> and reduce adherence.

and, separately, "Shorter files produce better adherence." No study, benchmark,
or number backs the adherence half of that claim. It is stated design
rationale.

This is a direct, unresolved conflict with Finding 1's affirmatively-supported
size null. Both cannot be right as stated. Confidence is `[high]` **on the fact
that the vendor says this** — not on the claim being true.

### Finding 3 — Hard limits and truncation differ sharply by host, and one truncates silently `[high]`

| Host | Hard limit | Truncation behaviour | Ordering guidance |
| --- | ---: | --- | --- |
| Claude Code | 4 MiB (file skipped above) | Loads in full below cap; `MEMORY.md` truncates at 200 lines / 25 KB **with an error returned** | Root → working directory; `CLAUDE.local.md` after `CLAUDE.md` |
| OpenAI Codex | 32 KiB, combined across all discovered files | **Silent truncation**, no TUI warning | Root → cwd concatenation; override files win |
| GitHub Copilot | "no longer than 2 pages" | Not documented | Personal > Repository > Organization |
| Cursor | 500 lines per rule (secondary attribution) | Not documented | Not documented |
| Gemini CLI | Not documented | Not documented | Global → project → just-in-time |
| agents.md standard | None — spec imposes no limit | Not documented | None; "use any headings you like" |

Two operational facts matter here. Codex's `PROJECT_DOC_MAX_BYTES = 32 * 1024`
truncates **silently** — GitHub issue openai/codex#7138 was filed by a user who
discovered it only by reading source after authoring a ~40 KB file. And that
budget is *combined across all discovered files*, not per file, so a scoped
`AGENTS.md` tree shares one ceiling.

At ~2,150 tokens (~8.6 KB), the proposal sits far below every published limit.
The nearest ceiling is Codex's 32 KiB combined budget, and only if many scoped
files are present at once.

Confidence `[high]`: these are primary vendor documents and source code, quoted
directly.

### Finding 4 — Instruction-count degradation is real and steep, but measured on instruction shapes unlike ours `[moderate]`

Two benchmarks vary instruction count as an independent variable:

**ManyIFEval** (Harada et al., *When Instructions Multiply*, EMNLP 2025
Findings, arXiv:2509.21051) holds the task description fixed and varies
instruction count 1→10. Prompt-level accuracy — all instructions satisfied at
once:

| Model | 1 instruction | 5 | 10 |
| --- | ---: | ---: | ---: |
| GPT-4o | 0.94 | 0.57 | 0.21 |
| Claude 3.5 Sonnet | 0.95 | 0.72 | 0.48 |
| Gemini 1.5 Pro | 0.96 | 0.71 | 0.39 |

Decline is monotonic with no cliff. A logistic regression on instruction count
alone predicts performance to roughly 10% error.

**IFScale** (Jaroslawicz et al., *How Many Instructions Can LLMs Follow at
Once?*, arXiv:2507.11538) runs 10→500 keyword instructions across 20 models and
finds three distinct decay shapes: threshold decay (near-perfect to ~150–250,
then a sharp drop), linear decay (steady slope from 10), and exponential decay
(rapid early loss, floor of 7–15%). Best frontier models reach 68% at 500.

**Why this only partly transfers.** Both benchmarks measure *prompt-level*
accuracy on simple verifiable instructions — keyword inclusion, format rules. A
root `AGENTS.md` is not scored all-or-nothing, and its statements are prose
norms, not checkable string constraints. Neither benchmark reports numbers in
the 10–60 window in text form. Downgrades: construct mismatch, and no study
separates instruction count from instruction token length (the two are
confounded by construction in every design retrieved).

### Finding 5 — Any size or count threshold is model-vintage-specific and decays as a claim `[moderate]`

This finding was added after the requester observed that behaviour is
model-dependent and moves fast. The evidence supports that directly, and it
reframes the whole question.

IFScale's three decay patterns are **model-family properties**, not a universal
curve — Claude 3.7 Sonnet and GPT-4.1 show linear decay from the start, while o3
and Gemini 2.5 Pro hold near-perfect to ~150–250 instructions. Same benchmark,
same task, opposite shapes.

A 2026 follow-up (Arize AI, *Models got an order of magnitude better at
following instructions in one year*) reports the threshold-decay boundary moving
from ~150–250 instructions in 2025 top models to ~2,000 in 2026 frontier models,
with GPT 5.5 holding 99% through N=5,000. This is a vendor-adjacent blog post
with no peer review, so it carries `[low]` weight on its own numbers — but its
*direction* is corroborated by the factorial study independently choosing Sonnet
4.6 / Opus 4.6 / 4.7 as its frontier baseline in mid-2026.

The consequence for this repository is structural, not numeric: **a size budget
derived from today's models is a claim with a shelf life, and it is not portable
across the five adapters, which run different models.** Any rule of the form
"keep it under N" inherits the exact failure mode this repository already
documents — a rule that is loaded, cited as authority, and unfalsifiable.

### Finding 6 — Position effects are unmeasured at this scale, and the short-context evidence points the opposite way `[low]`

"Lost in the Middle" (Liu et al., TACL 2024) is the canonical primacy/recency
source, but its experiments start at ~10 documents — roughly **3,000–6,000
tokens minimum**, rising to ~15,000. The U-curve is documented there. It was
**not tested at ~2,000 tokens**. The FLenQA follow-up puts the onset of
positional accuracy loss at around 3,000 tokens.

*Serial Position Effects of Large Language Models* (arXiv:2406.15981) finds
primacy in 73 of 104 model-task combinations, and that attention shifts toward
the input's beginning **as input length increases** — which says the effect
grows with length rather than holding at short length.

Pointing the other way: *Layer-wise Positional Bias in Short-Context Language
Modeling* (arXiv:2601.04098) finds that in short contexts **recency bias
increases monotonically across layers while primacy diminishes with depth**. If
that generalises to instruction compliance, the important rule belongs *last*,
not first — the opposite of standard practitioner advice. It is a
word-prediction study, so the generalisation is an `[inference]`, not a finding.

OpenAI's GPT-4.1 prompting guide recommends placing instructions at both the
beginning and end of context, and says "above" beats "below" if used once. It
attributes this to internal testing and publishes no methodology, sample size,
or effect size.

**The honest answer: no published study moves a single rule from top to bottom
of a ~2k-token instruction block and measures downstream compliance.** The
factorial study is the closest, and its position null has no Bayes-factor
support. "Front and center" is unproven in both directions at this scale.

### Finding 7 — RETRACTED. Displacement has been measured, and it is negative `[low]`

> **Retracted by the adversarial pass.** The original claim — "the displacement
> cost of promotion has never been measured" — was false, and rested on this
> author mischaracterising arXiv:2603.13351 by attributing IFScale's results to
> it. Corrected text follows; full reasoning in the counterpoints.

The nearest direct measurement is *Prompt Complexity Dilutes Structured
Reasoning* (arXiv:2603.13351). A reasoning framework scored **100% in isolation
and 0–30% inside a "60+ line production prompt which had evolved through
iterative additions of style guidelines, format instructions, and profile
features"**, on Claude Sonnet 4.6. The named mechanism is a style directive —
"Lead with specifics" — forcing conclusion-first output and reversing the
reasoning order. That is displacement caused by exactly the kind of content this
decision proposes to add.

It is weak evidence: 20 trials per condition, one problem, single author citing
their own prior work. It still points against pure addition.

Supporting it, *On the Paradoxical Interference between Instruction-Following and
Task Solving* (arXiv:2601.22047) finds that inserting a **self-evident**
constraint — one already satisfied by the original successful output — still
produces substantial performance drops, including on Claude Sonnet 4.5, with
failing cases allocating more attention to constraints than succeeding ones.
Displacement with the benefit held at zero.

What remains genuinely unmeasured is the narrower question of whether *promoting*
an existing rule costs less than *inserting* a new one. Adjacent conflict
research does not answer it:
- *On the Paradoxical Interference between Instruction-Following and Task
  Solving* (arXiv:2601.22047) — adding a self-evident constraint to a
  previously-solved prompt costs task performance; 32B–72B models retain
  64.9%–82.3%. Failing cases allocate *more* attention to constraints, implying
  attention is a displaced finite resource.
- *Control Illusion* (arXiv:2502.15851) — constraints hit 74.8–90.8% compliance
  in isolation, but when two conflict, obedience to the designated
  higher-priority one falls to 9.6–45.8%, and models acknowledge the conflict
  only 0.1–20.3% of the time.
- *PRIME* (arXiv:2606.22470) — on incompatible instructions, 70% of responses
  follow at least one, 30% follow neither, with a 48–50% first-directive bias.

All four concern *conflicting* or *density-maximal* instructions. The
cognitive-load rules do not conflict with the existing `AGENTS.md` content;
they govern a different surface (chat prose vs. code and process). So the
nearest evidence is about a case that is not ours.

Rated `[uncertain]` rather than listed as a gap because there *is* a
directional claim — the literature leans toward a constrained-resource view over
independence — but the grounds for applying it here are weak.

### Finding 8 — Long sessions, not file structure, carry the largest measured effect `[moderate]`

The factorial study's headline is not a null. Its largest measured effect is
**within-session decay: each additional function the agent generates is
associated with ~5.6% lower odds of compliance per step (OR = 0.944)**,
reproduced on a second codebase and on Opus 4.6 at matched configuration. The
authors flag it as identified during analysis rather than pre-specified, and
non-monotonic rather than a constant per-step effect.

Multi-turn benchmarks corroborate the shape independently. Multi-IF
(arXiv:2410.15553) finds all 14 tested models degrade monotonically with turn
count — o1-preview falls from 87.7% at turn 1 to 70.7% at turn 3. MT-Eval
(arXiv:2401.16745) finds every model except GPT-4 struggling to hold initial
global instructions as conversations lengthen.

Three independent sources, consistent direction, so `[moderate]` despite the
post-hoc identification in the primary source.

**This matches the observed failure exactly.** The rule was breached over a long
session, not in the first reply. That points at persistence, not at where the
text sits in the file.

### Finding 9 — Community size heuristics are a cargo cult `[moderate]`

The "under 200 lines", "150–200 instruction ceiling", and "degrades past 500
words" figures recur across many posts attributed to research. The *AGENTS.md
Field Guide, 2026* explicitly flags that the line-budget heuristic "comes from
one widely-cited blog post, not a study". The one authoritative source for the
200-line figure is Anthropic's own docs — design guidance, not measurement
(Finding 2).

One practitioner benchmark does report an ordering effect: a 30-day, 12-developer,
~17,000-request trial claims rules at the bottom of the file were ignored 43%
more often than rules at the top, and that both Cursor and Copilot degrade past
~1,200 tokens of instructions. It is self-published on an unverified site, is a
single team, and the 43% figure appears nowhere else. Rated `[low]` on its own;
noted because it is the only ordering measurement found outside the factorial
study, and it disagrees with it.

Separately, a corpus study of **2,303 public context files** (*Agent READMEs*,
arXiv:2511.12884) gives real size distributions: median 485 words for Claude
Code, 535 for Copilot, 335 for Codex. It measures no adherence, so it sets a
convention baseline only. Our current file at ~920 words already sits near twice
the community median; the proposal takes it to ~1,320.

## What this means for the three decision questions

**1. Is ~2,150 tokens near a degradation threshold?** No published evidence says
so, and the one controlled study affirmatively supports no size effect
(Finding 1). Every vendor ceiling is far above it (Finding 3). The countervailing
claim is Anthropic's own uncited guidance (Finding 2). On the instruction-count
axis the proposal lands near 60 statements, which sits above ManyIFEval's tested
ceiling of 10 and below IFScale's threshold-decay knee for strong models
(Finding 4) — but those benchmarks score all-or-nothing on checkable
constraints, which `AGENTS.md` is not.

**2. Is ordering a real lever?** Unproven at this scale. The canonical
primacy/recency evidence begins around 3,000 tokens (Finding 6); the factorial
study's position null has no affirmative support; the one short-context
architectural result points toward recency, favouring *last* over *first*; and
the only practitioner measurement claiming a large ordering effect is a single
unreplicated self-published trial (Finding 9). "Front and center" is a
defensible editorial choice. It is not an evidence-backed performance lever, and
should not be sold as one.

**3. Does promotion cost the displaced rules?** *Adding* instructions has a
measured cost, twice over, including the case where the added constraint was
already satisfied (Finding 7, as corrected). Whether *promoting* an existing rule
is cheaper than adding a new one is still unmeasured. The practical consequence:
prefer promoting-and-pruning over pure addition, because every study that
measured a displacement cost measured it for added instructions.

**The finding that most deserves to change the plan is Finding 8.** The largest
measured effect on adherence is session length, not file structure — and that is
precisely the shape of the observed failure. No static placement in a file
addresses a within-session decay effect.

The case for inlining rests on a mechanism, not on an adherence measurement: it
removes two hops that were provably skipped in this repository. That gain is real
regardless of how the size question resolves. What the original version of this
section did — conclude "no evidenced downside, so there is no reason not to do
it" — converted absence of evidence into evidence of absence, in a document
written to warn against exactly that. The adversarial pass sustains the direction
and attaches three conditions: name the kill condition before changing anything,
apply Anthropic's own "would removing this line cause a mistake?" test to each
added bullet, and prefer promoting-and-pruning to pure addition.

Finding 5 constrains how any of this may be written down: a numeric size budget
would be model-vintage-specific, non-portable across five adapters, and
unfalsifiable in exactly the way this repository already knows how to fail.

## Known unknowns

- **Known-unknown:** does the factorial study's size null replicate on prose
  style rules rather than "a trivial target annotation"? Would be closed by:
  re-running its design with a compliance target that is a writing-style
  constraint, which is the artifact class this repository actually cares about.
- **Known-unknown:** what is the adherence curve between 10 and 60 distinct
  instructions? Would be closed by: ManyIFEval extended past its 10-instruction
  ceiling, or IFScale reporting its 10–60 window numerically rather than only in
  figures.
- **Known-unknown:** does the U-shaped position effect exist at ~2,000 tokens?
  Would be closed by: a replication of Liu et al.'s design at 2k context, which
  no retrieved study has run.
- **Known-unknown:** does promoting an existing rule cost less than inserting a
  new one? Would be closed by: a factorial design varying promotion and
  insertion separately against per-rule adherence.
- **Known-unknown:** do the four non-Claude adapters truncate, reorder, or drop
  a ~2,150-token root file in practice? Would be closed by: running the file
  through each host and inspecting what arrives — Gemini CLI exposes
  `/memory show` for exactly this.
- **Unknowable, as posed:** what the "right" size limit is for this repository's
  file across all five adapters. Why not: the adapters run different models, the
  decay shape is a model-family property, and the thresholds moved by roughly an
  order of magnitude within twelve months (Finding 5). A single number cannot be
  both current and portable, so the question has no stable answer — it has to be
  replaced by a measurement this repository re-runs.
- **Unknowable from published evidence:** whether *this* repository's rule would
  have been followed had it been inlined. Why not: the counterfactual cannot be
  run on a session that already happened, and single-artifact attribution is
  exactly what population-level ablation evidence cannot supply.

## Citations

| # | Work | Venue / Year | Identifier | Primacy |
| --- | --- | --- | --- | --- |
| 1 | McMillan, *Instruction Adherence in Coding Agent Configuration Files: A Factorial Study of Four File-Structure Variables* | arXiv, 2026-05-11 | [2605.10039](https://arxiv.org/abs/2605.10039) | Primary |
| 2 | Harada et al., *When Instructions Multiply* | EMNLP Findings, 2025 | [2509.21051](https://arxiv.org/abs/2509.21051) | Primary |
| 3 | Jaroslawicz et al., *How Many Instructions Can LLMs Follow at Once?* (IFScale) | arXiv, 2025-07-15 | [2507.11538](https://arxiv.org/abs/2507.11538) | Primary |
| 4 | Liu et al., *Lost in the Middle: How Language Models Use Long Contexts* | TACL 12:157–173, 2024 | [ACL Anthology](https://aclanthology.org/2024.tacl-1.9/) | Primary |
| 5 | *Serial Position Effects of Large Language Models* | arXiv, 2024-06-23 | [2406.15981](https://arxiv.org/abs/2406.15981) | Primary |
| 6 | *Layer-wise Positional Bias in Short-Context Language Modeling* | arXiv, 2026-01-07 | [2601.04098](https://arxiv.org/abs/2601.04098) | Primary |
| 7 | *Agent READMEs: An Empirical Study of Context Files for Agentic Coding* | arXiv, 2025-11-17 | [2511.12884](https://arxiv.org/abs/2511.12884) | Primary |
| 8 | Wallace et al., *The Instruction Hierarchy* | OpenAI / arXiv, 2024 | [2404.13208](https://arxiv.org/abs/2404.13208) | Primary |
| 9 | *Control Illusion: The Failure of Instruction Hierarchies in LLMs* | arXiv, 2025-02-19 | [2502.15851](https://arxiv.org/abs/2502.15851) | Primary |
| 10 | *PRIME: Evaluating Prompt Resolution Under Incompatible Instructions* | arXiv, 2026 | [2606.22470](https://arxiv.org/abs/2606.22470) | Primary |
| 11 | *Prompt Complexity Dilutes Structured Reasoning* | arXiv, 2026 | [2603.13351](https://arxiv.org/abs/2603.13351) | Primary |
| 12 | *On the Paradoxical Interference between Instruction-Following and Task Solving* | arXiv, 2026 | [2601.22047](https://arxiv.org/abs/2601.22047) | Primary |
| 13 | *Multi-IF: Benchmarking LLMs on Multi-Turn and Multilingual Instructions Following* | arXiv, 2024 | [2410.15553](https://arxiv.org/abs/2410.15553) | Primary |
| 14 | *MT-Eval: A Multi-Turn Capabilities Evaluation Benchmark* | arXiv, 2024 | [2401.16745](https://arxiv.org/abs/2401.16745) | Primary |
| 15 | *Order Matters: Investigate the Position Bias in Multi-constraint Instruction Following* | arXiv, 2025-02 | [2502.17204](https://arxiv.org/abs/2502.17204) | Primary (abstract only) |
| 16 | Zhou et al., *Instruction-Following Evaluation for Large Language Models* (IFEval) | arXiv, 2023-11 | [2311.07911](https://arxiv.org/abs/2311.07911) | Primary |
| 17 | Anthropic, Claude Code memory documentation | vendor docs, 2026 | [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory) | Primary |
| 18 | OpenAI Codex, AGENTS.md configuration docs | vendor docs | [learn.chatgpt.com](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | Primary |
| 19 | openai/codex issue #7138 — silent AGENTS.md truncation | GitHub issue | [codex#7138](https://github.com/openai/codex/issues/7138) | Primary |
| 20 | GitHub Copilot custom instructions | vendor docs | [docs.github.com](https://docs.github.com/en/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot) | Primary |
| 21 | Gemini CLI, GEMINI.md context docs | vendor docs | [google-gemini.github.io](https://google-gemini.github.io/gemini-cli/docs/cli/gemini-md.html) | Primary |
| 22 | agents.md open standard | Agentic AI Foundation / Linux Foundation | [agents.md](https://agents.md/) | Primary |
| 23 | OpenAI, GPT-4.1 prompting guide | vendor cookbook | [developers.openai.com](https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide) | Secondary |
| 24 | Arize AI, *Models got an order of magnitude better at following instructions in one year* | vendor blog, 2026 | [arize.com](https://arize.com/blog/llm-instruction-following-benchmark-2026/) | Secondary |
| 25 | *.cursorrules vs copilot-instructions.md — 30-Day Benchmark* | self-published, 2026 | [rpdi.us](https://rpdi.us/blog/cursorrules-vs-copilot-instructions-md-benchmark-2026/) | Secondary (unverified publisher) |
| 26 | *The AGENTS.md Field Guide, 2026 edition* | blog, 2026 | [iuriio.com](https://www.iuriio.com/blog/posts/2026/05/agents-md-field-guide-2026) | Tertiary |
| 27 | *Your CLAUDE.md Is a Wish List, Not a Contract* | blog, 2025 | [techtrenches.dev](https://techtrenches.dev/p/your-claudemd-is-a-wish-list-not) | Secondary |
| 28 | *Your AGENTS.md is a Liability* | blog, 2025 | [paddo.dev](https://paddo.dev/blog/your-agents-md-is-a-liability/) | Secondary |
