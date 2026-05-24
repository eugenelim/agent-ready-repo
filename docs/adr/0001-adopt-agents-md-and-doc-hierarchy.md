# ADR-0001: Adopt AGENTS.md + spec/ADR/RFC governance

- **Status:** Accepted
- **Date:** YYYY-MM-DD <!-- replace with the date you adopt this template -->
- **Deciders:** <maintainers>
- **Supersedes:** none
- **Related:** [`docs/CONVENTIONS.md`](../CONVENTIONS.md)

## Context

This repository is a mixed monorepo (apps + shared packages + tooling) with
a small-to-medium contributor base. We use Claude Code and other AI coding
agents heavily, alongside human contributors.

We had two problems:

1. **Documentation drift.** Decisions, designs, and current-state
   descriptions were mixed in the same files. Every quarter someone had to
   re-read a 2,000-line README to find out why a thing was the way it was,
   and the answer was usually "we don't remember."
2. **Inconsistent agent quality.** Agents (Claude Code, Cursor, others) gave
   wildly different output depending on which contributor was using them,
   because each contributor had their own ad-hoc prompts and rules.

We needed a single, opinionated structure that:

- Keeps four kinds of writing separated by lifecycle (foundational, decisional,
  proposal, feature-level).
- Gives agents a stable context file at the root, in a format that works
  across tools.
- Stays under the empirically-observed instruction budget (~150-200 instructions
  before adherence degrades).

## Decision

We adopt the following:

1. **`AGENTS.md` at the repository root** as the canonical agent context file,
   with `CLAUDE.md` as a symlink. The file is kept under ~200 lines and uses
   progressive disclosure — it points to docs and skills rather than
   embedding their content.

2. **A two-axis documentation hierarchy** in `docs/`, separated by audience
   and lifecycle:
   - **Foundational** (single file): `CHARTER.md` — mission, scope, principles.
     Modeled on the [CNCF charter pattern](https://contribute.cncf.io/maintainers/governance/charter/).
   - **Frozen history**: `adr/` (decision records).
   - **Governance**: `rfc/` (in-flight proposals).
   - **Living, internal**: `architecture/` (code structure — for contributors),
     `product/` (roadmap + changelog — for maintainers).
   - **Living, external**: `guides/` (Diátaxis-organized user docs:
     `tutorials/`, `how-to/`, `reference/`, `explanation/`).
   - **Per-feature**: `specs/<feature>/` — living during build, frozen after ship.

3. **Conventional Commits** for all commits, with footer references to the
   spec/ADR/RFC the commit implements.

4. **Per-package `AGENTS.md`** for package-specific rules, loaded on demand
   by the agent's directory walk.

5. **Skills in `.claude/skills/`** for repeating multi-step tasks; not added
   speculatively, only after a workflow is performed three times.

The full mechanics are in [`docs/CONVENTIONS.md`](../CONVENTIONS.md).

## Consequences

**Positive:**

- New contributors and agents have one place to look first (AGENTS.md) and a
  predictable hierarchy below it.
- Decision history is preserved (ADRs) without polluting current-state docs
  (architecture/).
- The instruction budget is respected — root AGENTS.md is small; detail is
  loaded on demand from skills and subdirectory AGENTS.md files.
- Agent output becomes more consistent across contributors because the
  prompt-shaping context is shared.

**Negative:**

- More upfront ceremony for changes that touch governance (RFC required).
- Contributors have to learn the difference between an ADR and a spec, and
  between a spec and an RFC. The CONVENTIONS.md doc tries to make this fast.
- Per-package `AGENTS.md` files are an attractive nuisance — easy to bloat.
  We mitigate by linting them in CI (see `tools/lint-agents-md.py`).

**Neutral / to revisit:**

- AGENTS.md is still an evolving cross-tool standard. If it diverges
  meaningfully from CLAUDE.md's expected format in the future, we'll revisit.
- We don't currently enforce a maximum size on subdirectory AGENTS.md files
  in CI — only the root. We may add a cap if package-level files start to
  bloat.

## Alternatives considered

- **Single `CLAUDE.md`, no AGENTS.md.** Rejected: locks us into one tool, and
  Claude Code itself reads AGENTS.md as a fallback. Symlinking gives us
  cross-tool compatibility for free.
- **A `constitution/` folder with separate mission, principles, and glossary
  files.** Initially adopted, then rejected: the foundational content is
  short and meant to be read together. A folder implied editorial weight
  the project doesn't have, and fragmenting the mission across files made
  it harder for both humans and agents to load the whole picture. Mature
  projects (Kubernetes, CNCF projects, ASF) overwhelmingly use a single
  charter document. Glossary moved to `guides/reference/` where vocabulary
  belongs.
- **No ADRs, just a richer architecture doc.** Rejected: this conflates "why"
  with "what" and means the rationale gets lost as the architecture evolves.
- **No RFC layer; just open an ADR for every proposal.** Rejected: ADRs are
  records of decided things; RFCs are deliberation. Mixing them muddies both.
- **Specs and plans in the same file.** Rejected: they have different
  lifecycles. The spec is a contract that should match implementation; the
  plan is a working document that's allowed to evolve. Conflating them
  blocked us from updating either honestly.
- **No `product/` directory — keep roadmap and changelog at the repo root.**
  Rejected: roadmap and changelog are the product equivalent of
  `architecture/`; without a parallel product layer, there's no answer to
  "what is the product doing today" — only frozen specs and decision
  history. Co-locating them makes the parallel obvious.
- **Free-form user docs, not Diátaxis.** Rejected: the empirical case for
  Diátaxis (Canonical, LangChain, Sequin, multiple CNCF projects) is
  strong, and the failure mode it prevents — mixing tutorials with
  reference, how-tos with explanation — is the dominant cause of bad
  user docs. The four-bucket structure also gives agents a crisp
  decision when generating user-facing content.
- **Auto-generate AGENTS.md from the codebase.** Rejected: empirical evidence
  (ETH study, March 2026) shows auto-generated context files perform *worse*
  than no file. The signal-to-noise ratio is too low.

## References

- [AGENTS.md spec](https://agents.md/)
- ["Writing a good CLAUDE.md", HumanLayer](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- [Spec-driven development, Thoughtworks](https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices)
- [CNCF charter pattern](https://contribute.cncf.io/maintainers/governance/charter/)
- [Diátaxis documentation framework](https://diataxis.fr/)
- [Keep a Changelog](https://keepachangelog.com/)
