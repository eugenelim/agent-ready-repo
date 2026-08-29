# Pre-EXECUTE adversarial review — adjudication

- **Run:** e0d188ee-62d1-4afa-9692-4e90eda84419, HEAD 57da9ac36
- **Reviewer role:** adversarial-reviewer (execution readiness)

## Sustained — blockers

| id | summary | seam |
| --- | --- | --- |
| B1 | T10's Done-when says the lint "imports `DIRECT_CODES`"; AC31 requires an `ast` parse "rather than importing it". An executor following the plan ships the artifact the AC forbids. | plan T10 |
| B2 | No task creates `DIRECT_CODES` or `make_direct_diagnostic`. T1 and T3 both consume registered codes and both `Depends on: none`; the only deriving task, T5, depends on T1/T2/T4/T4a. AC31's constructor-rejection behaviour has no TDD owner. | plan T1/T3/T5 |
| B3 | T3 declares it owns the bound-versus-integrity attribution mechanism and records none. `file_safety.py:100-134` raises bare `UnsafeContentError` for both; AC33 forbids message parsing. T3's own two fixtures cannot both pass under the recorded design. | plan T3 |
| B5 | `_project_direct_directory` maps exactly one level, so a normalized pack retaining `skills/<category>/<name>/` projects the **category** as the skill, contradicting AC2's leaf identity. "flatten"/"leaf" appear nowhere in plan.md. T0d records four admitted category-grouped repos, so the shape is reachable. | LLD + T4 + AC24 |
| B6 | T2's Tests omit the four code-side refusals T0b explicitly ordered (`recipes`, `runtime-dependencies`, `adaptation`, `seeds`). No other task owns AC10. | plan T2 |
| B7 | AC35's per-repository fixture table was never committed; the re-assertion trigger has fired twice (E14 shapes, E15 depth) and is unowned since T0d is resolved. | AC35 + owning task |

## Sustained — concerns and nits

| id | summary |
| --- | --- |
| C9 | **Regression-set half only.** `test_upgrade_bulk_all.py` has 0 `CatalogueError` message assertions; `test_org_bootstrap.py` has 29 and is unnamed. The "61 raise sites" figure **holds** package-wide. |
| C10 | T11's Windows executed-count cites a precedent that is an import probe, not a count mechanism; `_step` returns only a returncode. |
| C13 | AC36 requires measurement with **every** Family-2 budget at its limit; the recorded run names entries/files/total bytes only, omitting depth 12 and 500 selected skills. E15 leans on that figure. **Owner-visible either way.** |
| C14 | `claude_code.py:119-130` degrades to an empty protected set on `ConfigError`, after which `sweep_orphans` rmtrees unprotected skill dirs — so an old reader **deletes** direct skills instead of refusing 0.5 per AC12. No task mentions the sweep. |
| C16 | E14:426 and E15:434 cite "AC32's headroom rule" / "AC32's cost ceiling"; the ceiling is AC36, the corpus is AC35, and E15 withdraws the headroom basis in the same paragraph. |
| N17 | E15 opens "E11 bounds path depth at 10" but E11 was amended in place to "depth (12, per E15)" — the errata contradict each other. |
| N18 | ADR-0100:29 is grammatically garbled after the mechanical renumber. |

## Refuted

- **B4** — the *mechanism* holds (T0a cited `self_host.py:832`, a drift-message
  source map, not the renderer; `claude_code.py:202-226` copytrees with
  `ignore_absolute_symlinks`, dropping `__pycache__`). The *consequence* does not:
  `PackState.files` is populated from the **rendered** projection map and
  `count_drifted_files` iterates only recorded files, so a dropped `__pycache__`
  entry never enters the map and cannot produce non-zero footprint DRIFT. AC22
  independently forbids comparing the source digest. **The citation still needs
  fixing; the claimed harm does not exist.**
- **C8** — AC16 is built and stubbed by T4a, AC17 by T5; overlapping AC lines are
  the plan's convention throughout. Over-listing, no verification gap.
- **C11** — the AC26 sentinel residual is covered where AC26 lives: T6 sentinel
  absence + golden `state.toml`, T8 sentinel control, T9, and T11's output sweep.
- **C12** — Terms define a Collection as having **no root `pack.toml`**, so AC2's
  duplicate-leaf refusal does not bind a **direct pack** whose categories declare
  the same leaf. AC13's preimage case is reachable for that shape.

## Positive claims corroborated

- T1's fixtures are concrete; `test_trust_fallback_tls.py:96-114` is real precedent
  for the loopback-TLS carve-out, and the root conftest carries no socket fixture.
- `list_confined_regular_files`'s signature matches T3's recorded spike exactly.
- **T10a's floor verifies:** 4,119 collected at this revision (measured), 4,119 − 919
  = 3,200, and `Makefile:408` is the sole macro line to amend.

## Open indeterminates

- **C15** — module home for the four new modules. `catalogue_tooling/` places them
  inside the ADR-0056 portable-engine boundary with its own gates; top-level does
  not. AC16 lifts from `catalogue_tooling/okf_discovery.py` (pulls one way);
  Repository anchors name top-level modules (pulls the other). **Owner decision.**
- **P-E11-floors** — the interpreter patch a CI job resolves is not fixed by any
  repository file. The guard is call-time, so a below-floor runner refuses rather
  than skips; not a defect, not verifiable here.
