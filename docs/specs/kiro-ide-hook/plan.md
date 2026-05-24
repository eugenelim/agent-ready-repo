# Plan: kiro-ide-hook primitive (RFC-0005 follow-on)

- **Spec:** [`spec.md`](spec.md) (stub — RFC drives this work)
- **Driving RFC:** [RFC-0005](../../rfc/0005-user-scope-hook-support.md)
  — particularly § *Kiro IDE event hooks — new `kiro-ide-hook`
  primitive*, § *Validate-time rule lift* → *Sibling vocabularies for
  IDE event hooks*, and § *Follow-on artifacts*.
- **Amends two specs in-place:**
  [`distribution-adapters/spec.md`](../distribution-adapters/spec.md)
  (deliverable A) and
  [`agent-spec-cli/spec.md`](../agent-spec-cli/spec.md) (deliverable B).
- **Branch:** `eugenelim/kiro-ide-hook-impl` (off `main`).

## Trio

**Files I'll touch.**

- `docs/specs/distribution-adapters/spec.md` — prose for the new
  primitive row, vocabulary fields, placeholder grammar, pipeline
  order extension, user-scope refusal text; new AC items.
- `docs/specs/agent-spec-cli/spec.md` — `install` /
  `uninstall` behavior for `.apm/kiro-ide-hooks/`; pipeline-order
  reference; no state-file shape change; new AC items.
- `docs/specs/user-scope-hooks/spec.md` — one cross-link line in
  the existing Rail B section pointing at the new
  `distribution-adapters` § v0.4 IDE event hooks subsection so the
  independent kiro-ide-hook user-scope refusal is discoverable from
  the Rail B reader's perspective.
- `packages/agentbundle/agentbundle/_data/adapter.schema.json` —
  primitive-enum extension; optional `ide-event-vocabulary` /
  `ide-action-vocabulary` array fields under
  `projections.<primitive>`.
- `packages/agentbundle/agentbundle/_data/adapter.toml` —
  `[primitive."kiro-ide-hook"]` table;
  `[adapter.kiro.projections.kiro-ide-hook]` projection table;
  explicit `[[adapter.<other>.projection]] mode = "dropped"` rows for
  claude-code / codex / copilot; `[contract] version` bump **gated on
  T-E1/T-E2**.
- `packages/agentbundle/agentbundle/_data/pack.schema.json` —
  add `"0.4"` to `adapter-contract.version` enum. **Lands in
  T-CONTRACT, not T-C1**, so the schema enum and the contract
  version write hit the tree in the same commit (per declined-pattern
  register item 3).
- `packages/agentbundle/agentbundle/build/phase_order.py` — extend
  `PHASE_ORDER` tuple to insert `"kiro-ide-hook"` after
  `"hook-wiring"`.
- `packages/agentbundle/agentbundle/build/projections/kiro_ide_hook.py`
  *(new file)* — `direct-file` projector with single-pass
  `${hook-body:<name>}` expansion against `then.command`.
- `packages/agentbundle/agentbundle/build/adapters/kiro.py` — dispatch
  the new primitive through `_dispatch_table_form`; resolve `<pack>`
  in target template.
- `packages/agentbundle/agentbundle/build/scope_rails.py` — new
  `check_kiro_ide_hook` function mirroring the existing
  `check_kiro_event_vocabulary` shape (in-memory rail + filesystem
  wrapper). Required fields, vocabulary membership, placeholder
  grammar, unresolvable refusal — all in one rail file so the four
  Kiro-related rails (`check_kiro_attach_to_agent`,
  `check_kiro_event_vocabulary`, `check_kiro_wiring`,
  `check_kiro_ide_hook`) sit together.
- `packages/agentbundle/tests/fixtures/kiro_ide_hook/` *(new
  directory)* — synthetic `.kiro.hook` fixtures (askAgent + runCommand
  with placeholder) and any captured-from-IDE fixture.
- `packages/agentbundle/tests/test_kiro_ide_hook.py` *(new file)* —
  unit tests per refusal path + projection success path.
- `.context/probes/kiro/` *(new directory, gitignored)* — Q6 / Q11
  probe fixtures and protocol notes; outcomes recorded in
  `docs/specs/kiro-ide-hook/probes.md`.
- `docs/specs/kiro-ide-hook/probes.md` *(new file)* — captures Q6
  recursion outcome, Q6 extension-filter outcome, Q11 captured
  fixture path + canonical vocabulary strings.
- `docs/adr/0003-kiro-ide-hook-primitive-per-surface.md` *(new
  file — number is next-available; ADR-0002 is the last extant one)*
  — records the primitive-per-surface decision for Kiro hooks
  (deliverable F, post-implementation).
- `docs/ROADMAP.md` — add tracking item for first `kiro-ide-hook`
  consumer pack; confirm-already-closed line for RFC-0001 Open Q1.

**What tests will demonstrate done.**

- `make test -C packages/agentbundle` passes (existing harness picks
  up the new `test_kiro_ide_hook.py`).
- `make build-check` passes (self-host gate clean).
- Each refusal path (T-C2.{1-5}) has a TDD-style red-green-refactor
  commit pair pinning the stderr message.
- After T-E1/T-E2 land, `adapter.toml`'s `[contract] version = "0.4"`
  + the pinned target/vocabulary strings round-trip through the
  validator and produce a synthetic fixture pack's `.kiro/hooks/<pack>/*.kiro.hook`
  bytes verbatim.
- `python -m agentbundle --version` continues to print the contract
  version it ships against (no regression).

**What I am NOT changing.**

- No new projection *mode* — `kiro-ide-hook` is `direct-file`. The
  novelty is placeholder expansion and the validate vocabularies, not
  a mode addition.
- No state-file schema change (`hook-wiring-owned` already at v0.3;
  `kiro-ide-hook` files need no ownership record because they live
  under pack-namespaced `<pack>/<name>.kiro.hook` directories that
  uninstall removes verbatim — RFC § State-file impact, p. 1058-1065).
- No user-scope projection for `kiro-ide-hook` in v1 — refused at
  contract layer until upstream Kiro #5440 closes (RFC § Scope).
- No state-file ownership record for kiro-ide-hook (pack-namespacing
  carries the disambiguation).
- No translation between adapter event vocabularies.
- No first-consumer pack publication — tracked as a separate ROADMAP
  item (deliverable G).
- No `steering` primitive — RFC's falsifiability test parks it.
- No knowledge-on-Kiro, no Kiro Power deployment.
- No edits to `packs/*/` content beyond ROADMAP updates — none of the
  four shipped packs declare `.apm/kiro-ide-hooks/`.
- **Pre-EXECUTE audit committed in the trio:**
  - Verified `packs/*/` carries no source-form `.apm/.../adapter.toml`
    or schema file (per user-global memory: never edit projected
    paths; the `_data/` files in `agentbundle/` are the source of
    truth, not a projection).
  - Verified `uninstall.py:138-186` (per-file Tier-1/Tier-2 loop) +
    `uninstall.py:228, 260-294` (empty-parent sweep): the existing
    per-file path plus its sweep already removes `.kiro/hooks/<pack>/`
    cleanly when every recorded file matches state — *no
    directory-removal code path is added* in this PR.

## Declined-pattern register

Patterns I was tempted by and chose against, with reasons:

- **Tempted to add a `direct-file-with-placeholder` projection
  mode.** Declining — modes describe *how* bytes move; placeholder
  expansion is a one-line post-process applied only to `then.command`
  in this primitive. A new mode would be shape inflation that no
  other primitive would reuse. The expansion lives inside the
  primitive's projector module.
- **Tempted to extract a generic placeholder-expansion helper
  (`packages/agentbundle/agentbundle/build/placeholder.py`) used by
  both `make build --self`'s `<adapt:NAME>` resolver and the new
  `${hook-body:<name>}` resolver.** Declining — the two have
  different syntax, different scan surfaces, and different unresolved
  policies (adapt markers pass through during normal builds;
  `${hook-body:<name>}` refuses). Three lines of regex per site is
  cheaper than the abstraction. Revisit when a third placeholder
  appears.
- **Tempted to widen `pack.schema.json`'s
  `adapter-contract.version` enum to `"0.4"` in the same commit as
  the schema's primitive-enum extension.** Declining — the v0.4
  declaration is probe-gated. Bumping the schema enum now lets a pack
  legally declare v0.4 before the contract bumps; the version-enum
  bump lands in lockstep with the `[contract] version` write.
- **Tempted to author a synthetic Q11 captured fixture by inferring
  the camelCase spellings from community examples.** Declining —
  the prompt explicitly bars guessing the projection target /
  vocabulary; the captured fixture is the evidence, not a placeholder
  for evidence. Stop and surface.
- **Tempted to add a `kiro-ide-hook-owned` state-file table mirroring
  `hook-wiring-owned`.** Declining — RFC § State-file impact rules
  this out by design (pack-namespacing handles uninstall by directory
  removal). Adding the table would be the squatter problem one level
  up.
- **Tempted to ship the contract version bump alongside the spec
  amendment prose without the probe outcomes.** Declining — the
  prompt directive is explicit, and "ship contract v0.4 with a
  target string that has to change on first use is a contract-version
  lie" (RFC § *Gating verifications before contract version 0.4
  ships*).
- **Tempted to add a `recurse-into-subdirectories` declarative
  adapter field so the contract carries Kiro's behaviour
  declaratively.** Declining — there is no second consumer for such
  a field; the probe outcome decides one target string, not a
  contract-level discipline.
- **Tempted to record `.kiro/hooks/<pack>/` as a single directory
  entry in `[pack.<name>.files]` rather than per-file**, to make a
  "directory removal" path in uninstall true. Declining — every other
  direct-file primitive records per-file and uninstall's Tier-2 SHA
  check is per-file; introducing a directory-granularity state entry
  is a state-file shape change disguised as a convenience, and the
  existing per-file path plus its empty-parent sweep already handles
  the kiro-ide-hook uninstall correctly.
- **Tempted to scan every string field in the `.kiro.hook` JSON for
  `${hook-body:...}` placeholders** rather than just `then.command`.
  Declining — RFC § Substitution rules clause 1 fences the scan to
  `then.command`; scanning `name`, `description`, `when.patterns`, or
  `then.prompt` would silently expand placeholders an adopter wrote
  literally (the `prompt` text is for the agent, not the bundler).

## Verification mode per task

The table below is the contract for "how do we know each task is
done":

| Task     | Mode       | Verification artifact                                                                |
| -------- | ---------- | ------------------------------------------------------------------------------------ |
| T-A      | Goal-based | Spec prose lands; new AC items added with `[ ]`; cross-spec links resolve.           |
| T-B      | Goal-based | Same shape as T-A on the sibling spec.                                               |
| T-C1     | TDD        | Schema accepts valid contract; rejects each malformed shape.                         |
| T-C2.1–5 | TDD        | One refusal path per construction test; red commit → green commit.                   |
| T-C3     | TDD        | Phase-order tuple change + test that wiring projects after hook-body.                |
| T-C4     | TDD        | End-to-end: fixture pack with one askAgent + one runCommand+placeholder hook builds. |
| T-D1     | Goal-based | `.kiro.hook` fixture files exist with the documented JSON shape.                     |
| T-D2     | Goal-based | Captured fixture exists under `tests/fixtures/kiro_ide_hook/` (gated on T-E2).       |
| T-E1     | Manual QA  | User runs Q6 probe in Kiro IDE; outcome recorded in `probes.md`.                     |
| T-E1b    | TDD        | (Fires only on Q6 yes×no quadrant.) Existing user-scope hook-body projection tests retargeted; old path turns red, new path green; `make build-check` clean. |
| T-E2     | Manual QA  | User authors a `.kiro.hook` via Kiro IDE UI; file captured under fixtures.           |
| T-G      | Goal-based | `make build-check` after `git status` shows ROADMAP delta only.                      |
| T-F      | Goal-based | ADR file lands; cross-links to RFC § Follow-on artifacts ADR bullet (b).             |
| T-CONTRACT | TDD       | Schema + adapter.toml + pack.schema.json round-trip post-bump; build remains green. |

## Task DAG

```
T-C1  (schema enum + new fields, no version bump yet)
T-D1  (synthetic askAgent/runCommand fixtures)
T-E1  (Q6 probe scaffolding — surface to user)
T-A   (distribution-adapters spec prose)
T-B   (agent-spec-cli spec prose)
            │
   ── all independent (Depends on: none) ──
            │
            ▼
T-C2   (validate rail, depends on T-C1 + T-D1)
T-C3   (phase order update + projector module, depends on T-C1 + T-D1)
T-C4   (Kiro adapter dispatch wires it together; depends on T-C2 + T-C3)
            │
            ▼
   ── probe gate ──
            │
T-E1 outcome → ▼  (Q6 fixes target.repo string)
   │   │
   │   └── if yes-recurse × no-extension-filter ─► T-E1b cross-primitive retarget
   │                                              (Depends on: T-E1 outcome only)
   │
T-E2 outcome → ▼  (Q11 fixes vocabulary list + canonical fixture)
            │
            ▼
T-CONTRACT  (adapter.toml v0.4 bump + pack.schema.json enum + probe-pinned values; depends on T-E1 + T-E2 + (T-E1b if it fired))
            │
            ▼
T-F   (ADR; depends on T-CONTRACT)
T-G   (ROADMAP entries; can land any time but pairs with T-CONTRACT for changelog clarity)
```

## Tasks (with Acceptance Criteria, Tests, Approach)

### T-A — Amend `docs/specs/distribution-adapters/spec.md`

**Depends on:** none. Prose only; cites RFC-0005 section anchors.

**Acceptance Criteria** (anchored in RFC-0005 § *Follow-on artifacts*
→ Amendment to distribution-adapters):

- [ ] Primitive table grows a `kiro-ide-hook` row: source
      `.apm/kiro-ide-hooks/<name>.kiro.hook`; Kiro → `direct-file` →
      `.kiro/hooks/<pack>/<name>.kiro.hook` *(target-string final form
      depends on T-E1; the prose pins the lean and links to
      `probes.md` for the recorded outcome)*; `dropped` on every
      other adapter.
- [ ] `[adapter.kiro.projections.kiro-ide-hook]` table fields
      documented in a new sibling subsection `## v0.4 IDE event hooks
      (RFC-0005)` inserted after the existing
      `## v0.3 user-scope hook handling (RFC-0005)` at
      [distribution-adapters/spec.md:509](../distribution-adapters/spec.md):
      `mode`, `target.repo`, `on-conflict`, `ide-event-vocabulary`,
      `ide-action-vocabulary`.
- [ ] Validate rail (required fields, vocabulary membership,
      placeholder grammar, unresolvable refusal) documented.
- [ ] Pipeline ordering invariant extended: `hook-body` → `agent` →
      `hook-wiring` → `kiro-ide-hook` → `command` → `skill` (RFC §
      Substitution rules → phase-order constraint).
- [ ] User-scope refusal text per RFC § Scope quoted verbatim into
      the spec.
- [ ] Contract version `0.3 → 0.4` declared with the gating note
      ("ships only after T-E1 / T-E2 outcomes are pinned").
- [ ] No edits to the seven projection-mode definitions (the mode is
      `direct-file`; no new mode introduced).

**Tests:** Goal-based — `make build-check` clean after the prose
change; manual link-resolution check across the two amended specs.

**Approach:**
1. Insert a new "v0.4 IDE event hooks" subsection after § *v0.3
   user-scope hook handling*. Mirror its shape (declaration block,
   merge / refusal / failure-mode rules, contract-version subsection
   at the bottom).
2. Append AC items to § *Acceptance Criteria* with the `[ ]`
   bookkeeping shape used by existing v0.3 items.
3. Add a Changelog entry dated today, naming RFC-0005 and the
   v0.3 → v0.4 contract bump gating.

### T-B — Amend `docs/specs/agent-spec-cli/spec.md`

**Depends on:** none. Prose only.

**Acceptance Criteria** (RFC-0005 § *Follow-on artifacts* →
Amendment to agent-spec-cli):

- [ ] `install` documents `.apm/kiro-ide-hooks/` handling for the
      Kiro adapter: copy each `<name>.kiro.hook` file to
      `<scope-root>/.kiro/hooks/<pack>/<name>.kiro.hook` with the
      placeholder expansion applied before write.
- [ ] `uninstall` removes the projected `.kiro.hook` files via the
      existing per-file Tier-1 path
      ([uninstall.py:138-186](../../../packages/agentbundle/agentbundle/commands/uninstall.py)
      Tier-1/Tier-2 loop +
      [uninstall.py:228, 260-294](../../../packages/agentbundle/agentbundle/commands/uninstall.py)
      empty-parent sweep) — every projected file is recorded under
      `[pack.<name>.files]` with its SHA; SHA-match deletes (Tier-1),
      SHA-mismatch preserves (Tier-2). The pack-namespaced subdirectory
      `.kiro/hooks/<pack>/` empties out and the existing best-effort
      empty-parent sweep removes it. No new directory-removal code
      path is added.
- [ ] `uninstall` preserves adopter-edited `.kiro.hook` files
      (SHA mismatch → Tier-2 warn-and-preserve, same property as every
      other `direct-file` primitive that ships today). The T-B
      amendment paraphrases — not quotes verbatim — RFC § State-file
      impact's `runCommand` callout, in language consistent with
      the actual Tier-2 path: a `runCommand`-shaped hook whose
      `then.command` was tuned by the adopter (local fix the pack
      author hasn't shipped) is preserved on uninstall via the same
      Tier-2 SHA-mismatch path; salience is higher than for an
      askAgent prompt edit because the adopter's tweak is often a
      load-bearing local fix.
- [ ] **RFC drift flagged separately.** RFC-0005 § State-file
      impact (lines 1067-1086) describes uninstall as "unconditional"
      / "directories all get nuked regardless of adopter edits" —
      which contradicts shipped `uninstall.py` (Tier-2 preserve since
      the v0.3 user-scope-hooks track shipped). The T-B amendment
      describes **actual code behaviour**, not the stale RFC text.
      The RFC text amendment is *not* in scope for this PR; recorded
      as a deferred follow-up in the PR description so a future
      RFC-text edit lands as its own unit.
- [ ] Build-pipeline ordering invariant referenced by link
      (single source of truth in the sibling spec; this spec cites it).
- [ ] No state-file shape change (the v0.3 schema covers
      `kiro-ide-hook` because no ownership record is needed beyond
      the per-file `[pack.<name>.files]` entries every direct-file
      primitive already records; this is explicitly stated).
- [ ] User-scope `--scope user` refused for `kiro-ide-hook` bearing
      packs with the RFC § Scope text, **independent of the existing
      Rail B** (a `kiro-ide-hook`-only pack with `user-scope-hooks =
      true` still refuses because the primitive itself is repo-only
      in v1).
- [ ] Cross-link from `docs/specs/user-scope-hooks/spec.md` § Rail B
      to the new `kiro-ide-hook` § in distribution-adapters so a
      reader of *that* spec sees the independent refusal exists.

**Tests:** Goal-based — `make build-check` clean; cross-spec link
resolution.

**Approach:**
1. Add a new subsection "v0.4 `kiro-ide-hook` primitive (RFC-0005)"
   after § *v0.3 user-scope hook handling*.
2. Append matching AC items.
3. Append a Changelog entry.

### T-C1 — `adapter.schema.json` extension

**Depends on:** none.

**Acceptance Criteria:**

- [ ] `projections.<primitive>.properties` gains `ide-event-vocabulary`
      and `ide-action-vocabulary` as optional arrays-of-strings
      (`minItems: 1`). The fields are already implicitly permitted
      (no `additionalProperties: false` on the inner object); this
      change makes them explicit/documented.
- [ ] Existing v0.3 contract continues to validate cleanly after
      the change.
- [ ] The schema enum for `projections.<primitive>.mode` is
      **unchanged** — `direct-file` is reused.
- [ ] **No change to `primitive.required` in this task.** Adding
      `"kiro-ide-hook"` to the required list lands in T-CONTRACT in
      lockstep with the `[primitive."kiro-ide-hook"]` declaration in
      `adapter.toml` — otherwise validate would reject the
      pre-bump contract. Same reasoning as `pack.schema.json`'s
      `adapter-contract.version` enum bump.
- [ ] **No change to `pack.schema.json` in this task.** The
      `adapter-contract.version` enum bump to `"0.4"` lands in
      T-CONTRACT in lockstep with the `[contract] version` write.

**Tests** (in `packages/agentbundle/tests/test_adapter_contract.py`
or sibling — extend the existing table-driven tests):

```python
def test_schema_accepts_kiro_ide_hook_primitive(contract_loader):
    contract = contract_loader.load()
    assert "kiro-ide-hook" in contract["primitive"]
    assert contract["primitive"]["kiro-ide-hook"]["source-path"] == ".apm/kiro-ide-hooks/"

def test_schema_rejects_missing_ide_event_vocabulary_on_declared_projection():
    # When a contract declares kiro-ide-hook projection on kiro, the
    # ide-event-vocabulary field is required.
    ...

def test_schema_accepts_v0_4_pack_adapter_contract_version():
    # Pack declaring [pack.adapter-contract] version = "0.4" validates.
    ...
```

**Approach:**
1. Edit `primitive.required` array.
2. Add `ide-event-vocabulary` / `ide-action-vocabulary` keys under
   the existing `projections.<primitive>.properties` object.
3. Widen the `pack.schema.json` version enum.
4. Run the existing contract conformance tests; add the new tests.

### T-C2 — `kiro-ide-hook` validate rail

**Depends on:** T-C1, T-D1.

**Acceptance Criteria:** each refusal is a separate stderr message,
one-line, naming the offending pack and the offending file.

- [ ] **T-C2.1** Missing-required-field refusal:
      `pack <P>'s kiro-ide-hook <file> is missing required field <field>`.
- [ ] **T-C2.2** `when.type` not in `ide-event-vocabulary`:
      `pack <P>'s kiro-ide-hook <file> uses event '<type>'; not in adapter 'kiro' ide-event-vocabulary`.
- [ ] **T-C2.3** `then.type` not in `ide-action-vocabulary`:
      `pack <P>'s kiro-ide-hook <file> uses action '<type>'; not in adapter 'kiro' ide-action-vocabulary`.
- [ ] **T-C2.4** Malformed placeholder:
      `pack <P>'s kiro-ide-hook <file> contains malformed placeholder '<text>'; expected ${hook-body:<name>} with name matching [a-zA-Z0-9_-]+`.
- [ ] **T-C2.5** Unresolvable placeholder:
      `pack <P>'s kiro-ide-hook <file> references unknown hook-body '${hook-body:<name>}'; no such hook-body in pack`.

**Tests** (per refusal, in
`packages/agentbundle/tests/test_kiro_ide_hook.py`):

```python
def test_validate_refuses_missing_required_field(tmp_path):
    pack = build_pack(tmp_path, kiro_ide_hook="missing-name.kiro.hook")
    result = run_validate(pack)
    assert result.exit_code != 0
    assert "missing required field name" in result.stderr

# ... one test per refusal path, parameterised by fixture.
```

**Approach:** add `check_kiro_ide_hook(pack_path, contract)` to
`packages/agentbundle/agentbundle/build/scope_rails.py` — the rail
home for the three existing Kiro-specific rails
(`check_kiro_attach_to_agent`, `check_kiro_event_vocabulary`,
`check_kiro_wiring`). Mirror `check_kiro_event_vocabulary`'s shape:
an in-memory rail callable plus a filesystem wrapper that walks
`.apm/kiro-ide-hooks/` in `sorted(os.walk(...))` order. Non-UTF-8
files skipped silently per the existing Rail C convention. Wire it
into the `validate` and `install` call sites the existing Kiro rails
already hook (grep for `check_kiro_event_vocabulary` to find them).

**Sub-tasks for parallel implementer dispatch (T-C2 family):**

- T-C2.1, T-C2.2, T-C2.3, T-C2.4, T-C2.5 — each refusal-path test
  is an independent commit; they share the validate.py rail
  implementation but the tests don't share state. Per the prompt
  ("C's tests (per-refusal-path tests are independent of each
  other)"), these could parallelise — but the cost-benefit of
  five-way fan-out for ~30-line test functions is poor; in EXECUTE
  pick one of: implement the rail once, then write the five tests
  serially, OR implement TDD by writing all five tests up front
  (red) then the rail (green). The latter is cheaper than five
  worktrees.

### T-C3 — Phase order + projector module

**Depends on:** T-C1, T-D1.

**Acceptance Criteria:**

- [ ] `PHASE_ORDER` tuple in `phase_order.py` becomes:
      `("hook-body", "agent", "hook-wiring", "kiro-ide-hook", "command", "skill")`.
- [ ] New `packages/agentbundle/agentbundle/build/projections/kiro_ide_hook.py`
      module exports `project(pack_path, contract, output_root)` (or
      the existing per-projection callable shape — match the
      `merge_into_agent_json.py` signature observed during EXECUTE).
- [ ] Placeholder expansion: single-pass, verbatim, scan-`then.command`-
      only (RFC § *Substitution rules* clauses 1-5).
- [ ] `then.command` is the **only** scanned field.
- [ ] Resolved text not re-scanned (no nested expansion).
- [ ] `<pack>` and `<name>` placeholders in the projection-target
      string resolve at projection time.

**Tests:**

```python
def test_phase_order_includes_kiro_ide_hook_between_wiring_and_command():
    from agentbundle.build.phase_order import PHASE_ORDER
    assert PHASE_ORDER.index("kiro-ide-hook") == PHASE_ORDER.index("hook-wiring") + 1
    assert PHASE_ORDER.index("kiro-ide-hook") < PHASE_ORDER.index("command")

def test_run_command_placeholder_expands_to_projected_hook_body_path(tmp_path):
    pack = build_pack(tmp_path, hook_body="lint.py", kiro_ide_hook="lint-on-save.kiro.hook")
    output = run_build(pack, tmp_path / "out")
    written = (output / ".kiro/hooks/example-pack/lint-on-save.kiro.hook").read_text()
    assert "./tools/hooks/lint.py" in written
    assert "${hook-body:" not in written  # all placeholders expanded

def test_ask_agent_hook_passes_through_verbatim(tmp_path):
    # askAgent hooks with no `${` substring byte-copy verbatim;
    # assert SHA equality between source and target.
    ...
```

**Approach:**
1. Edit `phase_order.py` — change the tuple to
   `("hook-body", "agent", "hook-wiring", "kiro-ide-hook", "command",
   "skill")`. One-line edit.
2. Create `projections/kiro_ide_hook.py` with the signature
   `project(pack_path: Path, contract: dict, output_root: Path) ->
   None` mirroring the existing per-projection callable shape (see
   `merge_into_agent_json.py` for the reference). Branching:
   - Read each `.kiro.hook` under `.apm/kiro-ide-hooks/` in
     `sorted(os.walk(...))` order.
   - **askAgent byte-copy shortcut.** If raw bytes contain no
     `${` substring (which implies no `then.command` placeholder)
     **and** parsed `then.type == "askAgent"`, byte-copy the source
     file to the resolved target via `shutil.copy2`. Preserves
     original key ordering, whitespace, and trailing-newline shape;
     skips a JSON re-serialize round trip.
   - Otherwise, parse as JSON; raise `KiroIdeHookRefusal` on parse
     error. Scan `then.command` (only) with `re.sub` against
     `\$\{hook-body:([a-zA-Z0-9_-]+)\}` — verbatim single-pass
     substitution, no shell quoting. Resolved text is NOT re-scanned.
     Map each capture to the same pack's projected `hook-body` target
     (resolve `[adapter.kiro.projections.hook-body].target.repo`
     against the *projected* path the hook-body projection wrote at
     the prior phase — relative path under the pack's output root).
   - Output-path resolution:
     - `<pack>` ← `pack_path.name` (verified to be reachable from the
       projector's call shape; the new module does **not** reuse
       `_project_direct_file_template` since that helper only knows
       `<name>`).
     - `<name>` ← `entry.stem.removesuffix('.kiro')` (the `.kiro.hook`
       suffix is the literal extension; the stem strips `.hook` only,
       so we strip `.kiro` ourselves to get the bare hook name).
     - Substitute both into
       `[adapter.kiro.projections.kiro-ide-hook].target.repo` and
       write under `output_root / resolved.lstrip('/')`.
   - Write the file.
3. Wire into `kiro.py` adapter — extend `_dispatch_table_form` to
   recognise `kiro-ide-hook` and dispatch to the new projector.

### T-C4 — Kiro adapter wires it together

**Depends on:** T-C2, T-C3.

**Acceptance Criteria:**

- [ ] `kiro.py::_dispatch_table_form` dispatches `kiro-ide-hook` to
      the new projector.
- [ ] End-to-end: fixture pack with one `.apm/hooks/lint.py` and one
      `.apm/kiro-ide-hooks/lint-on-save.kiro.hook` builds cleanly,
      and the projected JSON contains `./tools/hooks/lint.py`.
- [ ] An askAgent fixture (no placeholder) round-trips byte-for-byte.
- [ ] Validate runs before project; a malformed fixture refuses at
      validate time (T-C2 path), not at projection.

**Tests:** subsumes the T-C3 end-to-end tests; pure integration.

**Approach:** one-line dispatch addition plus integration assertions.

### T-D1 — Synthetic `.kiro.hook` fixtures

**Depends on:** none.

**Acceptance Criteria:**

- [ ] `packages/agentbundle/tests/fixtures/kiro_ide_hook/ask_agent_basic.kiro.hook`
      — askAgent shape, no placeholder.
- [ ] `packages/agentbundle/tests/fixtures/kiro_ide_hook/run_command_with_placeholder.kiro.hook`
      — runCommand shape, contains `${hook-body:lint}` against a
      same-pack `hook-body` named `lint`.
- [ ] Both validate against the documented `.kiro.hook` schema (RFC
      § Pack-side source).

**Tests:** consumed by T-C2 / T-C3 / T-C4.

**Approach:** hand-author the two JSON files from the RFC's example
verbatim. Use representative-but-stable strings (no machine-specific
values).

### T-D2 — Captured-fixture consumption (gated on T-E2)

**Depends on:** T-E2 (user runs probe; capture lands during T-E2).

**Acceptance Criteria:**

- [ ] `test_kiro_ide_hook.py` adds a parametrize block that consumes
      the captured fixture(s) from T-E2 as the vocabulary-source-of-
      record: every captured file is validated against the rail
      (T-C2) and projects cleanly through the new projector (T-C3).
- [ ] If T-E2 captured a runCommand-shaped fixture, an additional
      test confirms `${hook-body:<name>}` placeholder expansion
      against a captured file's `then.command`. If only askAgent was
      captured (RFC Q11's floor), this sub-test is skipped with a
      `pytest.skip` reason naming the gap.

**Tests:** the captured fixture path is itself a test fixture —
this task wires the parametrize, it doesn't author the file.

**Approach:** add a `pytest.mark.parametrize` decorator that
discovers every file under `tests/fixtures/kiro_ide_hook/captured/`
and asserts validate + project pass. Single test function; no
hand-rolled file paths.

### T-E1 — Q6 recursion + extension-filter probe

**Depends on:** none.

**Acceptance Criteria:**

- [ ] `docs/specs/kiro-ide-hook/probes.md` records both observations
      (recursion: yes/no; extension filter: yes/no) plus the chosen
      `target.repo` string per the 2×2 in RFC § Unresolved Q6.
- [ ] `.context/probes/kiro/` carries the probe workspace fixtures
      (the canary `.kiro.hook` files used to drive the probe).

**Tests:** Manual QA — record observations in `probes.md`.

**Approach (probe protocol):**

1. Create probe workspace: `mkdir .context/probes/kiro/probe-workspace`.
2. Drop two hook files:
   - `.context/probes/kiro/probe-workspace/.kiro/hooks/canary-flat.kiro.hook`
     — askAgent triggered on `fileSave`, prompt
     `"Probe: flat file fired"`.
   - `.context/probes/kiro/probe-workspace/.kiro/hooks/subdir/canary-nested.kiro.hook`
     — same shape, prompt `"Probe: nested file fired"`.
   - `.context/probes/kiro/probe-workspace/.kiro/hooks/canary-other.txt`
     — non-`.kiro.hook` extension carrying the same JSON
     (extension-filter test).
3. Open the workspace in Kiro IDE; trigger a `fileSave` event by
   editing and saving any tracked file.
4. Observe which canary(ies) fired (Kiro's hook-firing surface in
   the IDE UI).
5. Record the 2×2 outcome in `probes.md`.

**Surface trigger:** if the operator can't drive the Kiro IDE in
this session, this task surfaces and the loop pauses at T-CONTRACT.

### T-E1b — Conditional cross-primitive `hook-body` retarget (Q6 yes×no quadrant only)

**Depends on:** T-E1 outcome.

**Fires only when:** Q6 lands `yes-recursion × no-extension-filter`
(RFC § Unresolved Q6 2×2 table). In that quadrant, Kiro reads every
file under `.kiro/hooks/<subdir>/` regardless of extension — so
projecting `hook-body` scripts (`.sh`/`.py`) into the same subtree
as `.kiro.hook` files would have Kiro try to parse them as hooks.
The mitigation: move user-scope `hook-body` from `.kiro/hooks/<pack>/`
to `.kiro/hook-bodies/<pack>/`.

**Acceptance Criteria:**

- [ ] `[adapter.kiro.projections.hook-body].target.user` in
      `packages/agentbundle/agentbundle/_data/adapter.toml` updates
      from `.kiro/hooks/<name>.{sh,py}` (current v0.3) to
      `.kiro/hook-bodies/<pack>/<name>.{sh,py}`.
- [ ] `[adapter.kiro.scope] allowed-prefixes.user` widens to include
      `.kiro/` *and* `.kiro/hook-bodies/` if separate-prefix
      enforcement is required (likely subsumed by the existing
      `.kiro/` prefix, but verify against `target_resolver.py`
      semantics).
- [ ] The user-scope-hooks spec is amended: the `hook-body` user-
      scope target string in its Acceptance Criteria updates in
      lockstep.
- [ ] `make build-check` clean after the retarget.

**Tests:** TDD — extend the existing user-scope `hook-body`
projection tests so the new target path is the green case and the
old one fails.

**Approach:**
1. Confirm T-E1's outcome lands the yes×no quadrant from
   `probes.md`. If any other quadrant, **this task does not fire**
   — mark it `[skipped: Q6 quadrant <X> hit]` in the plan's
   bookkeeping and proceed straight to T-CONTRACT.
2. If the quadrant fires: bundle the `hook-body` retarget into the
   same PR as T-CONTRACT per the RFC's "cross-primitive consequence
   in the yes×no quadrant only" note. The retarget cannot be
   deferred — shipping v0.4 with collision-prone targets would
   break Kiro at runtime.

**Surface trigger:** if the quadrant fires and the operator is not
present to confirm the user-scope-hooks spec amendment shape, this
task surfaces; T-CONTRACT pauses behind it.

### T-E2 — Q11 captured-vocabulary fixture

**Depends on:** none (parallel with T-E1).

**Acceptance Criteria:**

- [ ] **Floor: at least one** IDE-UI-authored `.kiro.hook` file
      under `packages/agentbundle/tests/fixtures/kiro_ide_hook/captured/`.
      Per RFC § Unresolved Q11, one captured shape is the floor.
- [ ] **Preferred: one of each action type** (askAgent + runCommand)
      if Kiro's IDE UI exposes both in the operator's installed
      version; if only one is reachable, document why in
      `probes.md`.
- [ ] The captured file's `when.type` and `then.type` strings are
      pinned in `probes.md` as the canonical vocabulary anchors
      for `ide-event-vocabulary` and `ide-action-vocabulary` in
      `adapter.toml`.

**Tests:** Manual QA.

**Approach (probe protocol):**

1. Open the Kiro IDE.
2. Use the hook-author UI to create one askAgent-shaped hook (any
   trigger). If the UI also exposes runCommand-shaped hooks,
   author one of those too.
3. Save.
4. Locate the resulting `.kiro.hook` file(s) Kiro wrote.
5. Copy them into the fixtures directory under `captured/`.
6. Read off the canonical strings and record them in `probes.md`.

**Surface trigger:** same as T-E1.

### T-CONTRACT — adapter.toml v0.4 bump (probe-gated)

**Depends on:** T-E1, T-E2, and (if it fired) T-E1b.

**Acceptance Criteria:**

- [ ] `[contract] version` bumps `"0.3" → "0.4"`.
- [ ] `[primitive."kiro-ide-hook"]` table added with
      `source-path = ".apm/kiro-ide-hooks/"`.
- [ ] `adapter.schema.json` `primitive.required` array grows
      `"kiro-ide-hook"` — lands here, not T-C1, so the schema's
      required list and the contract's `[primitive]` declaration
      hit the tree in the same commit.
- [ ] `adapter.schema.json` array-form `primitive` enum
      (`adapter.<name>.projection.items.properties.primitive.enum`)
      grows `"kiro-ide-hook"` — same reason as the previous AC:
      the `[[adapter.<other>.projection]] primitive = "kiro-ide-hook",
      mode = "dropped"` rows would otherwise fail enum validation.
      Two distinct enum sites in the same schema file; both must
      widen together. Pre-EXECUTE adversarial review caught this
      bookkeeping gap.
- [ ] `[adapter.kiro.projections.kiro-ide-hook]` table added with:
      `mode = "direct-file"`, `target.repo = "<probe-pinned-string>"`,
      `on-conflict = "prompt-then-preserve"`,
      `ide-event-vocabulary = [<probe-pinned-list>]`,
      `ide-action-vocabulary = ["askAgent", "runCommand"]`.
- [ ] `[[adapter.<other>.projection]]` rows added with
      `primitive = "kiro-ide-hook", mode = "dropped"` for claude-code,
      codex, copilot.
- [ ] `pack.schema.json` `adapter-contract.version` enum extends to
      include `"0.4"` — **lands here**, in lockstep with the
      `[contract] version` write, per Blocker 3 from the
      pre-EXECUTE adversarial review.
- [ ] **Q10 baked decision pinned.** `then.type = "runCommand"`
      accepted by the validate rail without a per-pack consent flag
      (RFC § Unresolved Q10 option (a)); no `--allow-shell-hooks`
      install flag is added; no `runCommand`-refusal path is added.
      The consent gesture is the one-time `install` of the pack
      itself, same shape as `hook-body` shell scripts wired via
      `merge-into-agent-json`.
- [ ] All existing contract-conformance tests pass against the v0.4
      contract.

**Tests:** Goal-based — `python -m agentbundle validate
<fixture-pack>` exits zero against a v0.4-declaring pack; existing
v0.3 packs continue to validate.

**Approach:** one diff against `adapter.toml`. The probe outcomes
fully determine the writeable values; no human judgment at this step.

### T-F — ADR (both bullets — verified bullet (a) is orphaned)

**Depends on:** T-CONTRACT.

**Verified pre-EXECUTE:** `docs/adr/` contains only ADR-0001
(adopt-agents-md-and-doc-hierarchy) and ADR-0002 (install-scope-per-
pack-default-and-allowance) at the time of the adversarial review.
The user-scope-hooks spec/plan do **not** produce an ADR. ADR
bullet (a) from RFC § Follow-on artifacts is therefore orphaned and
this PR carries both bullets.

**Acceptance Criteria:**

- [ ] `docs/adr/0003-kiro-hook-merge-contracts-and-primitive-per-surface.md`
      lands recording **both** durable decisions from RFC § Follow-on
      artifacts → ADR bullets (a) + (b):
  - **(a) Merge contracts for hand-edited and pack-owned files.**
    The CLI may write to hand-edited shared user-settings files
    under an ID-tagged array-append merge contract
    (`user-merge-json`) and to pack-owned agent files under a
    per-agent variant of the same contract (`merge-into-agent-json`).
    Subsequent user-scope merge work (`env`, `mcpServers`, anything
    else under a `managed-key.user`) cites this ADR.
  - **(b) Primitive-per-surface for Kiro hooks.** IDE-event hooks on
    Kiro live in their own primitive (`kiro-ide-hook`) rather than
    being shoehorned into `hook-wiring`'s `merge-into-agent-json`
    mode (wrong firing model), a generic `event-hook` primitive
    (Kiro-specific schema), or Kiro Powers (different distribution
    shape). Future Kiro hook surfaces follow the same
    primitive-per-surface discipline.
- [ ] Cross-link to RFC-0005, particularly § *Falsifiability test
      for future RFC reviewers* (for bullet b's gap-vs-asymmetry
      rationale).

**Tests:** Goal-based.

**Approach:** apply the `new-adr` skill. Single ADR file carrying
both bullets — they're the same RFC's follow-on, and splitting them
into two ADRs (against the same RFC) would create a per-decision
search problem.

### T-G — ROADMAP entry

**Depends on:** none.

**Acceptance Criteria:**

- [ ] `docs/ROADMAP.md` grows an open item under the
      `distribution-adapters` (or `agent-spec-cli`) section tracking
      the first `kiro-ide-hook` consumer pack — separate from any
      existing user-scope-hooks consumer.
- [ ] Verify the `closes RFC-0001 Open Q1` closure marker is already
      in place in `docs/ROADMAP.md` (search by text, not line
      number) from the v0.3 work; if so, no edit needed. If absent,
      add the closure marker.

**Tests:** Goal-based — `make build-check` clean post-edit.

**Approach:** append the open item under the appropriate section.

## Out-of-loop concerns

- **`AGENTS.md` package-level dependency record.** No new dependencies
  added (stdlib only); no AGENTS.md update needed.
- **Self-host gate.** `make build-check` after every commit. Drift
  between `packs/<pack>/` and `<repo>/` would be a regression of
  RFC-0002's self-host invariant.
- **Spec/RFC version coherence.** The two amended specs cite RFC-0005
  by section anchor — section anchors must resolve. Pre-PR check.

## Termination criteria

The loop stops when **either**:

1. All tasks above complete and `loop-cohort.py check
   docs/specs/kiro-ide-hook --phase review` exits zero.
2. **Surface trigger.** If the operator cannot run T-E1 or T-E2 in
   this session (the Kiro IDE flow needs interactive input), the loop
   stops at the T-CONTRACT boundary: T-A, T-B, T-C1, T-C2, T-C3,
   T-C4, T-D1, T-G can all land; T-CONTRACT, T-F, T-D2 follow up
   once the probes run. The PR is opened with the in-scope work and
   a clear "v0.4 ship gate pending probes" callout in the
   description.
