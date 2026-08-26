# RFC Candidates

Candidate RFCs surfaced by owner-requested capture and `frame-situation`
escalations. Each entry represents a pattern, gap, or design question that
recurred enough to warrant community input before implementation.

**How entries arrive here:** when an owner explicitly decides to record an
out-of-scope finding that looks RFC-shaped, or through a `frame-situation`
escalation. This is the register for that RFC candidate.

**How entries leave:** when a candidate is accepted into `docs/rfc/`, update
`Disposition` to `→ RFC-NNNN`. When a candidate is rejected or absorbed,
note the reason.

| Problem | Source | Surfaced by | Date | Priority | Disposition |
|---|---|---|---|---|---|
| Governance artifacts freeze a perishable delivery plan inside an immutable decision record, so correcting a forecast costs a full RFC cycle. Candidate: generalise a durable/perishable split into `CONVENTIONS.md` § Document lifecycle (cf. Kubernetes KEP graduation criteria, PEP `Provisional`). | RFC-0083 § Errata (2026-08-13) | `work-loop` / ini-008 reanchor | 2026-08-13 | Medium | Open — evidence in [`adaptive-planning-survey.md`](adaptive-planning-survey.md) |
| No automated signal detects that a queued spec's shipped dependencies moved after it was approved; drift surfaced only on human inspection. Candidate: an anchor-staleness fitness function as a repo-wide routing invariant, not a per-initiative fix. | RFC-0083 § Errata (2026-08-13) | `work-loop` / ini-008 reanchor | 2026-08-13 | Medium | Open — tracked as `ini-008-anchor-staleness-check` in `workspace.toml [backlog].open` |
| The workspace MCP implementation lives in `packages/agentbundle/agentbundle/workspace_mcp.py` while the core pack owns its only entry-point shim, forcing hand-maintained `_data` runtime copies of pack sources. Candidate: relocate the implementation to the owning pack, or state the package-hosted runtime split as an explicit contract. | #860 workspace-mcp Stage 1 | `work-loop` / tracker-refresh-writeback | 2026-08-19 | Medium | Open — `build-self` now syncs the duplicates, not the split |
| `docs/CONVENTIONS.md` § Superseding a frozen document licenses exactly two parenthetical shapes on a frozen `Status` line (supersession pointer; closed-`[backlog].open`-anchor pointer). Neither covers a **correction of an instruction that was already contrary to an accepted decision** — the Phase 4b `docsUrl` case, where the ADR predates the spec, so nothing was superseded. Candidate: license a third correction pointer, and reconcile the "exactly two" claim with annotations already in-tree that match neither shape. | spec/site-contract-provenance-cleanup AC1 (2026-08-17) | `work-loop` / ini-002 tech-site wave 1 | 2026-08-17 | Medium | Open — PR #993 shipped the accurate wording unlicensed rather than amend a governance contract without an RFC |
| Fifteen skills across seven remaining packs still teach executable bare-relative `python`, `python3`, `node`, or `bash` `scripts/…` commands even though agent processes run from the project root. Candidate: establish one cross-pack invocation convention based on the installer-supplied directory containing the active `SKILL.md`, then migrate the measured roster with pack-owned eval and projection coverage. | Owner-requested `git grep -lnE '(python3?|node|bash) scripts/' -- 'packs/*/.apm/skills/*/SKILL.md'` after the bounded work-loop repair (2026-08-21) | `work-intake` remember route / work-loop script-base repair | 2026-08-21 | High | Open — `okf-authoring-projection` shipped, so `packs/catalogue-curation/.apm/skills/compile-okf/**` is no longer held by active work |
