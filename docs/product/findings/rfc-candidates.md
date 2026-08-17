# RFC Candidates

Candidate RFCs surfaced by work-loop scope-deferrals and `frame-situation`
escalations. Each entry represents a pattern, gap, or design question that
recurred enough to warrant community input before implementation.

**How entries arrive here:** when `work-loop` defers something out of scope
and the item looks RFC-shaped, the agent prompts "Add to
`rfc-candidates.md` or `roadmap-intents.md`?" This is the register for the
RFC branch of that prompt.

**How entries leave:** when a candidate is accepted into `docs/rfc/`, update
`Disposition` to `→ RFC-NNNN`. When a candidate is rejected or absorbed,
note the reason.

| Problem | Source | Surfaced by | Date | Priority | Disposition |
|---|---|---|---|---|---|
| Governance artifacts freeze a perishable delivery plan inside an immutable decision record, so correcting a forecast costs a full RFC cycle. Candidate: generalise a durable/perishable split into `CONVENTIONS.md` § Document lifecycle (cf. Kubernetes KEP graduation criteria, PEP `Provisional`). | RFC-0083 § Errata (2026-08-13) | `work-loop` / ini-008 reanchor | 2026-08-13 | Medium | Open — evidence in [`adaptive-planning-survey.md`](adaptive-planning-survey.md) |
| No automated signal detects that a queued spec's shipped dependencies moved after it was approved; drift surfaced only on human inspection. Candidate: an anchor-staleness fitness function as a repo-wide routing invariant, not a per-initiative fix. | RFC-0083 § Errata (2026-08-13) | `work-loop` / ini-008 reanchor | 2026-08-13 | Medium | Open — tracked as `ini-008-anchor-staleness-check` in `workspace.toml [backlog].open` |
| `docs/CONVENTIONS.md` § Superseding a frozen document licenses exactly two parenthetical shapes on a frozen `Status` line (supersession pointer; closed-`[backlog].open`-anchor pointer). Neither covers a **correction of an instruction that was already contrary to an accepted decision** — the Phase 4b `docsUrl` case, where the ADR predates the spec, so nothing was superseded. Candidate: license a third correction pointer, and reconcile the "exactly two" claim with annotations already in-tree that match neither shape. | spec/site-contract-provenance-cleanup AC1 (2026-08-17) | `work-loop` / ini-002 tech-site wave 1 | 2026-08-17 | Medium | Open — PR #993 shipped the accurate wording unlicensed rather than amend a governance contract without an RFC |
