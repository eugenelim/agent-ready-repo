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
produces. Its fixtures become literal manifests of the shape production now
supplies. They are not read from `packs/`: this tree ships to adopters, where
no catalogue exists. AC6 is what binds the literals to the shipped manifests,
and it runs repository-only.

`test_reemit_drops_tampered_existing_parent`'s two assertions are **deleted**,
not amended: they state the data loss as the contract.

Preservation fixtures are literal bytes, not serialised from a dict — a
serialised fixture cannot carry the comment AC2 is about or the line ending AC3
is about. Each asserts the exact complete result, because a survival-only
assertion passes on a file nobody wrote to.

The anchoring case (AC7) belongs with the resolver's own tests and runs with a
working directory other than the repository root.

The document and schema checks (AC6, AC8, AC9, AC9) are catalogue rules and
belong in the repository's `tests/conformance/`, not under
`packages/agentbundle/tests/` — that tree ships to adopters, where no `packs/`
directory exists and a derivation over `packs/*/pack.toml` would enumerate an
empty set and pass on empty state.

## Durable-output map

| Spec output | Task | Evidence |
| --- | --- | --- |
| Interface compatibility (`pack.schema.json`) | T1 | Parity gate green |
| User-facing promise (reference docs) | T4 | Corrected value, no comment-loss claim |
| Current architecture (`agentbundle.md` § 7.1) | T4 | Both reader classes agree |
| Release history (changelog) | T4 | An `agentbundle` entry and one per bumped pack |

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

**One refusal contract, not eight.** The spec's "best-effort maintenance"
section owns this; the tasks derive from it rather than re-deciding per state.
Operationally it means `_append_layout_section` never propagates an exception.
The jail refusal that currently raises `PathJailError` becomes report-and-
return; so does the read side, including `safety.user_state_path` raising
before the file-existence check. Only then does the call-site `except` narrow
to the marker call, which keeps its fatal exit — narrowing first would convert
an absorbed failure into an uncaught traceback after files are projected.

Rounds 2 and 3 each answered this question per-state and got a different answer
each time, so the spec's table now fixes one verdict per state in evaluation
order, and the tasks below implement that table rather than reasoning about
states individually.

**Why the designed no-ops stay silent.** Three states write nothing by
contract: no layout file, the section already present as a table, and a pack
declaring only one of the two keys. Each is the common case on some install —
the first on any repository without a layout file, the second on every
re-install of a configured pack, the third on every pack in the catalogue that
declares no layout at all. A diagnostic on any of them prints once per pack per
scope for a path that is working correctly. Only the three error states report.

**Why a layout failure must not fail the install.** The call site treats an
`OSError` or a jail refusal as fatal and returns 1. That has never fired,
because the write has never executed. Once it does, a read-only layout file
would abort an install whose files are already projected — a total failure over
an optional maintenance step. The append reports and yields instead.

**Why mode and symlinks need their own observations.** `write_jailed` creates
its temp file privately and the atomic replace carries that mode onto the
target, so an adopter's group-readable file silently becomes owner-only; and a
symlinked target is replaced by a regular file, stranding whatever it pointed
at. Both are invisible to a byte comparison, which is why AC12 and AC13 observe
the stat mode and the link rather than the contents. The reader already refuses
a symlinked layout file, so refusing to write one makes the two agree.

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
  assertion, so it lives in `packages/agentbundle/tests/unit/`. (AC9)
- The shipped parity gate compares the two copies byte-for-byte and must stay
  green. (AC9)

**Approach:**
- Add the key to `contracts/pack.schema.json` under both scope sub-tables,
  with the `^[a-z0-9][a-z0-9-]*$` pattern rather than a bare string type, and
  copy to `packages/agentbundle/agentbundle/_data/pack.schema.json`.

**Done when:** those checks pass.

### T2: Read `section` and `output_dir`, and append instead of re-emitting

**Depends on:** T1, T3

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
- One case per *report* row of the spec's state table, exercised individually:
  bad `section` class, out-of-root `output_dir`, symlinked path, unopenable
  file and unpreparable user-state directory, undecodable, unparseable,
  occupied by scalar or array, and a failing write. Each leaves the file
  byte-identical and emits one stderr line. (AC4)
- One case per *silent* row: absent file, section already present as a table,
  pack declaring only one key. Nothing written, nothing printed. (AC5)
- A state matching two rows takes the earlier verdict: a re-install whose
  section is present *and* whose `output_dir` is out of root reports. (AC5)
- Every reporting row leaves `install`'s exit status and projected files
  unaffected — including the read-side rows, which today the wide `except`
  absorbs as a failed install. A marker write failure still exits non-zero.
  (AC11)
- A group-readable layout file has the same stat mode after the append. (AC12)
- A symlinked layout file is refused, still a symlink afterwards, with no
  exception escaping the function. (AC13)
- An `output_dir` resolving outside the scope's root — absolute, `~`-anchored,
  or via `..` — is refused and reported. (AC14)
- A `section` outside the character class is refused at the schema and at the
  install site. (AC15)
- The injection round-trip stays green and is mutation-checked by removing the
  emitter call. (AC10)

**Approach:**
- Read with `read_bytes`; decode a throwaway copy inside the existing `try`.
- Widen the already-present check from "is a table" to "is present", and route
  the table case to the silent return while scalar and array report.
- Refuse a symlinked target before writing, matching the resolver, reporting
  rather than raising.
- Confine the resolved `output_dir` to the scope's root before writing, and
  refuse a `section` outside `^[a-z0-9][a-z0-9-]*$`.
- Carry the target's existing mode across the atomic replace.
- Do not widen the call-site `except`. `_append_layout_section` handles every
  reporting state internally and returns, so it never reaches that handler;
  the handler then narrows to `_append_install_marker` alone, which keeps its
  fatal exit. These are one mechanism, not two: the function absorbs, and the
  call site stops catching for it.
- Delete the section-rebuild loop and both drop-and-warn branches.
- Source the table name from `section` and the value from `output_dir`,
  returning early when either is not a string.
- Emit both through `_emit_basic_string`; write original bytes plus separator
  plus table through `safety.write_jailed`.
- Delete `test_reemit_drops_tampered_existing_parent`'s two assertions.
- Rewrite `test_symlink_layout_file_fails_closed`: it asserts
  `pytest.raises(PathJailError)` out of the function, which the refusal
  contract replaces with report-and-return. It also covers only an out-of-tree
  link, which `assert_under` already refuses; the in-tree case AC13 is about is
  untested today and is added.
- Build the unit fixtures as literal manifests in the test tree, not by reading
  `packs/`. That tree ships to adopters, where no catalogue exists; AC6 is what
  binds the literals to the shipped manifests, and it runs repository-only.

**Done when:** those cases pass and the mutation check confirms AC10 can fail.

### T3: Declare a section in each consuming pack

**Depends on:** T1, T5

**Tests:**
- Every pack declaring `[pack.layout.<scope>]` declares a (`section`,
  `output_dir`) pair that one `references/agentbundle-layout.md` under that
  pack documents together, with the walked set's size asserted. Derived from
  the repository, so it runs in `tests/conformance/` where the catalogue is
  present. (AC6)

**Approach:**
- Add `section` to the five manifests: `architect` → `architecture`,
  `desk-research` → `research`, `experience-design` → `design`,
  `product-engineering` → `product`, `product-strategy` → `strategy`.
- Do not bump here. T4 is the single bump moment for every pack this change
  touches; `architect` is edited by both tasks, and bumping in each would
  advance it twice and leave one version naming no released code state.

**Done when:** the check passes and `agentbundle catalogue lint` is clean.

### T4: Correct what this change falsifies, and record it

**Depends on:** T2, T3, T5

**Tests:**
- `architect`'s manifest and both of its `references/agentbundle-layout.md`
  files name `docs/architecture`. Scoped to those three files: two
  `evals.json` assertions name `docs/design` deliberately, as negatives, and
  must survive. (AC8)

**Approach:**
- Change `architect`'s `output_dir` and the two reference docs' documented
  value.
- Remove the comment-loss sentence from every `references/agentbundle-layout.md`
  that carries it, file set derived; regenerate the `workspace-status`
  projections rather than editing them, and run `make build-self` so the
  self-host drift gate sees them. No criterion: this is a documentation
  correction, owned by the Durable outputs' user-facing-promise row.
- Replace `agentbundle.md` § 7.1 with shipped behaviour, describing both reader
  classes. Owned by the Durable outputs' current-architecture row.
- Retire the `[backlog].open` entry at `workspace.toml:449`.
- Bump every pack this change touches, once each — the five edited in T3 plus
  any edited here — and `pyproject.toml` with `agentbundle/version.py` together
  for the engine changes in T2 and T5. This is the only task that bumps.
  Resolve each version against `origin/main` at the time it runs.
- Write the changelog: one `agentbundle` entry and one per bumped pack. The
  release-impact gate accepts a version bump *or* a changelog edit as its
  indicator, so the bumps above satisfy it with no changelog at all — the entry
  has to be its own completion condition. It states the adopter-visible
  changes: byte preservation, the occupied-name refusal, the lone-CR
  narrowing, and that the third-party `parent` data loss could already fire.
- Record the probe outputs and the AC10 mutation-check result in
  `notes/verification-ledger.md`.

**Done when:** AC8 passes, `make build-check` is green, the backlog entry is
gone, and `docs/product/changelog.md` carries an `agentbundle` entry plus one
for each pack bumped by this change.

### T5: Anchor a repo-scope relative value, and refuse a relative user-scope one

**Depends on:** none

**Tests:**
- A relative `output_dir` in the repo-scope file resolves against the
  repository root, asserted from a working directory that is not the repository
  root. (AC7)
- A relative `output_dir` in the user-scope file is not resolved, and the
  reason reaches stderr naming the file and the key. The assertion is on that
  message: `_read_scope` sits inside `contextlib.suppress(Exception)`, so an
  implementation that raises is indistinguishable from an unconfigured file and
  would pass an absence-based assertion. (AC7)

**Approach:**
- Make `_read_scope` scope-aware: anchor a repo-scope relative value to the
  resolver's own repository root, and surface a relative user-scope value rather
  than resolving it, per RFC-0040's Ask-first rule.
- T5 precedes T3, because declaring a section is what makes the installer write
  repo-relative defaults, and those are what carry a relative value into this
  path for the first time.

**Done when:** that case passes and the resolver's existing tests stay green.


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
  this repairs, reintroduced. AC6 derives both sides from the repository, scoped
  by matching the (section, base) pair against one documented pair — wide
  enough not to go red on `product-engineering`'s three named sections, and
  narrow enough that `discovery` carried on `product`'s base fails, because no
  document describes that pair.
- **A bump collides.** Peer sessions claim versions concurrently; this
  repository collided twice in one day. Resolve every version against
  `origin/main` when T4 runs.

## Changelog

- 2026-09-10 — drafted as `layout-default-append`; premise invalidated in
  review.
- 2026-09-11 — re-drafted on pack-keyed sections, merged with the preservation
  fix, then cut back after review established that skills resolve sections by
  prose instruction and cannot consult an alias table — which makes a declared
  `section` the only route that repairs the install without moving the
  vocabulary. The vocabulary move is logged as separate work.
