---
title: "Library, SDK, and CLI systems"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - SS-L1
  - SS-L1b
---
# Library, SDK, and CLI systems

## Scope and routing signals

Use when the primary deliverable is embedded in another process, invoked as a command, or consumed through a public programming surface.

## Decisions and minimum evidence

Supports compatibility, packaging, portability, and consumer-safety decisions. Minimum evidence covers public API/CLI, invocation lifecycle, dependency/runtime support, configuration, error/exit semantics, versioning, distribution, extension points, security boundary, and consumer tests.

## Architectural questions

- What public behavior has become a compatibility contract?
- Which host-process, shell, filesystem, network, or platform assumptions leak outward?
- How are deprecation, failure, cancellation, and upgrade communicated?

## Mechanisms and trade-offs

Stable facades, semantic versioning, capability detection, adapters, schema validation, deterministic packaging, and compatibility suites trade innovation speed against consumer stability.

## Evidence and counter-evidence

Seek exports/entry points, CLI parsers, package manifests, compatibility tests, release notes, install paths, and usage examples. Counter-evidence includes internal symbols used externally and platform-specific behavior absent from tests.

## Failure modes and false positives

A small repository can have a large compatibility surface; static linking does not eliminate supply-chain or host risks; docs alone do not prove stable behavior.

## Confirmation scenarios

Exercise install, first use, invalid input, partial failure, upgrade, downgrade/rollback, and removal on each supported platform class.

## Related concepts and escalation

Pair with interface contracts, testability, supply-chain/security specialist review, and transactional or batch workload lenses as triggered.

## Provenance and lifecycle

Synthesized from ISO architecture concerns and cross-platform/cloud design guidance. Confidence: moderate; review annually.

Research claim trace: `SS-L1`, `SS-L1b`; see the living source packet with the same concept path.
