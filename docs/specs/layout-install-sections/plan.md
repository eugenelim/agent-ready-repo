# Plan: Catalogue install writes a layout section the skills read

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/agentbundle.md` § 7.1 records the
  measured drift, and names both reader classes — `workspace_mcp.py` and the
  skills. The `[backlog].open` entry at `workspace.toml:449` owns the defect and
  names both halves, the key/section mismatch and the fixture shape that hid
  it, which is why one spec closes it. The analogous implementation is
  `install.py::_append_install_marker`: same read, sanitise, re-emit shape, same
  jail — a shape precedent only, since it appends unconditionally and never
  replaces an entry (`install.py:3126-3136`). Tests live at
  `packages/agentbundle/tests/unit/test_append_layout_section.py`;
  `packages/AGENTS.md` § Test conventions assigns homes by assertion owner.
  Named uncertainty: adopter files cannot be observed, so nothing here can tell
  whether an adopter has hand-authored a section under a name no pack declares.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records
> its baseline. After approval, `spec.md` and `plan.md` are pinned in
> substance; only lifecycle bookkeeping is permitted, and execution
> observations belong in
> `docs/specs/layout-install-sections/notes/verification-ledger.md`. A genuine
> artifact error follows the controlled-amendment path.

## Approach

The installer reads the wrong key and writes the wrong section name. Correcting
the key alone is not safe, because the code that runs once the append is
reachable rebuilds the whole file from that key and discards everything else —
so the rebuild has to go in the same change.

Where the section name comes from is the decision that sizes this work. Deriving
it from the pack name would mean moving 23 skill bodies and the document corpus
onto that vocabulary, because a skill resolves its section by prose instruction
to the agent and cannot consult a Python alias table. Declaring it in the
manifest instead means the installer writes exactly what each pack's skills
already read, and no skill body, guide or convention page changes. That is the
route taken; the vocabulary move is logged separately.

The resolver is untouched. Skills do not read through it, so it cannot make an
installed default findable or unfindable. One bug in it is in scope, because
this change activates it: it anchors a relative configured value to the process
working directory, and writing repo-relative defaults turns a path reachable
only by hand-authored config into the common one.

## Constraints

- `packages/agentbundle/` is a protected tree with only `build/recipes/` and
  `/tests/` carved out, so every commit touching the installer, the resolver or
  `_data/` carries `Engine-Change-RFC: RFC-0040`.
- The two `pack.schema.json` copies are byte-parity gated; they move in one
  commit or the gate fails. `_data/pack.schema.json` is a maintained copy, not
  generated — the hand copy is correct and the gate is what catches a one-sided
  move.
- `packages/AGENTS.md` cross-package traps bind: `tmp_path` rather than
  `mkdtemp`, explicit `encoding="utf-8"`, no hardcoded `/tmp`, and
  `AGENTBUNDLE_USER_ROOT` set with `HOME` for any user-scope case.
- `packages/agentbundle/AGENTS.md` says to normalize CRLF before byte
  comparisons of *checked-out text*. That does not apply to these fixtures: the
  test writes them with explicit line endings, and normalising erases the
  difference AC2 and AC3 exist to detect.
- `safety.write_jailed` and `config._emit_basic_string` stay on the path. They
  are security controls, not implementation detail.
- `packs/AGENTS.md` § Version bump rule governs each edited pack;
  `packs/AGENTS.local.md` governs the engine bump.

## Construction tests

`packages/agentbundle/tests/unit/test_append_layout_section.py` holds the
installer cases; it is also the file whose fixture shape let this through,
passing `pack_name="research"` with a `parent` key — a combination no pack
produces. Its fixtures are re-pointed at the real manifests.

`test_reemit_drops_tampered_existing_parent`'s two assertions are **deleted**,
not amended: they state the data loss as the contract.

Preservation fixtures are literal bytes, not serialised from a dict — a
serialised fixture cannot carry the comment AC2 is about or the line ending AC3
is about. Each asserts the exact complete result, because a survival-only
assertion passes on a file nobody wrote to.

The anchoring case (AC7) belongs with the resolver's own tests and runs with a
working directory other than the repository root.

The document and schema checks (AC6, AC8, AC9, AC10) are catalogue rules and
belong in the repository's `tests/conformance/`, not under
`packages/agentbundle/tests/` — that tree ships to adopters, where no `packs/`
directory exists and a derivation over `packs/*/pack.toml` would enumerate an
empty set and pass on empty state.

## Durable-output map

| Spec output | Task | Evidence |
| --- | --- | --- |
| Interface compatibility (`pack.schema.json`) | T1 | Parity gate green |
| User-facing promise (reference docs) | T4 | Corrected value, no comment-loss claim |
| Current architecture (`agentbundle.md` § 7.1) | T6 | Both reader classes agree |
| Release history (changelog) | T6 | An `agentbundle` entry and one per bumped pack |

## Design (LLD)

### Design decisions

**Why `section` is declared, not derived.** No function of the pack name yields
the section: `experience-design` writes `[design]`, `desk-research` writes
`[research]`. Deriving it would require moving the vocabulary, and the readers
that matter are prose instructions inside skill bodies, not code that could
consult a map. An installer-held table was rejected for the same reason it was
rejected in RFC-0040's design: a hand-maintained table far from the manifests it
describes is the shape that produced this defect.

**Why the key fix and the preservation fix are one change.** Correcting the key
is what makes the re-emit reachable. Shipped apart, either the release deletes
adopter sections, or the preservation fix must build its fixtures on `parent` —
the one shape no pack produces, which the backlog entry names as the reason the
original defect went unseen.

**Why the parse stays.** Two obligations still need it: refusing a file that
cannot be read, and detecting an occupied name. Neither needs the parsed values
written back.

**Why append rather than preserve-more-keys.** Preserving more keys means
enumerating what an adopter may have written, which is unknowable. Not
rewriting is the only approach whose correctness does not depend on that
enumeration.

**Why an occupied name refuses.** Today an occupying scalar or array is
silently destroyed and the output still parses — the loss is real, the invalid
TOML is not. Once the file is preserved rather than rebuilt, appending beside an
existing scalar of the same name *would* redeclare, so the refusal is a property
of the new design rather than a repair of the old. It costs the pack's default
on a file whose name is already taken, which is the lesser harm against
destroying what the adopter put there.

**Why the absent-file case stays silent.** It is the designed no-op and the
common case. Obliging a diagnostic there would emit one line per declaring pack
per scope on every install into a repository with no layout file.

**Why bytes, not text.** `read_text` folds CRLF and lone CR to LF, so a
text-mode read rewrites every Windows adopter's file. The decode stays inside
the refusal boundary: a non-UTF-8 file is caught today by the same `except` that
catches a parse failure, and moving the decode outside turns a warning into an
uncaught traceback.

**Why the resolver is otherwise untouched.** Skills resolve the layout file
themselves and never call it, so its coverage does not decide whether an
installed default is found. Its three-of-five coverage and the `[product]`
sharing are real, and logged.

### Data & schema

`[pack.layout.<scope>]` gains one optional string key, `section`. `parent` stays
in the schema: removing it is a separate compatibility question, and nothing
reads it once the installer stops.

### Interfaces & contracts

`_append_layout_section`'s signature is unchanged. It reads `section` and
`output_dir` instead of `parent`, names the table from `section` instead of
`pack_name`, and writes bytes-read-plus-one-table instead of a reconstruction.
Its refusals gain the non-UTF-8 case explicitly and widen the occupied-name case
from "is a table" to "is present".

### Failure, edge cases & resilience

An empty file takes the append path and yields one table. A file with no line
ending gets `\n`, there being no style to match. A pack declaring `output_dir`
but not `section`, or the reverse, appends nothing — the same no-op an absent
sub-table takes today, so a pack that has not opted in is unaffected.

## Tasks

### T1: Admit `section` in the pack schema

**Depends on:** none

**Tests:**
- A manifest carrying `section` inside `[pack.layout.repo]` validates; one
  carrying an unknown sibling does not. This is an engine-distribution
  assertion, so it lives in `packages/agentbundle/tests/unit/`. (AC10)
- The shipped parity gate compares the two copies byte-for-byte and must stay
  green. (AC10)

**Approach:**
- Add the key to `contracts/pack.schema.json` under both scope sub-tables and
  copy to `packages/agentbundle/agentbundle/_data/pack.schema.json`.

**Done when:** those checks pass.

### T2: Read `section` and `output_dir`, and append instead of re-emitting

**Depends on:** T1

**Tests:**
- A declaring pack appends `[<section>] output_dir = <output_dir>`; the result
  is the original bytes plus the separator plus that table. A pack missing
  either key appends nothing. (AC1)
- A file with comments, blank lines, adopter sections, an extra key inside a
  section, a nested sub-table and a top-level non-table value is otherwise
  byte-identical. (AC2)
- A CRLF file stays CRLF; a file without a trailing newline gains exactly one
  in its own style; one with a trailing newline gains none; a file with no line
  ending gains `\n`. (AC3)
- Undecodable, unparseable, and occupied-name-as-table/scalar/array each leave
  the file byte-identical and write the reason to stderr. (AC4)
- An absent file is not created and nothing is printed. (AC5)
- The injection round-trip stays green and is mutation-checked by removing the
  emitter call. (AC11)

**Approach:**
- Read with `read_bytes`; decode a throwaway copy inside the existing `try`.
- Widen the already-present check from "is a table" to "is present".
- Delete the section-rebuild loop and both drop-and-warn branches.
- Source the table name from `section` and the value from `output_dir`,
  returning early when either is not a string.
- Emit both through `_emit_basic_string`; write original bytes plus separator
  plus table through `safety.write_jailed`.
- Delete `test_reemit_drops_tampered_existing_parent`'s two assertions and
  re-point the suite's fixtures at the real manifests.

**Done when:** those cases pass and the mutation check confirms AC11 can fail.

### T3: Declare a section in each consuming pack

**Depends on:** T1

**Tests:**
- Every pack declaring `[pack.layout.<scope>]` declares a `section` equal to
  the section its own shipped skill bodies and reference docs instruct a reader
  to look in. Both sides derived from the repository. (AC6)

**Approach:**
- Add `section` to the five manifests: `architect` → `architecture`,
  `desk-research` → `research`, `experience-design` → `design`,
  `product-engineering` → `product`, `product-strategy` → `strategy`.
- Bump each edited pack's `pack.toml` and `.claude-plugin/plugin.json`.

**Done when:** the check passes and `agentbundle catalogue lint` is clean.

### T4: Correct the two documented facts this change falsifies

**Depends on:** none

**Tests:**
- `architect`'s manifest and both of its reference docs name
  `docs/architecture`; no `architect` surface names `docs/design`. (AC8)
- No `references/agentbundle-layout.md` claims the append fails to preserve
  comments or off-schema keys. The file set is derived. (AC9)

**Approach:**
- Change `architect`'s `output_dir` and the two reference docs' documented
  value.
- Remove the comment-loss sentence from the six reference docs that carry it;
  regenerate the `workspace-status` projections rather than editing them.
- Bump each edited pack.

**Done when:** both checks pass.

### T5: Anchor a repo-scope relative value to the repository root

**Depends on:** none

**Tests:**
- A relative `output_dir` in the repo-scope file resolves against the
  repository root, asserted from a working directory that is not the repository
  root. (AC7)

**Approach:**
- Resolve a repo-scope relative value against the resolver's own repository
  root instead of the ambient working directory. User-scope values stay
  absolute per RFC-0040.

**Done when:** that case passes and the resolver's existing tests stay green.

### T6: Record the release

**Depends on:** T2, T3, T4, T5

**Tests:**
- None of its own. Every obligation is discharged by another task's criterion
  or by the release gates.

**Approach:**
- Bump `pyproject.toml` and `agentbundle/version.py` together.
- Replace `agentbundle.md` § 7.1 with shipped behaviour, describing both reader
  classes.
- Retire the `[backlog].open` entry at `workspace.toml:449`.
- Add the changelog entries, resolving versions against `origin/main` at the
  time this runs.
- Record the probe outputs and the AC11 mutation-check result in
  `notes/verification-ledger.md`.

**Done when:** `make build-check` is green and the backlog entry is gone.

## Rollout

No migration and no flag. The append has never written a section from this
catalogue, so there is no prior state to reconcile, and an adopter with no
layout file is unaffected. An adopter who hand-authored a section keeps it: the
append never replaces one.

The data loss is not known never to have fired. The schema admits `parent` and
`agentbundle install` accepts an external catalogue, so a third-party pack
declaring it has been able to destroy adopter sections for as long as this has
shipped. The changelog says that rather than calling it latent.

One narrowing ships with the byte-preserving read: a file using lone-CR line
endings parses today only because `read_text` translates them, and is refused as
unparseable afterwards. It is reported, not silent.

## Risks

- **A fix that appends raw bytes disarms the injection control.** The
  round-trip test would pass with the emitter bypassed if the value were benign.
  T2 mutation-checks it.
- **Preservation assertions that only check survival cannot fail.** The function
  returns before writing for any shipped manifest today, so a survival-shaped
  test passes on an untouched file. Every case asserts the exact complete result
  and sources its manifest from the catalogue.
- **A declared section drifts from what the skills read.** That is the defect
  this repairs, reintroduced. AC6 derives both sides rather than comparing
  against a list, so a skill body edited later fails the check.
- **A bump collides.** Peer sessions claim versions concurrently; this
  repository collided twice in one day. Resolve every version against
  `origin/main` when T6 runs.

## Changelog

- 2026-09-10 — drafted as `layout-default-append`; premise invalidated in
  review.
- 2026-09-11 — re-drafted on pack-keyed sections, merged with the preservation
  fix, then cut back after review established that skills resolve sections by
  prose instruction and cannot consult an alias table — which makes a declared
  `section` the only route that repairs the install without moving the
  vocabulary. The vocabulary move is logged as separate work.
