# Reading disagreements and rulings

The hand check (`hand-check.json`) recorded 83 reading disagreements: items where a reader's plain reading differs from what the spec's Terms decide. The health result and the hand check agree on every set (`accuracy-diff.json`), so each item concerns the Terms, not the code.

**Ruling:** eugenelim ruled in session on 2026-10-26 that none is a defect in health. Each item is an accepted limit of the Terms or no issue, by group:

- **Group 1** (54 items): rule worked as written; plain reading agrees.
- **Group 2** (4 items): reported item a reader may call not real; accepted: a passed date, a version form and a header citation are decided by the Terms.
- **Group 3** (17 items): item the Terms skip; accepted limit of the deterministic grammar and rooted-path rule.
- **Group 4** (2 items): reported finding the reader agrees is real.
- **Group 5** (6 items): cosmetic excerpt whitespace.

| Record | Group | Reader's note |
| --- | --- | --- |
| ADR-0016 | 3 | Plain reading sees two version references here: 'Gemini 3' and the '2.5' inside `gemini-2.5-flash-lite`. The Terms find neither. '2.5' comes straight after '-' and is followed by '-flash', a word joined by '-', so the first version form excludes it. 'Gemini 3' has no 'v' and is a single digit run, so neither form matches. Result: no version mention, class judge rather than version. |
| ADR-0018 | 3 | Plain reading treats 'an annual standards refresh' as a recurring date-based trigger. The trigger text holds no date mention under the Terms, so the class is judge, not scheduled. |
| ADR-0027 | 3 | `assets/adr.md` reads as a path relative to the new-adr skill directory, but the Terms resolve it from the repository root, so it is unlocated rather than checked. |
| ADR-0032 | 3 | `lens-genai-agentic.md` is a skill reference file (one copy in each of two skills), but the Terms make it an unlocated bare filename. |
| ADR-0035 | 3 | `lens-serverless.md` is a skill reference file, but the Terms make it an unlocated bare filename. |
| ADR-0036 | 4 | The test file most likely sits in a package's own tests tree (e.g. under packages/agentbundle/). The Terms resolve it from the repository root, where tests/unit is absent, so it counts as missing. |
| ADR-0037 | 1 | The trigger contains the word 'stable' but does not start with it, so it is judge, not stable. |
| ADR-0039 | 5 | The source breaks 'derived-ownership' across a line. The join rule adds a space, giving 'derived- ownership'; a plain reading has no space. |
| ADR-0039 | 2 | `v0.3` is a state-schema version rather than a software release. The class is version either way. |
| ADR-0040 | 1 | `.agents/skills/` names an adapter install prefix in adopters' repos, not this repo's file. It resolves present only because this repo has its own .agents/skills. |
| ADR-0041 | 3 | `evals/evals.json` is relative to the new-adr skill directory, but the Terms make it unlocated. |
| ADR-0044 | 5 | The continuation lines are indented two spaces. The Terms join lines with one space but don't say to strip each line's leading space, so the literal text keeps runs of three spaces. A plain reading uses single spaces: '...provable autonomy predicate... under a new harness...'. |
| ADR-0048 | 1 | `ledger.toml` and `last-synced.toml` are runtime state files under ~/.agentbundle/, not repo paths. They are unlocated as the Terms decide. `<run-id>/`, `sources/<source-hash>/` and `content-hashes[]` are excluded as candidates by their characters. |
| ADR-0049 | 1 | `json.dump` is a Python function, not a path. The Terms treat it as a path candidate because it ends in '.dump'. |
| ADR-0049 | 1 | `build/lint_packs.py` most likely sits inside a package (e.g. packages/agentbundle/...). The Terms resolve it from the root, where 'build' is absent, so it is unlocated rather than missing. |
| ADR-0049 | 1 | `.write_text` is not a candidate: after its only '.', 'write_text' is not 1 to 5 letters or digits. `*.schema.json` is excluded by the '*'. |
| ADR-0051 | 1 | The Decision summary also has a 'Revisit if' line with different wording (line 28). The Terms take only the Consequences one (line 83). `tomllib.loads()` and `tomli.loads()` end in ')' and contain no '/', so they are not path candidates. |
| ADR-0053 | 2 | 'v1' matches the second version form ('v' plus digits, space on both sides), so the class is version. Read plainly, 'D4's v1 exclusion' means the pack's first-release scope, not a software version, and a person would class this trigger judge. |
| ADR-0054 | 1 | The signal's backtick spans (`grep -rn "check-workspace"`, `git ls-files`, `adversarial-reviewer`) are not path candidates: the first two contain whitespace, and the third has no '/' and no file extension. |
| ADR-0055 | 1 | The 'Consequences:' paragraph inside the Decision section is not a section. The Terms use the '## Consequences' section. |
| ADR-0061 | 3 | Read plainly, the first clause has already fired: the 2026-09-28 erratum says the `pending_transition` schema shipped in core 2.27.1. The trigger has no date mention, so the Terms class it judge, not due. |
| ADR-0068 | 1 | 'ACP v1' names a protocol version, so the plain reading agrees with class version. The trigger does not depend on a version being reached, though: it fires if v1 itself is redefined. |
| ADR-0070 | 5 | Trigger form: the 'Revisit if' rest is empty and the next line is blank, so the trigger is the '- ' and indented lines after it. They are joined verbatim: the leading '- ' is kept and so are the continuation indents, which leaves three spaces at each join. The Decision summary has a different two-clause 'Revisit if'; the Terms ignore it. |
| ADR-0070 | 1 | Version: the text says 'git ≥2.5'. '≥' is not one of the allowed prefixes, so the mention is '2.5' alone; the plain reading is a minimum git version. '`:162-165`' has no dots, so it is not a version, and 162 and 165 are outside 1900–2099, so they are not dates. |
| ADR-0070 | 3 | Check files: read plainly, `plan.md` is docs/specs/local-scope-install/plan.md (named in References), `info/exclude` is the git-internal .git/info/exclude, and `install.py` is the engine's install module. The Terms mark all three unlocated because their first segment is not an entry directly under the root. |
| ADR-0072 | 1 | The ADR has a '## Verification' section but no '## Confirmation' section, so the Terms count it as having no Confirmation. |
| ADR-0073 | 1 | The trigger text also takes in the 'Reverse the decision if' sentences on the following lines, which the plain reading treats as a separate list. 'six months' is not a date form. The ADR says the review is 'scheduled rather than event-driven', but the trigger has no date mention, so the Terms do not class it scheduled. |
| ADR-0075 | 1 | The signal text stops at the '- **Owner:**' line. The second mentions of `tools/` and `packages/agentbundle/tests/` after it, and the `docs/rfc/0082-notes/` link, are outside the signal text. |
| ADR-0076 | 1 | `spec.md` / `plan.md` in the Signal are generic artifact names, not repository paths. The Terms make them unlocated candidates, which matches the plain reading that they are not checkable file citations, so this is not a defect. |
| ADR-0076 | 1 | The Decision summary carries a `- **Revisit if:**` line too, but only the Consequences line counts. The two texts are the same here. |
| ADR-0078 | 1 | Generic `spec.md` / `plan.md` names are treated as unlocated candidates. The plain reading agrees that they cite no specific file. |
| ADR-0079 | 1 | Errata dated 2026-08-12 say Confirmation is satisfied and cite `docs/specs/claude-plugin-hook-parity/publish-control-evidence.json`. That text is outside the Confirmation section, so it is not signal text and creates no item. |
| ADR-0081 | 1 | The Consequences trigger is longer than the Decision summary's `Revisit if`. The Terms use the Consequences one. |
| ADR-0082 | 1 | The Consequences trigger differs from the Decision summary trigger, which mentions an external capture service. The Terms take the Consequences line. |
| ADR-0083 | 1 | The record has no `## Confirmation` section. Its body names pinned versions (`mermaid@11.16.1`, `lodash@4.17.11`), but none appear in the trigger text, so the class is judge, not version. 'j695' in the GHSA id is not a bare year: it touches a letter. |
| ADR-0084 | 5 | The trigger is a `- **Revisit if:**` bullet. Its continuation line starts with two spaces. I joined the lines with one space after dropping the indent; if the indent is kept, the join holds extra spaces. |
| ADR-0084 | 1 | A body line mentions 'the `Revisit if` trigger' but does not start with the marker, so it is not the trigger line. |
| ADR-0084 | 1 | `bandit` in the Signal is not a candidate: no '/' and no extension. |
| ADR-0086 | 1 | No `## Confirmation` section. The trigger is on the last lines of the file, so it ends at EOF rather than at a blank line. |
| ADR-0087 | 1 | No `## Confirmation` section. The body names 'git 2.50.1', but it is not in the trigger, so the class is not version. |
| ADR-0088 | 1 | No `## Confirmation` section. |
| ADR-0089 | 4 | Stale citation: the plain reading is that this eval moved or the pack was renamed, since `.agents/skills/new-rfc/evals/evals.json` exists in the listing. The Terms judge the path as written, so it is `missing`. This is a stale record, not a health defect. |
| ADR-0090 | 1 | '1.0.0' and '1.1.0' appear in Context and Alternatives but not in the trigger, so they do not make the class version. |
| ADR-0091 | 1 | Signal backtick spans `components-only`, `unsupported` and `runtime-verified` have no '/' and no extension, so they are not candidates. |
| ADR-0094 | 1 | Signal text stops at the `**Owner` line, so the `**Residual:**` bullet's `tools/repo/worktree_hygiene.py` is not a signal item. `make lint-editable-install` holds whitespace, so it is not a candidate. |
| ADR-0096 | 1 | 'GNU Make 3.81' is in Alternatives, not the trigger, so the class is not version. |
| ADR-0100 | 1 | The Decision summary trigger lists five numbered conditions, including the N/N−1 support window 'expires', and differs from the Consequences trigger. The Terms take the Consequences line. |
| ADR-0100 | 1 | The `**Revisit trigger:**` lines in Decision subsections do not count as trigger text. |
| ADR-0100 | 3 | A '2026-08-28 Erratum' says one per-decision trigger has already fired. That is a plain-reading 'due' signal, but its date is not in the trigger text, so the class is judge. |
| ADR-0100 | 1 | '0.4' and '0.5' are versions in D10, outside the trigger. |
| ADR-0106 | 1 | `.git` in the Signal is a repository-spelling suffix the identity tests exercise, not a check file; the Terms still make it a path candidate (ends with '.' and 1-5 letters), and it resolves to the root `.git` file, so it is reported present. |
| ADR-0108 | 2 | 2026-09-10 is the date a trigger already fired and was answered, not a revisit deadline; a plain reading finds nothing overdue, but the Terms class any passed date mention as `due`. |
| ADR-0108 | 3 | `scripts/` plainly means the `new-spec` skill's own scripts directory, not a root path; under the Terms it is unlocated. |
| ADR-0112 | 3 | `build_gate_chain.py` plainly names tools/repo/build_gate_chain.py (cited with that path elsewhere in the ADR); under the Terms the bare name is unlocated, not checked. |
| ADR-0116 | 1 | The backticked link text and the link target name the same dataset file; plain reading sees one present file, but the Terms give two signal items, one unlocated (backtick, as written) and one present (link, joined to docs/adr). |
| ADR-0117 | 1 | `lint-adr-shape.py docs/adr` plainly names the lint script, but the span holds whitespace so it is not a path candidate. |
| ADR-0120 | 3 | `semantic-surface-resolution.v1` plainly carries a contract version (v1), but `v1` is preceded by '.', so neither version form matches; the Terms class it `judge`, not `version`. |
| ADR-0126 | 1 | The Consequences trigger (line 112) is used, not the summary line (line 20), which words it differently ('the split forces' vs 'a forced split produces'). |
| ADR-0126 | 5 | The continuation line keeps its two leading spaces because the Terms only strip surrounding whitespace from the first line, so the joined text has three spaces before 'halves'. |
| ADR-0126 | 3 | `SKILL.md` and `pack.toml` are generic per-pack names that a plain reading would resolve inside each pack; the Terms class them as unlocated. |
| ADR-0126 | 1 | `work-intake` is not a candidate (no '/' and no extension). |
| ADR-0127 | 1 | The paragraph after the Owner line (that no lint exists yet) and the References paths are outside the signal text, so the signal yields no items. |
| ADR-0128 | 1 | The signal also names a 'construction test' and a 'handoff corpus test' with no paths, so they yield no candidates. |
| ADR-0131 | 1 | The version is read as '2.14.0', not '>=2.14.0': the '>=' prefix is preceded by the letter 'T' of 'PyJWT', so a prefixed match fails, and the bare match starts after '=' and is allowed. |
| ADR-0131 | 1 | The trigger comes from the Consequences section (4 clauses), not the summary (3 clauses). |
| ADR-0131 | 1 | The signal text runs on through the '- **Residual:**' bullet up to '- **Owner:**', because only Mode, Signal or Owner end it. |
| ADR-0131 | 1 | `2.9.0` and `2.14.0` are version numbers, not paths, but the Terms make them unlocated path candidates. |
| ADR-0131 | 1 | `fixed_in` is not a candidate. |
| ADR-0132 | 1 | The Consequences trigger differs from the summary one ('more than three dispositions…'); the Terms take Consequences. |
| ADR-0132 | 1 | The real assertions, including `tests/roster/`, are in the paragraph after the Owner line, which is outside the signal text, so it yields no items. |
| ADR-0133 | 1 | `tools/test-run-pip-audit-gate.py` appears only in the paragraph after Owner, so it is not signal text. |
| ADR-0133 | 1 | `ACTION:` is not a candidate (it starts with a URI scheme and has no '/' or extension). |
| ADR-0139 | 5 | The continuation lines keep their two leading spaces (same Term reading as ADR-0126). |
| ADR-0140 | 1 | '0107' in 'RFC-0107' touches '-', and 107 is outside 1900–2099, so it is no date mention. |
| ADR-0143 | 1 | The signal is a nested bullet list with no backticks or links; `pages.yml` sits on the Owner line, outside the signal text. |
| ADR-0144 | 1 | `review-report.v1` is a record-schema name, not a file, but it is a candidate under the Terms. |
| ADR-0144 | 3 | `work-supervisor.py` really lives under the work-loop skill's `scripts/`; the Terms do not resolve it, so it is unlocated. |
| ADR-0146 | 3 | The span `tools/run-pip-audit-gate.py tools/requirements-sast.txt` contains whitespace, so it is no candidate; a plain reading would check both paths. |
| ADR-0146 | 3 | The summary has no Revisit line; the trigger comes from Consequences. |
| ADR-0147 | 3 | The span `tools/run-pip-audit-gate.py tools/requirements-sast.txt` contains whitespace, so it is no candidate (same as ADR-0146). |
| ADR-0148 | 1 | `Dependency receipts:` contains whitespace, so it is no candidate; `close-work` and `depends-on-headers` have no '/' or extension. |
| citations | 2 | RFC-0050's Related field says itself that 'ADR-0023 is superseded in this session', but it does not name ADR-0042 anywhere in its header (ADR-0042 first appears at line 32). By the Term it is still a header citation. Someone reading for meaning might call it an acknowledged supersession, not a stale citation. |
| citations | 1 | ADR-0061's header names ADR-0125 in its 'Superseded in part' field. That field is not 'Supersedes' or 'Supersedes in part', so the field exclusion does not apply. ADR-0061 is excluded only because the same line also names the successor ADR-0144. |
