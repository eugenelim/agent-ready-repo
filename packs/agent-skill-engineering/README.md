# Agent Skill Engineering

Your agent can frame, write, review, and tune portable agent skills (`SKILL.md` files) without free access to your repository.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install it once for your user account:

```bash
agentbundle install --pack agent-skill-engineering
```

In Claude Code you can install it as a plugin instead:

```bash
claude plugin install agent-skill-engineering@agent-ready-repo
```

## What your agent can do

- Plan a new skill before writing any file: when it should trigger, what it produces, what it may touch, and how to test it.
- Create a skill or change an existing one, after you authorize the write.
- Design a knowledge corpus that your other skills can consult, with a source for every claim.
- Review a skill for trigger precision, portability, security, and fixed mechanics, and report findings by check id.
- Tune a skill against a failure you measured, with before and after results.

## Skills

- **`author-or-update-agent-skill`** — Frames, creates, or updates a skill, or plans a read-only knowledge provider. Writes only after you authorize it.
- **`review-or-optimize-agent-skill`** — Reviews a skill read-only, and optimizes it only when you bring a measured failure and approve the write.
- **`ase-okf-reference`** — An internal knowledge router the two workflows load from. You never invoke it yourself.

## Works with

Works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, Kiro IDE, and Kiro CLI. Pair it with [Catalogue Curation](../catalogue-curation/README.md) if you maintain a catalogue of skills. To write one skill by hand, see [Author a skill](../../guides/_shared/how-to/author-a-skill.md).

## Questions

**Will it change my files without asking?** No. Framing and review are read-only. Creating, updating, and optimizing each wait for your explicit approval.

**What does it know about skills?** Sixteen governed topics, among them trigger quality, trust boundaries, Python and pytest, TypeScript and Node test runners, and the portable plugin core. Each topic states the evidence behind its claims.

**Does it read my credentials?** No. It never inspects them. Any later signed-in step must use a separate tool with least access.

**Can it write skills for any agent?** It aims for portable skills. Its runtime profile covers Claude Code only; other agents are not profiled.

## Details

Scope: user (default), repo · Version: 0.4.3 · Source: [packs/agent-skill-engineering](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/agent-skill-engineering)
