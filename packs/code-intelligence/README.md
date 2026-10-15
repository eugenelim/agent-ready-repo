# Code Intelligence

Your agent can answer what is true about your code, such as what calls this and what breaks if you change it, by querying an index instead of guessing.

## Install

Install it from inside the repository you want to query:

```bash
cd path/to/your-repo
agentbundle install --pack code-intelligence
```

The pack drives [Wicked Estate](https://github.com/mikeparcewski/wicked-estate), which you install and run once to build the index:

```bash
cargo install wicked-estate --version 0.29.2 --locked
echo '.wicked-estate/' >> .gitignore
wicked-estate index .
```

It also installs at user scope:

```bash
claude plugin install code-intelligence@agent-ready-repo
```

## What your agent can do

- Find a symbol and explain a class or service from the code graph.
- Work out the impact of a change: who calls it, what depends on it, and which dependents are direct or indirect.
- Trace behavior and value lineage through the code.
- Spot hotspots and clusters in the architecture.
- Gather the context a task needs, and say how many call sites the index could not resolve.

## Skills

- **`code-intelligence`** — Maps each question to the right Wicked Estate command, tells you when to stop, and keeps a guessed link from being reported as a fact.
- **`code-investigator`** — A subagent that investigates how or why something happens in a fresh context. It labels each finding observed, verified, or unestablished.
- **`impact-analyst`** — A subagent that analyses the impact of changing one symbol, module, or file, and states its own limits first.

## Works with

The pack declares Claude Code as its agent. [Core](../core/README.md) is optional: when both are installed, Core's exploration skill can use this pack for code-graph evidence. See [Understand the code](../../guides/code-intelligence/README.md).

## Questions

**How do I check my setup?** Run `python '<skill-dir>/scripts/estate_preflight.py' --check`. `<skill-dir>` is the installed `code-intelligence` skill folder, such as `.claude/skills/code-intelligence` at repo scope. Exit 0 is ready, 2 means the binary is missing, 3 means no index, and 4 means the binary is older than the 0.29 floor.

**What if there is no index?** The agent falls back to ordinary repository search and labels it as search. A list of callers from `grep` is not a blast radius.

**Does it change my code?** No. It reads. Commands that change the graph, such as `index` and `annotate`, always ask first.

**Why does an empty answer from the MCP server not mean my code is empty?** With `--readonly`, a store path that does not exist is served as an empty in-memory store. Check `--db`, `WICKED_ESTATE_DB`, or `WICKED_MEMORY_DB` first. By default the pack uses the CLI, not MCP.

**Must another provider match Wicked Estate?** No. [The composition example](.apm/skills/code-intelligence/references/composition-example.md) is illustrative, not a contract. Other providers may expose fewer, different, or new capabilities and need not emulate Wicked Estate. The current investigation patterns may change.

## Details

Scope: repo (default), user · Version: 0.1.9 · Source: [packs/code-intelligence](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/code-intelligence)
