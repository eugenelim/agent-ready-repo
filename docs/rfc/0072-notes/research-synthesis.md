# RFC-0072 Research Synthesis

Supporting evidence for `docs/rfc/0072-agentbundle-enterprise-distribution.md`.

---

## D1 — HTTPS catalogue channel descriptor: mutable pointer → immutable archive

**Prior art verified:**

- **Homebrew Bottles** — [`https://docs.brew.sh/Bottles`](https://docs.brew.sh/Bottles).
  *"Contains the SHA-256 hash of the bottle for the given OS/architecture."*
  Homebrew formula (mutable, updated per release) references a bottle archive (immutable, SHA-256 verified). Checksum mismatch falls back to source build. **PASS — exact pattern**.

- **Debian SecureApt** — Mutable `Release` file (channel descriptor) + immutable `.deb` packages + SHA-256 embedded in `Packages` index. The `stable` suite pointer is the mutable artifact; the versioned `.deb` binary is the immutable one. **Consistent pattern — not independently fetch-verified; corroborating evidence only.**

- **conda sharded repodata (CEP-21)** — Mutable repodata shards point to immutable package archives; conda-lock pins the resolved archive for reproducibility. **Consistent pattern — not independently fetch-verified; corroborating evidence only.**

- **Docker image digests** — Image tags (`latest`, `stable`) are mutable; the `sha256:` digest addresses an immutable content-addressed layer. Same pattern at the container level. **Consistent pattern — not independently fetch-verified; corroborating evidence only.**

**Spike result:**

`_is_valid_source` (`source_defaults.py:76–98`) currently rejects all non-`git+https://` URL schemes. `urlsplit("catalogue+https://foo").scheme` returns `"catalogue+https"` — non-empty → hits `return False` at line 96. The fix is a new `startswith` branch before that gate. **Non-blocking; no rewrite of layers 1–2 or 4 required.**

---

## D2 — Org Artifactory bootstrap: new layer 3 in the precedence chain

**Prior art verified:**

- **npm `.npmrc` scope binding** — [`https://docs.npmjs.com/cli/v11/configuring-npm/npmrc/`](https://docs.npmjs.com/cli/v11/configuring-npm/npmrc/). Registry binding documented; `@scope:registry` key form supported. **DIRECTIONALLY CONFIRMED** — the exact `@scope:registry` form was not observed in the fetch; cite as directional prior art for package-shipped config concept, not as an exact syntax match.

- **pip `--extra-index-url` / `--index-url` in `pip.conf`** — pip supports pre-distributed `pip.conf` files in well-known locations; enterprises ship internal index config as part of the Python toolchain setup. Documented but not as a distributed-in-wheel mechanism. **Partial prior art for shipping config with the package.**

- **ADR-0036 D1** — "user config deliberately outranks editable detection." The new layer 3 sits between user config (layer 2) and editable detection (former layer 3, now layer 4). User intent still wins. ADR-0036 D1 is preserved.

- **Fail-closed rationale** — ADR-0036's layer 5 (packaged default) is intentionally lenient: a blank/malformed `source` yields `None` (the private-fork pattern). For an explicitly-enabled org config (`enabled = true`), falling through silently would be incorrect — the organization has declared an intent that a malformed value subverts. Fail-closed with a named error is the right behavior for explicit intent.

---

## D3 — Source conflict install guard

**Prior art verified:**

- **Cargo Source Replacement** — [`https://doc.rust-lang.org/cargo/reference/source-replacement.html`](https://doc.rust-lang.org/cargo/reference/source-replacement.html).
  *"Cargo has a core assumption about source replacement that the source code is exactly the same from both sources."*
  Cargo enforces single-source identity per crate at build time; mixing is unsupported. **PASS — validates the refuse-by-default pattern.**

- **ADR-0021 D7** — `@catalogue/pack` identity declared; multi-catalogue resolution deferred. The source conflict guard is an explicit bridging mechanism until multi-catalogue resolution is implemented. D3 is compatible with ADR-0021 — it does not pre-empt the longer-term resolution.

- **Why `--force` does not bypass:** A source mismatch is a provenance problem, not a preference. Overriding it with `--force` would require the user to assert that two different sources contain the same pack content — an assertion agentbundle cannot validate at install time. The block is a correctness gate, not a workflow gate.

---

## D4 — Bulk upgrade plan/apply split

**Prior art verified:**

- **Cargo `cargo-update`** — [`https://doc.rust-lang.org/cargo/commands/cargo-update.html`](https://doc.rust-lang.org/cargo/commands/cargo-update.html).
  `cargo update` only writes `Cargo.lock`; downloads and builds occur in a separate `cargo build` step. Confirmed behavioral separation of "plan" (resolve what will change) from "apply" (build/download). **CONFIRMED — consistent with D4 preflight model.**

- **pip no built-in upgrade-all command** — pip has no built-in mechanism to upgrade all installed packages at once. `pip list --outdated` → script loops are the common workaround. `--upgrade-strategy` was added in pip 9 (issue #59) but applies per-package, not as a bulk "upgrade all." **Note: the initial research draft incorrectly stated pip "deliberately has no upgrade-all command" — this is not a design statement made by pip maintainers and was dropped from the RFC body.**

- **Homebrew `brew upgrade` (no args)** — upgrades all outdated formulae; failed formula outputs a summary of partial completion; other formulae are not rolled back. Behavioral prior art for disclosed non-atomicity. **Consistent pattern — not independently fetch-verified; corroborating evidence only.**

- **ADR-0036 D5 / D3** — No repo-scoped source; no cwd fallback. Preflight that scans state rows and resolves sources is consistent with this — sources are resolved through the chain, not inferred from cwd.

---

## D5 / D6 — CLI surfaces and layout checks

**No external verification needed for D5 surface ratification.** `--format table|json` is a standard Unix CLI pattern (k8s `kubectl`, GitHub CLI `gh`, AWS CLI `--output json`). `upgrade --all` is a universal package manager verb. `package-catalogue` is a new verb with no contested external precedent.

**D6 formatting error evidence:** Previous `list-installed` table output had formatting errors (reported by user; not yet investigated — the implementing spec for `spec/list-installed-update-status` must audit and correct before recording golden files). Golden-file snapshot tests are the standard regression pattern for CLI output.

---

## Citation status summary

| Citation | Status |
|----------|--------|
| Homebrew Bottles — SHA-256 digest quote | **PASS** — fetched, quote confirmed |
| Cargo source replacement — source code identity quote | **PASS** — fetched, quote confirmed |
| Cargo cargo-update — plan/apply split | **CONSISTENT** — behavioral confirmation, not explicit design guarantee |
| npm .npmrc scope registry | **DIRECTIONALLY CONFIRMED** — registry binding confirmed, exact key syntax not independently verified |
| Debian SecureApt / conda CEP / Docker digest | **CORROBORATING** — pattern consistent, not independently fetch-verified |
| pip no built-in upgrade-all | **CORRECTED** — "deliberately no upgrade-all" claim dropped after verification; revised to behavioral fact |
