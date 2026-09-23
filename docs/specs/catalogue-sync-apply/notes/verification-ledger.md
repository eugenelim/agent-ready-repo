# Verification ledger — catalogue sync, the apply path and the scoping flags

Execution observations, one section per wave. The plan contract sends them here
rather than into the plan, which is hash-pinned from `plan-locked` onward.

## Shaping — grounding derivations

- **Date:** 2026-09-22

Four read-only probes under
[`grounding/`](grounding/) established the facts the contract rests on. The
plan's § Grounding table holds each invocation; this section holds what each
one printed.

| Derivation | Printed |
| --- | --- |
| `probe-scope-subtrees.py` | `--package credbroker` → `packages/credbroker/`, gated on the `credential-brokers` pack; `--package agentbundle` → `.agentbundle/tooling/agentbundle/`, gated on vendored tooling. `collect_fields` replaces the recorded recipe when `cfg.packs` is not `None`; `_plan_stale_owned_paths`'s `current_paths` is the keep-set |
| `probe-pin-ref.py` | `resolve_catalogue` returns a `Path` only; `_resolve_https` parses the ref from the URI and defaults it to `main`, never resolving it to a commit SHA; the pattern is the module-level `_HTTPS_RE` |
| `probe-jailed-write-admits-planned-paths.py` | external 1,907 planned paths, vendored 2,147; zero rejected as a direct write and zero as a companion write in both modes |
| `probe-rollback-snapshot-bound.py` | external 13.7 MiB, vendored 17.3 MiB of replayed bytes; largest single file 0.2 MiB; worst-case peak 34.5 MiB for replay plus a full-run snapshot |

### Residuals reported

- The architecture's § Granularity calls both `--package` targets "`packages/`
  subtrees". Only `credbroker` is one; the vendored `agentbundle` lands under
  `.agentbundle/tooling/`. AC-0053 corrects it.
