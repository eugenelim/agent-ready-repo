---
title: Skill script conventions
summary: Apply the catalogue’s common flags, usage documentation, shortcut, shared-library, setup, and operation-logging conventions to helper scripts.
pack: _shared
kind: reference
---

# Skill script conventions

Reference for helper scripts under a skill's `scripts/` directory. These conventions apply to any script — TypeScript or Python — that the skill invokes via the agent's `Bash` tool.

## Standard flags

Every script that can show UI or trigger side effects should accept this consistent flag set. Users learn the pattern once and it works everywhere.

| Flag | Meaning | When to add |
|------|---------|-------------|
| `--headed` | Show the browser or UI window (default: headless) | Any script that drives a browser |
| `--yes` | Skip all confirmation prompts (default: ask) | Any script that deletes or sends |
| `--debug` | Emit verbose internal state — raw responses, timing, selector hits | Any script where internal state helps debugging |
| `--raw` | Return only the function's return value as clean JSON, no metadata wrapper | Scripts that output structured data for the skill to parse |

**Value flags use `=` form** — `--limit=50`, not `--limit 50`. Parsers that scan for `--key` treat the next positional as an unrelated argument otherwise, which silently mis-parses multi-flag invocations.

## Usage docblock

Open every script with a usage block listing all flags and their defaults. This is the contract — the skill body, README, and any user-facing docs all reference it:

**TypeScript:**

```typescript
/**
 * Usage:
 *   npx tsx scan.ts
 *   npx tsx scan.ts --headed
 *   npx tsx scan.ts --limit=50      # page size cap; default 100
 *   npx tsx scan.ts --all-dms       # include DMs older than 30 days
 *   npx tsx scan.ts --debug         # print raw first page of results
 */
```

**Python:**

```python
# Usage:
#   python scan.py
#   python scan.py --headed
#   python scan.py --limit=50      # page size cap; default 100
#   python scan.py --debug         # print raw first page of results
```

## Shortcut IDs

When a script acts on a typed collection — conversations, files, tasks — assign each item a **type-prefix + number** shortcut ID. This lets the user say `mark-read D1 G2` rather than long names or indices.

Define the prefix table in the skill body so users can look it up:

| Prefix | Type |
|--------|------|
| `D`    | Direct message |
| `G`    | Group / meeting |
| `C`    | Channel |
| `M`    | Meeting recording |

IDs are position-stable within a session but may change between probe refreshes — document this.

## Sharing code across skills

Skills must be self-contained — cross-skill relative imports (`../../sibling/scripts/`) are not portable across adapter projections and violate the self-contained-folder rule. When two or more skills in the same pack need shared helpers (auth clients, config loaders, API wrappers), put the shared code in `.apm/shared-libs/<name>/` instead. The projection system copies it into each adapter's layout alongside the skill directories.

```
packs/<pack>/.apm/
  shared-libs/
    helpers/       # shared auth, config, API clients
  skills/
    skill-a/       # uses helpers from shared-libs/
    skill-b/       # same helpers, independently projected
```

Never copy-paste shared logic between skill `scripts/` directories — auth helper drift is the hardest class of bug to diagnose across multiple skills.

## Idempotent setup scripts

A setup script should be safe to re-run at any point in a session. Each step must check whether it is already done before running:

```
1. Check Node version — already meets floor? Skip install, proceed.
2. Install npm dep — already present? Skip, proceed.
3. Check config exists — already written? Skip wizard, proceed.
4. Open headed browser for sign-in — already authenticated? Skip, proceed.
5. Run verification probe — exits 0? Report success.
```

The check-before-act shape makes partial runs safe: a session that was interrupted midway resumes from the next uncompleted step, not from the top.

## First-value onboarding keys

The `[pack.first-value]` table in `pack.toml` contains **natural-language instructions** the agent follows during first-session onboarding — not shell commands. The agent reads and acts on them as instructions:

```toml
[pack.first-value]
verification   = "Ask the agent to convert README.md to a Word document; confirm a README.docx file is created."
recovery       = "If the conversion fails, check that the source file exists and is a supported format; try converting a simpler file first."
starter-task   = "Export this project's README as a shareable Word document"
starter-prompt = "Convert README.md in this project to a Word document and save it as README.docx."
```

`verification` and `recovery` are agent instructions, not shell commands — write them as a human would instruct an agent. For programmatic setup detection (checking if a binary is on PATH, confirming config exists), use the skill's own `## Prerequisites` section and `--check` verb pattern instead.

## Pack config and operation logging

Skills that need to store user-specific settings or record what they have done use the pack-config API — available in Python and as a CLI. See the full reference at [`guides/_shared/reference/pack-config-api.md`](pack-config-api.md).

**Read pack config** — values set by the user via `agentbundle pack-config set <pack> <key> <value>`:

```python
from agentbundle.pack_config import pack_dir, load_pack_config

config = load_pack_config(pack_dir("<pack-name>"))
base_url = config.get("base_url", "https://example.com")
```

```bash
agentbundle pack-config get <pack-name> base_url
```

**Write operation log entries** — structured records of what the skill did (for audit, undo, and user history):

```python
from agentbundle.pack_config import pack_dir, write_entry
from datetime import datetime, timezone

write_entry(pack_dir("<pack-name>"), {
    "verb":      "send-message",
    "to":        recipient,
    "subject":   subject,
    "timestamp": datetime.now(timezone.utc).isoformat(),
})
```

```bash
agentbundle oplog <pack-name>   # list recent entries
```

**Credentialed skills** — if the skill holds tokens or API keys, the credential-brokers contract governs storage (see [How to add a credentialed skill](../../credential-brokers/how-to/add-a-credentialed-skill.md)); `pack_dir()` gives the base directory the broker writes into.
