# Orientation views

The saved report orients the reader on the whole system, then on each subsystem,
then on the physical deployment. This reference says how to fill the three
subsections of `assets/assessment.md` and where parts of the work belong.
`assess` supplies evidence and provenance; sibling skills author the visuals.

## Order and provenance

Fill **Overall architecture**, **Architecture by subsystem**, and **Physical
architecture** in that order, inside `Conceptual current state` and before the
Map checkpoint. Each ends with a `Sources checked` table: one row per source
actually read, its locator, its evidence class, and what the source could not
show. Evidence classes are defined in `references/evidence-method.md`
§ Claim calibration. A row never claims more than its source supports.

## Diagrams

Write a short diagram brief per subsection: what the diagram must show, the
evidence behind each element, and which links are observed, inferred, or
reported. Hand the brief to `architect-diagram` to author the Mermaid. Mark
links that are not observed so the reader can tell them apart, and do not hand
draw a diagram this skill has not checked. Do not edit `architect-diagram` to
fit this skill.

## Physical architecture

Take the deployment evidence from the repository: container files, manifests,
infrastructure code, and deployment documentation. Apply the identifier and
price rules in `../architect-design/references/physical-bom.md`: take each
identifier from the repository, a lock file, or a manifest, write a visible
placeholder rather than invent one, and never take a version or a price from
memory. Its rule to start from a design does not apply, because an assessment
describes what exists. When the repository has no deployment evidence, make
the first line of the subsection `not assessed` on its own, then name the
missing evidence on the next line, and leave the `Sources checked` table showing
what was searched. Do not draw components that no source shows.

## Subsystems

List a subsystem only when a source shows it as a unit with its own
responsibility. A folder is evidence about organization, not a subsystem by
definition. State what the subsystem does, what it talks to, and which source
says so.
