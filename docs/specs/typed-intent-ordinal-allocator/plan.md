# Plan: a typed allocator that refuses where the untyped one guesses

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `packs/governance-extras/.apm/skills/new-adr/scripts/next-ordinal.py:103` (`_PREFIX = re.compile(r"^(\d{4,})[-.]")` — the anchored pattern that returns `0001` on a typed directory), `:162` (`_remote_ordinals`, which unions records on `refs/remotes/origin/HEAD` — committed-and-pushed records absent from the working tree, *not* a peer's unpushed work, which ADR-0108:41 records as the limit of this whole approach; it returns an empty set when there is no remote to consult and degrades to the working tree on a timeout), `:213` (`duplicate_ordinals`, which refuses rather than reporting clean on a scan it could not complete), `:256` (`next_ordinal`); `packs/governance-extras/tests/skills/new-adr/test_next_ordinal.py:14-20` (load-by-path module loader and the local-Git fixture pattern this suite reuses); `packs/core/.apm/skills/work-intake/SKILL.md:329-340` (§ 6 *Delegate intent admission*, the named integration point) and `:60` (the public routing precedence that sends an explicit `intake-intent` request past § 6); `packs/core/.apm/skills/intake-intent/SKILL.md:100-107` (Procedure steps 3 and 5, the preserve-or-confirm step this slice amends) and `:195-212` (`## Boundaries`, which refuses shell access); `packs/core/.apm/skills/intake-intent/scripts/intent_renderer.py:66` (`repository_intent_target`, which composes `docs/product/intents/{slug}.md`) and `:171` (`admit_repository_intent`, which already accepts `slug` and `level`); `packs/core/.apm/skills/work-loop/scripts/file_safety.py:221` (`list_confined_regular_files`, the blessed confined listing) with `tests/roster/test_close_work_extraction_and_immediate_disposition.py:853-857` (the byte-identity pin every hand-maintained `packs/**` copy needs, per `packs/AGENTS.local.md:54-57`); `tests/AGENTS.md:27-42` (the three edits a new `tests/roster/` file obliges). Named uncertainty: the existing typed corpus was authored by hand, so the allocator's first real run must agree with numbers a human chose — T2's baseline assertion measures it rather than assuming it.

## Approach

The allocator is a new script because the existing one is not extensible into it: `_PREFIX` is anchored at position zero, so on `FEAT-0002-intent-graph-navigation.md` it does not match, and `next_ordinal` then returns `1` with exit 0 while `--check` prints "no duplicate ordinals" for a directory in which it saw nothing. Loosening that pattern to accept an optional prefix would change what `new-adr` and `new-rfc` allocate over their own untyped corpora, which is the one behaviour this slice must not touch. So: a second script, and a test that pins the two to the same answer on comparable inputs.

The shape carries over rather than being reinvented. `next-ordinal.py` already solved the hard parts — the `origin` union that widens the view past the working tree, and a `--check` mode that refuses rather than reporting clean on an incomplete scan. Three things change. The pattern matches the owner's typed filename contract instead of a bare digit run. The maximum is grouped per type token rather than per directory. And a *failed* remote query refuses instead of degrading, because a working-tree-only answer presented as authoritative is the plausible-but-wrong result the slice exists to stop; a directory with no remote to consult is a different case and allocates normally, since the working tree is then the complete available view.

Refusal is the design centre, not an edge case. Where the untyped script's fallback is `0001`, the typed one's is no ordinal at all — for a malformed in-namespace filename, for a scan it could not complete, and for an altitude the parent's table does not map. `intake-intent` already has the receiving shape: `admit_repository_intent` takes `slug` and composes the target from it, so an allocated ordinal is expressed as a prefixed slug and an unmapped level as the bare slug. No new capability is needed to receive either.

The integration covers two entry paths with two mechanisms, because they have two capability sets. `work-intake` § 6 already "passes the confirmed repository destination, and authority mode to `intake-intent`" and already declares `Bash`, so it allocates before that pass, on the destination it was going to supply anyway. The direct path at `SKILL.md:60` reaches `intake-intent` without a caller, and that skill's `## Boundaries` refuses a shell — so it cannot allocate and this slice does not grant it one. Its Procedure step 3 refuses instead: creating a mapped-level intent without an allocated ordinal stops and names the path that allocates, and a prefix supplied with the request is not accepted as proof, because the owner cannot check it against the working tree and `origin`. Preserving an existing path is untouched, prefixed or not, which is what the parent's forward-only guardrail means in practice and covers most of what the direct route is used for.

## Assumption trio

**Written** — `packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py` (new); `packs/core/.apm/skills/work-intake/scripts/file_safety.py` (new, byte-identical copy); `packs/core/.apm/skills/work-intake/SKILL.md` (§ 6); `packs/core/.apm/skills/intake-intent/SKILL.md` (one clause of Procedure step 3); both skills' `evals/evals.json` and `evals/eval_queries.json`; `packs/core/tests/skills/work-intake/test_intent_ordinal.py` (new); `packs/core/tests/skills/work-intake/test_work_intake.py`; `packs/core/tests/skills/intake-intent/test_intake_intent_manifest.py` (new); `tests/roster/test_typed_ordinal_collision_equivalence.py` (new); `tests/roster/test_close_work_extraction_and_immediate_disposition.py` (one added parity assertion); `.github/workflows/build-check.yml`; `tools/lint-ci-parity.py`; `packs/core/pack.toml`; `packs/core/.claude-plugin/plugin.json`; `docs/product/changelog.md`; `docs/specs/typed-intent-ordinal-allocator/notes/verification-ledger.md`.

**Generated, not hand-edited** — `.claude-plugin/marketplace.json` and the adapter projections under `packs/core/`, all written by `make build-self`.

**Read only, asserted against, never written** — `docs/product/intents/FEAT-0001-intent-identity-and-registration.md` (the owner's token table); every file under `docs/product/intents/` (the live-shape assertion); `packs/governance-extras/.apm/skills/new-adr/scripts/next-ordinal.py`.

**Explicitly unamended, and that is the evidence** — `packs/core/tests/skills/intake-intent/test_intake_intent.py`.

**Done is demonstrated by** — the new pack suite and the two roster tests green, `test_intake_intent.py` green unamended, and the four recorded admission sessions in the verification ledger.

**Not changing** — `next-ordinal.py` and its two suites; `intake-intent`'s `allowed-tools`, `## Boundaries` and every control in them; the existing corpus, since the parent intent's guardrail makes adoption forward-only, so an intent carrying no ordinal today keeps none and no file is renumbered.

**Tempted and declined:**

- *Generalise `next-ordinal.py` to handle both shapes.* Declined under rung 7 (minimum correct change preserving ownership and tests): it lives in `governance-extras`, serves two skills there, and widening its pattern changes what those skills allocate over untyped directories.
- *A shared cross-pack ordinal library.* Declined under rung 1 (skip an addition not genuinely needed): two callers in two packs with different matching rules is not a library, and a cross-pack import would put a `governance-extras` path on a `core` skill's load path.
- *A counter file or a retired-ordinal list.* Declined by an explicit requirement rather than a rung: AC-0003 forbids it, and ADR-0108's context records this repository colliding twice on a shared mutable counter across worktrees.
- *Reimplement confined directory listing.* Declined under rung 2 (reuse an adequate repository solution): `file_safety.list_confined_regular_files` is the blessed helper named in the root `AGENTS.md`, and `close-work` establishes the per-skill copy plus its byte-identity pin as this repository's carrying pattern.
- *Derive a token for an unmapped altitude.* Declined by the parent intent's own decision: the table is closed, and a derived token is exactly the plausible-but-wrong answer this slice exists to stop.
- *Grant `intake-intent` a shell so it can allocate on the direct path.* Declined by a trust-boundary control rather than a rung: its `## Boundaries` refuses shell, network and external-locator access for a skill that handles untrusted intent sources, and a refusal buys the same invariant at no capability cost.

## Constraints

- **Shipped pack content carries no internal-governance citations** (`packs/AGENTS.md`). The script and both skill bodies state their rules directly; the parent intent, ADR-0108 and ADR-0033 are cited in the spec and here, never in pack content.
- **A pack test may not read above its pack** (`tests/AGENTS.md:22-25`, enforced by `tools/test-lint-pack-test-boundary.py`), because pack tests ship with the pack. The core suite therefore runs on synthetic fixtures only, and every test that reads `docs/` or a second pack lives in `tests/roster/`.
- **A new `tests/roster/` file obliges three further edits** (`tests/AGENTS.md:27-42`): a step in `.github/workflows/build-check.yml` naming the file and placed **above** the bulk `pytest tests/ -q` step, because the job is fail-fast with no step-level `if:` and a named step below it never runs; a matching `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py` with the value `LOCAL("test-after-build-check")`; and a `.workspace-prune-protected.toml` entry only if the test names a `docs/specs/<slug>` path as a literal, which T2's does not.
- **A hand-maintained `packs/**` copy of `file_safety.py` is pinned byte-identical by a test** (`packs/AGENTS.local.md:54-57`). The pattern lives at `tests/roster/test_close_work_extraction_and_immediate_disposition.py:853-857`, which pins only the `close-work` copy; a third copy needs its own assertion beside it, or it silently diverges from the canonical helper with nothing red.
- **A non-cosmetic pack update also updates that pack's eval harness** (`packs/AGENTS.md:60`). Both changed skills already carry `evals/evals.json` and `evals/eval_queries.json`, so each gains coverage of its new behaviour.
- **Version bumps are patch-sized here** (`packs/AGENTS.md:43-47`): patch for changed content, minor for a new primitive. A script added inside an existing skill is changed content of that skill, not a new projected primitive, so this is a patch bump.
- **`Level` is an open set** (ADR-0033 D2) while the parent's token table is closed. An unmapped level is a normal, expected input with a defined outcome — no ordinal — not an error condition.
- **Adoption is forward-only**, owned by the parent intent's `## Guardrail` and the brief's renumber non-goal, with ADR-0108 D6 as the cited precedent rather than the governing decision. The allocator reads the existing corpus to compute a maximum; it never rewrites it.
- **Streams reconfigure to UTF-8 before the first print** (`packs/AGENTS.md`), as `next-ordinal.py:main` already does.

## Construction tests

**Unit, in the pack** — `packs/core/tests/skills/work-intake/test_intent_ordinal.py`, on synthetic fixtures only, because it ships with the pack.

**Integration, at the repository** — `tests/roster/test_typed_ordinal_collision_equivalence.py`. It is a roster test because it reads a second pack's script and the repository's own `docs/`, both of which a pack test may not reach. It asserts equivalence over **paired** typed and untyped fixtures, not over the real ADR/RFC corpora: a directory with no typed records is indistinguishable from a valid intent directory holding only legacy names, which AC-0001 requires to yield `0001`, so a real-corpus non-answer assertion would contradict the first-allocation criterion.

**Manual verification** — four sessions, each recorded in `notes/verification-ledger.md` with its invocation, its observed result, and its stop boundary. A unit test can prove the allocator returns `FEAT-0006`; only a session proves a skill asked it and passed the answer through. Each session stops at the first durable effect — the written file, or the refusal before any write — and the ledger states which arms were documented but not exercised.

## Durable-output map

No `## Durable Outputs` table in the spec, so nothing to mirror. Each task names the criteria it discharges.

## Tasks

### T1: The allocator — one maximum per type, and a refusal where there is no type

**Depends on:** none

**Mode:** TDD

**Tests:** the stub below is exact and materializes unchanged at `packs/core/tests/skills/work-intake/test_intent_ordinal.py` during EXECUTE. It compiles, and it earned its red from disposable scratch on 2026-09-20 against a deliberately-wrong skeleton (`token_for_level` → `None`, `classify` → `"outside"`, `next_typed_ordinal` → `1`, `main` → `0`): **15 failed, 7 passed**. The 7 are the cases whose expected value the degenerate skeleton happens to return; they are pinned by their siblings in the same parametrization rather than standing alone, and the split is recorded so a later reader does not mistake the stub for fully-discriminating on its own.

```python
"""Red stub for T1. Materialized unchanged at
packs/core/tests/skills/work-intake/test_intent_ordinal.py during EXECUTE."""

import importlib.util
import pathlib
import sys

import pytest

sys.dont_write_bytecode = True

_SCRIPTS = pathlib.Path(__file__).resolve().parents[3] / ".apm/skills/work-intake/scripts"
_SPEC = importlib.util.spec_from_file_location(
    "core_work_intake_intent_ordinal", _SCRIPTS / "intent_ordinal.py"
)
MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(MODULE)


def _snapshot(directory: pathlib.Path) -> set[tuple[str, int]]:
    """Name and size of every entry, so a write of any kind shows up."""
    return {(p.name, p.stat().st_size) for p in directory.rglob("*")}


def test_each_type_sequences_independently(tmp_path: pathlib.Path) -> None:
    for name in ("CAP-0001-a.md", "CAP-0002-b.md", "FEAT-0001-c.md"):
        (tmp_path / name).write_text("", encoding="utf-8")
    assert MODULE.next_typed_ordinal(tmp_path, "CAP") == 3  # AC-0001
    assert MODULE.next_typed_ordinal(tmp_path, "FEAT") == 2  # AC-0001


@pytest.mark.parametrize(
    ("level", "token"),
    [
        ("product-vision", "VISION"),
        ("product-strategy", "STRAT"),
        ("capability", "CAP"),
        ("feature", "FEAT"),
        ("initiative", None),
        (None, None),
        ("`feature`", None),
    ],
)
def test_the_level_lookup_is_an_exact_match(level: str | None, token: str | None) -> None:
    assert MODULE.token_for_level(level) == token  # AC-0001, AC-0002


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("FEAT-0001-x.md", "valid"),
        ("FEAT-0001.md", "malformed"),
        ("FEAT-0001.txt", "malformed"),
        ("FEAT-x.md", "malformed"),
        ("FEAT-12-y.md", "malformed"),
        ("FEAT-0001x.md", "malformed"),
        ("FEAT-0001", "malformed"),
        ("EPIC-0001-x.md", "outside"),
        ("legacy-slug.md", "outside"),
    ],
)
def test_the_filename_partition(name: str, expected: str) -> None:
    assert MODULE.classify(name) == expected  # AC-0004, AC-0013


def test_an_outside_name_is_skipped_and_a_malformed_one_is_fatal(
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "legacy-slug.md").write_text("", encoding="utf-8")
    assert MODULE.next_typed_ordinal(tmp_path, "FEAT") == 1  # AC-0001 first allocation
    (tmp_path / "FEAT-12-y.md").write_text("", encoding="utf-8")
    assert MODULE.next_typed_ordinal(tmp_path, "FEAT") is None  # AC-0004, AC-0010


def test_no_remote_is_not_a_failure(tmp_path: pathlib.Path) -> None:
    """tmp_path is no repository at all, which is the positive-fixture shape."""
    assert MODULE.next_typed_ordinal(tmp_path, "FEAT") == 1  # AC-0015


def test_allocation_writes_nothing(tmp_path: pathlib.Path) -> None:
    (tmp_path / "FEAT-0001-a.md").write_text("", encoding="utf-8")
    before = _snapshot(tmp_path)
    MODULE.next_typed_ordinal(tmp_path, "FEAT")
    assert _snapshot(tmp_path) == before  # AC-0003


def test_check_refuses_an_unreadable_directory(tmp_path: pathlib.Path) -> None:
    assert MODULE.main(["--check", str(tmp_path / "absent")]) == 1  # AC-0011


def test_check_has_both_halves(tmp_path: pathlib.Path) -> None:
    (tmp_path / "CAP-0001-a.md").write_text("", encoding="utf-8")
    (tmp_path / "FEAT-0001-b.md").write_text("", encoding="utf-8")
    assert MODULE.main(["--check", str(tmp_path)]) == 0  # AC-0012 cross-type
    (tmp_path / "FEAT-0001-c.md").write_text("", encoding="utf-8")
    assert MODULE.main(["--check", str(tmp_path)]) == 1  # AC-0012 same-type
```

Deferred to EXECUTE, as assertions added to this file rather than a rewrite of it: the local Git fixture for `origin` visibility and its unpushed-peer limit (AC-0005), the failing and timing-out remote queries (AC-0011), and the record-shaped symlink (AC-0011). Each needs a fixture the stub does not carry, and `references/tdd-stubs.md` admits a deferred assertion in an approved stub.

**Approach:**

- Match the owner's contract, not a prefix. Two patterns, so the classes cannot leave a gap: the introducer `^<TOKEN>-` decides in-or-out of the namespace, and the end-anchored shape `^<TOKEN>-\d{4,}-[^/]+\.md$` decides valid-or-malformed inside it. Both build their alternation from the mapping's own values, so the token set appears once in the module. Deriving malformed as "introducer and not shape" is what makes the partition exhaustive by construction; enumerating malformed shapes instead is how `FEAT-0001x.md` and `FEAT-0001` escaped an earlier draft.
- The anchored shape is narrower than `next-ordinal.py`'s `[-.]`, deliberately (AC-0013). Inheriting `[-.]` would count `FEAT-0001.md` and `FEAT-0001.txt`, letting a file the owner's contract does not admit raise the maximum.
- `token_for_level` is a dict lookup with an exact-match key, transcribing the parent intent's table rather than deciding it. The script states the mapping directly because shipped pack content carries no internal-governance citations, and a comment names the transcription so a future edit knows where the decision lives.
- The three filename classes are the load-bearing design choice, because most files in `docs/product/intents/` carry no typed prefix. Treating an unmatched name as an incomplete scan would make the live corpus unallocatable; treating a malformed typed name as merely uninteresting would let it vanish from duplicate checking. `classify` returns the class rather than a boolean, so a fourth case cannot fall through to a default.
- Separate a missing remote from a broken one (AC-0011, AC-0015). No repository, no remote, or no `refs/remotes/origin/HEAD` means the working tree is the complete available view and allocation proceeds — this is the shape of every positive fixture in the suite, so conflating the two would make the suite unsatisfiable. A query that *fails or times out* means the view is incomplete and unknowably so, and refuses. That is the one deliberate behavioural divergence from the script being modelled, and AC-0005's equivalence is scoped to fixtures where `origin` answers, so the two claims do not collide.
- Enumerate through `file_safety.list_confined_regular_files`, copied beside the script, so a record-shaped symlink is refused rather than counted. Carry `_remote_ordinals` over almost intact — the `GIT_*` redirect scrub, `--literal-pathspecs`, `-z`, and the root-relative pathspec run from the repository root. Each of those comments in the source records a defect already paid for once; only the timeout arm changes.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-intake/ -q` is green and `python3 -m agentbundle catalogue self-host --root . --check` passes.

**Touches:** packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py, packs/core/.apm/skills/work-intake/scripts/file_safety.py, packs/core/tests/skills/work-intake/test_intent_ordinal.py

### T2: Pinned to its owner and to the untyped allocator, and admitted to the roster

**Depends on:** T1

**Mode:** TDD

**Tests:** `no stub (implementation-discovered)` — the fixtures are two local Git repositories and a parse of the parent intent's Markdown table, and the exact shape of both is settled by writing them. The predicate: the module does not exist, the table's parse boundaries are not knowable from the artifact alone without reading its surrounding prose, and a stub written now would be rewritten rather than filled. Proof obligation discharged in the verification ledger at EXECUTE, recording the fixture shape actually built and the assertions it carries.

- Paired fixtures carrying the same logical ordinals in the two grammars — `0007-x.md` beside `FEAT-0007-x.md` — yield the same next ordinal from both scripts, so the shared `max + 1` and `origin`-union behaviour is pinned across them (AC-0005). Equality over a directory neither script can parse would be trivially true, which is why the fixtures are paired rather than shared.
- A record committed on `refs/remotes/origin/HEAD` and absent from the working tree raises the maximum; a record in a second, unpushed clone does not — asserted as the stated limit, so nobody later reads the union as peer-collision safety (AC-0005).
- The allocator's mapping and its parser's token namespace hold exactly the parent intent's table — keys and values, set equality in both directions (AC-0014). A one-way check would pass an implementation that added `epic → EPIC` or kept a token the owner removed.
- Every typed file in `docs/product/intents/` satisfies the anchored valid shape (AC-0013), enumerated at test time so the check keeps working as the corpus grows.
- Baseline: the next ordinal for each token in the parent's table is one above the highest live file of that type, computed from the directory rather than pinned to a literal (AC-0001). This is the named uncertainty made mechanical — the only check that the allocator agrees with numbers a human already chose.

**Approach:**

- Load both scripts by path under distinct module names, following `test_next_ordinal.py:14-20`. Do not put either `scripts/` directory on `sys.path`.
- Roster admission is three edits, not one file (`tests/AGENTS.md:27-42`), and they are part of this task rather than a follow-up: the named step in `build-check.yml` must sit **above** the bulk `pytest tests/ -q` step or it never runs, and `tools/lint-ci-parity.py` gains the matching `STEP_DISPOSITION` of `LOCAL("test-after-build-check")`. No `.workspace-prune-protected.toml` entry is needed, because this test names no `docs/specs/<slug>` literal.
- Add the `file_safety.py` byte-identity assertion for the new copy beside the existing `close-work` one at `tests/roster/test_close_work_extraction_and_immediate_disposition.py:853-857`. `packs/AGENTS.local.md:54-57` requires it for every hand-maintained `packs/**` copy; without it a source-side hardening fix never reaches this copy and nothing goes red.
- Run `ruff check .` after adding the file: the repository lint targets do not cover it (`tests/AGENTS.md:44-46`).

**Done when:** `python3 -m pytest tests/roster/test_typed_ordinal_collision_equivalence.py tests/roster/test_close_work_extraction_and_immediate_disposition.py -q` is green, `python3 tools/lint-ci-parity.py` passes, and `ruff check .` is clean.

**Touches:** tests/roster/test_typed_ordinal_collision_equivalence.py, tests/roster/test_close_work_extraction_and_immediate_disposition.py, .github/workflows/build-check.yml, tools/lint-ci-parity.py

### T3: Both entry paths, one without a shell

**Depends on:** T1

**Mode:** Goal-based check, plus Visual / manual QA for the four recorded sessions

**Tests:** `no stub (mode)` for the prose assertions; the sessions are manual QA.

- § 6 names the allocation step and its script, and states that the allocated ordinal is expressed as a prefixed slug in the confirmed repository destination it already passes to `intake-intent` (AC-0006).
- § 6 distinguishes the two refusal classes: an absent or unmapped level means the bare slug, and admission and registration proceed unchanged (AC-0007); an allocation, scan or parse failure while **creating** at a mapped level stops before any write or registration (AC-0010). One unprefixed fallback for both would write the very thing AC-0009 forbids.
- `intake-intent`'s Procedure step 3 states that **creating** at a mapped level requires an already-allocated ordinal in the confirmed destination, that a prefix supplied with the request is not accepted as proof of allocation, and that it derives none itself; lacking one it stops and names the path that allocates (AC-0009).
- Procedure step 3 states that an existing repository path is preserved whether or not it carries a prefix, so an existing unprefixed mapped-level intent is updated in place with no allocation and no refusal (AC-0009).
- A construction check over `intake-intent/SKILL.md` frontmatter and its `## Boundaries` block rejects shell, network and any new tool (AC-0008). The existing suite exercises the renderer and never opens `SKILL.md`, so it cannot carry this claim.
- `packs/core/tests/skills/intake-intent/test_intake_intent.py` passes unamended (AC-0008).
- Both skills' `evals/` cover the new behaviour: `work-intake` a mapped-level admission and an unmapped-level one, `intake-intent` the creation refusal and the existing-path preservation (`packs/AGENTS.md:60`).
- Four recorded sessions (AC-0006, AC-0007, AC-0009): through `work-intake`, a mapped level lands at `docs/product/intents/<TYPE>-NNNN-<slug>.md` and an unmapped level at `docs/product/intents/<slug>.md` with no partial write; direct to `intake-intent`, a new mapped-level request refuses — including one carrying an arbitrary `FEAT-9999-` prefix, refused on the same ground rather than trusted — and an existing unprefixed mapped-level intent is updated in place.

**Approach:**

- `work-intake`: one step before the existing delegation sentence at `SKILL.md:331-333`. It must not restate admission policy — § 6 already forbids this router from copying `intake-intent`'s template or certifying its result — and the allocation step is a destination computation, not an admission decision.
- `intake-intent`: one clause on Procedure step 3, and nothing else in the body. The owner cannot allocate — its `## Boundaries` refuses a shell and this slice does not move that line — so creation at a mapped level refuses, unconditionally on a supplied prefix. One rule, stated once: a prefix the owner cannot verify against the working tree and `origin` proves nothing, so accepting it would readmit the silent-wrong failure through a second door. The cost is real and bounded — direct `intake-intent` no longer creates a new mapped-level intent, and the refusal names `work-intake` as the one-step path that does — while every existing-path update is untouched, which is most of what the direct route is used for.
- AC-0008 needs two pieces of evidence, not one. `test_intake_intent.py` passing unamended shows admission behaviour is intact; it never opens `SKILL.md`, so it cannot show that no capability was added. The manifest check carries that half. That the slice's only body edit there is one clause of Procedure step 3 is a verification choice this plan owns, not part of the criterion.

**Done when:** the prose and manifest assertions pass, `test_intake_intent.py` is green unamended, both eval harnesses cover the new behaviour, and the four sessions are recorded in `notes/verification-ledger.md` with their stop boundaries.

**Touches:** packs/core/.apm/skills/work-intake/SKILL.md, packs/core/.apm/skills/intake-intent/SKILL.md, packs/core/.apm/skills/work-intake/evals/, packs/core/.apm/skills/intake-intent/evals/, packs/core/tests/skills/work-intake/test_work_intake.py, packs/core/tests/skills/intake-intent/test_intake_intent_manifest.py, docs/specs/typed-intent-ordinal-allocator/notes/verification-ledger.md

### T4: Release surface

**Depends on:** T1, T2, T3

**Mode:** Goal-based check

This task discharges no acceptance criterion and states so deliberately: it carries no observable outcome of its own, only the repository rails a pack-content change owes. Folding it into T1 or T3 would put a version bump inside a behavioural task and force the bump before the other task settled.

**Tests:**

- `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the same bumped version — **patch**, because a script added inside an existing skill is changed content of that skill rather than a new projected primitive (`packs/AGENTS.md:43-47`).
- `docs/product/changelog.md` has a `core` release heading matching that version, topmost among `core` headings, with a `### Highlights` bullet.
- `make build-self` regenerates `.claude-plugin/marketplace.json` and the adapter projections on a clean tree.

**Approach:**

- Bump last, after T1–T3 are settled, so one version covers all of them. Read the current `core` version at that moment rather than reserving one now — an unpushed bump collides silently with a peer session's.

**Done when:** `make lint-ruff lint-mypy` and `make build-self` pass on a clean tree.

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.md

## Rollout

Pack content only; adopters pick it up on the next install. New intents created through `work-intake` gain a typed prefix; existing files are untouched and existing references keep resolving. Two behaviour changes to flag in the changelog entry. An adopter whose intents carry no `Level`, or a level outside the parent's table, sees exactly today's behaviour — an unprefixed filename. An adopter who invokes `intake-intent` directly to create a new mapped-level intent now gets a refusal naming `work-intake`; updating an existing intent that way is unchanged.

## Risks

- **The allocator inherits the silent-wrong failure it was built to avoid.** A refusal that returns `0001`, or a `--check` that prints clean over a directory it never read, is the same defect in a new file. T1's refusal cases are the guard, and they assert the absence of a number rather than the presence of an error string.
- **The remote distinction collapses in either direction.** Refusing on a *missing* remote makes every positive fixture in the suite unsatisfiable; degrading on a *failed* query hands back the plausible-but-wrong ordinal. AC-0015 and AC-0011 fail on opposite errors, and T1 asserts both.
- **Equivalence asserted by construction.** A test that runs both scripts over a directory neither can parse agrees trivially. T2's paired fixtures are what make the agreement load-bearing.
- **The bypass reopens, or the refusal is over-applied.** `SKILL.md:60` routes an explicit `intake-intent` request past § 6, so an allocator wired only into § 6 is skipped there — AC-0009 is the guard, and T3's direct-path sessions are the only evidence that reaches it. The opposite error costs more: a refusal firing for an *unmapped* level, or for an existing-path update, would block admissions and edits that must proceed. T3's four sessions exercise a mapped refusal, an unmapped success, and an existing-path update for exactly that reason.
- **The integration proved only in prose.** Both skills are bodies, so T3's assertions establish the instruction, not the behaviour. The four recorded sessions are the only evidence that reaches the written filename, and they are observations rather than a suite.
- **A roster test that runs but attributes nothing.** A named step placed below the bulk `pytest tests/ -q` step in a fail-fast job never executes. T2 owns the placement and `tools/lint-ci-parity.py` is what catches the mismatch.

## Changelog

- 2026-09-20 — Adversarial review on the spec+plan pair returned 7 blockers and 5 concerns; all twelve are resolved and eight were repository mechanics this plan had not reached. The pivotal one: every positive fixture was an `origin`-less `tmp_path`, while AC-0011 made a missing `origin` a refusal — no implementation could pass both, so AC-0015 now separates a missing remote from a broken query. The rest: T1's stub is now exact, compiled and red-validated in scratch per `work-loop/SKILL.md:252`; T2 carries the three roster-admission edits from `tests/AGENTS.md:27-42` and the `file_safety.py` byte-identity pin from `packs/AGENTS.local.md:54-57`; T3 carries both skills' eval-harness updates per `packs/AGENTS.md:60` and states the supplied-prefix rule once instead of twice contradictorily; T4 is a patch bump, not minor, and says plainly that it discharges no criterion; the Approach summary's reversed `origin` and filename-class claims are corrected; the construction-test summary no longer describes the abandoned real-corpus design; T3 declares both its modes; and the scope inventory is one list separating written, generated, read-only and deliberately-unamended files.

- 2026-09-20 — Round 9: forward-only was attributed to ADR-0108 D6, which governs spec-directory identifiers. The parent intent's `## Guardrail` and the brief's renumber non-goal own the rule for intents and cite D6 only as precedent, so the attribution moved. The fixed corpus counts came out with it: the brief states that a measured count is evidence of scale and not the obligation, so every corpus claim is now derived at test time.
- 2026-09-20 — Round 8: the no-unprefixed-write invariant was universal and collided with forward-only adoption. Most live intents are unprefixed and sit at a mapped level, so a universal invariant would have made each of them either unwritable or a violation on its next edit. The invariant and AC-0010 are now scoped to creation, and the update-in-place case is stated and tested.
- 2026-09-20 — Round 7: three fixes. Validity was a prefix test inherited from `next-ordinal.py`'s `[-.]`, so a slugless `FEAT-0001.md` or an unanchored `FEAT-0001.txt` would have raised the maximum against the parent's `<TYPE>-NNNN-<slug>.md` contract — AC-0013 anchors it, and all 14 live typed files were checked against the narrower shape first. AC-0014 makes the mapping check bidirectional, since a one-way check would pass a parser that grew a token the owner never listed. AC-0008 dropped its edit-location and named-test clauses to the plan, keeping the criterion behavioural.
- 2026-09-20 — Round 6: the level-to-token table was copied into the spec under an ownership claim that traced to nothing. The parent intent's `## Boundary` has held it as an owner decision since 2026-09-18, and the brief says at `:71` that it is not restated. The spec now cites the owner and keeps only the matching behaviour, which is what this slice actually decides.
- 2026-09-20 — Round 5: four gaps, all in the contract rather than the design. The level-to-token mapping was never stated — ADR-0033 D2 grounds the four recognized `Level` values but maps none of them, so the table is now declared in the spec. AC-0004's classes were enumerated rather than derived, so `FEAT-0001x.md` and `FEAT-0001` fell outside all three; they are now complementary against one introducer. `origin` failures were uncovered by AC-0011, which would have let a Git timeout degrade to a working-tree-only ordinal — the exact named risk — so they refuse, diverging deliberately from `next-ordinal.py`. And AC-0012 adds the duplicate control's positive half: same-type duplicates fail, cross-type equal ordinals pass.
- 2026-09-20 — Round 4: the direct path's supplied-ordinal escape valve closed. The owner cannot check a handed-in `FEAT-9999-` against the working tree and `origin`, so accepting a prefix as proof of allocation was the same silent-wrong failure through a second door; a new mapped-level direct admission now refuses unconditionally, with existing-path updates explicitly unaffected. AC-0004's partition given an exact grammar with scan failures split out to AC-0011, and the ADR/RFC non-answer assertion dropped — it could not be distinguished from AC-0001's first allocation.
- 2026-09-20 — Round 3 cleared the ownership finding and reached the criteria. Four fixes: AC-0007's unprefixed fallback was reachable by an allocation failure on a mapped level, contradicting AC-0009, so AC-0010 splits the refusal classes; AC-0005 claimed the `origin` union catches an unpushed sibling, the opposite of what ADR-0108:41 records, and asserted an undefined equivalence, now defined over paired fixtures; AC-0004 had no parse domain, which would have made the unprefixed live intents unallocatable, so three filename classes are declared; AC-0008's evidence could not see a capability change, so a manifest check carries that half.
- 2026-09-20 — Round 2 held the ownership finding: making the bypass visible is not making the allocator reachable, since a confirmed missing ordinal still writes a mapped intent unprefixed. The direct path changed from confirm to refuse — it writes only a destination that already carries an ordinal and derives none — so AC-0001 is universal on both paths.
- 2026-09-20 — Shaping review found the allocator owned by the router rather than by admission. The premise held: `work-intake/SKILL.md:60` routes an explicit `intake-intent` request directly to the owner, bypassing § 6. Resolved by covering both paths with different mechanisms rather than by relocating the allocator — the owner declares no shell and this slice does not grant one — so T3 gained the direct-path arm and AC-0009, and AC-0008 moved from a whole-file diff to a capability assertion.
- 2026-09-20 — Authored. Integration re-pointed from `intake-intent` to `work-intake`: `work-intake` already supplies the confirmed repository destination and already declares `Bash`, so allocation needs no new capability and ADR-0098 D2 keeps `intake-intent` the owner of admission with its files unchanged. Acceptance criteria labelled per ADR-0108 and each bound to one verification group.
