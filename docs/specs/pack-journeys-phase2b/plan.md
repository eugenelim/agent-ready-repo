# Plan: pack-journeys-phase2b

- **Status:** Drafting

## Task list

### T0 — Extend lint-journey-contract.py to accept State label
**Files:** `tools/lint-journey-contract.py`
**Mode:** Goal-based
**Depends on:** none

Add `"State": 5` to `FIXED_RANK` dict. `State` is optional (rank 5, after Output).
`Output` remains required. Legacy files without `**State:**` continue to pass; files
with it now pass too. No self-test changes needed (existing fixtures have no State).

Done when: `python tools/lint-journey-contract.py` exits 0 on a file with `**State:** read-only`.

---

### T1 — Validator (TDD)
**Files:** `tools/lint-pack-journeys.py`, `tools/test-lint-pack-journeys.py`
**Mode:** TDD
**Depends on:** none

Red stubs first, then implement the tool:

Tests:
- `test_valid_journey_exits_0` — minimal valid JOURNEY.md → exit 0
- `test_journey_id_differs_from_pack_name_valid` — journey_id ≠ pack dir name → exit 0
- `test_missing_journey_id` — no `journey_id` → exit 1
- `test_invalid_state_in_stage` — `**State:** bogus` → exit 1
- `test_invalid_start_state` — `start_state: bogus` in frontmatter → exit 1
- `test_invalid_end_state` — `end_state: bogus` in frontmatter → exit 1
- `test_nonexistent_skill` — skill name not in `.apm/skills/` → exit 1
- `test_skill_count_mismatch` — 2 listed, 1 in pack → exit 1
- `test_duplicate_journey_id` — two packs with same journey_id → exit 1
- `test_dual_ownership_same_slug` — pack-local + non-generated central same slug → exit 1
- `test_dual_ownership_same_pack_diff_slug` — pack-local + non-generated central same
  pack field, different slug → exit 1
- `test_generated_central_not_dual` — pack-local + central with `generated: true` → exit 0
- `test_write_stage_missing_decide` — `**State:** confirmed-write` without `**You decide:**` → exit 1
- `test_decision_required_missing_decide` — `**State:** decision-required` without decide → exit 1
- `test_missing_output_label` — stage with no `**Output:**` → exit 1

Approach:
- Fixture mode: `LPJ_PACKS_DIR` and `LPJ_JOURNEY_DIR` env vars → temp dirs
- No PyYAML dependency; parse frontmatter with regex (same pattern as lint-journey-contract.py)
- `STATE_VOCAB`, `WRITE_STATES` as module-level frozensets
- Skill dir check via `pathlib`

Done when: `python tools/test-lint-pack-journeys.py` exits 0.

---

### T2 — Astro schema extension
**Files:** `web/src/content.config.ts`
**Mode:** Goal-based
**Depends on:** none

Add optional fields to the `journeys` collection schema:
```typescript
journey_id: z.string().optional(),
start_state: z.string().optional(),
end_state: z.string().optional(),
generated: z.boolean().optional(),
```

Done when: `npm run build --prefix web` succeeds with existing journey files.

---

### T3 — Sync in build-site.py with --journeys-only flag
**Files:** `tools/build-site.py`
**Mode:** Goal-based
**Depends on:** none

Changes:
1. Add `sync_pack_journeys(packs_dir, journey_dir, dry_run=False) -> int`:
   - Glob `packs_dir.glob("*/JOURNEY.md")` sorted
   - Parse frontmatter (minimal regex): extract `journey_id` and `pack`
   - If `journey_id` missing → print error, sys.exit(1)
   - Dual-ownership check (same-slug): if target exists without `generated: true` → error, exit 1
   - Same-pack check (different-slug): scan `journey_dir/*.md` for any non-generated
     file whose `pack:` field equals the source pack → error, exit 1
   - Inject `generated: true` after the opening `---` in frontmatter (or update if present)
   - Write target file; print sync line
   - Return count

2. Add `--journeys-only` argument to `main()`'s `ArgumentParser`:
   - When `--journeys-only` is set, call `sync_pack_journeys()` and return immediately
   - Skip all other aggregation (no tokens check, no pack READMEs, no guides mirror, etc.)

3. Call `sync_pack_journeys()` from the normal `main()` path too (after `build_pack_index()`):
   ```python
   print("build-site: syncing pack journeys …")
   n = sync_pack_journeys(packs_dir, REPO_ROOT / "web/src/content/journeys", dry_run=args.dry_run)
   print(f"  {n} pack-local JOURNEY.md files synced")
   ```

Done when: `python tools/build-site.py --journeys-only --dry-run` shows the sync step
(verified via fixture or dry-run; real generation requires T7's git rm first, since the
legacy file without `generated: true` triggers the dual-ownership guard).

---

### T4 — Pre-PR gate wiring and ordering
**Files:** `tools/catalogue/pre_pr_catalogue.py`
**Mode:** Goal-based
**Depends on:** T1, T3

Three additions (in order):

1. Run journey sync before parity/contract lints:
   ```python
   _run("pack-journey sync", [py, "tools/build-site.py", "--journeys-only"])
   ```
   Insert immediately before the `web-journey parity` `_run` call.

2. Add pack-journey lint and self-test (after `web-journey parity self-test`):
   ```python
   _run("pack-journey lint", [py, "tools/lint-pack-journeys.py"])
   _run("pack-journey lint self-test", [py, "tools/test-lint-pack-journeys.py"])
   ```

3. Add journey-contract lint and self-test (alongside or after step 2):
   ```python
   _run("journey-contract lint", [py, "tools/lint-journey-contract.py"])
   _run("journey-contract lint self-test", [py, "tools/test-lint-journey-contract.py"])
   ```

Done when: `make pre-pr` passes; zero JOURNEY.md files is a valid no-op state;
new gates appear in pre-pr output.

---

### T5 — Pilot JOURNEY.md
**Files:** `packs/product-documentation/JOURNEY.md`
**Mode:** TDD (lint-pack-journeys.py must pass)
**Depends on:** T1

Migrate from `web/src/content/journeys/product-documentation.md` with additions:
- Prepend `journey_id: product-documentation` as first frontmatter field
- Add `start_state: read-only` and `end_state: confirmed-write`
- Add `**State:**` after `**Output:**` in each stage:
  - Stage 1 "Describe the documentation goal": `**State:** read-only`
  - Stage 2 "Draft the artifact": `**State:** draft`
  - Stage 3 "Review and finalize": `**State:** confirmed-write`

Stage 3 already has `**You decide:**` (gate G-review) — satisfies write-state boundary.

Done when: `python tools/lint-pack-journeys.py` exits 0 on the file (with LPJ_PACKS_DIR
pointing at the real packs/ dir).

---

### T6 — pages.yml — sync before web build
**Files:** `.github/workflows/pages.yml`
**Mode:** Goal-based
**Depends on:** T3

Add a Python setup step and journey-sync step before "Build Astro marketing site":
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.11"

- name: Sync pack journeys
  run: python tools/build-site.py --journeys-only
```

Insert before "Build Astro marketing site". No existing Python setup step is in the
job — the runner currently relies on the pre-installed interpreter for the later
"Aggregate content" step. Adding `actions/setup-python@v5` (Python 3.11) here covers
both this sync step and the later aggregation step. The `--journeys-only` flag is fast
(seconds, no Node dependency).

Done when: pages.yml has the sync step before the web npm build; the step exits 0 with
zero JOURNEY.md files.

---

### T7 — Legacy file removal and gitignore
**Files:** `web/src/content/journeys/product-documentation.md` (deleted),
           `web/src/content/journeys/.gitignore` (new)
**Mode:** Goal-based
**Depends on:** T3, T5

1. `git rm web/src/content/journeys/product-documentation.md`
2. Create `web/src/content/journeys/.gitignore`:
   ```
   # Generated from packs/*/JOURNEY.md by tools/build-site.py --journeys-only.
   # Edit packs/{pack}/JOURNEY.md — not these generated files.
   product-documentation.md
   ```
3. Run `python tools/build-site.py --journeys-only` → confirms file generated
4. `git status --short` confirms: legacy file deleted (D), generated file untracked
   (suppressed by .gitignore)

Done when: legacy file absent from git; `.gitignore` present; generated file exists
on disk; `python tools/lint-journey-contract.py` still exits 0.

---

### T8 — Internal maintainer how-to guide
**Files:** `guides/_shared/how-to/pack-journey-authoring.md` (new)
**Mode:** Goal-based
**Depends on:** T1, T5

Sections to document:
1. **When a pack needs a JOURNEY.md** (six criteria + when NOT required)
2. **Journey-level frontmatter contract** (all required and optional fields)
3. **Stage contract** (label set, order, State label requirement)
4. **State vocabulary** (table: 9 values + descriptions + which require You decide)
5. **Skill reference validation** (lint checks .apm/skills/ existence + count)
6. **Route preservation** (journey_id = URL slug; must match legacy stem being retired)
7. **Installation exclusion** (JOURNEY.md not read by agentbundle install; no config needed)
8. **Migration procedure** (step-by-step):
   a. Choose `journey_id` equal to the legacy file stem
   b. Create `packs/{pack}/JOURNEY.md` with all fields + State labels
   c. `python tools/lint-pack-journeys.py` to validate
   d. `git rm web/src/content/journeys/{slug}.md`
   e. Add slug to `web/src/content/journeys/.gitignore`
   f. `python tools/build-site.py --journeys-only` to generate
   g. `python tools/lint-journey-contract.py` to verify generated file
   h. `make pre-pr` to confirm all gates pass
9. **Avoiding duplicate canonical sources** (dual-ownership error conditions)

Internal guidance only. File is in `docs/guides/how-to/`, NOT `guides/` (catalogue-facing).

Done when: file exists at the exact path; `make build-check` passes.

---

### T9 — web/CLAUDE.md update
**Files:** `web/CLAUDE.md`
**Mode:** Goal-based
**Depends on:** T3, T7

Add to `## Build` section:
"Some files in `web/src/content/journeys/` are generated from `packs/*/JOURNEY.md` by
`tools/build-site.py --journeys-only`. Running `npm run build --prefix web` without first
running `python tools/build-site.py --journeys-only` (or `make site-build`) will fail
if generated files are absent."

Done when: note added; no other content changed.

---

### T10 — Integration verification
**Files:** none (verification only)
**Mode:** Goal-based + Manual QA + install smoke test
**Depends on:** T0–T9

Steps:
1. `python tools/test-lint-pack-journeys.py` → exit 0
2. `python tools/build-site.py --journeys-only` → generates product-documentation.md
3. `python tools/lint-pack-journeys.py` → exit 0
4. `python tools/lint-journey-contract.py` → exit 0 (generated file passes with State)
5. `python tools/lint-web-journey-parity.py` → exit 0 (generated file present, count ok)
6. `make pre-pr` → exit 0
7. `make build-check` → exit 0
8. `make site-build` → exit 0
9. Manual QA — serve via `npm run dev --background --prefix web`:
   - Verify `/journeys/product-documentation/` at 1440/1024/390px
   - Skill cards show `author-product-docs`
   - Human gates section visible
   - Pack page `/packs/product-documentation/` shows journey link
10. Install smoke (AC12):
    ```bash
    tmpdir=$(mktemp -d)
    catalogue="$(git rev-parse --show-toplevel)"
    python -m agentbundle install --pack product-documentation \
        --output "$tmpdir" "$catalogue"
    if find "$tmpdir" -name "JOURNEY.md" | grep -q .; then
        echo "AC12 FAIL: JOURNEY.md found in install output"
        rm -rf "$tmpdir"
        exit 1
    fi
    echo "AC12 PASS"
    rm -rf "$tmpdir"
    ```
    Note: the trailing `"$catalogue"` positional is required so the CLI resolves the
    pack from this repo's working tree, not a pip-installed/remote catalogue.

11. Existence assertion (AC7):
    ```bash
    python tools/build-site.py --journeys-only
    grep -q "generated: true" web/src/content/journeys/product-documentation.md \
        && echo "AC7 PASS" || (echo "AC7 FAIL: generated: true absent"; exit 1)
    ```

12. AC16 assertion — only one pack-local JOURNEY.md exists:
    ```bash
    count=$(find packs -name "JOURNEY.md" | wc -l | tr -d ' ')
    [ "$count" -eq 1 ] && echo "AC16 PASS" || (echo "AC16 FAIL: $count JOURNEY.md files"; exit 1)
    ```

13. `FORCE=1 make build-self` → exit 0
14. `git status --short` after build-self — no unexpected files

---

### T11 — Spec completion: flip Status, check ACs, changelog
**Files:** `docs/specs/pack-journeys-phase2b/spec.md`, `docs/product/changelog.md`
**Mode:** Goal-based
**Depends on:** T10

1. In spec.md: change `**Status:** Draft` to `**Status:** Shipped`
2. Mark each AC `[x]` (or `(deferred: <slug>)` for any deferred item)
3. Add `[Unreleased]` changelog entry in `docs/product/changelog.md`:
   - New validator `lint-pack-journeys.py` for pack-local JOURNEY.md files
   - `--journeys-only` flag in `build-site.py`
   - State vocabulary and stage contract for pack-local journeys
   - `product-documentation` pilot migration
   - Maintainer how-to guide at `guides/_shared/how-to/pack-journey-authoring.md`

Done when: spec status is Shipped; all ACs checked; changelog updated.
