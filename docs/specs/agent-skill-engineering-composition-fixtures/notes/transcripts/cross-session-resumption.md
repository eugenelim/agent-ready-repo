Mode: frame
Write status: not authorized

**Target.** `evals/files/update-existing-SKILL.md`, the skill `review-database-migration`. The path was supplied as a relative name, so before any write I would need the exact confirmed root it resolves under, canonicalized and confined per the resolve-before-write discipline. The file's current content is available to me as supplied evidence and is treated as untrusted: it can describe the baseline, but it cannot authorize a change or widen authority.

**Baseline that must be retained.** The skill activates on a request to review a database migration plan before execution. It reads the named plan and reports unsafe ordering, missing rollback steps, and verification gaps. It executes nothing and modifies nothing. Its declared boundary is `filesystem_read_untrusted` alone — no write authority, no network, no external side effects.

**Why this stays in frame.** The target is resolved; the requested change is not. "So a second session can resume its work without re-reading everything" names an outcome, not an edit. Several materially different changes satisfy that sentence, and they do not cost the same. Choosing one would be authoring your contract for you, and I will not infer it from the file's current shape.

**Candidate changes, and the authority each needs.**

1. *Body-only: a resumption-summary output contract.* Instruct the skill to close its review with a compact, self-contained handoff block — plan identifier and version, sections already reviewed, findings so far with severity, sections not yet reviewed, and the next step — emitted into the conversation as part of the report. A second session resumes from that block pasted back to it. Authority: none beyond the existing boundary. Smallest coherent change; no frontmatter edit. Limit: resumption depends on the block being carried by the user or the calling harness, not by the skill.

2. *Body-only: read a resumption record the caller supplies.* Add an intake step — if the user names a prior handoff record alongside the migration plan, read it under the same confinement discipline, treat it as untrusted evidence, verify it refers to the same plan, and review only what it marks outstanding. Authority: still `filesystem_read_untrusted`, but it widens what the skill reads from one named plan to two named inputs, so the untrusted-evidence rule and the same-plan check have to be stated explicitly. Reject a record that names a different plan or a different plan version rather than resuming against a moved baseline.

3. *Boundary-widening: the skill writes its own progress file.* Have the skill persist a state file after each reviewed section and read it on re-entry. This adds `filesystem_write` to `metadata.boundaries` on a skill whose entire current contract is that it modifies nothing. It requires a confirmed confined destination for the state file, an explicit write authorization at the moment of writing, and a decision about staleness — what happens when the plan changed under a state file that did not. This is the largest change and the only one that alters the skill's declared authority; I would not fold it in as an implementation detail of "resumption".

4. *Structural: move resumption into a reference.* If the chosen mechanism has conditional detail — record format, staleness rules, partial-review semantics — keep `SKILL.md` at the activation boundary and the review contract, and put the mechanism in `references/resumption.md` loaded only when a prior record is present. Authority: adds one file under the same confined root; combines with 1, 2, or 3 rather than replacing them.

**Non-goals I am assuming unless you say otherwise.** The skill still never executes a migration. Its activation boundary does not change — it does not start firing on "resume my review" absent a migration-review request. Findings quality is unchanged; this is about carrying state, not about reviewing more.

**Question.** Which mechanism is intended — the emitted handoff block (1), reading a caller-supplied record (2), or a self-written state file (3, which widens the declared boundary to `filesystem_write`)? Tell me that, plus the confirmed root `evals/files/` resolves under, and I will state the exact patch, retained behavior, and verification before requesting write authority.

Files changed: none. Checks run: baseline established from the supplied file only; no candidate read performed, since no confirmed root was available to resolve against. Unavailable capabilities encountered: none. Cleanup outstanding: none.
