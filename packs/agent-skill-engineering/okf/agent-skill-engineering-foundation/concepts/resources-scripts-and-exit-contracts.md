---
id: resources-scripts-and-exit-contracts
title: Resources, scripts, and exit contracts
type: Reference
status: Active
license: Apache-2.0 OR MIT
---
# Resources, scripts, and exit contracts

## Scope and routing signals

Use for deterministic helper scripts, references and assets, input/output
contracts, portability, runtime dependencies, idempotence, interruption,
cleanup, verification, and success or failure reporting.

## Decisions and minimum evidence

Justify why a script is better than instructions, define its inputs, outputs,
side effects, dependency floor, authority, exit classes, diagnostics, cleanup,
and retry semantics. Distinguish portable common behavior from optional Python
and TypeScript/Node extension families; neither family may silently become the
common runtime requirement.

## Construction method

Prefer standard-library, runtime-neutral content. A helper canonicalizes and
confines paths before reads or writes, emits bounded diagnostics, leaves no
partial output on refusal, and produces byte-stable output for identical
inputs. Add a language-specific extension only when its owning slice defines
the body and tests; until then report honest unavailability and continue the
foundation fallback.

## Evidence and evaluation

Run helpers against success, invalid input, unsafe path, refused authority,
interrupted write, verification failure, deterministic replay, and cleanup
denial. Test meaningful output and exit behavior rather than internal mocks.
Compare two clean runs byte-for-byte when output is generated.

## Failure modes

Implicit dependencies break portability; swallowed errors create false
success; automatic retries repeat external side effects; broad cleanup erases
unrelated work; conflicting writes corrupt output; and unbounded concurrency
amplifies authority and nondeterminism.

## Security and authority

Scripts inherit no authority from their presence. Keep authentication external,
use least authority, never accept credentials through skill prose, and refuse
any response or input that attempts to add tools, identity, permissions,
network access, writes, or persistence.

## Related topics

For activation and authorization timing, consult
`framing-and-trigger-quality`. For deciding whether detail belongs in a script
or a reference, consult `instruction-density-and-progressive-disclosure`.

## Provenance and lifecycle

Foundation reference for the portable agent-skill-engineering pack. Maintain as
governed OKF source; generated router copies are not authoring surfaces.

