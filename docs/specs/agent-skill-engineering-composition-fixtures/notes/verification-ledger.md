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

| Case | Assertion | Prior | Measured | Basis |
| --- | --- | --- | --- | --- |
| `cross-session-resumption` | Adds a durable record a later session can read to resume | false | false | Inherited; the case asks for durability while its sibling assertion requires the read-only boundary preserved. Originating record: `docs/specs/agent-skill-engineering-corpus/qa.md`, which records the measurement decision but carries no owner-authority field or date. Authority for retaining it: the repository owner, 2026-09-09, given after being shown that the originating record documents the miss without an authority field. |
| `progressive-result-presentation` | Pairs each incomplete state with the next action it hands the user | false | false | Inherited; measured false again this round, and the one verdict two readings contest. Originating record and authority: `docs/specs/agent-skill-engineering-languages-and-execution/qa.md` § "Known-miss exemption — authority recorded", the repository owner in session, 2026-08-31. |

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

One reading per recorded verdict, produced by a grading context reading each
transcript fresh and without sight of the earlier round's verdicts. Forty-two
verdicts, forty-two readings. An earlier version of this section recorded only
the five readings where the grader had qualified itself and substituted a
blanket sentence for the rest; AC10 asks for a reading per verdict, so the
blanket sentence was not evidence and the remaining readings were obtained.

**`frame-new-skill`**

| # | Verdict | Reading |
| --- | --- | --- |
| 0 | true | The response opens with “Read-only” and closes with “Mode: frame” and “Write status: not authorized.” |
| 1 | true | The “Activation boundary” supplies five realistic prompts each under both “Should activate” and “Should not activate.” |
| 2 | true | Activation is defined separately from the “Boundaries” authority table and the later “Non-goals” section. |
| 3 | true | The response proposes a SKILL.md-plus-references tree while stating “No files created” and “Files changed: none.” |

**`update-existing-skill`**

| # | Verdict | Reading |
| --- | --- | --- |
| 0 | true | The “Current contract inventory” catalogs the existing name, activation boundary, outcome, input, non-goals, authority, structure, and portability floor. |
| 1 | true | The response retains pre-execution migration review and says options A, B, and D leave `filesystem_read_untrusted` unchanged while B only narrows activation. |
| 2 | true | The A–E candidate list identifies each possible edit and its authority implications while explicitly refusing to infer which unspecified change the user wants. |
| 3 | true | The response requires “Explicit write authorization” and then names frontmatter, boundary, activation, retained-behavior, and link verification. |

**`cold-start-orientation`**

| # | Verdict | Reading |
| --- | --- | --- |
| 0 | true | The response begins with “Mode: frame” and “Write status: not authorized.” |
| 1 | true | The observable outcome and portability sections name repository identity documentation, effective scoped instructions, verification and commit conventions, VCS state, request paths, and the architecture entry point as orientation inputs. |
| 2 | true | The response states the stopping point as “orientation complete, no files changed; say what to build” and lists planning or performing the later change as a non-goal. |
| 3 | true | It repeatedly states the orientation is read-only and concludes “No files were created or changed.” |

**`cross-session-resumption`**

| # | Verdict | Reading |
| --- | --- | --- |
| 0 | false | The response remains in “Mode: frame” and discusses a future mode transition but never explicitly names `update` as the required eventual mode against a confirmed existing skill root. |
| 1 | false | It only proposes possible handoff or checkpoint designs and explicitly reports “Files changed: none,” so no durable resumption record is added. |
| 2 | true | The response inventories the existing activation, outcome, authority, and non-goals, says any design must account for all four, and plans verification that “the review contract still holds.” |
| 3 | true | It states that nothing will be written until authorization and asks for explicit confirmation before any mutation, especially the write-capable option 4. |

**`progressive-result-presentation`**

| # | Verdict | Reading |
| --- | --- | --- |
| 0 | true | The response identifies itself as read-only framing and closes with “Mode: frame” and “Write status: not authorized.” |
| 1 | true | The completion-state vocabulary explicitly names `complete / partial / blocked / not started`. |
| 2 | false **(contested — see below)** | It requires every incomplete receipt to carry exactly one next action with its precondition, and the evidence section applies that rule to partial, blocked, and interrupted outcomes. |
| 3 | true | It forbids silently narrowing scope to manufacture `complete` and requires unavailable progress information to be reported as `partial` rather than `complete`. |

**`knowledge-provider-read-only-entry`**

| # | Verdict | Reading |
| --- | --- | --- |
| 0 | true | The response explicitly begins “Mode: knowledge-provider.” |
| 1 | true | It designs the root index, decision-oriented child indexes, leaves, routing, provenance, and retrieval evaluation while stating that nothing was written. |
| 2 | true | The security section says “Entry is read-only” and that the mode gains no write authority merely through entry or time spent in it. |
| 3 | true | The closing paragraph says answering the root question does not authorize writing and that file creation needs separate explicit authorization immediately before the write. |

**`pytest-suite`**

| # | Verdict | Reading |
| --- | --- | --- |
| 0 | true | The bare-import passage treats unique module identity as necessary to prevent full-corpus runs from silently testing another skill’s cached module, making it a correctness contract rather than style. |
| 1 | true | The cleanup passage specifies per-test `tmp_path`, notes that end-of-session cleanup can be skipped by interruption or process death, and places scratch directories outside the repository tree. |
| 2 | true | The shared-fixture passage calls shared mutable state a defect because parallel workers race and serial order can alter the verdict. |
| 3 | true | The response explicitly trades fixture scope and process cost against assurance by allowing expensive fixtures the widest scope their assertions permit and preferring function calls over interpreter spawning. |

**`node-browser-suite`**

| # | Verdict | Reading |
| --- | --- | --- |
| 0 | false | The worker section rejects CPU count as the sole concurrency input but never frames worker sizing against memory consumption or per-browser cost. |
| 1 | true | The install section requires preinstalled, version-checked dependencies and explains that installing during tests can resolve a different dependency set and mutate the lockfile. |
| 2 | true | The shared-state section calls a reused profile directory a correctness defect and names cookies, localStorage, service workers, cache, and locking as cross-worker contamination. |
| 3 | true | The language-extension section confines runner APIs, worker models, Node versions, and browser-driver details to the unevidenced `typescript-node` ecosystem rather than promoting them to the portable floor. |

**`subagent-composition`**

| # | Verdict | Reading |
| --- | --- | --- |
| 0 | true | The response identifies 200 concurrent writers and a shared-summary lost-update race, then assigns all writes to the parent. |
| 1 | true | It rejects automatic full-conversation inheritance and instead defines a deliberately scoped, self-contained worker brief containing only the necessary root, fields, rules, schema, and trust statement. |
| 2 | true | Under “Bound the concurrency,” it makes the parent fix a batch width and dispatch workers in waves instead of deriving fan-out from all roughly 200 catalogue entries. |
| 3 | true | The response says the parent aggregates all worker returns and that this aggregate—not the last worker’s summary—is the audit result. |
| 4 | true | It requires a uniform return schema with `complete / partial / failed` and mandates that missing, failed, or interrupted units remain named and counted in the aggregate. |

**`hook-plugin-design`**

| # | Verdict | Reading |
| --- | --- | --- |
| 0 | true | The response states that a hook firing after publication cannot prevent publication and can only report on an artifact already released. |
| 1 | true | It explicitly treats `.release-guard/policy.md` as untrusted data whose embedded directives cannot widen authority or become instructions. |
| 2 | true | The response observes that the hook, linter, formatter, and Slack digest have no common trigger and recommends separating their distinct outcomes. |
| 3 | false | Although it exposes the HTTP-client coupling and notes that installing the guard also installs a network surface, it never explicitly requires that dependency to be disclosed to consumers before installation. |
| 4 | true | It says matching the team’s existing `release` prefix deliberately creates ambiguous resolution between installed and local commands. |

#### One contested verdict, resolved conservatively

`progressive-result-presentation[2]` — "Pairs each incomplete state with the
next action it hands the user" — is the one assertion on which two independent
readings of the same transcript disagree.

- The grading round read it **false**: the response requires one next action in
  general but never pairs `not started` or `interruption` with a concrete
  handed-off action.
- The readings pass read it **true**: the response requires every incomplete
  receipt to carry exactly one next action with its precondition, and applies
  that to partial, blocked and interrupted outcomes.

Both are defensible against the transcript, which enumerates four states and
mandates one next action per receipt without pairing state to action
individually. The same assertion also passed in the second discarded round, so
three readings have produced two verdicts.

The recorded verdict stays **false** and the inherited exemption stays. A
contested verdict resolves to the recorded miss rather than to the reading that
would let an exemption be deleted: choosing the other way would remove a
standing exemption on the strength of a judgement call with no principled
tie-break, which is how a green tree gets bought.

The underlying defect is in the assertion, not in the workflow's behaviour: it
does not say whether a universal rule over receipts satisfies "each incomplete
state", so two careful readers reach opposite answers. It is an inherited
declaration this slice does not own. Sharpening it belongs to whoever owns that
case; it is raised in this slice's pull request rather than recorded as a
durable follow-on, per the work-loop's disposition rule for excluded work.

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

Every guard this slice adds or widens is listed below and each was proved able
to fail. Two earlier versions of this table did not support that sentence: the
AC8 distinctness guard and the AC3 declared-case guard had no killing mutation
of their own, and the AC8 row proved two other guards instead. Both now have
one. Each mutation was restored by editing, never by checkout, and each file
confirmed byte-identical afterwards.

| Invariant | Mutation | Guard that reddened | Assertion message |
| --- | --- | --- | --- |
| `AUTHORING_EVAL_IDS` scopes the digest sweep | Remove `hook-plugin-design` | `test_the_authoring_eval_id_set_covers_every_declared_case` | `AUTHORING_EVAL_IDS is [...] against declared [...]. Narrowing this set removes a graded result from the digest sweep` |
| Declared-case set equals base plus two | Remove both new ids from the equality | `test_authoring_behavior_evals_cover_frame_and_existing_update` | set-equality mismatch on the declared id set |
| `AUTHOR_EVIDENCE_SOURCES` covers every pinned source | Remove the hook/plugin payload | `test_independent_behavior_results_cover_both_authoring_cases` | `set(result["source_files"]) <= set(AUTHOR_EVIDENCE_SOURCES)` |
| Required declaration fields are non-empty (AC1) | Empty `hook-plugin-design`'s `prompt` | `test_composition_cases_declare_a_complete_field_set` | `AssertionError: ('hook-plugin-design', 'prompt')` |
| Each new case names its own payload (AC2) | Point a new case at an inherited payload | `test_each_composition_case_names_its_own_payload` | `AssertionError: ('hook-plugin-design', 'evals/files/pytest-suite-SKILL.md')` |
| Per-case pattern list is exact (AC4) | Swap in an unrelated admitted topic | `test_composition_case_declares_its_exact_pattern_list` | declared list not equal to the fixed per-case list |
| Marker set equals the sibling's base set (AC5) | Declare `Mode: knowledge-provider` on a framing case | `test_composition_cases_reuse_the_sibling_marker_set` | `AssertionError: subagent-composition` |
| Seeded-defect text belongs to its own case (AC6) | Name a text the case does not declare | `test_each_composition_case_names_a_distinct_seeded_defect_assertion` | `AssertionError: ('hook-plugin-design', 'Not one of its assertions')` |
| A verdict is readable against its transcript (AC9) | Forge a `captured_response_sha256` | `test_every_verdict_is_readable_against_its_own_transcript` | digest mismatch on the recomputed transcript |
| One transcript per record (AC9) | Point two records at one transcript | `test_authoring_transcripts_are_one_per_record` | resolved-target collision |
| Records belong to the declared round (AC11) | Rewrite every record's `observation_id`, leaving `graded_run` declaring the true round | `test_every_authoring_record_belongs_to_one_round` | `AssertionError: (['forged-round'], '2026-09-09-composition-fixtures-r1')` |
| Payload binding survives a swap (AC8) | Exchange the two cases' declared `files` | `test_independent_behavior_results_cover_both_authoring_cases` and `test_authoring_behavior_evidence_matches_its_source_digest` | recorded `source_files` no longer match the declared files |
| Result-id set admits exactly the widened set (AC12) | Drop `hook-plugin-design` from the recorded results | `test_independent_behavior_results_cover_both_authoring_cases` | set-equality mismatch on the recorded result ids |
| No record is hidden by a duplicate id (AC9, AC11) | Append a second copy of the `pytest-suite` record | `test_every_verdict_is_readable_against_its_own_transcript` and `test_independent_behavior_results_cover_both_authoring_cases` | `AssertionError: ['pytest-suite']` |
| The base is the one the ledger records (AC3, AC5, AC8) | Bump `BASE_COMMIT` without changing the ledger's recorded base | `test_the_base_commit_matches_the_one_the_ledger_records` | `AssertionError: BASE_COMMIT is 96d3d08e5... but the ledger records d44484b29...` |
| Retained transcripts are host-clean (AC17) | Add `/Users/someone/checkout/notes.md` to a retained transcript | `test_recorded_evidence_fields_carry_no_host_identifying_data` | host-identity pattern match in the transcripts root |
| The transcript scan root is not repointed (AC17) | Point the retained-transcript root at a directory that does not exist | `test_recorded_evidence_fields_carry_no_host_identifying_data` | `AssertionError: ('retained transcripts', 0)` |
| Payloads are distinct drafts (AC8) | Overwrite one payload with the other's bytes | `test_composition_payloads_are_distinct_non_empty_drafts` | `AssertionError: ('hook-plugin-design', 'subagent-composition')` |
| Declared-case set equals base plus two (AC3) | Drop an inherited case from the declarations | `test_the_declared_case_set_gains_exactly_the_two_new_ids` | set-equality mismatch against the base-derived set |
| Transcripts stay inside the scrub root (AC9, AC17) | Copy a transcript beside `spec.md` and repoint its record | `test_every_verdict_is_readable_against_its_own_transcript` | `AssertionError: ('pytest-suite', 'escaped-transcript.md', 'transcripts must live under notes/transcripts/')` |
| The scan root is the real transcript directory (AC17) | Repoint the root at a sibling directory that also holds ten Markdown files | `test_recorded_evidence_fields_carry_no_host_identifying_data` | root does not equal its independently written expected location |
| Seeded-defect verdict is true or exempted (AC13) | Flip `subagent-composition`'s seeded-defect verdict to false | `test_the_seeded_defect_assertion_is_true_or_exempted` and the exemption guard | unexempted false verdict |

**Two mutations that first appeared to prove the guard sound, and did not.**
Both were defects in the mutation, not the guard, and both are recorded because
a mis-aimed mutation looks exactly like a passing proof.

- The payload-swap mutation was first run against the distinctness guard alone,
  which stayed green — correctly, since a swap leaves both payloads non-empty
  and distinct. Re-run across the suite, it reddens two other guards through the
  recorded `source_files`. The proof was aimed at a guard that does not own the
  property.
- The round-identity mutation first replaced every occurrence of the identifier
  in the file, which moved `graded_run.observation_id` along with the records, so
  they still agreed. Isolating the mutation to the records reddens it.

An earlier mutation in this slice had the same shape: a forty-character JSON
substring matched an earlier record, so it flipped the wrong case's verdict and
the guard correctly stayed green.

**A guard that could not fail, found and repaired.** The seeded-defect guard was
first written as `assert verdict or (case_id, named) in _known_miss_pairs()`,
calling a helper that did not exist; both verdicts were true, `or`
short-circuited, and the test passed while referencing an undefined name.

**A second dead control behind the first repair.** The replacement helper parsed
the exemption pairs out of this module's own source text and kept the delimiting
quote characters, so every parsed pair held a quoted string while the assertion
texts read from JSON carry none — no exemption could ever match, and the
exemption branch of AC13 was dead. The anti-vacuity assertion added to catch
exactly that class passed, because it tested that the set was non-empty rather
than that its contents resolved. The pairs are now a module constant with no
parse, and the anti-vacuity check asserts every entry names an assertion some
case actually declares.

### Scans

- Export-boundary pytest scan and the pack host-identity scan: both pass over
  the payloads, declarations, and records.
- The committed portability grep from `packs/AGENTS.local.md`, run over the two
  payloads: clean. It is the only one of the two portability controls that
  matches a bare `RFC-NNNN` or `ADR-NNNN`.
- Structural host-identity patterns over the retained transcripts and the
  records: clean.

### Suite state

`packs/agent-skill-engineering/tests`: 243 passed.


## T3 — publish and close

Completed 2026-09-09.

### Published surfaces

- **Manifests.** `pack.toml` and `.claude-plugin/plugin.json` both at `0.4.2`,
  one patch above the `0.4.1` they carried at the base commit.
- **Aggregate (AC25).** `FORCE=1 make build-self` propagated the bump to
  `.claude-plugin/marketplace.json` as a single-line change. A second run left
  the file unchanged, which is the check: regeneration-is-a-no-op, since the
  generator writes its target in place and leaves no separate artifact to
  compare against.
- **Changelog (AC26).** Topmost free-standing `##` entry for the pack.
  `Highlights` disposition decided in the same step and recorded in the entry:
  no `### Highlights` section, because the release changes the pack's
  evaluation evidence and not what a consumer can do — no skill body,
  reference, mode, corpus topic, or provider contract moved.
- **Architecture (AC20).** All four RFC-required fields recorded: implemented
  names, their paths, the dependency edge on the composition-floors slice, and
  the verification evidence. Document remains `PLANNED` and states that the
  Gate 2 verdict belongs to closeout.
- **Spec index (AC27).** Row added: mixed shape, 27 ACs / 3 tasks.
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
  to a ledger record, verified by parsing the set out of the guard and matching
  each pair against this file. The five do not carry identical fields, and an
  earlier version of this read claimed they did:
  - the three **added** this slice carry case, assertion text, prior verdict,
    measured verdict, owner authority and the date it was given, which is what
    the Never-do rule enumerates for an exemption change;
  - the two **inherited** entries now carry all six fields too, each citing the
    slice that added it. `progressive-result-presentation` traces to
    `docs/specs/agent-skill-engineering-languages-and-execution/qa.md` §
    "Known-miss exemption — authority recorded", which carries the owner
    authority and the date 2026-08-31. `cross-session-resumption` traces to
    `docs/specs/agent-skill-engineering-corpus/qa.md`, which records the
    measurement decision but no authority field, so the owner gave one for its
    retention on 2026-09-09.
  Two earlier versions of this read were wrong. The first claimed all five
  carried authority and date when two carried neither. The second corrected the
  claim by re-reading the Never-do field list as governing an exemption
  *change* rather than each entry — which contradicts AC15's own per-entry
  scoping, and the spec outranks a reading of it. This version supplies the
  fields rather than narrowing the criterion.
- **AC20, architecture fields.** Read at close; all four present, `PLANNED`
  retained, no gate verdict claimed.

An earlier automated check of the authority phrase reported a gap that was not
one: the phrase spans a line wrap, so the substring search missed it. Re-checked
against whitespace-normalised text. Recorded because a false gap and a real one
look identical in a grep result.

### AC23 — brief digest re-pinned

The registration pinned `sha256-bytes-v1:87f73f2f…`, the brief's digest when T1
wrote the entry. T1 also edited the brief — adding the Spec-map row and
correcting the *Not yet started* paragraph — so the brief moved to
`sha256-bytes-v1:c5e26fcf…` and the pin went stale within the slice. Re-pinned
at close against a freshly computed digest. This is why AC23 requires the
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
| `packs/agent-skill-engineering/tests` | 243 passed |
| `tests/roster` projection suites | 104 passed, 12 subtests |
| `lint-spec-status.py --root .` | exit 0, spec metadata clean |
| `lint-brief-coverage.py --root .` | exit 0, row resolves as `Shipped` |
| `agentbundle catalogue lint --root . --deep` | exit 0 |
| `agentbundle catalogue verify --root .` | exit 0 |
| Workspace projection | no finding for this spec; no `impossible_transition`, no `duplicate_membership` |

## Open, routed onward

**The skill's `references/` tree is not digest-bound in the recorded evidence.**
Records pin `SKILL.md`, `evals/evals.json` and the payloads. The second
discarded round is direct evidence that suppressing `references/` materially
moves the measured responses, so a tree that changes the answers can drift
without any guard noticing. Measured at close: `references/` has no commit and
no diff across this slice, so nothing recorded here is stale.

Not repaired here on the owner's decision of 2026-09-09. Widening the binding
changes the `source_files` contract AC9 and AC12 pin and that the sibling
review-skill records inherit unchanged; at a Shipped spec that is the amendment
path, not a closeout edit. Routed to whoever owns the next slice that touches
this evidence, and named in this slice's pull request.

## Observed gate failures

None. Two pre-existing warn-only spec-status warnings on unrelated specs were
present before this slice and are unchanged by it.
