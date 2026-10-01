# Plan: The intent rename transaction

- **Status:** Executing
- **Spec:** [`spec.md`](spec.md)

## Approach

Stage every deterministic postimage, seal that stage last, and only then touch a
live target. Commit creates the successor by an exclusive hard link to its
retained staged inode, replaces ordinary targets from same-directory
temporaries, and edits `workspace.toml` semantically while holding the shared
workspace lock only for that registry read-modify-write. Forward and backward
recovery accept no path or write authority from the durable record: the
operator supplies the original request again, and recovery re-derives the
allowed write set from that request and the pinned Git snapshot before it
changes anything.

T0 measured this shape on 2026-09-29 after the six inherited measurements, not
before them. A parseable record survived with zero and one of two staged
postimages, so `complete.json` is a separate seal written only after every
postimage. A recomputed digest authenticated nothing, so the seal is a
completeness and damage signal only. A hard link distinguished this
transaction's inode from separately created identical bytes, which closes both
the successor identity race and ownership of a stranded shared lock without
changing what other workspace writers observe. The full results are in
`notes/verification-ledger.md`.

The implementation remains one script beside the shipped request, tombstone
and allocator contracts. It uses the standard library and the pack's existing
confinement helpers. No new module boundary, dependency or tool permission is
introduced.

## Constraints

- **`docs/specs/intent-renumber-and-reissue/spec.md`** owns the request
  contract, the tombstone field contract, the citation relation and the
  allocator property. This slice composes them. Cite that spec by path and its
  obligations by name; a bare `AC-####` resolves against local criteria only
  (`lint-contract-item-alignment.py:638-643`), so a cross-spec number silently
  misresolves and reports clean.
- **The shared workspace lock must not be held across the transaction.**
  Measured 2026-09-28: a `SIGKILL` while holding `.workspace-repair.lock`
  leaves the file, the recorded owner PID is dead, the next writer gets
  `FileExistsError`, and `intake_transaction.py` exposes no release or break
  verb — so every workspace writer blocks until a human clears it.
- **Reuse before building.** `resolve_confined_target`
  (`work-intake/scripts/intake_transaction.py:144-165`) is the confined path
  resolver; `open_validated_parent` (`close-work/scripts/cooling.py:595`)
  yields the validated no-follow descriptor; the runtime-shipped
  `work-intake/scripts/file_safety.py` supplies confined reads and the
  `max_files` / `max_entries` / `max_bytes` budgets;
  `cooling.py:615-645` is the durable-write precedent. The predecessor's plan
  proposed hand-rolling the first of these before a reviewer found it.
- **One registry mechanism.** `workspace.toml` is never a fixed postimage in
  the central stage. Under the shared lock, the operation re-reads the current
  bytes, parses the canonical membership, repoints every exact occurrence of
  the source path to the successor path, validates the resulting registry, and
  preserves every unrelated byte and concurrent entry. Recovery classifies the
  registry as before or after from both the unique membership and the absence
  of stale source-path occurrences, then applies that same whole-file citation
  transition. This is locked live editing; the central staged-file mechanism
  does not also claim to own the registry.
- **Generated projections stay generated.** The operation rewrites the `.apm/`
  source and never its adapter projection. The installed operator flow closes
  with the repository's self-host command, and `CAT-V-015` remains the owner of
  source-to-projection equality. The corpus lint and the rename hold no shared
  lock; a torn read must remain a loud non-zero result rather than a false clean.
- `work-intake` declares `Read Write Edit Bash`. No tool surface widens.

## Repository anchors

- `packs/core/.apm/skills/work-intake/scripts/intent_rename_request.py` is the
  shipped, side-effect-free request boundary and owns root discovery, source
  confinement, registry membership, namespace-token validation and the initial
  clean-path refusal.
- `packs/core/.apm/skills/work-intake/scripts/intent_tombstone.py` is the
  shipped pure serializer and parser. The transaction passes it the date
  sampled once when the operation starts.
- `packs/core/.apm/skills/work-intake/scripts/intake_transaction.py` supplies
  the existing workspace-lock filename and the externally observed lock-file
  protocol. The rename does not call its long-held transaction wrapper.
- `packs/core/.apm/skills/close-work/scripts/close_work.py` supplies
  `open_validated_parent`, the descriptor walk reused before every write.
  `packs/core/.apm/skills/close-work/scripts/cooling.py` is the corresponding
  same-directory temporary and descriptor-relative `os.replace` precedent.
- `packs/core/.apm/skills/work-intake/scripts/file_safety.py` is the installed
  runtime sibling and owns the bounded, confined, single-link regular-file read
  used for the recovery record, seal and staged postimages. The transaction
  loads that sibling by path like the shipped request script; it never imports
  `packages/agentbundle` build internals.
- Tests follow the path-qualified script-loader pattern in
  `packs/core/tests/skills/work-intake/test_intent_rename_request.py` and the
  failure-injection shape in `test_intake_transaction.py`.

Named uncertainty: Windows reparse-point and hard-link behavior is not measured.
The implementation therefore keeps platform-dependent filesystem errors on the
fail-closed path and does not claim Windows support from the macOS result.

## Inherited open findings

Six Blockers stood unresolved against the predecessor's transaction when it was
cut out on 2026-09-28. They are inputs to this slice's design, not defects in
it. The review artifacts were session-local and are not present in this
worktree. This section is the complete surviving record and the primary input
to the design.

They fall into two groups, and the grouping is the most useful thing the
predecessor learned.

**Group 1 — the lock and the registry.** Narrowing the shared lock to the
registry read-modify-write left the lock artifact outside the partial-state
record, so a kill inside that critical section strands recovery itself. The
registry was described as both staged-and-replaced and locked-live-edited, two
mechanisms in one document. And an identity-aware exclusive-create on the
successor cannot, by byte comparison alone, distinguish this transaction's
earlier pass from a concurrent admission that produced identical bytes.

**Group 2 — the recovery record.** A record written before a kill is read after
it by a process that must decide whether to replay a write-set over live paths.
It currently has no bounded confined parse, no closed schema, no completion
seal written last, no independent re-derivation of the allowed write set, and
no postimage validation before the first destructive act. The no-follow
descriptor that protects creation cannot survive the kill that makes recovery
necessary, so recovery must reacquire it.

Group 2 is the harder half and the reason this is a slice rather than a repair:
every item in it follows from one property — a durable recovery record must be
trusted by a process that did not write it — rather than from any wording.

## Assumptions and exclusions

- **Files expected to change:** the transaction and resolver script beside the
  shipped contracts, work-intake tests and evals, both pack version manifests,
  the two skill bodies that currently state the capability wall, the accepted
  ADR, the maintainer how-to, `docs/product/changelog.md`, this spec and plan,
  and their verification ledger. Adapter projections change only through
  self-host.
- **Done is demonstrated by:** real `SIGKILL` coverage at every stage and
  commit checkpoint; forward and backward recovery to the two byte-checked end
  states; malformed, altered and symlink-swapped recovery inputs refusing
  before mutation; the cited-set and allocator properties; the installed-pack
  operator flow; the targeted suite and repository gates named by the spec.
- **Not changing:** the shipped request or tombstone contracts, the allocator's
  namespace or rule, the shared lock protocol observed by other writers, the
  corpus lint's no-lock race behavior, the brief's Spec map, or any Draft
  follow-on intent in this initiative.

Declined additions:

- A new transaction package or abstraction layer — `Cut before adding`, rung 2:
  the shipped sibling scripts and confinement helpers already supply the
  needed ownership seams.
- A cryptographic signature for the recovery record — `Cut before adding`,
  rung 3: no repository secret or signer exists, and T0 shows the digest is not
  authority; independent re-derivation is the control this boundary needs.
- A transaction-wide lock — forbidden by the measured repository-wide outage,
  not merely declined by the cut ladder.
- `tomlkit` as a new runtime requirement — `Cut before adding`, rung 3: the
  registry change is one validated path-value edit and the installed operation
  must not inherit `repair-apply`'s optional dependency.

Expected review shape: DEEP and below 2,000 reviewable behavior-and-test lines.
The dependency boundaries are T1/T2 (transaction and recovery core), T3–T5
(domain properties), then T6/T7 (decision and installed surface).

Resolve-vs-surface record opened at PLAN: every review Blocker and Concern that
is required for the twelve criteria or the recovery trust boundary is fixed in
this slice. The brief Spec-map amendment and shared stale-lock recovery for
other writers remain owner decisions outside this slice. Knowledge provider
unavailable; no eligible `agent-skill-engineering-reference/v1` capability was
present on the active tool surface.

## Design (LLD)

### Operator and in-process surfaces

`intent_rename.py` is the one new script. Its in-process surface returns a
closed `RenameResult` carrying `status`, a fixed diagnostic `code`, and an
optional opaque `operation_id`; expected refusals do not escape as exceptions.
`run_intent_rename`, `recover_intent_rename` and `resolve_intent_path` are the
orchestration seams. `derive_citing_paths`, `repoint_citation_bytes` and
`derive_successor_path` expose the three pure domain calculations their
construction tests pin. Private `_checkpoint` and `_today` callbacks exist only
for deterministic failure and UTC-date injection; the real-kill matrix drives
the same named checkpoints in child processes and neither seam appears on the
installed CLI.
The installed operator surface exposes three actions:

1. `rename <source-path> <target-token>` plans, stages and commits a new
   operation. One matching recovery record refuses `recovery-required` and
   names its opaque operation ID; more than one refuses `recovery-ambiguous`.
2. `recover <forward|back> <source-path> <target-token> <tombstone-date>`
   selects the one record whose safely parsed request equals the
   operator-supplied request. The record does not choose the source, token,
   direction or date. The date is an ISO 8601 calendar date explicitly
   re-supplied by the operator and validated through the shipped serializer.
3. `resolve <intent-path>` reads the confined source. For a tombstone, it
   boundedly and confinedly inspects exactly the `Reissued as:` target preamble
   to classify missing, tombstone or live, then reports the source and target.
   It never returns target content or recursively follows a target tombstone.

All printed diagnostics are fixed tokens plus confined repository-relative
paths. Both streams are configured to UTF-8 before the first print, as the pack
contract requires.

Owned by: T1, T2, T3, T4, T5, T7

### Snapshot and derived write set

Plan is read-only. It validates the shipped rename request, samples the date and
current `HEAD`, and derives the whole non-registry write set from that snapshot:

- one created successor at the allocator's next ordinal for the target token;
- the vacated source replaced by the shipped three-field tombstone;
- every tracked, decodable, non-projection, non-registry file containing the
  vacated path, each replaced by the exact old-path to new-path byte
  substitution;
- the `.apm/` source for any generated projection, never the projection; and
- `workspace.toml` as a semantic registry transition, not a fixed staged file.

The tracked parent set comes from `git --no-optional-locks --literal-pathspecs
ls-files -z --`. Every read is bounded. The plan refuses an undecodable citing
file, a file or byte budget overflow, a missing projection source, a dirty
affected path, a tracked-but-absent successor name, or a successor that already
exists. The base commit, exact ordered path set, action kind, preimage digest
and deterministic postimage digest are fixed before Stage. `workspace.toml`
records only its `registry-edit` action kind and the derived source and
successor strings because unrelated entries may legitimately change before its
locked critical section; the action still covers every occurrence required by
the citation-conservation criteria.

Recovery re-runs this derivation from the operator's source, token and
explicitly re-supplied tombstone date against the recorded base commit, which
must still be `HEAD`. It compares the exact ordered path set, action kinds and
deterministic digests with the record. The record's date is comparison data
only: the operator's bounded date is validated through the shipped serializer
and independently re-derives the complete tombstone bytes. A record path is
never joined to the root until the independently derived path in the same
position is equal.

Owned by: T1, T3, T4

### Stage record and completion seal

Stage creates `.intent-rename-<operation-id>` through a held no-follow
descriptor for `docs/product/intents/`. The identifier comes from `secrets`,
is validated against one closed lowercase-hex grammar, and grants no path
authority. Its sealed immutable entry set contains only:

- `record.json`, canonical strict JSON with a closed versioned schema;
- one numbered canonical postimage per non-registry write; and
- `complete.json`, written and directory-fsynced last, containing the SHA-256
  digest of `record.json` and the ordered postimage digests.

Limits are closed constants: record bytes, seal bytes, write count, per-file
bytes, total staged bytes and directory-entry count. JSON serialization uses
`allow_nan=False`. Loading rejects duplicate and unknown object keys, wrong
scalar or container types, non-finite numbers, nesting beyond a fixed depth,
containers beyond a fixed member count and strings beyond a fixed length before
semantic use; a decoder recursion failure is the same fixed refusal. Diagnostics
echo no record data.

The blessed confined-file helper reads the single-link record, seal and
postimages before Commit. The sealed core entry set is exact and every
postimage must equal the bytes independently re-derived for its path. After
Commit starts, the only permitted extra stage entries are the ephemeral
`lock.claim` and the closed `cleanup.json` marker described below; they may not
coexist. Descriptor-relative `O_NOFOLLOW` opens plus `fstat` validate the two
retained-identity exceptions that the single-link helper deliberately rejects:

- the successor postimage has link count one while the live successor is absent,
  or link count two only while that live name is the same `(st_dev, st_ino)`;
- `lock.claim` has link count one while the shared name is absent, or link count
  two only while `.workspace-repair.lock` is the same `(st_dev, st_ino)`.

Any other entry, link count, inode relation or file type refuses before
mutation. Neither runtime entry is covered by `complete.json`; the claim grants
no authority over a live lock, and the cleanup marker grants no authority over
a live path.

The seal proves only that Stage reached its last durable write and that the
bytes read together are undamaged. It is not a signature. A valid seal is
required before Commit may start. A missing, invalid or no-longer-completable
seal never authorizes a live-path mutation. Without `cleanup.json`, recovery
may only remove an exact confined stage after independently proving every live
target is still its preimage and the successor is absent. With `cleanup.json`,
it may only finish stage-only disposal after independently proving the live
tree is exactly all-before or all-after. Every other state refuses.

Owned by: T1, T2

### Commit and target identity

Commit begins only from a validated sealed stage. Before the first destructive
act it reopens the repository root and every target parent through
`open_validated_parent`, classifies every live target, and refuses the whole
attempt if any replaced path is neither its preimage nor postimage, or if the
created successor is occupied by any inode other than the retained staged
postimage.

The successor is first. `os.link` creates the final name exclusively from the
staged postimage. On `FileExistsError`, equality of `(st_dev, st_ino)` with the
staged postimage is the only already-applied result; identical bytes on another
inode are `successor-conflict`. Ordinary targets are then applied in the
derived order by copying the retained postimage to one operation-id-qualified
temporary beside the target and calling descriptor-relative `os.replace` with
the same parent descriptor for both names. Recovery removes only that exact
temporary after a no-follow regular-file check; it never sweeps a prefix shared
with another operation.

`workspace.toml` is last. While holding the shared workspace lock, the operation
re-reads and parses its current bytes. Before-state requires exactly one source
membership, no successor membership and at least that source occurrence; the
operation replaces every exact source-path occurrence in the current bytes,
then parses and validates the result before a same-directory replace.
After-state requires exactly one successor membership and no remaining source
occurrence. This repoints `needs` edges, headers, comments and any other literal
occurrence covered by the citation contract while preserving all unrelated
bytes and entries added before lock acquisition. Any other state refuses.

Owned by: T1

### Shared-lock ownership without a protocol change

The registry critical section uses the existing
`.workspace-repair.lock` name and PID bytes but acquires it by inode claim:

1. After validating the sealed immutable stage, exclusively create the optional
   runtime entry `lock.claim` as a single-link regular file containing the
   current ASCII PID, and fsync it.
2. Exclusively hard-link that inode at `.workspace-repair.lock` through the
   held repository-root descriptor. Existing writers see the same file name,
   mode and PID payload they already understand.
3. Before release, no-follow stat both names and unlink the shared name only
   when `(st_dev, st_ino)` still matches. Then unlink the retained claim. A kill
   before the hard link leaves a one-link claim with no live-path authority.

After a kill, recovery clears a lock only when the retained claim and shared
name are the same inode, the payload is one bounded canonical PID, and that PID
is verifiably dead. A different inode is another writer's lock even when the
bytes match; a live PID is active work. After clearing its own dead claim,
recovery removes the dead retained claim, exclusively creates a fresh claim at
the same known stage name for its own PID, and competes normally for the shared
name. This keeps the lock outside the long transaction window while making the
one kill-prone critical section recoverable.

Owned by: T1, T2

### Recovery state machine

Forward and backward recovery share one validation barrier. Before either
changes a target they reacquire all descriptors, validate the record, seal,
snapshot, derived write set, staged postimages, exact directory entry set,
shared-lock identity if present, and every live target:

- a replaced target may equal only its preimage or postimage;
- the successor may be absent or the same inode as its staged postimage; and
- the registry may carry only the before or after membership relation; the
  after relation also requires no remaining source-path occurrence, with all
  unrelated valid registry content preserved; and
- each retained successor postimage or optional lock claim must satisfy its
  exact one-link or owned two-link state before it can justify a live action.

An alien byte sequence, foreign inode, symlink, unknown field, excess entry,
changed `HEAD`, changed derived set or budget failure refuses before the first
destructive act. Validation is one full pass; execution does not discover a
new target from record data.

Forward applies only preimage targets, treats postimages as already applied,
edits the registry last under its claim, and validates the complete state.
Backward restores only postimage targets from Git-derived preimages, reverses
the registry transition under its claim, unlinks the successor only when inode
identity proves ownership, and validates the byte-identical pre-rename state.

Only after one terminal validation and release of the shared lock does the
operation write and directory-fsync canonical `cleanup.json`. Its closed schema
names the operation ID, terminal direction, record digest and completion-seal
digest. Those fields are comparison data, not authority; the marker's only
meaning is that recovery may perform stage-only cleanup after independently
revalidating a terminal live state.

Disposal is ordered and restartable: the shared lock must be absent; the
optional one-link claim and outside-target temporaries are removed; the cleanup
marker is durably written; then postimages, `complete.json`, `record.json`,
`cleanup.json`, and the empty stage directory are removed in that order. At
every interruption, `cleanup.json` remains until it is the sole stage entry.
Recovery accepts only an exact remaining subset implied by that order and an
independently validated all-before or all-after live state. Without the marker,
a no-seal stage is discardable only from the all-before state. An unknown entry
or alien link relation refuses rather than being recursively deleted.

Owned by: T1, T2

### Security and failure controls

- Path authority comes only from the operator request plus independent
  derivation. Record paths are compared data, never instructions.
- The repository root and each parent descriptor are reacquired after a kill;
  no descriptor is assumed to survive process death.
- Every exceptional condition is fail-closed and returns a fixed token. No
  traceback, absolute path, record content or staged bytes reach stdout or
  stderr.
- No retry loop is unbounded. Candidate operation records, stage entries,
  citing files, bytes and temporary-name attempts each have a fixed cap.
- SHA-256 is used for damage comparison, not authentication. Operation IDs and
  temporary suffixes use `secrets`, not `random`.
- The operation invokes Git with argument vectors, `--literal-pathspecs`, an
  explicit `--` before paths, disabled optional locks for reads, a timeout and
  `stdin=DEVNULL`; it never builds a shell command from a record or request.

Owned by: T2, T7

## Tasks

### T0 — Measure the transaction's failure modes before designing it

**Tests:** `no stub (goal-based)`. A throwaway harness drove real kills and
recorded the surviving lock, registry, stage record, postimages and seal. It
also measured altered-record handling, preimage/postimage classification,
hard-link identity and the available mount topology. The 2026-09-29 ledger
entry is the result; no harness code ships.

**Approach:** The predecessor's spike is the starting shape and is recorded in
`notes/verification-ledger.md`. What it did not reach: kill-inside-the-registry
critical section, kill between record write and stage completion, recovery run
against a record altered after the kill, and the same-device-different-mount
`EXDEV` case if an environment can produce one.

**Depends on:** none

### T1 — The transaction applies in full or reaches exactly one recoverable state

**Tests:** `test_ac_0003_preapply_refusal_leaves_tree_and_index_unchanged`,
`test_ac_0026_both_recovery_directions_reach_only_an_end_state`,
`test_ac_0002_and_ac_0024_successor_and_slug_bytes_are_conserved`, and
`test_ac_0013_valid_request_commits_tombstone_and_registry`; AC-0003, AC-0026,
AC-0002, AC-0024 and AC-0013; `stub: true`. Stored for
`packs/core/tests/skills/work-intake/test_intent_rename_transaction.py`:

```python
# STUB: AC-0003, AC-0026, AC-0002, AC-0024, AC-0013
from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


_PARENTS = Path(__file__).resolve().parents
PACK_ROOT = _PARENTS[3] if len(_PARENTS) > 3 else Path.cwd() / "packs/core"
SCRIPT = PACK_ROOT / ".apm/skills/work-intake/scripts/intent_rename.py"
SOURCE = "docs/product/intents/FEAT-0001-rename-test.md"
SUCCESSOR = "docs/product/intents/STRAT-0001-rename-test.md"
TOMBSTONE_DATE = date(2026, 9, 29)


def _load() -> Any:
    spec = importlib.util.spec_from_file_location("core_work_intake_intent_rename", SCRIPT)
    assert spec and spec.loader, SCRIPT
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rename = _load()


def _commit(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test Runner"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "fixture"],
        cwd=root,
        check=True,
        capture_output=True,
    )


def _fixture(root: Path) -> bytes:
    source = root / SOURCE
    source.parent.mkdir(parents=True)
    source_bytes = (
        "# Rename test\n\n"
        "- **Slug:** `rename-test`\n"
        "- **Status:** Draft\n"
        "- **Level:** feature\n"
        "- **Owner:** test-owner\n\n"
        f"Self: {SOURCE}\n"
    ).encode()
    source.write_bytes(source_bytes)
    (root / "citation.md").write_text(f"See {SOURCE}.\n", encoding="utf-8")
    (root / "workspace.toml").write_text(
        "[backlog]\n"
        f'open = [{{path = "{SOURCE}", kind = "intent", '
        'source = {mode = "repo-origin"}, summary = "rename", needs = []}}]\n',
        encoding="utf-8",
    )
    _commit(root)
    return source_bytes


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


def _interrupt_after_successor(checkpoint: str) -> None:
    if checkpoint == "after-successor":
        raise rename.InjectedInterruption(checkpoint)


def test_ac_0003_preapply_refusal_leaves_tree_and_index_unchanged(tmp_path: Path) -> None:
    _fixture(tmp_path)
    before = _tree(tmp_path)
    result = rename.run_intent_rename(SOURCE, "UNKNOWN", repository_root=tmp_path)

    assert result.code == "token-unknown"
    assert _tree(tmp_path) == before
    assert subprocess.run(
        ["git", "status", "--porcelain"], cwd=tmp_path, check=True, capture_output=True
    ).stdout == b""


def test_ac_0026_both_recovery_directions_reach_only_an_end_state(tmp_path: Path) -> None:
    forward_root = tmp_path / "forward"
    back_root = tmp_path / "back"
    forward_root.mkdir()
    back_root.mkdir()
    _fixture(forward_root)
    before_back = _fixture(back_root)

    forward_partial = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=forward_root,
        _checkpoint=_interrupt_after_successor,
        _today=lambda: TOMBSTONE_DATE,
    )
    back_partial = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=back_root,
        _checkpoint=_interrupt_after_successor,
        _today=lambda: TOMBSTONE_DATE,
    )
    assert forward_partial.status is rename.RenameStatus.PARTIAL
    assert back_partial.status is rename.RenameStatus.PARTIAL

    forward = rename.recover_intent_rename(
        "forward",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=forward_root,
    )
    backward = rename.recover_intent_rename(
        "back",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=back_root,
    )

    assert forward.status is rename.RenameStatus.COMMITTED
    assert (forward_root / SUCCESSOR).is_file()
    assert backward.status is rename.RenameStatus.ROLLED_BACK
    assert (back_root / SOURCE).read_bytes() == before_back
    assert not (back_root / SUCCESSOR).exists()
    assert not list((back_root / "docs/product/intents").glob(".intent-rename-*"))


def test_ac_0002_and_ac_0024_successor_and_slug_bytes_are_conserved(tmp_path: Path) -> None:
    source_bytes = _fixture(tmp_path)
    result = rename.run_intent_rename(SOURCE, "STRAT", repository_root=tmp_path)

    assert result.status is rename.RenameStatus.COMMITTED
    expected = source_bytes.replace(SOURCE.encode(), SUCCESSOR.encode())
    assert (tmp_path / SUCCESSOR).read_bytes() == expected
    assert b"- **Slug:** `rename-test`" in (tmp_path / SUCCESSOR).read_bytes()
    assert b"- **Slug:** `rename-test`" in (tmp_path / SOURCE).read_bytes()


def test_ac_0013_valid_request_commits_tombstone_and_registry(tmp_path: Path) -> None:
    _fixture(tmp_path)
    result = rename.run_intent_rename(SOURCE, "STRAT", repository_root=tmp_path)

    assert result.status is rename.RenameStatus.COMMITTED
    tombstone = (tmp_path / SOURCE).read_text(encoding="utf-8")
    assert f"- **Reissued as:** {SUCCESSOR}" in tombstone
    workspace = (tmp_path / "workspace.toml").read_text(encoding="utf-8")
    assert SOURCE not in workspace
    assert SUCCESSOR in workspace
```

Scratch validation: `py_compile` passed; pytest collected red because the
planned `intent_rename.py` contract does not exist yet. EXECUTE adds the real
kill matrix, all named checkpoints, the unaffected-intent case, index snapshots,
lock/stage/temporary absence, `workspace.toml` membership plus `needs`
repointing, kills after the successor and shared-lock hard links, owned two-link
recovery, alien-link refusal, no-seal incomplete-stage versus cleanup-marker
classification, and disposal-interruption cases before green.

**Depends on:** T0

### T2 — Recovery treats its record as untrusted input

**Tests:** `no stub (implementation-discovered)`. Discovery predicate: T1 must
first materialize the closed record and seal serializers plus the named
checkpoint that leaves a complete sealed stage without committing. Proof
obligation: mutate that real artifact through truncation, duplicate keys,
unknown fields, wrong types, excessive nesting, container members and string
length, a recomputed-seal write-set change, staged-postimage change, and parent
symlink swap, and show `recover_intent_rename` returns the fixed refusal without
echoing content while a before/after snapshot proves no live target changed.
Add the owned and alien successor-link and lock-claim states, alien-live-target,
foreign-identical-successor-inode, foreign-lock-inode, live-lock-owner, changed
`HEAD`, record-date disagreement with the operator-supplied date, entry-count
and byte-budget cases. Kill once before the seal exists and once after
`cleanup.json` is durable but `complete.json` is removed; prove the first can
only discard an all-before stage and the second can only finish stage cleanup
from an independently validated terminal tree. Covers AC-0026's recovery arm.

**Depends on:** T1

### T3 — The citing set is exactly the files containing the vacated path

**Tests:** `test_ac_0001_and_ac_0018_derived_set_equals_independent_string_search`;
AC-0001 and AC-0018; `stub: true`. Stored for
`packs/core/tests/skills/work-intake/test_intent_rename_citations.py`:

```python
# STUB: AC-0001, AC-0018
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any


_PARENTS = Path(__file__).resolve().parents
PACK_ROOT = _PARENTS[3] if len(_PARENTS) > 3 else Path.cwd() / "packs/core"
SCRIPT = PACK_ROOT / ".apm/skills/work-intake/scripts/intent_rename.py"
SOURCE = "docs/product/intents/FEAT-0001-source.md"
SUCCESSOR = "docs/product/intents/STRAT-0001-source.md"


def _load() -> Any:
    spec = importlib.util.spec_from_file_location("core_work_intake_intent_rename_citations", SCRIPT)
    assert spec and spec.loader, SCRIPT
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rename = _load()


def test_ac_0001_and_ac_0018_derived_set_equals_independent_string_search(
    tmp_path: Path,
) -> None:
    intents = tmp_path / "docs/product/intents"
    intents.mkdir(parents=True)
    fixtures = {
        SOURCE: f"# Source\n\n- **Slug:** `source`\n\nSelf: {SOURCE}\n",
        "inline.md": f"[source]({SOURCE})\n",
        "header.md": f"- **Discovery:** {SOURCE}\n",
        "config.toml": f'path = "{SOURCE}"\n',
        "fence.md": f"```text\n{SOURCE}\n```\n",
        "docs/specs/intent-rename-transaction/notes/verification-ledger.md": SOURCE,
    }
    for relative, text in fixtures.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)

    actual = set(
        rename.derive_citing_paths(
            SOURCE, SUCCESSOR, repository_root=tmp_path, created_paths=(SUCCESSOR,)
        )
    )
    expected = {
        relative
        for relative, text in fixtures.items()
        if SOURCE in text
        and relative not in {SOURCE, "docs/specs/intent-rename-transaction/notes/verification-ledger.md"}
    }

    assert actual == expected
    for relative in actual:
        before = (tmp_path / relative).read_bytes()
        after = rename.repoint_citation_bytes(before, SOURCE, SUCCESSOR)
        assert after == before.replace(SOURCE.encode(), SUCCESSOR.encode())
```

Scratch validation: `py_compile` passed; pytest collected red because the
planned module is absent. EXECUTE adds the untracked successor, `.apm/` source
plus adapter projection, non-UTF-8 refusal, tracked-file and byte budgets, and
the two-direction set comparison before green.

**Approach:** Derive the parent set from `git ls-files -z` with an explicit
`--` terminator; the relation and its exclusions are the sibling spec's, not
this one's to restate.

**Depends on:** T1, T2

### T4 — The new ordinal is the allocator's next for the target token

**Tests:** `test_ac_0012_uses_allocator_next_instead_of_vacated_ordinal`;
AC-0012; `stub: true`. Stored for
`packs/core/tests/skills/work-intake/test_intent_rename_allocation.py`:

```python
# STUB: AC-0012
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


_PARENTS = Path(__file__).resolve().parents
PACK_ROOT = _PARENTS[3] if len(_PARENTS) > 3 else Path.cwd() / "packs/core"
SCRIPT = PACK_ROOT / ".apm/skills/work-intake/scripts/intent_rename.py"


def _load() -> Any:
    spec = importlib.util.spec_from_file_location("core_work_intake_intent_rename_allocation", SCRIPT)
    assert spec and spec.loader, SCRIPT
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rename = _load()


def test_ac_0012_uses_allocator_next_instead_of_vacated_ordinal(tmp_path: Path) -> None:
    intents = tmp_path / "docs/product/intents"
    intents.mkdir(parents=True)
    source = "docs/product/intents/FEAT-0001-rename-test.md"
    (tmp_path / source).write_text("- **Slug:** `rename-test`\n", encoding="utf-8")
    (intents / "STRAT-0002-existing.md").write_text(
        "- **Slug:** `existing`\n", encoding="utf-8"
    )

    successor = rename.derive_successor_path(
        source, "STRAT", repository_root=tmp_path
    )

    assert successor == "docs/product/intents/STRAT-0003-rename-test.md"
    assert successor != "docs/product/intents/STRAT-0001-rename-test.md"
```

Scratch validation: `py_compile` passed; pytest collected red because the
planned module is absent. EXECUTE adds every namespace token, tombstones in the
corpus, allocator refusal and occupied tracked or untracked successor cases.

**Depends on:** T1

### T5 — Resolution stops at a tombstone, and inbound tombstones re-point

**Tests:** `test_ac_0007_missing_target_names_tombstone_and_target`,
`test_ac_0008_tombstone_target_names_both_tombstones`, and
`test_ac_0009_resolution_stops_without_returning_successor_content`; AC-0007,
AC-0008 and AC-0009; `stub: true`. Stored for
`packs/core/tests/skills/work-intake/test_intent_rename_resolution.py`:

```python
# STUB: AC-0007, AC-0008, AC-0009
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


_PARENTS = Path(__file__).resolve().parents
PACK_ROOT = _PARENTS[3] if len(_PARENTS) > 3 else Path.cwd() / "packs/core"
SCRIPT = PACK_ROOT / ".apm/skills/work-intake/scripts/intent_rename.py"


def _load() -> Any:
    spec = importlib.util.spec_from_file_location("core_work_intake_intent_rename_resolution", SCRIPT)
    assert spec and spec.loader, SCRIPT
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rename = _load()


def _tombstone(target: str) -> str:
    return (
        "# Tombstone: old\n\n"
        "- **Slug:** `old`\n"
        "- **Tombstone:** 2026-09-29\n"
        f"- **Reissued as:** {target}\n"
    )


def test_ac_0007_missing_target_names_tombstone_and_target(tmp_path: Path) -> None:
    old = "docs/product/intents/FEAT-0001-old.md"
    target = "docs/product/intents/STRAT-0001-new.md"
    path = tmp_path / old
    path.parent.mkdir(parents=True)
    path.write_text(_tombstone(target), encoding="utf-8")

    result = rename.resolve_intent_path(old, repository_root=tmp_path)

    assert result.code == "tombstone-target-missing"
    assert result.paths == (old, target)


def test_ac_0008_tombstone_target_names_both_tombstones(tmp_path: Path) -> None:
    old = "docs/product/intents/FEAT-0001-old.md"
    target = "docs/product/intents/STRAT-0001-new.md"
    final = "docs/product/intents/CAP-0001-final.md"
    for relative, text in ((old, _tombstone(target)), (target, _tombstone(final))):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    result = rename.resolve_intent_path(old, repository_root=tmp_path)

    assert result.code == "tombstone-target-is-tombstone"
    assert result.paths == (old, target)


def test_ac_0009_resolution_stops_without_returning_successor_content(tmp_path: Path) -> None:
    old = "docs/product/intents/FEAT-0001-old.md"
    target = "docs/product/intents/STRAT-0001-new.md"
    for relative, text in ((old, _tombstone(target)), (target, "successor secret\n")):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    result = rename.resolve_intent_path(old, repository_root=tmp_path)

    assert result.code == "tombstone"
    assert result.paths == (old, target)
    assert not hasattr(result, "content")
```

Scratch validation: `py_compile` passed; pytest collected red because the
planned module is absent. EXECUTE adds two inbound tombstones that re-point in
the same transaction, malformed tombstone values and no-follow path cases.

**Depends on:** T1

### T6 — The transaction and recovery model is recorded as a decision

**Tests:** `no stub (goal-based)`. The ADR exists, is `Accepted`, states the phase model,
what recovery may trust, and the rejected alternatives — including the five
mechanisms the predecessor tried and why each failed, since that is the
evidence the decision rests on. `spec.md` cites it in `Constrained by:`.

**Approach:** ADR-0134 is prepared and cited during PLAN. The owner accepts it
at the same gate as this spec and plan, before their substantive content locks.
T6 changes neither locked artifact; after T1 and T2 it verifies the implemented
transaction still conforms to ADR-0134 D1–D7 and records any mismatch as a
re-plan stop rather than amending the contract in flight.

**Depends on:** T1, T2, T3, T4, T5

### T7 — An operator can run a rename, and recover one, from an installed core pack

**Tests:** `no stub (goal-based and manual QA)`.
`packs/core/tests/skills/work-intake/test_intent_rename_installed_surface.py`
installs the real Core pack into a disposable repository through the existing
Codex repo-scope install route, asserts the installed artifact is
`.agents/skills/work-intake/scripts/intent_rename.py`, and invokes that file in
a subprocess exactly as the operator does:

```text
python3 .agents/skills/work-intake/scripts/intent_rename.py rename <source-path> <target-token>
python3 .agents/skills/work-intake/scripts/intent_rename.py recover <forward|back> <source-path> <target-token> <tombstone-date>
```

The first invocation proves one end-to-end rename. The test then supplies a
partial-state fixture produced by the transaction construction helper and
proves one recovery through the second installed CLI invocation; importing or
calling `run_intent_rename` or `recover_intent_rename` is not admissible proof
for AC-0025. Manual QA follows
`guides/product-engineering/how-to/rename-an-intent.md` through one rename and
one recovery using those same installed commands, and records the date,
installed artifact path, commands, fixed result codes and pass/fail outcome in
the `T7 installed-operator manual QA` section of
`notes/verification-ledger.md`.

**Approach:** The two `SKILL.md` statements that nothing renames an intent point
here instead, and the Core release entry lands in
`docs/product/changelog.md` under the released Core version. `packs/AGENTS.md`
requires the matching `pack.toml` and `.claude-plugin/plugin.json` version bumps
and an eval-harness update; they land in this task.

**Depends on:** T1, T2, T3, T4, T5, T6

## Changelog

- 2026-10-01 — spec scope re-approved by eugenelim. The only change since
  the 2026-09-30 approval is the ADR collision renumber from ADR-0131 to
  ADR-0134; no criterion, boundary or test changed.
- 2026-10-01 — build strategy re-approved by eugenelim. The only change
  since the 2026-09-30 approval is the same ADR-0131 to ADR-0134 renumber;
  T0 through T7 are unchanged.
- 2026-09-30 — spec scope approved by eugenelim after the measurement-led
  design, adversarial review and secure-design review returned clean.
- 2026-09-30 — build strategy approved by eugenelim; T0 remains the measured
  prerequisite and T1 through T7 are locked for execution.
- 2026-09-29 — completed T0 and designed the transaction from its measurements:
  a sealed bounded recovery record, independently re-derived write authority,
  preimage/postimage validation, hard-link identity for the successor and
  shared-lock claim, one locked-live registry mechanism, and exact PLAN stubs.
- 2026-09-29 — repaired the first pre-execute review: admitted only the two
  owned retained-link states, bounded the full JSON shape, made the locked
  registry edit conserve every citation, and ordered T2 after T1.
- 2026-09-29 — corrected the Core release-history destination after the second
  pre-execute review.
- 2026-09-29 — prepared and cited ADR-0134 before approval, aligned T3 behind
  the T1/T2 boundary, and corrected LLD task ownership after the third review.
- 2026-09-29 — removed the record's last byte-authority exception and added a
  durable cleanup marker that makes every no-seal recovery state unambiguous.
- 2026-09-29 — corrected the recovery-read anchor to the runtime-shipped Core
  sibling rather than the catalogue build package.
- 2026-09-29 — made the completion criterion distinguish non-registry bytes
  from the locked live registry edit, promoted dead-owner proof, and aligned
  one-hop tombstone target classification with the resolver criteria.
- 2026-09-29 — ordered the ADR conformance check after every clause-owning task
  and corrected the predecessor-history count before acceptance.
- 2026-09-29 — pinned T7's goal-based and manual proof to the installed Codex
  work-intake script and named the durable manual-QA evidence boundary.
- 2026-09-28 — cut from `intent-renumber-and-reissue` and drafted. Carries that
  slice's twelve transaction criteria unchanged, its measured failure modes,
  and its six unresolved security Blockers as design inputs.
