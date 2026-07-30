# Plan: catalogue-wave2-pack-integrations

- **Status:** Executing
- **Spec:** [`spec.md`](spec.md)

Mode: full (structural schema change — new `[[pack.integrations]]` field in
`contracts/pack.schema.json`; new CLI surface in `agentbundle show`; new
validation rules in `agentbundle catalogue verify`; first-party pack.toml
changes; engine change RFC-0076).

## Assumptions

- `contracts/pack.schema.json` and `agentbundle/_data/pack.schema.json` are
  byte-identical at HEAD (Wave 1 parity gate). Confirmed.
- All pilot consumer/provider primitive paths verified to exist at HEAD
  (see spec.md Assumptions section).
- Version 0.27.0 is the next minor bump from 0.26.1. Verify before
  opening the PR that no concurrent PR is racing to this version.
- `jsonschema` is available in the test environment (used by
  `agentbundle.build.validate`).

## Files touched

| File | Change |
|------|--------|
| `contracts/pack.schema.json` | Add `integrations` array property |
| `packages/agentbundle/agentbundle/_data/pack.schema.json` | Byte-identical sync |
| `packages/agentbundle/agentbundle/catalogue_tooling/verify.py` | New `_step_integration_validation` step (step 19) |
| `packages/agentbundle/agentbundle/commands/show.py` | Surface `integrations` in table + JSON output |
| `packages/agentbundle/tests/unit/test_catalogue_wave2_schema.py` | New — schema + parity tests (AC1-AC4) |
| `packages/agentbundle/tests/unit/test_catalogue_wave2_validation.py` | New — integration validation tests (AC5-AC12) |
| `packages/agentbundle/tests/integration/test_show_cmd.py` | Add AC15-AC16 tests; update AC3 key-set assertion |
| `packs/core/pack.toml` | Add two `[[pack.integrations]]` entries; version 0.15.6 → 0.15.7 |
| `packs/core/.claude-plugin/plugin.json` | Version bump to 0.15.7 |
| `packs/governance-extras/pack.toml` | Add three `[[pack.integrations]]` entries; version 0.9.2 → 0.9.3 |
| `packs/governance-extras/.claude-plugin/plugin.json` | Version bump to 0.9.3 |
| `guides/_shared/reference/catalogue-authoring-standards.md` | Replace placeholder with section 11 |
| `packages/agentbundle/agentbundle/_data/catalogue-scaffold/guides/_shared/reference/catalogue-authoring-standards.md` | Sync scaffold copy |
| `packages/agentbundle/pyproject.toml` | Version 0.26.1 → 0.27.0 |
| `packages/agentbundle/agentbundle/version.py` | `CLI_VERSION` → `"0.27.0"` |
| `docs/product/changelog.md` | Add 0.27.0 entry (schema, validation, show, pilots) |

Not changing: `list-packs`, `install`, the degrade path in `show` (no TOML
source there — `integrations=[]` passed silently), any other command surface,
CI workflows, AGENTS.md.

## Tasks

---

### Task 1 — Schema: add `integrations` array to `pack.schema.json` (AC1-AC4)

**Verification mode:** TDD
**Depends on:** none

**Tests (stub file: `tests/unit/test_catalogue_wave2_schema.py`):**

```python
# STUB: AC1 — integrations property exists and is an optional array
def test_integrations_property_exists_in_schema():
    schema = _load_schema()
    assert "integrations" in schema["properties"]["pack"]["properties"]
    assert "integrations" not in schema["properties"]["pack"]["required"]

# STUB: AC2 — pack without integrations validates
def test_pack_without_integrations_validates():
    errors = _validate({"pack": {"name": "x", "version": "1.0.0"}})
    assert errors == []

# STUB: AC3 — valid integration entry validates
def test_valid_integration_entry_validates():
    errors = _validate({"pack": {"name": "x", "version": "1.0.0",
        "integrations": [_valid_entry()]}})
    assert errors == []

# STUB: AC3 — missing required field fails
def test_integration_missing_required_field_fails():
    entry = {k: v for k, v in _valid_entry().items() if k != "id"}
    errors = _validate({"pack": {"name": "x", "version": "1.0.0",
        "integrations": [entry]}})
    assert errors != []

# STUB: AC3 — invalid kind fails
def test_integration_invalid_kind_fails():
    entry = {**_valid_entry(), "kind": "unknown"}
    errors = _validate({"pack": {"name": "x", "version": "1.0.0",
        "integrations": [entry]}})
    assert errors != []

# STUB: AC4 — parity check exits 0
def test_parity_bytes_identical():
    live = _LIVE_SCHEMA_PATH.read_bytes()
    bundled = _BUNDLED_SCHEMA_PATH.read_bytes()
    assert live == bundled
```

**Approach:**

Add the following property to the `pack` object in `contracts/pack.schema.json`
(NOT in the `required` array):

```json
"integrations": {
  "type": "array",
  "items": {
    "type": "object",
    "additionalProperties": false,
    "required": ["id", "pack", "kind", "role", "consumers", "providers",
                 "when", "purpose", "fallback"],
    "properties": {
      "id":        {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]*$"},
      "pack":      {"type": "string"},
      "kind":      {"type": "string", "enum": ["input", "augment", "review", "handoff"]},
      "role":      {"type": "string"},
      "consumers": {"type": "array", "minItems": 1,
                    "items": {"type": "string",
                              "pattern": "^(skill|agent|command|hook):[a-z0-9][a-z0-9-]*$"}},
      "providers": {"type": "array", "minItems": 1,
                    "items": {"type": "string",
                              "pattern": "^(skill|agent|command|hook):[a-z0-9][a-z0-9-]*$"}},
      "when":      {"type": "string", "minLength": 1},
      "purpose":   {"type": "string", "minLength": 1},
      "fallback":  {"type": "string", "minLength": 1},
      "version":   {"type": "string"}
    }
  }
}
```

After editing `contracts/pack.schema.json`, byte-copy it to
`packages/agentbundle/agentbundle/_data/pack.schema.json`. Run
`python3 tools/catalogue/check_contract_parity.py` to confirm AC4.

**Note:** `kind` enum and `when`/`purpose`/`fallback` `minLength: 1` are
enforced by the schema (AC6/AC8 satisfied here). Step 19 only adds
rules the schema cannot express.

**Done when:** `test_catalogue_wave2_schema.py` passes; `check_contract_parity.py`
exits 0.

---

### Task 2 — Validation rules: add integration-specific rules to `verify.py` (AC5-AC12)

**Verification mode:** TDD
**Depends on:** Task 1

**Tests (stub file: `tests/unit/test_catalogue_wave2_validation.py`):**

```python
# STUB: AC5 — duplicate integration IDs error
def test_verify_duplicate_integration_id_errors(): ...

# STUB: AC7 — consumer ref missing in declaring pack errors
def test_verify_consumer_ref_missing_errors(): ...

# STUB: AC7 (agent) — consumer agent ref missing in declaring pack errors
def test_verify_consumer_agent_ref_missing_errors(): ...

# STUB: AC9 — self-target errors
def test_verify_self_target_errors(): ...

# STUB: AC10 (accept) — valid semver ranges pass
@pytest.mark.parametrize("v", ["^1.0.0", ">=2.0.0 <3.0.0", "1.2.3",
                                "~1.2", "1.0.0 - 2.0.0", "1.0.0 || 2.0.0"])
def test_verify_valid_version_range_passes(v): ...

# STUB: AC10 (reject) — invalid version strings error
@pytest.mark.parametrize("v", ["latest", "@1", "not-a-version"])
def test_verify_invalid_version_range_errors(v): ...

# STUB: AC11 — absent target pack does NOT error
def test_verify_absent_target_pack_passes(): ...

# STUB: AC12 — provider ref missing when target present errors
def test_verify_present_target_provider_missing_errors(): ...

# STUB: happy path — valid integration passes
def test_verify_valid_integration_passes(): ...
```

**Approach:**

Add two private helpers and one new step function to `verify.py`.

**`_resolve_primitive_ref(ref, pack_dir) -> bool`** — resolves a
type-qualified ref against a pack's `.apm/` directory. Type-to-path mapping:
- `skill:<name>` → directory `pack_dir/.apm/skills/<name>/`
- `agent:<name>` → file `pack_dir/.apm/agents/<name>.md`
- `command:<name>` → file `pack_dir/.apm/commands/<name>.md`
- `hook:<name>` → any file `pack_dir/.apm/hooks/<name>.*` (stem-match
  iteration: `Path(f).stem == name` for each file in hooks dir)

Skills are directories; agents/commands are `.md` files; hooks can have
arbitrary extensions. Edge cases:
- `.apm/hooks/` absent → hook ref resolves False (guard with `dir.is_dir()`)
- Hook stem = `Path(filename).stem`; `"pre-install.py"` → `"pre-install"` ✓;
  multi-dot names (`"a.b.py"` → stem `"a.b"`) would need `hook:a.b`, but the
  schema's id pattern `^[a-z0-9][a-z0-9-]*$` prohibits dots in IDs so such
  hook names are unreferenceable and resolve False by definition.

**`_is_valid_semver_range(version) -> bool`** — npm-compatible semver range
validator without any new dependency:
1. Split on `||` (union ranges).
2. For each part (stripped): check if it matches the hyphen-range pattern
   `^\d[.\d]* - \d[.\d]*$` first. If so, it's valid.
3. Otherwise, split on whitespace and check each atom against:
   `^(?:[~^]|[<>]=?)?(?:0|[1-9]\d*)(?:\.(?:0|[1-9]\d*)(?:\.(?:0|[1-9]\d*)(?:-[\w.]+)?)?)?$`
4. Any non-matching atom returns False.

Accept: `^1.0.0`, `>=2.0.0 <3.0.0`, `1.2.3`, `~1.2`, `1.0.0 - 2.0.0`,
`1.0.0 || 2.0.0`. Reject: `latest`, `@1`, `not-a-version`.

**`_step_integration_validation(root, config, pack, tmpdir)`** — step 19:
- Derive packs dir defensively: `packs_root = root / (getattr(config, "paths", None) and config.paths.packs or "packs")`. Never skip on `config is None` — the step must run on bare pack directories without a catalogue.toml (including test fixtures).
- Pass 1: collect `all_pack_dirs: dict[str, Path]` (all pack names → dirs,
  unfiltered by `pack` arg — needed for AC12 cross-reference)
- Pass 2 (with `pack` filter): for each pack with `[[pack.integrations]]`:
  - AC5: initialise `seen_ids: set[str] = set()` fresh for **each declaring pack** (scoped per-pack per spec.md AC1 — different packs may reuse the same id). Error on duplicate within a pack.
  - AC7: for each `consumers` ref → `_resolve_primitive_ref(ref, pack_dir)` → error if False
  - AC9: `entry["pack"] == declaring_name` → error
  - AC10: `entry.get("version")` is not None and `_is_valid_semver_range(v)` is False → error
  - AC11/AC12: if `entry["pack"]` in `all_pack_dirs`, check each `providers` ref
    via `_resolve_primitive_ref(ref, all_pack_dirs[target])` → error if False;
    if target is absent → skip provider check (no error, AC11)
- All errors use code `CAT-V-019`

**Note:** AC6 (`kind` enum) and AC8 (`when`/`purpose`/`fallback` non-empty)
are enforced by the schema in step 3. Step 19 does NOT re-implement these.
AC8 is verified by `test_integration_empty_when_fails` in
`test_catalogue_wave2_schema.py`; the validation stub omits it.

Insert in `_VERIFY_STEPS`:
```python
(19, "pack integration validation", _step_integration_validation),
```
Appended at the end of the list. Runs only after steps 1–18 pass.
Since step 3 validates the schema (which catches invalid kinds and empty text),
step 19 only fires on schema-valid pack.tomls.

**Done when:** All nine validation tests pass.

---

### Task 3 — Show output: surface `integrations` in `show.py` (AC13-AC16)

**Verification mode:** TDD
**Depends on:** Task 1

**Tests (add to `tests/integration/test_show_cmd.py`):**

```python
# STUB: AC14 + AC15 — JSON includes integrations when declared
def test_show_integrations_json_present_when_declared(tmp_path, capsys): ...

# STUB: AC14 + AC16 — JSON has integrations: [] when not declared
def test_show_integrations_json_empty_when_not_declared(tmp_path, capsys): ...

# STUB: AC13 + AC15 — table includes integrations row when declared
def test_show_integrations_table_row_when_declared(tmp_path, capsys): ...

# STUB: AC13 + AC16 — table shows "-" when no integrations
def test_show_integrations_table_row_shows_dash_when_absent(tmp_path, capsys): ...
```

Also update `test_json_exact_keys_sorted_arrays_source_catalogue` to include
`"integrations"` in the expected key set.

**Approach:**

In `run()`, extract:
```python
integrations = pack.get("integrations") or []
```

Extend `_emit()` signature with `integrations: list[dict]`:
- JSON path: add `"integrations": integrations` (with `"version": None` for absent
  version fields in each entry — use `e.get("version")` not `e["version"]`)
- Table path: add row `["integrations", summary]` where:
  - `summary = ", ".join(f"{e['id']} ({e['kind']} → {e['pack']})" for e in integrations)` when non-empty
  - `"-"` when empty

In `_degrade()`: pass `integrations=[]` (degrade has no TOML — an empty array
surfaces nothing visible; no key is hidden). The degrade path is not extended.

**Done when:** Four new tests pass; key-set assertion updated and green.

---

### Task 4 — Pilot entries: add `[[pack.integrations]]` to core and governance-extras (AC17-AC21)

**Verification mode:** Goal-based + manual QA
**Depends on:** Task 1, Task 2, Task 3

**Done when:**
- `agentbundle catalogue verify --root .` exits 0
- `agentbundle show core --format json` returns entries with IDs
  `"frontend-preflight-augment"` and `"frontend-cold-reviewer"`
- `agentbundle show governance-extras --format json` returns entries with IDs
  `"promoted-research-evidence"`, `"design-proposal-product-engineering"`,
  `"design-proposal-architect"`

**Approach:**

Add to `packs/core/pack.toml`:

```toml
[[pack.integrations]]
id = "frontend-preflight-augment"
pack = "frontend-engineering"
kind = "augment"
role = "Frontend pre-flight augmentation"
consumers = ["skill:work-loop"]
providers = ["skill:frontend-engineering"]
when = "The target repository declares HTML/CSS/JS as a primary output and the frontend-engineering pack is installed."
purpose = "Inline the frontend-engineering skill into the work-loop pre-EXECUTE gate when the build produces an HTML/CSS/JS primary artifact."
fallback = "If frontend-engineering is absent, work-loop records a named skip (FE pre-flight: skipped) and continues without the FE gate."

[[pack.integrations]]
id = "frontend-cold-reviewer"
pack = "frontend-engineering"
kind = "review"
role = "Frontend cold reviewer"
consumers = ["skill:work-loop"]
providers = ["agent:frontend-reviewer"]
when = "The diff's primary output is HTML/CSS/JS and the frontend-engineering pack is installed."
purpose = "Run the frontend-reviewer agent during work-loop REVIEW for diffs whose primary output is HTML/CSS/JS."
fallback = "If frontend-engineering is absent, the REVIEW phase skips the frontend-reviewer and records a named skip."
```

Add to `packs/governance-extras/pack.toml`:

```toml
[[pack.integrations]]
id = "promoted-research-evidence"
pack = "desk-research"
kind = "input"
role = "Promoted research evidence"
consumers = ["skill:new-rfc"]
providers = ["skill:desk-research", "skill:desk-research-project-synthesize"]
when = "A desk-research project has produced synthesized findings that inform the RFC being drafted."
purpose = "Provide structured research evidence from a completed desk-research project as an input artifact to the RFC drafting workflow."
fallback = "If desk-research is absent, new-rfc proceeds without promoted evidence and notes the missing input in the RFC context block."

[[pack.integrations]]
id = "design-proposal-product-engineering"
pack = "product-engineering"
kind = "input"
role = "Design proposal"
consumers = ["skill:new-rfc"]
providers = ["skill:frame-intent", "skill:de-risk-intent"]
when = "A product-engineering shaping artifact (frame-intent or de-risk-intent output) is ready and informs the RFC under authorship."
purpose = "Feed a product-engineering design proposal into the RFC drafting workflow as a typed input artifact."
fallback = "If product-engineering is absent, new-rfc proceeds without the design proposal input and notes the gap."

[[pack.integrations]]
id = "design-proposal-architect"
pack = "architect"
kind = "input"
role = "Design proposal"
consumers = ["skill:new-rfc"]
providers = ["skill:architect-design", "skill:architect-review"]
when = "An architect design or review artifact is available and shapes the technical decisions captured in the RFC."
purpose = "Feed an architect design or review output into the RFC drafting workflow as a typed input artifact."
fallback = "If architect is absent, new-rfc proceeds without the architecture design proposal and notes the gap."
```

Bump versions:
- `packs/core/pack.toml`: `0.15.6` → `0.15.7`
- `packs/core/.claude-plugin/plugin.json`: `0.15.6` → `0.15.7`
- `packs/governance-extras/pack.toml`: `0.9.2` → `0.9.3`
- `packs/governance-extras/.claude-plugin/plugin.json`: `0.9.2` → `0.9.3`

Run `make build-self` to reproject `dist/claude-plugins/core/` and
`dist/claude-plugins/governance-extras/`.

---

### Task 5 — Authoring hub: replace placeholder with section 11 (AC22-AC25)

**Verification mode:** Goal-based (greppable checks + sync tool)
**Depends on:** none

**Done when:**
- Wave 2 placeholder removed (Wave 4 Journey placeholder must remain):
  `grep -c "Wave 2 of the catalogue-contracts initiative"
  guides/_shared/reference/catalogue-authoring-standards.md` returns 0 (AC22)
- Section 11 header exists: `grep -c "^## 11\. Optional pack integrations"
  guides/_shared/reference/catalogue-authoring-standards.md` returns 1 (AC22)
- Contract citation present: `grep -c "contracts/pack.schema.json"
  guides/_shared/reference/catalogue-authoring-standards.md` ≥ 1 (AC22)
- Four kind values documented: `grep -c "input.*augment.*review.*handoff"
  guides/_shared/reference/catalogue-authoring-standards.md` ≥ 1 (AC22)
- Ten-field table header present: `grep -c "Field.*Type.*Required.*Description"
  guides/_shared/reference/catalogue-authoring-standards.md` ≥ 1 (AC22)
- No governance citations: `grep -E "RFC-|ADR-|docs/specs/"
  guides/_shared/reference/catalogue-authoring-standards.md` returns nothing
  in the new section 11 text (AC25)
- `python3 tools/catalogue/sync_authoring_scaffold.py --check` exits 0 (AC23/AC24)

**Verification mode note:** The spec lists AC22-25 as "visual/manual QA" — these
greps are the manual-QA checklist items, each anchoring a required content
element from spec.md AC22. They are deterministic assertions, not prose descriptions.

**Approach:**

Replace the unnumbered placeholder section in
`guides/_shared/reference/catalogue-authoring-standards.md` with:

```markdown
## 11. Optional pack integrations

**Contract:** `contracts/pack.schema.json` (`[[pack.integrations]]` array)

A pack can declare optional behavior seams with other packs using the
`[[pack.integrations]]` array table in `pack.toml`. The entire array is
optional — packs without integrations remain fully valid and installable.

**The ten fields** (all fields in each entry are required except `version`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique kebab-case identifier within this pack |
| `pack` | string | yes | Name of the target pack |
| `kind` | string | yes | One of: `input`, `augment`, `review`, `handoff` |
| `role` | string | yes | Short user-facing label for this integration |
| `consumers` | string[] | yes | Type-qualified primitive refs in the declaring pack |
| `providers` | string[] | yes | Type-qualified primitive refs in the target pack |
| `when` | string | yes | Human-readable conditions under which this seam activates |
| `purpose` | string | yes | What the integration achieves when active |
| `fallback` | string | yes | What the consuming skill does when the target pack is absent |
| `version` | string | no | Semver range of the target pack version |

**The four `kind` values:**

- `input` — the target provides an artifact the declaring pack's skill reads
- `augment` — the target pack's skill is inlined into the consuming skill's workflow
- `review` — the target pack's agent or skill is invoked as a reviewer pass
- `handoff` — the consuming skill passes control to the target at a defined boundary

**What integrations are not:**

No auto-install (declaring an integration does not install the target pack), no
dependency closure (`[pack.dependencies]` owns hard requirements), no executable
`when` expressions (the `when` field is explanatory text only).

**The `fallback` requirement:**

Every integration must declare what the consuming skill does when the target is
absent. An agent reading the integration without the target installed needs to
know how to proceed.

**Lint and verify:**

\`\`\`bash
agentbundle catalogue verify --root .
\`\`\`

Primitive refs (e.g., `"skill:work-loop"`) are validated against the declaring
and target packs' `.apm/` directories. An absent target pack does not fail
verification — the check is portable across catalogues that may not include
every optional pack.
```

After editing the live file, run
`python3 tools/catalogue/sync_authoring_scaffold.py` (no `--check`) to write
the scaffold copy, then verify with `--check`.

---

### Task 6 — Version bump and changelog (AC26-AC27)

**Verification mode:** Goal-based
**Depends on:** none

**Done when:**
- `grep "0.27.0" packages/agentbundle/pyproject.toml` matches
- `grep "0.27.0" packages/agentbundle/agentbundle/version.py` matches
- `grep "0.27.0\|Unreleased" docs/product/changelog.md` matches an entry
  that names the four items (schema, validation, show, pilots)
- At least one commit in the PR has `Engine-Change-RFC: RFC-0076`

**Approach:**

1. `packages/agentbundle/pyproject.toml`: `version = "0.26.1"` → `"0.27.0"`
2. `packages/agentbundle/agentbundle/version.py`: `CLI_VERSION = "0.26.1"` → `"0.27.0"`
3. `docs/product/changelog.md`: add entry under `[Unreleased]`:

```markdown
- **`agentbundle` 0.27.0 — `[[pack.integrations]]` convention**: packs can
  now declare optional cross-pack behavior seams in `pack.toml`. The new
  `[[pack.integrations]]` array (governed by `contracts/pack.schema.json`)
  carries ten fields: `id`, `pack`, `kind` (`input`/`augment`/`review`/
  `handoff`), `role`, `consumers`, `providers`, `when`, `purpose`,
  `fallback`, and an optional `version` semver range. `agentbundle catalogue
  verify` validates integration refs (uniqueness, primitive resolution,
  self-target prohibition, semver range grammar, provider presence when the
  target is in the same catalogue). `agentbundle show <pack>` surfaces
  declared integrations in table and JSON output. Five first-party
  integration entries ship across `packs/core` (two, targeting
  `frontend-engineering`) and `packs/governance-extras` (three, targeting
  `desk-research`, `product-engineering`, and `architect`).
```

The commit touching `contracts/pack.schema.json` and
`agentbundle/_data/pack.schema.json` must include
`Engine-Change-RFC: RFC-0076` in its message footer; the commit touching
`agentbundle/commands/show.py` similarly (per spec Boundaries).

---

## Commit plan

| Commit | Contents | Footers |
|--------|----------|---------|
| 1 (schema) | Task 1: schema + `_data/` sync + stub tests | `Engine-Change-RFC: RFC-0076`; `Spec: docs/specs/catalogue-wave2-pack-integrations/spec.md` |
| 2 (validation) | Task 2: verify.py step + validation tests | `Spec: docs/specs/catalogue-wave2-pack-integrations/spec.md` |
| 3 (show) | Task 3: show.py + show tests | `Engine-Change-RFC: RFC-0076`; `Spec: docs/specs/catalogue-wave2-pack-integrations/spec.md` |
| 4 (pilots) | Task 4: pack.toml files + plugin.json + build-self | `Spec: docs/specs/catalogue-wave2-pack-integrations/spec.md` |
| 5 (authoring hub) | Task 5: guide + scaffold sync | `Spec: docs/specs/catalogue-wave2-pack-integrations/spec.md` |
| 6 (version) | Task 6: version + changelog | `Spec: docs/specs/catalogue-wave2-pack-integrations/spec.md` |
