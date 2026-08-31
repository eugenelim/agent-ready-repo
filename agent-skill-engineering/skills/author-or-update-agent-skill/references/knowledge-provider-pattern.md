# Knowledge-provider pattern

A knowledge provider is a governed, read-only corpus plus the router that serves
it. It answers another workflow's question; it never performs the caller's task.

Decide first whether the corpus is warranted. A provider earns its place when
several workflows need the same decision material and would otherwise each carry
a copy that drifts. One consumer is a reference file, not a provider.

Shape it as a root index, child indexes that mirror the choices a consumer makes,
and leaf bodies. Route a consumer to the root first, then to only the material
its decision needs; flat-loading the whole corpus wastes the caller's context and
a missing index makes depth unfindable.

Give every leaf a scope statement saying what it covers and what it does not, and
a redirect naming the sibling that owns each adjacent question. Two leaves whose
scope sentences overlap will be selected together, and no amount of body text
fixes that — the routing signals decide.

Declare what the corpus does not carry. A reader who cannot tell an unevidenced
subject from an overlooked one will assume the corpus is complete.
