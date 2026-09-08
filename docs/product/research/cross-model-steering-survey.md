# Steering agent-loop behavior across models and adapters

> Discipline: applied (practitioner and peer-reviewed survey)

Commissioned 2026-09-02 for the `cross-adapter-behavior-enforcement` brief. Independent desk research; findings are cited to their sources and labelled by evidence class. Retained so the briefs can cite it rather than restate it.

---

# Prior art: calibrating behavioral steering across models and host adapters

> Discipline: applied (practitioner-pattern survey)

## Bottom line

Natural-language instructions are a probabilistic steering mechanism, not a portable enforcement layer. The evidence consistently shows variation by model family, model size, prompt form, instruction position, context length, turn count, language, and instruction composition.

The correct qualification unit is:

`pack version × host adapter version × model snapshot × inference/tool configuration`

A result for one member of that tuple does not establish transfer to another. Transfer is measurable through paired evaluations, but it must be measured.

External mechanisms can be model-invariant for narrowly encoded properties:

- Grammar-constrained decoding can guarantee membership in a formal language.
- Deterministic validators can reject nonconforming artifacts.
- Tool allowlists, permissions, sandboxes, hooks, and state machines can prevent disallowed transitions or actions.
- None of these guarantees that the model chose the right content, tool, arguments, or plan unless those properties are also mechanically checked.

Therefore:

- Use prose for judgment, priorities, heuristics, and soft preferences.
- Convert safety boundaries, required lifecycle steps, artifact invariants, and machine-checkable outcomes into controls outside the model.
- Publish prose compatibility only after testing every claimed model–adapter pair.

Confidence: **high**, based on converging benchmark, constrained-decoding, and first-party adapter evidence.

---

## Mechanism 1 — Executable instruction-following evaluations

### What it is

Turn each prose requirement into one or more observable assertions. Score both:

- **Clause accuracy:** fraction of individual requirements satisfied.
- **Whole-response accuracy:** fraction of responses satisfying every applicable requirement.
- **Trajectory accuracy:** whether the agent performed the required actions and reached the right final state.

### Evidence it works

IFEval introduced roughly 500 prompts built from 25 kinds of objectively verifiable constraints. Its strength is reproducible, programmatic grading; its limitation is that it mostly measures visible, single-turn output constraints, not an agent loop. [“Instruction-Following Evaluation for Large Language Models”](https://arxiv.org/abs/2311.07911) — preprint.

FollowBench increased instructions from one to five constraints across content, scenario, style, format, and examples. It evaluated 13 open and closed models and used rule-based checks where possible, with an LLM judge for semantic constraints. [“FollowBench: A Multi-level Fine-grained Constraints Following Benchmark for Large Language Models”](https://aclanthology.org/2024.acl-long.257/) — peer-reviewed, ACL 2024.

ComplexBench evaluated 15 models on composed `AND`, chain, and conditional-selection instructions. Scores varied substantially: GPT-4-1106 reached 0.800 overall, GPT-3.5-Turbo-1106 0.682, Llama-3-70B-Instruct 0.757, and Llama-3-8B-Instruct 0.638. Performance fell as composition and nesting became harder. Even GPT-4 failed about 20% of the benchmark’s requirements. [“Benchmarking Complex Instruction-Following with Multiple Constraints Composition”](https://arxiv.org/abs/2407.03978) — peer-reviewed, NeurIPS 2024 Datasets and Benchmarks.

Multi-IF expanded IFEval into 4,501 three-turn conversations in eight languages. Every tested model degraded over turns; for example, o1-preview fell from 0.877 on turn one to 0.707 on turn three. Error profiles also differed by language and model family. [“Multi-IF: Benchmarking LLMs on Multi-Turn and Multilingual Instructions Following”](https://arxiv.org/abs/2410.15553) — preprint.

### Model dependence and weaker-model degradation

Instruction following is not a scalar capability that transfers uniformly. Models have distinct profiles for lexical, formatting, conditional, multi-turn, and multilingual requirements. Larger models generally do better in ComplexBench, but family and training effects prevent model size from being a dependable proxy.

A weaker or differently trained model tends to:

- satisfy common clauses but miss rare or negatively worded ones;
- satisfy each clause occasionally while rarely satisfying all clauses together;
- lose earlier requirements over multiple turns;
- mishandle conditionals and irrelevant branches;
- produce fluent artifacts that hide constraint failures.

Confidence: **high** for the existence of model variance; **moderate** for any general prediction based only on model size.

### How to verify transfer

Run the same clause-linked cases through every model–adapter pair. Preserve identical task data but record the adapter’s actual rendered message sequence, tool schemas, context ordering, and inference settings. Compare paired clause outcomes, not only aggregate benchmark scores.

IFEval alone is insufficient. A portable pack needs a pack-specific derivative containing its actual requirements and representative agent trajectories.

---

## Mechanism 2 — Prompt form, order, position, salience, and density

### What it is

The model’s response changes when semantically similar instructions differ in delimiters, headings, enumeration, order, message role, or location within a long context.

### Evidence it works—and fails to transfer

FormatSpread found changes of up to 76 accuracy points from plausible formatting variations on LLaMA-2-13B. Sensitivity remained after increasing model size, adding demonstrations, or instruction tuning. A format that helped one model transferred weakly: the probability that a pairwise format ranking persisted to another model was below 0.62, only slightly above chance. [“Quantifying Language Models’ Sensitivity to Spurious Features in Prompt Design”](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6c0e99d736da621403018ca7b32b1a4d-Abstract-Conference.html) — peer-reviewed, ICLR 2024.

Few-shot example ordering also changes performance, and a good ordering for one model does not reliably transfer to another. [“Fantastically Ordered Prompts and Where to Find Them”](https://aclanthology.org/2022.acl-long.556/) — peer-reviewed, ACL 2022.

DOVE evaluated several model families across more than 250 million outputs and prompt perturbations involving delimiters, enumerators, wording, and other dimensions. It found both model-specific sensitivity and instances that remained difficult across perturbations. [“DOVE: A Large-Scale Multi-Dimensional Predictions Dataset Towards Meaningful LLM Evaluation”](https://aclanthology.org/2025.findings-acl.611/) — peer-reviewed, Findings of ACL 2025.

“Lost in the Middle” found a U-shaped position effect: relevant information was often used best near the beginning or end and substantially worse in the middle, including by explicitly long-context models. The study tested retrieval and question answering, not instruction clauses directly, so applying it to project instructions is a supported risk inference rather than direct proof. [“Lost in the Middle: How Language Models Use Long Contexts”](https://aclanthology.org/2024.tacl-1.9/) — peer-reviewed, TACL 2024.

### Instruction density

ManyIFEval, with up to ten text instructions, and StyleMBPP, with up to six code requirements, found consistent degradation across ten LLMs as instructions accumulated. Its regression models estimated unseen instruction combinations with about 10% error using 500 and 300 examples respectively. [“When Instructions Multiply: Measuring and Estimating LLM Capabilities of Multiple Instructions Following”](https://aclanthology.org/2025.findings-emnlp.896/) — peer-reviewed, Findings of EMNLP 2025.

IFScale tested 20 models with as many as 500 keyword-inclusion requirements. Even its best model reached only 68% individual-instruction accuracy at maximum density, with model-dependent degradation patterns and bias toward earlier instructions. Keyword inclusion is artificial, so 68% is not a general ceiling. [“How Many Instructions Can LLMs Follow at Once?”](https://arxiv.org/abs/2507.11538) — preprint.

A recent five-model experiment reported zero perfect responses by 80 simultaneous rules, with no universal winner among Markdown, prose, tables, and plain text. System-versus-user placement helped some models and hurt others. It is a single-author, not-yet-reviewed preprint and should be treated as suggestive. [“Prompt Design at Scale: How Format, Instruction Count, and Context Length Shape Instruction Adherence and Hallucination in Large Language Models”](https://arxiv.org/abs/2607.19257) — preprint.

There is no defensible universal limit such as “five rules” or “200 lines.” The ceiling depends on rule difficulty, independence, output length, model, and scoring method. Whole-response success also falls combinatorially: even independent clauses with 95% compliance yield only \(0.95^{20}\approx36\%\) perfect responses.

Confidence: **high** that density reduces perfect adherence; **low** for any universal numeric ceiling.

### How it degrades

Different models:

- favor different delimiters or enumeration styles;
- forget different positions;
- trade content correctness against format compliance differently;
- fail abruptly rather than gradually when context becomes crowded;
- exhibit different responses to repeating or moving instructions.

### How to verify it

For each model, perturb at least:

- Markdown versus plain text;
- bullets versus prose;
- clause order;
- important clause at beginning, middle, and end;
- system/developer versus ordinary contextual placement where supported;
- short context versus realistic maximum-history context;
- single-turn versus multi-turn;
- isolated clause versus the full pack.

Report the performance range across variants, not only the best prompt.

---

## Mechanism 3 — Instruction roles and hierarchy

### What it is

Hosts label some content as system, developer, user, conversation history, tool output, or untrusted data. Models are expected to prefer higher-authority instructions when these conflict.

### Evidence

OpenAI demonstrated that targeted hierarchy training improved GPT-3.5’s resistance to lower-priority conflicting instructions, including attacks not seen in training. This shows that hierarchy adherence is learned model behavior, not a property automatically created by a `system` label. [“The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions”](https://arxiv.org/abs/2404.13208) — vendor-authored preprint.

SysBench evaluates system-message constraint violations, task misjudgment, and multi-turn instability. Its existence and findings support treating system-message adherence as a separately measured capability. [“SysBench: Can LLMs Follow System Message?”](https://proceedings.iclr.cc/paper_files/paper/2025/hash/b917f916e7eed84ffe8f5e63492b2be8-Abstract-Conference.html) — peer-reviewed, ICLR 2025.

IHEval contains 3,538 examples across nine tasks. All tested models suffered a sharp decline when instructions at different priorities conflicted; the best open model reported in the paper resolved only 48% correctly. [“IHEval: Evaluating Language Models on Following the Instruction Hierarchy”](https://arxiv.org/abs/2502.08745) — preprint.

Control Illusion tested six models and found that system/user separation did not reliably determine which formatting constraint won. Models sometimes followed their learned preference for a constraint type over the nominal message priority. [“Control Illusion: The Failure of Instruction Hierarchies in Large Language Models”](https://ojs.aaai.org/index.php/AAAI/article/view/40339) — peer-reviewed, AAAI 2026.

### Model and adapter dependence

Role labels matter only to the extent that:

1. the adapter preserves them;
2. the chat template represents them distinctly;
3. the model was trained to interpret that representation;
4. competing host instructions do not change the result.

This is especially important for project files. Claude Code states that `CLAUDE.md` is delivered as a **user message after the system prompt**, not as part of the system prompt. It explicitly says the content is context, not enforced configuration. [Claude Code: “How Claude remembers your project”](https://code.claude.com/docs/en/memory) — vendor documentation.

Thus, “the file loaded” and “the rule has high authority” are separate claims.

### How to verify it

Build an instruction-conflict matrix for each model–adapter pair:

- project file versus direct user request;
- root versus nested project file;
- ordinary instructions versus retrieved file content;
- system/developer versus user;
- user versus tool output;
- earlier versus later instruction at the same level;
- format conflict versus substantive conflict.

Record whether the model follows the expected winner, follows the loser, satisfies neither, or silently combines incompatible rules.

Confidence: **high** that hierarchy behavior is model-dependent and must be tested.

---

## Mechanism 4 — Grammar-constrained and structured decoding

### What it is

At each token, a decoder masks tokens that cannot lead to a valid string under a grammar, automaton, parser, or JSON schema.

### Evidence

PICARD rejects inadmissible tokens through incremental parsing and substantially improved valid SQL generation from T5 models. [“PICARD: Parsing Incrementally for Constrained Auto-Regressive Decoding from Language Models”](https://aclanthology.org/2021.emnlp-main.779/) — peer-reviewed, EMNLP 2021.

Grammar-constrained decoding can formally guarantee output membership in a supported context-free grammar, provided tokenizer alignment and the decoder implementation are sound. [“Flexible and Efficient Grammar-Constrained Decoding”](https://proceedings.mlr.press/v267/park25l.html) — peer-reviewed, ICML 2025.

OpenAI reports that Structured Outputs combines schema-trained models with constrained decoding and achieved 100% schema conformance on its internal complex-JSON-schema evaluation. This is a vendor result, not independent evidence of semantic correctness. [OpenAI, “Introducing Structured Outputs in the API”](https://openai.com/index/introducing-structured-outputs-in-the-api/) — vendor documentation.

### Model invariance

**Invariant by construction:** syntactic membership in the exact grammar or supported schema subset.

**Not invariant:**

- factual correctness;
- choosing the right enum member;
- including meaningful rather than empty data;
- selecting the correct tool;
- correct tool arguments;
- completeness beyond what the schema encodes;
- termination and latency behavior.

A weaker model commonly degrades into schema-valid but semantically wrong output. The grammar removes illegal exits from the search space; it does not add missing reasoning capability.

### Verification

Test two layers separately:

1. Feed generated output to an independent parser/schema validator.
2. Execute or semantically grade its contents against the task outcome.

Also test unsupported schema features, truncation, refusal paths, parallel calls, nullable or empty structures, and impossible constraints. Fail closed when the validator cannot establish conformity.

Confidence: **high** for syntax guarantees; **high** that semantic correctness remains model-dependent.

---

## Mechanism 5 — Tool schemas and forced function calls

### What it is

The adapter limits available tools, describes typed inputs, optionally forces a call, and validates arguments before execution.

OpenAI’s API exposes `tool_choice: required` and allowed-tool subsets. Google documents `any` as forcing a function call and `validated` as enforcing schema adherence. [OpenAI Responses API reference](https://platform.openai.com/docs/api-reference/responses-streaming/response/refusal?lang=python), [Gemini function-calling documentation](https://ai.google.dev/gemini-api/docs/function-calling) — vendor documentation.

### Model invariance

- An external allowlist can make calling an unavailable tool impossible.
- A forced-call mode can prevent free-text completion when implemented by the provider.
- Validation and rejection can guarantee that executed arguments meet the encoded schema.

The model still chooses poorly among allowed tools and can supply valid but wrong arguments. The Berkeley Function Calling Leaderboard exists because correct tool selection, relevance detection, argument construction, parallel use, and multi-turn use vary materially across models. [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html) — academic benchmark and technical report.

### Degradation

A weaker model may:

- call a permitted but irrelevant function;
- omit necessary calls;
- repeat calls;
- hallucinate semantically invalid values that pass type checks;
- fail to recover after a validator rejection;
- exhaust retries without reaching a legal useful action.

### Verification

Run executable function-call cases for:

- one tool, competing tools, and no applicable tool;
- missing or conflicting parameters;
- parallel versus serial requirements;
- validator rejection and retry;
- multi-turn state changes;
- side-effecting calls in dry-run or simulated environments.

Confidence: **high** that allowlists and validation constrain the action surface; **high** that useful tool selection remains model-dependent.

---

## Mechanism 6 — Deterministic scaffolding, state machines, and hooks

### What it is

The surrounding program owns lifecycle state and decides which transitions and actions are legal. The model proposes; the control plane validates, permits, modifies, defers, or rejects.

Examples include:

- explicit workflow states and legal transition tables;
- artifact validators and required-gate predicates;
- maximum retries and time budgets;
- idempotency keys;
- filesystem and network permissions;
- transaction boundaries and human approval;
- pre-tool and pre-stop interceptors.

Claude Code documents that `PreToolUse` hooks can deny a call before execution and that a `Stop` hook can prevent the loop from stopping. GitHub Copilot exposes `preToolUse`; Cursor exposes `beforeShellExecution`, `beforeMCPExecution`, and related hooks. [Claude Code hooks reference](https://code.claude.com/docs/en/hooks), [GitHub Copilot hooks](https://docs.github.com/en/copilot/concepts/agents/hooks), [Cursor hooks](https://prod.cursor.com/docs/hooks) — vendor documentation.

### Model invariance

These are the strongest model-invariant mechanisms, provided that:

- they run outside the model;
- every relevant action passes through them;
- they validate trusted state rather than model assertions;
- failure is closed rather than open;
- the model cannot edit or bypass the control plane.

A shell hook with deterministic code can be invariant. A “prompt hook” that asks another LLM whether an action looks safe is still probabilistic.

### Degradation

On a weaker model, the safe failure modes are more blocks, retries, escalations, or inability to complete. The system should not relax the invariant merely because the model repeatedly proposes illegal actions.

### Verification

Unit-test the transition and policy code without any model. Then run adapter integration tests proving that every write, command, network call, completion event, and delegation event reaches the intended interception point. Include malformed hook output, hook timeout, adapter crash, restart, and concurrent action cases.

Confidence: **high**, limited to the properties and action paths actually controlled.

---

## Mechanism 7 — Cross-adapter project instructions

| Host | Native project mechanism | Scope and precedence | Host-specific behavior |
|---|---|---|---|
| Codex | `AGENTS.md`, `AGENTS.override.md` | Builds a chain from project root to current directory; one file per directory; 32 KiB combined default | Discovers once per run; supports configurable fallback filenames. [Codex documentation](https://developers.openai.com/codex/guides/agents-md) |
| Claude Code | `CLAUDE.md`, `.claude/rules/*.md` | Ancestors load at launch; nested files can load when files below them are read | Does **not** natively treat `AGENTS.md` as the project file; use `@AGENTS.md` from `CLAUDE.md` or a symlink. `@path` imports recurse to four hops. Project instructions are delivered as user-context, not hard configuration. [Claude Code documentation](https://code.claude.com/docs/en/memory) |
| Cursor | `AGENTS.md`, `.cursor/rules/*.mdc` | Current documentation supports nested rules and more-specific instructions; rule metadata can control automatic, intelligent, or manual inclusion | `.mdc` supports glob scope and `@filename` references; Cursor rules and hooks are not portable Markdown semantics. [Cursor Rules](https://prod.cursor.com/docs/rules) |
| GitHub Copilot | `.github/copilot-instructions.md`, path-specific `.instructions.md`, and some agent files | Support differs across Copilot Chat, cloud agent, code review, IDE, and CLI | Some surfaces accept `AGENTS.md`; some accept `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`; others accept none of them. [GitHub support matrix](https://docs.github.com/en/copilot/reference/custom-instructions-support) |
| Gemini CLI | `GEMINI.md` by default | Loads global, ancestor/project, and subdirectory context files and concatenates them | Supports `@file.md`; `context.fileName` can be configured to include `AGENTS.md`. [Gemini CLI documentation](https://google-gemini.github.io/gemini-cli/docs/cli/gemini-md.html) |

The [AGENTS.md convention](https://agents.md/) standardizes a discoverable Markdown filename and describes nearest-file precedence. It does not standardize message role, byte limits, lazy loading, conflict semantics, imports, hooks, tool permissions, or model behavior.

Therefore, a portable pack needs:

- a canonical semantic source;
- thin host projections or documented adapter configuration;
- adapter conformance tests that inspect what was actually loaded;
- model behavioral tests after adapter rendering.

Confidence: **high** for the documented loader differences; **low** for undocumented internal prompt placement in hosts that do not expose it.

---

## Minimum per-model calibration before claiming support

This is a recommended qualification floor, not a published universal standard.

### 1. Fix the test identity

Record exact pack revision, model identifier or snapshot, host and adapter versions, inference settings, tool definitions, permissions, context-window policy, and retry rules.

### 2. Prove adapter delivery mechanically

Use host diagnostics such as Codex’s reported instruction sources, Claude’s `/context`, or Gemini’s `/memory show`. Prefer source paths and content hashes from the adapter over asking the model whether it “read the instructions.”

Test imports, nested scope, truncation limits, fallback names, and precedence.

### 3. Give every load-bearing clause direct coverage

For each clause, include:

- a normal positive case;
- a case where following the clause is inconvenient;
- a direct conflict or tempting counter-instruction;
- a long-context or middle-position case;
- a multi-turn case if the clause must persist;
- a non-applicable case to detect over-application.

Use deterministic grading whenever the requirement can be expressed mechanically.

### 4. Run repeated trials

Anthropic recommends multiple trials because agent outputs vary and emphasizes grading final environment state, not merely the transcript. [“Demystifying evals for AI agents”](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) — vendor engineering guidance.

As a minimal statistical interpretation, 30 independent trials with zero observed failures only support an approximate 95% upper failure bound of 10% under the tested distribution—the rule of three. That is a weak compatibility claim, not high assurance. For a 5% bound, use about 60 zero-failure trials; for 1%, about 300.

### 5. Measure robustness, not one favored rendering

Run at least three semantically equivalent prompt renderings and beginning/middle/end placement variants. Report median, worst variant, and confidence intervals. A prompt that succeeds only in its tuned wording is not portable.

### 6. Use separate thresholds

- **Hard safety or authority constraint:** mechanical enforcement required; prose score is diagnostic.
- **Required workflow behavior:** high whole-trajectory threshold plus external completion checks.
- **Formatting and style:** per-model threshold may differ if downstream validation or repair exists.
- **Advisory preference:** report expected compliance rather than pass/fail support.

### 7. Keep a canary suite

On every model snapshot, host update, prompt change, or tool-schema change:

- run a small clause-balanced canary first;
- stop rollout on loader, hierarchy, tool, or hard-invariant regression;
- then run the full golden suite;
- retain traces so changed behavior can be attributed to model, adapter, or pack.

### 8. Degrade safely

If a startup capability probe shows that the adapter lacks an instruction file, hook, forced tool mode, schema feature, or permission boundary:

- disable the affected feature;
- switch to a mechanically safer workflow;
- require human approval;
- or declare that model–adapter tuple unsupported.

Do not silently replace missing enforcement with stronger wording.

---

## Which mechanisms are model-invariant?

| Mechanism | Model-invariant property | Important limit |
|---|---|---|
| External schema/parser validation | Invalid output is rejected | Does not make valid output correct |
| Sound grammar-constrained decoding | Output belongs to the encoded grammar | Only supported syntactic/formal properties |
| Tool allowlist or removal | Disallowed tool cannot be selected | Allowed tool may still be used wrongly |
| Pre-execution permission check | Rejected action cannot execute through that path | Must cover every execution path and fail closed |
| Filesystem/network sandbox | Operations outside the boundary fail | Boundary configuration may be wrong |
| Deterministic state machine | Illegal transition cannot be committed | Model can stall or choose a poor legal transition |
| Deterministic postcondition gate | Completion cannot be accepted without the predicate | Predicate may under-specify real success |
| Human approval gate | Action waits for approval | Human review quality is outside the mechanism |

Prose instructions, demonstrations, XML or Markdown structure, repetition, salience markers, system-role placement, chain-of-thought requests, LLM judges, and prompt-based hooks are **not** model-invariant.

---

## Can prose be reliable across models?

The evidence supports this narrower position:

- Prose can achieve high empirical reliability for a bounded task distribution on a qualified model–adapter pair.
- Clear, concise, non-conflicting, salient instructions usually improve the odds.
- There is no evidence that a prose instruction set can provide model-independent behavioral guarantees.
- Adding more prose eventually reduces whole-set adherence and can create conflicts that are resolved differently across models.
- A successful prompt on one model is useful prior information for another model, not proof of transfer.

The honest publication language is therefore:

> “This instruction set was evaluated on these named model–adapter versions, with these measured compliance rates and known failures.”

It should not be:

> “These instructions ensure that any supported agent behaves this way.”

Only external mechanical enforcement supports the latter kind of claim, and only for the properties it actually encodes.

## Known unknowns

- **Known-unknown:** Comparative performance of the same real coding-agent pack across Codex, Claude Code, Cursor, Copilot, and Gemini under controlled model substitution. Would be closed by a shared cross-adapter harness capturing rendered messages, tools, trajectories, and final artifacts.
- **Known-unknown:** How Codex, Cursor, Copilot, and Gemini internally assign message roles to every class of project instruction. Public documentation is incomplete outside the explicitly documented Claude behavior.
- **Known-unknown:** A general instruction-density ceiling for realistic heterogeneous skill files. Existing studies use different constraint types and metrics, so their numerical ceilings do not transfer directly.
- **Unknowable in advance:** Whether a future model or host release preserves today’s behavior. Closed models and adapters can change without exposing training or prompt-stack details; only recurring regression tests can answer it after release.

No repository files or git state were modified.