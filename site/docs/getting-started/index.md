# Get Started

agent-ready-repo ships the complete AI operating model for software teams. This guide gets you from zero to your first loop in under five minutes.

## What you're installing

When you install a pack, you get:

- **Skills** — slash commands your agent runs on request (`/work-loop`, `/new-spec`, `/bug-fix`)
- **Subagents** — specialist reviewers that read your diff cold (`adversarial-reviewer`, `security-reviewer`, `quality-engineer`)
- **Hooks** — automation that fires at session start and before a PR opens
- **Seeds** — scaffolding for your repo's governance docs

Everything lands as files in your repo (or your home directory for user-scope packs). No runtime, no service, no lock-in.

## Step 1: Install the CLI

```bash
pip install agentbundle
```

The `agentbundle` CLI manages pack installation, upgrade, and discovery. One-time setup — upgrade it like any other pip package.

## Step 2: Pick your starting point

=== "Just the build loop"

    The flagship pack. Works in any repo, any stack.

    ```bash
    agentbundle install --pack core
    ```

    You get: `work-loop`, `new-spec`, `bug-fix`, four reviewer subagents, session-start and pre-PR hooks.

=== "Full company OS"

    All three loops — discovery, build, release.

    ```bash
    agentbundle install --pack core
    agentbundle install --pack product-engineering --scope user
    agentbundle install --pack release-engineering
    ```

=== "Inception profile"

    For taking a raw idea from zero to a buildable repo.

    ```bash
    agentbundle install --profile inception
    ```

    Lands: `research` + `product-engineering` + `architect`

=== "Solution architect"

    Design, research, and API contracts.

    ```bash
    agentbundle install --profile solution-architect
    ```

    Lands: `architect` + `research` + `contracts`

## Step 3: Adapt to your repo

After install, open your agent and run:

```
/adapt-to-project
```

This reads your repo's stack and conventions, then tailors the installed skills to match. It fills in the command stubs in your `AGENTS.md` and wires up the hooks correctly.

## Step 4: Use the loop

Your first real task:

```
Implement <feature> with the work-loop.
```

The build loop will:

1. **Plan** — name the files it'll touch, write the tests, name what it won't change
2. **Execute** — red-green-refactor or goal-based, depending on the task
3. **Gate** — lint, typecheck, tests must all pass
4. **Review** — adversarial reviewer reads the diff cold in a fresh context
5. **Decide** — fix blockers, defer nits, ship

---

## What's next

- [Install routes](install.md) — CLI, Claude Plugins, APM, and local clone
- [The three loops explained](three-loops.md) — how discovery, build, and release compose
- [Choose your packs](../packs/index.md) — the full catalogue with one-liner descriptions
- [Adapter support matrix](../guides/_shared/reference/adapter-support.md) — what works in your agent
