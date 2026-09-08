# Live adapter and client smoke evidence

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/claude-plugin-route-scope AC15](../../specs/claude-plugin-route-scope/spec.md)

## Outcome

Maintainers have dated, reproducible live-client evidence for generated adapter artifacts and client marketplace behavior, including recovery paths and stated client limitations.

## Opportunity

Documentation, generated-path, hermetic-manifest, projection, walkthrough, and simulated evidence pass, but they do not prove that the real clients load, detect, install, delist, or recover from the relevant artifacts.

## What this absorbs

### cursor-live-smoke

Documentation and generated-path checks pass, but a real Cursor tool has not loaded the generated repo/user artifacts. Run a dated Cursor IDE/CLI smoke covering skill, subagent, command, read-only reviewer behavior, and recovery. The binder-publishing decision record says `copilot`, `cursor`, and `gemini` were not installed, so those adapters are unmeasured. Unblocks when the dated Cursor smoke is recorded.

### claude-clean-room-plugin-smoke

Hermetic manifest checks pass, but the graphical Claude client has not completed the clean-profile marketplace lifecycle. Run a dated add, install, enable, discover, uninstall, and recover matrix on the current supported client, including reproducible client limitations. ADR-0072 records that a periodic or release-gated job running the real `claude` client against the published marketplace would close the CI gap. Unblocks when the dated lifecycle matrix is recorded.

### live-mock-mcp-detection-qa

Walkthrough and projection checks pass, but four skills have not exercised present, absent, sensitive, and brownfield detection through a live mock MCP tool. Add a harness that can register a stub MCP retrieval tool and record all four skills' scenarios, including architect-diagram's contradicted-edge case. The product-engineering knowledge-surfaces spec states that the session cannot inject a *live* mock MCP knowledge tool. Unblocks when the harness records every scenario.

### plugin-postmerge-marketplace-check

The PR can exercise only a local marketplace, so it cannot prove the published dist-branch client route. After publish, record real `claude plugin details` and post-delist update behavior against the published marketplace. The source authority makes the post-merge re-run a separate recorded step. Unblocks when the published-marketplace observation is recorded.

### adapt-to-project-ac4b-transcripts

Simulated evidence does not replace AC4b's real-adopter class-2/3/4 sessions and user-scope judgment rows. Record real-adopter AC4b repo-scope class-2/3/4 rows 8–16 and user and APM rows 19–34 in the existing manual-QA matrix after APM install parity. The matrix's premise that no user-scope-eligible pack ships is stale: RFC-0036 identifies the `converters` pack as user-scope-default with `allowed-scopes = ["user","repo"]`, and rows 19–28 need an updated trigger before the named live transcripts are recorded. Unblocks when APM install parity is complete and the named real-adopter sessions are recorded.

## Assumptions

- The AC4b user-scope premise has changed because `converters` ships as a user-scope-default pack; update the rows 19–28 trigger before recording the transcripts.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
