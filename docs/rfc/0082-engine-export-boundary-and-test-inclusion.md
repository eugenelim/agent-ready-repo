# RFC-0082: Engine export boundary and per-surface test inclusion

- **Status:** Draft
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-07
- **Date closed:**
- **Decision weight:** heavy
- **Related:** [ADR-0071](../adr/0071-pack-runtime-export-boundary-and-test-placement.md)
  (the pack-side companion this extends to the engine),
  [`docs/specs/pack-test-boundary-remaining-packs/`](../specs/pack-test-boundary-remaining-packs/)
  (whose disposition record names the gap this closes),
  [`0082-notes/`](0082-notes/) (promoted spike transcripts)

## Reviewer brief

- **Decision:** whether `packages/<pkg>/<pkg>/` is the engine's runtime export
  boundary, with test inclusion decided per distribution surface rather than
  uniformly.
- **Recommended outcome:** accept.
- **Change if accepted:**
  - `packages/agentbundle/agentbundle/build/tests/` relocates to
    `packages/agentbundle/tests/build/`. The importable package does not move.
  - The source distribution carries the complete test tree; the wheel, the
    zipapp, and the vendored copy carry none.
  - Two pure-stdlib enforcement instruments, both in-repo: an artifact gate
    over the built wheel and sdist, and a unit test over the vendored payload.
- **Affected surface:** four distribution surfaces (wheel, sdist, zipapp,
  `agentbundle init --tooling vendored`); the ten operative files that reference
  the current test path, enumerated in *Evidence*; plus `packages/AGENTS.md`,
  which documents the convention but carries no path reference; and
  `build/self_host.py`'s fixture guard plus its covering test. No pack *source* changes, though the
  vendored surface currently carries pack tests and this RFC closes that too. No
  adopter-visible CLI change.
- **Stakes:** reversible. The relocation is a `git mv`, two enumerable edit sets
  (path anchors inside the suite, operative references outside it), and one
  behavioural rewrite — a shipped destructive-write guard that the new layout
  would silently disable; the per-surface rule is packaging configuration.
- **Review focus:** (1) that the asymmetry in D2 is argued rather than asserted,
  and (2) that D5's enforcement instruments actually fire — the third-party tool
  the supporting research recommended does not, and getting all four surfaces
  right takes two instruments plus a layout argument for the zipapp.
- **Not in scope:** any version bump *in this RFC* — the implementing changeset
  carries exactly one; src layout; pack test placement (ADR-0071 owns it);
  relocating `tools/test*.py`.

## The ask

**Recommendation (BLUF).** Adopt `packages/<pkg>/<pkg>/` — the importable Python
package directory — as **the engine's runtime export boundary**: the line past
which content is shipped to a consumer, and inside which tests never live. *The
engine* here means the `agentbundle` Python package: the CLI and build machinery
this repository publishes to PyPI. Then decide test inclusion **per distribution
surface** rather than uniformly: the source distribution yes and complete; the
wheel, the zipapp, and the vendored copy no.

This is the engine-side companion to **ADR-0071**, which decided the same
question one directory level down, for *packs*. A **pack** is one installable
bundle of skills, subagents, and hooks living at `packs/<name>/`; the engine
installs packs into a user's repository. ADR-0071 established that a pack's
`.apm/` subdirectory — the part of the pack that gets projected into an adopter's
tree — is *that* boundary, and moved pack tests out of it to `packs/<pack>/tests/`.
Its reasoning transfers directly: a boundary that holds only because consumers
happen not to look past it is not a boundary.

**Why now (SCQA).**

*Situation.* ADR-0071 (2026-08-06) settled where pack tests live and what `.apm/`
exports across the boundary.

*Complication.* It scoped itself to packs. The engine — the `agentbundle` Python
package — has test code in several places, one written convention naming two of
them, and four distribution surfaces that each behave differently. Measured against
`agentbundle` 0.29.8 on 2026-08-07: the wheel ships 45 test entries out of 184;
the source distribution ships exactly 8 top-level test files and no
`conftest.py`, so they cannot be run; `agentbundle init --tooling vendored`
sweeps the working tree with no exclusions whatsoever. Only the zipapp is
correct, and its rule is a one-liner in `tools/build_zipapp.py` that no document
records. A *disposition record* — the note a completed piece of work leaves
behind saying what it decided itself versus what it escalated — written the day
before this RFC names the gap outright: *"`agentbundle/build/tests/` is inside
the package and does ship — nothing moved out of there."*

*Question.* Where is the engine's export boundary, and what does each surface
carry across it?

### Decisions requested

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Relocate the in-package test tree, or exclude it in packaging config? | Relocate to `packages/agentbundle/tests/build/` | Both cheaper fixes leave the tests inside the boundary, so the rule stays uncheckable; setuptools chose exclusion under compatibility pressure this repo does not have | this review | Confirm relocation over the two exclusion variants; confirm src layout stays deferred |
| D2 | One test-inclusion rule for all surfaces, or one per surface? | Per surface — sdist yes, wheel/zipapp/vendored no | PyPA: wheels should never include tests, sdists commonly do; conda-forge builds from the sdist and runs the suite | this review | Rule on the asymmetry — or partially accept, deferring the sdist half |
| D3 | Should the vendored copy carry tests? | None — it is wheel-class (option C) | Its documented consumption path is `pip install -e`, so it is an install source, not a source tree; adopter assurance comes from `agentbundle catalogue verify` | this review | Confirm the classification |
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

The consequence is four distribution surfaces behaving four ways. Measured
against `agentbundle` 0.29.8 by building both artifacts from a clean source copy
on 2026-08-07:

| Surface | Built by | Test content today | Correct? |
| --- | --- | --- | --- |
| zipapp (`.pyz`) | `tools/build_zipapp.py` | none — `shutil.ignore_patterns("__pycache__", "tests", "*.pyc")` | yes, by an undocumented one-liner |
| wheel | `python -m build` | 45 of 184 entries are the in-package test tree | no |
| sdist | `python -m build` | the in-package test tree's `.py` modules only — its fixtures absent — plus exactly 8 top-level `tests/test*.py` files, and no `conftest.py` | no — present but unrunnable, for two independent reasons |
| vendored | `agentbundle init --tooling vendored` | the entire working tree of `packages/agentbundle/`, unfiltered, **and** the whole of `packs/catalogue-curation/` including its pack tests | no |

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

1. State the engine's export boundary once, in a form that structure enforces
   rather than convention asserts.
2. Give each distribution surface a stated, justified test-inclusion rule.
3. Make the rule checkable in CI, so it fails on regression rather than on
   review attention.
4. Record `tools/test*.py` co-location as a deliberate exception, so it stops
   reading as a fourth unexplained convention.

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
- **A repository-root `tests/` tree.** A new top-level directory is RFC-gated
  here, and ADR-0071 rejected the equivalent for packs on the grounds that it
  separates a test from the thing it validates.
- **Fixing the unrelated packaging defects this RFC's research surfaced.** The wheel also
  carries `agentbundle/_data/install-marker.py` at a non-importable path, and the
  sdist carries `agentbundle.egg-info/`. Both are real; neither is this boundary.

## Proposal

### The boundary

> `packages/<pkg>/<pkg>/` — the importable Python package directory — is the
> engine's runtime export boundary. Tests never live inside it.

This is the same shape of rule as ADR-0071's, one level up the tree: there,
`.apm/` is the boundary and pack tests live at `packs/<pack>/tests/`; here, the
package directory is the boundary and engine tests live at
`packages/<pkg>/tests/`.

**The source code does not move.** Only the test tree does.

```
packages/agentbundle/
├── agentbundle/                  ← unchanged; this directory IS the boundary
│   ├── build/
│   │   ├── tests/                ← moves out
│   │   ├── main.py  adapters/  recipes/  …    ← stay
│   ├── commands/  catalogue_tooling/  _data/  cli.py  …   ← stay
├── tests/
│   ├── unit/                     ← unchanged
│   ├── integration/              ← unchanged
│   └── build/                    ← lands here
├── conftest.py
└── pyproject.toml
```

Every import path is preserved. `agentbundle.build.main`, `agentbundle.cli`, and
every other module resolve exactly as before. The single name that stops
resolving is `agentbundle.build.tests`, which nothing imports.

### Per-surface test inclusion

| Surface | Tests | Rationale |
| --- | --- | --- |
| **sdist** | **yes** — complete, via an explicit `graft` | Downstream redistributors build from sdists and run the suite. A partial tree is worse than none. |
| **wheel** | no | A wheel contains exactly what is installed, and nothing more. |
| **zipapp** | no | Build-essential code only; already correct, now written down. |
| **vendored** | no | Wheel-class — see D3. |

The sdist rule needs a `MANIFEST.in` with an explicit `graft tests`, because
setuptools' default sweep is partial by design. Two documented traps apply and
must be handled in implementation: `MANIFEST.in` is order-dependent (a
`global-exclude` placed before a `graft` does not apply to the grafted files),
and a stale `.egg-info/SOURCES.txt` causes setuptools to reuse the previous file
list rather than regenerate it, so `MANIFEST.in` edits silently do not take
effect.

### Why the vendored copy is wheel-class

This is the contested call, so the reasoning is stated rather than assumed.

`agentbundle init` scaffolds a new catalogue — an adopter's own repository of
packs, built on this engine. Its `--tooling` flag takes two values: `external`,
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

**This surface also leaks *pack* tests, which ADR-0071 was supposed to have
closed.** Vendored mode calls `_collect_dir_bytes` a second time, on
`packs/catalogue-curation/`, copying it wholesale to
`.agentbundle/tooling/packs/catalogue-curation`. That pack carries its own tests
at `packs/catalogue-curation/tests/`, exactly where ADR-0071 put them — and they
ride along. ADR-0071's reasoning for why pack tests never reach an adopter is
that *"projection adapters read only `.apm/` and `seeds/`"*. That reasoning does
not cover this path, because vendored mode is a raw tree copy, not a projection
adapter. It is a genuine hole in an accepted decision, found by this RFC's
research and closed by the same exclusion work — carefully, because the routine
these two copies share is also used by the paths that must keep carrying tests.
See migration step 2.

### `tools/` — a named exception

`tools/test*.py` stays co-located with the scripts it tests. The boundary is
scoped to distribution surfaces, and `tools/` crosses none: no packaging
configuration references it — not `[tool.setuptools.packages.find]`, not
`[tool.setuptools.package-data]`, and not `[catalogue.package].include`, which
lists only `packs/core`. The exception is recorded here and in
`packages/AGENTS.md` so that it reads as a decision rather than an oversight.

### Enforcement

A pure-stdlib checker in `tools/`, run in `release-agentbundle.yml` immediately
after the existing "Build wheel + sdist" step. It opens the built artifacts with
`zipfile` and `tarfile` and asserts both halves of the rule: no test content in
the wheel, and a complete test tree — modules *and* fixtures — in the sdist.
Roughly thirty lines, no new dependency, and consistent with this repo's standing
rule that new `tools/` scripts are pure-stdlib Python.

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

### Migration path

Sequenced so each step is independently verifiable:

1. **Move the tree, and update every operative reference.** `git mv`, the
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
2. **`MANIFEST.in` and the vendored exclusions.** Graft the test tree into the
   sdist — including its non-`.py` fixtures, which `package-data` does not carry
   today and which are the second reason the shipped tests cannot run. A third trap
   applies here beyond the two named above: setting `include_package_data = True`
   would promote the newly grafted tree into the *wheel*, inverting D2. The
   package sets it nowhere today, and must not start.
   Then exclude tests from the vendored payload — **at the call site, not inside
   `_collect_dir_bytes`.** The routine has four callers, and only two of them are
   vendored: the engine copy and the `packs/catalogue-curation/` copy. The other
   two copy the adopter's selected packs and shared guides in *every* mode, and
   those must keep carrying tests — ADR-0071 says catalogue archives carrying
   tests is *wanted*. An implementer who adds the exclusion inside the shared
   routine would strip tests from the adopter's own catalogue and break an
   accepted decision this RFC explicitly upholds.
3. **Adopter wiring — probably nothing, and the RFC should say so.** The engine
   ships a bundled *catalogue scaffold*: the file tree `agentbundle init`
   materialises into a newly-created catalogue. The original sketch of this
   migration assumed the scaffold needed updating. On inspection it holds
   `packs/`, `profiles/`, and `guides/` and no Python package at all, so the
   boundary this RFC defines — a rule about `packages/<pkg>/<pkg>/` — has nothing
   to attach to there. An adopter's own packs are already governed by ADR-0071
   via the scaffold's pack authoring guidance.

   The one arguable edit is a line telling adopters that a vendored
   `.agentbundle/tooling/` tree is engine-owned and not somewhere to add their
   own tests. That is worth a sentence at most. Its marginal cost is one
   scaffold-sync run — the version bump and the `Engine-Change-RFC:` trailer are
   already owed by steps 1, 2, and 5, so they are not an argument against this
   step. **Recommendation: skip it anyway**, on the merits rather than the cost:
   the boundary is engine-internal and an adopter has nothing to apply it to.
   Revisit only if the implementing spec finds a concrete rule an adopter would
   otherwise get wrong.
   Recorded rather than deleted, because "we looked and there was nothing to do"
   is a more useful migration note than silence.
4. **CI gate.** Add both instruments. Wire the artifact gate into the release
   workflow's build job, immediately after the artifacts are produced — and add
   the gate script's own path to that workflow's `pull_request.paths` filter,
   which today lists only `packages/agentbundle/**` and the workflow file. Without
   that, a pull request changing only the gate would never run it.
5. **One release, cut last.** The whole changeset ships together, with the single
   version bump this repository requires for a non-cosmetic package change. *This
   RFC changes no code and bumps nothing*; the bump belongs to the implementing
   changeset.

## Options considered

### D1 — how the boundary is achieved

MECE along *how much of the tree's identity changes*: nothing changes; only
packaging configuration changes; only the directory's package-ness changes; the
directory moves; the directory and the package both move. Those five exhaust the
axis — there is no sixth position between "delete one marker file" and "move the
directory".

| Option | Trade-off | If accepted |
| --- | --- | --- |
| **A — do nothing** | zero work | The wheel keeps shipping tests, the sdist keeps shipping unrunnable ones, and there is still no rule to cite in review. Cost of delay: every new test module compounds the eventual move. |
| **B — exclusion only** | smallest diff; no path churn | Correctness stays configuration-deep and re-breakable, and getting it right is subtler than it looks. Measured: `exclude = ["tests", "tests.*"]` — the form the setuptools issue below is usually quoted for — matches **nothing** here, because those patterns are anchored at the top level and this tree is nested; only `["*.tests", "*.tests.*"]` empties the set. `include_package_data = True` would independently defeat either. Each surface then needs its own separate correct exclusion. Most damning: the rule stays uncheckable — "do not put tests here" cannot be verified when tests are already there. |
| **B′ — delete `build/tests/__init__.py`** | one file deleted; zero configuration | The intuitive minimal fix, and it **does not work**. Measured: with `namespaces = true` (the default), deleting the marker leaves 44 of 45 test entries in the wheel, because PEP 420 discovery does not need it. To make B′ function it must become "delete the marker *and* set `namespaces = false`" — at which point it is option B with an extra step, carrying the same uncheckability, and still leaving the sdist and vendored surfaces untouched. Listed because it is the option a reader will reach for, and it is worth recording that it was measured rather than assumed. |
| **C — relocate the test tree ★** | one mechanical move, two enumerated edit sets, and one guard rewrite | The boundary becomes structural. All four surfaces inherit correctness from layout rather than from four separate correct configurations. Cost: the path-anchor and operative-reference edits enumerated in *Evidence*. |
| **D — relocate, and adopt a src layout** | the fuller upstream recommendation | Touches every path resolution in the package, plus editable-install machinery. Large blast radius for a marginal gain over C. |

**Prior art.** B is what setuptools did for exactly this defect: its own wheel
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

### D3 — the vendored copy's assurance instrument

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

**Operative references outside the suite.** A separate, unfiltered sweep for the
literal path found ten files that must change with it. It is listed here because
the migration's size claim depends on it, and because the first version of this
RFC named four and was wrong:

| File | References | Note |
| --- | --- | --- |
| `.github/workflows/build-check.yml` | 17 | the bulk of the work; a filtered sweep misses this |
| `.github/workflows/catalogue-tooling-ci-gates.yml` | 5 | |
| `agentbundle/catalogue_tooling/self_host_windows.py` | 4 | **shipped engine code** — see *Risks*, assumption 1 |
| `pyproject.toml` (repository root) | 2 | mypy `exclude` |
| `packages/agentbundle/pyproject.toml` | 1 | `testpaths` |
| `packages/agentbundle/tests/integration/test_install_snapshot.py` | 1 | a test asserting on the other test root |
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

Filled in on acceptance.

- **ADR** recording the boundary and the per-surface rule as a decision.
- **Spec** covering the migration, sequenced as: move the test tree →
  `MANIFEST.in` and the vendored exclusions → catalogue-scaffold adopter wiring
  (conditional — recommended skipped; see migration step 3) →
  CI gate → a single release cut last.
- **`packages/AGENTS.md`** — extend § Test conventions to name the boundary, all
  engine test roots, and the `tools/` exception.

One unrelated defect surfaced during research and is deliberately excluded from
this RFC's scope: the wheel ships `agentbundle/_data/install-marker.py` at a
non-importable path. It needs a `[backlog].open` slug in `workspace.toml` so it
survives this RFC being rejected or its follow-ons stalling.

(A second finding — that `catalogue verify` is described as an "18-step" pipeline
at several sites while it now runs nineteen — is already owned by the approved
`docs/specs/catalogue-verifier-correctness/` spec, which enumerates the same
sites. Cited rather than re-listed here, so the two do not drift.)
