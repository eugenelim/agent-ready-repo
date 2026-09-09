# Verification ledger — Agent Skill Engineering Composition Fixtures

Observations produced by execution. The spec and plan are pinned at approval;
this file is where anything measured during the build is recorded.

## Base

- **Base commit:** `d44484b29d1ba0f56cb0baf42fd79b1348e26a58`. Every "before this
  slice" comparison set — AC3's declared-case set, AC5's marker set, AC8's
  payload digests, AC12's inherited records, AC22's milestone string — is read
  from this commit with `git show d44484b29:<path>`.
- **Base freshness:** `check-base-freshness.py` returned
  `{"status": "ok", "message": "head is current", "target": "origin/main"}` on
  2026-09-09, before the first edit. The branch tip and `origin/main` were the
  same commit, so the base commit above is also the merge-base.
- **Base milestone,** recorded because AC22 compares against it:
  `M3 · slice 4 consumer integrations shipped; 3c and 3e are unblocked and
  parallel, 3d needs 3c, 5 needs 3c, 6 closes — see the brief's slice table`

## T1 — lifecycle roll

Completed 2026-09-09 in one commit. Evidence, in the order the task names it:

- **Registration moved, not appended.** `workspace_status.py explain` reports
  this spec in `collection=work.active` with `findings=[]`. Neither
  `duplicate_membership` nor `impossible_transition` is emitted for it. The
  `.queue` entry is gone rather than duplicated — the defect the round-3 review
  caught in the task's original wording.
- **AC22, all three conditions, measured against the base commit.** The
  milestone differs from `git show d44484b29:workspace.toml`: `True`. It
  contains "in flight": `True`. It no longer offers 3e as unblocked or parallel:
  `True`. New string: `M3 · slice 3e composition behavior fixtures in flight;
  slice 4 consumer integrations shipped; 3c unblocked, 3d needs 3c, 5 needs 3c,
  6 closes — see the brief's slice table`.
- **Brief Spec-map row (AC24), confirmed by reading.**
  `lint-brief-coverage.py --root .` exits 0 and resolves the row as
  `agent-skill-engineering-composition-fixtures: Implementing`. Exit 0 is not
  the evidence — the lint exits 0 on an unresolved back-link too — the resolved
  line is.
- **Brief prose reconciled.** The *Not yet started* paragraph no longer asserts
  that 3e has no spec, plan, or workspace entry; 3e moved to a new *In flight*
  paragraph and the remaining list reads "3c, 3d, 5 and 6".
- **Roster gates.** `tests/roster/test_workspace_status_projection.py` and
  `tests/roster/test_status_projection_and_context_exclusion.py`: 104 passed,
  12 subtests passed, 27.49s.
- **Status pair.** `spec.md` `Implementing`, `plan.md` `Executing`, both in the
  same commit as the registration move and the milestone rewrite.

## T2 — declare, pin, grade, reconcile

Completed 2026-09-09. Observation identifier `2026-09-09-composition-fixtures-r1`.

### Round attestation (AC11)

The responses were generated in this round, not copied. Each case ran in its own
isolated context that held no material from the authoring context: the executor
received the shipped `SKILL.md`, the skill's own `references/` tree, and the
prompt with its payload. Withheld from every executor: the assertion list, the
pattern identifiers, the seeded-defect naming, and the expected output. Grading
ran in a further separate context that received the captured transcripts and the
assertion lists but authored none of them. Neither freshness nor separation is
decidable from tree bytes, which is why both are attested here rather than
gated.

### Two discarded rounds, and why

Two earlier rounds were run and discarded rather than recorded. Both were
instrument failures, and recording either would have written false findings into
a shipped fixture.

1. **Executor mismatch.** The first round used a different agent runtime from
   the one that produced the recorded baseline. Five of eight inherited verdicts
   "regressed" against a byte-identical skill body — the swap, not the pack.
   Responses ran 260 bytes to 1.4 KB.
2. **Suppressed progressive disclosure.** The second round used the matched
   runtime but instructed the executor to read only `SKILL.md` and the prompt.
   `author-or-update-agent-skill` routes to eleven `references/` files, so this
   prevented the skill from executing its own contract; three responses said so
   outright. Responses ran 3.7–7.0 KB.

The recorded round allows the skill's own `references/` tree and still withholds
the evaluation material. Responses run 4.8–9.6 KB and six of eight inherited
verdicts match the baseline exactly.

The general lesson, recorded because it cost two rounds: the comparison was
verified carefully each time and the instrument was not.

### Inherited verdicts that moved (AC12)

| Case | Recorded | Measured | Reading |
| --- | --- | --- | --- |
| `cross-session-resumption` | `[T,F,T,T]` | `[F,F,T,T]` | index 0 newly false; the response stayed in `frame` and declined to name `update` without a resolved root |
| `node-browser-suite` | `[T,T,T,T]` | `[F,T,T,T]` | index 0 newly false; see the provider note below |

Six of eight are unchanged. `progressive-result-presentation[2]` is false again,
matching the baseline — it passed in the second discarded round, which was
itself instrument noise, so its inherited exemption stands rather than being
deleted.

### Corrected predeclaration, under owner authority (Never do)

- **Case:** `cross-session-resumption`
- **Field:** `expect.output_contains`
- **Declared:** `["Mode: frame", "Write status: awaiting explicit authorization"]`
- **Measured:** the response emitted `Write status: not authorized`
- **Prior recorded observation:** the baseline observed the declared pair
- **Ground:** the measurement is the better reading. The skill body is
  byte-identical to the baseline, so the marker was situational rather than
  fixed and the declaration was over-specified.
- **Authority:** repository owner, 2026-09-09, after being shown the
  declaration, the baseline record, and the transcript line.
- **Correction:** the declared pair is now
  `["Mode: frame", "Write status: not authorized"]`.

This was surfaced rather than repaired because AC9 requires every declared
marker to occur in its own transcript, and the marker check refused the record
write before anything was persisted.

### Exemptions (AC14, AC15)

Two inherited, still failing, retained:

| Case | Assertion | Basis |
| --- | --- | --- |
| `cross-session-resumption` | Adds a durable record a later session can read to resume | Inherited; the case asks for durability while its sibling assertion requires the read-only boundary preserved |
| `progressive-result-presentation` | Pairs each incomplete state with the next action it hands the user | Inherited; measured false again this round |

Three added, each measured false this round and each authorised by the
repository owner on 2026-09-09 after being shown the assertion, the transcript,
and the reading:

| Case | Assertion | Prior | Measured | Reading |
| --- | --- | --- | --- | --- |
| `cross-session-resumption` | Names update as the mode the work will need, against the named existing skill root, without entering it before authorization | true | false | The response stayed in `frame` and refused to name a mode without a resolved root — arguably better than the assertion asks, but it does not satisfy it |
| `node-browser-suite` | Frames worker sizing against memory and browser cost, not CPU count alone | true | false | Rejects CPU-derived worker counts, but on determinism grounds rather than resource cost |
| `hook-plugin-design` | Names the undisclosed shared dependency as something a consumer must see before install | new | false | Identifies the HTTP-client coupling and its cost, but never says a consumer must see it before installing |

**Provider note on `node-browser-suite`.** The response emitted the declared
diagnostic `knowledge provider unavailable` and declined Node-specific guidance.
This was investigated before the exemption was sought. The provider is a
separate installed skill whose own description states it is invoked only through
an explicit capability call, and the workflow's step 3 says to detect it only
through exposed capability metadata — so its absence is the contract's normal
degraded path, not a suppression by this harness. The assertion also remains
reachable on the portable floor: the corpus sentence is "Browser workers consume
real browser and setup resources; select their count from the workload rather
than CPU count alone", and the response made the second half of that point
without the first. Recorded as a genuine miss.

### Seeded-defect verdicts (AC13)

| Case | Named assertion | Verdict |
| --- | --- | --- |
| `subagent-composition` | Identifies unassigned write ownership as unsafe once workers run in parallel | true |
| `hook-plugin-design` | States that a post-action hook cannot stop the action it observed | true |

Both payloads measure the floors they name. `subagent-composition` scored 5/5
and called the shared-tally clause "a genuine lost-update race … this clause
must be deleted outright, not repaired". `hook-plugin-design` scored 4/5 and
identified the post-publication hook's stated-outcome contradiction.

### Assertion grounding, per new assertion (AC7)

Each assertion either new case declares tests a requirement its declared floor
states. Read at review on 2026-09-09; no assertion is satisfiable by a generic
response that does not meet the underlying requirement.

`subagent-composition`, against `skills-and-subagents-common-floor`:

| Assertion | Floor requirement it tests |
| --- | --- |
| Unassigned write ownership unsafe in parallel | "Assign explicit ownership before any parallel write"; failure mode "Parallel writes without assigned ownership corrupt each other" |
| Caller context per worker is a decision | "Which skill knowledge must the delegated agent receive"; failure mode "Passing the whole caller context defeats the isolation that motivated delegating" |
| Concurrency bound set by the parent | "Cap concurrency"; "What concurrency cap, token budget, waiting behavior … apply?" |
| Parent keeps synthesis | "Keep final synthesis and authority in the parent loop"; failure mode "Treating a delegate's result as authority moves the decision away from the loop accountable for it" |
| Structured result and visible partial failure | "Require a structured result rather than free prose"; "a partial failure is visible rather than silently absorbed" |

`hook-plugin-design`, against `hooks-common-floor` and
`plugin-package-common-floor`:

| Assertion | Floor requirement it tests |
| --- | --- |
| Post-action hook cannot stop what it observed | "Putting a decision in a post-action hook cannot undo the action it observed" |
| Repository policy file is untrusted input | "Interpreting an untrusted repository file as hook instructions executes attacker-chosen code" |
| Component cohesion | "Component cohesion: do these components belong together for a reason a user would recognize?" |
| Dependency disclosure before install | "Dependency disclosure: what does it pull in, and is that visible before install?" |
| Shared prefix is a namespace collision | "Namespace collision: what happens when two packages claim the same name?"; failure mode "Silent namespace collision shadows a user's own component" |

### Per-verdict transcript readings (AC10)

The grading context returned a per-assertion verdict for every case with a
one-sentence reading wherever it judged false or close. Those readings are
reproduced in the exemption tables above and in the moved-verdict table; every
other verdict was judged true against its transcript with no qualification.
Each verdict rests on the transcript retained at
`notes/transcripts/<case-id>.md`, whose digest the record carries and whose
bytes the guard recomputes.

### Payload-defect readings (AC5, advisory)

Read at review on 2026-09-09. Both payloads carry the defect their declaration
names, in prose a reader recognises without the assertion in hand:
`subagent-composition-SKILL.md` has ~200 workers patching their own manifests
while all of them also update one shared tally, and takes the last worker's
summary as the result; `hook-plugin-design-SKILL.md` fires its hook after
publication while claiming it stops the release, and reads a repository-root
policy file as instructions. The two are not variants of one draft — different
domains, different floors, no shared prose.

### Bare-identity reading (AC17, advisory)

Read at review on 2026-09-09 over the two payloads, the two declarations, the
ten transcripts, and the rewritten records. No personal name, account
identifier, private service name, credential, or session metadata appears. The
structural scans cannot decide this class, which is why it is a recorded read.

### Mutation proofs

Every guard this slice adds or widens was proved able to fail. Each mutation was
restored by editing, never by checkout, and each file confirmed byte-identical
afterwards.

| Invariant | Mutation | Guard that reddened |
| --- | --- | --- |
| `AUTHORING_EVAL_IDS` scopes the digest sweep | Remove `hook-plugin-design` | `test_the_authoring_eval_id_set_covers_every_declared_case` |
| Declared-case set equals base plus two | Remove both new ids from the equality | `test_authoring_behavior_evals_cover_frame_and_existing_update` |
| `AUTHOR_EVIDENCE_SOURCES` covers every pinned source | Remove the hook/plugin payload | `test_independent_behavior_results_cover_both_authoring_cases` |
| A verdict is readable against its transcript | Forge a `captured_response_sha256` | `test_every_verdict_is_readable_against_its_own_transcript` |
| One transcript per record | Point two records at one transcript | `test_authoring_transcripts_are_one_per_record` |
| One observation identifier per round | Give one record a different identifier | `test_every_authoring_record_belongs_to_one_round` |
| A seeded-defect miss is exempted or fails | Flip `subagent-composition`'s seeded-defect verdict to false | `test_the_seeded_defect_assertion_is_true_or_exempted` and the exemption guard |

**A guard that could not fail, found and repaired.** The seeded-defect guard was
first written as `assert verdict or (case_id, named) in _known_miss_pairs()`,
calling a helper that did not exist. Both verdicts were true, `or`
short-circuited, and the test passed green while referencing an undefined name —
it could not fail in the only direction that mattered. It now parses the
exemption set from the module and asserts that set is non-empty before using it.
Recorded because the slice's whole subject is controls that cannot fail, and
this one was written in the middle of it.

**A mutation that did not land.** The first attempt at the seeded-defect proof
replaced a 40-character JSON substring that occurs earlier in the file, so it
flipped `frame-new-skill`'s first verdict instead and the guard correctly stayed
green. Retargeted by byte offset within the intended record. A mutation proof
that does not mutate the intended subject proves nothing.

### Scans

- Export-boundary pytest scan and the pack host-identity scan: both pass over
  the payloads, declarations, and records.
- The committed portability grep from `packs/AGENTS.local.md`, run over the two
  payloads: clean. It is the only one of the two portability controls that
  matches a bare `RFC-NNNN` or `ADR-NNNN`.
- Structural host-identity patterns over the retained transcripts and the
  records: clean.

### Suite state

`packs/agent-skill-engineering/tests`: 242 passed.


## T3 — publish and close

Completed 2026-09-09.

### Published surfaces

- **Manifests.** `pack.toml` and `.claude-plugin/plugin.json` both at `0.4.2`,
  one patch above the `0.4.1` they carried at the base commit.
- **Aggregate (AC24).** `FORCE=1 make build-self` propagated the bump to
  `.claude-plugin/marketplace.json` as a single-line change. A second run left
  the file unchanged, which is the check: regeneration-is-a-no-op, since the
  generator writes its target in place and leaves no separate artifact to
  compare against.
- **Changelog (AC25).** Topmost free-standing `##` entry for the pack.
  `Highlights` disposition decided in the same step and recorded in the entry:
  no `### Highlights` section, because the release changes the pack's
  evaluation evidence and not what a consumer can do — no skill body,
  reference, mode, corpus topic, or provider contract moved.
- **Architecture (AC20).** All four RFC-required fields recorded: implemented
  names, their paths, the dependency edge on the composition-floors slice, and
  the verification evidence. Document remains `PLANNED` and states that the
  Gate 2 verdict belongs to closeout.
- **Spec index (AC26).** Row added: mixed shape, 27 ACs / 3 tasks.
- **Pack README.** Read and left unchanged: it makes no fixture-inventory or
  evaluation-coverage claim, so there was no stale sentence to reconcile.

### AC19 — the measure's own list

Compared the recorded result ids against the eleven the M2 expanded measure
names, transcribed from RFC-0097 § *Experiment / validation*, Gate 2 rather than
read back out of the fixture: the four foundation cases plus pytest suite,
Node/browser suite, subagent composition, hook/plugin design, cold-start
workspace orientation, cross-session resumption, and progressive result
presentation. None missing. One extra record,
`knowledge-provider-read-only-entry`, which the measure does not name and which
the criterion permits.

### Review reads

- **AC15, exemption authorities.** All five entries in the exemption set resolve
  to a ledger record carrying case, assertion text, prior verdict, measured
  verdict, authority and date. Verified by parsing the set out of the guard and
  matching each pair against this file.
- **AC20, architecture fields.** Read at close; all four present, `PLANNED`
  retained, no gate verdict claimed.

An earlier automated check of the authority phrase reported a gap that was not
one: the phrase spans a line wrap, so the substring search missed it. Re-checked
against whitespace-normalised text. Recorded because a false gap and a real one
look identical in a grep result.

### AC22 — brief digest re-pinned

The registration pinned `sha256-bytes-v1:87f73f2f…`, the brief's digest when T1
wrote the entry. T1 also edited the brief — adding the Spec-map row and
correcting the *Not yet started* paragraph — so the brief moved to
`sha256-bytes-v1:c5e26fcf…` and the pin went stale within the slice. Re-pinned
at close against a freshly computed digest. This is why AC22 requires the
comparison at close rather than at registration.

No other registration was touched. `brief_queue.executing` pins RFC-0097 rather
than the brief, and the shipped siblings' older pins are the pre-existing drift
the Follow-on records.

### Close

Spec `Shipped`, plan `Done`, all 27 criteria ticked, registration moved from
`["ini-009".work].active` to `.shipped`, brief Spec-map row rolled to `Shipped`,
the in-flight paragraph removed, and the initiative milestone rolled so it no
longer advertises 3e as in flight.

### Gates

| Gate | Result |
| --- | --- |
| `packs/agent-skill-engineering/tests` | 242 passed |
| `tests/roster` projection suites | 104 passed, 12 subtests |
| `lint-spec-status.py --root .` | exit 0, spec metadata clean |
| `lint-brief-coverage.py --root .` | exit 0, row resolves as `Shipped` |
| `agentbundle catalogue lint --root . --deep` | exit 0 |
| `agentbundle catalogue verify --root .` | exit 0 |
| Workspace projection | no finding for this spec; no `impossible_transition`, no `duplicate_membership` |

## Observed gate failures

None. Two pre-existing warn-only spec-status warnings on unrelated specs were
present before this slice and are unchanged by it.

