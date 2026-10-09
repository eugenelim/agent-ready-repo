---
name: navigate-intents
description: Use this skill when the user asks to look up, trace, explore, or summarise product intents (outcomes, opportunities, capabilities, features), briefs, or specs in the repository. Triggers on phrases like "show me intent:my-slug", "which intents are accepted", "trace the parent of this intent", "what brief links to this spec", "find outstanding intents", "intent graph", "show me the intent hierarchy", "how many capability intents are there". Do NOT use for creating or editing intents (use `work-intake`). Do NOT use for ADR or RFC queries (use `navigate-decisions`).
metadata:
  boundaries: [filesystem_read]
---

# Skill: navigate-intents

Read-only query skill for intent graph navigation.  Derives and traverses
the directed acyclic graph formed by live intents, briefs, and specs using
their ``Parent intent:``, ``Brief:``, and ``Discovery:`` pointer fields.

## Safety controls

- **Read-only.** This skill never writes to the repository.  It calls
  ``intent_graph.derive()`` which uses the confinement helper to read
  corpus files.
- **Confinement.** All file access goes through the co-located
  ``_file_safety.py`` helper; operations that would escape the repository
  root raise ``UnsafeContentError`` before any data is read.
- **Standard library only.** The graph derivation module imports no
  third-party packages.

## When to use

Use this skill whenever the user asks to explore the intent hierarchy: find
an intent by slug, trace its ancestors or descendants, check which briefs
reference an intent, or identify specs whose ``Discovery:`` field names a
particular intent.

## When not to use

- To create or revise an intent, brief, or spec — use `work-intake`.
- To look up ADRs or RFCs — use `navigate-decisions`.
- To run delivery-relation resolution or traceability linting — use
  `work-loop` or `close-work`.
