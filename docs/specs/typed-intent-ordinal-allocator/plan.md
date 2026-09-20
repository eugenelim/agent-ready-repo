# Plan: a typed allocator that refuses where the untyped one guesses

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `packs/governance-extras/.apm/skills/new-adr/scripts/next-ordinal.py:103` (`_PREFIX = re.compile(r"^(\d{4,})[-.]")` — the anchored pattern that returns `0001` on a typed directory), `:162` (`_remote_ordinals`, which unions records on `refs/remotes/origin/HEAD` — committed-and-pushed records absent from the working tree, *not* a peer's unpushed work, which ADR-0108:41 records as the limit of this whole approach), `:213` (`duplicate_ordinals`, which refuses rather than reporting clean on a scan it could not complete), `:256` (`next_ordinal`); `packs/governance-extras/tests/skills/new-adr/test_next_ordinal.py:14-20` (load-by-path module loader and the local-Git fixture pattern this suite reuses); `packs/core/.apm/skills/work-intake/SKILL.md:329-340` (§ 6 *Delegate intent admission*, the named integration point); `packs/core/.apm/skills/intake-intent/scripts/intent_renderer.py:66` (`repository_intent_target`, which composes `docs/product/intents/{slug}.md`) and `:171` (`admit_repository_intent`, which already accepts `slug` and `level`); `packs/core/.apm/skills/work-loop/scripts/file_safety.py:221` (`list_confined_regular_files`, the blessed confined listing, already carried as a byte-identical per-skill copy in `close-work`). Named uncertainty: the existing typed corpus was authored by hand, so the allocator's first real run must agree with numbers a human chose — recorded as T2's baseline assertion rather than assumed.

## Approach

The allocator is a new script because the existing one is not extensible into it: `_PREFIX` is anchored at position zero, so on `FEAT-0002-intent-graph-navigation.md` it does not match, and `next_ordinal` then returns `1` with exit 0 while `--check` prints "no duplicate ordinals" for a directory in which it saw nothing. Loosening that pattern to accept an optional prefix would change what `new-adr` and `new-rfc` allocate over their own untyped corpora, which is the one behaviour this slice must not touch. So: a second script, and a test that pins the two to the same answer wherever the corpus is untyped.

The shape carries over rather than being reinvented. `next-ordinal.py` already solved the three hard parts — the `origin` union that catches an unpushed sibling, the timeout that says so instead of degrading silently, and a `--check` mode that refuses rather than reporting clean on an incomplete scan. The new script keeps all three and changes only what the pattern matches and how the maximum is grouped: one maximum per type token, not one for the directory.

Refusal is the design centre, not an edge case. Where the untyped script's fallback is `0001`, the typed one's fallback is no ordinal at all — for an unparseable filename, for an altitude the prefix table does not map, and for a `--check` scan it could not complete. `intake-intent` already has the receiving shape for that: `admit_repository_intent` takes `slug` and composes the target from it, so an allocated ordinal is expressed as a prefixed slug and a refusal is expressed as the bare slug. No new capability is needed to receive either.

The integration covers two entry paths with two mechanisms, because they have two capability sets. `work-intake` § 6 already "passes the confirmed repository destination, and authority mode to `intake-intent`" and already declares `Bash`, so it allocates before that pass, on the destination it was going to supply anyway. The direct path at `work-intake/SKILL.md:60` reaches `intake-intent` without a caller, and that skill's `## Boundaries` refuses a shell — so it cannot allocate and this slice does not grant it one. Its Procedure step 3 instead refuses: for a mapped level it writes only a destination that already carries an ordinal, and otherwise stops and names the path that allocates. Refusing needs no capability at all, and it is the only answer that keeps AC-0001 universal — deriving an ordinal prompt-only would give the owner a number it cannot check against `origin`, which is the failure the whole slice is built against.

## Assumption trio

- **Files touched.** New: `packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py`, a copy of `file_safety.py` beside it, `packs/core/tests/skills/work-intake/test_intent_ordinal.py`, `tests/roster/test_typed_ordinal_collision_equivalence.py`. Amended: `packs/core/.apm/skills/work-intake/SKILL.md` § 6, one clause of `packs/core/.apm/skills/intake-intent/SKILL.md` Procedure step 3, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`.
- **Done is demonstrated by.** The two new suites green, `packs/core/tests/skills/intake-intent/test_intake_intent.py` green unamended, and one recorded admission in the verification ledger showing a prefixed filename and a refused one written bare.
- **Not changing.** `next-ordinal.py` and its two suites; `intake-intent`'s `allowed-tools`, `## Boundaries` and every control in them; the existing corpus — ADR-0108 D6 is forward-only, so the 133 unprefixed intents stay unprefixed and no file is renumbered.

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
    assert MODULE.token_for_level("`feature`") is None        # AC-0002

def test_the_three_filename_classes(tmp_path):
    for name, cls in (("FEAT-0001-x.md", "valid"), ("FEAT-0001.md", "valid"),
                      ("FEAT-x.md", "malformed"), ("FEAT-12-y.md", "malformed"),
                      ("FEAT-0001x.md", "malformed"), ("FEAT-0001", "malformed"),
                      ("EPIC-0001-x.md", "outside"), ("legacy-slug.md", "outside")):
        assert MODULE.classify(name) == cls                   # AC-0004
    (tmp_path / "legacy-slug.md").write_text("", encoding="utf-8")
    assert MODULE.next_typed_ordinal(tmp_path, "FEAT") == 1   # skipped; first allocation
    (tmp_path / "FEAT-12-y.md").write_text("", encoding="utf-8")
    assert MODULE.next_typed_ordinal(tmp_path, "FEAT") is None  # AC-0004, AC-0010

def test_check_refuses_an_unreadable_directory(tmp_path):
    assert MODULE.main(["--check", str(tmp_path / "absent")]) == 1  # AC-0004

def test_allocation_writes_nothing(tmp_path):
    before = _snapshot(tmp_path)
    MODULE.next_typed_ordinal(tmp_path, "FEAT")
    assert _snapshot(tmp_path) == before                      # AC-0003
```

- Scan failures refuse rather than counting partially. Local: a missing directory, an unreadable entry, a record-shaped symlink, as `next-ordinal.py:213` does. Remote: a missing `origin` reference, a failing Git query, and an induced timeout — asserted explicitly, because this is where the behaviour diverges from the script being modelled (AC-0011).
- `--check` fails on two `FEAT-0001` records and passes on `CAP-0001` beside `FEAT-0001`, so the duplicate control has both halves and cannot pass by rejecting everything (AC-0012).
- A five-digit typed prefix parses as itself, so `FEAT-12345-x.md` does not collide with `FEAT-1234-y.md` (AC-0001).
- The `origin` union is exercised in a local Git fixture: a record committed on `refs/remotes/origin/HEAD` and absent from the working tree raises the maximum. A record in a second, unpushed clone does not — asserted as the stated limit, so nobody later reads the union as peer-collision safety (AC-0005).
- One case per recognized `Level` confirms the table maps it to its intended token, and three unmapped inputs — an intervening altitude, an absent field, a decorated `` `feature` `` — map to nothing (AC-0001, AC-0002).

**Approach:**

- Match `^(?P<token>VISION|STRAT|CAP|FEAT)-(?P<ordinal>\d{4,})[-.]` and group maxima by token. Keep `next-ordinal.py`'s five-digit rule: the digit run parses whole, so a wider ordinal does not alias a narrower one.
- `token_for_level` is a dict lookup over the closed table with an exact-match key. It returns `None` for an absent, unmapped, or non-bare level — one backticked `feature` already exists in the corpus, and it is the live instance of an unmapped level, which admits unprefixed under AC-0002.
- The three filename classes are the load-bearing design choice, because 133 of the 141 files in `docs/product/intents/` carry no typed prefix. Treating an unmatched name as an incomplete scan would make the live corpus unallocatable; treating a malformed typed name the same way would let it vanish from duplicate checking. Two patterns, not three, so the classes cannot leave a gap: the introducer `^(VISION|STRAT|CAP|FEAT)-` decides in-or-out of the namespace, and the full grammar `^(VISION|STRAT|CAP|FEAT)-(\d{4,})[-.]` decides valid-or-malformed inside it. Deriving malformed as "introducer and not grammar" is what makes the partition exhaustive by construction; enumerating malformed shapes instead is how `FEAT-0001x.md` and `FEAT-0001` escaped an earlier draft. `EPIC-0001-x.md` is outside, not malformed, because `EPIC` is not in the closed table. `classify` returns the class rather than a boolean, so a fourth case cannot fall through to a default.
- Scan failures are separate from every class and refuse (AC-0011), including the remote half. `next-ordinal.py:_git_output` degrades to a working-tree-only answer on a timeout and says so on stderr; this allocator refuses instead, because a working-tree-only ordinal is precisely the plausible-but-wrong answer the slice exists to stop. That is the one deliberate behavioural divergence from the script this one is modelled on, and AC-0005's equivalence is scoped to the fixtures where `origin` answers, so the two claims do not collide.
- Enumerate through `file_safety.list_confined_regular_files`, copied beside the script as `close-work` does, so a record-shaped symlink is refused rather than counted.
- Carry `_remote_ordinals` over almost intact — the `GIT_*` redirect scrub, `--literal-pathspecs`, `-z`, and the root-relative pathspec run from the repository root. Each of those comments in the source records a defect already paid for once. The one change is the timeout arm: it refuses rather than returning `None` to a caller that then allocates anyway.

**Done when:** the new pack suite is green, `packs/core/tests/skills/work-intake/` is green, and `python3 -m agentbundle catalogue self-host --root . --check` passes.

**Touches:** packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py, packs/core/.apm/skills/work-intake/scripts/file_safety.py, packs/core/tests/skills/work-intake/test_intent_ordinal.py

### T2: Pinned to the untyped allocator wherever the corpus is untyped

**Depends on:** T1

**Mode:** TDD

**Tests:**

- Paired fixtures carrying the same logical ordinals in the two grammars — `0007-x.md` beside `FEAT-0007-x.md` — yield the same next ordinal from both scripts, so the shared `max + 1` and `origin`-union behaviour is pinned across them (AC-0005). Equality over a directory neither script can parse would be trivially true, which is why the fixtures are paired rather than shared.
- The real `docs/adr/` and `docs/rfc/` corpora are deliberately not asserted against. A directory with no typed records is indistinguishable from a valid intent directory holding only legacy names, and AC-0001 requires that one to yield `0001` — so a "returns nothing here" assertion would contradict the first-allocation criterion.
- Baseline against the real intent corpus: the typed allocator's next ordinal for each of `VISION`, `STRAT`, `CAP` and `FEAT` is one above the highest hand-authored file of that type in `docs/product/intents/` (AC-0001).

**Approach:**

- Load both scripts by path under distinct module names, following `test_next_ordinal.py:14-20`. Do not put either `scripts/` directory on `sys.path`.
- The baseline assertion is the named uncertainty made mechanical: it is the only check that the allocator agrees with the numbers a human already chose, and it is expected to move as the corpus grows, so it is computed from the directory rather than pinned to a literal.

**Done when:** `python3 -m pytest tests/roster/test_typed_ordinal_collision_equivalence.py -q` is green.

**Touches:** tests/roster/test_typed_ordinal_collision_equivalence.py

### T3: both entry paths, one without a shell

**Depends on:** T1

**Mode:** Goal-based check

**Tests:**

- § 6 names the allocation step and its script, and states that the allocated ordinal is expressed as a prefixed slug in the confirmed repository destination it already passes to `intake-intent` (AC-0006).
- § 6 distinguishes the two refusal classes: an absent or unmapped level means the bare slug, and admission and registration proceed unchanged (AC-0007); an allocation, scan or parse failure on a *mapped* level stops before any write or registration (AC-0010). One unprefixed fallback for both would write the very thing AC-0009 forbids.
- `intake-intent`'s Procedure step 3 states that for a mapped level it writes only a destination already carrying an ordinal, stops with a named refusal otherwise, and derives none itself (AC-0009).
- A construction check over `intake-intent/SKILL.md` frontmatter and its `## Boundaries` block rejects shell, network and any new tool, and asserts Procedure step 3 is the only changed text in the skill. The existing suite cannot see the manifest, so it cannot carry this claim (AC-0008).
- `packs/core/tests/skills/intake-intent/test_intake_intent.py` passes unamended (AC-0008).
- One recorded session per path: an intent admitted through `work-intake` lands at `docs/product/intents/FEAT-NNNN-<slug>.md`; one whose level is unmapped lands at `docs/product/intents/<slug>.md` with no partial write; a new direct `intake-intent` request with a mapped level refuses, writing nothing and naming the path that allocates; and the same request carrying an arbitrary `FEAT-9999-` prefix is refused too, not trusted (AC-0006, AC-0007, AC-0009).
- An existing prefixed intent is still updated in place through the direct path, so the refusal covers new admissions only (AC-0009).

**Approach:**

- `work-intake`: one step before the existing delegation sentence at `SKILL.md:331-333`. It must not restate admission policy — § 6 already forbids this router from copying `intake-intent`'s template or certifying its result — and the allocation step is a destination computation, not an admission decision.
- `intake-intent`: one clause on Procedure step 3, and nothing else. The owner cannot allocate — its `## Boundaries` refuses a shell and this slice does not move that line, because granting `Bash` to the skill handling untrusted intent sources costs more than the identity it buys. So a new mapped-level direct admission refuses outright. It does not accept a supplied prefix either: unverifiable against the working tree and `origin`, a prefix would be proof of nothing and would readmit the silent-wrong failure through a second door. The cost is real and bounded — direct `intake-intent` no longer admits a new mapped-level intent, and the refusal names `work-intake` as the one-step path that does. Existing-path updates are untouched, which is most of what the direct route is used for.
- AC-0008 needs two pieces of evidence, not one. `test_intake_intent.py` passing unamended shows admission behaviour is intact; it exercises the renderer and never opens `SKILL.md`, so it cannot show that no capability was added. The manifest check is what carries that half.

**Done when:** the prose assertions pass, `test_intake_intent.py` is green unamended, and the session is recorded in `notes/verification-ledger.md`.

**Touches:** packs/core/.apm/skills/work-intake/SKILL.md, packs/core/.apm/skills/intake-intent/SKILL.md, packs/core/tests/skills/work-intake/test_work_intake.py, packs/core/tests/skills/intake-intent/test_intake_intent.py, docs/specs/typed-intent-ordinal-allocator/notes/verification-ledger.md

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
- **The bypass reopens, or the refusal is over-applied.** `work-intake/SKILL.md:60` routes an explicit `intake-intent` request past § 6, so an allocator wired only into § 6 is skipped there — AC-0009 is the guard, and the direct-path session in T3 is the only evidence that reaches it. The opposite error costs more: a refusal that fires for an *unmapped* level would block admissions that are meant to proceed unprefixed, so T3's session pair must exercise a mapped refusal and an unmapped success, not just the first.
- **The integration proved only in prose.** `work-intake` is a skill body, so T3's assertions establish the instruction, not the behaviour. The single recorded session is the only evidence that reaches the written filename, and it is one observation, not a suite.

## Changelog

- 2026-09-20 — Round 5: four gaps, all in the contract rather than the design. The level-to-token mapping was never stated — ADR-0033 D2 grounds the four recognized `Level` values but maps none of them, so the table is now declared in the spec. AC-0004's classes were enumerated rather than derived, so `FEAT-0001x.md` and `FEAT-0001` fell outside all three; they are now complementary against one introducer. `origin` failures were uncovered by AC-0011, which would have let a Git timeout degrade to a working-tree-only ordinal — the exact named risk — so they refuse, diverging deliberately from `next-ordinal.py`. And AC-0012 adds the duplicate control's positive half: same-type duplicates fail, cross-type equal ordinals pass.
- 2026-09-20 — Round 4: the direct path's supplied-ordinal escape valve closed. The owner cannot check a handed-in `FEAT-9999-` against the working tree and `origin`, so accepting a prefix as proof of allocation was the same silent-wrong failure through a second door; a new mapped-level direct admission now refuses unconditionally, with existing-path updates explicitly unaffected. AC-0004's partition given an exact grammar with scan failures split out to AC-0011, and the ADR/RFC non-answer assertion dropped — it could not be distinguished from AC-0001's first allocation.
- 2026-09-20 — Round 3 cleared the ownership finding and reached the criteria. Four fixes: AC-0007's unprefixed fallback was reachable by an allocation failure on a mapped level, contradicting AC-0009, so AC-0010 splits the refusal classes; AC-0005 claimed the `origin` union catches an unpushed sibling, the opposite of what ADR-0108:41 records, and asserted an undefined equivalence, now defined over paired fixtures; AC-0004 had no parse domain, which would have made the 133 unprefixed live intents unallocatable, so three filename classes are declared; AC-0008's evidence could not see a capability change, so a manifest check carries that half.
- 2026-09-20 — Round 2 held the ownership finding: making the bypass visible is not making the allocator reachable, since a confirmed missing ordinal still writes a mapped intent unprefixed. The direct path changed from confirm to refuse — it writes only a destination that already carries an ordinal and derives none — so AC-0001 is universal on both paths.
- 2026-09-20 — Shaping review found the allocator owned by the router rather than by admission. The premise held: `work-intake/SKILL.md:60` routes an explicit `intake-intent` request directly to the owner, bypassing § 6. Resolved by covering both paths with different mechanisms rather than by relocating the allocator — the owner declares no shell and this slice does not grant one — so T3 gained the direct-path arm and AC-0009, and AC-0008 moved from a whole-file diff to a capability assertion.
- 2026-09-20 — Authored. Integration re-pointed from `intake-intent` to `work-intake`: `work-intake` already supplies the confirmed repository destination and already declares `Bash`, so allocation needs no new capability and ADR-0098 D2 keeps `intake-intent` the owner of admission with its files unchanged. Acceptance criteria labelled per ADR-0108 and each bound to one verification group.
