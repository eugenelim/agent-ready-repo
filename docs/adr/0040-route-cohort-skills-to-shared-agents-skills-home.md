# ADR-0040: Route cohort skills to the shared `.agents/skills/` home

- **Status:** Accepted
- **Date:** 2026-06-26
- **Decision-makers:** eugenelim
- **Supersedes:** the **skill-home sub-decision** of [ADR-0013](0013-copilot-full-parity-user-scope-adapter.md), [ADR-0015](0015-cursor-full-parity-distribution-adapter.md), and [ADR-0016](0016-gemini-cli-full-parity-adapter.md) only — each of those ADRs' agent / hook / command projection decisions stand
- **Related:** [RFC-0052](../rfc/0052-shared-prefix-aware-multi-adapter-install.md) Decision 3 (the call this records — the one RFC-0052 decision that required an explicit Approver yes), [ADR-0039](0039-footprint-co-ownership-install-identity-and-shared-prefix-class.md) (the `shared` prefix class + co-ownership model this routing relies on), [RFC-0009](../rfc/0009-codex-native-skills.md) (codex's existing `.agents/skills/` native home, the precedent)

## Context

`.agents/skills/` is an Anthropic-maintained open standard now read by **codex, cursor, gemini, and copilot**. When the cursor, gemini, and copilot adapters were specified (ADR-0015 / ADR-0016 / ADR-0013), each chose the tool's *native* skill directory — `.cursor/skills/`, `.gemini/skills/`, `.github/skills/` + `~/.copilot/skills/` — because those tools' `.agents/skills/` support was absent or immature. ADR-0016 stated outright that "the `.agents/skills/` alias is not relied on."

That support has matured, confirmed against each tool's current documentation:

- **Cursor** loads skills from `.agents/skills/`, `.cursor/skills/`, `~/.agents/skills/`, `~/.cursor/skills/` ([Cursor skills docs](https://cursor.com/docs/skills)).
- **Gemini CLI** reads `.agents/skills/` and `~/.agents/skills/`, and within a tier the **`.agents/skills/` alias takes precedence over `.gemini/skills/`** (docs updated 2026, [Gemini CLI skills docs](https://geminicli.com/docs/cli/skills/)) — directly reversing ADR-0016's "alias is not relied on."
- **Copilot** reads `.agents/skills/` (project) and `~/.agents/skills/` (personal), alongside `.github/skills/` / `~/.copilot/skills/` ([GitHub Docs — About agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills), [VS Code — Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills)).

So one physical skill copy at `.agents/skills/` can serve the whole cohort, and ADR-0039's co-ownership model can let two same-pack installs land there once and be shared. The native-home decision in the three ADRs is now stale — but only for the *skill* primitive; their agent/hook/command projection was unaffected by skill-discovery and remains correct.

This is RFC-0052 Decision 3, the single decision that required an explicit Approver yes (the other RFC-0052 decisions adopt by silence) precisely because it supersedes three Accepted ADRs and couples the catalogue to upstream tools' skill-discovery behaviour.

## Decision

> **Every adapter in the `.agents/skills/` cohort — codex, cursor, gemini, copilot — writes the `skill` primitive to the shared `.agents/skills/` prefix. Their agent, hook, and command primitives stay on each tool's native paths exactly as ADR-0013 / ADR-0015 / ADR-0016 specify. This supersedes the skill-home sub-decision of those three ADRs and nothing else in them.**

Concretely: codex already targets `.agents/skills/` (RFC-0009); cursor, gemini, and copilot move their skill output there. The cohort and the prefix class are recorded as contract data per ADR-0039, so the routing is declarative. Cursor, gemini, and copilot gain `.agents/skills/` in their `allowed-prefixes` at **both** repo and user scope (codex already lists it at both; the other three list only their native trees today), so the routed skill path is jail-admissible at the default repo scope as well as user scope.

| Shared prefix | Reader cohort (shipped adapters) | Skill copy | Agents |
| --- | --- | --- | --- |
| `.agents/skills/` | codex, cursor, gemini, copilot (forward-ready for Claude Code) | one, co-owned across same-pack rows | private, per-adapter format |
| `.kiro/skills/` | kiro-ide, kiro-cli | one, co-owned across same-pack rows | private — `.json` (cli) vs `.md` (ide) |
| `.claude/skills/` | claude-code (island, today) | private | private |

Each prior ADR is marked with the repo's partial-amendment status idiom (the precedent is ADR-0001) — `Accepted — partially amended: the skill-home sub-decision is superseded by ADR-0040; agent/hook/command projection stands` — not a bare "Superseded by", which would wrongly imply the whole ADR is gone.

## Decision drivers

- **One copy serves the cohort** — the whole point of a shared prefix; native-home routing forces a separate copy per adapter for skills every cohort member already reads.
- **Evidence has changed** — the three ADRs chose native homes against then-current tool behaviour; that behaviour has since matured (Gemini now *prefers* the alias), so the decision they made on the old evidence no longer holds for skills.
- **Supersede surgically, not wholesale** — only skill discovery changed; the agent/hook/command decisions in those ADRs are independent and correct, so the supersession is sub-decision-scoped.
- **Stay inside the security posture** — routing copies files to a shared directory; it adds no symlink and no new override, consistent with ADR-0039.

## Consequences

**Positive:**

- A single `.agents/skills/` copy serves codex, cursor, gemini, and copilot; installing a pack for any cohort member lands skills once and every member reads them.
- Cohort membership is declarative contract data — a future cohort adapter (e.g. Claude Code, if it adopts `.agents/skills/`) joins by a one-line contract change, not an engine edit.
- The supersession is honest and narrow: the three ADRs keep their still-correct agent/hook/command decisions and carry an accurate partial-amendment marker.

**Negative:**

- Couples the catalogue to upstream tools' evolving skill-discovery behaviour. If a cohort adapter quietly drops `.agents/skills/` support, its routed skills stop being discovered — mitigated because the cohort is contract data (demoting an adapter to its native home is a one-line change) and per-tool support is re-verified at each contract bump.
- Three Accepted ADRs gain a partial-amendment marker — a real, if small, governance cost.

**Neutral / to revisit:**

- `.claude/skills/` stays a private island today. If Claude Code adopts `.agents/skills/` ([claude-code#31005](https://github.com/anthropics/claude-code/issues/31005)), it joins the cohort by a contract edit; that is a future decision, not pre-committed here.

## Confirmation

The implementing spec (`docs/specs/shared-prefix-aware-multi-adapter-install/`) carries the acceptance criteria: the contract gains the prefix-class + reader-cohort fields; cursor/gemini/copilot skill output targets `.agents/skills/`; cursor, gemini, and copilot `allowed-prefixes` include `.agents/skills/` at both repo and user scope (codex already does); and a cohort-coexistence test installs a pack for codex then cursor and asserts the second install co-owns the existing `.agents/skills/` copy rather than sweeping or double-writing it. Re-verification of each tool's `.agents/skills/` support is a checklist item at every future adapter-contract bump.

## Alternatives considered

- **Keep native skill homes (the status quo of ADR-0013/0015/0016).** Rejected against *one copy serves the cohort* and *evidence has changed*: every cohort member reads `.agents/skills/` today, so native homes force a redundant per-adapter skill copy and leave the shared prefix unused; the evidence that justified native homes has matured.
- **Route skills *and* agents to shared prefixes.** Rejected against *supersede surgically*: only skill discovery is shared across the cohort; agent formats genuinely differ per tool (kiro-cli `.json` vs kiro-ide `.md`; per-tool frontmatter mappings), so agents stay private and the three ADRs' agent decisions stand untouched.
- **Adopt `.agents/skills/` via symlinks from each native dir.** Rejected for the same no-symlink posture reason ADR-0039 records; a direct copy to the shared prefix achieves single-source-of-truth without it.

## References

- [RFC-0052 Decision 3 + Evidence](../rfc/0052-shared-prefix-aware-multi-adapter-install.md) — the cohort-support evidence base and the explicit-Approver-yes requirement.
- [ADR-0039](0039-footprint-co-ownership-install-identity-and-shared-prefix-class.md) — the `shared` prefix class and co-ownership model this routing relies on.
- [ADR-0001](0001-adopt-agents-md-and-doc-hierarchy.md) — the partial-amendment status idiom precedent.
- Cohort docs: [Cursor](https://cursor.com/docs/skills), [Gemini CLI](https://geminicli.com/docs/cli/skills/), [Copilot](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills).
