# RFC-0082: Test ownership boundaries and per-surface inclusion

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-07
- **Date closed:** 2026-08-08
- **Decision weight:** heavy
- **Related:** [ADR-0071](../adr/0071-pack-runtime-export-boundary-and-test-placement.md)
  (the pack-side companion this extends — and whose *"keeps catalogue-wide
  behaviour in the engine's own suite"* clause this RFC revisits),
  [`docs/specs/pack-test-boundary-remaining-packs/`](../specs/pack-test-boundary-remaining-packs/)
  (whose disposition record names the gap this closes),
  [`0082-notes/`](0082-notes/) (spike transcripts and the provisional
  first-cut ownership mapping)

## Reviewer brief

- **Decision:** who owns each test in this repository — the engine, the
  catalogue, a single pack, or a `tools/` script — where each owner's tests live,
  and which distribution surfaces carry them.
- **Recommended outcome:** accept.
- **Change if accepted:**
  - Four test owners, four homes: engine tests at `packages/<pkg>/tests/`,
    catalogue tests at a new repository-root `tests/`, pack tests at
    `packs/<pack>/tests/` (already ADR-0071's rule), and tools tests at `tools/`.
    Ownership is assigned per test **class**, because real modules are mixed.
  - Nothing testable lives inside `packages/<pkg>/<pkg>/` — the importable
    package — which is the engine's runtime export boundary.
  - Test inclusion is decided per surface *and per owner*: the sdist carries the
    engine suite; the catalogue channels (`catalogue package` archives and
    `agentbundle catalogue init`, in both tooling modes) carry the catalogue and pack
    suites; the wheel, zipapp, and vendored engine copy carry none.
  - Catalogue tests that ship must be **rule-shaped** — portable to any
    catalogue — not **roster-shaped**, which pins this repository's own content.
  - Two pure-stdlib enforcement instruments, both in-repo.
- **Affected surface:** four engine distribution surfaces plus two catalogue
  channels; 82 test modules to classify and relocate; the ten operative
  files that reference the current in-package test path, enumerated in
  *Evidence*; `packages/AGENTS.md`; `build/self_host.py`'s fixture guard plus its
  covering test; and five positive allowlists that exclude a root `tests/` by
  construction — `tools/lint-build.py`'s `RFC_AUTHORISED_DIRS`,
  `catalogue_tooling/package.py`'s `_DEFAULT_INCLUDE_DIRS` and
  `_SOURCE_INCLUDE_DIRS`, `sync_authoring_scaffold.py`'s `_SYNC_PAIRS`, and the
  `Makefile`'s `SAST_DIRS` scan roots. A new top-level `tests/` directory. No adopter-visible
  CLI change.
- **Stakes:** the boundary decisions are reversible; the classification is the
  costly part, because deciding an owner per module is judgement that does not
  compress. Shipped in two specs so the release-blocking half lands first.
- **Review focus:** (1) D1's new top-level `tests/` — the only irreversible ask,
  refused by the pre-PR build lint's allowlist until this RFC is Accepted, and the option ADR-0071
  explicitly declined; (2) that D6's taxonomy carves at the joints, especially
  the engine-test-borrowing-the-catalogue case; and (3) that D2's per-owner rule
  leaves every shipped suite actually *runnable* where it lands.
- **Not in scope:** any version bump *in this RFC* — the implementing changesets
  carry one; src layout; changing ADR-0071's `packs/<pack>/tests/` destination;
  relocating the existing `tools/test*.py` files, which stay put. (Moving
  tools-owned tests that currently sit *elsewhere* into `tools/` is in scope —
  the first cut found three.)

## The ask

**Recommendation (BLUF).** Give every test in this repository an **owner** — the
engine, the catalogue, one pack, or a `tools/` script — put each owner's tests in
its own tree, and decide distribution inclusion per surface *and per owner*.

Three terms, since a cold reader needs them up front. **The engine** is the
`agentbundle` Python package: the CLI and build machinery published to PyPI.
**The catalogue** is this repository's shippable content — `packs/`, `profiles/`,
`contracts/`, and the marketplace aggregate — which the engine installs into a
user's repository. A **pack** is one installable bundle of skills, subagents, and
hooks at `packs/<name>/`.

The concrete rule: `packages/<pkg>/<pkg>/` — the importable package directory —
is **the engine's runtime export boundary**, and nothing testable lives inside
it. Engine tests sit beside it at `packages/<pkg>/tests/`. Catalogue tests leave
the engine package entirely, for a new repository-root `tests/`. Pack tests stay
at `packs/<pack>/tests/`, where ADR-0071 already put them. The source
distribution then carries the engine suite; the catalogue channels carry the
catalogue and pack suites; the wheel, zipapp, and vendored engine copy carry
none.

This extends **ADR-0071**, which decided the same question one directory level
down. ADR-0071 established that a pack's `.apm/` subdirectory — the part
projected into an adopter's tree — is *that* boundary, and moved pack tests out
of it. Its reasoning transfers directly: a boundary that holds only because
consumers happen not to look past it is not a boundary. But this RFC also asks to **reverse one of
its decisions and supersede another** — see *Problem & goals*, where the sentence
in question is quoted in full.

**Why now (SCQA).**

*Situation.* ADR-0071 (2026-08-06) settled where pack tests live and what `.apm/`
exports across the boundary.

*Complication.* It scoped itself to packs, and disposed of everything else in one
sentence — quoted here in full, because both of its clauses are revisited:
*"This catalogue declines a root `tests/` — a new top-level directory is
RFC-gated here — and keeps catalogue-wide behaviour in the engine's own suite."*
This RFC asks to reverse the first clause and supersede the second. The gating
mechanism it refers to is real — an allowlist in the pre-PR build lint — which is
what makes D1 a decision rather than a filing preference. Worth noting honestly:
that audit is weaker than it looks. It resolves its baseline with
`git merge-base HEAD main`, which fails on a CI checkout where only
`origin/main` exists, and the linter then *skips the audit and returns success*.
So it protects a local pre-PR run and not much else. Spec 2 should fix the
fallback while it is adding an entry to the list. Measured against `agentbundle` 0.29.8 on
2026-08-07: the wheel ships 45 test entries out of 184; the source distribution
ships 8 top-level test files with no `conftest.py` and no fixtures, so they
cannot run; `agentbundle catalogue init --preset self-hosted --tooling vendored` sweeps the working tree with no
exclusions whatsoever. Only the zipapp is correct, via an undocumented one-liner
in `tools/build_zipapp.py`.

And underneath all four surfaces sits the deeper fault: **82 test modules inside
`packages/agentbundle/` reach out and assert things about the *catalogue*.** They
walk `REPO_ROOT / "packs"`. Not all of them are catalogue-*owned* — the first-cut
mapping shows most are still engine tests borrowing a pack as input, and that
some are mixed, carrying catalogue-conformance classes inside an engine module.
What none of them has is a declared owner.

Relocating them within the engine package — the first draft of this RFC did
exactly that — moves the problem without fixing it, and makes the sdist rule
incoherent, because catalogue assertions can never run from an sdist that
contains no `packs/`.

*Question.* Who owns each test, where does each owner's tests live, and which
surfaces carry them?

### Decisions requested

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D6 | Who owns a test, and how do we tell? | Five owners — engine (including engine-borrowing-the-catalogue), catalogue (rule- or roster-shaped), pack, and tools — decided by *what the test asserts*, not by what it reads; and applied per test **class**, since modules turn out to be mixed | The read-based signal is the one that misleads: an adapter test reads `packs/core` but asserts nothing about it | this review | Rule on the taxonomy — it drives D1 and D2 |
| D1 | Where does each owner's tests live? | Engine → `packages/<pkg>/tests/`; catalogue → a new repository-root `tests/`; pack → `packs/<pack>/tests/` | A new top-level directory is RFC-gated here, and this is the RFC; ADR-0071's self-containment argument covers packs, not cross-catalogue conformance | this review | Approve the new top-level `tests/`; confirm relocation over the two exclusion variants |
| D2 | What does each surface carry? | Per surface **and per owner** — sdist carries the engine suite; catalogue channels carry the catalogue and pack suites; wheel, zipapp, vendored engine carry none | PyPA: wheels never, sdists commonly. A suite must be runnable where it lands, which is what the current mixture prevents | this review | Rule on the asymmetry — or partially accept, deferring the sdist half |
| D3 | Should the vendored copy carry tests? | Its **engine** half, no — it is wheel-class. Its **catalogue** half, yes — `catalogue init` ships catalogue and pack tests under the default preset *and* both `--preset self-hosted --tooling` modes | The vendored engine's consumption path is `pip install -e`; but a new catalogue needs to verify itself, which is ADR-0071's own "that is wanted" | this review | Confirm the split classification |
| D7 | May a shipped catalogue test pin this repository's content? | No — shipped catalogue tests must be rule-shaped; roster-shaped ones stay home and are marked non-shipping | A roster-shaped test fails on day one in an adopter's catalogue, which is the same present-but-unrunnable defect this RFC exists to end | this review | Confirm portability is a gating property, not a style note |
| D4 | Does the boundary reach `tools/test*.py`? | No — scope it to distribution surfaces and record co-location as a named exception | `tools/` is absent from all three packaging config tables | this review | Confirm the exception is recorded, not silently tolerated |
| D5 | What enforces the rule? | Two in-repo pure-stdlib instruments — an artifact gate after the existing build step, plus a unit test for the vendored payload | `check-wheel-contents` never fires on a nested test tree, and `pydistcheck`'s natural-reading flag passes while broken | this review | Confirm in-repo over third-party |

## Problem & goals

### Diagnosis

Test code is scattered across the locations below. One written convention covers
two of them.

| Location | Governed by |
| --- | --- |
| `packages/agentbundle/tests/unit/` | `packages/AGENTS.md` § Test conventions |
| `packages/agentbundle/tests/integration/` | `packages/AGENTS.md` § Test conventions |
| `packages/agentbundle/tests/` (8 loose modules) | governed by `packages/AGENTS.md`, and **in violation of it** |
| `packages/agentbundle/agentbundle/build/tests/` | nothing |
| `tools/test*.py` | nothing |
| `packs/<pack>/tests/` | ADR-0071 |
| `packages/credbroker/tests/` | nothing written — but already conformant |

The third row is not a separate *convention* — it is the existing one being broken.
`packages/AGENTS.md` states that the test roots are `tests/unit/` and
`tests/integration/` and that new tests go in the appropriate root; eight modules
sit directly at `tests/` in neither. They are worth naming because they are not
merely untidy: being at the top level is exactly what makes them the 8 files
setuptools' default sweep picks up, so this convention drift is the direct cause
of the arbitrary sdist slice described below.

### The deeper fault: no test has a declared owner

The table above is about *placement*. Underneath it is an ownership problem that
placement alone cannot fix.

82 modules across all three `packages/agentbundle/` test roots
resolve `REPO_ROOT` and read the live catalogue — `packs/`, `contracts/`,
`profiles/`, the marketplace aggregate. Measured 2026-08-07:

| Root | Reads the live catalogue | Package-internal only |
| --- | --- | --- |
| `agentbundle/build/tests/` | 29 of 44 | 15 |
| `tests/unit/` | 29 of 135 | 106 |
| `tests/integration/` | 24 of 71 | 47 |

Two consequences follow, and the second is the one that matters.

**It makes the sdist rule incoherent.** These modules anchor on
`REPO_ROOT = Path(__file__).resolve().parents[5]`, then read `REPO_ROOT / "packs"`.
The sdist is built from `packages/agentbundle` alone and contains no `packs/`,
`contracts/`, or `profiles/` — so from inside an extracted sdist that anchor
escapes the archive entirely. Any rule of the form "the sdist carries the test
tree" ships a downstream packager a suite that fails on a path which does not
exist. That is the same present-but-unrunnable defect described above, reproduced
by the fix rather than removed.

**But "reads the catalogue" is not the same as "tests the catalogue",** and
conflating them is how a mechanical split goes wrong.
`build/tests/test_adapter_claude_code.py` opens with *"Tests for the Claude Code
adapter"*, imports `agentbundle.build.adapters.claude_code`, and reaches for
`packs/core` only because a real pack is a convenient *input*. It asserts nothing
about the catalogue. Moving it to a catalogue test tree would be wrong; the
correct treatment is to re-point it at a fixture, leaving it an engine test.
Meanwhile `build/tests/test_shipped_packs_v08_declarations.py` hardcodes
`V08_PACKS = (atlassian, figma, converters, …)` and asserts that *this
repository's* packs declare a contract version. That is not portable to any other
catalogue.

So the classifying question is **what does the test assert**, not what it reads.
D6 turns that into a taxonomy.

The last row is the one to note: `packages/credbroker/tests/` already conforms.
Its wheel is clean by construction, because its tests sit outside the importable package —
the same `pyproject.toml` shape as `agentbundle`, a different tree layout, and a
different outcome. The rule this RFC proposes already holds for one of the two
packages here. We are regularising, not inventing.

Neither in-package placement was ever decided. `packages/agentbundle/tests/` and
`packages/agentbundle/agentbundle/build/tests/` both first appear on 2026-05-22,
in unrelated commits landing unrelated features. The layout is whatever the
author of each reached for — the same finding ADR-0071 recorded for packs, one
directory level up.

The consequence is four engine distribution surfaces behaving four ways. Measured
against `agentbundle` 0.29.8 by building both artifacts from a clean source copy
on 2026-08-07:

| Surface | Built by | Test content today | Correct? |
| --- | --- | --- | --- |
| zipapp (`.pyz`) | `tools/build_zipapp.py` | none — `shutil.ignore_patterns("__pycache__", "tests", "*.pyc")` | yes, by an undocumented one-liner |
| wheel | `python -m build` | 45 of 184 entries are the in-package test tree | no |
| sdist | `python -m build` | the in-package test tree's `.py` modules only — its fixtures absent — plus exactly 8 top-level `tests/test*.py` files, and no `conftest.py` | no — present but unrunnable, for two independent reasons |
| vendored | `agentbundle catalogue init --preset self-hosted --tooling vendored` | the entire working tree of `packages/agentbundle/`, unfiltered, **and** the whole of `packs/catalogue-curation/` including its pack tests | no |

**Why four and not five.** This repository also produces *catalogue* archives —
source archives of the packs and their configuration, as distinct from the Python
package (`catalogue package`, plus the self-hosted source flavour). They are
deliberately excluded. ADR-0071 already decided their rule, and decided it the
other way: *"Catalogue archives carry tests; installers do not install them. […]
That is wanted — downstream verification, auditing, security review, testing an
extracted release."* The catalogue archives are sdist-class by an existing
accepted decision, which this RFC neither reopens nor contradicts. The four
surfaces here are the ones that carry the *engine*.

Three of these are defects with distinct causes, so no single switch fixes them:

- **The wheel** ships tests because `[tool.setuptools.packages.find]` defaults to
  `namespaces = true`, so setuptools discovers directories as PEP 420 namespace
  packages whether or not they carry an `__init__.py`, and
  `include = ["agentbundle*"]` then matches them. This is worth stating precisely,
  because the intuitive diagnosis is wrong and an earlier draft of this RFC got
  it wrong: the tree's `__init__.py` is *not* what puts it in the artifact.
  Measured — deleting that file and rebuilding leaves 44 of the 45 test entries
  in the wheel, the only casualty being the deleted file itself. Under the
  default finder the tree is discovered as `agentbundle.build.tests` **plus eight
  `…tests.fixtures.*` namespace packages**; only with `namespaces = false` does
  the classic finder stop seeing them.
- **The sdist** is worse than under-inclusive: it is *arbitrarily* inclusive, and
  it fails in two independent ways. First, setuptools' default sweep auto-includes
  files matching `tests/test*.py` at the top level only — so `tests/unit/`,
  `tests/integration/`, and `conftest.py` are absent, while 8 files that depend on
  that missing `conftest.py` are present. Second, `[tool.setuptools.package-data]`
  grafts only `_data/` (two patterns) and `build/recipes/`, so the in-package test tree ships its
  `.py` modules while its fixtures — the JSON, TOML, Markdown, and shell files
  those modules read — do not. Either failure alone makes the shipped tests
  unrunnable. A downstream packager who tries to run them gets a failure that says
  nothing about our code. Both must be fixed together, which is why the sdist rule
  below specifies a graft rather than a package-discovery change.
- **The vendored copy** has no exclusions at all. The routine that assembles it,
  `_collect_dir_bytes` in `agentbundle/catalogue_tooling/initialise_self_hosted.py`,
  walks the working tree and copies every non-symlink file. Its payload is
  therefore not a fixed quantity — it is whatever happens to be on disk when the
  command runs. For the `packages/agentbundle/` half, a freshly-cloned workspace
  measures 545 files / 4.6 MB, of which 73% of files and 58% of bytes are tests;
  in a workspace where the suite has been run locally, `__pycache__` rides along
  and both figures climb substantially. That variance is itself the defect. The
  same routine is called a second time on `packs/catalogue-curation/`, which
  carries pack tests of its own — so this surface also ships pack test content,
  discussed below.

### Goals

1. Give every test an owner, decided by a rule that stays true for tests not yet
   written.
2. State the engine's export boundary once, in a form that structure enforces
   rather than convention asserts.
3. Give each surface *and each owner* a stated, justified inclusion rule — such
   that every shipped suite is runnable where it lands.
4. Let an adopter's catalogue verify itself, from `agentbundle catalogue init` onward,
   regardless of tooling mode.
5. Make the rules checkable in CI, so they fail on regression rather than on
   review attention.
6. Record `tools/test*.py` co-location as a deliberate exception, so it stops
   reading as an unexplained convention.

### Non-goals

These could reasonably have been goals. They are deliberately dropped.

- **Adopting a src layout.** Moving `packages/agentbundle/agentbundle/` to
  `packages/agentbundle/src/agentbundle/` is the fuller form of the same
  recommendation, and is now `uv init`'s default. It is dropped because it
  touches every `Path(__file__).parents[N]` resolution in the package, editable
  install detection, and the `.pth` and `egg-info` machinery — a large blast
  radius for a marginal gain over what D1 already buys. Considered and deferred,
  not overlooked.
- **Relocating `tools/test*.py`.** See D4; the boundary does not reach code that
  ships through no surface.
- **Changing pack test placement.** ADR-0071 owns it and is not reopened.
- **Rewriting every borrowed-catalogue engine test onto fixtures at once.** D6
  says an engine test that borrows `packs/core` as an input should be re-pointed
  at a fixture. Doing that for every such module is a large mechanical job with
  its own regression risk, and it is not required for any surface to become
  correct. The specs may leave a module borrowing the live catalogue, provided
  its *owner* is recorded as the engine and it is not shipped where it cannot run.
  That proviso needs a mechanism, since a `graft` is unconditional: still-borrowing
  modules live under a single `tests/live-catalogue/` subdirectory that
  `MANIFEST.in` prunes. Emptying that directory is spec 2's exit condition — it
  makes the remaining debt visible and countable instead of dissolved into a
  non-goal.
- **Fixing the unrelated packaging defects this RFC's research surfaced.** The wheel also
  carries `agentbundle/_data/install-marker.py` at a non-importable path, and the
  sdist carries `agentbundle.egg-info/`. Both are real; neither is this boundary.

## Proposal

### The ownership taxonomy (D6)

Every test gets exactly one owner, decided by **what it asserts**. The unit is
the test **class**, not the module: applying this to real code found engine
modules carrying catalogue-conformance classes, so module-granular ownership
forces a wrong answer for some of them.

| Category | Asserts | Home | Ships with |
| --- | --- | --- | --- |
| **Engine** | engine code behaves correctly | `packages/<pkg>/tests/` | sdist only |
| **Engine, borrowing the catalogue** | engine code behaves correctly, using a live pack as *input* | `packages/<pkg>/tests/` — same owner; re-point at a fixture when convenient | sdist only, once fixture-backed |
| **Catalogue, rule-shaped** | *any* catalogue's content is well-formed | repository-root `tests/` | catalogue archives **and** `agentbundle catalogue init` |
| **Catalogue, roster-shaped** | *this* repository's specific content | repository-root `tests/`, marked non-shipping | nothing |
| **Pack** | one pack's own content or behaviour | `packs/<pack>/tests/` (ADR-0071) | catalogue archives, and `catalogue init --preset self-hosted` (already true today) |
| **Tools** | a `tools/` script's behaviour | `tools/`, co-located (D4) | nothing — `tools/` crosses no surface |

The middle two rows are the ones that earn their keep. Without the
engine-borrowing row, a mechanical "reads `packs/`" split drags adapter and
installer tests out of the engine suite where they belong. Without the
rule/roster distinction, shipping catalogue tests to a new catalogue hands the
adopter a suite that fails immediately — see D7.

The **Tools** row exists because applying this taxonomy to real modules produced
one: three modules in the engine's in-package test tree turn out to test
`tools/lint-agents-md.py`. They import no engine code and belong at `tools/` per
D4 — which until now stated an exception to the boundary without naming a
destination. No automated signal surfaces them; they look like ordinary engine
tests.

**A first-cut mapping exists and is deliberately provisional.**
[`0082-notes/first-cut-ownership-mapping.md`](0082-notes/first-cut-ownership-mapping.md)
hand-classifies the 36 candidate modules in `agentbundle/build/tests/` (36 under
a path-form match, 29 under the quoted-directory match used in the table above —
the mapping records the method, and four of the 36 prove to be false positives)
— the tree spec 1 empties — and reports signals only for the other two roots,
because an automated verdict there would be the mechanical split D6 rejects. Its shape is the argument to test this proposal against, and it corrected this
RFC twice. Two consequences carry into the design. Spec 1's default of leaving
unresolved modules as engine tests is safe, because most of them genuinely are
engine tests. And **no module in that tree is a standalone rule-shaped
conformance test** — the rule-shaped material exists, but embedded as test
*classes* inside engine modules. So the shipped conformance suite is assembled by
**extraction**, not by moving files, and D7's roster rewriting is the smaller
half of the work. The mapping records four contested calls rather than smoothing
them over.

### The boundary

> `packages/<pkg>/<pkg>/` — the importable Python package directory — is the
> engine's runtime export boundary. Tests never live inside it.

Same shape as ADR-0071's rule, one level up the tree: there, `.apm/` is the
boundary and pack tests live at `packs/<pack>/tests/`; here, the package
directory is the boundary and engine tests live at `packages/<pkg>/tests/`.

**The source code does not move.** Only test trees do.

```
packages/agentbundle/
├── agentbundle/                  ← unchanged; this directory IS the boundary
│   ├── build/
│   │   ├── tests/                ← empties out (engine → up, catalogue → root)
│   │   ├── main.py  adapters/  recipes/  …    ← stay
│   ├── commands/  catalogue_tooling/  _data/  cli.py  …   ← stay
├── tests/                        ← the ENGINE suite, and only that
│   ├── unit/  integration/  build/
├── conftest.py
└── pyproject.toml

tests/                            ← NEW top-level: the CATALOGUE suite
├── conformance/                  ← rule-shaped; ships to new catalogues
└── roster/                       ← roster-shaped; pins this repo, never ships

packs/<pack>/tests/               ← unchanged (ADR-0071)
```

Every import path is preserved. `agentbundle.build.main`, `agentbundle.cli`, and
every other module resolve exactly as before. The one name that stops resolving
is `agentbundle.build.tests`, which nothing imports.

The `conformance/` ÷ `roster/` split inside the new tree is what makes D7
mechanically checkable: shipping is a directory rule, not a per-file judgement
someone has to remember.

**The new top-level directory is gated, and this RFC is the gate.**
`tools/lint-build.py` holds `RFC_AUTHORISED_DIRS`, a hard-coded allowlist of
top-level directories whose comment reads *"Add entries only when an Accepted RFC
authorises the new directory."* It runs in the pre-PR build lint and fails on any
unlisted top-level directory (see *Problem & goals* for how much weaker that
guard is in CI than it looks). So `tests/` cannot be created until this RFC is
**Accepted**, and adding it to that tuple is a required implementation step, not
an incidental edit. This is also why D1 is a genuine decision rather than a
filing preference: the repository has a mechanism that refuses it by default.

**One carve-out has to be stated, or the boundary rule contradicts itself.** The
bundled catalogue scaffold lives at
`packages/agentbundle/agentbundle/_data/catalogue-scaffold/` — *inside* the
importable package, and shipped in the wheel by design via `package-data`. Once
the scaffold gains a `tests/` template so new catalogues inherit one, there is
test-shaped content inside the export boundary. That is intended and is not a
violation: scaffold content is **inert template material**, never collected or
executed in this repository. The enforcement gate must discriminate on that
basis — content under `_data/catalogue-scaffold/` is exempt — and the exemption
must be written into the gate rather than left to a reviewer's judgement, since a
naive path check would either fail the wheel or, if loosened, stop protecting it.

**The same carve-out must reach the zipapp builder, and this one bites hard.**
`tools/build_zipapp.py` copies the package with
`shutil.ignore_patterns("__pycache__", "tests", "*.pyc")`. That pattern matches
the *name* `tests` at any depth, so the moment the scaffold gains a `tests/`
template the zipapp silently drops it. The scaffold is hash-manifest-verified at
init time, so the consequence is not a quietly thinner artifact: the missing
files fail manifest verification and `catalogue init` aborts outright with a
scaffold-integrity error. The bare-`tests` pattern must be narrowed to the
relocated engine tree before the scaffold template lands. It is the same
name-anywhere hazard flagged for `bandit.yaml` in *Evidence*, with a much worse
failure mode.

### Per-surface, per-owner inclusion

| Surface / channel | Engine suite | Catalogue suite | Pack suites |
| --- | --- | --- | --- |
| **sdist** | **yes** — complete, via an explicit `graft`, **but only once the engine suite is fixture-backed** (see below) | no — cannot run there; the archive has no `packs/` | no |
| **wheel** | no | no | no |
| **zipapp** | no | no | no |
| **vendored engine copy** | no — wheel-class | no | no |
| **`catalogue package` archive** | no | **yes** — needs an allowlist edit; see below | **yes** (ADR-0071, already true) |
| **`agentbundle catalogue init`** (default preset — materialises the bundled scaffold) | no | **yes**, `conformance/` only | n/a — no packs selected |
| **`agentbundle catalogue init --preset self-hosted`**, both `--tooling external` and `--tooling vendored` | no | **yes**, `conformance/` only | **already true** — each selected pack's `tests/` is copied today |

Two corrections to how this reads, because the CLI surface is easy to get wrong
and an earlier draft of this RFC did. The command is `agentbundle catalogue
init`, not `agentbundle init`. And `--tooling` is not a general flag: it is
rejected unless `--preset self-hosted` is given, so it selects between two
*different code paths* — the self-hosted path copies from a source catalogue,
while the default preset materialises the engine's bundled scaffold. Both must
carry the catalogue suite, and they need separate implementation work because
they share no code.

Two channels also need a positive allowlist widened rather than a filter relaxed
— they exclude a root `tests/` by construction, not by policy:
`catalogue package`'s `_DEFAULT_INCLUDE_DIRS` and `_SOURCE_INCLUDE_DIRS`.

Read the two right-hand columns as the answer to *"how does an adopter's
catalogue verify itself?"*, and the left as *"how does a redistributor verify the
engine?"*. They are different consumers asking different questions, which is why
one uniform rule was never going to fit.

**The sdist graft is sequenced, and this is load-bearing.** A `graft` is
unconditional: it ships whatever is in the tree. Spec 1 leaves unclassified
modules in the engine suite by default, and a share of those still borrow the
live catalogue — so grafting in spec 1 would ship a redistributor a suite that
fails on `REPO_ROOT / "packs"`, which is precisely the defect this RFC exists to
end, reintroduced by its own fix. Worse, a presence-checking gate would certify
it green.

Therefore: **spec 1 enforces only the absence half** — no test content in the
wheel, zipapp, or vendored engine copy. **The sdist graft lands in spec 2**, once
classification has left the engine suite genuinely self-contained, and its gate
asserts runnability by extracting the sdist and collecting the suite, not merely
by counting files. The two halves of D2 are both accepted here; only their
delivery is staged.

The sdist rule needs a `MANIFEST.in` with an explicit `graft tests`, because
setuptools' default sweep is partial by design. Two documented traps apply and
must be handled in implementation: `MANIFEST.in` is order-dependent (a
`global-exclude` placed before a `graft` does not apply to the grafted files),
and a stale `.egg-info/SOURCES.txt` causes setuptools to reuse the previous file
list rather than regenerate it, so `MANIFEST.in` edits silently do not take
effect.

### Why the vendored copy is wheel-class

This is the contested call, so the reasoning is stated rather than assumed.

`agentbundle catalogue init --preset self-hosted` scaffolds a new catalogue from an
existing source — an adopter's own repository of
packs, built on this engine. Under that preset, its `--tooling` flag takes two values: `external`,
where the adopter installs the engine from PyPI like any other dependency, and
`vendored`, where the engine's source is copied into their repository so their
catalogue tooling is self-contained and pinned rather than floating on a
published release. Vendored mode is the case at issue.

It copies the engine's source to `.agentbundle/tooling/agentbundle/` in the
adopter's repository. (Three similarly-named things are in play: `agentbundle`
the importable Python package, `packages/agentbundle/` its directory in *this*
repository, and `.agentbundle/` a state directory in the *adopter's* repository.
The vendored path contains two of them.) Being source-form, the copy looks
sdist-class. It is not — because of how the adopter is told to consume it. The
command itself emits the instruction:

> `Vendored tooling at .agentbundle/tooling/agentbundle/ — run: pip install -e .agentbundle/tooling/agentbundle/`

The vendored tree is not a source tree to read. It is an **install source the
adopter pip-installs**. Its consumption path is identical to the wheel's, so it
inherits the wheel's rule.

That leaves the real question: how does an adopter gain confidence in what they
just installed? Not by running the engine's unit tests, which answer *is the
engine correct?* — a question already settled by our CI before the release they
installed. Their question is *is my catalogue valid?*, and the instrument that
answers it is `agentbundle catalogue verify`: a multi-step validation pipeline
that checks their own catalogue's configuration, pack declarations, dependency
references, generated manifests, and the output each pack projects into a
consuming repository. It ships as engine code inside the package they just
installed, so it needs no additional artifact. It is stronger evidence for their
actual question than our unit tests would be. Anyone who does want the engine's
own suite gets it from the sdist.

Two implementation consequences, because both are easy to miss.

**The relocation alone does not fix this surface.** `_collect_dir_bytes` copies
the outer `packages/agentbundle/` directory, so after the move it would carry
`packages/agentbundle/tests/` — the relocated tree included. The vendored path
needs its own explicit exclusion in code. It has none today, not even for
`__pycache__`, which is why its payload varies with the state of the working tree
it was invoked from.

**Only the *engine* half of this surface is wheel-class.** Everything above
concerns the copy of `packages/agentbundle/` that the adopter pip-installs. The
same command also creates their catalogue — and a catalogue that cannot verify
itself is exactly the gap `catalogue verify` exists to close. So `agentbundle
init` carries the catalogue suite (`tests/conformance/`) and each selected pack's
`packs/<pack>/tests/`, in **both** `--tooling external` and `--tooling vendored`.
The tooling mode governs how the adopter gets the *engine*; it says nothing about
whether their catalogue is testable.

This is the same call ADR-0071 already made for catalogue archives — *"Catalogue
archives carry tests; installers do not install them. […] That is wanted —
downstream verification, auditing, security review"* — applied to the other
channel that produces a catalogue. Vendored mode looked contradictory only while
"the vendored copy" was treated as one undifferentiated blob.

**Vendored mode currently leaks *pack* tests through a path ADR-0071 does not
cover** — and, given the above, the fix is narrower than it first appeared.
Vendored mode calls `_collect_dir_bytes` a second time on
`packs/catalogue-curation/`, copying it wholesale into
`.agentbundle/tooling/packs/catalogue-curation`. That is the *engine tooling*
tree, not the adopter's catalogue: `catalogue-curation` is vendored there as an
operator tool, so its tests are engine-side baggage and should be excluded.
ADR-0071's reasoning for why pack tests never reach an adopter — *"projection
adapters read only `.apm/` and `seeds/`"* — does not reach this path at all,
because a raw tree copy is not a projection adapter. That gap is real and this
RFC closes it. See migration step 2, and note the care required: the routine
these copies share also serves the paths that must keep carrying tests.

### `tools/` — a named exception

`tools/test*.py` stays co-located with the scripts it tests — and, per the
taxonomy above, *tools tests* are a destination as well as an exception: a test
of a `tools/` script belongs at `tools/` wherever it currently lives. The
first-cut mapping found three sitting in the engine's in-package tree.
 The boundary is
scoped to distribution surfaces, and `tools/` crosses none: no packaging
configuration references it — not `[tool.setuptools.packages.find]`, not
`[tool.setuptools.package-data]`, and not `[catalogue.package].include`, which
lists only `packs/core`. The exception is recorded here and in
`packages/AGENTS.md` so that it reads as a decision rather than an oversight.

### Enforcement

A pure-stdlib checker in `tools/`, run in `release-agentbundle.yml` immediately
after the existing "Build wheel + sdist" step. It opens the built artifacts with
`zipfile` and `tarfile`. Roughly thirty lines, no new dependency, and consistent
with this repo's standing rule that new `tools/` scripts are pure-stdlib Python.

**It arrives in two stages, matching the two specs** — a gate asserting a
property the tree does not yet have would simply be red:

- **Spec 1 — the absence half.** No test content in the wheel; none in the
  zipapp or the vendored engine payload. This is enforceable the moment the tree
  moves.
- **Spec 2 — the presence half.** A complete engine test tree — modules *and*
  fixtures — in the sdist, and *runnable there*: extract the archive and collect
  the suite, rather than counting files. Presence alone is what let the current
  8-file slice look acceptable.

Asserting the sdist's *presence* half matters as much as the wheel's absence
half. A gate that only strips is a gate that will eventually strip the sdist too.

**What this gate does and does not cover — stated plainly, because the gap is
real.** Reading built artifacts covers two of the four surfaces. The zipapp is
built by no CI workflow at all (only by a `make` target), and the vendored
payload is not an artifact a release job can open — it is produced on an
adopter's machine. That matters, because the vendored surface is the one whose
correctness rests on hand-written code exclusions rather than on layout, which is
exactly the configuration-deep fragility D1 rejects option B for. Leaving it
unenforced would reproduce that flaw inside the recommendation.

So the enforcement is two instruments, not one:

- **The artifact gate** (wheel, sdist) in the release workflow, as above. The
  zipapp needs no separate check: its exclusion is a literal in the builder and
  the relocation makes it redundant.
- **A unit test over the vendored payload**, living in
  `packages/agentbundle/tests/`, asserting that `_collect_dir_bytes`'s two
  vendored call sites emit no test content, and that the packs call site — which
  runs in every mode — still does. (The fourth call site copies shared guides,
  which contain no test content either way, so there is nothing to assert there.)

On timing, the existing wiring is already better than it first appears:
`release-agentbundle.yml` triggers on tags *and* on any pull request touching
`packages/agentbundle/**`, and its "Build wheel + sdist" step carries no
tag-only condition — so the artifacts are built on every pull request that could
change their contents, and the gate inherits that. No new trigger is needed.

The unit test is therefore justified by *surface coverage*, not by timing: the
vendored payload is produced on an adopter's machine and is not an artifact any
CI job can open, so reading built artifacts can never reach it.

### Migration path — two specs

The work splits cleanly along a seam of its own: one half is mechanical,
release-blocking, and independently verifiable; the other is a
judgement-per-module classification with no release urgency. Shipping them
together would hold the first hostage to the second.

**Spec 1 — the engine export boundary.** Empties `agentbundle/build/tests/`,
stops the wheel, zipapp, and vendored engine copy carrying tests, and lands the
absence half of the enforcement. It does **not** graft the sdist — see the
sequencing note under *Per-surface, per-owner inclusion*. Ships a release. Does
not require any test to be classified as catalogue-or-engine: modules whose owner
is unresolved move to `packages/agentbundle/tests/` as engine tests by default,
which is where they already effectively live. Steps 1, 2 (its vendored half only), 4, and 5 below.

**Spec 2 — the catalogue and pack carve-out.** Classifies the 82 catalogue-reading modules per D6, moves rule-shaped conformance to
`tests/conformance/`, roster-shaped to `tests/roster/`, pack-owned to
`packs/<pack>/tests/`, and wires the shipping channels in `catalogue package` and
`agentbundle catalogue init`. Step 3 below, plus step 2's `MANIFEST.in` half —
the largest part of the work.

The ordering matters and is not arbitrary: spec 1 makes the export boundary real,
so spec 2's relocations cannot silently re-enter an artifact while it is
underway.

Steps, sequenced so each is independently verifiable:

1. **(Spec 1) Move the tree, and update every operative reference.** `git mv`, the
   path-anchor edits inside the suite, and the ten operative files outside it —
   both sets enumerated in *Evidence*. This step is larger than it looks: one CI
   workflow alone carries most of the references. Two of them are not
   configuration and need judgement rather than a rewrite:
   `agentbundle/catalogue_tooling/self_host_windows.py`, which is shipped engine
   code that invokes the suite by path (see *Risks*), and `bandit.yaml`, whose
   `*/build/tests/*` entry becomes dead while its `*/tests/*` entry continues to
   match — so security-scan coverage is unchanged, but the stale entry and its
   comment should go.

   **One more edit is mandatory and is not a path reference at all.**
   `agentbundle/build/self_host.py` refuses a destructive real-write self-host
   with the substring test `if "tests/fixtures/" in packs_dir.as_posix()`. Today
   `agentbundle/build/tests/fixtures/` matches. After the move the path becomes
   `…/tests/build/fixtures/`, where those two components are no longer adjacent —
   so the guard silently stops firing and the command would overwrite the working
   tree with fixture data. The guard must be rewritten to match `tests` and
   `fixtures` as path components that are both present but *not necessarily
   adjacent* — after the move they are separated by `build/`, so an
   adjacency-preserving component check fails exactly as the substring does. Note
   the guard goes half-dead rather than dead: `packages/agentbundle/tests/fixtures/`
   is unaffected and keeps matching, which is precisely why this would not be
   noticed. Its covering test
   must change too: it currently asserts against a hardcoded literal path, so it
   would stay green while the real guard was dead.
2. **(Spec 1) The vendored exclusions; (Spec 2) the `MANIFEST.in` graft.** The
   graft is deferred with the sdist half: when it lands it must carry the test
   tree's non-`.py` fixtures too, which `package-data` does not carry today and
   which are the second reason the shipped tests cannot run. A third trap applies
   beyond the two named above: setting `include_package_data = True` would promote
   the grafted tree into the *wheel*, inverting D2. The package sets it nowhere
   today, and must not start.

   In spec 1, exclude tests from the vendored payload — **at the call site, not inside
   `_collect_dir_bytes`.** The routine has four callers, and only two of them are
   vendored: the engine copy and the `packs/catalogue-curation/` copy. The other
   two are the adopter's own catalogue: the packs copy runs unconditionally, and
   the guides copy runs when `--guides selected` is given. Both must keep carrying
   tests — ADR-0071 says catalogue archives carrying
   tests is *wanted*. An implementer who adds the exclusion inside the shared
   routine would strip tests from the adopter's own catalogue and break an
   accepted decision this RFC explicitly upholds.
3. **(Spec 2) Classify, relocate, and ship the catalogue and pack suites.** The
   substantial half.

   1. **Classify every catalogue-reading module against D6.** Start from the
      provisional mapping in `0082-notes/first-cut-ownership-mapping.md`, which
      hand-classifies `agentbundle/build/tests/` and leaves the other two roots
      to this step. Note its candidate count is method-sensitive — 82 under the
      quoted-directory match, 103 under a path-form match — so re-derive rather
      than inherit either. This is judgement per module and does
      not compress: the automated signal — "does it resolve `REPO_ROOT / packs`"
      — finds the candidate set but cannot separate an engine test borrowing a
      pack as input from a genuine conformance test. *Evidence* records both the
      candidate set and why the automated split is insufficient.
   2. **Relocate by owner, extracting where a module is mixed.** Rule-shaped
      conformance → `tests/conformance/`; roster-shaped → `tests/roster/`;
      pack-owned → `packs/<pack>/tests/`, following ADR-0071's existing layout;
      tools-owned → `tools/`. Engine tests stay put. Where one module carries
      both kinds — the common case in the first cut, not the exception — split
      the conformance classes out rather than moving the module wholesale. The
      mapping names the three known instances in `build/tests/` and warns to
      expect more in the other two roots.
   3. **Make the shipped ones portable (D7).** A test moving into
      `tests/conformance/` must assert a *rule* over whatever packs it finds, not
      a roster. Where an existing test pins a list — `V08_PACKS` is the worked
      example — either rewrite it as a rule or classify it roster-shaped and
      leave it home. Rewriting is preferred where the rule is expressible;
      "leave it home" must not become the default that empties the shipped suite.
   4. **Wire the channels — four concrete edits, none of them a filter relax.**
      Each channel excludes a root `tests/` by *positive allowlist*, so nothing
      happens until the allowlist is widened:
      - `tools/lint-build.py` — add `"tests",  # RFC-0082` to
        `RFC_AUTHORISED_DIRS`, without which the directory cannot exist at all.
      - `catalogue_tooling/package.py` — add `("tests",)` to
        `_DEFAULT_INCLUDE_DIRS` and `"tests"` to `_SOURCE_INCLUDE_DIRS`, so both
        archive flavours carry the conformance suite.
      - `agentbundle catalogue init --preset self-hosted` — materialise
        `tests/conformance/` into the new catalogue. Each selected pack's
        `tests/` **already ships** here today, unfiltered, so that column needs
        no work; it needs only to survive step 2's exclusion edit, which is why
        step 2 insists the exclusion goes at the vendored call sites and not
        inside the shared routine.
      - `agentbundle catalogue init` (default preset) — a separate code path that
        materialises the bundled scaffold, so the scaffold gains a
        `tests/conformance/` template and its authoring guidance. A real scaffold
        change: version bump, `Engine-Change-RFC:` trailer, scaffold-sync run —
        **and an entry in `tools/catalogue/sync_authoring_scaffold.py`'s
        `_SYNC_PAIRS`**, a fifth explicit pair list whose own comment says new
        files must be added there to participate. A template file absent from
        `_SYNC_PAIRS` gets no manifest entry, so `init` never materialises it and
        the omission surfaces only as a non-blocking INFO — shipping green while
        shipping nothing.
        Note the carve-out under *The boundary* — this template content sits
        inside the export boundary by design and the gate must exempt it.
   5. **Give the new tree a runner.** The repository root has no
      `[tool.pytest.ini_options]`, the `Makefile` enumerates every suite by
      explicit path, and no workflow references a root `tests/` — so an
      unwired tree is collected by nothing and Goal 5 goes unmet for the
      catalogue suite. Wire it into the `Makefile` test target and
      `build-check.yml`. Heed the `Makefile`'s existing warning about duplicate
      test basenames: consolidating modules from three roots into one tree can
      collide, and pytest refuses duplicates outright.
   6. **Verify by construction, not by inspection.** Run `agentbundle catalogue
      init` into a temporary directory and execute the materialised suite against
      the scaffolded catalogue. If it does not pass there, the shipped tests are
      not portable and step 3.3 is not done. This is the only check that
      distinguishes a genuinely rule-shaped suite from one that merely looks it.
4. **(Spec 1) CI gate — absence half.** Add the artifact gate's absence
   assertion and the vendored-payload unit test; the sdist presence assertion
   lands with spec 2's graft. Wire the artifact gate into the release
   workflow's build job, immediately after the artifacts are produced — and add
   the gate script's own path to that workflow's `pull_request.paths` filter,
   which today lists only `packages/agentbundle/**` and the workflow file. Without
   that, a pull request changing only the gate would never run it.
5. **(Spec 1) One release, cut last within the spec.** Spec 1's changeset ships
   together, with the single version bump this repository requires for a
   non-cosmetic package change. Both specs touch `packages/agentbundle/**`, the
   range guarded by the curation lint, so **both** carry the
   `Engine-Change-RFC:` commit trailer — not just spec 2's scaffold change. Spec 2 carries its own bump when its scaffold
   change lands. *This RFC changes no code and bumps nothing.*

## Options considered

### D6 — how a test's owner is decided

MECE along *what signal decides the owner*. A test can be classified by where it
currently sits, by what it reads, by what it asserts, or not at all.

| Option | Trade-off | If accepted |
| --- | --- | --- |
| **A — no taxonomy (status quo)** | zero work | Ownership stays implicit, so every future test lands wherever its author guesses. This is the mechanism that produced the present state; ADR-0071 diagnosed the same thing for packs. |
| **B — by current location** | trivially mechanical | Encodes the existing accident as the rule. Rejected on sight. |
| **C — by what the test reads** | fully automatable — one grep for `REPO_ROOT / "packs"` | Wrong for the largest group. Adapter and installer tests read a live pack purely as input; classifying them catalogue-owned would strip the engine suite of most of its integration coverage. Measured: 29 of 44 modules in `build/tests/` read the live catalogue, but the majority of those assert only engine behaviour. |
| **D — by what the test asserts ★** | correct; not automatable | Requires per-module judgement over 82 files. Buys a rule that stays true for tests not yet written, which is the whole point of a convention. |

**Prior art.** ADR-0071 made the same move one level down, deciding pack test
placement by *ownership* ("the pack is the ownership and test-execution
boundary") rather than by convenience. This is that principle applied upward,
and the reason its "keeps catalogue-wide behaviour in the engine's own suite"
clause needs revisiting: that clause assigned a *location* without assigning an
*owner*, so catalogue-owned tests ended up inside the engine.

**Recommended: D**, with C used to *find* the candidate set and D to decide each
one. The cost is honest and is why this is spec 2's bulk.

### D7 — may a shipped catalogue test pin this repository's content?

MECE along *what a shipped test is allowed to assume*.

| Option | Trade-off | If accepted |
| --- | --- | --- |
| **A — ship everything in the catalogue suite** | simplest wiring | Roster-shaped tests fail immediately in an adopter's catalogue, which has different packs. The adopter's first experience of their new catalogue is a red suite testing someone else's content. |
| **B — ship nothing; catalogue tests stay home** | no portability problem | Gives up the point of the exercise: a new catalogue cannot verify itself, which is the gap `catalogue verify` was built to close and the reason D3's vendored classification works at all. |
| **C — shipped tests must be rule-shaped; roster-shaped are marked and stay ★** | keeps both properties | Requires the distinction to be visible and checkable. Making it a directory split (`conformance/` ÷ `roster/`) rather than a per-file convention means the shipping rule is mechanical and the classification is reviewable in a diff. |
| **D — ship everything, let adopters delete what fails** | zero authoring discipline | Ships a known-broken artifact and calls it configuration. This is the present-but-unrunnable defect with extra steps. |

**Recommended: C.** Note it is a real constraint on authoring, not a filing
convention: it says a conformance test must express *why* something is required,
not *which* things currently satisfy it. `V08_PACKS = (atlassian, figma, …)`
becomes "every pack declares a contract version the engine supports" — a better
test for this repository too, since the roster form silently passes when a new
pack forgets to add itself.

### D1 — where each owner's tests live

Given D6's taxonomy, the destinations for catalogue and pack tests follow from
ownership (a repository-root `tests/`, and `packs/<pack>/tests/` per ADR-0071).
What remains genuinely open is the *engine* tree: how it stops being inside the
export boundary. MECE along *how much of the tree's identity changes*: nothing
changes; only packaging configuration changes; only the directory's package-ness
changes; the directory moves; the directory and the package both move. Those five
exhaust the axis — there is no sixth position between "delete one marker file"
and "move the directory".

| Option | Trade-off | If accepted |
| --- | --- | --- |
| **A — do nothing** | zero work | The wheel keeps shipping tests, the sdist keeps shipping unrunnable ones, and there is still no rule to cite in review. Cost of delay: every new test module compounds the eventual move. |
| **B — exclusion only** | smallest diff; no path churn | Correctness stays configuration-deep and re-breakable, and getting it right is subtler than it looks. Measured: `exclude = ["tests", "tests.*"]` — the form the setuptools issue below is usually quoted for — matches **nothing** here, because those patterns are anchored at the top level and this tree is nested; only `["*.tests", "*.tests.*"]` empties the set. `include_package_data = True` would independently defeat either. Each surface then needs its own separate correct exclusion. Most damning: the rule stays uncheckable — "do not put tests here" cannot be verified when tests are already there. |
| **B′ — delete `build/tests/__init__.py`** | one file deleted; zero configuration | The intuitive minimal fix, and it **does not work**. Measured: with `namespaces = true` (the default), deleting the marker leaves 44 of 45 test entries in the wheel, because PEP 420 discovery does not need it. To make B′ function it must become "delete the marker *and* set `namespaces = false`" — at which point it is option B with an extra step, carrying the same uncheckability, and still leaving the sdist and vendored surfaces untouched. Listed because it is the option a reader will reach for, and it is worth recording that it was measured rather than assumed. |
| **C — relocate the test tree ★** | one mechanical move, two enumerated edit sets, and one guard rewrite | The boundary becomes structural. All four surfaces inherit correctness from layout rather than from four separate correct configurations. Cost: the path-anchor and operative-reference edits enumerated in *Evidence*. |
| **D — relocate, and adopt a src layout** | the fuller upstream recommendation | Touches every path resolution in the package, plus editable-install machinery. Large blast radius for a marginal gain over C. |

**Prior art — ADR-0071 Option B, answered.** ADR-0071 considered and rejected
"a repository-root `tests/` tree mirroring `packs/`" for two reasons: it
separates a test from the thing it validates, and it "gives cross-pack tests and
pack-owned tests the same home, which is the ambiguity we are trying to remove".
The first still holds for *pack* tests, which is why this RFC leaves them at
`packs/<pack>/tests/`. The second is answered by construction: because D6 assigns
an owner before a location, cross-catalogue conformance and pack-owned tests get
*different* homes, so the root tree carries only one of them. ADR-0071 rejected a
root `tests/` that would have held both; this proposes one that holds neither
pack tests nor engine tests.

B is what setuptools did for exactly this defect: its own wheel
shipped test files (#3017), and the fix (#3018) tightened exclusion rules rather
than moving the tree. That precedent is instructive in both directions — it
proves the failure is real, and it shows a large project reaching for the weaker
remedy under compatibility pressure it could not escape. This repository has no
such constraint: nothing imports `agentbundle.build.tests`, so no external
contract binds the location. C and D follow pytest's own integration guidance,
which recommends tests outside application code so that they run against the
package *as installed*. Within this repository, `packages/credbroker/` already
demonstrates C.

**Recommended: C.**

### D2 — what the rule quantifies over

MECE along *the scope of a single rule*: no rule, one rule excluding everywhere,
one rule including everywhere, or one rule per surface.

| Option | Trade-off | If accepted |
| --- | --- | --- |
| **A — no rule (status quo)** | zero work | Four accidental behaviours, one correct by luck. |
| **B — uniform exclude** | one switch, trivially enforced | Breaks downstream redistributors. conda-forge builds from the PyPI sdist and runs the upstream suite, and its own documentation names the fallback when tests are absent: use "the GitHub source archive created for a tag" — a second source of truth for the same release. Fedora and Debian build from source and run upstream suites where they exist, with the same consequence. |
| **C — uniform include** | no downstream complaints | Contradicts PyPA guidance outright and inflates every install with content that is never executed. |
| **D — per surface ★** | correct for each consumer independently | Four rules to hold in mind, and an asymmetry that must be re-argued each time someone encounters it. Requires an explicit `graft` rather than relying on defaults. |

**Prior art.** The Python Packaging User Guide states the asymmetry directly and
verbatim: *"Wheels are meant to contain exactly what is to be installed, and
nothing more. In particular, wheels should never include tests and
documentation, while sdists commonly do."* The redistributor side is corroborated
by conda-forge's own documentation and, on the packaging forum thread cited
below, by a Pillow maintainer reporting that *"we've had downstream distro
packagers request tests"* and by a CPython core developer arguing that where no
wheel is available, running the tests is how a downstream confirms the build
actually works.

**Recommended: D.**

### D3 — what the vendored copy carries

MECE along *how much test content the vendored tree carries*: all of it, a
curated part of it, or none. Those three exhaust the axis.

| Option | Trade-off | If accepted |
| --- | --- | --- |
| **A — vendor all tests** (sdist-class) | consistent with "source form ships tests" | Most of the payload becomes tests. Widens the adopter's audit surface to code they cannot patch, and any copied tree containing `test_*.py` is collected by pytest unless explicitly excluded. |
| **B — vendor a curated subset** | some local assurance | A subset nobody maintains, reproducing the present-but-unrunnable failure deliberately. |
| **C — vendor none** (wheel-class) ★ | smallest payload; matches the `pip install -e` consumption path | The adopter needs a stated assurance path, or this becomes the gap that produces the next ad-hoc convention. `agentbundle catalogue verify` is that path, and the sdist is the escape hatch for anyone who wants the engine's own suite. |

Note that C is only defensible *with* its assurance path attached. "Vendor no
tests and say nothing" is the same option with the argument left out, and it is
the one to avoid.

**Prior art.** Vendoring conventions narrow what they copy, and test code is a
standard thing to drop — though the strength of that convention is weaker than it
is often reported, and the checked version is stated here rather than the
received one. `go mod vendor` copies what is needed "to build and test packages
in the main module", and its reference states that "packages that are only
imported by tests of packages outside the main module are not included" — an
exclusion of test-only *dependencies*, not of test files as such.
`cargo-vendor-filterer` supports excluding paths from vendored crates and carries
`{ name = "*", exclude = "tests" }` among its worked examples, though the "key
use case" its documentation actually names is dropping embedded C libraries, not
tests. pip's vendoring policy works from PyPI sdists, so development trees never
enter in the first place. The strongest form of the claim — "every ecosystem
strips tests by default" — is not supported; what the sources support is that
excluding test content from a vendored copy is normal, expected, and supported by
tooling. That is enough for D3, which does not need a universal norm.

**Recommended: C.**

### D4 — whether the boundary reaches non-distributed trees

MECE along *scope of the rule relative to distribution*.

| Option | Trade-off | If accepted |
| --- | --- | --- |
| **A — centralise `tools/` tests** | one convention repo-wide | Churn across the whole `tools/` suite for no distribution benefit. |
| **B — scope to distribution; record the exception ★** | honest, zero churn | An exception to explain — which is the point, since it stops being folklore. |
| **C — stay silent** | zero work | The convention remains a fourth unexplained pattern. |

**Recommended: B.**

### D5 — the enforcement instrument

MECE along *dependency posture*: nothing, third-party tool, or in-repo code.

| Option | Trade-off | If accepted |
| --- | --- | --- |
| **A — nothing; rely on the written rule** | zero work | This is how the present state arose. |
| **B — `check-wheel-contents`** | an established tool | **Does not catch this defect.** Its test-name check applies at the *library top level*; our tests are nested inside the package, and the tool reports nothing about them. Adopting it also means first resolving an unrelated warning it already raises. |
| **C — `pydistcheck --expected-files`** | one tool covers both surfaces | A new CI dependency, and the flag choice is a trap: the directory-pattern form silently passes on wheels, because setuptools wheels contain no directory entries for it to match. |
| **D — two in-repo pure-stdlib instruments ★** | no new dependency; matches the repo's stated rule that new `tools/` scripts are pure-stdlib Python | An artifact gate in `tools/` (~thirty lines) plus a unit test over the vendored payload in `packages/agentbundle/tests/`, since no CI job can open an adopter-side copy. Two small things we own rather than one dependency we don't. |

**Recommended: D.** B is rejected on tested evidence rather than on preference —
see *Evidence*. C is a viable fallback if the in-repo gate proves burdensome.

The repository has already made this call once, for the same boundary one level
down: `tools/lint-pack-test-boundary.py` is a pure-stdlib, in-repo boundary lint
written to enforce ADR-0071. D5 is the engine-side instance of an established
local pattern, not a novel preference for hand-rolled tooling.

## Risks & what would make this wrong

### Pre-mortem

- **The shipped conformance tree lands outside SAST entirely.** Not via an
  exclusion glob — via scope. `SAST_DIRS := tools packs packages` in the
  `Makefile` is the single source of truth that `build-check.yml` reads, and a
  repository-root `tests/` is in none of those roots, so Bandit and Semgrep never
  descend into it. This is code that *ships to adopters* sitting outside the
  security gate. Mitigation: spec 2 must decide explicitly, and the edit is
  adding `tests` to `SAST_DIRS` — not touching `bandit.yaml`, whose `*/tests/*`
  glob would not match `tests/conformance/x.py` in any case.
- **The shipped catalogue suite is roster-shaped in practice, and every adopter's
  new catalogue starts red.** D7 states the rule, but the rule is only as good as
  the classification, and "rewrite as a rule" is harder than "mark it roster and
  leave it" — so the pressure is toward an empty shipped suite or a broken one.
  Mitigation: migration step 3.6 verifies by *running* the materialised suite
  against a freshly scaffolded catalogue. A suite that cannot pass there is not
  shippable, and that check cannot be satisfied by inspection.
- **Spec 2's classification is done mechanically because it is large.** Eighty-two
  modules of judgement invites someone to reach for the grep. That grep
  is precisely what D6 option C rejects. Mitigation: the taxonomy names the
  engine-borrowing-the-catalogue case explicitly, and the spec should require a
  recorded owner per module rather than a bulk move.
- **The move silently disables a shipped safety guard, and the test that covers
  it stays green.** This is not hypothetical — it is the concrete case above:
  `self_host.py`'s destructive-write refusal is a substring match on
  `tests/fixtures/` that the new layout breaks, and its covering test asserts
  against a hardcoded literal rather than the real path, so nothing goes red.
  It is the most dangerous class of finding here, because the failure is a
  *silently weakened control*, not a broken build. Mitigation: the migration
  names it explicitly, and the implementing spec should sweep for other
  substring-shaped path guards rather than assuming this is the only one — a
  path-component check would have survived the move, and a literal-argument test
  will never catch its absence.
- **The move breaks tests in a way the spike missed, and lands mid-release.**
  Mitigation: the migration's first step is independently verifiable — the suite
  must be green after the move and before anything else changes. The
  two inventories in *Evidence* — path anchors inside the suite, operative
  references outside it — were built by enumerating syntactic forms across the
  whole tree rather than by spot-checking files. The second inventory was wrong
  in this RFC's first draft and was corrected by an unfiltered re-sweep, so the
  method's failure mode is a filtered grep, and the implementing spec should
  re-run both sweeps rather than trusting these lists.
- **The `MANIFEST.in` graft silently does not take effect** because of a stale
  `SOURCES.txt`, and the sdist ships without tests while the gate is written to
  assert their presence. Mitigation: the CI gate checks the *built artifact*,
  not the configuration — a config that fails to apply fails the gate.
- **The vendored exclusion is written as a `tests` pattern and over-matches**,
  dropping something an adopter needs. Mitigation: exclude by explicit relative
  path, not by name-anywhere pattern.
- **The written rule outlives the enforcement.** Someone disables the gate to
  unblock a release and it never returns. Mitigation: the gate runs in the same
  job as the build, before the publish step depends on it.

### Key assumptions (falsifiable)

1. **No shipped code depends on the test tree's location.** The narrow form —
   nothing *imports* `agentbundle.build.tests` — is true and was checked. The
   broader form is **false as stated, and the correction matters**:
   `agentbundle/catalogue_tooling/self_host_windows.py` subprocess-invokes
   `pytest agentbundle/build/tests/<module>.py` for four modules by literal path.
   That file lives inside the package, so it ships in the wheel, the zipapp, and
   the vendored copy — meaning those artifacts already carry a runner pointing at
   a tree they do not contain, and will still do so after this change. The
   relocation must update it, and the implementing spec should decide whether that
   runner belongs inside the export boundary at all. It is also the body of the
   Windows build-check leg, so the move breaks that leg until the paths are
   updated. Found by adversarial review of this RFC, not by the original sweep —
   which is the honest reason to state assumption 1 in the broad form.
2. **`tools/` ships through no distribution surface.** Falsified by a `tools/`
   reference in any *packaging* configuration. Checked against
   `[tool.setuptools.packages.find]`, `[tool.setuptools.package-data]`, and
   `[catalogue.package].include`; none. (`tools/` does appear in the root
   `pyproject.toml` under `[tool.ruff.lint.per-file-ignores]` — a lint setting,
   not a packaging one.)
3. **Downstream redistributors of *this* package would run its tests.**
   Weaker than the others: agentbundle is not currently packaged by Fedora,
   conda-forge, or Debian. The evidence establishes what redistributors do in
   general, not that any has asked us. This assumption is about keeping the door
   open, and a reviewer may reasonably weigh it lower.
4. **An adopter's real question is catalogue validity, not engine correctness.**
   Falsified by an adopter asking to run engine unit tests against a vendored
   copy. Untested against real adopters.

### Drawbacks

- **Four rules are harder to hold than one.** The asymmetry is the design, but it
  is a genuine cost: anyone touching packaging must know which surface they are
  changing. A single "strip tests" switch would be easier to remember and wrong.
- **The relocation is churn.** Most of the test suite gets a mechanically edited
  path anchor. Mechanical edits are where transcription errors hide.
- **The sdist half is speculative benefit.** Nobody redistributes this package
  today. We are paying real configuration cost — a `MANIFEST.in` with two known
  traps — against a consumer that does not yet exist.
- **The strongest evidence against the sdist half deserves stating.** On the
  packaging forum thread cited below, a `build` maintainer argued that without a
  standardised way to invoke tests from an sdist, including them "increase[s]
  file sizes and do[es] not really provide almost any benefit"; a pip maintainer
  held that standardising invocation was a prerequisite. That objection applies to
  this proposal in full. It is accepted and outweighed: the cost is bounded and
  one-time, the benefit accrues to a consumer we cannot serve retroactively, and
  shipping a *partial* tree — the status quo — is worse than either alternative.
- **There is no normative specification behind D2.** The forum thread closed
  without consensus and no standards-track document followed. The available
  evidence cannot distinguish "settled, so no specification was needed" from
  "contested, so none was possible". D2 therefore rests on a practice consensus
  with a documented dissent, not on a standard. A reviewer should weigh it as
  such.

## Evidence & prior art

### Spike result

The assumption that, if false, sinks the proposal: *that the wheel actually
ships tests today, and that relocation rather than exclusion is required.*

Both artifacts were built from a clean copy of `packages/agentbundle` (excluding
`__pycache__` and `.egg-info` so the measurement was not polluted), using
`build` 1.5.0 and setuptools 83.0.0, against version 0.29.8 on 2026-08-07.

- **Wheel:** 184 entries, 45 of them the in-package test tree.
- **Sdist:** 218 entries — the in-package test tree's `.py` modules only, its
  fixtures absent, plus exactly 8
  top-level `tests/test*.py` files, and no `conftest.py`. `tests/unit/` and
  `tests/integration/` are absent entirely.
- **Vendored:** replicating `_collect_dir_bytes` over the working tree yields 545
  files / 4.6 MB in a freshly-cloned workspace, 73% of files and 58% of bytes
  being tests, with no exclusions applied at any point.

**The relocation was then applied to a temporary copy and installed.**
`pip install -e` exits 0; `import agentbundle` and `import agentbundle.build`
resolve; the console script reports its version correctly; and
`import agentbundle.build.tests` raises `ModuleNotFoundError` — the intended
outcome. Editable install is unaffected because
`[tool.setuptools.packages.find] include = ["agentbundle*"]` resolves the package
directory, and a sibling `tests/` tree is outside its reach. This is already how
`packages/credbroker/` installs today.

**Migration cost, measured against a control.** The relocated suite and an
identically-scoped unmoved control were both run. The control produced 8
failures; the relocated tree produced 10. The 8 are shared and attributable to
the partial repository copy used for the experiment, not to the move.

**Read the remaining 2 correctly — they are a residual, not a total.** The
mechanical `parents[5]` → `parents[4]` rewrite was applied to the relocated copy
*before* the comparison ran. So "2" measures what survives the mechanical sweep,
not what the move costs; without that sweep the great majority of the suite would
have failed on import. The number's real value is in *what* the two are, and the table
below names three idioms for a reason: the sweep rewrote only `parents[5]`, so
the chained-`.parent` module and one of the two `parents[2]` modules are exactly
what failed. (The other `parents[2]` module did not surface a failure in this
harness; it still needs the same rewrite.) These are the cases a mechanical sweep
cannot fix, and they are the migration's actual judgement work.

| Anchor idiom | Modules | Migration action |
| --- | --- | --- |
| `parents[5]` → repository root | 35 | mechanical rewrite to `parents[4]` |
| chained `.parent.parent.parent.parent` | 1 | same correction, different idiom — a `parents[N]`-only sweep misses it |
| `parents[2]` → reaches *into* the package (`agentbundle/_data/`) | 2 | genuine rewrites; must resolve the package explicitly |

The last row is the substantive finding. Those two modules resolve package data
by relative depth, which works *only* because the test lives inside the package.
That coupling is what makes the current placement self-reinforcing, and removing
it is the point of the move rather than an incidental cost of it.

**References outside the suite.** A separate, unfiltered sweep for the literal
path found ten files that must change with it — eight operative, two prose. It is listed here because
the migration's size claim depends on it, and because the first version of this
RFC named four and was wrong:

| File | References | Note |
| --- | --- | --- |
| `.github/workflows/build-check.yml` | 17 | the bulk of the work; a filtered sweep misses this |
| `.github/workflows/catalogue-tooling-ci-gates.yml` | 5 | |
| `agentbundle/catalogue_tooling/self_host_windows.py` | 4 | **shipped engine code** — see *Risks*, assumption 1 |
| `pyproject.toml` (repository root) | 2 | mypy `exclude` |
| `packages/agentbundle/pyproject.toml` | 1 | `testpaths` |
| `packages/agentbundle/tests/integration/test_install_snapshot.py` | 1 | prose — a docstring mention, not an executable path |
| `Makefile` | 1 | test target |
| `.github/workflows/release-agentbundle.yml` | 1 | pre-release suite |
| `bandit.yaml` | 1 | entry goes dead; `*/tests/*` still matches, so coverage is unchanged |
| `packs/AGENTS.local.md` | 1 | prose reference |

Two caveats on the method. The per-file counts include comment and prose
mentions of the directory, not only executable path references — that is the
right basis for migration sizing, but it means the numbers are not a count of
lines that must change. And the sweep matches the literal path, so it cannot see
references that name the directory without its parents. `tools/build_zipapp.py`'s
`ignore_patterns("__pycache__", "tests", "*.pyc")` is one such — it goes dead
after the move exactly as the Bandit entry does, and only a second pass for bare
`"tests"` patterns finds it. A third class is invisible to both passes:
references that *compose* the path from parts, such as `tools/lint-build.py`'s
`Path(build_dir) / "tests" / "fixtures"`, and literal references *inside* the
suite itself, which fall between the two inventories above. That third class was
not enumerated here; the implementing spec must sweep it, and
`self_host.py`'s substring guard — see migration step 1 — is the reason to take
it seriously rather than treat it as tidy-up.

Historical references in `docs/specs/**`, earlier `docs/rfc/**`, the package
`CHANGELOG.md`, and `docs/product/changelog.md` are deliberately excluded: those are shipped records of past work, and this
repository's convention is to rename operative references only.

### The ownership mapping, and why it cannot be automated

The candidate set was found mechanically: modules resolving `REPO_ROOT` (or an
equivalent `parents[N]` walk) *and* reading `packs/`, `contracts/`, `profiles/`,
or `guides/`. Measured 2026-08-07 — 29 of 44 in `agentbundle/build/tests/`, 29 of
135 in `tests/unit/`, 24 of 71 in `tests/integration/`.

A second pass tried to split that set by which pack each module names. It does
not survive inspection, and the failures are instructive rather than incidental:

- **The signal is dominated by false positives from directory names.** An early
  pass assigned 24 modules to a pack called `contracts` — they were reading the
  repository-root `contracts/` directory holding the adapter contract, which
  shares a name with a pack. Same hazard for `core`.
- **Reading a pack is not testing it.** `test_adapter_claude_code.py` opens
  *"Tests for the Claude Code adapter"*, imports
  `agentbundle.build.adapters.claude_code`, and uses a real pack only as input.
  Any read-based classifier calls it catalogue-owned. It is engine-owned.
- **Some catalogue tests are not portable.**
  `test_shipped_packs_v08_declarations.py` hardcodes
  `V08_PACKS = (atlassian, figma, converters, …)`. It is genuinely
  catalogue-owned, and genuinely unshippable as written — the distinction D7
  exists to make.

**A provisional first cut is published, scoped to what was actually read.**
[`0082-notes/first-cut-ownership-mapping.md`](0082-notes/first-cut-ownership-mapping.md)
hand-classifies every catalogue-touching module in `agentbundle/build/tests/`,
records its discriminator, and names three contested calls. For `tests/unit/` and
`tests/integration/` it reports signals and stops.

That asymmetry is deliberate and is the point. A machine-generated verdict for
all 103 candidates would carry an authority the method does not have — the
failures above *are* the evidence that a mechanical split gets this wrong, and an
early automated pass on this very RFC misfiled 24 modules into a pack named
`contracts` that were reading the repository-root `contracts/` directory. Hand
classification also earned its keep: it found three modules testing a `tools/`
script, which no read-based or invoke-based signal surfaces, and which the
taxonomy had no destination for until they appeared.

What this RFC fixes is the *rule*, and it now ships a worked example of applying
it. Applying it to the rest is spec 2's job, one module at a time.

### Enforcement tooling, tested rather than cited

Both candidate tools were run against the real artifacts:

- **`check-wheel-contents` 0.6.3** exits 1 on our wheel — but for an unrelated
  module-path warning, saying nothing about the 45 test entries. Its
  common-name check (which does include `test` and `tests`) applies only at the
  library top level; our tree is nested at `agentbundle/build/tests/`. **The tool
  does not detect this defect.**
- **`pydistcheck`** passes our sdist with zero errors by default. Its
  `--expected-directories` form *silently passes* on our wheel: setuptools
  wheels carry no directory entries, so `--inspect` reports `directories: 0` and
  the pattern has nothing to match. The `--expected-files` form does work — exit
  1, 45 unexpected files — and the positive sdist assertion correctly fails when
  the tree is absent.

The directory-pattern result is the reason D5 recommends an in-repo gate: a
check that passes while the property it guards is broken is worse than no check,
and the distinction between the two flags is not discoverable from the
documentation. **Full transcripts of both tool runs, with the source excerpt that
explains the `check-wheel-contents` behaviour, are in
[`0082-notes/enforcement-tool-trials.md`](0082-notes/enforcement-tool-trials.md)**
— D5 is a designated review focus, so its evidence is reproducible rather than
summarised.

### Repo precedent

- **ADR-0071** — establishes `.apm/` as the pack-side runtime export boundary.
  Its rejection of the do-nothing option supplies D1's core argument: correctness
  that depends on a consumer's incidental behaviour rather than on structure
  cannot be checked. Its `Applies to` line names "the packaging path", but in
  context that means the catalogue source archive produced by `catalogue
  package` — not the Python wheel. The engine was never in its scope.
- **`docs/specs/pack-test-boundary-remaining-packs/disposition-record.md`** —
  records the deferral in as many words: *"`agentbundle/build/tests/` is inside
  the package and does ship — nothing moved out of there."* This RFC closes a
  knowingly-left gap, not an unnoticed one.
- **`packages/credbroker/`** — the conformant in-repo precedent for D1.
- **`tools/build_zipapp.py`** — the one correct surface, and the undocumented
  one-liner that makes it correct.
- **`tools/lint-pack-test-boundary.py`** — the pure-stdlib boundary lint written
  for ADR-0071. The direct precedent for D5: this repository already answered
  "what enforces a runtime export boundary?" with in-repo stdlib code once.
- **`packages/AGENTS.md` § Test conventions** — names two of the five locations
  and is silent on distribution.
- **`.github/workflows/release-agentbundle.yml`** — builds both artifacts and
  runs `twine check`, which validates metadata rather than contents. The natural
  insertion point for D5's gate.

### External prior art

Web search was available and used. The proposal draws on a practitioner survey
held outside this repository, but **no claim below rests on that summary**: every
source listed here was fetched directly while drafting this RFC and confirmed to
contain the claim it is cited for. Two of the survey's conclusions did not
survive that check and are corrected in place above — its characterisation of
`go mod vendor` as omitting `*_test.go`, and its reading of which enforcement
check catches a nested test tree. The load-bearing claims:

- [PyPA, Package Formats](https://packaging.python.org/en/latest/discussions/package-formats/)
  — wheels should never include tests and documentation, while sdists commonly
  do. This is D2's foundation.
- [pytest, Good Integration Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
  — tests outside application code, so they run against the installed package.
  D1's foundation.
- [setuptools #3017](https://github.com/pypa/setuptools/issues/3017) and its fix
  in [#3018](https://github.com/pypa/setuptools/pull/3018) — the worked precedent
  for this exact defect, remedied by exclusion rather than relocation. D1's
  counter-case.
- [setuptools #3260](https://github.com/pypa/setuptools/issues/3260) and
  [#2347](https://github.com/pypa/setuptools/issues/2347) — the two traps option
  B inherits and the `MANIFEST.in` staleness the migration must handle.
- [conda-forge, adding tests](https://conda-forge.org/docs/tutorials/adding-tests/)
  — the redistributor evidence behind D2's sdist half, including the verbatim
  fallback: *"packages may not include the necessary test files in the source
  distribution. If running the tests is desirable in these cases, you may need to
  use the GitHub source archive created for a tag."*
  **A caveat on the Fedora evidence.** Fedora is frequently cited as *requiring*
  the upstream suite in `%check`. That requirement's strength has moved — it was
  proposed as a MUST, relaxed to a SHOULD after pushback during the guidelines
  overhaul, and later restated more strongly — and the canonical guidelines page
  could not be retrieved to confirm the current wording. The Fedora strand is
  therefore treated as corroborating, not load-bearing; D2's sdist half rests on
  the PyPA guidance and the conda-forge documentation above, both verified
  directly.
- [discuss.python.org, "Should sdists include docs and tests?"](https://discuss.python.org/t/should-sdists-include-docs-and-tests/14578)
  — both the support and the dissent recorded under *Drawbacks*.
- [Go Modules Reference](https://go.dev/ref/mod),
  [cargo-vendor-filterer](https://github.com/coreos/cargo-vendor-filterer/), and
  [pip's vendoring policy](https://pip.pypa.io/en/stable/development/vendoring-policy/)
  — the cross-ecosystem vendoring consensus behind D3.
- [check-wheel-contents](https://github.com/jwodder/check-wheel-contents) and
  [pydistcheck](https://pydistcheck.readthedocs.io/) — D5's candidates, tested
  above rather than taken on documentation.

**Empty prior art is itself a finding, and there is one here.** No source
addresses a package that ships through several channels at once with a different
test-inclusion rule per channel. The per-surface rule in D2 is composed from
single-surface guidance, not lifted from an established multi-surface policy. If
a reviewer knows of a project that has published one, that would be better
evidence than anything cited here.

## Open questions

1. **Should the CI gate fail the build or warn on first introduction?**
   Recommended default: fail immediately. The defect it guards exists today, so
   the gate is written against a known-good post-migration state and has nothing
   to grandfather. · owner: eugenelim · decide-by: the implementing spec.
2. **Does the shipped Windows self-host runner belong inside the export
   boundary?** `self_host_windows.py` ships in every artifact and invokes the
   test suite by path — a test runner living on the wrong side of the line this
   RFC draws. Recommended default: relocate it out of the package in the
   implementing spec, since it is developer tooling rather than engine runtime.
   Deliberately *not* decided here: it was surfaced by adversarial review after
   the options were framed, and it deserves its own analysis rather than being
   folded into D1 late. · owner: eugenelim · decide-by: the implementing spec.

D2's sdist half is decided in the table above, not parked here. A reviewer who
weighs assumption 3 lower can partially accept — take the wheel, zipapp, and
vendored halves now and defer the sdist graft — by saying so against D2.

## Follow-on artifacts

Accepted 2026-08-08. The ADR is authored; the two specs follow.

- **[ADR-0075](../adr/0075-test-ownership-taxonomy-and-per-owner-inclusion.md)** — **authored**. Records the
  ownership taxonomy, its four homes, the class-level granularity, and the
  per-surface per-owner inclusion rule. It must record its relationship to ADR-0071
  precisely: ADR-0071's `.apm/` boundary and `packs/<pack>/tests/` destination
  stay in force, so the new ADR carries `Related: ADR-0071` and states the
  partial supersession in prose — **not** `Supersedes: ADR-0071`, which would
  mark a still-governing decision as dead. ADRs are immutable here and CI
  enforces it, so the correction lives in the new ADR naming the old one, never
  in an edit to ADR-0071.
- **Spec 1 — engine export boundary.** Move the test tree out of the package →
  the vendored exclusions → the `self_host.py` guard rewrite → the absence-half
  CI gate → one release. Release-blocking; lands first. The `MANIFEST.in` graft
  is **not** here — it belongs to spec 2, once the engine suite is self-contained.
- **Spec 2 — catalogue and pack carve-out.** Classify per D6 → relocate to
  `tests/conformance/`, `tests/roster/`, and `packs/<pack>/tests/` → make shipped
  tests rule-shaped per D7 → widen the four positive allowlists → wire
  `catalogue package` and `agentbundle catalogue init` (default preset *and* both
  `--preset self-hosted --tooling` modes) → land the `MANIFEST.in` graft with
  fixture coverage → verify by scaffolding a catalogue and running its
  materialised suite.
- **`packages/AGENTS.md`** — extend § Test conventions to name the taxonomy, the
  four homes, and the `tools/` destination. It currently names two roots of what
  is now a four-owner model.
- **The scaffold's authoring guidance** — a new catalogue should be told it owns
  a `tests/` tree and what belongs in it.

One unrelated defect surfaced during research and is deliberately excluded from
this RFC's scope: the wheel ships `agentbundle/_data/install-marker.py` at a
non-importable path. It needs a `[backlog].open` slug in `workspace.toml` so it
survives this RFC being rejected or its follow-ons stalling.

(A second finding — that `catalogue verify` is described as an "18-step" pipeline
at several sites while it now runs nineteen — is already owned by the approved
`docs/specs/catalogue-verifier-correctness/` spec, which enumerates the same
sites. Cited rather than re-listed here, so the two do not drift.)
