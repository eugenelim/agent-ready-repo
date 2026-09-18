# Spec: design-handoff-read

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none — no synchronous, event, or RPC interface surface.
- **Shape:** mixed
- **Depends on:** [`docs/specs/design-output-addressing/`](../design-output-addressing/spec.md)
  — satisfied: that spec is Shipped, and it gave `direction/<slug>.md` and
  `tokens/<slug>.md` the addresses this spec reads.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: an author corrects them in place as the work teaches.
> `What this slice does not attempt` is **contract**: it records what an owner
> decided to leave out, so narrowing or widening it is an amendment, not a
> correction.

## Objective

The `frontend-engineering` shared pre-flight — the step all four of its modes run
— honours a named aesthetic direction instead of re-deriving one. It resolves the
adopter's `[design] output_dir`, reads the aesthetic direction, the per-screen
brief, and the token taxonomy when each is present, and consults its own canonical
product-reference set only for a slot no artifact filled. Today the pack has no
awareness of that directory at all: its only link to the design pack is a probe
for whether a skill is installed.

This is the one new trust boundary in the surrounding work. A value the adopter
controls becomes a filesystem path, files under it are read, and their content
reaches the step that emits production frontend code — which is the committed
deliverable, so anything the content induces outlives the session.

## What this slice does not attempt

Four controls were specified across review rounds two and three and are
deliberately **not** in this slice: rejecting a set of Unicode code points,
redacting location-bearing values out of artifact content, bounding what a
confirmation prompt displays, and predicating transcription on what the operator
saw. A fifth, **shape validation of frontmatter values**, went with them: it was
specified when the extracted set named sections and per-field shapes, and the
corpus then showed the real artifacts carry keys no template declares and omit
keys every template does. Validating a shape the writer never promised refuses
correct artifacts, so no shape obligation survives here and the first heading is
explicitly unvalidated free text. It belongs with the other four in the follow-on,
where a schema derived from the writers rather than guessed at can carry it. Each was specified as prose, and round four showed prose cannot carry any of
them — a code-point denylist cannot converge by enumeration, prefix-anchored
redaction has no reach over a whole-file value, and a display bound that truncates
what the operator sees while the emit step receives the whole file makes the
confirmation weaker, not stronger. They need an executable read path with unit
tests, not a longer paragraph. They are named in Follow-ons with that conclusion,
and this slice ships the controls prose can carry.

What that leaves is still the whole of the read: where the directory comes from,
whether it may be read at all, which files are this handoff, what is done with
them, and what happens when any of that fails.

## The three artifacts read

| Artifact | Read path | Required frontmatter `type:` | Written by |
| --- | --- | --- | --- |
| Aesthetic direction | `direction/<slug>.md` | `creative-direction` | `creative-direction` |
| Per-screen brief | `screens/<slug>/<screen>.md` | `screen-flow-brief` | `user-flow` |
| Token taxonomy | `tokens/<slug>.md` | `token-taxonomy` | `design-system` |

`<slug>` is the surface or product slug the operator names for the surface being
built; when the request carries none, the step elicits it before reading, and a
run where no slug is obtainable is a named refusal rather than a guess.

**The slug is validated before any path is composed, and never repaired.** It must
match `^[a-z0-9]+(-[a-z0-9]+)*$` and be at most 64 characters. A non-conforming
slug is a named refusal raised before a path exists, and the step does not
sanitize it, strip the offending characters, or derive a replacement from the
product name or anything else in the request — it says which rule the slug broke
and asks for a conforming one. This is transcribed from the shipped containment
module, which records the failure it prevents: given a slug carrying traversal
segments, an agent substituted a tidy slug of its own and completed the write, so
the operator asked for one name and silently received another while the control
reported success. That failure does not need the slug to escape the approved root
— a silently rewritten slug resolves *inside* it, passes confinement, and composes
one product's direction with another's taxonomy — which is why validation is not
covered by confinement and is stated here as its own control. All
three slots resolve under that one slug, so a direction from one product cannot be
composed with a taxonomy from another. `<screen>` ranges over every conforming
brief under `screens/<slug>/` — several briefs under one slug is the expected
case, not an ambiguity.

## What is consumed

Per artifact: **the first `# ` heading, the frontmatter as found, and the body as
one opaque block.** Nothing else, and no section name anywhere.

Measured against this repository's `docs/design/` on 2026-09-18, a section-keyed
contract does not hold: all six `screen-flow-brief` artifacts carry all nine of
their template's sections, but the one real `creative-direction` artifact carries
**none** of its template's four literally — its headings are
`What this amendment changes`, `New arbitration — two entries only`, `Hand-off`
and others, with only `Open questions for the gate` coming near the template's
`Open questions` as a superset string — and its frontmatter carries `scope`, `surface-genre`, `amends`, `status`, `gate`
and `updated` — six keys the `creative-direction` template never declares — while
carrying neither `slug` nor `date`. No `token-taxonomy` artifact
exists in the tree. These templates are scaffolds an author edits freely, not a
format.

**Frontmatter is taken as found.** A key a template declares but the file omits is
recorded absent and the artifact is still consumed. Only `type:` is required,
because it is what identifies the file as this artifact at all.

**Extraction reads raw text and discards HTML comments.** The screen-brief
template ships its genre sub-sections commented out and asks the author to
uncomment one, so comment content is normal in these files and renders invisibly
in any markdown viewer. Carrying it forward would feed the step text that whoever
reviewed the design tree never saw.

**The first `# ` heading is extracted, and it is not a discriminator.** All three
templates put a product name there. Real artifacts carry more than one `# ` line —
`docs/design/screens/team-orientation/internal-case-route.md` carries two — so the
first is taken. It is unvalidated free text; it is shown to an operator to read
and is never matched, compared, or used to decide belonging mechanically.

**This widens the pack's extract-only-expected-fields rule, deliberately.**
`packs/AGENTS.md` § Security and authoring rules says to extract only expected
fields and ignore embedded directives. Taking the body whole keeps the second half
and departs from the first, on the owner's decision of 2026-09-18, because the
corpus shows the narrow reading extracts nothing from the artifact this spec
exists to read. The compensating controls are the `type:` filter, the read bounds,
and the rule that no artifact content is ever followed as an instruction.

**`type:` decides what a file is, not whether it is trustworthy.** A file under a
read path whose frontmatter `type:` is absent, unparseable, or not that path's
required literal **is not that artifact**: the step skips it and keeps scanning,
as the sibling `experience-status` skill already does for a non-brief file under
`screens/<slug>/`. This is not a refusal. Stating it the other way round would
refuse a correct tree — `docs/design/` holds 28 distinct `type:` values across the
38 of its 42 files that carry one, including a `design-system` file under
`direction/` and a `canvas-composition` file under `screens/`.

The screen brief carries two type markers: frontmatter `type: screen-flow-brief`
and a body field `**Type:** screen-brief` that the structural-orphan lint reads.
This step validates the frontmatter marker; the two literals differ, so they
cannot silently agree.

## Approving the root

`output_dir` resolves by the `[design]` section's own contract — repo-root
`./agentbundle-layout.toml` first, then user-profile — which this spec names
rather than restates.

**Comparison is on resolved path components.** Wherever this spec says a path is
within a root, it means the realpath of the path equals the realpath of the root
or is a descendant of it component-by-component. A string prefix test is not that
test: `/home/u/repo-backup/design` is not within `/home/u/repo`. The repository
tree means the realpath of the worktree root.

**How the worktree root is determined is not fixed here, and the out-of-tree key
is advisory against a hostile clone.** The ordinary determination reads
repository-controlled state, so a cloned repository that authors
`agentbundle-layout.toml` can also make an out-of-tree root read as in-tree.

What that grants is worth stating exactly, because an earlier draft priced it as
costing the clone nothing it already had, and that was wrong. Defeating the
determination suppresses both the approval-time confirmation and the per-artifact
confirmation, so the agent reads files **outside the repository** — a shared design
vault, another product's tree — at the three fixed read paths, unconfirmed, and
carries them into committed code. That is the boundary between "reads this
repository" and "reads elsewhere on this machine", not merely defence in depth.

It is recorded rather than closed for two reasons: the user-profile half of the
union does not depend on the determination and still fires, and choosing a
determination source the repository under test cannot set is a decision this
slice's authority does not fix. An adopter cloning an untrusted repository should
treat the out-of-tree key as advisory.

**Reserved trees are refused, not confirmed.** A root at or beneath `.apm/` in the
repository branch, or at or beneath the agent host's installed-skill directories
in the user-profile branch, is refused outright. The shipped containment module
states this and states that every control not phrased around a write binds a
reader too; without it an `output_dir` of `.apm/skills/frontend-engineering` would
feed the agent's own instruction files to the emit step as design intent.

**A heightened root** is one that is user-profile-sourced **or** resolves outside
the repository tree — the union, because either alone leaves a case uncovered.
`packs/AGENTS.md` requires a belonging check for any user-level config shared
across projects, and a user-profile root can resolve inside the repository tree; a
repo-root value in a cloned repository can name an absolute path outside it. A
heightened root takes per-artifact operator confirmation.

Exactly two tokens name where the value came from, and neither is a path:
`repository layout configuration` and `user-profile layout configuration`.

## The read bounds

Stated once here; every other site names this section rather than restating a
number.

| Bound | Value | Origin |
| --- | --- | --- |
| Matching files read | 12 | Chosen ceiling over a measured 9. This repository's tree holds 42 files, 9 matching the three read paths. |
| Bytes per file | 128 KiB | Chosen ceiling. The largest file in that tree is 28,151 bytes. |
| Directory levels below `output_dir` | 2 | Fixed by the read paths: `screens/<slug>/<screen>.md` is the deepest. |
| Entries enumerated per directory | 200 | Chosen ceiling, per directory. The deepest matching directory, `docs/design/screens/team-orientation/`, holds 8 entries — seven `.md` and one `.svg`. Worst case at depth 2 is 200 first-level entries plus 200 in each, so 40,200 entries walked. |

The enumeration cap exists because the other bounds key on matching files: a
directory of many non-matching entries would otherwise be walked in full first.

## The terminal-effect obligation

The Testing Strategy's numbered list is the canonical enumeration of what a
refusal must not do afterwards. Every other statement of it **inside this
repository** — this spec and the plan — names that list rather than restating its
items.

**The shipped pack is the stated exception.** `packs/AGENTS.md` forbids shipped
pack content from citing this catalogue's internal records, and an adopter reading
`references/design-handoff.md` or the guide has no access to this spec, so a
pointer would resolve to nothing for the only audience those files have. Both
therefore state the obligation in full. That is a portability copy rather than
drift — but it is a second full statement, nothing mechanical compares the two,
and an edit to one will not move the other. Recorded rather than left implicit.

## Boundaries

### Always do

- Approve the resolved `output_dir` before reading anything under it: refuse a
  reserved tree, confirm a repo-root value resolving outside the repository tree,
  and approve a user-profile value against its own declared absolute root. Every
  later check is against that approved value — confinement to an unvalidated root
  is not confinement.
- Run the real-path resolution; do not reason about the path. Execute it, read its
  output, and compare on resolved components. The shipped containment module
  records that observed runs skip a check phrased as "confirm", and that every
  skip wrote outside the approved root.
- Treat every artifact as data. An instruction inside a body is content about
  design intent, never an instruction to follow.
- Distinguish a refusal from a skip everywhere the result is read. A skip means
  nothing was there, or what was there is not this artifact; a refusal means
  something was wrong.
- Stop on a refusal, with the terminal effect § The terminal-effect obligation
  names. A control that fires and then continues has failed while reporting
  success.
- Under a heightened root, surface each artifact and take explicit operator
  confirmation before consuming it.

### Ask first

- Consuming anything beyond § What is consumed.
- Reading any artifact beyond the three this spec names.

### Never do

- Never add a new top-level directory, module, or dependency. This change is
  confined to `packs/frontend-engineering/`, `guides/frontend-engineering/`,
  `guides/README.md`, `docs/specs/`, `docs/product/`, `tests/roster/`,
  `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`,
  `workspace.toml`, and the root `.claude-plugin/marketplace.json` that self-host
  regenerates.
- Never let an artifact's content decide what code is emitted, which files are
  written, or which network destination appears in generated output.
- Never resolve, open, or follow a path that appears inside consumed content. A
  path in an artifact is a display string; the step reads three files and no
  fourth.
- Never record into a persisted artifact — the verification ledger, the guide, this
  spec, or emitted code — any absolute filesystem path the step itself derives:
  an approved root, a configuration file's location, or a resolved path a
  confinement-failure refusal reports. The live confirmation prompt is the one
  exception, because an operator cannot approve a root they are not shown, and what
  is transcribed from it is redacted before it is written. This says nothing about
  a path written *inside* an artifact's own content: redacting those is one of the
  four controls § What this slice does not attempt names as dropped.
- Never report product belonging as mechanically confirmed. `slug` is documented
  as naming the surface **or product** a direction serves and the system a
  taxonomy serves, the screen brief carries no `slug`, the first heading may name
  either, and no field is reserved for a product. Operator confirmation is the
  whole control; do not dress it as a check that passed.
- Never add a product-identity frontmatter field or a migration for one here.
- Never change an `experience-design` writer template or skill. This slice reads
  what they produce.
- Never treat a missing or rejected confirmation as a skip, and never reach the
  canonical product-reference set after a refusal.
- Never ship a control with only a positive observation. Each control owes a
  recorded negative run or a named owner waiver.
- Never edit a lint, test, or checker to make a failing gate pass.

## Testing Strategy

Most controls here govern agent instruction prose, so they are not unit-testable
and no gate reads them. Those are verified by **visual / manual QA against staged
fixtures, paired**: one run where the control is not needed and one where it must
fire. A single benign run establishes only that the happy path works, and a single
observed refusal from a non-deterministic agent establishes that the control fired
once, so each observation states the fixture, the observed output, and which half
it is.

**One automated test carries what prose cannot.** Three review rounds each found
the spec asserting a fact about the design artifacts that the real corpus
contradicts. Hand-transcription is the mechanism, and a review round cannot fix a
transcription process. So a construction test reads every file under this
repository's `docs/design/` and asserts the contract in
`references/design-handoff.md` classifies each one as this spec requires. It
asserts nothing about agent behaviour.

**A negative observation proves the terminal effect, and only what output can
show.** Three properties an earlier draft asked for — that no content from the
rejected artifact was consumed, that earlier extractions were discarded, and that
no code derives from the read — are unobservable: the step must read a file to
test it, so those bytes are in context before any control can fire. Asking a run
to attest to them would be asking it to certify something it cannot see. Each
negative run instead records, from that run's own output, all five of:

1. the run refused, naming which control refused and why;
2. it did not repair or normalize the rejected value;
3. it did not substitute another slug, artifact, or output directory;
4. it did not downgrade the refusal to a skip; and
5. the mode halted in a named state the operator must resolve, rather than
   continuing to emit — neither from the handoff nor from the canonical
   product-reference set.

Item 5 is what distinguishes a stopped read from a continued one, and it is
observable. Any of the five left unobserved makes the run a partial observation.
Re-run it rather than recording it.

**The residual, stated because it is load-bearing.** A post-read refusal bounds
what is displayed, transcribed and emitted. It cannot unread the bytes. An adopter
who needs content never to enter the agent's context must enforce that outside the
agent.

A fixture re-staged after the instruction text changes is re-run against the final
text. A passing observation recorded against superseded instructions is evidence
about a control that no longer exists.

Criteria marked **(static)** below need no run. Every unmarked criterion is a
control criterion and owes the paired runs above.

## Acceptance Criteria

- [x] The `frontend-engineering` shared pre-flight — the step every one of its four
      modes runs — approves the resolved `output_dir` before reading under it:
      refusing a reserved tree outright, taking explicit confirmation for a
      repo-root value resolving outside the repository tree, and approving a
      user-profile value against its own declared absolute root. The reserved-tree
      test applies at every point the confinement predicate does — the approved
      root, each directory component as enumeration reaches it, and each resolved
      artifact path — so an approved root that merely *contains* a reserved tree
      cannot reach one through the slug, and a component resolving into a reserved
      tree is refused before its listing is surfaced or its depth counted.
- [x] The step executes a real-path resolution of each artifact it is about to
      read, reads that resolution's output, and compares it against the approved
      `output_dir` on resolved path components — equality or descendant, never a
      string prefix — surfacing the comparison result.
- [x] The step derives every displayed and recorded relative path for a consumed
      artifact from the resolution output that comparison consumed, not from the
      requested path.
- [x] The step binds `<slug>` to the slug the operator names for the surface being
      built, eliciting it when the request carries none, and resolves all three
      slots under that one slug.
- [x] The step treats a file under a read path whose frontmatter `type:` is absent,
      unparseable, or not that path's required literal as **not that artifact** —
      skipping it and continuing the scan — rather than as a refusal, so a design
      directory legitimately holding other artifact types cannot refuse the read.
- [x] The step consumes an artifact whose frontmatter omits a key its template
      declares, recording that key as absent. Only `type:` is required.
- [x] The step consumes, per artifact, the first `# ` heading, the frontmatter as
      found, and the body as one opaque block with HTML comments removed, keying on
      no section name.
- [x] Under a heightened root — user-profile-sourced or resolving outside the
      repository tree — the step surfaces each artifact to the operator before
      consuming it: the approved root, the configuration file it was read from, the
      artifact's `output_dir`-relative path, the configuration source token, its
      first heading, and its frontmatter; and takes explicit confirmation before
      consuming it.
- [x] The step treats a missing or refused confirmation, at either the approval
      step or an artifact, as a named refusal and does not consume that artifact.
- [x] The step enforces § The read bounds, evaluating them in this order: enumerate
      a directory up to its entry cap, resolving each entry as it is reached and
      checking it for depth; then the matching-file count; then per-file size. It
      surfaces which bound it exceeded rather than reading a partial set. When the
      entry cap truncates a directory before a later entry is reached, the cap is
      the bound reported.
- [x] The step applies the resolved-component confinement predicate at every
      directory component as it is reached during enumeration, not only to an
      artifact it is about to read. An entry whose resolution leaves the approved
      root — a symlinked `screens/<slug>/`, for instance — is a confinement-failure
      refusal at that point, before its listing is surfaced and before its depth is
      counted against the bound.
- [x] Every path the step surfaces or records names it relative to `output_dir`
      plus the configuration source token, except a confinement-failure refusal,
      which reports the resolved path so the operator can see where the read would
      have gone.
- [x] The step reads the three artifacts, when present, before consulting the
      canonical product-reference set in the shared pre-flight's named aesthetic
      reference step.
- [x] The step resolves each of the three artifacts independently and states the
      result for every combination. A slot with no conforming artifact is a named
      skip for that slot, and the canonical product-reference set fills that slot
      alone. When no `[design]` section resolves, or no slot has a conforming
      artifact, the step reports the directory-level skip rather than three
      per-slot skips. Any refusal stops the whole read, and the canonical set is not
      reachable for any slot.
- [x] The step records one named skip only after both branches of the resolution
      order have been tried — the repo-root `agentbundle-layout.toml` and, when that
      is absent or carries no `[design]` key, the user-profile one — and neither
      yields a `[design] output_dir`. It records a differently worded named skip
      when the section resolves but no slot has a conforming artifact.
- [x] The step treats every other dependency failure as a refusal, not a skip: a
      layout file that exists but cannot be parsed, a `[design]` section whose
      `output_dir` is missing, empty, or not a string, a file that passes the
      `type:` filter but cannot be read, and a canonicalization that raises —
      including the symlink-loop error class, which raises differently from an I/O
      failure.
- [x] The step states that each of its six refusals stops the handoff read with the
      terminal effect the Testing Strategy's numbered list states, and halts the
      mode in a named state rather than continuing to emit. The six, stated so that
      every refusal this spec can raise is an instance of one:
      **(a)** a reserved-tree hit at *any* resolved path — the approved root, a
      directory component reached during enumeration, or an artifact path;
      **(b)** a confinement failure at *any* resolved path the step reaches, artifact
      or directory component;
      **(c)** a non-conforming slug, or a run where no slug is obtainable;
      **(d)** a missing or refused confirmation, at the approval step or an artifact;
      **(e)** a breached bound; and
      **(f)** a dependency failure.
      Those six are the complete refusal set, and every criterion above uses these
      names.
- [x] The step carries consumed content to the code-emitting step as data with no
      instruction authority, and never resolves, opens, or follows a path appearing
      inside it.
- [x] **(static)** `references/design-handoff.md` reproduces § What is consumed and
      the read paths with their required `type:` literals, states that a `type:`
      mismatch means not-this-artifact and is skipped rather than refused, states
      that the step keys on no section name and discards HTML comments, states that
      a declared `type:` is a collision guard and not an authenticity claim, and
      names the frontmatter marker as the one validated for the screen brief.
- [x] **(static)** `references/design-handoff.md` resolves the `[design]` section by
      name and states no base path of its own.
- [x] **(static)** `references/design-handoff.md` states that nothing in the three
      artifacts discriminates the product they belong to, so operator confirmation
      is the control and belonging is never reported as mechanically confirmed; and
      carries the terminal-effect obligation in full, under the portability
      exception § The terminal-effect obligation records, so a reader can check it
      without access to this repository.
- [x] **(static)** `references/design-handoff.md` states the residual the Testing
      Strategy names: a refusal cannot unread bytes, and an adopter needing content
      never to enter the agent's context enforces that outside the agent.
- [x] **(static)** A construction test in `tests/roster/` reads every file under
      `docs/design/` and asserts the contract in `references/design-handoff.md`
      classifies each one into exactly one of four states — consumed, skipped as
      not-this-artifact, off every read path, or refused — failing when any file is
      mishandled, when the parsed contract is empty, when the corpus walk finds no
      files, or when the parsed contract does not carry exactly the three artifact
      rows with the read paths and `type:` literals § What is consumed fixes. That
      last floor is what holds the `token-taxonomy` row, which no file in the corpus
      exercises. It runs on pull requests through a `build-check.yml` step and a
      matching `tools/lint-ci-parity.py` disposition.
- [x] **(static)** Every enumeration of the shared pre-flight's steps inside
      `packs/frontend-engineering/` resolves after the insertion. The known sites
      are the skill's opening summary, the pre-flight's own step count, the
      `#### Steps 1–3. Proceed through the shared PLAN phase pre-flight` heading,
      and each mode's "run steps …" line in
      `.apm/skills/frontend-engineering/SKILL.md`; the pre-flight sequence in
      `JOURNEY.md`; the starter prompt and expected result in `pack.toml`; and
      `.apm/skills/token-architecture/SKILL.md`'s reference to the seed token block
      as a numbered step of this pre-flight. That list is the sites known at
      authoring time, not a closed set — the obligation is that every such
      enumeration in the pack resolves, and the implementer sweeps for step
      references rather than working the list alone.
- [x] **(static)** Every enumeration of the pre-flight's steps inside
      `guides/frontend-engineering/` resolves after the insertion:
      `reference/frontend-engineering.md`'s pre-flight list and
      `tutorials/scaffold-a-component.md`'s numbered walk.
- [x] **(static)** `guides/frontend-engineering/how-to/read-the-design-handoff.md`
      exists, states what is read, what is ignored, what each skip and each refusal
      means, that these controls are agent instructions with no gate behind them,
      and what an adopter who needs a guarantee must do instead. It also states what
      the slice does not inspect inside an artifact — content is consumed without
      normalization or redaction into code the adopter commits — because that is the
      larger of the two residuals and the no-gate sentence does not cover it. It is
      linked from `guides/frontend-engineering/README.md`.
- [x] **(static)** The guide lints the owning `guides/AGENTS.md` names all exit 0
      against the new page: `tools/validate_guides.py`, which checks frontmatter
      against `contracts/guide.schema.json`, and `tools/lint-guide-titles.py`, which
      checks `title` matches the body H1. `tools/lint-guidebook-steps.py` also exits
      0, but it is recorded as covering nothing here: it treats a page as a step
      only when the frontmatter carries `order:`, and no page under
      `guides/frontend-engineering/` does, so it reports OK with or without the new
      file. The first two are what red when the page is wrong.
- [x] **(static)** Each control criterion above — every criterion not marked
      **(static)** — has both a positive and a negative recorded run in the
      verification ledger, or a named owner waiver recorded in this spec. This
      criterion is marked static because it is an obligation over the other
      criteria, not a control of its own: a reader checks it by reading the ledger
      against the criteria list.

      **Owner waiver, eugenelim, 2026-09-18 — the heightened-root confirmation
      control and its refusal.** Those two criteria are implemented and readable in
      the step, but neither has a recorded paired run: staging a user-profile
      `output_dir` means writing a real layout file into the operator's own home
      configuration, which the fixture harness will not do. Every other control
      criterion has both halves recorded in the ledger. The waiver is named here
      rather than left as a silent gap, and the follow-on executable read path is
      where this case becomes testable without touching an operator's own
      configuration.
- [x] **(static)** No recorded observation in the verification ledger carries an
      absolute filesystem path — not the fixture root, and not a resolved path a
      confinement-failure refusal reported. The corpus-agreement test asserts this
      over the ledger, and reds when the ledger is absent, empty, or holds no
      recorded observation, so an assertion that scans nothing cannot read as a
      pass. A missed redaction fails a gate rather than shipping on an
      implementer's promise.
- [x] **(static)** `agentbundle catalogue verify --root .` exits 0.
- [x] **(static)** The `frontend-engineering` skill's eval surface carries a case
      covering the design-handoff read, as `packs/AGENTS.md` requires of every
      non-cosmetic pack update.
- [x] **(static)** The topmost `## [frontend-engineering][<version>] — YYYY-MM-DD`
      heading in `docs/product/changelog.md` names that pack's new `pack.toml`
      version, at the level directly beneath `[Unreleased]`.

## Follow-ons

- **The four controls this slice drops, and why they need a tool.** Review round
  four established that each is unstateable in prose at the precision it needs.
  A **code-point denylist** cannot converge by enumeration — four rounds added
  ranges and round four still named U+2028/29, U+00AD, U+034F, U+180E, the Hangul
  fillers, U+2800 and the variation selectors as gaps; the control has to be a
  permitted set plus normalization, which is a function, not a table.
  **Redaction** anchored on a value's prefix has no reach over a whole-file body,
  and the legitimate case it exists for — a serialization note naming a path — sits
  mid-body; it needs a scan over the value, which is a function.
  **Display bounds** made the confirmation weaker rather than stronger: every real
  artifact body exceeds 4 KiB — measured 2026-09-18 over the nine files on the
  three read paths, bodies run 5,736 to 15,231 bytes — so a 4 KiB bound would show
  the operator between 26.9% and 71.4% of what the emit step receives. Display and consumption have to be the same bytes, which
  means one code path produces both. And a **transcription predicate** comparing
  emitted strings against what the operator saw is a comparison, not a rule.
  The owner's decision of 2026-09-18 was to ship the read without them rather than
  specify them a fifth time. The follow-on is an executable read path —
  a script in the pack that resolves, approves, scans, filters, normalizes and
  returns a bounded result, with a unit test per control — after which these four
  become testable rather than asserted.

- **F3 writer hardening — the product discriminator.** Closing product belonging
  means adding a frontmatter field that names the product and a migration for
  every artifact already written without it. That is writer-side work in
  `experience-design`, and the `design-output-addressing` owner deferred it on
  2026-09-17 rather than inventing a rule under review pressure. This spec reads
  what that contract produces; it does not change the contract. Until the field
  exists, the read path takes operator confirmation. A discriminator is still
  needed even though all three H1s may carry a product name: an H1 is unvalidated
  free text with no declared form, so it can be read by a human and not matched by
  a machine, which is exactly the gap a reserved field would close.
- **F1 — the reserved-tree set is not closed.** The shipped containment module
  reserves `.apm/` for the repo-root branch and names `~/.claude/skills` as one
  example for the user-profile branch, without enumerating either set. This spec
  inherits that limit unchanged and does not close it.
- Pack maintainer: `packages/agentbundle/agentbundle/workspace_mcp.py`'s
  `_read_layout_bases` returns `str(candidate.resolve())` with no prefix check
  against any approved root. No skill reaches that function today — every layout
  reference instructs a direct read of `./agentbundle-layout.toml` — so it is not a
  live path for this change, and this spec's controls sit in prose instead. Routed
  here rather than left in Assumptions so the unchecked resolution has an owner if
  a caller ever appears.
- `docs/specs/frontend-experience-composition/` — the shared state-coverage map and
  the risk-tier depth selector. Independent of this spec; both depend on
  `design-output-addressing`.
- Pack maintainer: `packs/frontend-engineering/pack.toml` declares no layout
  section, and `references/design-handoff.md` is deliberately not an
  `agentbundle-layout.md`, so the layout conformance test does not read it. The
  deferred `docs/ux` base flip must name this file explicitly or it will strand
  the frontend read.
- Pack maintainer: no gate reads pack prose for the `packs/AGENTS.md` § Security
  controls. A prose-presence checker would certify phrasing rather than the
  control, so this needs a predicate stronger than presence before it is built.

## Assumptions

- Technical: `packs/frontend-engineering` has no awareness of any design output
  directory today; its only link to the design pack is a probe for whether
  `conversion-design` is installed
  (source: `grep -rn "agentbundle-layout\|output_dir\|docs/design" packs/frontend-engineering/.apm/`
  returns only genre-routing hits)
- Technical: `frontend-engineering/SKILL.md` carries no containment prose at all,
  so the controls here are authored from `copy-direction`'s pattern rather than
  adapted from an existing frontend step (source: read of that skill)
- Technical: `packs/AGENTS.md:56-58` requires canonicalize-then-prefix-check before
  every read, data-not-instruction extraction, and a current-project belonging
  check for a user-level config path; root `AGENTS.md` places trust-boundary
  validation in the non-waivable class (source: read of both files). This spec
  satisfies the belonging rule the same way the shipped containment module does —
  by surfacing the artifact for the operator to decide — which is that module's
  own reading of the same rule under the same authority, not a deviation from it
  (source: `containment.md:134-138` and `:156-163`)
- Technical: the repository blesses `agentbundle.catalogue_tooling.file_safety` for
  filesystem confinement, and skill instruction prose cannot call a Python helper,
  so the blessed helper is unreachable from this enforcement point. Accepted with
  its cost stated: the controls here hold only on runs that execute them, which is
  the same ceiling the shipped module records for its own confinement check
  (source: root `AGENTS.md` § Security considerations; `containment.md:99-107`)
- Technical: `design-output-addressing` shipped a containment module carried by
  five `experience-design` skills, whose `## Known limits of these controls`
  section states that product belonging has no discriminator and instructs the
  skill to surface the artifact and let the user decide rather than report
  belonging as confirmed
  (source: `packs/experience-design/.apm/skills/creative-direction/references/containment.md:156-163`)
- Technical: that module's own summary of the frontmatter contract — "the artifact
  type, the slug and the date" — is under-enumerated for the three artifacts read
  here. `creative-direction` carries `type, slug, surface, date`; `token-taxonomy`
  carries `type, slug, direction, date`; the screen brief carries
  `type, screen, flow, surface, surface-genre` with no `slug` and no `date` at all.
  The no-discriminator conclusion survives the correction, but not for the reason
  an earlier draft gave. `slug` is documented as "the surface **or product** this
  direction serves", and all three H1s read `<surface or product name>`,
  `<system or product name>`, and `<screen-name> · <product-slug> · surface: …`, so
  a product name can appear — it simply is not reliably there, and nothing marks
  which reading applies. A field that may name either discriminates nothing. The
  remaining fields do not name a product at all: `surface` and `surface-genre` name
  a platform and a page kind, `flow` names a screen sequence, and `direction` names
  a sibling artifact. § What is consumed carries the corrected sets and extracts
  the first heading for the operator to read
  (source: `creative-direction-template.md:2-7` and `:10`,
  `token-taxonomy-template.md:2-5` and `:8`, `screen-brief-template.md:22-30`,
  2026-09-18)
- Technical: the three artifacts' frontmatter `type:` literals are
  `creative-direction`, `screen-flow-brief`, and `token-taxonomy`. The screen brief
  additionally carries a body field `**Type:** screen-brief` that the
  structural-orphan lint reads instead of the frontmatter; the two literals differ,
  so naming which marker this step validates is sufficient to keep them apart
  (source: `screen-brief-template.md:23` and `:33-36`)
- Technical: the shipped containment module records that an agent given a
  traversal-bearing slug substituted a tidy slug of its own and completed the
  write, which is the repair-and-continue failure the terminal-effect criteria here
  are written against
  (source: same file, `## Slug validation`, `Refuse it; do not repair it`)
- Technical: `copy-direction/SKILL.md` approves the resolved `output_dir` before
  reading under it — a repo-root value must stay within the repository tree or take
  explicit confirmation — and is the only skill in either pack carrying that step
  (source: read of its step 1)
- Technical: no skill reaches `packages/agentbundle/agentbundle/workspace_mcp.py`;
  every layout reference instructs a direct read of `./agentbundle-layout.toml`,
  and `_read_layout_bases` returns `str(candidate.resolve())` with no prefix check,
  so skill prose is the only enforcement point
  (source: `workspace_mcp.py:1576-1619`; `tests/conformance/test_pack_layout_declared_section.py:5-7`)
- Technical: a user-profile `output_dir` must be an absolute path and is shared
  across every repository, so one vault can serve two products
  (source: `packs/experience-design/.apm/skills/copy-direction/references/agentbundle-layout.md`)
- Technical: § The read bounds is the one home for the bound values, their
  measurements and whether each was measured or chosen. This Assumption records
  only the probe's provenance: one walk of this repository's `docs/design/` on
  2026-09-18, re-run after a 2026-09-16 walk that read 41 files and the same 9
  matches. The numbers themselves live in that section and are not restated here
- Technical: `tools/check-guide-index.py` asserts only that every active pack has a
  direct link in `guides/README.md`; it cannot observe whether an individual page
  is reachable (source: read of that tool)
- Technical: this spec is large for the corpus, not typical of it. Measured
  2026-09-18 over the 471 specs under `docs/specs/` that carry criteria: 7,630
  criteria, mean 16.2, **median 13**. This spec carries 32, about 2.5× the median.
  Recorded rather than smoothed over, because five review rounds is what a spec
  this size costs and a reader deciding whether to split the next one should see
  the real number (source: probe over `docs/specs/*/spec.md`, 2026-09-18)
- Process: every non-cosmetic pack-content change bumps matching versions and
  updates that pack's eval harness (source: `packs/AGENTS.md`)
- Process: each phase ships its guide with the capability
  (source: `.claude/skills/new-rfc/SKILL.md:274`; the `docs/CONVENTIONS.md`
  citation two sibling specs copy no longer resolves — that file was retired)
- Product: this spec is separated from the addressing work because it is the only
  new trust boundary in it and warrants its own review surface
  (source: user confirmation 2026-09-16)
