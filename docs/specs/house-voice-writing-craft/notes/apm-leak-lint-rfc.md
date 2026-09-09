# APM leak-lint retirement anchor

## Disposition

Retired on 2026-09-08. Do not open the proposed RFC or restore
`tools/lint-agent-artifacts.py` for this deferral.

The concrete adopter-facing reference cleanup shipped in
[`apm-internal-ref-sweep`](../../apm-internal-ref-sweep/spec.md). Subsequent
decision archaeology established that commit `96232e6` deliberately deleted
the standalone linter after its checks moved behind `agentbundle catalogue
lint` and `agentbundle catalogue verify`; the owning shipped specification also
rejected a compatibility shim. See the
[`lint-agent-artifacts.py` archaeology](../../bug-fix-systematic-debugging/notes/lint-agent-artifacts-archaeology.md).

The remaining `.apm` references include legitimate repository workflow and
governance material, so the retired blanket-lint proposal does not define a
safe new invariant. Any later restriction requires independently grounded
scope and authority rather than reopening this item.

