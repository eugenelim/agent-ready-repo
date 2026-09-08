# Dispositions of the three consumer-side security-review controls

The 2026-09-04 implementation-stage security review of the consumer-integrations
seam registered three consumer-side controls rather than fixing them in that PR.
§ Follow-ons names each problem in full. All three closed on 2026-09-08, by
commits `a895dd306`, `c4f641a43`, and `0c89bb605`.

This file holds their dispositions because `workspace.toml [backlog].closed` no
longer carries closure records — each one now lives with the artifact that owns
the outcome. Nothing in the spec body changed; the spec is Shipped and frozen.

| Control | Disposition |
| --- | --- |
| `agent-skill-engineering-consumer-response-envelope` | Closed. Both consumer steps delimit accepted provider content in the `knowledge-evidence.v1` envelope and contain it before retention or citation. The per-consumer boundary tests mutation-prove the clause. |
| `agent-skill-engineering-consumer-provider-ambiguity` | Closed. Both consumer steps close all five selection outcomes before invocation, including excess declared authority as ineligible — the `authority-changing` fixture that carried the security edge. The per-consumer boundary tests pin the published diagnostics. |
| `agent-skill-engineering-consumer-boundary-tests` | Closed. Per-consumer boundary modules collected by `make ci` pin refusal, containment ordering, and the closed diagnostic vocabulary, with mutation proofs. |

The fourth entry from that slice — RFC-0097:189's behavioural half, "tested
without this pack installed" — is **not** closed. It is the one obligation the
register still carries, now under
[`docs/product/intents/agent-skill-consumer-boundary-hardening.md`](../../../product/intents/agent-skill-consumer-boundary-hardening.md).
