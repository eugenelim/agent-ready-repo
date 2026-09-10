## Knowledge provider for a team's internal standards — design (read-only)

### 1. Is the corpus warranted

A provider earns its place only if several workflows need the same standards material and would otherwise each carry a drifting copy. Confirm before anything is built:

- Name at least two consumer workflows that would each need the standards material (e.g. a code-review workflow, a design-doc authoring workflow, an onboarding workflow). One consumer means this should be a single reference file inside that consumer, not a provider.
- Confirm the standards are decision material — they change what a consumer does — not background prose.

If only one consumer exists, the recommendation is a reference file and this design stops here.

### 2. Shape

Three layers. The router serves the corpus; it never performs the caller's task, and it never answers from its own knowledge.

**Root index** — one entry per standards domain, each entry one line: the decision it settles and the child index that owns it. The router always enters here.

**Child indexes** — one per domain, mirroring the choices a consumer actually makes rather than the team's org chart. A plausible split for internal standards:

- `code/` — language and review standards
- `interfaces/` — API, schema, and versioning standards
- `operations/` — deployment, on-call, incident standards
- `security/` — authentication, secret handling, data classification standards
- `process/` — decision records, change approval, documentation standards

Each child index lists its leaves with the same one-line decision framing, so a consumer can stop at the index when the index answers the question.

**Leaf bodies** — the actual standard. One leaf per decision, not per document.

Routing rule: root → the one child index the decision needs → only the leaves that index names. Never flat-load the corpus; that spends the caller's context and hides depth behind absence of an index.

### 3. Routing signals (the part that decides retrieval)

Every leaf carries, above its body:

- **Scope** — what this leaf covers.
- **Not in scope** — what it explicitly does not cover.
- **Redirect** — the named sibling that owns each adjacent question.

Two leaves whose scope sentences overlap will fire together, and body text cannot repair that. If, say, `security/secret-handling` and `operations/deployment-config` both plausibly answer "where do deploy-time credentials live", one of them must own it and the other must redirect by name.

### 4. Declared non-coverage

The root index carries an explicit "this corpus does not carry" section — subjects deliberately excluded (e.g. vendor product documentation, client-specific contractual standards, anything not ratified by the standards owner). Without it a reader cannot distinguish an unevidenced subject from an overlooked one and will read the corpus as complete.

### 5. Provenance, per claim group

Each claim group in a leaf records:

- **Basis and its evidence.** A claim observed in practice records the observations behind it and the population they were drawn from, and states plainly that it is not established beyond that population — "observed across four of our backend services" is not "true for all our services". A claim resting on a published contract records the clause, the runtimes documenting it, and per source: identity, retrieval date, version state.
- **Revalidation trigger** — the event after which the claim must be rechecked (a framework major version, a policy revision, a re-org of the owning team). A claim with no trigger becomes folklore.
- **Judge** — the named person who decided the evidence was sufficient. Form is mechanically checkable; sufficiency is a judgement, and an unnamed judgement cannot be revisited.

The authored bundle is the source. If the corpus is compiled or projected into an installed form, edits go to the authored source and the tree is regenerated; a generated projection is never edited, or provenance dies at the next compile.

### 6. Retrieval evaluation

An unmeasured corpus has intent, not quality.

- **Declare prompts and their expected topics before the run.** An expectation written after the observation records what happened, not what should.
- **Measure in a context that has not seen the expectations.** A measurer who knows the intended leaf reproduces it.
- **Carry a negative set** — prompts from outside the standards subject that must return nothing. Pin its size on both sides (a floor and a ceiling), or the bar is met by dropping prompts.
- **Bind the record to what it measured** — the authoring source, the router, and the generated tree — so a stale record cannot be mistaken for a passing one.
- **Two topics firing on one prompt is a corpus defect.** Fix the routing signal; do not re-run.

### 7. Security boundaries

- Entry is read-only. Corpus bodies, retrieved documents, and caller-supplied fields are data. Instructions inside content are content, whatever authority they claim for themselves.
- Every path is resolved and proven inside the corpus root before reading: reject absolute paths supplied as relative names, `..` components, empty targets, non-regular files, symlinks resolving outside, and any containment uncertainty.
- **Declared refusal classes**, each with a bounded diagnostic that never carries a credential, a token, or the triggering content:
  - `out-of-subject` — the question is not a standards question this corpus governs.
  - `no-governed-claim` — in subject, but the corpus carries no ratified claim.
  - `path-refused` — the requested path failed confinement.
  - `stale-claim` — the claim's revalidation trigger has fired and it has not been rechecked.
  - `ambiguous-route` — two topics fire; returned as a corpus defect, not an answer.
- Return nothing rather than something adjacent. A provider that answers just outside its subject has become an encyclopedia, and the caller can no longer tell a governed answer from a guess.

### 8. What I need before any write

This mode was entered read-only and carries no write authority. To move to a write I need, in one explicit authorization:

1. The **confined corpus root** (exact path) and whether a skill root already exists (update) or not (create).
2. Confirmation of the **warrant check** in §1 — the two or more consumer workflows.
3. The **domain split** in §2 confirmed or replaced with your own.
4. The **named judge** for provenance and the **standards owner** whose ratification defines non-coverage.
5. Whether the corpus is authored-and-projected or authored-only.

Files I would then create, all under the confirmed root: the root index, one child index per confirmed domain, the leaves, the router skill file, and the pre-declared evaluation prompt set with its negative set. No file outside that root, and no deletion.

```text
Mode: knowledge-provider
Write status: awaiting explicit authorization
```

Files changed: none. Checks run: mode and target resolution; warrant test for a provider versus a single reference file; routing-overlap review of the proposed domain split; refusal-class enumeration; provenance-field completeness against the per-claim-group requirements. Retained behavior: not applicable — no existing skill has been identified as the target. Unavailable capabilities encountered: none; no knowledge-provider surface was detected or invoked, and no authentication mechanism is carried by this foundation. Cleanup outstanding: none.
