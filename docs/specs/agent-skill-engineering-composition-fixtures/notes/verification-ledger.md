# Verification ledger — Agent Skill Engineering Composition Fixtures

Observations produced by execution. The spec and plan are pinned at approval;
this file is where anything measured during the build is recorded.

## Base

- **Base commit:** `18ea69ba9928008f664680620898027dc7abb6fe`. Every "before
  this slice" comparison set — AC3's declared-case set, AC5's marker set, AC8's
  payload digests, AC12's inherited records, AC22's milestone string — is read
  from this commit with `git show 18ea69ba9:<path>`.
- **The base moved once, after round 8.** It was
  `d44484b29d1ba0f56cb0baf42fd79b1348e26a58` for rounds 1 to 8.
  `check-base-freshness.py` returned `{"status": "ok", "message": "head is
  current"}` on 2026-09-09 before the first edit, and `{"status": "surface",
  "message": "branch is 4 commit(s) behind 'origin/main'"}` when re-run after
  round 8. The branch was rebased onto `origin/main`, which is why the base and
  the merge-base are the same commit again.
- **Moving it did not move any comparison.** The authoring skill tree
  `packs/agent-skill-engineering/.apm/skills/author-or-update-agent-skill/` is
  byte-identical between the old and the new base: the same eight inherited
  case ids, the same declarations, the same payloads. Only the commit id
  changed, so AC3, AC5, AC8 and AC12 compare against exactly the bytes they
  compared against before. What did change is the corpus the skill reads while
  being graded, which is why the round was re-taken — see "Re-measurement after
  the rebase".
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

Completed 2026-09-09. The round recorded below was
`2026-09-09-composition-fixtures-r1`; it was superseded in full by
`…-r2` after the rebase — see "Re-measurement after the rebase". The
attestation and the two discarded rounds are kept because they describe the
instrument, which `r2` reused unchanged.

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

### Per-verdict transcript readings for `r1` — superseded history (AC10)

**These readings are not the current record.** They were taken against the
`r1` transcripts, which `r2` replaced in full, and three rows below state
the opposite verdict to what ships. The current record is "Per-verdict
readings for `r2`" further down this file; this table is retained so the
superseded round stays auditable.

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
| Records belong to the declared round (AC11) | Rewrite every record's `observation_id`, leaving `graded_run` declaring the true round | `test_every_authoring_record_belongs_to_one_round` | `AssertionError: (['forged-round'], '2026-09-09-composition-fixtures-r2')` |
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
| Verdicts are booleans, not truthy values (AC11, AC13, AC14) | Replace a `true` verdict with the JSON string `"false"` | `test_independent_behavior_results_cover_both_authoring_cases` and `test_the_seeded_defect_assertion_is_true_or_exempted` | `AssertionError: ('subagent-composition', 0, 'str')` |
| Every retained transcript is scanned, whatever its suffix (AC17) | Add a `.txt` transcript carrying `/Users/someone/checkout` under the transcript root | `test_recorded_evidence_fields_carry_no_host_identifying_data` | `retained transcripts: <path>/leaked.txt: (/Users/\|/home/\|/opt/\|/var/\|/etc/\|C:\\)` |
| A new payload does not duplicate a base payload (AC8) | Overwrite a new payload with an inherited payload's bytes | `test_composition_payloads_are_distinct_non_empty_drafts` | recorded digest present in the base-payload set |
| Seeded-defect verdict is true or exempted (AC13) | Flip `subagent-composition`'s seeded-defect verdict to false | `test_the_seeded_defect_assertion_is_true_or_exempted` and the exemption guard | unexempted false verdict |
| The scan reads inside the root, not through a link out of it (AC17) | Symlink `notes/transcripts/escaped.md` at a clean external Markdown file | `test_recorded_evidence_fields_carry_no_host_identifying_data` | `AssertionError: ('retained transcripts', '<root>/escaped.md', 'symlink')` |
| The AC5 sibling is the one the criterion names (AC5) | Retarget `MARKER_SIBLING` to `node-browser-suite`, which declares the identical marker pair | `test_the_marker_sibling_is_the_one_ac5_names` | `AssertionError: MARKER_SIBLING is 'node-browser-suite' but AC5 names ['pytest-suite']` |
| Retained transcripts stay host-clean after the move (AC17) | Append `/Users/someone/checkout/notes.md` to a retained transcript | `test_retained_transcripts_carry_no_host_identifying_data` | host-identity pattern match on the transcript |
| The relocated scan reads inside the root (AC17) | Symlink a clean external Markdown file into the transcript root | `test_retained_transcripts_carry_no_host_identifying_data` | `AssertionError: ('<root>/escaped.md', 'symlink')` |
| The pattern set cannot be emptied at its source (AC17) | Empty `HOST_IDENTIFYING_PATTERN_STRINGS` in the pack suite | `test_retained_transcripts_carry_no_host_identifying_data` | `AssertionError: the pack suite declares no host-identifying patterns` |
| A declared write status is one the skill can emit (AC4) | Declare `Write status: pending owner sign-off` | `test_every_declared_write_status_is_one_the_skill_can_emit` | value not in the receipt vocabulary |
| The vocabulary is read, not guessed (AC4) | Collapse `SKILL.md`'s receipt line to a single value | `test_every_declared_write_status_is_one_the_skill_can_emit` | `AssertionError: the receipt line parsed to {'not authorized'}` |
| The vocabulary comes from the receipt section (AC4) | Move the vocabulary line above `## Completion receipt` and rename the receipt's own field to `Authorization status:` | `test_every_declared_write_status_is_one_the_skill_can_emit` | `AssertionError: the Completion receipt section carries 0 lines beginning 'Write status: '` |
| The receipt vocabulary has exactly one home (AC4) | Add a second `Write status: ` line above the receipt offering a wider list, and declare its extra value | `test_every_declared_write_status_is_one_the_skill_can_emit` | `AssertionError: SKILL.md carries 2 lines beginning 'Write status: '` |
| The round identifier is not blank (AC11, AC12) | Set `graded_run.observation_id` and all ten record identifiers to `""` | `test_every_authoring_record_belongs_to_one_round` | `AssertionError: graded_run carries observation_id ''` |

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

Completed 2026-09-09. **This section records the pre-rebase close.** The
figures below — the manifest version, the base-commit comparison, the gate
counts — were true when T3 ran and the rebase moved all three. They are kept
as the record of that close; the current state is in "Post-rebase close"
at the end of this file.

### Published surfaces

- **Manifests.** `pack.toml` and `.claude-plugin/plugin.json` both at `0.4.2`,
  one patch above the `0.4.1` they carried at the base commit.
- **Aggregate (AC25).** `FORCE=1 make build-self` propagated the bump to
  `.claude-plugin/marketplace.json` as a single-line change. A second run left
  the file unchanged, which is the check: regeneration-is-a-no-op, since the
  generator writes its target in place and leaves no separate artifact to
  compare against.
- **Changelog (AC26).** Topmost free-standing `##` entry for the pack.
  `Highlights` disposition decided in the same step: no `### Highlights`
  section, because the release changes the pack's evaluation evidence and not
  what a consumer can do — no skill body, reference, mode, corpus topic, or
  provider contract moved. The entry states that verdict and its reason as
  context for a reader of the changelog, but that is not where AC26 or step 4
  of the `packs/AGENTS.local.md` release procedure puts the record: both name
  the PR's *What did you not change that you considered?* answer. Round 8
  corrected the entry, which had claimed the procedure sanctioned the
  changelog as the location — a false attribution a later release could have
  followed while skipping the answer the step exists to produce. **AC26's
  second disjunct is therefore discharged outside the tree and is still open
  at this writing:** the verdict and reason must appear in that PR answer when
  the PR opens. Nothing in the repository can check it — the evidence is an
  external artifact — so it is carried here rather than treated as closed by
  the tick.
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

**The pin went stale a second time, within review.** Two review-repair commits
after the T3 close edited the brief again — the delivered-slice count and the
3e row — so the digest pinned at close stopped describing HEAD. Nothing caught
it, because as this slice's own Follow-on records, no gate reads
`source.revision`. Re-pinned at the end of round 7, deliberately as the last
edit in the round that touches the brief: any later brief edit re-stales it
silently, and this is the second time that has happened in one slice. A
standing check belongs to the workspace-hygiene Follow-on, not to a closeout
edit on a frozen spec.

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

## Recorded divergence — the transcript boundary

AC9 admits any transcript path under this spec's `notes/` directory; the shipped
guard and the host-identity scrub root both enforce the narrower
`notes/transcripts/`. A transcript at `notes/escaped.md` would satisfy the
criterion and redden the guard.

The narrowing is fail-closed — it can reject a conforming transcript, never
admit a non-conforming one — and it is what keeps every cited transcript inside
the only root that scrubs it. It stands as shipped, recorded here rather than
resolved in code:

- rewriting AC9's text is the owner amendment path on a Shipped spec, not a
  closeout edit; and
- widening the guard and the scan back to all of `notes/` reddens today,
  because the mutation row below documents the literal string
  `/Users/someone/checkout/notes.md` as a test input, and a structural scanner
  cannot tell a documented example from real host data. Widening would cost
  either obfuscating that record or carving an exclusion into the scan.

**Withdrawn claim.** The round-4 commit message and an earlier line here said
the criterion, the guard and the scrub root "name one place". They do not. The
guard and the scrub root name one place; the criterion names its parent.

## Anchor sweep — every hand-written comparison set in the guard module

Round 7 found the base-payload population unpinned, the same class as
`BASE_COMMIT` in round 3. Rather than wait for the next instance, every
hand-written literal collection in
`packs/agent-skill-engineering/tests/skills/author_or_update/test_contract.py`
was enumerated and checked for whether narrowing it reddens something:

| Anchor | Narrowing caught by |
| --- | --- |
| `AUTHORING_EVAL_IDS` | its own equality against the declared set |
| `AUTHOR_EVIDENCE_SOURCES` | the `source_files` subset assertion; proved in round 1 |
| `KNOWN_MISSES` | the bidirectional exemption check — dropping a live exemption leaves an unexempted false verdict |
| `MEASUREMENT_FORCED_CLAUSES` | its own set-equality pin |
| `COMPOSITION_CASES` | AC3's equality: narrowing it makes the declared set unequal to base plus two |
| `EXPECTED_PATTERNS` | per-case equality, and a missing key raises under the parametrisation |
| `AUTHOR_ROUTES` | inherited from before this slice; parametrised route resolution |
| `base_payloads` | **was unpinned** — now derived from the base declarations, proved |
| `MARKER_SIBLING` | **was unpinned, and outside this sweep's seed** — now bound to AC5's text, proved in round 8 |

`BASE_COMMIT` is bound to this ledger's recorded base, proved in round 3. No
hand-written comparison set in the module is now narrowable without a guard
reddening.

**The sweep had its own blind spot, found in round 8.** It enumerated
collections, and `MARKER_SIBLING` is a scalar — one string naming the sibling
AC5 compares against. Both limbs of the AC5 guard read through it, so it
decides what that criterion enforces, and it was unpinned for the same reason
`BASE_COMMIT` had been: a bare literal. Five inherited cases declare the
identical marker pair today, which is what makes the cheap repair cheap — when
a later slice moves `pytest-suite`'s markers, the guard reddens on its own
sibling-unmoved limb, and retargeting this one token to any of the five turns
it green while AC5's second limb goes unenforced. It is now bound to AC5's
text, so that repair has to move a shipped criterion instead. Proved by
retargeting it to `node-browser-suite`: the AC5 guard itself stays green — 47
of 48 tests pass — and only the binding reddens, which is the reviewer's
premise confirmed rather than merely accepted.

The generalisation: a sweep reaches only the shapes its seed contains. Round
7's seed was "hand-written collection", so it could not see a hand-written
scalar. The anchors in this module are now every literal that a comparison
reads through, collection or not.

## Re-measurement after the rebase

The round recorded here is `2026-09-09-composition-fixtures-r2`. It replaces
`…-r1` in full: all ten authoring cases were re-executed and re-graded, and
every record's transcript, digest and verdicts are from `r2`.

**Why the round was re-taken.** The branch was four commits behind
`origin/main`, and one of them rewrote two of the three OKF concept topics the
new fixtures route to — `skills-and-subagents-common-floor` and
`plugin-package-common-floor`. The subagent floor gained the sentence "The
worker receives only the context the parent passes it, not the parent's
conversation", which is the defect `subagent-composition`'s payload seeds; the
plugin floor gained a portable core contract. `r1` graded the skill against
corpus bytes that no longer exist. The `references/` Follow-on names this exact
exposure, and here it stopped being hypothetical.

**Instrument.** Unchanged from `r1` and attested on the same terms: one
isolated context per case holding no authoring material, receiving the shipped
`SKILL.md`, the skill's own `references/` tree, and the prompt with its
payload. Withheld from every executor: the assertion list, the pattern
identifiers, the seeded-defect naming, and the expected markers. Grading ran in
a further separate context that received the transcripts and the assertion
lists and authored neither. Responses run 4.6–10.5 KB, against `r1`'s 4.8–9.6
KB, so the instrument sits in the same band that distinguished the recorded
round from the two discarded ones.

**Result: eight of ten verdict rows are unchanged. Two moved.**

| Case | `r1` | `r2` | Reading |
| --- | --- | --- | --- |
| `progressive-result-presentation` | `TTFT` | `TTTT` | index 2 newly true; the response pairs every stop reason with a `next_action` and `next_action_needs`. Its exemption is deleted — an exemption that excuses nothing is a false record of a miss. |
| `node-browser-suite` | `FTTT` | `FTTF` | index 3 newly false. Newly exempted — see the AC15 record below. |

`hook-plugin-design` is **not** in that table, and the correction is worth
keeping visible. The `r2` grading initially read index 3 as true and this
table recorded the move; round 9 found the retained transcript does not carry
it, so the verdict went back to `false` and the exemption was restored. The
row stayed here saying the opposite for one round — the sixth stale-companion
instance in this slice and the first created by the repair for a previous one.
`hook-plugin-design` is `TTTFT` in both rounds.

Both new composition cases report the defect their payload seeds.
`subagent-composition` scored 5 of 5. `hook-plugin-design` scored 4 of 5, its
index-3 miss exempted under the authority recorded below.

**The new miss, and why it is exempted rather than repaired.**
`node-browser-suite[3]` asks the response to bound at least one guarantee to
its ecosystem rather than stating it portably. The `typescript-node` topic
lives in a separate skill reached only through capability metadata and is not
present, so the response withheld every ecosystem-specific mechanism and said
so. That is the same cause already exempted at index 0 of the same case, and
it is the contract's normal degraded path rather than a defect.

The assertion is unsatisfiable in that path, and this is worth stating plainly:
the contract forbids naming ecosystem mechanism without the topic, and the
assertion requires naming it, so no response can satisfy both while the topic
is absent. `r1` scored it true, which on this reading was the weaker behaviour
— a response that named mechanism it had no evidence for. The exemption records
a contradiction between a declared assertion and the shipped contract, not a
missed capability, and repairing it means either shipping the topic or
rewriting the assertion, neither of which belongs in a review round on a frozen
spec.

### Per-verdict readings for `r2` (AC10)

One reading per recorded verdict, taken by the grading context against the
retained `r2` transcript that verdict rests on. The grading context received
the transcripts and the assertion lists and authored neither.

The `r1` reading table further up this file is retained as history and is not
the current record: three of its rows state the opposite verdict, because `r2`
moved them. Read this table for what ships.

| Case | # | Verdict | Reading against the retained `r2` transcript |
| --- | --- | --- | --- |
| `frame-new-skill` | 0 | true | declares "Mode: frame", write not authorized, no files |
| `frame-new-skill` | 1 | true | six should-activate and six should-not-activate concrete prompts given |
| `frame-new-skill` | 2 | true | separate "Non-goals" and "Authority and boundaries" sections apart from activation |
| `frame-new-skill` | 3 | true | proposed file tree shown; explicitly states creation needs separate authorization |
| `update-existing-skill` | 0 | true | full contract inventory precedes candidate change list |
| `update-existing-skill` | 1 | true | boundary stays filesystem_read_untrusted; activation only narrowed, never widened |
| `update-existing-skill` | 2 | true | candidates A-G each labelled with authority required, none chosen |
| `update-existing-skill` | 3 | true | verification section listed; agreement explicitly does not authorize write |
| `cold-start-orientation` | 0 | true | "Mode: frame", read-only end to end, no write boundary |
| `cold-start-orientation` | 1 | true | names AGENTS.md/CLAUDE.md chain, standards, structure, change surface, verification commands |
| `cold-start-orientation` | 2 | true | non-goals exclude proposing change; orientation not forwarded as edit authorization |
| `cold-start-orientation` | 3 | true | write authority none; report only, no caching or persistence |
| `cross-session-resumption` | 0 | **false** | never names update mode; stays in frame throughout |
| `cross-session-resumption` | 1 | **false** | only enumerates candidate mechanisms; adds no record, nothing durable |
| `cross-session-resumption` | 2 | true | activation unchanged, never executes migration, findings quality preserved |
| `cross-session-resumption` | 3 | true | asks for mechanism and confirmed root before requesting write authority |
| `progressive-result-presentation` | 0 | true | "Mode: frame", write not authorized, no file resolved |
| `progressive-result-presentation` | 1 | true | closed stop-reason vocabulary plus partial distinguished from success and failure |
| `progressive-result-presentation` | 2 | true | receipt requires next_action, next_action_needs, resume_from per stop |
| `progressive-result-presentation` | 3 | true | partial never reported as success; status field prevents collapsing readings |
| `knowledge-provider-read-only-entry` | 0 | true | receipt states "Mode: knowledge-provider" explicitly |
| `knowledge-provider-read-only-entry` | 1 | true | root index, child indexes, leaves, routing signals planned; no files created |
| `knowledge-provider-read-only-entry` | 2 | true | "entered read-only and carries no write authority" |
| `knowledge-provider-read-only-entry` | 3 | true | five items required in one explicit authorization before any write |
| `pytest-suite` | 0 | true | guarantee 1 makes collection identity a decision, not style |
| `pytest-suite` | 1 | true | guarantee 3 sets per-test lifetime, temporaries sited outside confined root |
| `pytest-suite` | 2 | true | guarantee 4 rejects one shared fixture directory under parallel runs |
| `pytest-suite` | 3 | true | boundary resolutions priced cheaper/dearer; fixture scope widest assertions still allow |
| `node-browser-suite` | 0 | **false** | argues pinned declared count only; memory and browser cost unmentioned |
| `node-browser-suite` | 1 | true | guarantee 2 requires locked pinned manifest, no test-time install |
| `node-browser-suite` | 2 | true | per-worker, per-run profile directories; shared profile races named unsafe |
| `node-browser-suite` | 3 | **false** | deliberately stated at portable floor, all ecosystem mechanism withheld |
| `subagent-composition` | 0 | true | 200 concurrent write authorities and shared summary race named unsafe |
| `subagent-composition` | 1 | true | fixed minimal brief decided instead of inheriting the conversation |
| `subagent-composition` | 2 | true | parent sets concurrency cap and timeout against unbounded all-200 fan-out |
| `subagent-composition` | 3 | true | parent aggregates; last-worker-summary rejected as skill-voiding defect |
| `subagent-composition` | 4 | true | machine-checkable return schema plus unaudited accounting for failures |
| `hook-plugin-design` | 0 | true | post-publication hook detects only; block requires pre-publication gate |
| `hook-plugin-design` | 1 | true | policy file is data, fixed schema parsed, prose discarded |
| `hook-plugin-design` | 2 | true | challenges chatroom rationale, urges splitting by authority and cadence |
| `hook-plugin-design` | 3 | **false** | states transitive cost and prescribes splitting; never requires pre-install disclosure |
| `hook-plugin-design` | 4 | true | release prefix framed as collision with team's existing local commands |

Five of the forty-two are false, and each is exempted with its authority in
the AC15 record below.

### Exemptions admitted in `r2` — owner authority (AC15, Never do)

Two entries in the exemption set date from `r2` and carry their authority
here. A basis living only in a commit message does not satisfy the rule, which
is why both are recorded with the same six fields the pre-`r2` entries carry.

**1. `hook-plugin-design`, index 3 — restored after a wrong flip.**

- **Case:** `hook-plugin-design`
- **Assertion:** "Names the undisclosed shared dependency as something a
  consumer must see before install"
- **Prior verdict:** false in `r1`, exempted
- **Measured in `r2`:** false
- **Ground:** the retained transcript's only passage on that dependency states
  its transitive cost and prescribes splitting the package by authority. It
  never says a consumer must be shown the dependency before installing. The
  `r2` grading initially read this as true and the exemption was deleted; two
  independent review lenses and the adjudication all found the transcript does
  not carry it, and the justification offered for the flip was verbatim the
  content the `r1` reading had already graded insufficient. The flip rested on
  no new supporting text and is reversed. The declared assertion text is
  unchanged — rewording it to match a measurement is the failure this rule
  exists to prevent.
- **Authority:** repository owner, 2026-09-09, after being shown the
  adjudication, the transcript passage, and both readings.

**2. `node-browser-suite`, index 3 — newly measured false.**

- **Case:** `node-browser-suite`
- **Assertion:** "Bounds at least one guarantee to its ecosystem rather than
  stating it portably"
- **Prior verdict:** true in `r1`
- **Measured in `r2`:** false
- **Ground:** the `typescript-node` topic lives in a separate skill reached
  only through capability metadata and is not present, so the response
  withheld every ecosystem-specific mechanism and said so. This is the same
  cause already exempted at index 0 of this case, and it is the contract's
  normal degraded path. The assertion is unsatisfiable in that path: the
  contract forbids naming ecosystem mechanism without the topic and the
  assertion requires naming it, so no response can satisfy both while the
  topic is absent. `r1` scored it true, which on this reading was the weaker
  behaviour — a response naming mechanism it had no evidence for. The
  exemption records a contradiction between a declared assertion and the
  shipped contract, not a missed capability. Repairing it means shipping the
  topic or rewriting the assertion; both are owner decisions outside a review
  round on a frozen spec, and the `references/` Follow-on is where the first
  belongs.
- **Authority:** repository owner, 2026-09-09, after being shown the
  contradiction, the `r1` verdict, and the alternative of reporting an
  unexcused miss.

### Corrected predeclaration, second instance (Never do)

- **Case:** `knowledge-provider-read-only-entry`
- **Field:** `expect.output_contains`
- **Declared:** `["Mode: knowledge-provider", "Write status: not authorized"]`
- **Measured in `r2`:** `Write status: awaiting explicit authorization`
- **Prior recorded observation:** `r1` and the baseline both observed the
  declared value, so unlike the `cross-session-resumption` correction this one
  is not a declaration that never matched.
- **Ground — the contract, not the observation.** `SKILL.md` fixes a
  three-value receipt vocabulary and defines each: `not authorized` covers a
  read-only mode or phase, `awaiting explicit authorization` means a write is
  planned and not yet granted, `authorized by the user` means it is. The
  response enumerates the files it would create and the five inputs it needs
  first, which is a planned ungranted write. `awaiting explicit authorization`
  is the value the contract prescribes; the earlier observations recorded the
  wrong one and the declaration pinned it.
- **Authority:** repository owner, 2026-09-09, after being shown the receipt
  vocabulary, both prior observations, and the response's file plan.
- **Correction:** the declared pair is now
  `["Mode: knowledge-provider", "Write status: awaiting explicit authorization"]`.

**A control, because this is the second time.** Both corrections share a
cheaper error underneath the judgement: a case can pin a write-status string
the skill has no way to emit, and such a declaration is unfalsifiable — it
fails identically whether the skill is right or wrong.
`test_every_declared_write_status_is_one_the_skill_can_emit` binds every
declared marker to the vocabulary `SKILL.md` declares. It deliberately does not
decide which of the three a given prompt should produce; that is a judgement
about a response and belongs to grading.

## Recorded divergence — this slice's evidence guards do not live where the plan puts them

`plan.md` names
`packs/agent-skill-engineering/tests/skills/author_or_update/test_contract.py`
as the home for the declare-and-pin coverage, and `spec.md` names the same
module and `test_corpus_admission.py`. Eight of those guards, two helpers and
the retained-transcript scan now live in
`tests/roster/test_ase_composition_fixture_evidence.py` instead. The approved
artifacts are frozen and keep their original wording; this is the record of
where the coverage actually is.

**Why it moved.** `tools/lint-pack-test-boundary.py`'s `pack-tests-stay-in-pack`
check refuses a pack test that reaches above its owning pack, and reported 32
findings against this slice. Two classes:

- **Repository-level reads.** `SPEC_DIR`, `TRANSCRIPT_ROOT` and `_at_base`'s
  `cwd` at the repository root. The frozen spec, its ledger and the retained
  transcripts are slice evidence under `docs/specs/`, not pack content, and
  `git show <base>` runs from the repository root.
- **Joins a static reading cannot confine.** `AUTHOR_ROOT / declared`, where
  `declared` comes from `evals.json` at runtime. The pack module states the
  rule it broke on its own line 16: paths are literal "so every path this
  suite opens is statically confined to its own pack". Runtime containment
  checking is a repository-level guarantee, not a pack-local one.

The lint has no allowlist for this check and names the destination, so the
move was forced rather than chosen. The split is by what a guard has to read,
not by which criterion it serves: several criteria are now covered from both
sides, and every property the plan named still has a guard.

**How this was missed for eight review rounds.** The gate was never run. The
local gate set used through rounds 1 to 8 was an inherited list — the pack
suite, the roster suite and five lints — and `make build-check`, which chains
the boundary lint, was not in it. Two adversarial lenses and a quality lens
read the diff without running it either. It surfaced the first time the branch
was pushed and `build-check.yml` ran on CI. An inherited gate list is not the
gate set.

**What did not change.** The relocated guards keep their assertions, their
messages and their recorded mutations. Three were re-proved after the move: a
seeded host path in a transcript, a symlink out of the transcript root, and an
emptied pattern set at its source. The host-identity pattern strings are read
from the pack suite rather than restated, so the two trees cannot drift to
different pattern lists.

## Audit gap — four review rounds are absent from the cohort record

Post-implementation review has run eight rounds. Rounds 1 to 4 fired
`findings-remain` but the controller never ran `review record --fingerprint`
after them, so `review_round_count` and `review_retry_count` stayed at zero and
the review retry cap of 5 never engaged across four findings-bearing rounds.
Round 5 is the first recorded correctly and read `round=1 retry=1`; rounds 6, 7
and 8 follow, so the register now reads `round=4 retry=4` against a cap of 5
while the true count of findings-bearing rounds is eight.

The raw reports and adjudications for all eight rounds are retained under
`.context/reviews/<run-id>/` and are validated and classified, so the evidence
exists; what is missing is the cohort's own count of it. The cap that exists to
force a convergence decision was therefore inert, and that decision was made by
the owner manually each round instead. Retroactive recording was not attempted:
the operation ids derive from transition sequences that have already passed, and
fabricating them would put false provenance in the state file.

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

## Post-rebase close

The T3 record above is the pre-rebase close and its figures no longer describe
the tree. This is the current one. It exists because the spec's verification
record closes only when no required observation lives outside this ledger, and
after the rebase the only current statement of the shipped version sat in the
architecture document, which is an approved artifact.

- **Manifests (AC25).** `packs/agent-skill-engineering/pack.toml` and
  `.claude-plugin/plugin.json` both at `0.4.3`, one patch above the `0.4.2`
  they carry at the current base commit `18ea69ba9`. The bump is a patch
  because the slice changes evaluation evidence and adds no primitive and
  removes none. `0.4.2` was this slice's version before the rebase; the peer
  concepts slice published `0.4.2` on `main` while this branch was open, so
  the two would have been one version string naming two code states.
- **Aggregate.** `.claude-plugin/marketplace.json` regenerated by
  `agentbundle catalogue self-host --write` on a clean tree, which is the only
  way it will run — it refuses a dirty one.
- **Web projection.** `web/src/lib/now-highlights.generated.json` regenerated
  by `tools/build-site.py --journeys-only`. It went stale on the rebase, which
  brought in the peer slice's `Highlights`; this slice contributes none, having
  no `Highlights` section.
- **Changelog.** `0.4.3` entry topmost for the pack, above the peer slice's
  `0.4.2`.

**Gates at close, all exit 0:** pack suite 267; roster suite 1385 passed, 6
skipped, 46 subtests; ruff; mypy; spec-status; brief-coverage; ci-parity;
pack-test-boundary; `catalogue lint --deep`; `catalogue verify`;
`diff --check`. Remote CI on the rebased head: `build-check`, `test-roster`,
`test-corpus` and `pages` all green.

Three of those gates were not in the local set this slice used for its first
eight rounds and were reached only by pushing: the pack-test boundary lint
inside `make build-check`, the repo-wide ruff run, and the generated web
projection inside `make test`. Each found a real defect. An inherited gate
list is not the gate set.

## Observed gate failures

None. Two pre-existing warn-only spec-status warnings on unrelated specs were
present before this slice and are unchanged by it.
