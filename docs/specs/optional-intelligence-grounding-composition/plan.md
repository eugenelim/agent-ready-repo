# Plan: Optional intelligence in repository grounding

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `packs/core/.apm/skills/new-spec/scripts/explore-grounding.py`; `packs/core/tests/skills/new-spec/test_explore_grounding.py`; `packs/core/.apm/skills/project-knowledge/SKILL.md` and `packs/core/tests/skills/project-knowledge/` as precedent for a reusable Core inquiry owner and its construction tests; `packs/core/.apm/skills/close-work/scripts/file_safety.py` and `tests/roster/test_close_work_extraction_and_immediate_disposition.py` (`test_projected_file_safety_matches_the_agentbundle_canonical`) as precedent for a co-located confinement helper and its byte pin; `Makefile` `run-test-suite` list and `tools/lint-ci-parity.py` `SUITE_DISPOSITION` as the suite registration path; `packs/AGENTS.md#version-bump-rule`; `docs/architecture/loop-contract.md`; `docs/rfc/0079-codebase-context-pack.md`.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> execution observations belong in `notes/verification-ledger.md`.

## Approach

Extract the existing path-seeded explorer into a narrow public
`repository-grounding` skill while preserving its command behavior and tests.
The explorer remains the repository-native probe. A new locator reader becomes
the only route by which a provider-returned file locator is read. The skill
owns the agent-level decision to consider an already-exposed capability,
invoke it in its native shape, carry caveats, verify load-bearing claims, or
deliberately fall back. `new-spec` delegates its existing grounding step to
this owner and never learns provider identities or lifecycle. Recorded
behavior-evaluation runs prove the agent-level cases, script tests prove the
deterministic ones, and a Core render verifies adapter parity.

## Constraints

- RFC-0079 owns exposed-capability discovery, native provider shapes,
  attribution, fallback, authority, and locator safety. Its D1 requires a
  change to name the inquiry owner before composing a provider, and forbids
  putting provider handling in the consuming workflow.
- ADR-0037 D5 makes every grounding read presence-checked: absence never fails
  the loop and is never CI-gated. No other part of ADR-0037 governs this work.
- `packs/AGENTS.md` and `packs/AGENTS.local.md` own version derivation, the
  complete pack release pipeline, the governance-citation grep for shipped
  content, and the byte pin on every hand-maintained `packs/**` copy of the
  confinement helper.
- Core must install and pass without `packs/code-intelligence`, Wicked Estate,
  an index, or any other provider.
- The repository-native explorer never becomes a provider broker and accepts no
  normalized provider payload. The locator reader accepts one locator string,
  not a provider result.
- Canonical `.apm` sources move first; generated projections are rebuilt rather
  than edited.
- `tools/AGENTS.md` requires a `SUITE_DISPOSITION` entry for every added or
  moved `run-test-suite` target.

## Construction tests

**Integration tests:** recorded behavior-evaluation runs ask the same grounding
question with a useful exposed capability and with no provider, and cover poor
fit, refusal, unavailability, timeout, malformed and incomplete output,
source conflict, unverifiable claims, disclosure, unsafe locators, and
provider output that carries instructions. A Core render proves
every declared adapter target contains the new skill.

**Manual verification:** inspect a rendered Core-only projection and confirm the
grounding inquiry completes without provider messaging; inspect a provider-fit
run and confirm the consuming `new-spec` procedure contains no provider step.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `packs/core/.apm/skills/repository-grounding/` | T1, T2 | Script tests and recorded behavior-evaluation runs | Core render inventory and shipped skill inventory |
| Core release pipeline surfaces | T1, T4 | Version-rule derivation, manifest parity, changelog, and Highlights-disposition checks | Required release surfaces agree on the target and consumer outcome |
| `packs/core/.apm/skills/new-spec/SKILL.md` | T3 | Delegation and absence assertions | Main-flow review finds no provider lifecycle branch |
| `packs/core/README.md` | T3 | Documentation assertions and link check | Public description matches shipped behavior |
| Reusable-learning disposition | T4 | Capture receipt or explicit no-capture note | Closeout records one disposition |

## Design (LLD)

### Design decisions

**A new owner, holding the existing baseline.** FEAT-0029 asked which existing
grounding owner holds the seam. The only existing one is the path-seeded
explorer, and it lives inside `new-spec`. Putting provider guidance there would
put provider handling in a consuming workflow, which RFC-0079 D1 and the
intent's boundary both forbid. So the existing baseline moves, unchanged, into
its own `repository-grounding` skill, and the provider guidance lands beside
it. The owner is new as a skill; the baseline it holds is the existing one.

**The `new-spec` edit is a delegation, not a main-flow change.** Step 3 still
runs the same path-seeded inquiry at the same point with the same seeds. Only
the path by which it reaches the explorer changes.

**The provider branch is guidance; the locator read is code.** Whether to use a
provider, how to invoke it, and when to fall back are agent choices, so they
live in `SKILL.md` and are proved by recorded behavior-evaluation runs. Reading
a file a provider pointed at is deterministic, so it is a script with tests.
This keeps provider transports out of Core code while giving the one risky
operation a single enforced route. Traces to AC-0001, AC-0002, AC-0003,
AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, and AC-0014.

**No compatibility wrapper, and a minor version.** The explorer's old path is a
script inside `new-spec`, invoked only by `new-spec`'s own procedure through a
skill-relative `<skill-dir>` path that T1 rewrites. It is not a primitive, so
moving it removes no skill, agent, command, or hook. Adding the
`repository-grounding` skill is a new primitive, so the version rule's class is
minor. Traces to AC-0013.

Owned by: T1, T2, T3

### Interfaces & contracts

The explorer CLI `explore-grounding.py --root <root> --phase <phase> <seed...>`
stays stable after relocation: it exits 0, including when an input is
unavailable, and exits 2 only when a seed escapes the root.

The locator reader is new:

```text
read-locator.py --root <repo> [--approved-root <dir>]... --locator-b64 <base64>
```

**Transport.** Provider-returned text never appears on a command line. The
agent passes the locator only as the standard base64 encoding of its UTF-8
bytes. That alphabet (`A-Z`, `a-z`, `0-9`, `+`, `/`, `=`) means nothing to a
POSIX shell, PowerShell, or `cmd.exe`, so no locator text can end a quote, run
a command, expand a variable, or change encoding on the way in. An encoding
slip by the agent fails safe: it is refused, or names a file that is missing.

- Every run that parses its arguments first prints `received: <decoded
  locator as a JSON string>` on stdout, so the text the reader acted on can be
  compared byte-for-byte with the provider's literal locator. The string is
  written by `json.dumps(text, ensure_ascii=True)`, so every non-ASCII
  character, U+0085, U+2028, and U+2029 included, appears only as a `\u`
  escape, and no hostile locator can forge a later output line.
- Exit 0: then prints `root: <absolute root>`, then `source: <path relative to
  that root>`, both as JSON strings written the same ASCII-only way, then the
  file text.
- Exit 3: then prints `refused: <reason>`. Reasons are `encoding`,
  `line-break`, `scheme`, `authority`, `nul`, `parent-segment`,
  `outside-roots`, `missing`, `unsafe-file`, and `oversize`.
- Exit 2: a usage error, such as a missing or repeated `--locator-b64`; the
  option uses an argparse action that rejects a second occurrence. It
  prints usage text on stderr and nothing on stdout, so no `received:` line
  appears.

The same module exposes `read_locator(root, locator, approved_roots=())`, which
takes the decoded locator text and returns a result with `status` (`read` or
`refused`), `reason`, `root`, `path`, and `data`. Tests call this function
rather than spawning a process; the CLI owns decoding.

Locator handling runs in this order, and nothing touches the filesystem before
step 5:

0. **Decode, then take one line.** The CLI decodes `--locator-b64` with strict
   base64 validation and strict UTF-8; either failure is refused as
   `encoding`, with `received:` printed as `null`. `read_locator` then refuses
   as `line-break` any character Python's `str.splitlines` treats as a line
   boundary: LF, CR, VT, FF, the file, group, and record separators, U+0085,
   U+2028, and U+2029.
1. **Classify the form.** A locator starting with a drive letter and a
   separator (`C:\` or `C:/`) is a path. A locator whose scheme is `file`
   (case-insensitive) is a URI. Any other `<scheme>:` prefix is refused as
   `scheme`, unless everything after the first `:` is a `<line>` or
   `<line>:<col>` suffix of digits, in which case the locator is a path. So
   `src.py:3` and `Makefile:12:4` are paths, and `https://x` and `pkg:Thing`
   are refused.
2. **Split before decoding.** From a URI, the fragment is split off at the
   first `#` and discarded, and then a trailing `:<line>` or `:<line>:<col>`
   suffix is split off the raw text. Its authority must be empty or
   `localhost`, or it is refused as `authority`. Only then is its path
   percent-decoded, exactly once. From a path, a trailing `:<line>` or
   `:<line>:<col>` suffix, or a trailing `#L<line>`, is split off; a path is
   never percent-decoded.
3. **Check the final path.** After any percent-decoding, a NUL byte is
   refused as `nul`, any `str.splitlines` boundary is refused as `line-break`,
   and a `..` segment, with both `/` and `\` as separators, is refused as
   `parent-segment`.
4. **Place the path.** Each root is made absolute with `os.path.abspath`, which
   follows no link. A relative path joins the repository root. An absolute
   path is matched against each root's absolute spelling and then its
   `os.path.realpath` spelling, so a provider's canonical path matches a root
   reached through a system link such as `/var` to `/private/var`. On Windows,
   both sides pass through `os.path.normcase` first, so drive and path case do
   not matter. Only the root's own prefix is translated; no component inside
   the root is resolved.
   A path under no root is refused as `outside-roots`. On Windows, a decoded
   URI path of the form `/C:/x` drops its leading `/` and is placed as the
   drive-letter path `C:/x`. On any other platform, a drive-letter path or URI
   can name no file under a root and is refused as `outside-roots`.
5. **Read through the helper.** The file is read with
   `read_confined_regular_file(root, path, max_bytes=MAX_READ_BYTES)` from the
   co-located `scripts/file_safety.py`. `MAX_READ_BYTES` is loaded from
   `explore-grounding.py` rather than copied.
6. **Classify a refusal.** `BoundExceeded` becomes `oversize`. Any other
   `UnsafeContentError` becomes `missing` when its chained cause is a
   `FileNotFoundError`, and `unsafe-file` otherwise. The helper opens every
   component without following links, so a linked component fails with a
   different cause and is never classed as missing.
   Classification reads only the exception type and its chained cause, never
   message text, and it never turns a refusal into a read.

`--approved-root` is supplied only from the user's explicit statement or the
calling workflow's declared bounds. `new-spec` declares none in this slice.
`SKILL.md` forbids taking an approved root from provider output, and a symbol
locator without a file location is never passed to the reader.

`new-spec` invokes the public `repository-grounding` method with its discovery
seed paths. There is no provider request or response interface. Evidence
returns through the inquiry's ordinary report with source class, attribution,
and material limits. Traces to AC-0005, AC-0007, AC-0008, and AC-0009.

Owned by: T1, T2, T3

### Failure, edge cases & resilience

No exposed capability, poor semantic fit, refusal, timeout, malformed or
incomplete output, and unavailable indexes all converge on the baseline.
Conflicting derived evidence remains visible but cannot satisfy the question.
Every locator refusal is reported with its reason, and the inquiry returns to
the baseline without hiding the unsafe result. The co-located confinement
helper enforces no-follow open, regular-file and root-containment checks,
hard-link refusal, byte bounds, and pre/post-open identity comparison. Traces
to AC-0001, AC-0003, AC-0004, AC-0005, and AC-0006.

Owned by: T2

### Dependencies & integration

`repository-grounding` depends only on Core and the Python standard library.
Its `scripts/file_safety.py` is a byte-identical copy of the blessed helper,
pinned by a test, because an installed Core has no `agentbundle` to import.
Optional providers are discovered from the active authorized surface at run
time; none is installed, imported, registered, or version-matched by Core.
`new-spec` is the sole consumer changed in this slice. Traces to AC-0005,
AC-0006, AC-0007, AC-0008, AC-0009, and AC-0010.

Owned by: T1, T2, T3

## Tasks

### T1: The path-seeded baseline has one public grounding owner without behavior drift

**Depends on:** none

**Touches:** `packs/core/.apm/skills/repository-grounding/**`, `packs/core/.apm/skills/new-spec/scripts/explore-grounding.py`, `packs/core/.apm/skills/new-spec/SKILL.md` (its step-3 grounding sentence and its own-scripts list), `packs/core/tests/skills/new-spec/test_explore_grounding.py`, `packs/core/tests/skills/repository-grounding/**`, `Makefile`, `tools/lint-ci-parity.py`, `tools/shard_test_roster.py`, `tools/test_local_ci_shared_test_deduplication.py`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/architecture/loop-contract.md`, and the regenerated projections `.claude/skills/new-spec/**`, `.agents/skills/new-spec/**`, `.claude/skills/repository-grounding/**`, and `.agents/skills/repository-grounding/**`

**Verification mode:** TDD regression checks plus goal-based registration and
release-pipeline checks.

**Tests:**
- The relocated `test_explore_grounding.py` keeps every current phase, outcome
  class, bound, and confinement case, including exit 2 on an escaping seed
  (AC-0009).
- `test_explorer_has_one_home_under_repository_grounding` — AC-0009 —
  `stub: true`, at
  `packs/core/tests/skills/repository-grounding/test_owner_layout.py`.
  Validated 2026-10-04 in disposable scratch: `py_compile` passed, and pytest
  failed red on `assert owner.is_file()` because the owner does not exist yet.

```python
"""The path-seeded explorer has exactly one home: the grounding owner."""

from __future__ import annotations

from pathlib import Path

SKILLS = Path(__file__).resolve().parents[3] / ".apm" / "skills"


# STUB: AC0009
def test_explorer_has_one_home_under_repository_grounding() -> None:
    """The explorer moved, and no second editable copy stayed behind."""
    owner = SKILLS / "repository-grounding" / "scripts" / "explore-grounding.py"
    former = SKILLS / "new-spec" / "scripts" / "explore-grounding.py"
    assert owner.is_file()
    assert not former.exists()
```

- `make test` gains a `run-test-suite` line for
  `packs/core/tests/skills/repository-grounding/`, with a matching
  `SUITE_DISPOSITION` entry and shard weight; running that line collects the
  relocated tests, and `tools/lint-ci-parity.py` passes. `no stub (mode)`:
  goal-based registration check.
- `tools/test_local_ci_shared_test_deduplication.py` re-pins
  `APPROVED_STANDALONE_PLAN_DIGEST` and `APPROVED_COMPOSED_PLAN_DIGEST` with a
  comment in the file's existing re-pin shape: sole-cause evidence that the
  only Makefile change is the one added line, and evidence that the prior pins
  were current. `no stub (mode)`: goal-based anchor re-pin.
- `packs/core/tests/skills/new-spec/test_repository_grounding_evals.py` stays
  with `new-spec`: it checks `new-spec`'s own preservation-proof evaluations,
  not the explorer.
- `new-spec/SKILL.md` delegates at step 3: it tells the agent to run the
  `repository-grounding` inquiry with its discovery seed paths, by skill name,
  and its own-scripts list drops the `explore-grounding.py` entry, since that
  list names only scripts under `new-spec`'s own `scripts/`. No live reference
  names the old path after T1. The past-tense mention in
  `docs/product/intents/work-loop-delivery-efficiency.md` is history and stays.
- After `make build-self`, no `new-spec` projection contains the file
  `scripts/explore-grounding.py`. `no stub (mode)`: goal-based projection
  check.
- Pack metadata checks prove `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json` carry the minor target derived under
  AC-0013, and `FORCE=1 make build-self` regenerates matching marketplace
  metadata. `no stub (mode)`: goal-based release check. The changelog entry and
  its Highlights disposition belong to T4, after the consumer-visible change
  exists.

**Approach:** Move the implementation and its explorer tests under the new
owner, register the suite, and update repository references in one change.

**Done when:** the stub is green, the registered suite passes, every tracked
reference resolves to the single implementation, and the version surfaces
agree on the derived target.

### T2: Optional evidence preserves baseline, authority, and locator safety

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/repository-grounding/SKILL.md`, `packs/core/.apm/skills/repository-grounding/references/**`, `packs/core/.apm/skills/repository-grounding/scripts/**`, `packs/core/.apm/skills/repository-grounding/evals/**`, `packs/core/tests/skills/repository-grounding/**`, `tests/roster/test_close_work_extraction_and_immediate_disposition.py`, `.github/workflows/build-check-windows.yml`, `tools/lint-ci-parity.py` (the suite's disposition reason only), and the regenerated projections `.claude/skills/repository-grounding/**` and `.agents/skills/repository-grounding/**`

**Verification mode:** TDD for the locator reader and the helper pin;
behavior evaluation for agent-level cases.

**Tests:**
- `test_confined_file_uri_is_read_and_outside_root_is_refused` — AC-0005 —
  `stub: true`, at
  `packs/core/tests/skills/repository-grounding/test_read_locator.py`.
  Validated 2026-10-04 in disposable scratch: `py_compile` passed, and pytest
  failed red with `FileNotFoundError` for `read-locator.py` because the reader
  does not exist yet.

```python
"""The locator reader is the one route by which a provider locator is read."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS = (Path(__file__).resolve().parents[3]
           / ".apm" / "skills" / "repository-grounding" / "scripts")


def _reader():
    """Load the reader under a pack- and skill-qualified module name."""
    spec = importlib.util.spec_from_file_location(
        "packs_core_repository_grounding_read_locator", SCRIPTS / "read-locator.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# STUB: AC0005
def test_confined_file_uri_is_read_and_outside_root_is_refused(tmp_path: Path) -> None:
    """A confined file URI is read; an absolute path outside every root is not."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src.py").write_text("x = 1\n", encoding="utf-8")
    outside = tmp_path / "secret.txt"
    outside.write_text("token\n", encoding="utf-8")

    accepted = reader.read_locator(repo, (repo / "src.py").as_uri())
    assert accepted.status == "read"
    assert accepted.data == b"x = 1\n"

    refused = reader.read_locator(repo, str(outside))
    assert refused.status == "refused"
    assert refused.reason == "outside-roots"
    assert refused.data is None
```

- The full reader matrix, on real filesystem fixtures (AC-0005):
  - accepted: root-relative, absolute, `file:///`, and `file://localhost/`
    locators; a top-level `src.py:3` and a nested `pkg/mod.py:3:7`; a URI with
    a `#L5` fragment; a `file:///<root>/src.py:3` URI with a line suffix; an
    absolute locator under a relative `--root`; a file inside an explicit
    `--approved-root`, with output naming that root;
  - refused before any filesystem access: locators holding a line feed, a
    carriage return, U+0085, and U+2028, and URIs whose paths decode to them
    through `%0A` and `%E2%80%A8` (`line-break`); `https:` and `pkg:Thing` (`scheme`);
    `file://remote-host/x` (`authority`); NUL (`nul`);
    `file:///<root>/%2e%2e/x`, `src/..:3`, and `src\..\x` (`parent-segment`);
  - refused by placement or the helper: an absolute path under no root, a file
    under an unapproved second root, and on POSIX the drive-letter path `C:/x`
    and URI `file:///C:/x` (`outside-roots`); the plain path `%2e%2e/x`, which
    is never decoded; the URI `<root URI>/src.py%23L5`, which decodes to the
    name `src.py#L5` rather than being stripped, with no file of that name in
    the fixture; and a missing file and
    a missing directory (`missing`); a symlinked file, a symlinked directory, a
    hard link, and a FIFO (`unsafe-file`); a file one byte above
    `MAX_READ_BYTES` beside an accepted file at exactly that size (`oversize`);
    and an identity change between check and open, simulated through the
    helper's seam (`unsafe-file`);
  - on Windows only: the URI built by `Path.as_uri()` from the fixture root
    (`file:///C:/...`) and the same URI with a lowercase drive and an encoded
    colon (`file:///c%3A/...`) are both placed under the root and read.
    Symlink and FIFO cases skip where the platform cannot create them.
- CLI decoding, on in-process `main(argv)` calls: invalid base64 and
  valid base64 of invalid UTF-8 are refused as `encoding` with
  `received: null`; the base64 of `` src.py'; $(touch PWNED) `x` '@; y; @' ``
  prints `received:` with exactly that text as a JSON string and is refused
  or read as literal text, with no `PWNED` file created; decoded locators
  holding a line feed, U+0085, or U+2028 each print a single escaped,
  ASCII-only `received:` line and produce no second `root:` or `source:` line;
  a missing `--locator-b64` and a repeated one each exit 2 with usage on
  stderr and empty stdout; and a read prints `root:` and `source:` as
  ASCII-only JSON strings.
- `.github/workflows/build-check-windows.yml` gains an explicit step running
  `packs/core/tests/skills/repository-grounding/test_read_locator.py`, beside
  the existing pack-owned portability step, so the Windows placement and
  reparse-point rules execute on a pull request. The suite's
  `SUITE_DISPOSITION` reason is updated in the same change to say that
  `make test` runs the whole suite and that this path-filtered Windows step
  also runs `test_read_locator.py` on a pull request.
- `test_projected_file_safety_matches_the_agentbundle_canonical` in
  `tests/roster/test_close_work_extraction_and_immediate_disposition.py` gains
  `repository-grounding` as a parameter, so the co-located
  `scripts/file_safety.py` is pinned byte-identical to
  `packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py`. A pack
  test checks the reader loads that co-located copy (AC-0005).
- Behavior evaluations in `repository-grounding/evals/evals.json`, each with a
  recorded run and evidence record in the verification ledger. `no stub
  (mode)`: behavior evaluation; agent choices have no in-process surface.
  - a paired provider-fit case and its no-provider twin; the provider-fit
    fixture exposes a depth cut that the run must keep (AC-0001, AC-0002);
  - poor-fit, refused, unavailable, timed-out, malformed, and incomplete
    provider cases (AC-0003);
  - a provider claim that contradicts repository source (AC-0004);
  - a provider that returns an outside-root locator, one that returns a
    symbol with no file location, and one whose locator is
    `` src.py'; $(touch PWNED) `x` '@; y; @' ``; the evidence record names the
    route that read, or declined to read, each locator, and the last case
    fails if a `PWNED` file exists in the workspace or the recorded
    `received:` text differs from that literal locator (AC-0005);
  - a configuration file hinting at an unexposed provider; the evidence record
    lists the surfaces considered (AC-0006);
  - two providers with different native shapes (AC-0007);
  - a request whose evidence record shows only the bounded question's content
    was sent; provider output carrying an `api_key:` field with the
    low-entropy placeholder `PLACEHOLDER_API_KEY_VALUE` and an endpoint under
    `internal.example.invalid`, which retained evidence omits (a local
    `gitleaks dir` run with `.gitleaks.toml` reports no leak for that shape);
    and a provider offering broad upload or persistence that the run declines
    (AC-0011);
  - a verified provider claim, and a claim whose check is unavailable
    (AC-0012);
  - provider output that embeds an instruction, proposes an approved root, and
    requests an index refresh; each case fails when the run complies
    (AC-0014).
- A construction test pins each evaluation case's id, fixture files, and
  assertions, and checks that every fixture file exists and every Python
  fixture parses.
- A goal-based absence scan of the shipped skill finds no instruction to probe
  hidden configuration, credentials, endpoints, pack directories, or arbitrary
  executables (AC-0006), and no normalized provider request, result,
  capability, provenance, freshness, or workflow-state representation
  (AC-0007). `no stub (mode)`: goal-based scan.

**Done when:** every reader test passes, every evaluation case has a recorded
passing run, and no provider result can widen scope or pass an acceptance
condition alone.

### T3: New-spec delegates grounding and Core documents the optional seam

**Depends on:** T1, T2

**Touches:** `packs/core/README.md`, `packs/core/tests/skills/new-spec/**`, `packs/core/tests/pack/**`

**Verification mode:** Goal-based integration and render checks.

**Tests:**
- Static tests prove `new-spec` delegates the existing inquiry but contains no
  provider identity, setup, invocation, freshness, or fallback branch
  (AC-0008). `no stub (mode)`: goal-based static check.
- `python -m agentbundle install . --pack core --adapter <surface> --scope repo
  --output <tmp>/<surface> --yes`, run into a fresh git repository for each of
  `claude-code`, `codex`, `copilot`, `kiro-ide`, `kiro-cli`, `cursor`, and
  `gemini`, yields `repository-grounding` (under `.claude/skills/`,
  `.agents/skills/`, or `.kiro/skills/`) in which every file of the skill
  tree, including `SKILL.md`, `references/**`, and `scripts/**`, is
  byte-identical to the source. The projected `explore-grounding.py`, run on a
  fixture repository with no provider present, exits 0 with its baseline
  report. The output is recorded in the verification ledger (AC-0010).
  `no stub (mode)`: goal-based install check.
- Documentation checks pin the optional, provider-neutral, native-shape story
  without naming the golden provider as a requirement (AC-0007, AC-0010).
  `no stub (mode)`: goal-based documentation check.

**Done when:** `new-spec`'s delegation from T1 passes the provider-ceremony
absence checks, the Core README describes the seam, and the install check
passes.

### T4: The complete grounding contract passes repository gates and closeout

**Depends on:** T1-T3

**Touches:** `docs/specs/optional-intelligence-grounding-composition/notes/**`, `docs/product/changelog.md`, `workspace.toml`

**Verification mode:** Goal-based repository gates; the verification ledger is
the task's evidence boundary.

**Tests:** `no stub (mode)` for every item: goal-based repository gates and
records.
- Targeted grounding, new-spec, pack, and parity suites pass
  (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007,
  AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014).
- The ledger maps every behavior-evaluation case to its recorded run and
  evidence record, including the request and retained-evidence records for
  AC-0011, the authoritative-check or unresolved result for AC-0012, and the
  declined directives for AC-0014.
- The free-standing Core entry is written in `docs/product/changelog.md`, and
  its Highlights disposition is decided by reading the complete release diff
  and its verification evidence. Release verification records the baseline
  versions, version-rule derivation, matching manifest target, that
  `.claude-plugin/marketplace.json` carries no Core entry,
  the entry, and that disposition (AC-0013).
- The governance-citation grep from `packs/AGENTS.local.md` returns no
  internal citation in shipped content.
- A `security-reviewer` pass covers the locator reader and the disclosure rule.
- Spec/plan status, traceability, link, and workspace checks pass.
- The local lint/type gate passes or its environment blocker is recorded.

**Done when:** the verification ledger maps every acceptance criterion named in
this task to green evidence, the workspace entry reflects the shipped state
when authorized, and closeout records the reusable-learning disposition.

## Rollout

This ships as a normal Core skill and a delegation at the existing `new-spec`
grounding step. No feature flag, infrastructure, service, credential, or
provider installation is needed. Reverting the delegation and restoring the
prior script path restores the earlier behavior; provider results create no
persistent state or migration.

## Risks

- An adopter's own automation may call `new-spec`'s old explorer path. The
  release entry names the new path so such a caller can be repointed.
- Prompt-level capability selection may become vague; heterogeneous behavior
  evals must fail examples that merely say "use available tools."
- The co-located confinement helper may drift from its source; the byte pin
  fails on any difference.
- The new owner may absorb workflow decisions; tests and review must keep it
  report-never-decide.

## Changelog

- 2026-10-04: spec approved by eugenelim as part of the CAP-0011 feature cohort.
- 2026-10-04: plan approved by eugenelim as part of the CAP-0011 feature cohort.
- 2026-10-04: spec and plan amended from sustained pre-EXECUTE review findings:
  locator reader and URI rules (AC-0005), adapter render check (AC-0010),
  per-case verification modes, suite registration, owner rationale, and the
  version class. Returned to Draft and Drafting for re-approval.
- 2026-10-04: second amendment from round-2 review: canonical locator order and
  root placement, refusal classification, symbol-locator guidance, per-surface
  install check (AC-0010), complete AC-0003 and AC-0011 coverage, new AC-0014
  (provider output stays data), outcome evidence records for action-limiting
  criteria per the owner's decision, and recorded stub validation.
- 2026-10-04: third amendment from round-3 review: helper byte pin moved to
  the roster suite, Makefile plan-digest re-pin, drive-letter placement, one
  suffix rule for URIs and paths, `no stub (mode)` records and the spec tally,
  changelog and Highlights moved to T4, registered stub loader, `Owned by:`
  lines, and whole-skill-tree projection identity.
- 2026-10-04: fourth amendment from round-4 review: standard-input transport
  for locators, T1 repoints the `new-spec` script entry, the encoded `#` case
  moved to its real bucket, a Windows runner step, and a scan-safe fixture
  token shape.
- 2026-10-05: fifth amendment from round-5 review: the owner chose base64 as
  the locator transport (`--locator-b64`), replacing standard-input
  here-documents; the reader echoes the decoded text as JSON; Windows root
  matching ignores case; T1 owns the whole `new-spec` delegation; the Windows
  step's disposition reason is kept true.
- 2026-10-05: sixth amendment from round-6 review: ASCII-only `received:`
  escaping, the `str.splitlines` line-break set with tests, the exit-2 output
  contract, projections in T2's Touches, and T3 no longer editing
  `new-spec/SKILL.md`.
- 2026-10-05: seventh amendment from round-7 review: the `line-break` refusal
  also runs on the decoded path, `root:` and `source:` share the ASCII-only
  JSON escaping, and a repeated `--locator-b64` is rejected and tested.
- 2026-10-05: amended spec approved by eugenelim after clean pre-EXECUTE
  adversarial and security reviews (round 8).
- 2026-10-05: amended plan approved by eugenelim.
- 2026-10-05: controlled amendment after T1-T3 completed, on the owner's ruling
  (ledger, "Owner ruling — AC-0013 marketplace clause"): the release criterion
  and its verification item no longer require a Claude marketplace entry,
  because Core is repository-only;
  T4's release check records that no Core entry exists. Completed tasks T1-T3
  are unchanged.
- 2026-10-05: amended spec approved by eugenelim after a clean amendment
  review.
- 2026-10-05: amended plan approved by eugenelim.
