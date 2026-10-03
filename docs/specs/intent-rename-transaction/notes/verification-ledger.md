# Verification ledger — the intent rename transaction

Measurements this slice's design rests on. The first entry is inherited from
`docs/specs/intent-renumber-and-reissue/`, where the transaction was
originally specified and where the spike was run.

## 2026-09-28 — the transaction's failure modes, measured instead of reasoned

Five generations of this transaction were specified in prose, and each review
round found a defect in the newest one. The sixth was written from measurement.
A throwaway spike drove real `SIGKILL`s at controlled points against fixture
trees and recorded what survived. Nothing from the spike ships; what ships is
the design it corrected.

| # | Question | Result |
| --- | --- | --- |
| A | Does `SIGKILL` strand `.workspace-repair.lock`? | **Yes.** File survives; recorded owner PID verifiably dead; next writer gets `FileExistsError`; the module exposes only `WORKSPACE_LOCK_FILE` and `_acquire_workspace_lock` |
| B | Does `os.replace` consume its source? | **Yes.** Source gone, target holds source bytes |
| C | Same-directory vs cross-device replace | Same-directory succeeds; cross-device raises `EXDEV` (errno 18) |
| D | Does path-based `mkdir` follow a swapped parent symlink? | **Yes — it escaped the root.** An `O_NOFOLLOW` descriptor walk refused it |
| E | What does `SIGKILL` mid-copy leave? | A surviving 120-byte orphan holding a partial tombstone preamble |
| F | Does `dir_fd` + `O_NOFOLLOW` + `S_ISREG` sweep safely? | **Yes.** Symlinked candidate refused, its target survived, real orphan unlinked |

**A is the one that changed the design.** An earlier repair had this operation
acquire the shared workspace lock before allocation and hold it to disposal, to
serialise against `intake-intent` admission. The measurement shows what that
costs: one kill inside the operation leaves a lock no code can clear, and every
workspace writer — repair-apply, migration apply and rollback, guarded refresh,
prune, admission — blocks until a human deletes the file. The fix traded a
silent two-writer race for a repository-wide outage, so it was withdrawn. The
lock is now held only around the registry read-modify-write, which is the
smallest window that still makes that edit atomic against other registry
writers.

The predecessor next tried to close the successor-filename race where it
occurred: exclusive-create followed by a byte comparison on `FileExistsError`.
That mechanism is **withdrawn and superseded by measurement K on 2026-09-29**.
Identical bytes cannot distinguish this transaction's earlier pass from a
concurrent admission. The retained-inode rule recorded below is the surviving
ownership evidence; a different or merely byte-identical inode is a conflict,
never an idempotent success.

**A also records a gap that is not this slice's.** The lock file carries the
owner PID and that PID is checkably dead after a kill, so stale-lock recovery is
implementable — but no writer in the repository performs it, and the helper
exposes no release or break verb. That predates this work and affects every
workspace writer equally. It is named under `## Follow-ons` rather than repaired
here, because widening a shared helper is not this contract's outcome.

**D and E** confirm two security findings that were previously argued rather
than shown: a staging root created by path is reachable outside the repository
if its parent is swapped between validation and use, and a kill mid-copy really
does leave a partial tombstone preamble of the kind the corpus lint rejects.
**F** validates the bounded sweep as specified.

What this does not bound: the same-device-different-mount `EXDEV` case, which
needs a bind mount the spike could not create without elevation. It is moot for
this design, because after the 2026-09-28 decision Commit never renames across
directories. Nor does it bound Windows behaviour, where the reparse-point
semantics of D and F differ and were not exercised.

## 2026-09-29 — recovery-record and identity boundaries

T0 extended the throwaway harness only across the open questions the inherited
run did not answer. It used real `SIGKILL`s against temporary fixture trees and
the shipped shared-lock acquisition helper. The harness itself remains
throwaway; these observations are its deliverable.

| # | Question | Result |
| --- | --- | --- |
| G | Does the stranded shared lock reveal whether the registry replace committed? | **No.** A kill before the replace left the old registry, and a kill after it left the new registry. Both left the same observable lock state: a regular lock file naming a dead owner PID, and the next shipped lock acquisition returned `FileExistsError`. |
| H | Does a complete, parseable recovery record prove staging completed? | **No.** A kill immediately after the record write left a parseable record and zero staged postimages. A kill after the first postimage left the same parseable record and one of two postimages. Only the run killed after a separately written completion seal had both postimages and a seal matching the record digest. |
| I | What does a digest seal establish if the record is altered after the kill? | It detects truncation and an alteration made without replacing the seal. It is not authority: an alteration with a recomputed seal passed the digest check. A closed schema rejected an added field, and independently re-deriving the allowed write set rejected an altered path even when its seal was recomputed. |
| J | Can preimage/postimage validation distinguish a safe replay from a clobber? | **Yes for replaced paths.** The fixture classified old bytes as the preimage, applied bytes as the postimage and unrelated concurrent bytes as neither. The last class can refuse before the first destructive act. For a created successor, identical bytes remain ambiguous and do not establish ownership. |
| K | Can filesystem identity distinguish this transaction's create from an identical concurrent create? | **Yes on the measured host.** An exclusive hard link made the staged successor and final path the same `(st_dev, st_ino)`. A separately created file with identical bytes had a different inode and made the link fail with `FileExistsError`. The same link identity also let a transaction-owned claim stand behind `.workspace-repair.lock`; unlinking the shared name preserved the claim. |
| L | Can this host produce a same-device, different-mount replace case without elevation? | **No.** The fixture root, `/private/tmp` and the repository all resolved to `/dev/disk3s1` mounted at `/System/Volumes/Data`, with the same `st_dev`. The inherited cross-device `EXDEV` result stands; this narrower mount topology remains unmeasured. |

G rules out using the lock file as a commit marker. Recovery has to validate the
registry bytes as preimage or postimage, and it cannot clear a dead lock merely
because the PID is dead: that would risk deleting another writer's lock. K
supplies the missing ownership proof without changing what other workspace
writers observe. The transaction can create a retained claim, link that inode
exclusively at `.workspace-repair.lock`, and later remove the shared name only
when a no-follow stat proves both names still identify that inode.

H and I separate three properties that earlier designs collapsed. A completion
seal written after every staged postimage proves the stage reached its last
write. Its digest catches damage but does not grant write authority. Recovery
therefore still needs a bounded confined parse, a closed schema, and a write set
derived again from the operator's request and repository snapshot rather than
accepted from the record.

J closes the last replay rule for replaced paths: recovery may proceed only
when every live target is still its recorded-and-rederived preimage or
postimage. An alien value refuses before any target changes. K closes the
created-path exception: byte equality is insufficient, so forward and backward
recovery recognise the successor only by identity with its retained staged
inode.

## 2026-09-30 — T6 ADR conformance

Read ADR-0134 D1-D7 against the implemented
`packs/core/.apm/skills/work-intake/scripts/intent_rename.py` and the T1-T5
construction tests. No mismatch was found.

- D1: `_snapshot_successor`, `derive_successor_path` and `_derive` allocate the
  target token's next ordinal, write the successor, and replace the vacated
  source with a shipped tombstone; `test_ac_0012_uses_allocator_next_for_every_namespace_token`
  and `test_ac_0013_valid_request_commits_tombstone_and_registry` cover that
  behavior.
- D2: `_write_stage` writes `record.json`, every numbered postimage, then
  `complete.json`; `test_t1_seal_is_last_and_record_is_comparison_only` proves
  the order and that the record carries comparison metadata rather than bytes.
- D3: `_strict_json`, `_load_stage`, `_derive` and
  `recover_intent_rename` bound and parse the record, re-derive paths and bytes
  from the operator request, tombstone date and pinned snapshot, and reject
  altered records before live mutation; `test_t2_record_parser_rejects_closed_schema_and_structural_attacks`,
  `test_t2_recomputed_record_or_postimage_changes_do_not_gain_authority`, and
  `test_t2_changed_head_and_operator_date_disagreement_refuse_before_mutation`
  cover those boundaries.
- D4: `_apply_forward` creates the successor with `os.link`,
  `_replace_at` uses operation-qualified same-directory temporaries for
  ordinary targets, and `_edit_registry` updates `workspace.toml` last under
  the shared lock; `test_t1_real_kill_after_successor_hard_link_recovers_forward`
  and `test_t1_registry_reread_preserves_unrelated_concurrent_bytes` cover the
  critical cases.
- D5: `_acquire_claim`, `_normalise_old_claim` and `_release_claim` retain
  `lock.claim` identity for `.workspace-repair.lock` and require same-inode,
  dead-PID proof before clearing; `test_t1_real_kill_after_lock_link_clears_owned_stranded_lock`,
  `test_t1_recovery_refuses_alien_lock_inode_without_unlinking_it`, and
  `test_t2_lock_claim_identity_and_pid_are_validated_before_mutation` cover
  owner, foreign and live states.
- D6: `_validate_targets`, `_remove_temporaries`, `_apply_forward` and
  `_apply_back` share the preimage/postimage and retained-inode validation
  barrier before mutation; `test_t1_recovery_refuses_alien_successor_link_before_destructive_act`,
  `test_t2_owned_successor_is_accepted_but_foreign_identical_inode_refuses`,
  and `test_recovery_refuses_forward_and_back_when_citation_set_record_changes`
  cover alien bytes, inode identity and derived-set changes.
- D7: `_write_cleanup`, `_dispose`, `_try_unsealed_cleanup` and
  `_resume_terminal_cleanup` require terminal-state validation before marker
  cleanup and restart disposal from exact owned entries only;
  `test_t1_incomplete_stage_rolls_back_and_cleanup_marker_finishes_forward`,
  `test_t1_unsealed_stage_with_unknown_entry_is_never_swept`,
  `test_t1_disposal_restarts_after_record_and_marker_removal`, and
  `test_t2_no_seal_and_cleanup_marker_are_terminal_state_limited` cover the
  restart and refusal cases.

The approved spec cites ADR-0134 in `Constrained by:`, satisfying the durable
decision closeout for this task.

## 2026-10-01 — Bounds audit: every artifact fits its reader's ceiling

Six adversarial rounds kept finding the same failure one site at a time. An
artifact was written, or an input read, without the ceiling that a later reader
applies. If the write side admits something a reader refuses, a sealed partial
results that no recovery can load. That breaks the two-state property.

The repair is one admission check, `_stage_budget_refused`. It runs before any
stage exists and runs the record through the same strict parser recovery uses.
The table lists every bounded artifact and input after that repair.

| Artifact or input | Reader's ceiling | Where the write or read side enforces it |
| --- | --- | --- |
| `record.json` | `_MAX_RECORD_BYTES`, plus the strict parser's depth, member and string limits | Admission: the byte size, and the same `_strict_json` call recovery makes |
| `complete.json` seal | `_MAX_SEAL_BYTES`, compared byte for byte | Admission: the canonical seal's size. At `_MAX_WRITES` the hash list alone exceeds this ceiling, so admission is what refuses that case |
| Staged postimages and live results | `_MAX_FILE_BYTES` per file | Admission: each expanded postimage, covering the successor, the tombstone and every repointed citation |
| All staged postimages together | `_MAX_CITING_BYTES` | Admission: the sum of the expanded postimages, not only the citing preimages |
| Stage entry set | `_MAX_STAGE_ENTRIES` (writes + 4) | Admission: total writes, including successor and source, at most `_MAX_WRITES` |
| Stage count | `_MAX_RECOVERY_CANDIDATES` | Admission: a new stage may not be the one that crosses the recovery bound |
| `workspace.toml` image | `_MAX_WORKSPACE_BYTES` | `_workspace_transition` in both directions, before the image is parsed or written; admission runs the forward transition |
| `workspace.toml` line count | `_MAX_REGISTRY_MERGE_LINES` (backward merge) | Admission: the forward image, so backward recovery stays possible |
| `cleanup.json` | `_MAX_CLEANUP_BYTES` | Fixed canonical shape of about 250 bytes |
| `lock.claim` payload | 20 bytes; PID at most `2**31 - 1` | The writer writes its own PID; the reader refuses an out-of-range PID before `os.kill` |
| Git output | `_MAX_REF_BYTES`, `_MAX_FILE_BYTES` | `_git` counts bytes while reading and kills Git once the cap is exceeded |
| Target preamble | `_MAX_PREAMBLE_BYTES` | Line-by-line decode that stops at the first visible `## ` heading |
| Tracked set | `_MAX_TRACKED_FILES` | `_tracked_paths` |

Each admission row has a regression test that sets the limit just below the
fixture's real need. It asserts a `stage-budget` refusal with no stage and no
changed file. Every one of those tests fails against the code before this
audit.

## 2026-10-01 — T7 installed-operator manual QA

Followed `guides/product-engineering/how-to/rename-an-intent.md` literally,
using the page's own example path
`docs/product/intents/FEAT-0001-checkout-redesign.md`. The run used a disposable
Git repository with this change's Core build installed by `agentbundle install <catalogue>
--pack core --scope repo --adapter codex`. It covered one rename and both
recovery directions.

The installed artifact was
`.agents/skills/work-intake/scripts/intent_rename.py`. `cmp` proved it
byte-identical to the canonical
`packs/core/.apm/skills/work-intake/scripts/intent_rename.py`. No installed file
contains the example path. The operator ran unmodified, with no
`sitecustomize.py` shim, and disposed of its own stage on every path.

Each recovery started from a real `SIGKILL` of the installed `rename` process,
sent from outside the process the moment its stage directory appeared. The
installed operator has no kill or date seam. The recovery date was the UTC date
of the interrupted run, 2026-10-01.

| Step | Command | Exit | Output |
| --- | --- | ---: | --- |
| Rename | `rename docs/product/intents/FEAT-0001-checkout-redesign.md STRAT` | 0 | `committed:committed:<operation-id>` |
| Resolve | `resolve docs/product/intents/FEAT-0001-checkout-redesign.md` | 0 | `resolve:tombstone:<vacated-path>:<successor-path>` |
| Corpus lint | `intent_corpus_lint.py --dir docs/product/intents --root .` | 0 | `intent-corpus-lint: clean — 2 entries, 1 live, 1 tombstone, 0 unreadable` |
| Forward recovery | `recover forward docs/product/intents/FEAT-0001-checkout-redesign.md STRAT 2026-10-01` | 0 | `committed:committed:<operation-id of the killed run>` |
| Backward recovery | `recover back docs/product/intents/FEAT-0001-checkout-redesign.md STRAT 2026-10-01` | 0 | `rolled_back:rolled-back:<operation-id of the killed run>` |

What each step left behind:

- **Rename.** The successor landed at `STRAT-0001-checkout-redesign.md`, the
  target token's first fresh ordinal. Its bytes equalled the source's with only
  the `Self:` path substituted. The vacated path held a tombstone carrying the
  same `Slug:` and a `Reissued as:` naming the successor. `citation.md` and
  `workspace.toml` were repointed, and no stage directory remained.
- **Forward recovery.** Recovery completed the killed rename under its own
  operation id and disposed of the stage. Resolve and the corpus lint then
  matched the uninterrupted rename, and a string search found the vacated path
  in no file.
- **Backward recovery.** Recovery restored the source, `citation.md`, and
  `workspace.toml` byte-identical to their pre-rename bytes. The successor and
  the stage were gone, and `git status` was clean.

The catalogue-only `FORCE=1 make build-self` step does not apply to a
disposable adopter install, which has no self-host projections.

Installed-operator manual QA result: **pass**.
