# oracle-table — per-tool concrete acquisition commands (the reference instance)

> **Loaded when:** the agent has detected the stack or library (protocol T0) and
> needs the concrete oracle commands — validate / plan / schema for an infra
> toolchain, or version-detect / type-checker / API-surface / probe for a
> software library.
> **Status:** this table is the **reference instance** — concrete commands for
> the strong-tier stacks so they are runnable without guessing. The normative
> protocol in `SKILL.md` stays tool-neutral; nothing here is normative, and a
> tool's absence from this table is not a statement that it is unsupported (the
> tier spectrum, not this table, is the authority on coverage).

Each row gives, per tool: the **T1 static oracle** (validate + plan/preview),
the **schema slice** command (what to pull for the diff's resources), and
**what the schema exposes vs. what it does not** — so the immutability signal
is read from the right place (see `SKILL.md` § Contract-source heterogeneity).

## Strong tier

| Tool | T1 oracle (validate + plan/preview) | Schema slice | Immutable / replace signal |
| --- | --- | --- | --- |
| **Terraform / OpenTofu** | `terraform validate` then `terraform plan -out=tfplan` (review the diff); `terraform show -json tfplan` for a machine-readable plan | `terraform providers schema -json` (fields: `type` / `description` / `required` / `optional` / `computed` / `sensitive` only) | **Not in schema JSON.** Read `# forces replacement` from `terraform plan` **+ provider docs** |
| **Pulumi** | `pulumi preview --diff` (per-resource diff); `pulumi preview --json` for machine-readable | `pulumi package get-schema <provider>` → the resource's `properties` + `inputProperties` | `replaceOnChanges` **in schema** — read it from the slice |
| **AWS CDK** | `cdk synth` (emits the CloudFormation template); `cdk diff` against the deployed stack | the synthesized template + the underlying CFN resource-type schema (below) | via the CFN resource schema (below) |
| **AWS CloudFormation** | a **change set** (`create-change-set` → `describe-change-set`) — the dry-run diff before execute | `aws cloudformation describe-type --type RESOURCE --type-name AWS::Svc::Res` → the resource-type schema | `createOnlyProperties` **in schema** — read it from the slice |
| **Kubernetes / Helm** | `kubectl apply --dry-run=server` (server-side validation against the live API); `helm template` then the same dry-run | `kubectl explain <resource>.<path> --recursive` (OpenAPI schema from the cluster) | immutability is per-resource (e.g. many `spec` fields); read `kubectl explain` notes + the resource's API reference |

## Medium tier

| Tool | T1 oracle | Schema slice | Notes |
| --- | --- | --- | --- |
| **Ansible** | `ansible-playbook --check --diff` (what-if; module-dependent fidelity) | module docs (`ansible-doc <module>`) — no uniform machine-readable resource schema | lean on T3 docs + the runtime probe; `--check` fidelity varies by module |
| **Bicep** | `az deployment ... what-if` (ARM what-if diff) | the underlying ARM resource-provider schema | what-if is the diff oracle; schema is ARM-template-shaped |
| **cloud-init** | YAML schema validation (`cloud-init schema --config-file`) | the cloud-init module schema | validates config shape, not runtime effect — the probe confirms |

## Weak / none tier

| Surface | Why no strong static oracle | Posture |
| --- | --- | --- |
| **bespoke REST + `curl`** | no validate / plan / schema; the API is the only source of truth | **declare weak**, retrieve the API's own docs/OpenAPI if any (T3), and ground the contract at the **runtime probe** |
| **hand-rolled bare-metal provisioning** | imperative scripts have no declarative oracle | same — declare weak, lean on the probe; consider whether the step can be made declarative (`state-and-idempotency`) |

On a weak surface the static contract is *low-confidence by construction*. The
honest move is to **say so and shift weight to the runtime data-plane probe**
(`SKILL.md` § the Final oracle), never to manufacture a static check the tool
cannot back.

---

# Software surface — per-ecosystem oracles

The same protocol tiers, keyed to the language toolchain instead of an IaC tool.
**T0** = detect the installed version (the contract is version-specific); **T1**
= the type checker / compiler (the deterministic signature oracle) plus an
API-surface extract of the *installed* package; **probe** = invoke-and-observe.
The tier strength is the *library's*, not the language's: a typed/stub-equipped
library is strong; the same language consuming an untyped or C-extension library
drops to medium/weak (read it from the table, declare it in the slice).

The **API-surface extract** column grounds the *current* call site against the
installed contract — that is the T1 job. A separate class of tool (`griffe
check`, `cargo-semver-checks`, `@microsoft/api-extractor`) answers a *different*
question — *did the API change between two versions* — which is a **migration**
signal, not a call-site oracle (grounding a fresh call has no prior version to
diff). Those are listed under **migration**, not conflated with the slice.

| Ecosystem | T0 — installed version | T1 — type/compiler oracle (run against the call site) | T1 — API-surface extract (the slice) | Probe — invoke & observe | Migration (version-diff, only when upgrading) |
| --- | --- | --- | --- | --- | --- |
| **Python** | `python -c "import importlib.metadata as m; print(m.version('pkg'))"` (live install, not the lockfile) | `mypy` / `pyright` (+ `pyright --verifytypes` for a `py.typed` package's completeness) | `inspect.signature` / `python -m pydoc`, or `griffe dump pkg` | `python -W error::DeprecationWarning` + a minimal call asserting the return type | `griffe check pkg -a <git-ref>` (diffs against a ref) |
| **TypeScript / JS** | `npm ls <pkg>` (walks `node_modules`) | `tsc --noEmit` against the call site | the shipped `.d.ts` | run the snippet under `node`; observe the value / thrown error | `@microsoft/api-extractor` API report diff |
| **Go** | `go list -m <module>` (resolved from `go.mod` — `go.sum` is integrity, not resolution) | `go build` / `go vet` (the compiler is exhaustive) | `go doc <pkg> <symbol>` | a `_test.go` exercising the call | `gorelease` (API-compat report) |
| **Rust** | `cargo tree -e normal` (resolved from `Cargo.lock`) | `cargo check` (borrow/lifetime/trait bounds are machine-enforced) | `cargo doc` / rustdoc JSON | a `#[test]` or `cargo run` on a minimal example | `cargo-semver-checks` (SemVer API diff) |
| **Java / JVM** | `mvn dependency:list` / `./gradlew dependencies` | the compiler (`javac`) | `javap -public -cp <classpath>` (reads the binary contract from bytecode) | a JUnit probe or `jshell` session | `japicmp` / `revapi` (bytecode API diff) |

**Known oracle gaps to declare, not paper over** (the per-surface weak-row in
`SKILL.md` § Oracle-tier honesty):

- **Native/foreign-code boundaries are the general weak-tier mechanism** —
  wherever the implementation drops out of the introspectable language
  (Python C extensions, native Node addons, JNI-backed Java, Rust FFI), the
  introspection oracle is *blocked at exactly the boundary it would help*: e.g.
  Python `inspect.signature` may raise on a C-accelerated function
  (numpy/pandas internals). This is *why* the weak-software row exists. Fall to
  T3 docs + the probe.
- **`cargo-semver-checks`** detects structural API breaks but **not** type-level
  changes (altered parameter types, changed generic bounds) — a strong
  *structural* signal, not a complete one.
- **Auto-generated stubs** (`stubgen`, shipped with mypy) default to `Any` — a
  scaffold, not a verified contract; do not report a stubgen skeleton as a
  strong-tier oracle.
- **Behavioral contracts** (call-order, thread-safety, semantic parameter
  changes) appear in **no** tier-1 oracle — only T2 (curated skill), T3
  (changelog), or the probe. A green type check is necessary, not sufficient.
