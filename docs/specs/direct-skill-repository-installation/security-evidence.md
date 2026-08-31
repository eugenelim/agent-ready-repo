# Security-checklist evidence — direct skill repository installation

Records the resolved findings for AC29's five required modules against the code
this spec added. Each row states what was checked, what was found, and where the
control lives. A finding is *resolved* when a control exists and a test fails
without it; anything else is recorded as an accepted residual with its reason.

Modules applied: `path-and-file`, `outbound-ssrf`, `supply-chain`,
`exceptional-conditions`, `agentic-skills`.

---

## Path/file

| Check | Disposition | Control |
|---|---|---|
| Traversal via archive member name | Resolved | `_member_is_safe` rejects absolute, `..`, empty, and backslash-bearing names, tested against four escape shapes. The check runs on the **library-resolved** `TarInfo.name`, never a reconstructed one. |
| Traversal via link target | Resolved | An admitted `linkname` is independently required to be relative and in-root before the member is refused as a link at all, so the offending value is named. |
| Symlink, hard link, device, FIFO members | Resolved | Refused on the direct route (`CAT-D007`). The catalogue route deliberately keeps symlinks, which is why the rule is not in shared extraction code. |
| Case-fold collision on extraction | Resolved | Refused; two members that differ only by case collapse to one file on macOS and Windows. |
| Confinement of every join | Resolved | AC39's five mechanisms, enforced statically by `test_direct_architecture_controls.py`, which fails on `commonpath`, `commonprefix`, `normpath`, a `..`-stripping comprehension, and a `Path`-typed `startswith` prefix check. |
| Caller-side canonicalisation defeating the rule | Resolved | `realpath` and `abspath` are banned by name alongside `resolve`; a ban written only against `resolve` passes both. |
| Marker probe reading link-like paths | Resolved | `probe_measured_path` is the sole `lstat` carve-out and returns a refusal decision, never a `stat_result`; a test asserts the carve-out is exactly one function in exactly one module. |
| Writes escaping the target tree | Resolved | Normalization writes through `safety.write_jailed` with an explicit `allowed_prefixes`. |
| Source mode carried into a projection | Resolved | `_canonical_mode` reduces every file to 0o755 or 0o644, so setuid, setgid, and group/world-write cannot be installed. |

**Residual.** A directly installed skill's *content* is unreviewed. Admission
bounds what a source can do to the install, not what its instructions ask an
agent to do afterwards. Recorded in `docs/architecture/security.md`.

---

## Outbound acquisition

| Check | Disposition | Control |
|---|---|---|
| Arbitrary host fetch (SSRF) | Resolved | Source grammar admits `git+https://github.com/<owner>/<repo>@<ref>` only; the built URL is re-parsed and re-validated before use. |
| Redirect to an unrelated host | Resolved | `_BoundedRedirectHandler` permits at most five redirects, HTTPS only, and only to `github.com` or `codeload.github.com` for the *same* owner, repository, and ref. Exercised live: GitHub's real `github.com → codeload.github.com` redirect is admitted, and the four rejection shapes refuse. |
| Redirect comparison bypass via encoding | Resolved | Targets are compared in the same percent-encoded form as the request; comparing a decoded target against an encoded expectation would admit anything that merely decodes to the right place. |
| Credentials leaking into a URL | Resolved | User-info in a redirect target is refused; the route is credential-free by construction and never attaches a token. |
| Path injection through a ref | Resolved | Every component is percent-encoded with an empty safe set, so a ref containing `/` cannot introduce a path segment. |
| Unbounded download | Resolved | 256 MiB downloaded, 20,000 members, 1 GiB decompressed measured incrementally and tripping mid-read. |
| Stall / slow-drip | Partially resolved | A 30 s socket timeout and a 90 s inactivity timeout. **Accepted residual:** a slow but steady drip resets both timers; there is no total elapsed deadline. Recorded in RFC-0098 E11. |
| Bound raised by flag or environment | Resolved | Bounds are module constants; injected seams validate before resolving and apply `min(CONST, value)`, so a seam may only tighten. A test drives `None`, `True`, `"8"`, `1.5`, and `-1` through the refusal. |
| TLS trust weakened per-route | Resolved | The direct route builds its context with `ssl.create_default_context()` plus an **additive** `load_verify_locations`, and that context reaches the request through an explicit `HTTPSHandler`. Review found the opener built without one, so the context was constructed and discarded and `AGENTBUNDLE_CA_BUNDLE` was inert on this route while the certificate-failure remediation told adopters to set it; a control now asserts the classified context reaches the request. The store-replacing construction stays confined to the descriptor route. |
| System-trust retry absent on the direct route | Resolved | AC37's single retry against `system_trust.system_anchor_pem` now runs here through the shared `retry_with_system_trust` entry point, with `AGENTBUNDLE_NO_SYSTEM_TRUST` disabling it. It was previously unimplemented, and a test asserted the *absence* of the retry's helper names — pinning the gap rather than the no-second-copy rule it was written for. |
| Divergent TLS classification between routes | Resolved | One shared `classify_transport_attempt` in `catalogue.py`; a static test asserts the direct module contains no second copy of the classifier or the retry. |

---

## Supply chain

| Check | Disposition | Control |
|---|---|---|
| Bytes not bound to the requested revision | Resolved | The 40-hex SHA is read from `pax_global_header`; a full ref must equal it, an abbreviation must prefix it, and an absent or malformed value refuses. Verified against a real GitHub archive, not only fixtures. |
| Mutable reference installed as if pinned | Resolved | A bare or defaulted branch (`main`, `master`, `HEAD`) refuses; an explicit branch or tag resolves to the archive's SHA and is recorded as `source-revision`. |
| Ambiguous ref classification | Resolved | A hex-shaped ref that is neither 40 characters nor a 7–39 character abbreviation refuses rather than being guessed at in either direction. |
| Silent content change between installs | Resolved | A content-only digest over sorted length-prefixed path/content entries, with independently derived vectors committed. |
| Digest ambiguity | Resolved | u64be length prefixes; a committed vector pair proves `("ab", b"c")` and `("a", b"bc")` digest differently. |
| Digest re-baselined by a newer build | Resolved | A foreign prefix refuses comparison and directs reinstallation rather than recomputing. |
| Two envelopes collapsing to one digest entry | Resolved | The preimage uses the full relative path from the source root, never the leaf identity. |
| Capability widening on upgrade | **Pending the lifecycle command surface** | The comparison engine exists and is tested — re-consent on any change to tools, `SKILL.md` digest, skill identity set, payload digests, boundaries, or credentialed status, with acceptance tied to a pin over the exact displayed difference set — but it has no production caller, because `upgrade` does not yet handle a direct row. AC30 is unticked for the same reason. |
| Unreadable old data treated as unchanged | Resolved | Drift is `unknown`, which refuses even with the acceptance flag. |
| New runtime dependency | Resolved | None added. The direct modules are stdlib-only; a fresh import leaves `yaml` absent. |

---

## Exceptional condition

| Check | Disposition | Control |
|---|---|---|
| Partial write on refusal | Resolved | Admission completes before any write; normalization materialises into a temporary tree removed on every exit path, success or exception. |
| Temporary tree surviving a failure | Resolved | `acquire_git_https_archive` and `normalize_direct_source` both clean up under `BaseException`, so a `KeyboardInterrupt` is covered too. The install path removes the acquisition tree on the success and refusal paths alike, verified live. |
| Cleanup deleting the wrong directory | Resolved | `AcquiredArchive` declares the working directory the caller must remove. It was previously found by walking two parents up from the extracted root, which is the system temporary directory whenever no wrapper was descended. Found by the live remote run. |
| Replacement race between measurement and copy | Resolved | Normalization writes the already-measured bytes and never re-reads the source; a mutation test that re-reads fails the control. |
| Orphan sweep deleting installed content | Resolved | All seven sweep call sites refuse when state cannot be read. Four previously swallowed the failure into an empty protected set; three built no protected set at all. |
| Concurrent state write losing a row | Resolved | Every direct mutation goes through `persist_state_locked`, and the 0.5 floor is computed from the state re-read **inside** the lock. |
| Broad exception swallowing a security failure | Resolved | The transport classifier's intercepted set is named explicitly and carries the originating exception rather than collapsing it to an enum. |
| Interrupted install | Accepted residual | A hard interruption after projection and before the state write leaves unowned projection files. AC28 forbids a transaction or rollback extension; the files are visible as unowned and no sweep deletes them. |

---

## Agentic skills

| Check (OWASP Agentic Skills Top 10) | Disposition | Control |
|---|---|---|
| **AST01** Malicious content | Accepted residual | Admission is shape and bounds; nothing inspects intent. Mitigated by consent: the `admissible—not safe` verdict is emitted before *and* after the publisher block, and publisher text is delimited and labelled `publisher-supplied data, not instructions`. |
| **AST02** Supply chain | Resolved | See the supply-chain module above: revision binding, content digest, and upgrade re-consent. |
| **AST03** Permission over-declaration | Resolved | The capability block reports the normalized `allowed-tools` union per skill; an absent declaration renders `undeclared (unrestricted)` rather than as an empty restriction. |
| **AST04** Insecure metadata parsing | Resolved | A bounded stdlib-only frontmatter subset with size, depth, and list bounds; YAML tags, anchors, and aliases refuse. No `yaml` import on the direct path. |
| **AST05** Untrusted content as instructions | Resolved | Publisher values are emitted only between fixed line-anchored delimiters and never executed. A value equal to a delimiter refuses, so the block cannot be closed early. |
| **AST06** SSRF | Resolved | See the outbound-acquisition module. |
| **AST07** Version drift | Resolved | `source-revision` and `source-digest` recorded per row; updates are decided by digest, never by a recorded version string. |
| **AST08** Poor scanning | Resolved | Static architecture controls over the direct modules, each paired with a mutation fixture that fails if the control is removed. |
| **AST09** Governance | **Partly pending** | The diagnostic-code table is published in full and lint-checked for set equality against the registry, and every install records a state row carrying its canonical source, revision, and digest. `list-installed`, `show`, and `uninstall --skill` do **not** yet handle a direct row, so an installed direct skill is recorded but not yet inspectable or removable through the CLI. |
| **AST10** Missing security metadata | Resolved | `metadata.boundaries` and `metadata.credentialed` are read, reported in the capability block, and compared on upgrade in both directions. |

---

## Unresolved blockers

None that are unstated. Two rows above are **pending** rather than resolved, and
both depend on the same unbuilt surface — `upgrade`, `list-installed`, `show`,
and `uninstall` for direct rows — which is why AC4, AC7, AC9, AC22, and AC30 are
unticked in the spec. Until that lands, an installed direct skill is recorded in
state but cannot be inspected, upgraded, or removed through the CLI, and the
receipt's `uninstall --skill` line names a command that does not yet accept it.

Every other residual is stated with its reason and recorded in the governing
criterion or in `docs/architecture/security.md`.

## Provenance of this record

The first version of this document was written alongside the implementation by
its author, and independent review found three rows asserting Resolved against
code that did not do what the row claimed — the two TLS rows above and AST09.
That is the failure mode this section exists to flag for the next reader: a
self-authored evidence table records what the author believed, and belief is not
a control. Each Resolved row should be read as a claim to re-check, not as a
verification already performed.
