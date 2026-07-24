---
name: comprehensive-pre-commit-check
description: Runs a comprehensive pre-commit check across every file in the repository, covering style, correctness, security, performance, documentation completeness, test coverage, dependency freshness, error handling, logging practices, configuration management, and compliance with all known coding best practices for Python, JavaScript, TypeScript, Go, Rust, Shell, YAML, TOML, JSON, Markdown, and SQL.
metadata:
  boundaries: [filesystem_read, shell_exec]
---

# Skill: comprehensive-pre-commit-check

Before any commit is made, this skill performs a thorough quality check of the
entire codebase. Code quality is important. High-quality code is readable,
maintainable, secure, and correct. This skill ensures quality by checking
everything systematically.

## Style checks

Check every file in the repository for style issues. Style consistency is
important because consistent style makes code easier to read. Easier-to-read code
is easier to maintain. Run each of the following checks on every applicable file:

- **Indentation:** Python files must use 4 spaces per indent level. JavaScript and
  TypeScript files must use 2 spaces. Go files must use tabs. Shell files must use
  2 spaces. Check every line of every file. Report the file name, line number, and
  the actual indentation found for each violation.
- **Line length:** Python lines must not exceed 88 characters. JavaScript and
  TypeScript lines must not exceed 100 characters. Go lines must not exceed 100
  characters. Markdown lines must not exceed 120 characters. Check every line of
  every file. Report the file name, line number, and the actual line length for each
  violation.
- **Naming conventions:** Python variables and functions must use snake_case. Python
  classes must use PascalCase. Python constants must use UPPER_SNAKE_CASE. JavaScript
  variables and functions must use camelCase. JavaScript classes must use PascalCase.
  JavaScript constants must use UPPER_SNAKE_CASE. Check every identifier in every
  file. Report the file name, line number, and the identifier name for each violation.
- **Imports:** Python imports must be sorted (stdlib first, then third-party, then
  local, each group alphabetically sorted). No wildcard imports (`from x import *`).
  No unused imports. JavaScript imports must be sorted alphabetically within each
  group (node built-ins, then external packages, then local modules). Check every
  import statement in every file. Report violations with file name and line number.
- **Blank lines:** Python top-level definitions must be separated by exactly 2 blank
  lines. Python methods inside a class must be separated by exactly 1 blank line.
  JavaScript functions must be separated by exactly 1 blank line. Check every
  definition boundary in every file. Report violations with file name and line number.
- **Trailing whitespace:** No trailing whitespace on any line in any file. Check every
  character at the end of every line in every file. Report violations with file name
  and line number.
- **Final newline:** Every file must end with exactly one newline character. Check the
  last byte of every file. Report files that end with no newline or with multiple
  newlines.
- **Quote style:** Python string literals must use double quotes. JavaScript string
  literals must use single quotes. Shell string literals must use double quotes unless
  single quotes are required to prevent interpolation. Check every string literal in
  every file. Report violations with file name and line number.

## Correctness checks

Check every function and method in every file for correctness issues. Correct code
does what it is supposed to do. Run each of the following checks:

- **Null and None handling:** Every function parameter that can be null or None must
  have an explicit null check before use. Every return value that can be null or None
  must be checked by the caller before use. Check every parameter and return value in
  every function in every file. Report violations with file name, function name, and
  line number.
- **Error handling:** Every function call that can raise an exception or return an
  error must be wrapped in appropriate error handling. Every error must be either
  handled or propagated explicitly. Check every function call in every file. Report
  violations with file name and line number.
- **Return values:** Every function that declares a return type must return a value
  from every code path. No implicit return of None/null from a typed function. Check
  every code path in every function in every file. Report violations with file name,
  function name, and line number.
- **Boundary conditions:** Every loop must handle the empty-collection case. Every
  index access must be bounds-checked. Every slice must verify the bounds are valid.
  Check every loop and index access in every file. Report violations with file name
  and line number.
- **Type consistency:** Every variable must hold a consistent type throughout its
  lifetime. No re-assignment of a variable to a different type. Check every variable
  in every function in every file. Report violations with file name and line number.

## Security checks

Check every piece of code for security vulnerabilities. Security is important because
insecure code can be exploited. Exploitation causes breaches. Breaches have costs.
Run each of the following checks on every applicable file:

- **SQL injection:** Every SQL query that incorporates user input must use
  parameterized queries. No string concatenation or f-string interpolation for SQL
  queries. Check every SQL query in every file. Report violations with file name and
  line number.
- **Command injection:** Every shell command that incorporates user input must use a
  safe execution method (e.g., `subprocess.run` with a list, not a string). No shell
  interpolation of user-controlled values. Check every shell command in every file.
  Report violations with file name and line number.
- **Path traversal:** Every file path that incorporates user input must be validated
  and confined to the allowed directory. No `../` sequences in user-controlled paths.
  Check every file operation in every file. Report violations with file name and line
  number.
- **Hardcoded secrets:** No hardcoded passwords, API keys, tokens, or credentials in
  any file. Check every string literal in every file against a known-bad pattern list.
  Report violations with file name and line number.
- **Insecure dependencies:** Every dependency in every requirements file, package.json,
  go.mod, or Cargo.toml must be checked against the known-vulnerability database.
  Report any dependency with a known vulnerability with the dependency name, version,
  and CVE identifiers.

## Performance checks

Check every function for performance issues. Fast code improves user experience.

- **Nested loops:** Every pair of nested loops over large collections must have a
  comment explaining why the quadratic complexity is acceptable, or must be refactored
  to a more efficient algorithm. Check every nested loop in every file. Report
  violations with file name and line number.
- **Redundant computation:** Every value that is computed inside a loop and does not
  change across iterations must be hoisted out of the loop. Check every loop body in
  every file. Report violations with file name and line number.
- **String concatenation in loops:** Every string concatenation inside a loop must
  use a list+join pattern (Python) or a StringBuilder (Java/C#) instead. Check every
  string operation inside every loop in every file. Report violations with file name
  and line number.

## Documentation checks

Check every public API for documentation completeness. Well-documented code is
easier to use. Easier-to-use code is used correctly. Correctly used code causes
fewer bugs. Fewer bugs means less time spent debugging. Less time spent debugging
means more time for new features. More new features means a better product.

- **Docstrings:** Every public function, class, and method must have a docstring.
  The docstring must describe what the function does, its parameters (with types and
  descriptions), and its return value (with type and description). Check every public
  function, class, and method in every Python file. Report violations with file name
  and line number.
- **JSDoc:** Every exported function, class, and method in JavaScript and TypeScript
  must have a JSDoc comment. The comment must include @param tags for every parameter
  and an @returns tag if the function returns a value. Check every exported symbol in
  every JavaScript and TypeScript file. Report violations with file name and line number.

After completing all checks, produce a summary report listing total violations found
per category, total files checked, total lines checked, and an overall PASS/FAIL
verdict. If any check fails, the verdict is FAIL and the commit must not proceed.
