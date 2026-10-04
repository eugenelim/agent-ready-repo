# Governance Extras Pack — Design Document

Living design reference for the governance-extras pack. Records the philosophy, invariants, and key decisions so the reasoning survives beyond individual PRs and applies when extending or replacing any skill.

This pack provides the RFC mechanism itself, so it has no upstream RFC of its own.

---

## TL;DR

`governance-extras` installs the governance layer on top of `core`: structured RFCs for cross-cutting proposals, ADRs for closed architectural decisions, and convention edits through tracked RFC review. Every skill previews its output and target path before writing anything — you confirm before any file is created. The scope is repo-only (governance records are per-project) and the dependency on `core` is required. ADRs resolve the portable `decision-record` role through Core before numbering or indexing, so adopter policy and established custom/external destinations win; `docs/adr/` remains the catalogue fallback. RFC and ADR are separate artifacts by design: an RFC is a live discussion; an ADR is a closed, immutable record. They serve different purposes and must not be conflated.

---

## Non-Goals

Things a reasonable reader might expect this pack to solve. It doesn't, by design:

- **Live governance dashboards.** `navigate-decisions` is a read-only, on-demand derivation from canonical ADR and RFC records. It does not maintain a live dashboard, send notifications, or integrate with an issue tracker. Generated query results and HTML files are disposable projections; the canonical records are the authority.
- **RFC comment thread management.** Responding to reviewer comments, threading replies, and tracking per-reviewer objections are a wiki or issue tracker's job. This pack writes structured RFC documents; comment threads live outside the repo.
- **Automated decision enforcement.** A shared convention is documentation — a shared understanding of how the project works. It is not a validator, a lint rule, or a CI gate. The pack writes the document; enforcement is the team's job.
- **Team approval workflows.** This pack writes RFC and ADR files. It does not create GitHub review requests, post to Slack, or orchestrate multi-person sign-off. The human gates (G-draft, G-accept, G-merge) are the adopter's checkpoints — the pack cannot substitute for the human work of circulating a document and getting a decision.

---

## 1. Why decisions need paper trails

### The problem this pack solves

Software teams make hundreds of architectural decisions over a project's lifetime. Most of those decisions are made in a chat thread, a meeting, or a conversation at a whiteboard — and the reasoning evaporates within a week. What survives is the decision itself (visible in the code or config) but not the *why*: the alternatives considered, the constraints that drove the choice, and the conditions under which the decision should be revisited.

This creates a class of repeated failure:

1. **Re-litigating closed decisions.** Without a record, a new team member or a team six months later re-opens the same debate. The original team spends time relitigating a settled question instead of moving forward.
2. **Overbuilding around an outdated constraint.** A decision made under a specific constraint ("we chose this because we were on AWS Lambda at the time") accumulates downstream assumptions. When the constraint changes, no one knows which decisions were contingent on it.
3. **Cargo-culting patterns.** Without rationale, a convention looks arbitrary. Teams follow it for the wrong reasons or abandon it without realizing the cost.

`governance-extras` addresses this by making the paper trail a first-class product of the development loop. An RFC is written before cross-cutting work begins; an ADR is written after a decision is made. Both are committed to the repo, versioned alongside the code they govern.

### Decisions outlive their authors

The ADR exists to answer "why did we choose this?" when the author is gone. This is the single most important property of the artifact. An ADR that does not carry the honest forces behind the decision — the alternatives that were seriously considered, the constraint that made the chosen option win, the condition under which the decision should be revisited — is worse than no ADR. It gives the next reader false confidence that the decision is documented while leaving them unable to evaluate whether it still applies.

The quality bar for an ADR is not "the decision is recorded." It is "a future engineer can reconstruct the reasoning from this document without speaking to anyone who was in the room."

---

## 2. RFC and ADR as separate artifacts

### Why two artifact types

The pack ships two distinct governance artifact types — RFC and ADR — because they serve structurally different purposes that cannot be collapsed into one form:

**RFC (Request For Comments):** A *discussion* artifact. An RFC is for "should we do X?" — a cross-cutting proposal that needs input before anyone builds. The RFC is a live document during its comment period: it evolves as objections are raised and addressed. When the comment period closes, the RFC's status is updated (Accepted, Rejected, or Deferred) and its body is frozen. The RFC is the debate; the ADR is the verdict.

**ADR (Architecture Decision Record):** A *record* artifact. An ADR is for "we decided X" — a closed, immutable record of a decision that was made. ADRs do not have comment periods. They record the decision, the forces that drove it, the alternatives that were considered and rejected, and the conditions under which the decision should be revisited. Once accepted, the ADR body is immutable — a reversal is a new ADR that supersedes the old one, never an edit.

### Why they must not be conflated

An RFC that is used to record a decision (instead of proposing one) produces a document that looks like a debate but carries a predetermined conclusion — misleading to every future reader who tries to evaluate whether the decision is still sound.

An ADR that is used to open a debate (instead of recording a closed one) produces a document with no clear decision — defeating the purpose of the ADR index entirely.

The pattern the pack enforces: an RFC that gets accepted generates an ADR. The RFC is the record of the debate; the ADR is the record of the outcome. They are different documents because they are different things.

---

## 3. The preview-before-write contract

### What it is

Every skill in this pack that writes a file — `new-rfc`, `new-adr` — shows you the output before creating anything on disk:

- The identifier (RFC-NNNN or ADR-NNNN)
- The target path (absolute and repo-relative)
- The index path that will gain a row
- A content preview of the drafted document

The file is not created until you confirm. This is not optional behavior or a flag — it is the structural shape of every write skill in the pack.

For `new-adr`, semantic destination resolution happens before the identifier,
ordinal scan, filename, or sibling index is selected. Compatible Core returns
`semantic-surface-resolution.v1`; the skill consumes its role, locators,
evidence, capability, confinement, revision, confirmations, and independent
authority facts unchanged. The precedence is explicit destination, declared
policy/configuration, established repository convention, established external
destination, ambiguity, then absence. Mandatory policy rejects a conflicting
explicit destination. Without compatible Core, the skill renders a portable
`decision-record` handoff and stops; human confirmation can correct its
evidence but cannot authorize a repository write or invent a second resolver.
External locators remain external, and every terminal or unsafe outcome has zero
ordinal, index, directory, or file effects.

### Why it exists

Governance documents are shared artifacts. An RFC or ADR committed to the repo
is immediately visible to every contributor who reads `docs/rfc/` or the
resolved `decision-record` destination. A file created before the author has
approved its content creates a window where the repo's governance record is in
a half-formed state.

The preview gate is cheap — it costs one confirmation before a file is written — and it eliminates the failure mode of the wrong content going to a shared location. The cost of fixing a bad ADR after it's committed (triggering a supersession record, updating the index, explaining the correction) is always higher than the cost of reading a preview.

---

## 4. The two critique tracks in new-adr

### Why two tracks

`new-adr` runs two critique passes on every ADR it produces:

1. **Standard critique.** The usual review: is the decision clear? are the alternatives honestly stated? is the rationale sound? are the consequences — including the negative ones — named?

2. **Adversarial critique (the strongest case against the decision).** This is the question the ADR must answer before it can be considered complete: what would a thoughtful, well-informed opponent say? What is the strongest case for *not* taking this decision? What assumption, if false, would make this decision wrong?

### Why the adversarial track is not optional

A critique that only validates the decision has been recorded — the decision is clear, the alternatives are named — produces an ADR that is formally complete but intellectually weak. The next engineer who reads it to evaluate whether the decision still applies has no basis for challenge: the document presents the reasoning without the strongest counterargument.

The adversarial track forces the decision to be held against its strongest opponent. An ADR that survives the adversarial critique is an ADR the next reader can trust — not because the decision is beyond challenge, but because the strongest challenge has been named and acknowledged.

This mirrors the `adversarial-reviewer`'s role in core's build loop: the value of the review comes from genuine adversarial intent, not from confirming the work was done.

---

## 5. Repo scope by design

### Why governance is per-project

`governance-extras` installs at repo scope only. This is not a configuration option — `allowed-scopes = ["repo"]` is declared in `pack.toml`.

The reason is structural: governance records are inherently project-specific. An ADR recording why this project uses Postgres is not useful in a different project. An RFC proposing a change to this project's A shared convention governs only this project. Unlike `architect` (whose method is portable across projects) or `desk-research` (whose methodology applies regardless of project), governance records carry the context of a specific project's history, constraints, and team decisions.

Installing governance-extras at user scope would make every skill write to a user-global location — which is the wrong place for records whose meaning depends on the project they govern.

### Why core is a required dependency

`governance-extras` writes RFCs to the repository RFC surface, ADRs to the
resolved `decision-record` destination, and conventions to
whichever artifact owns each rule; the catalogue seed paths are only fallbacks. These
surfaces only have meaning after `core` has scaffolded the repo structure. An
RFC in a repo with no governance surface, no agreed conventions, and no
established work loop is documentation in search of a process.

The dependency is version-pinned at `^0.1` — a soft floor that allows `core` to evolve without blocking governance-extras updates, while ensuring the basic scaffold is in place. The dependency is enforced at install time.

---

## 6. MADR-aligned but lean

### The format decision

ADRs in this pack follow a lean MADR-aligned format. "MADR" (Markdown Architectural Decision Records) is an established ADR template format with a defined set of sections. "Lean" means the pack omits sections that add ceremony without adding information for a small team.

The core sections (Decision, Context, Consequences, Alternatives considered) are always present. Optional sections (Decision drivers, Decision summary, Confirmation) are offered but not required — include each when it earns its place.

### What "earn its place" means

The Decision summary is a first-screen TL;DR placed before Context. It earns its place on a long ADR where the actual decision is not visible on the first screen — a multi-line title, a paragraph of metadata, and a long Context can push it off screen. On a short ADR, a five-line Decision summary is pure redundancy. The decision whether to include it is made per-ADR, not as a policy.

The same principle applies to every optional section: include it when a reader of the final ADR would benefit from it; omit it when it would repeat content already in a required section.

### Why lean over full MADR

Full MADR is designed for large teams and high-ceremony environments. Every section is required; the template is comprehensive. For a small team or a solo project, the overhead of maintaining every MADR field on every ADR produces documents that are formally complete but tediously redundant — teams start copying boilerplate rather than writing decisions. The lean variant keeps the load-bearing structure (decision + alternatives + consequences) without the process overhead.

---

## 7. Safety invariants

These constraints must never be violated by any skill in this pack or any skill that extends it.

1. **Preview before write, always.** No skill may create a file in a repository
   RFC, resolved decision-record, or other governance location without first
   displaying the identifier, target path, and content preview and receiving
   explicit author confirmation.

2. **ADR bodies are immutable after acceptance.** No skill may edit an accepted ADR's body. A reversal is a new ADR that supersedes the old one, never an in-place edit. The old ADR's body stays as history; only the status line changes.

3. **RFC and ADR must not be conflated.** No skill may use an RFC as an ADR or vice versa. An RFC that gets accepted generates an ADR; the two are separate files with separate purposes.

4. **Conventions and charter changes route semantically.** Maintenance and clarification are PRs; a changed obligation uses the unresolved-direction test; authority, mission, scope, and foundational principles are reserved. No skill routes on a pathname.

5. **Adversarial critique track is not optional.** Every ADR produced by `new-adr` includes the adversarial critique — the strongest case against the decision. An ADR that omits the adversarial track is not complete.

6. **`navigate-decisions` is read-only.** It never creates or modifies ADR files, RFC files, index entries, or any governance artifact. Its architecture is on-demand derivation from canonical records: it reads `docs/adr/` and `docs/rfc/` through the repository's blessed confined-filesystem helpers, derives a bounded query result or a self-contained offline HTML file, and leaves the canonical sources unchanged. Internal renderer, parser, payload, search, graph, and styling choices remain implementation decisions as long as the accepted behavior and safety contract holds. ADR and RFC authoring stays with `new-adr` and `new-rfc`; `navigate-decisions` does not take authoring work.

---

## 8. navigate-decisions architecture

### Read-only and on-demand derivation

`navigate-decisions` derives every result from canonical ADR and RFC records in `docs/adr/` and `docs/rfc/` at query time. It does not maintain a durable index or graph: every query discovers, admits, and reads the corpus fresh. Generated query results and offline HTML files are disposable projections; the canonical Markdown records remain the only authority.

### ADR and RFC separation

ADR and RFC are distinct artifact types with separate shapes, admission rules, and lifecycle values. The navigator admits them together as one corpus but never flattens their differences. Every record carries its `kind`, its exact lifecycle `raw_value` (including missing, unfamiliar, or qualified values), and its `source` path. Missing a `**Status:**` field yields the missing-state marker; any present value is admitted as-is. The navigator never normalizes lifecycle values across kinds or invents a single current-version answer across partial supersession scopes.

### Confined reads via vendored file_safety

Every corpus read goes through the repository's blessed confined-filesystem helper (`file_safety.py`), vendored beside the skill's scripts. Symlinks, hard links, special files, traversal escapes, duplicate identities, and identity-changing paths are refused before any content is read. A candidate larger than 2 MiB is refused with code `input_too_large`. Malformed candidates, unsafe inputs, and duplicate kind-plus-ordinal identities fail the whole operation; partial truth is never returned.

### Checked versus contextual versus navigation-only relationships

Three distinct trust classes govern every relationship the navigator emits:

- **Checked lineage** (`trust_class: checked`): both endpoints are admitted and reciprocal supersession metadata agrees on relation and scope. This is the only authoritative lineage.
- **Candidate lineage** (`trust_class: candidate`): a supersession entry whose mirror was not found. Unresolved evidence, not checked lineage.
- **Contextual reference** (`trust_class: contextual`): an explicit `Related` field reference. The source record points here; the relationship is not validated lineage.
- **Navigation-only** (`trust_class: navigation_only`): a caller assertion supplied at query time. Non-authoritative navigation input; it never becomes a source-record fact.

Free-form prose, filenames, dates, directory proximity, and model judgment do not create checked edges.

### Multi-form views

The same corpus fact model supports four views: corpus list (orientation and filtering), lifecycle graph (what superseded what and whether replacement is whole or partial), guidance context (a wider record beside narrower or related guidance), and record detail (complete rationale and provenance). Each view is a rendering lens over the same facts. Visual hierarchy, contextual references, and navigation grouping never become checked lineage. The implementation may use different internal representations and code paths for the agent query and HTML views; they are not required to share a renderer, component, payload, or search module.

### Safe offline publication

The HTML explorer is one self-contained file embedded with data, styles, and scripts. It performs no network or adjacent-file reads at runtime. Publication is atomic: an exclusively created temporary sibling is synced and then published with a no-replace operation; there is no overwrite mode. On POSIX, the temporary sibling and the published file are readable and writable only by their owner from creation through publication. A destination inside the repository worktree is refused; a full export exceeding 100 MiB is refused or requires explicit confirmation.

### Measured full-versus-bounded rule

The full-versus-bounded selection rule is evidence-backed. Chrome scale evidence recorded in the verification ledger shows the current corpus (238 records, ~5.7 MiB) is practical in full mode; the 100 MiB file-size threshold is the measured limit at which desktop Chrome stops being practical. Bounded mode is a first-class representation, not a partial-failure fallback: it retains the complete record inventory, exact headers, checked graph, contextual references, and provenance while omitting bodies.

### Reference-policy boundary

Every query result and HTML view states that it reports recorded decisions and candidate context, not the complete policy applicable to a proposed action. Absence is not permission, and retrieval relevance is not authority.

### Implementation freedom

Internal renderer, parser, payload, search, graph, styling, and module choices remain implementation decisions as long as the accepted behavior and safety contract holds. A future change that promotes a contextual relationship to checked authority, changes the public query contract, or adds a runtime dependency or hosted service crosses a separate governance boundary and must be decided explicitly.

---

## 9. Design decisions and rationale log

### Why RFC and ADR are separate artifacts (from v1)

The alternative was a single governance document type that serves both discussion and record functions — an "RFC/ADR hybrid" that starts as a live debate and transitions to a frozen record. This was rejected because the two lifecycle states (live and frozen) have incompatible properties: a live document should evolve as new objections emerge; a frozen document should never change. A hybrid would require the document to stop evolving at a specific transition point, creating a sharp discontinuity that is harder to enforce than keeping the artifacts separate.

**Alternative considered:** single document type with a lifecycle state transition (Draft → Open → Accepted, at which point the body freezes). Rejected because the single-document model obscures the structural difference between "this is a proposal being debated" and "this is a record of what was decided." Separate artifacts make the lifecycle states first-class rather than emergent from a status field.

### Why preview-before-write is structural, not optional (from v1)

The alternative was a `--dry-run` flag the author could pass to see the preview. This was rejected because a flag-based preview is a user opt-in, and the failure mode of not opting in (creating a file before reviewing it in a shared governance location) is worse than the friction of a mandatory confirmation step.

**Alternative considered:** `--dry-run` flag as in the current `agentbundle install` flow. Rejected because governance documents go to a shared location immediately: unlike an install preview (which affects only the local repo), an RFC or ADR preview is the last chance to catch a formatting error or a wrong path before the document is part of the team's governance record. The mandatory confirmation is the cheapest possible gate.

### Why MADR-aligned but lean, not full MADR (from v1)

Full MADR requires every section for every ADR, which creates ceremony overhead that disproportionately burdens small teams and solo projects. The lean variant keeps the sections that carry the decision (context, decision, consequences, alternatives) and makes the rest optional with a clear "earn its place" test.

**Alternative considered:** full MADR compliance, with every section required. Rejected because in practice, teams facing required empty sections fill them with placeholder text ("N/A", "none") that trains readers to skip sections they might otherwise benefit from. An optional section that is present when it adds value is more useful than a required section that is present with boilerplate.

### Why repo scope is not configurable (from v1)

The alternative was allowing `--scope user` as an option, letting a designer or architect maintain a personal governance log across multiple projects. This was rejected because a governance record's meaning depends on the project it governs. An ADR for "use Postgres as the primary store" does not belong in a user-level configuration that spans projects with different stores. The meaning of the record is project-bound; the scope must be too.

**Alternative considered:** user-scope as an opt-in flag. Rejected because governance documents are inherently shared artifacts — their value comes from being committed to the project repo, not from living in a personal configuration. A user-scope governance document is a personal note, not a governance record.
