# Plan: a typed allocator that refuses where the untyped one guesses

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `packs/governance-extras/.apm/skills/new-adr/scripts/next-ordinal.py:103` (`_PREFIX = re.compile(r"^(\d{4,})[-.]")` — the anchored pattern that returns `0001` on a typed directory), `:162` (`_remote_ordinals`, the `origin` union and its five-second timeout), `:213` (`duplicate_ordinals`, which refuses rather than reporting clean on a scan it could not complete), `:256` (`next_ordinal`); `packs/governance-extras/tests/skills/new-adr/test_next_ordinal.py:14-20` (load-by-path module loader and the local-Git fixture pattern this suite reuses); `packs/core/.apm/skills/work-intake/SKILL.md:329-340` (§ 6 *Delegate intent admission*, the named integration point); `packs/core/.apm/skills/intake-intent/scripts/intent_renderer.py:66` (`repository_intent_target`, which composes `docs/product/intents/{slug}.md`) and `:171` (`admit_repository_intent`, which already accepts `slug` and `level`); `packs/core/.apm/skills/work-loop/scripts/file_safety.py:221` (`list_confined_regular_files`, the blessed confined listing, already carried as a byte-identical per-skill copy in `close-work`). Named uncertainty: the existing typed corpus was authored by hand, so the allocator's first real run must agree with numbers a human chose — recorded as T2's baseline assertion rather than assumed.

## Approach

The allocator is a new script because the existing one is not extensible into it: `_PREFIX` is anchored at position zero, so on `FEAT-0002-intent-graph-navigation.md` it does not match, and `next_ordinal` then returns `1` with exit 0 while `--check` prints "no duplicate ordinals" for a directory in which it saw nothing. Loosening that pattern to accept an optional prefix would change what `new-adr` and `new-rfc` allocate over their own untyped corpora, which is the one behaviour this slice must not touch. So: a second script, and a test that pins the two to the same answer wherever the corpus is untyped.

The shape carries over rather than being reinvented. `next-ordinal.py` already solved the three hard parts — the `origin` union that catches an unpushed sibling, the timeout that says so instead of degrading silently, and a `--check` mode that refuses rather than reporting clean on an incomplete scan. The new script keeps all three and changes only what the pattern matches and how the maximum is grouped: one maximum per type token, not one for the directory.

Refusal is the design centre, not an edge case. Where the untyped script's fallback is `0001`, the typed one's fallback is no ordinal at all — for an unparseable filename, for an altitude the prefix table does not map, and for a `--check` scan it could not complete. `intake-intent` already has the receiving shape for that: `admit_repository_intent` takes `slug` and composes the target from it, so an allocated ordinal is expressed as a prefixed slug and a refusal is expressed as the bare slug. Nothing in `intake-intent` changes.

The integration is one step in `work-intake` § 6, which already "passes the confirmed repository destination, and authority mode to `intake-intent`" and already declares `Bash`. Allocation happens before that pass, on the destination `work-intake` was going to supply anyway.

## Assumption trio

- **Files touched.** New: `packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py`, a copy of `file_safety.py` beside it, `packs/core/tests/skills/work-intake/test_intent_ordinal.py`, `tests/roster/test_typed_ordinal_collision_equivalence.py`. Amended: `packs/core/.apm/skills/work-intake/SKILL.md` § 6, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`.
- **Done is demonstrated by.** The two new suites green, `packs/core/tests/skills/intake-intent/test_intake_intent.py` green unamended, and one recorded admission in the verification ledger showing a prefixed filename and a refused one written bare.
- **Not changing.** `next-ordinal.py` and its two suites; every file under `packs/core/.apm/skills/intake-intent/`; the existing typed corpus — ADR-0108 D6 is forward-only and no file is renumbered.

**Tempted and declined:**

- *Generalise `next-ordinal.py` to handle both shapes.* Declined under rung 7 (minimum correct change preserving ownership and tests): it lives in `governance-extras`, serves two skills there, and widening its pattern changes what those skills allocate over untyped directories.
- *A shared cross-pack ordinal library.* Declined under rung 1 (skip an addition not genuinely needed): two callers in two packs with different matching rules is not a library, and a cross-pack import would put a `governance-extras` path on a `core` skill's load path.
- *A counter file or a retired-ordinal list.* Declined by an explicit requirement rather than a rung: AC-0003 forbids it, and ADR-0108's context records this repository colliding twice on a shared mutable counter across worktrees.
- *Reimplement confined directory listing.* Declined under rung 2 (reuse an adequate repository solution): `file_safety.list_confined_regular_files` is the blessed helper named in the root `AGENTS.md`, and `close-work` establishes the per-skill copy as this pack's carrying pattern.
- *Derive a token for an unmapped altitude.* Declined by the spec: the prefix table is closed, and a derived token is exactly the plausible-but-wrong answer this slice exists to stop.

## Constraints

- **Shipped pack content carries no internal-governance citations** (`packs/AGENTS.md`). The script and § 6 state the rule directly; ADR-0108 and ADR-0033 are cited here and in the spec, not in pack content.
- **A pack test may not read above its pack**, because pack tests ship with the pack. So the core suite runs on synthetic fixtures only, and the collision-equivalence test that must read `docs/adr/`, `docs/rfc/` and a second pack's script lives in `tests/roster/`.
- **`Level` is an open set** (ADR-0033 D2) while the prefix table is closed. An unmapped level is therefore a normal, expected input with a defined outcome — no ordinal — not an error condition.
- **ADR-0108 D6 is forward-only.** The allocator reads the existing corpus to compute a maximum; it never rewrites it.
- **Every non-cosmetic `.apm/**` change bumps `pack.toml` and `.claude-plugin/plugin.json`** and earns a `changelog.md` release heading for `core`.
- **Streams reconfigure to UTF-8 before the first print** (`packs/AGENTS.md`), as `next-ordinal.py:main` already does.

## Construction tests

**Integration tests:** `tests/roster/test_typed_ordinal_collision_equivalence.py` loads both scripts by path and asserts equal answers over the real untyped corpora. It is a roster test, not a pack test, precisely because it reaches two packs and the repository's own `docs/`.

**Manual verification:** one admission session, recorded in `notes/verification-ledger.md` with the invocation and the resulting filename. A unit test can prove the allocator returns `FEAT-0003`; only a session proves `work-intake` asked it and passed the answer through.

## Durable-output map

No `## Durable Outputs` table in the spec, so nothing to mirror. Each task names the criteria it discharges.

## Tasks

### T1: The allocator — one maximum per type, and a refusal where there is no type

**Depends on:** none

**Mode:** TDD

**Tests:**

```python
# packs/core/tests/skills/work-intake/test_intent_ordinal.py
def test_each_type_sequences_independently(tmp_path):
    for name in ("CAP-0001-a.md", "CAP-0002-b.md", "FEAT-0001-c.md"):
        (tmp_path / name).write_text("", encoding="utf-8")
    assert MODULE.next_typed_ordinal(tmp_path, "CAP") == 3   # AC-0001
    assert MODULE.next_typed_ordinal(tmp_path, "FEAT") == 2   # AC-0001

def test_an_unmapped_level_gets_no_token(tmp_path):
    assert MODULE.token_for_level("portfolio") is None        # AC-0002
    assert MODULE.token_for_level(None) is None               # AC-0002
    assert MODULE.token_for_level("`feature`") is None        # AC-0004

def test_check_refuses_an_incomplete_scan(tmp_path):
    assert MODULE.main(["--check", str(tmp_path / "absent")]) == 1  # AC-0004

def test_allocation_writes_nothing(tmp_path):
    before = _snapshot(tmp_path)
    MODULE.next_typed_ordinal(tmp_path, "FEAT")
    assert _snapshot(tmp_path) == before                      # AC-0003
```

- A record-shaped symlink refuses in `--check`, as `next-ordinal.py:213` does (AC-0004).
- A five-digit typed prefix parses as itself, so `FEAT-12345-x.md` does not collide with `FEAT-1234-y.md` (AC-0001).
- The `origin` union is exercised in a local Git fixture: an unpushed sibling in the working tree and a committed record on `refs/remotes/origin/HEAD` both raise the maximum (AC-0005).
- A timeout on the Git call prints to stderr and allocates from the working tree alone, rather than degrading silently (AC-0005).

**Approach:**

- Match `^(?P<token>VISION|STRAT|CAP|FEAT)-(?P<ordinal>\d{4,})[-.]` and group maxima by token. Keep `next-ordinal.py`'s five-digit rule: the digit run parses whole, so a wider ordinal does not alias a narrower one.
- `token_for_level` is a dict lookup over the closed table with an exact-match key. It returns `None` for an absent, unmapped, or non-bare level — one backticked `feature` already exists in the corpus, and it is the live instance of the "plausible but unparsed" input AC-0004 names.
- Enumerate through `file_safety.list_confined_regular_files`, copied beside the script as `close-work` does, so a record-shaped symlink is refused rather than counted.
- Carry `_remote_ordinals` over intact — the `GIT_*` redirect scrub, `--literal-pathspecs`, `-z`, the root-relative pathspec run from the repository root, and the timeout that reports itself. Each of those comments in the source records a defect already paid for once.

**Done when:** the new pack suite is green, `packs/core/tests/skills/work-intake/` is green, and `python3 -m agentbundle catalogue self-host --root . --check` passes.

**Touches:** packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py, packs/core/.apm/skills/work-intake/scripts/file_safety.py, packs/core/tests/skills/work-intake/test_intent_ordinal.py

### T2: Pinned to the untyped allocator wherever the corpus is untyped

**Depends on:** T1

**Mode:** TDD

**Tests:**

- For `docs/adr/` and `docs/rfc/`, the typed allocator finds no typed records and returns no ordinal, while `next-ordinal.py` returns its own answer — the two do not contradict each other, because the typed one declines to answer (AC-0005).
- Over a fixture directory of untyped `NNNN-slug.md` records, the two scripts agree on the maximum found, so the shared parsing rule has not drifted (AC-0005).
- Baseline against the real intent corpus: the typed allocator's next ordinal for each of `VISION`, `STRAT`, `CAP` and `FEAT` is one above the highest hand-authored file of that type in `docs/product/intents/` (AC-0001).

**Approach:**

- Load both scripts by path under distinct module names, following `test_next_ordinal.py:14-20`. Do not put either `scripts/` directory on `sys.path`.
- The baseline assertion is the named uncertainty made mechanical: it is the only check that the allocator agrees with the numbers a human already chose, and it is expected to move as the corpus grows, so it is computed from the directory rather than pinned to a literal.

**Done when:** `python3 -m pytest tests/roster/test_typed_ordinal_collision_equivalence.py -q` is green.

**Touches:** tests/roster/test_typed_ordinal_collision_equivalence.py

### T3: `work-intake` § 6 allocates before it delegates

**Depends on:** T1

**Mode:** Goal-based check

**Tests:**

- § 6 names the allocation step and its script, and states that the allocated ordinal is expressed as a prefixed slug in the confirmed repository destination it already passes to `intake-intent` (AC-0006).
- § 6 states the refusal path explicitly: no ordinal means the bare slug, and admission and registration proceed unchanged (AC-0007).
- `packs/core/tests/skills/intake-intent/test_intake_intent.py` passes unamended, and `git diff --name-only` shows no file under `packs/core/.apm/skills/intake-intent/` (AC-0008).
- One recorded session: an intent admitted through `work-intake` lands at `docs/product/intents/FEAT-NNNN-<slug>.md`, and one whose level is unmapped lands at `docs/product/intents/<slug>.md` with no partial write (AC-0006, AC-0007).

**Approach:**

- One step, placed before the existing delegation sentence at `SKILL.md:331-333`. It must not restate admission policy: § 6's existing text already forbids this router from copying `intake-intent`'s template or certifying its result, and the allocation step is a destination computation, not an admission decision.
- The AC-0008 check is deliberately two-sided. The suite passing proves admission still works; the empty diff proves it was not made to work by amending the thing the suite measures.

**Done when:** the prose assertions pass, `test_intake_intent.py` is green unamended, and the session is recorded in `notes/verification-ledger.md`.

**Touches:** packs/core/.apm/skills/work-intake/SKILL.md, packs/core/tests/skills/work-intake/test_work_intake.py, docs/specs/typed-intent-ordinal-allocator/notes/verification-ledger.md

### T4: Release surface

**Depends on:** T1, T3

**Mode:** Goal-based check

**Tests:**

- `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the same bumped version — minor, because a new script in a skill is a new primitive.
- `docs/product/changelog.md` has a `core` release heading matching that version, topmost among `core` headings, with a `### Highlights` bullet.
- `make build-self` regenerates `.claude-plugin/marketplace.json`; `tests/roster/test_packaged_runtime_closure.py` confirms the new script's sibling import resolves inside the bundle.

**Approach:**

- Bump after T1 and T3 are settled, so one version covers both. Read the current `core` version at that moment rather than reserving one now — an unpushed bump collides silently with a peer session's.

**Done when:** `make lint-ruff lint-mypy` and `make build-self` pass on a clean tree.

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.md, .claude-plugin/marketplace.json

## Rollout

Pack content only; adopters pick it up on the next install. New intents admitted through `work-intake` gain a typed prefix; existing files are untouched and existing references keep resolving. An adopter whose intents carry no `Level`, or a level outside the closed table, sees exactly today's behaviour — an unprefixed filename.

## Risks

- **The allocator inherits the silent-wrong failure it was built to avoid.** A refusal that returns `0001`, or a `--check` that prints clean over a directory it never read, is the same defect in a new file. T1's refusal cases are the guard, and they assert the absence of a number rather than the presence of an error string.
- **Equivalence asserted by construction.** A test that runs both scripts over a directory neither can parse agrees trivially. T2's untyped fixture is what makes the agreement load-bearing; the real-corpus case is the weaker half and is stated as such.
- **The integration proved only in prose.** `work-intake` is a skill body, so T3's assertions establish the instruction, not the behaviour. The single recorded session is the only evidence that reaches the written filename, and it is one observation, not a suite.

## Changelog

- 2026-09-20 — Authored. Integration re-pointed from `intake-intent` to `work-intake`: `work-intake` already supplies the confirmed repository destination and already declares `Bash`, so allocation needs no new capability and ADR-0098 D2 keeps `intake-intent` the owner of admission with its files unchanged. Acceptance criteria labelled per ADR-0108 and each bound to one verification group.
