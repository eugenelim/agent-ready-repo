# RFC-0074: Pack config and operation log

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-27
- **Date closed:** 2026-07-28
- **Decision weight:** standard — additive public API; `PackState` (the per-pack state record in `state.toml`) schema addition is costly to reverse; the `make_pack_dir` function crosses file-I/O and path-confinement security boundaries, which routes the `pack-config-api` spec to full mode with a `security-reviewer` pass
- **Related:** [RFC-0046 convenient-install-defaults](0046-convenient-install-defaults.md), [ADR-0036 install-source precedence chain](../adr/0036-install-source-resolves-through-trusted-precedence-chain-no-repo-source-no-cwd.md), [`docs/specs/agentbundle-config-subcommand/`](../specs/agentbundle-config-subcommand/) (existing adapter/source config — different key space, no overlap)

## Reviewer brief

- **Decision:** Add a per-pack user-config API and an operation log to agentbundle (the Python package that builds and installs AI agent packs) so pack scripts can read site-specific configuration baked in at catalogue build time and write structured operation entries.
- **Recommended outcome:** Accept.
- **Change if accepted:**
  - New Python API: `pack_dir()`, `load_pack_config()` added to `agentbundle/config.py`; new `agentbundle/oplog.py` with `write_entry()`.
  - `catalogue.toml` schema gains optional `[catalogue].user-dir` and top-level `[pack-defaults.<pack>]` sections; `_data/install-defaults.toml` gains corresponding baked values. `catalogue.schema.json` and `CatalogueConfig` / `AgentbundleDistribution` dataclasses updated in the same spec.
  - New CLI subcommand groups: `agentbundle pack-config {get,set,unset,show}` and `agentbundle oplog {show,clear}`.
- **Affected surface:** `packages/agentbundle` (Python package, public API), `catalogue.toml` schema (published interface), `packs/AGENTS.md` (pack authoring guidance), `guides/_shared/reference/pack-config-api.md` (new reference guide).
- **Stakes:** Costly to reverse — `PackState` gains a new optional field, and the new public Python API will accumulate hard dependencies from pack scripts.
- **Review focus:** (1) `user-root` per adapter row in v0.4 `[pack.<name>.adapters.<adapter>]` — is the per-install-write model correct? (2) Regular-file `O_APPEND` inode-lock atomicity and its NFS limitation.
- **Not in scope:** Secrets/credential storage (use `credbroker` — the agentbundle credential module), migration from `~/.agent-commander/`, pack-config UI, enterprise secrets management.

## The ask

**Recommendation (BLUF — Bottom Line Up Front):** Accept new per-pack config and oplog primitives — a three-source config cascade (pack-source defaults and catalogue operator overrides merged at build time into one baked layer; user overrides applied at runtime), a per-pack directory co-located with the user-scope `~/.agentbundle/state.toml`, and an atomic JSONL (JSON Lines — one JSON object per line) operation log — that enable catalogue operators to bake enterprise-specific defaults and give pack scripts a stable cross-catalogue API.

**Why now (SCQA — Situation→Complication→Question):**
Pack scripts (the shell or Python scripts shipped inside a pack — a deployable unit of AI agent skills, agents, and hooks for one domain, e.g. `atlassian`, `github`) increasingly embed site-specific configuration — Jira base URL, Linear workspace, GitHub org — that a catalogue operator (the person or team who builds and publishes a catalogue — a collection of packs from one source) already knows at build time. Currently the agent must prompt the user for each value on every run; there is no mechanism for a catalogue to bake defaults, no place for a pack script to persist user preferences, and no cross-catalogue operation log. As agentbundle matures into a multi-catalogue runtime, the gap between "build-time operator knowledge" and "runtime pack access" is the primary adoption friction for enterprise catalogues.

**Decisions requested:**

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Where should a pack's `user-root` (the base directory for its config and oplog) be stored? | New optional field `user-root` on every adapter row this install writes in user-scope `~/.agentbundle/state.toml` (v0.4, backward-compatible optional field) | Already locked by `persist_state_locked` (the function that does re-read→merge→write under an `O_CREAT\|O_EXCL` lock file); no additional lock file needed; survives pack reinstall | This review | Confirm or propose alternative |
| D2 | How should per-pack defaults flow from catalogue operator to pack script? | Three-source cascade baked into `_data/install-defaults.toml` at catalogue build time (extends RFC-0046) | Runtime-only cascade requires the catalogue source reachable on every run; baking is cheaper and the established pattern | This review | Confirm or propose alternative |
| D3 | How should oplog entries be appended atomically? | POSIX: single `os.write()` to `O_CREAT\|O_APPEND` fd (kernel inode lock, not PIPE_BUF — PIPE_BUF governs pipes, not regular files); Windows: `statelock.state_lock` | Inode lock (`i_rwsem`/vnode lock) makes concurrent single-write appends atomic on local POSIX filesystems; NFS limitation documented | This review | Confirm or rule on NFS mitigation |
| D4 | One spec or two? | Two specs: `catalogue-pack-defaults` (build-side) then `pack-config-api` (runtime API + CLI) | Different audiences (catalogue operators vs. pack script authors) and a hard dependency order warrant separate ACs and phased shipping | This review | Confirm or consolidate |

## Problem & goals

**Goals:**

1. A catalogue operator can bake organization-specific defaults into a pack install (base URLs, project keys, workspace IDs) without requiring users to re-enter them on every run.
2. Pack scripts have a stable, cross-catalogue Python API to read their config (`load_pack_config`) and resolve their directory (`pack_dir`).
3. Pack scripts can write structured operation entries to a per-pack JSONL log (`write_entry`) for audit and rollback tooling.
4. Catalogues with disjoint pack slugs (machine-readable pack identifiers, e.g. `atlassian`, `github`) coexist without conflict; same-slug/different-root across two catalogues raises `PackRootConflict`.
5. The system is fail-soft: missing config files return empty dicts; missing oplog is silently created on first write.

**Non-goals:**

- **Secrets or credentials.** Config values are plain TOML — use `credbroker` for tokens, passwords, and API keys.
- **Migration from legacy paths.** `~/.agent-commander/` is out of scope; catalogues that need migration can declare `user-dir` explicitly and add a one-time migration step.
- **Pack-config UI.** The CLI `pack-config` subcommands are machine-readable; a richer interactive UI is deferred.
- **Superseding `agentbundle config`.** `agentbundle config` manages adapter and source (user-level CLI settings); `agentbundle pack-config` manages pack-level key/value config. Different key space; no overlap.
- **Enterprise secrets management.** `install-defaults.toml` is not a secrets store.

## Proposal

### Directory layout

```
~/.agentbundle/               ← default pack root (co-located with user-scope state.toml)
├── state.toml                ← per-pack PackState rows; includes user-root
├── atlassian/                ← pack slug is the subdirectory name
│   ├── config.toml           ← user overrides; loaded by load_pack_config
│   └── ops.jsonl             ← operation log; appended by write_entry
├── github/
│   ├── config.toml
│   └── ops.jsonl
└── core/
    └── ops.jsonl

~/agentcommander/             ← custom root declared by another catalogue
└── agent-commander/
    ├── config.toml
    └── ops.jsonl
```

**Reserved slugs:** Pack slugs may not be any of the fixed reserved names — `bin`, `state`, `credentials`, `state.toml` — that conflict with existing paths under `~/.agentbundle/`. The `catalogue-pack-defaults` spec enumerates the complete reserved set; `pack_dir` enforces it at call time against this fixed list (not against filesystem state, so a pack's own directory does not exclude its own slug on reinstall).

A catalogue declares its preferred pack root in `catalogue.toml`:

```toml
[catalogue]
user-dir = "~/agentcommander"          # optional; default "~/.agentbundle"
minimum-agentbundle-version = "0.21.0" # must be ≥ the releasing version
```

### Root resolution (D1)

`~/.agentbundle/state.toml` (the user-scope state file, located by `user_state_path(home)`) uses schema v0.4, with one `[pack.<name>.adapters.<adapter>]` row per installed pack/adapter pair (ADR-0039 — an Architecture Decision Record, an immutable record of a one-way-door decision). `user-root` is a new optional field, added to every adapter row this install writes:

```toml
schema-version = "0.4"

[pack.atlassian.adapters.claude-code]
installed-version = "1.2.0"
install-route     = "catalogue+https://example.yourorg.com/…"
scope             = "user"
user-root         = "~/.agentbundle"   # written at install time from catalogue.user-dir

[pack.atlassian.adapters.kiro]
installed-version = "1.2.0"
install-route     = "catalogue+https://example.yourorg.com/…"
scope             = "user"
user-root         = "~/.agentbundle"
```

`user-root` is written to every adapter row this install writes (rows from other catalogues are untouched — divergence between pre-existing rows is what triggers `PackRootConflict`). The field is optional; absent rows read as `"~/.agentbundle"` — no schema-version bump required.

`pack_dir(pack_name)` resolution order:

1. `home=` kwarg (test override sets the home base for all path resolution in this call).
2. Read `state.rows_for_pack(pack_name)` from `user_state_path(home)`. Collect distinct `user-root` values across rows. If all rows agree, expand `~` relative to `home` and use that path. Raises `PackRootConflict` when rows disagree (signals two catalogues installed the same slug with different roots — the error names both conflicting paths and the adapter rows they came from).
3. `user_state_path(home).parent` — the `~/.agentbundle/` directory itself — as fallback when no rows exist for the pack slug.

`safety.make_pack_dir(base, pack_name)` — a new function in the existing `agentbundle.safety` module — creates `<base>/<pack_name>/` with mode `0o700`, validates `pack_name` against slug grammar `^[a-z0-9][a-z0-9-]*$` (rejecting traversal like `../evil`), rejects any resolved base outside the user's home directory, and guards against symlink traversal and TOCTOU (Time-Of-Check Time-Of-Use) race.

### Config cascade (D2)

Three sources; two layers at runtime. Pack-source defaults and catalogue operator overrides are merged at build time into one baked entry — at runtime `load_pack_config` merges that baked entry with the user's `config.toml`.

| Source | When merged | Set by |
| --- | --- | --- |
| Pack-source defaults (lowest precedence) | Build time | Pack author |
| Catalogue operator overrides | Build time (wins over pack-source) | Catalogue operator |
| → Baked into `_data/install-defaults.toml` `[pack-defaults.<pack>]` | Ships in agentbundle package | `compile_defaults` |
| User overrides (`<pack_dir>/config.toml`) | Runtime | User |
| **Effective config** | Runtime shallow merge: baked → user | `load_pack_config` |

`_data/` is the data directory inside the `agentbundle` Python package source tree (e.g. `packages/agentbundle/agentbundle/_data/`).

### Catalogue operator setup

The following walkthrough shows how a catalogue operator configures pack defaults end-to-end.

**Step 1 — Declare `user-dir` (optional).** In the catalogue's `catalogue.toml`, add `user-dir` to the `[catalogue]` section if packs should land outside `~/.agentbundle/`. The value must resolve under the user's `$HOME` — `compile_defaults` and `agentbundle install` both validate this; setting an absolute path like `/opt/shared` is rejected at build time so operators get an error before users ever see a failure:

```toml
[catalogue]
name         = "my-catalogue"
display-name = "My Catalogue"
user-dir     = "~/my-catalogue"   # must be under $HOME
minimum-agentbundle-version = "0.21.0"
```

Omit `user-dir` to keep the default `~/.agentbundle/`.

**Step 2 — Declare per-pack defaults.** Add top-level `[pack-defaults.<slug>]` sections for any pack whose scripts require pre-configured values:

```toml
[pack-defaults.atlassian]
url         = "https://jira.yourorg.com/"
project-key = "INFRA"

[pack-defaults.github]
org = "yourorg"

[pack-defaults.linear]
workspace = "your-workspace"
```

These sections are intentionally at the document root (not under `[distribution.agentbundle]`) so pack authors can read them without knowing the distribution config shape.

**Step 3 — Bake the defaults.** Run the catalogue build step that invokes `compile_defaults`. It reads `catalogue.toml`, merges pack-source defaults with the operator overrides above (operator wins), sorts pack names and keys alphabetically (required for the byte-stable drift check), and writes the result to the path declared in `distribution.agentbundle.install-defaults-output`:

```
$ agentbundle compile-defaults
Wrote packages/agentbundle/agentbundle/_data/install-defaults.toml (3 packs, 4 keys)
```

The message echoes the resolved output path from `distribution.agentbundle.install-defaults-output` and the count of operator-supplied keys (pack-source-default keys baked alongside them are not counted separately here).

**Step 4 — Verify.** Inspect the baked file to confirm the operator overrides landed correctly:

```toml
# _data/install-defaults.toml (operator-supplied section; pack-source defaults
# are merged into the same section but not shown in this excerpt)
[pack-defaults.atlassian]
project-key = "INFRA"
url         = "https://jira.yourorg.com/"

[pack-defaults.github]
org = "yourorg"

[pack-defaults.linear]
workspace = "your-workspace"
```

The `check_defaults` lint (`agentbundle lint-defaults`) re-runs `compile_defaults` and fails if the output diverges from the checked-in file — CI catches any drift.

**Step 5 — Users get the values automatically.** After a user runs `agentbundle install`, pack scripts call `load_pack_config("atlassian")` and receive the baked defaults merged with any personal overrides in `~/.agentbundle/atlassian/config.toml`. No per-user setup is required for the baked values.

Users can inspect their effective config at any time:

```
$ agentbundle pack-config show atlassian
url          = "https://jira.yourorg.com/"   (baked default)
project-key  = "INFRA"                       (baked default)
token        # not set — use credbroker for credentials
```

And override a value:

```
$ agentbundle pack-config set atlassian project-key MY-PROJ
```

### Python API additions

```python
# agentbundle/config.py (additions)

def pack_dir(pack_name: str, *, home: Path | None = None) -> Path:
    """Return (and create) the user-scope directory for this pack.
    pack_name must match ^[a-z0-9][a-z0-9-]*$ — raises ValueError otherwise.
    Raises PackRootConflict when adapter rows disagree on user-root.
    """

def load_pack_config(pack_name: str, *, path: Path | None = None,
                     home: Path | None = None) -> dict:
    """Merge baked install-defaults [pack-defaults.<pack>] with user config.toml.
    Returns {} when both are absent.
    On malformed config.toml: logs a warning to stderr, returns baked layer only.
    Never raises on missing file.
    """
```

```python
# agentbundle/oplog.py (new module)

def write_entry(pack_name: str, action: str, src: str,
                dst: str | None = None, *, extra: dict | None = None,
                home: Path | None = None) -> None:
    """Append a JSONL entry to <pack_dir>/ops.jsonl.
    Entry shape: {"action": ..., "src": ..., "dst": ..., ...extra, "ts": <ISO-8601>}
    ts is captured after the payload and emitted as the LAST key.
    dst is omitted when None.
    extra reserved keys (ts, action, src, dst, _truncated) raise ValueError before I/O.
    Base-field oversize raises EntryTooLargeError (entry exceeds _MAX_ENTRY bytes).
    Extra-field oversize truncates with "_truncated": true.
    When os.environ.get("AGENTBUNDLE_NFS_OPLOG") is set, emits a RuntimeWarning
    before each write (NFS O_APPEND is not atomic; set user-dir to a local path).
    """
```

Atomicity implementation:

```python
_POSIX = os.name == "posix"
# Practical cap on entry size.
# On POSIX regular files, O_APPEND writes acquire the inode lock (Linux i_rwsem,
# macOS vnode lock) before extending the file, making concurrent single-write
# appends atomic. This bound is not PIPE_BUF (which governs pipes, not files).
_MAX_ENTRY = 4096

def _append_line(path: Path, line: bytes) -> None:
    if len(line) > _MAX_ENTRY:
        raise EntryTooLargeError(len(line), _MAX_ENTRY)
    if _POSIX:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            n = os.write(fd, line)
            if n != len(line):
                # Partial write: n bytes already appended; line is corrupt.
                # Emit a warning so callers know the log may contain a
                # non-JSON fragment at end-of-file.
                import warnings
                warnings.warn(
                    f"oplog partial write ({n}/{len(line)} bytes) — "
                    "ops.jsonl may contain a non-JSON fragment",
                    RuntimeWarning, stacklevel=4,
                )
        finally:
            os.close(fd)
    else:
        from agentbundle.statelock import state_lock
        with state_lock(path):
            with open(path, "ab") as f:
                f.write(line)
```

### CLI surface

```
agentbundle pack-config get   <pack> <key>
agentbundle pack-config set   <pack> <key> <value>
agentbundle pack-config unset <pack> <key>
agentbundle pack-config show  <pack>          # effective config with source labels
```

`pack-config show` labels values as `baked default` (from `install-defaults.toml`) or `user override` (from `config.toml`).

```
agentbundle oplog show  <pack>                # tail -n 50 equivalent; --since=<ISO>
agentbundle oplog clear <pack> --yes          # --yes always required; clears ops.jsonl
```

`oplog clear` always requires `--yes` — clearing an audit log is destructive in all contexts (interactive or non-interactive).

### Pack-author reference

`guides/_shared/reference/pack-config-api.md` (the `guides/_shared/` convention is the cross-catalogue shared documentation directory, portable across catalogues that adopt the same `guides/` layout) ships as the canonical pack-author reference for `load_pack_config`, `write_entry`, `pack_dir`, and how to declare `[pack-defaults.*]` in `catalogue.toml`. It lives permanently at that path; it is not a projection, and other catalogues reference it there without a PyPI dependency.

## Options considered

### D1 — Where to store per-pack user-root

Axis: where the durable per-pack root binding lives (cross-reinstall, cross-catalogue, concurrent-safe).

| Option | What it is | Trade-off | If accepted |
| --- | --- | --- | --- |
| **Side index file** (`~/.agentbundle/catalogues.toml`) | A separate TOML file holding slug → root mappings | No locking story (deletable, no lock); a missing file causes silent mislocation; a second writer corrupts it | Not recommended — breaks concurrency guarantee |
| **Per-catalogue env var** | Env var per pack slug set by the user or shell profile | Doesn't survive shell restarts without profile edits; not portable | Not recommended — wrong layer for durable state |
| **`user-root` in `[pack.<name>.adapters.<adapter>]` rows** (recommended) | New optional field on every adapter row this install writes, written at install time | Reuses `persist_state_locked`'s existing lock; backward-compatible (optional, read-time defaulted) | Costs: `PackState` grows one field; `pack_dir()` aggregates across adapter rows |
| **Do nothing** (implicit fallback) | Keep implicit `~/.agentbundle/` for everything | Cannot support multi-catalogue roots | Blocks Goal 4 |

**Selected: `user-root` in `PackState` adapter rows.**

### D2 — Config cascade model

Axis: when and where operator defaults are resolved.

| Option | What it is | Trade-off | If accepted |
| --- | --- | --- | --- |
| **Runtime-only cascade** | Pack script fetches catalogue defaults at runtime | Requires catalogue source reachable on every run; adds latency | Not recommended |
| **Build-time baking into `_data/install-defaults.toml`** (recommended) | `compile_defaults` merges and ships in package | Offline-safe; extends RFC-0046 pipeline | Spec mandates sorted key emission for byte-stable drift check |
| **Per-catalogue runtime config file** | A `catalogue-defaults.toml` alongside the package | Two files to maintain; drift breaks abstraction | Not recommended |
| **Do nothing** | Only user `config.toml`; no operator layer | Operators cannot pre-configure enterprise URLs | Wrong for enterprise use |

**Selected: build-time baking.**

### D3 — Oplog append atomicity

Axis: how concurrent writers safely append to a shared JSONL file on a regular file (not a pipe).

| Option | What it is | Trade-off | If accepted |
| --- | --- | --- | --- |
| **`flock`-based locking** | Advisory file lock via `fcntl.flock` | POSIX only; advisory and ignored by non-cooperating processes; NFS still unsafe | Not recommended |
| **POSIX inode-lock via `O_APPEND`** (recommended) | Single `os.write()` to `O_CREAT\|O_APPEND` fd; kernel inode lock guarantees atomicity on local POSIX regular files | NFS documented limitation; Windows → statelock; 4096-byte practical cap | No advisory-lock leaks |
| **Write-then-rename** | Write to temp file, `os.rename()` atomically | Replaces whole file; cannot append without a read-merge step | Not suitable for append log |
| **`statelock.state_lock` always** | Existing Windows-compatible lock for all platforms | Works everywhere; opens a `.lock` companion file; more overhead on POSIX | Viable; more complex POSIX path |
| **Do nothing** | No atomicity guarantee | Concurrent writes corrupt entries | Not acceptable |

**Selected: POSIX inode-lock `O_APPEND`; Windows `state_lock` fallback.**

### D4 — Spec carving

Axis: how many specs (ship units) the implementation decomposes into.

| Option | What it is | Trade-off | If accepted |
| --- | --- | --- | --- |
| **One combined spec** | `docs/specs/pack-config-and-oplog/` covers everything | Single ship unit; RFC-0046 precedent | Mixes catalogue-operator and pack-author audiences; forces sequential shipping |
| **Two specs, dependency order** (recommended) | `catalogue-pack-defaults` first, then `pack-config-api` | Separate ACs per audience; phased shipping | Two tracking items |

**Selected: two specs.**

## Risks & what would make this wrong

**Pre-mortem:**

1. **`compile_defaults` emits non-deterministic key order.** `check_defaults`'s byte-exact comparison flaps. Mitigation: `catalogue-pack-defaults` spec mandates alphabetical sort of pack names and keys; AC includes running `compile_defaults` twice and asserting byte-exact equality.

2. **NFS oplog corruption.** Enterprise NFS home directories silently interleave JSONL entries. Mitigation: `write_entry` emits a `RuntimeWarning` when `AGENTBUNDLE_NFS_OPLOG` is set; documented in `pack-config-api.md`; users advised to set `user-dir` to a local path.

3. **PackRootConflict for shared slugs.** Two catalogues install the same slug (e.g. `core`) with different `user-dir`. Mitigation: the exception names both conflicting paths and the adapter rows they came from; `agentbundle install` warns at install time.

4. **Public API churn.** `load_pack_config` and `write_entry` signatures change after hard dependencies exist. Mitigation: signatures locked as of this RFC; breaking changes require a new RFC.

5. **Partial oplog write.** A short `os.write` leaves a corrupt non-JSON fragment at end-of-file. Mitigation: `_append_line` emits a `RuntimeWarning` naming the byte counts; `oplog show` trims to the last complete newline on read.

**Key assumptions (falsifiable):**

- *`persist_state_locked` is the right lock for `user-root` writes.* `load_pack_config` and `pack_dir` read `user-root` without holding the lock (read-only, written once at install time); `user-root` is written only during `agentbundle install`/`uninstall` which already holds the lock. Holds.
- *4096 bytes is sufficient for a JSONL entry.* Base fields are CLI-argument-bounded; extra-field oversize truncates with `_truncated: true`. Holds for realistic inputs.
- *Alphabetical sort makes `compile_defaults` output byte-stable.* `compile_defaults` builds output via f-string template (not a general TOML serializer); whitespace is deterministic. Holds.

**Drawbacks:**

- `PackState` gains `user-root` permanently.
- Pack authors must understand the two-layer merge; documented in `pack-config-api.md`.
- The 4096-byte entry-size cap is non-obvious; documented.

## Evidence & prior art

**Spike result:** `compile_defaults` uses f-string template emission — sort order is fully in our control. Alphabetical sort is a mechanical addition to the existing emitter. No showstopper.

**Repo precedent:**

- [RFC-0046](0046-convenient-install-defaults.md): established `_data/install-defaults.toml`, `compile_defaults`, and `check_defaults`. This RFC extends the pipeline with `[pack-defaults.*]`.
- [ADR-0036](../adr/0036-install-source-resolves-through-trusted-precedence-chain-no-repo-source-no-cwd.md): the install-source precedence chain this RFC parallels for per-pack config.
- [`docs/specs/agentbundle-config-subcommand/`](../specs/agentbundle-config-subcommand/): shipped spec for `agentbundle config set adapter|source`. No overlap.
- `agentbundle/safety.py` → `user_state_path(home)`: returns `~/.agentbundle/state.toml`; `pack_dir` uses `.parent` of this path as the default pack root. `make_pack_dir` reuses the same symlink + TOCTOU guard pattern established here.

**External prior art:**

Web search not available in this session. The design draws on two well-established patterns:
- Layered config cascade (Cargo's `~/.cargo/config.toml`; npm's `.npmrc` global → project → per-user): the three-source model is standard for package managers needing operator-level configuration.
- Atomic append to JSONL audit logs (`O_APPEND` inode lock): the POSIX single-write pattern is the consensus approach for concurrent append on local filesystems.

No citations fabricated; the above are pattern-level observations, not fetched links.

## Follow-on artifacts

- [ADR-0058](../adr/0058-per-pack-config-root-in-packstate-adapter-rows.md): Per-pack config root (`user-root`) in `PackState` adapter rows — **filed** 2026-07-28
- [ADR-0059](../adr/0059-pack-config-cascade-via-install-defaults-baking.md): Three-source pack config cascade via build-time `install-defaults.toml` baking — **filed** 2026-07-28
- Spec: `docs/specs/catalogue-pack-defaults/` — `catalogue.toml` extensions (`user-dir`, `[pack-defaults.*]`), `catalogue.schema.json` + dataclass updates, `PackState.user-root`, `compile_defaults` sort requirement; ships first; `security-reviewer` pass on path-confinement in `make_pack_dir`
- Spec: `docs/specs/pack-config-api/` — `pack_dir`, `load_pack_config`, `oplog`, CLI subcommands, `guides/_shared/reference/pack-config-api.md`, `packs/AGENTS.md` update; depends on `catalogue-pack-defaults` spec
