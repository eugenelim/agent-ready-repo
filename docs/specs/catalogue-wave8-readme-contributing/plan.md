# Plan: catalogue-wave8-readme-contributing

- **Status:** Done
- **Superseded by:** [`documentation-entry-navigation`](../documentation-entry-navigation/plan.md)
- **Spec:** [`spec.md`](spec.md)

## Mode and declined patterns

Mode: full (public interface: README.md and CONTRIBUTING.md are public-facing documents
shipped to all adopters; structural: adds a named subsection to README.md; multi-feature:
README subsection + fork-language verification + pack table currency + CONTRIBUTING updates).

Declined:
- Tempted to automate README pack table from `pack.toml` files; declining — requires
  build-pipeline coupling that does not exist today; curated subset is the explicit spec
  decision (Wave 8 Assumption in spec).
- Tempted to update `docs/architecture/catalogue.md` fork-language; declining — that is
  a maintainer-facing architecture doc, not in Wave 8 scope (deferred per spec Assumption).
- Tempted to add a link to the future `/evaluate/` marketing page; declining — Wave 7
  scope; spec says use authoring hub as interim evaluate entry point.
- Tempted to add a `[[pack.integrations]]` authoring rule in detail; declining — contract
  ships in Wave 2; CONTRIBUTING carries only a forward-reference (spec AC8).

## Pre-EXECUTE self-coverage checks

- Domain claim: `guides/_shared/reference/catalogue-authoring-standards.md` exists.
  Verified at spec time (shipped in Wave 1).
- Domain claim: `guides/_shared/how-to/create-a-catalogue.md` exists.
  Verified at spec time (Wave 1 uses it as the redirect target).
- Domain claim: Wave 2's `[[pack.integrations]]` convention shipped with Wave 2 (0.27.0).
  Wave 8 updates all "in progress" forward-references to say "shipped in Wave 2; see
  the authoring hub for the full contract spec." Do not describe the full schema in
  CONTRIBUTING — the note remains navigational.
- Resolve-vs-surface: no open questions blocking this wave — Wave 1 shipped the
  foundation (D1–D4). Wave 8 is a documentation convergence pass.

## Task list

```
T1  README "Evaluate or build a catalogue" subsection   Depends on: none
T2  README fork-language verification                   Depends on: T1
T3  README pack table currency note                     Depends on: T1
T4  README pack descriptions currency check             Depends on: T1
T5  CONTRIBUTING authoring hub pointer                  Depends on: none
T6  CONTRIBUTING where-to-find table update             Depends on: T5
T7  CONTRIBUTING integration forward-reference          Depends on: T5
T8  CONTRIBUTING fork-language verification             Depends on: T5
T9  Regression + closeout                               Depends on: T1–T8
```

Parallel first wave: T1 (README) and T5 (CONTRIBUTING) — one per file.
Second wave: T2, T3, T4 (all serialize behind T1 on README.md);
T6, T7, T8 (serialize behind T5 on CONTRIBUTING.md) — can run in parallel across files.

---

## T1 — README § "Evaluate or build a catalogue" subsection

**Verification mode:** goal-based

**Touches:**
- `README.md`

**Tests:** none (goal-based)

**Approach:**

Locate README.md § "The catalogue". The Wave 1 PR added a `catalogue init` paragraph at
the end of this section. Absorb that paragraph into a new `### Evaluate or build a catalogue`
subsection:

```markdown
### Evaluate or build a catalogue

**Evaluating?** The [portable authoring hub](../../../guides/_shared/reference/catalogue-authoring-standards.md)
explains the catalogue structure, available contracts, and how to assess whether the
catalogue model fits your organisation's needs.

**Building?** Run `agentbundle catalogue init <target>` to scaffold a new catalogue in
`<target>`. See [Create a catalogue](../../../guides/_shared/how-to/create-a-catalogue.md) for
a walkthrough.
```

Remove the original `catalogue init` paragraph from the end of "The catalogue" section
to avoid duplication. Verify the navigation link strip at the top of README.md has a link
that covers the "The catalogue" section (or add `### Evaluate or build a catalogue` to
the strip if the strip uses `###`-level headings). Do not add a dead link.

**Done when:**
- `grep -q "Evaluate or build a catalogue" README.md` exits 0
- `grep -q "catalogue-authoring-standards.md" README.md` exits 0
- `grep -q "create-a-catalogue.md" README.md` exits 0

---

## T2 — README fork-language verification

**Verification mode:** goal-based

**Touches:**
- `README.md` (read-only unless stale fork language found)

**Tests:** none (goal-based)

**Approach:**

Run `grep -n "fork it as your own\|fork this catalogue\|clone this repo\|fork.*adopt" README.md`.
If any match is found (beyond what Wave 1 already removed), remove or rewrite the phrase
to use the `agentbundle catalogue init` path. Do not remove adopt-by-init language.

**Done when:** `! grep -qE "fork it as your own|fork this catalogue|clone this repo" README.md` exits 0 (no matches for any adopt-by-fork phrase).

---

## T3 — README pack table currency note

**Verification mode:** goal-based

**Touches:**
- `README.md`

**Tests:** none (goal-based)

**Approach:**

Locate the pack table in `## The catalogue` section. Add a note or caption directing
readers to `agentbundle list-packs` for the full catalogue. Position it immediately before
or after the table (not as an inline table cell). Example:

```markdown
> Full catalogue: run `agentbundle list-packs` to see all available packs.
```

Scope the grep verification to the `## The catalogue` section to avoid false-positives
from the Quick Start section (which already contains `agentbundle list-packs`).

**Done when:**
Within the `## The catalogue` section (grep between `## The catalogue` and the next `## `
heading), `grep -q "list-packs"` exits 0 and the match is positioned before/after the
table (not in Quick Start).

---

## T4 — README pack descriptions currency check

**Verification mode:** visual / manual QA

**Touches:**
- `README.md` (update stale descriptions only)

**Tests:** none (manual QA)

**Approach:**

For each pack row in the README.md table:
1. Read the `description` field from that pack's `pack.toml`.
2. Compare to the README.md table cell.
3. If description has drifted, update the table cell to match `pack.toml`.
4. If no descriptions have drifted, record "No description drift found" in the PR
   description as evidence of the verification.

**Done when:** PR description notes verification outcome; any stale descriptions corrected.

---

## T5 — CONTRIBUTING authoring hub pointer

**Verification mode:** goal-based

**Touches:**
- `CONTRIBUTING.md`

**Tests:** none (goal-based)

**Approach:**

Locate the `### Adding a new pack` section in `CONTRIBUTING.md`. Add a step 0 or
prominent note before the numbered steps:

```markdown
> Before starting: familiarise yourself with the
> [portable authoring standards](../../../guides/_shared/reference/catalogue-authoring-standards.md)
> — it covers the expected pack structure, JOURNEY.md convention, and contract files.
```

**Done when:** Within the "Adding a new pack" section, `grep -q "catalogue-authoring-standards.md"` exits 0.

---

## T6 — CONTRIBUTING "Where to find authoritative information" table

**Verification mode:** goal-based

**Touches:**
- `CONTRIBUTING.md`

**Tests:** none (goal-based)

**Approach:**

Locate the "Where to find authoritative information" table. Add a new row:

```markdown
| Catalogue authoring standards and contracts | [`guides/_shared/reference/catalogue-authoring-standards.md`](../../../guides/_shared/reference/catalogue-authoring-standards.md) |
```

**Done when:** Within the "Where to find authoritative information" table section,
`grep -q "catalogue-authoring-standards.md"` returns a match that includes
"Catalogue authoring" in the same line or adjacent row.

---

## T7 — CONTRIBUTING integration forward-reference

**Verification mode:** goal-based

**Touches:**
- `CONTRIBUTING.md`

**Tests:** none (goal-based)

**Approach:**

In the `### Adding a new pack` section, after the main numbered steps, add a note:

```markdown
**Optional cross-pack composition:** If the pack declares optional composition with other
packs, add `[[pack.integrations]]` entries to `pack.toml`. The `[[pack.integrations]]`
convention shipped with Wave 2 (0.27.0); see the
[authoring hub](../../../guides/_shared/reference/catalogue-authoring-standards.md) for the
full contract spec.
```

The note must name `[[pack.integrations]]` and state it shipped in Wave 2. It must not
define new schema or describe field semantics — navigational only.

**Done when:** Within the "Adding a new pack" section, `grep -q "pack.integrations"` exits 0
and the note references "shipped in Wave 2" or equivalent to indicate the convention is live.

---

## T8 — CONTRIBUTING fork-language verification

**Verification mode:** goal-based

**Touches:**
- `CONTRIBUTING.md` (read-only unless stale fork language found)

**Tests:** none (goal-based)

**Approach:**

Run `grep -n "fork it as your own\|fork this catalogue\|fork.*adopt" CONTRIBUTING.md`.
If any match is found, remove or rewrite using the `agentbundle catalogue init` path.

**Done when:** `! grep -qE "fork it as your own|fork this catalogue" CONTRIBUTING.md` exits 0 (no matches for any adopt-by-fork phrase).

---

## T9 — Regression + closeout

**Verification mode:** goal-based

**Touches:**
- `docs/specs/catalogue-wave8-readme-contributing/spec.md` (Status: Implementing → Shipped)
- `workspace.toml` (move Wave 8 entry from queue to shipped)

**Tests:** none (goal-based)

**Approach:**

1. `SKIP_SAST=1 make build-check` — exits 0.
2. `! grep -q "fork it as your own" README.md CONTRIBUTING.md` — exits 0 (no matches).
3. `wc -l AGENTS.md` ≤ 250; `wc -l packs/AGENTS.md` ≤ 150.
4. Update spec.md Status: Shipped.
5. Move Wave 8 entry from `queue` to `shipped` in `workspace.toml` ini-007 work section.
6. Run `python3 tools/lint-spec-status.py --root .` to confirm spec status is clean.

**Done when:**
- All six checks above pass
- Spec Status shows Shipped
- workspace.toml correctly reflects Wave 8 as shipped

## Constraints

- No Wave 8 task may touch `agentbundle/_data/` — this wave is docs only (spec Never do).
- T4 (pack descriptions) is manual QA — record verification outcome in PR description.
- `[[pack.integrations]]` must remain a forward-reference only — do not define schema.

## Risks

- The README.md "The catalogue" section layout may have changed since Wave 1. Read
  the current section in full before adding the subsection to ensure no duplication.
- The CONTRIBUTING.md "Where to find authoritative information" table may not exist yet;
  if absent, create it with at least the new row and a brief intro line.
- Wave 2 has shipped `[[pack.integrations]]` (0.27.0). T7's note says "shipped in
  Wave 2; see the authoring hub for the full contract spec." This is the current ground
  truth, not a conditional risk.
