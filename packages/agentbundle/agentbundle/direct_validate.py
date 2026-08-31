"""Direct-source validation output: the AC21 JSON envelope and its text form.

Kept beside the direct modules rather than inside ``commands/validate.py`` so
the catalogue route's bytes cannot move: that command's existing text output and
exit codes are untouched, and this module is reached only when a directory
carries no ``pack.toml``.
"""

from __future__ import annotations

import json

from agentbundle.direct_source import DirectAdmission

# AC21: the direct route has no catalogue, so its `catalogue_schema_version`
# default is 1 rather than a value read from a catalogue that is not there.
DIRECT_CATALOGUE_SCHEMA_VERSION = 1
DIRECT_SCHEMA_VERSION = 1


def _agentbundle_version() -> str:
    """Report the running version through the same accessor the linter uses."""

    from agentbundle import __version__

    return __version__


def direct_validation_summary(admission: DirectAdmission) -> dict[str, object]:
    """AC21's summary: the shape and the skills that were selected."""

    classification = admission.classification
    if classification is None:
        return {"shape": None, "selected_skills": []}
    return {
        "shape": classification.shape,
        "selected_skills": sorted(skill.name for skill in classification.skills),
    }


def render_direct_validation_json(admission: DirectAdmission) -> str:
    """Render the established envelope keys plus `summary`, deterministically."""

    payload = {
        "schema_version": DIRECT_SCHEMA_VERSION,
        "command": "validate",
        "operation": "direct",
        "agentbundle_version": _agentbundle_version(),
        "catalogue_schema_version": DIRECT_CATALOGUE_SCHEMA_VERSION,
        "ok": admission.ok,
        "diagnostics": [
            {
                "code": diagnostic.code,
                "severity": diagnostic.severity.name,
                "pack": diagnostic.pack,
                "path": diagnostic.path,
                "line": diagnostic.line,
                "col": diagnostic.col,
                "message": diagnostic.message,
                "remediation": diagnostic.remediation,
            }
            for diagnostic in admission.diagnostics
        ],
        "summary": direct_validation_summary(admission),
    }
    return json.dumps(payload, sort_keys=True, indent=2)


def render_direct_validation_text(admission: DirectAdmission) -> str:
    """Render the same result for a terminal."""

    summary = direct_validation_summary(admission)
    if admission.ok:
        skills = ", ".join(summary["selected_skills"]) or "none"  # type: ignore[arg-type]
        return f"ok: direct source valid (shape {summary['shape']}; skills: {skills})"
    # `path`, `message`, and `remediation` are escaped by
    # `make_direct_diagnostic` at construction, so this renderer cannot print a
    # raw bidi override or ANSI sequence even by forgetting to ask — which is
    # what happened when each surface escaped for itself.
    lines = [
        f"  [{diagnostic.code}] {diagnostic.severity.name} {diagnostic.path or ''}".rstrip()
        for diagnostic in admission.diagnostics
    ]
    for diagnostic in admission.diagnostics:
        lines.append(f"    {diagnostic.message}")
        if diagnostic.remediation:
            lines.append(f"    → {diagnostic.remediation}")
    return "\n".join(["FAIL: direct source refused", *lines])
