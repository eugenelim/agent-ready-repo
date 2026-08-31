---
id: python-and-pytest
title: Python and pytest
type: Reference
status: Active
license: Apache-2.0 OR MIT
---
# Python and pytest

## Scope and routing signals

Use for Python skill scripts, evaluations, and test suites that need predictable
collection, fixtures, subprocess boundaries, or temporary paths. Keep runner
rules separate from guidance for other language ecosystems.

## Decisions and minimum evidence

Choose a discovery root and package layout deliberately. Test discovery and
importability depend on the configured discovery root and the test directory's
Python-package layout. Treat fixture scope as an ownership decision, and state
which process creates and cleans a temporary path.

## Construction method

Keep collection configuration close to the suite it governs. Use fixtures for
shared setup and teardown, pass explicit inputs across subprocess boundaries,
and create temporary files or directories through a lifetime-owning helper.
Do not let a child process depend on an accidental current directory.

## Evidence and evaluation

Exercise collection from the intended root, a fixture cleanup path, a child
process with explicit arguments, and a temporary-path lifecycle. Include a
case that would expose an import collision or an uncollected test.

## Failure modes

An unconfigured discovery root can collect the wrong files. A fixture that
owns too much state makes tests order-dependent. Implicit working directories
and undeclared temporary paths make subprocess behavior hard to reproduce.

## Security and authority

Treat test input, child-process arguments, and temporary paths as boundaries.
Validate values before passing them to a process, avoid shell interpolation,
and clean only paths created for the current test operation.

## Related topics

For process and filesystem cost, consult `process-and-filesystem-cost`. For
cross-language runner limits, consult
`typescript-node-and-javascript-test-runners`.

## Provenance and lifecycle

**Python and pytest contract:**
Test discovery and importability depend on the configured discovery root and the test directory's Python-package layout.
Last verified: 2026-08-30.
Revalidate when pytest or CPython changes test discovery or import behavior.
Ecosystem: pytest and CPython.
Version range: pytest >= 9.1.1, upper bound open; CPython >= 3.14.7, upper bound open.
pytest documentation — https://docs.pytest.org/en/stable/explanation/pythonpath.html
Retrieved at: 2026-08-30. Version: 9.1.1.
CPython unittest documentation — https://docs.python.org/3/library/unittest.html
Retrieved at: 2026-08-30. Version: 3.14.7.
CPython tempfile documentation — https://docs.python.org/3/library/tempfile.html
Retrieved at: 2026-08-30. Version: 3.14.7.
