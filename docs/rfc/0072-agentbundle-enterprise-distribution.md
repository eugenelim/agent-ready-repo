# RFC-0072: AgentBundle Enterprise Distribution

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-23
- **Date closed:** 2026-07-23
- **Decision weight:** standard
- **Related:** [ADR-0036](../adr/0036-install-source-resolves-through-trusted-precedence-chain-no-repo-source-no-cwd.md) (the four-layer source chain this RFC extends), [ADR-0021](../adr/0021-pack-manifest-source-of-truth-and-scoped-identity.md) (pack identity model — `@catalogue/pack` declared, resolution deferred), [RFC-0046](0046-convenient-install-defaults.md) (convenient install defaults implementing spec), [RFC-0031](0031-catalogue-package-manager-posture.md) (package-manager posture: no server, no daemon, stdlib-only)

---

## Reviewer brief

- **Decision:** Accept six design decisions that extend agentbundle — the Python CLI tool that installs AI agent skill packs — to support enterprise distribution via internal Artifactory mirrors, machine-readable JSON output for CI, bulk upgrades, and source provenance tracking.
- **Recommended outcome:** Accept all six decisions.
- **Change if accepted:**
  - `PackState.source` hard-coded default is removed; source provenance is explicit on every write; same-name/different-source installs at one scope are refused before any mutation.
  - agentbundle gains a five-layer source precedence chain with a new org Artifactory bootstrap layer; `catalogue+https://` and `archive+https://` source schemes are added.
  - Three new CLI surfaces: `--format table|json` on `list-installed`/`upgrade`, `upgrade --all --scope repo|user`, `agentbundle package-catalogue`.
- **Affected surface:** `packages/agentbundle` (CLI, `PackState` schema, `source_defaults.py`, `install-defaults.toml`); `docs/guides/`.
- **Stakes:** Costly-to-reverse — `PackState` schema change and new source URL schemes enter the wire format; both are backward-compatible for existing state files.
- **Review focus:** (1) Source conflict semantics for legacy/unknown rows (D3). (2) Org bootstrap fail-closed behavior for a malformed `enabled = true` config (D2). These are the two places an incorrect decision leaves users stuck.
- **Not in scope:** full hosted registry, dependency solver, `pack@version` selectors, `upgrade --to/--latest`, multiple named user registries, background update daemon, cross-scope transactions, cross-pack rollback, Artifactory AQL-based discovery, silent source switching, new runtime dependencies.

---

## The ask

**Recommendation (BLUF):** Accept six design decisions that together make agentbundle viable for enterprise environments — cleaning up source provenance, adding an Artifactory channel resolver, enabling bulk upgrades with JSON output for CI, and shipping an org bootstrap mechanism and catalogue packaging command. The decisions are cohesive: source provenance is foundational; the rest build on it.

**Why now (SCQA):**
Agentbundle's source resolution chain (ADR-0036 — the four-layer precedence mechanism: explicit arg → user config → editable detection → packaged default) lets enterprise forks re-point the default catalogue source, but `PackState` — the dataclass that records each installed pack's state — hard-codes `source = "agent-ready-repo"` regardless of actual install origin. The historical literal is indistinguishable from a real provenance record, making source-based operations (conflict detection, upgrade routing, update status) unreliable. Enterprise environments also need Artifactory-hosted catalogue mirrors, JSON-output CI pipelines for automated upgrades, and an org bootstrap so developers get the right channel from install without manual configuration. None of these are currently possible. The question this RFC asks: how should we extend agentbundle's architecture to support enterprise distribution, and how should the four contested design decisions (channel pattern, bootstrap placement, source conflict, bulk atomicity) be resolved?

**Decisions requested:**

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
|----|----------|----------------|-----|-----------|-----------------|
| D1 | Should HTTPS catalogue distribution use a mutable channel descriptor pointing to an immutable versioned archive? | Yes — mutable channel JSON (`stable.json`) → immutable archive + SHA-256 | Universal ecosystem pattern (Homebrew, Debian, conda, Docker); SHA-256 on archive provides integrity; mutable pointer gives "follow the channel" semantics | This review | Confirm |
| D2 | Where should package-shipped org Artifactory bootstrap sit in the source precedence chain? | New layer 3 — between user config and editable detection | User explicit intent still wins; org bootstrap is a package-level permanent property more specific than a per-machine clone; fail-closed on malformed `enabled = true` | This review | Confirm |
| D3 | Should installing the same pack name at the same scope from a different source be refused before any mutation? | Yes — refuse by default; `--force` does not bypass | Without ADR-0021's `@catalogue/pack` resolution implemented, a mixed-source state file has no recovery path short of uninstall; the block is a conservative bridging mechanism | This review | Confirm |
| D4 | Should `upgrade --all` preflight all rows before any write, with disclosed non-atomicity on partial failure? | Yes — preflight then apply, stop on first failure, disclose outcome | Cargo-like plan/apply split; honest partial-failure semantics; preflight catches blocked rows before the filesystem is touched | This review | Confirm |
| D5 | Should three new CLI surfaces be ratified as described? | Yes — `--format table\|json`, `upgrade --all`, `agentbundle package-catalogue` | Standard patterns; additive; backward-compatible defaults | This review | Confirm |
| D6 | Should all CLI output (table and JSON) have explicit layout/usability checks? | Yes — snapshot tests, column alignment, truncation, terminal-width, JSON schema validation | Previous table output had formatting errors; layout checks catch regressions before they ship | This review | Confirm |

---

## Problem & goals

**Problems:**

1. `PackState.source` is always written as `"agent-ready-repo"` — a hard-coded literal that predates the install-defaults chain. It does not reflect actual install origin and cannot be used for conflict detection or upgrade routing. (`config.py:118`, `:395`; `install.py:1025`.)

2. The existing resolver (`source_defaults.py`) accepts only `git+https://` and local paths. Enterprise environments behind an Artifactory or other HTTPS artifact repository have no supported path.

3. `list-installed` produces only a human table with no machine-readable output, no "ahead" status, and no actionable reason codes for unknown update status. CI automation of upgrade decisions is not possible.

4. `upgrade` requires a single named pack. There is no way to upgrade all installed packs in a scope in one operation, and multiple adapter rows — a pack can be installed for several IDE targets simultaneously — for one pack do not independently track version state.

5. An org Artifactory fork has no structured way to ship a default channel URL. Every developer must run `config set source <url>` after install.

6. No tooling exists to package the catalogue repository into the Artifactory artifact layout (immutable release archive + mutable channel descriptor).

7. Previous CLI table output had formatting errors. There are no layout regression tests.

**Goals:**

- Every installed row records the actual catalogue source used.
- Machine-readable JSON output for `list-installed` and `upgrade` operations.
- Scoped bulk upgrade with explicit plan, honest partial-failure reporting, and a stable JSON contract.
- `catalogue+https://` and `archive+https://` source schemes, vendor-neutral (Artifactory, Nexus, S3, or any static HTTPS server).
- Out-of-the-box org bootstrap for developers installing from an org fork; no manual `config set source`.
- `agentbundle package-catalogue` CI command producing a deterministic, uploadable Artifactory layout.
- Correct, well-formatted CLI output at common terminal widths with regression protection.

**Non-goals** (deliberately out of scope — these could reasonably have been included):

- Full hosted registry, server, or daemon (RFC-0031 Principle 3: stdlib-only, habit not infrastructure).
- Registry search or publication APIs.
- Dependency solver.
- `pack@version` selectors; `upgrade --to`; `upgrade --latest`.
- Multiple named user registries.
- Background update daemon.
- Cross-scope transactions.
- Cross-pack rollback engine.
- Artifactory AQL-based "latest" discovery or timestamp sorting.
- Silent source switching or silent downgrades.
- Pack-version removal or monorepo-wide package versioning.
- A new runtime dependency — Python 3.11 stdlib-only constraint is preserved throughout.
- Artifactory upload credentials in agentbundle itself (packaging and publishing are separate responsibilities).

---

## Proposal

### D1 — HTTPS catalogue channel descriptor

Two new source URL schemes:

**`catalogue+https://<url>`** — points to a small, mutable JSON channel descriptor. The descriptor is the authoritative meaning of "current" or "stable" for a named channel; agentbundle fetches it, resolves the immutable archive it points at, verifies the SHA-256, then extracts and uses the archive. The descriptor may be replaced by CI on each release; the archive it points at is immutable once published.

Channel descriptor schema v1:

```json
{
  "schema": 1,
  "kind": "agentbundle-catalogue",
  "bundle": "<string>",
  "channel": "<string>",
  "release": "<string>",
  "artifact": "<relative-or-absolute-https-url>",
  "sha256": "<64 lowercase hex characters>",
  "published_at": "<ISO-8601, optional>",
  "source_revision": "<string, optional>",
  "minimum_agentbundle_version": "<semver string, optional>"
}
```

Required: `schema`, `kind`, `bundle`, `channel`, `release`, `artifact`, `sha256`. Optional fields absent from the descriptor do not cause failure. `schema` must equal `1`; `kind` must equal `"agentbundle-catalogue"`.

The `artifact` URL may be:
- a relative URL, resolved against the descriptor URL; or
- an absolute HTTPS URL on the same origin.

Cross-origin artifacts are refused. HTTP (non-TLS) artifacts are refused. URL user-info in either the channel URL or the artifact URL is refused.

`minimum_agentbundle_version`, when present, is checked against the running agentbundle version before the archive is downloaded; an older client fails with a clear version error.

**`archive+https://<url>#sha256=<digest>`** — a direct archive URI with a required integrity fragment. No channel descriptor; no "follow the channel" semantics. Suitable for reproducible pinned installs.

**Logical source identity:** The installed source is the channel URI (`catalogue+https://…/channels/stable.json`), not the resolved archive path. This is consistent with ADR-0036 D4 (stateless resolution): the channel is the stable identity; the versioned archive is the resolved artifact at a point in time. Persisting the temporary extraction path as the source would be incorrect.

**Integrity and safety:** SHA-256 is computed during streaming download and verified before extraction. Digest mismatch fails before any install or upgrade mutation with a clear error naming expected and received digests. Named safety limits (easy-to-adjust constants):

| Limit | Value |
|-------|-------|
| Channel descriptor | 1 MiB |
| Compressed archive | 256 MiB |
| Archive members | 20,000 |
| Total expanded bytes | 1 GiB |
| HTTP timeout | documented finite value |

Compressed-archive limit is enforced even when `Content-Length` is absent or dishonest. Path traversal, absolute paths, symlinks, hard links, device files, and FIFOs are rejected during extraction. HTTPS redirects: same-host only; bearer token is never forwarded to a different host. Temporary directory is cleaned up on failure.

**Bearer token authentication:** supplied via `AGENTBUNDLE_HTTP_BEARER_TOKEN`. Sent as `Authorization: Bearer <token>`. Never persisted in state, never printed, never included in exception repr output, always redacted in error messages. TLS trust uses the standard OS/Python CA configuration (`SSL_CERT_FILE`); there is no certificate-disable option. Corporate proxy environments: `HTTPS_PROXY` and `NO_PROXY` are honored via the standard `urllib` proxy handler; a custom opener built for bearer-token injection and redirect control must explicitly preserve proxy support (the implementing spec must assert this).

**Integrity trust boundary:** SHA-256 covers archive integrity relative to the channel descriptor — it proves the downloaded archive is the one the descriptor named and was not tampered with in transit. Channel descriptor authenticity rests on HTTPS transport and trusting the mirror; the descriptor itself is not independently signed. This is the standard Homebrew/conda channel model and is appropriate for a trusted internal Artifactory, but the implementing spec must document the boundary.

**Scheme validation:** `_is_valid_source` (`source_defaults.py:76–98`) is extended with two new branches before the existing scheme gate: `catalogue+https://` and `archive+https://`. All other schemes remain rejected. Local paths and `git+https://` are unaffected.

### D2 — Five-layer source precedence chain

The existing four-layer chain (ADR-0036) gains a new layer 3:

```
Layer 1: Explicit --catalogue argument (pass-through, unvalidated — unchanged)
Layer 2: User [settings].source (validated — unchanged)
Layer 3: Package-shipped organization Artifactory bootstrap  ← NEW
Layer 4: Editable-install detection via PEP 610 (unchanged)
Layer 5: Packaged [defaults].source in install-defaults.toml (unchanged)
```

Layer 3 is sourced from `agentbundle/_data/install-defaults.toml`, which is extended to support an optional `[organization.artifactory]` block:

```toml
# Public default — org block is disabled.
[organization.artifactory]
enabled = false

[defaults]
source = "git+https://github.com/eugenelim/agent-ready-repo"
```

An org fork sets `enabled = true` and fills in the required fields:

```toml
# Example corporate fork — all values use example.test placeholders.
[organization]
name = "Acme Engineering"        # display only

[organization.artifactory]
enabled = true
base-url = "https://artifactory.example.test/artifactory"
repository = "agentbundle-generic-local"
bundle = "engineering"
channel = "stable"

[defaults]
source = ""  # blank — org bootstrap fires at layer 3
```

When `enabled = true`, agentbundle constructs:
`catalogue+<base-url>/<repository>/catalogues/<bundle>/channels/<channel>.json`

For the example above:
`catalogue+https://artifactory.example.test/artifactory/agentbundle-generic-local/catalogues/engineering/channels/stable.json`

**Validation (applied only when `enabled = true`):**
- `base-url` must use HTTPS with no user-info, query parameters, or fragments.
- `repository`, `bundle`, and `channel` must match `[A-Za-z0-9._-]+`.
- Path separators, `..`, and percent-encoded traversal are rejected.
- A trailing slash on `base-url` is normalized.
- A malformed `enabled = true` config **fails closed** — it does not fall through to layer 4, **and it is only evaluated when layers 1 and 2 are both empty** (i.e., no explicit `--catalogue` arg and no valid `[settings].source` in user config). An explicit layer-1 arg or a valid layer-2 user config source is resolved before layer 3 is reached, so a malformed org block does not affect those installs. The error message names the malformed field and the config file path.

The public default ships `enabled = false`; no real org endpoints or credentials are committed to the public repository. Tests and documentation use `example.test` placeholders only.

**Placement rationale vs. ADR-0036:**
- Layer 2 (user config) outranks layer 3: explicit `config set source` overrides org bootstrap. ADR-0036 D1 ("user config deliberately outranks auto-detection") is preserved.
- Layer 3 outranks layer 4 (editable detection): org bootstrap is a permanent property of the installed package, not a per-machine or per-session preference. A developer who installed from a wheel (no editable record) still receives the org channel. A developer who installed from an editable clone of the org fork receives the org channel via layer 3 rather than layer 4 — same result, earlier in the chain.
- Fail-closed at layer 3: ADR-0036 D5 allows an absent/blank layer-5 packaged default to fall through silently (the private-fork pattern). For an explicitly-enabled org config (`enabled = true`), falling through silently is incorrect — the organization intentionally directed installs to a specific Artifactory endpoint, and a malformed value subverts that intent. An explicit error is the right behavior.

### D3 — Source conflict install guard

Before any install write occurs, the handler scans all installed `(pack, adapter)` rows — a pack can be installed for multiple IDE adapters simultaneously — at the target scope for the same pack name.

**Rules:**

| Condition | Result |
|-----------|--------|
| Same pack, same scope, same canonical source, different adapters | Allowed |
| Same pack, same scope, different canonical sources | **Refused** |
| Same pack, same scope; existing row has legacy/unknown source | **Refused** — cannot prove equal |
| Same pack in repo scope vs. user scope from different sources | Not blocked (status may warn) |
| `--force` flag present, source mismatch exists | **Refused** — `--force` does not bypass |

The check fires before any projection write, hook, state write, or other mutation.

**Legacy/unknown source:** both `None` in state and the historical hard-coded literal `"agent-ready-repo"` are treated as unknown provenance. The historical literal was written by prior code for installs from any source, including non-public-repo sources; it does not prove origin. A row with legacy/unknown source cannot be proven equal to any incoming canonical source, so a second adapter install for that pack is refused until the row is migrated through an explicit upgrade or uninstalled.

**Migration path:** a successful upgrade from a deliberately selected source may migrate a legacy row by writing the real canonical source at that point. Merely reading state does not migrate it.

**Canonicalization:** a single `canonicalize_source(value: str) -> str | None` function is used by install, upgrade, status, and conflict checks. Rules:
- Local paths: resolve to absolute normalized path; resolve `.` and `..`; no transient extraction directories.
- Remote sources: retain the logical update source (channel URI); normalize scheme and hostname case; normalize trailing slashes where semantically safe; reject URLs containing user-info credentials; never persist `Authorization` headers or bearer tokens; redact query-string secrets in errors and logs.

### D4 — Bulk upgrade (`upgrade --all`)

**CLI shape:** exactly one of `--pack <name>` or `--all` is required. `--scope repo|user` is required with `--all`. `--adapter` is rejected with `--all`. Repo and user scope are separate operations.

**Preflight phase** — runs before any write:

1. Load all selected state rows.
2. Resolve every required source (each distinct source resolved once per invocation).
3. Locate every selected pack in its resolved source.
4. Parse and compare every installed and source version.
5. Verify manifests and contract compatibility.
6. Verify the installed adapter is still supported by the pack.
7. Render every candidate projection.
8. Run all path-jail and ownership safety classification.
9. Classify all rows.

**Row classification:**

| Status | Meaning | Apply action |
|--------|---------|--------------|
| `upgrade-available` | Installed version < source version | Candidate for mutation |
| `up-to-date` | Installed version = source version | Skip |
| `ahead` | Installed version > source version | Skip; state no downgrade explicitly |
| `unknown` / blocked | Cannot safely compare; source error; manifest error; unsupported adapter | **Block all writes** |

A blocked row blocks the entire mutating operation before the first write. A dry run containing blocked rows shows the complete blocked plan and returns a non-zero exit code. There is no skip-errors option in this first implementation.

**Apply phase** (after confirmed plan):
- Deterministic order: canonical source → pack name → adapter name.
- Stop on the first apply failure.
- Completed rows retain their applied state. The failing row is marked `failed`. Remaining candidates are marked `not-attempted`.
- Partial completion is disclosed honestly. The operation is never described as rolled back.

**Confirmation:** one combined plan is shown; one confirmation prompt covers the whole operation. `--format json` without an interactive terminal requires `--yes` (no silent mutation on a JSON pipe).

**Co-owned adapter paths:** files shared between adapter rows (a pack installed for multiple IDEs may project the same skill file) use the existing co-ownership and hash-safety behavior. A file is not classified as unmanaged because a different adapter row also owns it. State updates remain row-specific.

### D5 — CLI surface additions

**`--format table|json`** on `list-installed` and `upgrade`. Table is the default (backward-compatible). In JSON mode: exactly one valid JSON document to stdout; all progress, warnings, and diagnostics go to stderr; no human prose or table mixed into JSON stdout. Credential-redacted source strings in both formats. Deterministic output ordering.

`list-installed` JSON contract (schema version 1):

```json
{
  "schema_version": 1,
  "command": "list-installed",
  "scope": "repo",
  "updates_only": false,
  "sources": [
    { "source": "catalogue+https://…", "resolved": true, "error_code": null, "error_message": null }
  ],
  "rows": [
    {
      "pack": "core",
      "adapter": "claude-code",
      "scope": "repo",
      "source": "catalogue+https://…",
      "installed_version": "0.13.6",
      "available_version": "0.13.7",
      "status": "upgrade-available",
      "status_reason": null,
      "drift_count": null
    }
  ],
  "summary": { "total": 1, "up_to_date": 0, "upgrade_available": 1, "ahead": 0, "unknown": 0 }
}
```

`upgrade --all` JSON contract (schema version 1, `"command": "upgrade"`, `"mode": "all"`). Row `outcome` values: `planned`, `completed`, `skipped`, `blocked`, `failed`, `not-attempted`. Update status (`upgrade-available`, `ahead`, etc.) and execution outcome are separate concepts carried on separate fields.

**`upgrade --all --scope repo|user`:** mutually exclusive with `--pack`. No `--scope all`. No dual-scope inference.

**`agentbundle package-catalogue`:** maintainer/CI command only; does not install anything.

Required arguments: `--root`, `--bundle`, `--release`, `--channel`, `--output`.  
Optional: `--source-revision`, `--minimum-agentbundle-version`, `--published-at`, `SOURCE_DATE_EPOCH`.

No git shell-out; CI supplies the commit via `--source-revision`.

Output layout:
```
dist/artifactory/
  catalogues/
    <bundle>/
      releases/
        <release>/
          catalogue-<release>.tar.gz
          catalogue-<release>.tar.gz.sha256
      channels/
        <channel>.json
```

Archive content: `packs/`, `profiles/`, `docs/contracts/`, `README.md`, `LICENSE`, `catalogue-manifest.json`. Explicitly excluded: `.git/`, `.github/`, build output, `dist/`, test results, local state, credentials, environment files, arbitrary untracked files.

Archive is deterministic: sorted paths, normalized uid/gid/timestamps/modes, reproducible gzip, digest generated after final bytes. `SOURCE_DATE_EPOCH` honored. Identical inputs produce byte-identical archives.

`catalogue-manifest.json` inside the archive carries: `schema`, `bundle`, `release`, `source_revision`, `generated_at`, included file paths with SHA-256 digests, pack names and versions.

The command refuses to overwrite an existing release archive; no `--force-overwrite` in this first implementation.

### D6 — CLI output layout/usability checks

Previous `list-installed` table output had formatting errors. All new and existing table-producing commands must satisfy:

1. **Snapshot/golden-file tests** for each table-producing command (`list-installed`, `upgrade --dry-run` plan output). Golden files are stored in the test suite. A CI diff flags regressions.

2. **Column alignment:** tests assert consistent column separator positions when given mixed-length input (short names, long names, Unicode identifiers). ANSI escape codes, if ever used, must not be counted in column-width accounting.

3. **Truncation/wrapping:** long version strings, long source URIs, and long pack names must be truncated gracefully rather than breaking table structure. Tests cover values wider than a column's maximum display width.

4. **Terminal widths:** layout is verified at 80 and 120 columns.

5. **JSON schema validation:** all JSON-output tests assert `json.loads(stdout)` succeeds; the `schema_version` field is present and has the expected value.

The existing `list-installed` table output is reviewed against these requirements in the implementing spec; formatting errors are corrected before new status columns are added. The golden file is recorded from corrected output, not from the erroneous baseline.

---

## Options considered

### D1 — How to express "current version of this channel"

| Option | Verdict | Key trade-off |
|--------|---------|---------------|
| Do-nothing (git+https only) | Rejected | Blocks enterprise environments without direct GitHub access |
| Direct archive URIs only (`archive+https#sha256`) | Rejected as primary | No "follow the channel" semantics; every release requires updating org bootstrap config |
| **Mutable channel descriptor → immutable archive** | **Accepted** | Universal pattern; SHA-256 integrity on the archive; CI replaces only the channel JSON |
| Content-addressed channel (no mutable pointer) | Rejected | Cannot discover the current release without already knowing its digest |
| Mutable tag, no integrity guarantee | Rejected | No integrity; no serious ecosystem uses this |

### D2 — Org bootstrap placement in the precedence chain

| Option | Verdict | Key trade-off |
|--------|---------|---------------|
| Do-nothing | Rejected | Every developer must manually `config set source` |
| Above user config (layer 1.5) | Rejected | Overrides explicit user intent; contradicts ADR-0036 D1 |
| **New layer 3 (between user config and editable detection)** | **Accepted** | User intent wins; org bootstrap is a package-level permanent property; fail-closed |
| Below editable detection (layer 4.5) | Rejected | Editable clone silently beats org bootstrap for wheel-installed developers |
| Replace packaged default | Rejected | Loses fail-closed semantics for malformed `enabled = true` config |

### D3 — Same-name/different-source install at same scope

| Option | Verdict | Key trade-off |
|--------|---------|---------------|
| **Allow silently (do-nothing / status quo)** | Rejected | Unresolvable `PackState` ambiguity; upgrade routing undefined; cost of delay: inconsistent state accumulates silently |
| Warn only | Rejected | Warning is forgotten; inconsistent state is permanent |
| **Refuse by default; `--force` no bypass** | **Accepted** | Bridging mechanism until ADR-0021 resolution lands; state stays unambiguous |
| Namespace by source (`@catalogue/pack`, ADR-0021 D7) | Deferred | Long-term direction; resolution not yet implemented |
| Auto-switch source | Rejected | Silent supply-chain risk |

### D4 — Bulk upgrade plan/apply split and failure semantics

| Option | Verdict | Key trade-off |
|--------|---------|---------------|
| Do-nothing | Rejected | CI bulk upgrade is impossible |
| Greedy apply, no preflight | Rejected | No plan visibility; unpredictable failure mode |
| **Preflight + stop-on-first-fail + disclosed non-atomicity** | **Accepted** | Cargo-like plan/apply split; honest partial-failure semantics |
| Preflight + rollback on failure | Rejected | Infeasible for co-owned adapter paths; claiming rollback is worse than disclosing non-atomicity |
| Fully atomic | Rejected | Requires a filesystem transaction log agentbundle does not have |

### D5 — CLI surfaces (no contested decisions; ratified as described)

### D6 — CLI output layout checks (no contested decisions; ratified as described)

---

## Risks & what would make this wrong

**Pre-mortem — top failure modes:**

1. *Legacy rows block all second-adapter installs.* If many repos have existing rows with no recorded source (the hard-coded `"agent-ready-repo"` or `None`), the D3 conflict guard makes adding a second adapter for any installed pack impossible until the user either runs an explicit upgrade (which migrates the source) or uninstalls and reinstalls. Mitigation: the error message names the recovery step; the upgrade migration path is documented; the implementing spec must cover this in its acceptance criteria.

2. *Malformed org bootstrap fails cryptically at every install.* A fork shipping a bad `[organization.artifactory]` block causes every install to fail. Mitigation: the error message names the malformed field and the config file path; the public default ships `enabled = false`; the private-fork pattern (blank `source`, rely on editable detection) is the fallback explicitly documented.

3. *Bulk upgrade partial failure leaves the repo in an inconsistent state.* Rows 1–2 of 5 upgraded, row 3 fails. Mitigation: the partial-completion summary names completed/failed/not-attempted; the PR annotation guidance shows how CI surfaces this; re-running `upgrade --all` is safe (already-upgraded rows are `up-to-date`).

4. *SHA-256 streaming download saturates disk.* Mitigation: the 256 MiB compressed-archive limit is enforced even when `Content-Length` is absent; download streams to a temp file, not in-memory; temp file is deleted on any failure.

5. *D6 golden files are recorded from erroneous output.* If the snapshot is taken before the formatting errors are corrected, the test is a regression fence for broken behavior, not a correctness guarantee. Mitigation: the D6 implementing spec must review existing table output and correct errors before recording the golden file; the golden file review is an explicit acceptance criterion.

**Key assumptions (falsifiable):**

- `_is_valid_source` (`source_defaults.py:76–98`) can be extended to accept `catalogue+https://` and `archive+https://` without touching the rest of the resolution chain. *Confirmed via code inspection: the scheme gate at lines 95–96 is the single targeted extension point — a new `startswith` branch before `if urlsplit(value).scheme: return False`. Non-blocking.*

- The `catalogue+https://` resolver can be implemented with stdlib `urllib` + `tarfile` with no new runtime dependency. *Consistent with RFC-0031 Principle 3; the existing `catalogue.py` git+https fetcher uses only stdlib. The HTTPS extension is additive.*

- Backward-compatible reading of legacy rows (`source=None` or `source="agent-ready-repo"`) does not require a state schema version bump. *No bump needed: the field becomes `str | None = None`; existing state files parse cleanly by falling back to `None` on a missing key.*

**Drawbacks:**

- Five-layer source chain is more precedence to reason about than four. Mitigated by a documented precedence table; most users still hit exactly one layer.
- The source conflict block (D3) may surprise users who currently have multi-source installs. Mitigated by the error message naming the recovery step.
- Disclosed non-atomicity (D4) means a partially-applied bulk upgrade requires re-running the command. Mitigated by honest outcome reporting and idempotent re-runs.
- `catalogue+https://` and `archive+https://` are new wire-format strings that permanently extend `PackState` and user config. Changing them later is costly. Mitigated by the explicit scheme prefix making them unambiguous and extensible.

---

## Evidence & prior art

**Spike / de-risk result:**

`_is_valid_source` (`source_defaults.py:76–98`) currently rejects any non-`git+https://` URL via the `urlsplit` scheme gate. `urlsplit("catalogue+https://...")` returns scheme `"catalogue+https"` — non-empty → rejected at line 96 (`return False`). The fix is a targeted new branch before this gate. No function rewrite required; layers 1–2 and 4–5 are unaffected. **Confirmed non-blocking.**

**Repo precedent:**

- **ADR-0036** — The four-layer trusted-by-construction source chain; packaged data file as the fork re-pointing mechanism (D5); no repo-scoped source (D3, code-provenance boundary reasoning); user config deliberately outranks editable detection (D1). This RFC extends the chain to five layers and is consistent with all five sub-decisions.
- **ADR-0021** — `@catalogue/pack` identity declared (D7); multi-catalogue resolution explicitly deferred. D3 of this RFC (source conflict block) is a bridging mechanism explicitly compatible with ADR-0021's eventual resolution; it does not pre-empt it.
- **RFC-0031** — Package-manager posture: no server, no index, no daemon; Principle 3 (stdlib-only, no new runtime dependency). All six decisions in this RFC respect this constraint.
- **RFC-0046** — The implementing spec for ADR-0036 (`convenient-install-defaults`). `source_defaults.py` is the targeted extension point for D1 and D2.

**External prior art (verified citations only):**

- [Homebrew Bottles](https://docs.brew.sh/Bottles) — **PASS**: *"Contains the SHA-256 hash of the bottle for the given OS/architecture."* Mutable formula → immutable bottle + SHA-256; checksum mismatch causes fallback to source build. Prior art for D1.
- [Cargo Source Replacement](https://doc.rust-lang.org/cargo/reference/source-replacement.html) — **PASS**: *"Cargo has a core assumption about source replacement that the source code is exactly the same from both sources."* One authoritative source per crate in a scope; mixing different sources for the same crate name is not supported. Prior art for D3.
- [Cargo Book — cargo-update](https://doc.rust-lang.org/cargo/commands/cargo-update.html) — **CONSISTENT**: `cargo update` only writes `Cargo.lock`, performing no downloads or builds (separate `cargo build` step). The plan/apply split is the closest prior art for D4's preflight model.
- [npm — .npmrc](https://docs.npmjs.com/cli/v11/configuring-npm/npmrc/) — **DIRECTIONALLY CONFIRMED**: registry binding in `.npmrc` is supported; the `@scope:registry` key form is documented. Directional prior art for D2's package-shipped config concept. Spot-check the exact key syntax before citing as a primary reference.

Debian SecureApt, conda sharded repodata CEP, and Docker image digests were cited by the research agent but not independently fetch-verified; they are treated as corroborating pattern evidence for D1, not as primary citations. Full research synthesis: [`0072-notes/research-synthesis.md`](0072-notes/research-synthesis.md).

---

## Open questions

1. **Should `list-installed` show a source identity column in the default table output?**
   Recommended default: Show a truncated source column only when multiple distinct sources are present; omit it when all rows share one source. Reduces noise in the common single-source case. Owner: eugenelim. Decide-by: `spec/list-installed-update-status`.

2. **Should `agentbundle package-catalogue` validate pack evals before packaging?**
   Recommended default: No — packaging is a structural/integrity operation; eval results are a separate quality gate that CI should run independently. Coupling the packaging command to an LLM judge would make it non-deterministic. Owner: eugenelim. Decide-by: `spec/package-catalogue-command`.

---

## Follow-on artifacts

To be filled in when accepted:

- ADR-NNNN: Source identity as pack ownership at a scope (D3 decision record)
- ADR-NNNN: Mutable channel descriptor → immutable archive pattern for HTTPS catalogues (D1 decision record)
- ADR-NNNN: Package-shipped organization Artifactory bootstrap configuration (D2 decision record)
- ADR-NNNN: Bulk upgrade — preflighted but not transactionally atomic (D4 decision record)
- Specs: `spec/packstate-source-provenance`, `spec/source-conflict-install-guard`, `spec/list-installed-update-status`, `spec/upgrade-bulk-all`, `spec/https-catalogue-channels`, `spec/organization-artifactory-bootstrap`, `spec/package-catalogue-command`, `spec/artifactory-publishing-workflow`, `spec/corporate-update-documentation`, `spec/agentbundle-enterprise-distribution-release` (per `workspace.toml` `["ini-004".work].queue`)
