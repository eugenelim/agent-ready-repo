# Delivery brief: Rename one CLI flag

- **Status:** Draft
- **Owner:** CLI maintainers
- **Source:** repository request

## Outcome

Rename the `--old-name` flag to `--new-name` and update its reference page.
The CLI and documentation are owned by one team, ship in one repository and
release, and require no cross-team or cross-slice coordination.

## In scope

- Change the single CLI flag.
- Update the reference page in the same delivery slice.

## Non-goals

- Change command behavior.
- Add a migration service.

## Constraints

Keep the existing compatibility alias for one release.

## Assumptions and risks

- The CLI and reference edit ship together.
- Future adopters might eventually want remote configuration, analytics, and
  an administration dashboard.

## Spec map

| Candidate slice | State |
| --- | --- |
| Rename the flag and update its reference page | proposed |
| Add remote configuration synchronization | proposed |
| Add flag-usage analytics | proposed |
| Add an administration dashboard | proposed |

## Deferred scope

None. All candidate slices are included so later teams do not need to reopen
the brief.

## Materialization

Create this brief now and open every listed spec before confirming which
future capabilities are actually needed.
