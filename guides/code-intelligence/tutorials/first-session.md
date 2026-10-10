---
title: Your first code-intelligence session
summary: Run the pack on your existing legacy app, trace one real behavior, and identify what a planned change could affect using copy-and-paste prompts.
pack: code-intelligence
kind: tutorial
---

# Your first code-intelligence session

Use your existing legacy app to answer a practical question: what could break
when you change a function? You will finish with a source-backed explanation
of one behavior, a list of affected code, and checks to consider before editing.

Here is the request you will work toward:

```text
Use the code-intelligence skill to find what depends on the function I plan
to change. Check the important callers in source and tell me what you could
not establish. Do not change application code.
```

This walkthrough uses Claude Code. Setup installs tools and writes a local
index. The investigation steps read your app without editing it. Use a repository
and agent environment you are authorized to use; keep app source and findings
inside that environment.

## 1. Choose one change in your app

Open a local checkout of your legacy app. Pick a function involved in a change
you already need to make.

For example: **add a field to an existing request and find where the app reads,
validates, and saves it.** Start with the request handler. You will trace today's
behavior before assessing the proposed change.

Write down these three details for your own use:

```text
Change: Add an optional field to an existing request.
Entry point: <actual handler or function name>
File: <path to that function>
```

Replace the change with your real task if needed. Use that same task throughout
the walkthrough. In each prompt below, replace angle-bracket placeholders with
your app's names.

**Check:** you can point to the function and explain the intended change in one
sentence. You do not need a demo repository or a rewritten app.

## 2. Install the pack in that checkout

Run this command from the root of your app repository:

```bash
agentbundle install --pack code-intelligence --scope repo --adapter claude-code
```

The pack stands alone. To install it for every repository you work in, add
`--scope user` instead of `--scope repo`.

The `core` pack is optional. Its exploration skill can use this pack as a source
of code-graph evidence. To add it:

```bash
agentbundle install --pack core --scope repo --adapter claude-code
```

These commands add agent guidance to the checkout. If a pack is already
installed for this adapter, skip its command. Use
`agentbundle list-installed --no-check` to see the installed packs. To update
an existing installation, follow [Upgrade packs](../../_shared/how-to/upgrade-packs.md).

If `agentbundle` is missing, follow the
[CLI installation instructions](../../_shared/reference/agentbundle.md#install-agentbundle)
first. Keep the app's existing instructions when the installer reports a conflict.

**Check:** the installed-pack listing includes `code-intelligence` for
`claude-code`.

## 3. Install the code indexer

The pack uses Wicked Estate to build a searchable map of your code. Check
whether its command is available:

```bash
wicked-estate --version
```

If it is absent or older than 0.21, run:

```bash
cargo install wicked-estate --version 0.21.0 --locked
```

This compiles from source and can take several minutes. If `cargo` is missing
or your machine blocks installation, use your usual IT/support route to prepare the
tool. You do not need an MCP server for this walkthrough.

**Check:** `wicked-estate --version` reports 0.21 or newer.

## 4. Build the app's index

Add this line to the app's `.gitignore` if it is not already present:

```text
.wicked-estate/
```

Then, from the app repository root, run:

```bash
wicked-estate index .
wicked-estate stats
```

Indexing writes `.wicked-estate/graph.db`; it does not change application code.
The time needed depends on the app. `stats` should report nodes and edges.
If it reports `STALENESS:`, rebuild the index before continuing. If indexing
fails or produces an empty graph, stop before treating answers as graph-backed.
Keep the error locally. For a self-serve trial, record the blocked step and a
generic reason in your response worksheet; optional IT/support help is fine.

**Check:** `stats` shows a populated graph without a staleness warning.

## 5. Open the agent and check readiness

Start a fresh Claude Code session in the app checkout. Paste:

```text
Use the installed code-intelligence skill. Locate its bundled
scripts/estate_preflight.py and run it with --check --root pointing to this
repository. Then run wicked-estate stats here and check for staleness.
Tell me whether the pack and graph are ready. Do not install tools, rebuild
the index, or edit application code in this step.
```

**Check:** the preflight reports `status: ready`, and the agent confirms a
populated graph without a staleness warning. If it cannot find the skill,
check the pack installation and reopen the session. A text-search fallback
can still help, but it does not show that this graph trial is working.

If you started from a self-serve trial worksheet, return to it now for the
investigation prompts and fill-in response fields. Otherwise, continue below.

## 6. Trace today's behavior

Paste this prompt, using the entry point from step 1:

```text
Use the code-intelligence skill to investigate <entry point> in <file>.
My planned change is: <one-sentence change>.

Trace what happens today from this entry point through validation and storage,
where those exist. Read the source for the important connections.
Separate what the graph shows, what you verified in source, and what remains
unclear. Give file and line references. Do not edit code or the graph.
```

**Check:** you get a short explanation of the actual code path with source
references. Open one cited file and check the claim yourself. If the agent
chose the wrong function, supply the correct file and ask it to resolve that
function before continuing.

## 7. Find what the change could affect

Paste:

```text
Use the code-intelligence skill to analyze the impact of changing <entry point>
in <file> to <one-sentence change>.

Find its callers and other dependents. Read the important dependent code and
explain whether it uses the behavior being changed. Distinguish direct callers
from wider dependencies where the evidence supports that distinction.
Put unresolved references, truncated results, traversal limits, and staleness
at the top. Give file and line references. Do not edit code or the graph.
```

**Check:** the report identifies affected code and explains each claimed impact.
It also states what the index could not see. If connections are unresolved or
the search hit a limit, treat the list as the known affected code, not every
possible dependency.

For hosts that expose the pack's subagents, you can ask for the same work by
name: `code-investigator` traces behavior; `impact-analyst` examines change
impact. The prompts above use the main skill and do not require subagents.

## 8. Turn the findings into your next step

Paste:

```text
From the findings above, list the existing tests and code paths I should inspect
before making this change. Tie each item to a verified source reference.
Separate confirmed checks from gaps that need manual investigation.
Do not implement the change or claim the app is safe to change.
```

**Check:** you have a short inspection checklist tied to your real task. You
decide whether the evidence is enough to proceed. Rebuild the index after code
changes before relying on it for a new analysis.

For a self-serve trial, submit only your worksheet's coded summaries through
the feedback channel you were given.
Keep source, screenshots, raw tool output, repository identity, and customer
data local. No facilitator is needed to complete the walkthrough.

For another task, see [Investigate a codebase](../how-to/investigate-a-codebase.md).
