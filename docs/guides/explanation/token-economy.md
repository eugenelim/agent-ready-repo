# The token economy of the loop

The loop runs adversarial reviewers in fresh sessions, spins up
sub-agents, plans before it codes, and re-reviews until a cold reader
says `Clean`. All of that costs tokens, and the first reaction to a
token bill is usually "where's the waste?" The waste is worth finding,
but it is the smaller point. The loop is not trying to spend the fewest
tokens. It spends them where they buy something you can't measure in
tokens.

The leverage in agentic engineering moved. It used to sit in the prompt;
it now sits in the *loop* — how context is allocated, isolated, and
re-read across a long-running session. Get that allocation right and you
are an informed engineer moving fast. Get it wrong and you are either
paying for noise or starving the one step that protects quality. The two
mistakes look identical on an invoice and opposite in the codebase.

## The cost is countable; the return is not

Tokens are the most legible thing about a session, so they attract all
the attention. But the loop's payoff — a spec that didn't drift, an edge
case caught before merge, a reviewer that wasn't talked out of a
finding — never shows up in a token count. The cost is quantitative; the
return is qualitative.

That asymmetry is the trap. If you judge the loop on the metric you
*can* see, you will cut exactly the spend that earns the return you
*can't* see, and you'll have a cheaper agent that ships worse code. The
right posture is not "spend less." It is "waste nothing, and invest
deliberately."

## Where the tokens actually go

Two things surprise people who look for the first time.

**First: the prose you read is a rounding error.** Here is a
representative breakdown of resident context — the conversation re-sent
to the model on every turn. (Figures are an illustrative profile from an
instrumented measurement of real multi-session usage, rounded, shown as
shares and rates — not a benchmark or a budget.)

| Block | Share | What it is |
| --- | --- | --- |
| tool results | ~46% | file and command output read back in |
| tool calls | ~30% | edit / write / command payloads — the work itself |
| reasoning | ~12% | the model's thinking |
| **agent prose** | **~6.5%** | the messages a human reads |
| user prompts | ~6% | the human's input |

The part that *feels* verbose — the agent explaining itself — is the
smallest slice you can control. Trimming it is a rounding error. What the
agent *generates* tells the same story: roughly 62% of output is the
edits and commands that are the work, ~24% is reasoning, and only ~13% is
prose. Most of it is irreducible.

**Second: the dominant cost is not what's written — it's what's
re-read.** Every turn re-sends the whole conversation as cached input, so
a file dump pulled in early is paid for again on every subsequent turn.
In the measured sample, cached re-reads outweighed generated output by
roughly **190×**. The real lever is therefore the *size of resident
context*, not the length of any one message. That single fact explains
every waste-cutting choice below.

## What the loop refuses to waste

These are the tokens that buy nothing, and the loop is built to avoid
them:

- **It defaults to light mode.** The state machine, multi-pass review,
  and separate spec/plan files load only when a risk trigger fires. A
  small change never pays for heavyweight machinery.
- **It discloses progressively.** Skill bodies stay lean; deeper
  references load only when a step needs them. A reviewer's brief inlines
  only the security module that matches the boundary the diff crossed,
  not the whole library.
- **It budgets the always-resident files.** `AGENTS.md` is capped on
  purpose, because it is re-read every single session; detail lives in
  docs and skills that load only when relevant.
- **It drops report text after recording it.** Once a reviewer's findings
  are captured, the verbatim report leaves resident context. The decision
  survives; the bulk does not.
- **It doesn't restate what the runtime already does.** Every supported
  tool ships context-isolating sub-agents and already steers toward
  delegation. Re-teaching that in the pack would itself be resident-context
  cost for no gain.

None of these trade away quality. They remove tokens that were doing no
work.

## What it spends on purpose: a cold reviewer

Here is the most expensive deliberate choice in the loop, and the one
most worth defending: **the adversarial reviewer runs in a fresh context,
not the implementer's.**

The context that wrote the code is the worst possible judge of it. It
lived through every assumption, every "good enough," every shortcut it
told itself was fine. It has already agreed with the code — it *is* the
code's point of view. Ask it to review its own work and it grades
generously, because it cannot see the drift it drifted into. A fresh
context can. It reads the spec, the diff, and the conventions cold and
measures the code against the **contract**, not against the story of how
the code came to be.

That independence is the entire value of the review, and it isn't free.
A fresh reviewer pays a bootstrap — its system prompt, `AGENTS.md`, and
the skill, reloaded before it reads a single line of the diff, on the
order of ~166k tokens. That is not waste. It is the price of an unbiased
read. A same-context review would be cheaper precisely because it does
less: it inherits the maker's blind spots along with the maker's context.
You'd save tokens and lose the thing you were paying for.

The same isolation that makes review independent also keeps heavy work
out of the main thread:

| | Main thread | Delegated sub-agent |
| --- | --- | --- |
| avg context re-read per turn | ~237 ktok | ~55 ktok (**~4.3× leaner**) |
| share of total billed tokens | ~89% | ~11% |
| raw file/command output absorbed | ~13 MTok | **~29 MTok** (kept out of main) |

A tool result's true cost is `size × turns-it-survives-in-context`. In
the main thread a dump survives for hundreds of turns; inside a sub-agent
it survives that agent's short life and is then discarded — only the
summary returns. In the measured sample, sub-agents absorbed more than
twice the raw dump volume that ever reached the main thread, for about a
tenth of total spend. The bootstrap that buys reviewer independence is
the same bootstrap that buys this isolation.

This is also why the loop does **not** say "always delegate." The
bootstrap only pays off for large, early, multi-file exploration and for
the independence of review. For a single small or known-location read,
reading inline is cheaper than the bootstrap. Spend it where it buys
something.

## The expensive mistake is a wasted round, not a verbose turn

The costliest failure mode in an agentic loop is not a long context — it
is a **wasted round**: the agent confidently builds the wrong thing, or
iterates blindly, and the whole loop runs again. An agent fills any gap
in your intent with a plausible guess; left unchecked, it spends a full,
token-heavy round implementing that guess before anyone notices it was
wrong. A 166k-token cold review that catches drift early is cheap against
re-doing the work downstream.

The loop guards rounds directly:

- **Spec-first** — a lean inline spec in light mode, a full spec when
  risk warrants — spends a little context up front so the agent doesn't
  burn a round building the wrong thing. The spec is durable intent that
  survives the context turning over.
- **Mechanical gates** (lint, typecheck, tests) fail before review, so no
  round is spent reviewing code that doesn't run.
- **Iteration and token-budget caps** stop the loop loud instead of
  letting it spiral — and stasis detection stops a third pass on findings
  that already repeated. Runaway rounds are a stop condition, not a silent
  bill.

Anti-drift alignment is the thing being bought here. Fresh context and
the spec are how it's paid for, and not wasting rounds is how the
investment pays back.

## The dial: light mode vs. full mode

There is no single right amount to spend, so the loop makes it a dial.
Light mode is the default — lean spec, one bounded review, no state
machine. A risk trigger (unfamiliar territory, a security boundary, a
structural or irreversible change, a new dependency) escalates to full
mode, where the extra spec rigor and review passes earn their cost. You
invest more context exactly where a miss is expensive, and you don't pay
for it where it isn't. The mode *is* the token posture, made explicit.

## Where to read next

- [The core pack as a system](core-pack.md) — the parts that make up the
  loop, and how the cold reviewer fits the rest.
- [`docs/CONVENTIONS.md` § How we do non-trivial work](../../CONVENTIONS.md#how-we-do-non-trivial-work) —
  the contributor-side rationale for light vs. full mode.
- [Why the plan owns the LLD](why-the-plan-owns-the-lld.md) — another
  place the loop spends a little up front to avoid a wasted round.
