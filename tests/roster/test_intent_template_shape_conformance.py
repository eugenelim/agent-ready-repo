"""`frame-intent`'s template satisfies the intent metadata shape contract.

Covers the cross-pack half of T7 in
`docs/specs/intent-metadata-shape-contract/plan.md`. It reads
`packs/product-engineering/` and `packs/core/` in one assertion, so it cannot
live in either pack's suite — a pack test may not read above its own pack, and
the validator and the template ship in different packs. `tests/AGENTS.md` puts
a repository-level assertion here.

The core pack's own half — the `intake-intent` renderer against the same
validator — is in
`packs/core/tests/skills/intake-intent/test_intent_template_conformance.py`.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = (
    ROOT
    / "packs"
    / "product-engineering"
    / ".apm"
    / "skills"
    / "frame-intent"
    / "assets"
    / "intent-template.md"
)
VALIDATOR = (
    ROOT
    / "packs"
    / "core"
    / ".apm"
    / "skills"
    / "work-intake"
    / "scripts"
    / "intent_shape.py"
)

# One representative value per field the template seeds. A placeholder offering
# a choice resolves to one member of that choice; a free-text placeholder
# resolves to a plausible value.
REPRESENTATIVE = {
    "Slug": "an-example-intent",
    "Level": "feature",
    "Owner": "eugenelim",
    "Status": "Draft",
    "Kind": "outcome",
    "Scale": "app",
    "Maturity": "brownfield",
}

FIELD_LINE = re.compile(r"^- \*\*([^*:]+):\*\*(.*)$")
PLACEHOLDER = re.compile(r"<[^<>]*>")


def _load_validator():
    name = "roster_core_work_intake_intent_shape"
    spec = importlib.util.spec_from_file_location(name, VALIDATOR)
    assert spec and spec.loader, VALIDATOR
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _resolve(text: str) -> str:
    """Resolve every preamble placeholder to a representative value.

    Only the part of a field line before its trailing HTML comment is touched.
    The comments themselves contain angle-bracketed examples — `Superseded by
    <slug>` among them — and rewriting those would change what the author reads
    rather than what the validator judges.
    """
    out = []
    for line in text.splitlines():
        match = FIELD_LINE.match(line)
        if not match:
            out.append(line)
            continue
        name, remainder = match.group(1).strip(), match.group(2)
        head, sep, comment = remainder.partition("<!--")
        value = REPRESENTATIVE.get(name)
        if value is not None:
            head = PLACEHOLDER.sub(value, head)
        out.append(f"- **{name}:**{head}{sep}{comment}")
    return "\n".join(out)


def test_the_resolved_frame_intent_template_satisfies_the_contract() -> None:
    """AC-0018: a template that seeds a refused shape re-dirties the corpus at
    the next admission, so the template is validated rather than trusted."""
    shape = _load_validator()
    resolved = _resolve(TEMPLATE.read_text(encoding="utf-8"))

    violations = shape.validate_live_intent(resolved)
    assert violations == [], [f"{v.field}: {v.reason}" for v in violations]


def test_the_resolved_template_also_satisfies_the_corpus_scoped_rules() -> None:
    """Both surfaces, because passing one is not passing the contract.

    `validate_live_intent` accepts a `Superseded by:` stranded beside a
    non-`Superseded` status by design — that pairing rule is corpus-scoped. A
    template seeding one would therefore pass the check above and still produce
    an intent the corpus lint refuses at the next admission, which is the exact
    failure this file exists to prevent.
    """
    shape = _load_validator()
    resolved = _resolve(TEMPLATE.read_text(encoding="utf-8"))

    slugs = shape.resolvable_slugs([resolved])
    violations = shape.validate_corpus_scoped(resolved, slugs)
    assert violations == [], [f"{v.field}: {v.reason}" for v in violations]


def test_a_template_seeding_a_stranded_pointer_would_be_caught() -> None:
    """The mutation that makes the supersession control above able to fail.

    Calling an always-clean surface on a conforming template proves nothing: the
    check passes just as well with the rule deleted. This feeds the same surface
    the template it is meant to reject — a populated `Superseded by:` beside
    `Status: Draft` — so the pair discriminates.
    """
    shape = _load_validator()
    seeded = _resolve(TEMPLATE.read_text(encoding="utf-8")).replace(
        "- **Superseded by:**", "- **Superseded by:** a-successor <!--", 1
    )
    assert shape.validate_corpus_scoped(seeded, {"a-successor"}) != []


def test_a_template_seeding_an_accepted_record_beside_draft_would_be_caught() -> None:
    """The mutation that makes the state-coherence control able to fail.

    A template seeding `Accepted:` beside `Status: Draft` would produce a corpus
    violation at the next admission; `validate_corpus_scoped` must refuse it so
    the guard discriminates rather than passing on an always-clean surface.
    """
    shape = _load_validator()
    resolved = _resolve(TEMPLATE.read_text(encoding="utf-8"))
    # Insert Accepted: into the preamble (just before the first heading).
    seeded = re.sub(
        r"(\n## )",
        "\n- **Accepted:** 2026-09-20 by eugenelim\1",
        resolved,
        count=1,
    )
    slugs = shape.resolvable_slugs([seeded])
    assert shape.validate_corpus_scoped(seeded, slugs) != []


def test_every_required_field_is_seeded_by_the_template() -> None:
    """Resolving a placeholder cannot invent a field the template omits."""
    shape = _load_validator()
    resolved = _resolve(TEMPLATE.read_text(encoding="utf-8"))
    seeded = dict(shape.read_preamble(resolved))

    for required in shape.REQUIRED_FIELDS:
        assert required in seeded, required
        assert seeded[required], required


def test_the_template_seeds_no_retired_field_name() -> None:
    shape = _load_validator()
    names = {
        name for name, _ in shape.read_preamble(TEMPLATE.read_text(encoding="utf-8"))
    }
    assert names.isdisjoint(shape.RETIRED_FIELDS), names & set(shape.RETIRED_FIELDS)


def test_the_progress_fields_are_seeded_and_read_as_absent() -> None:
    """Each is seeded as a comment with no value, which the contract treats as
    absent rather than malformed — so an author who has not reached that stage
    deletes nothing and asserts nothing."""
    shape = _load_validator()
    resolved = _resolve(TEMPLATE.read_text(encoding="utf-8"))
    raw = TEMPLATE.read_text(encoding="utf-8")

    for field in shape.PROGRESS_FIELDS:
        assert f"- **{field}:**" in raw, field
    state = shape.progress_state(resolved)
    for field in shape.PROGRESS_FIELDS:
        assert state[field] == shape.PROGRESS_ABSENT, (field, state[field])


def test_the_unresolved_template_asset_is_not_corpus_input() -> None:
    """AC-0018 reaches the rendered artifact, not the asset.

    The asset carries unresolved placeholders and would be refused; it is not
    in `docs/product/intents/`, so the corpus lint never sees it.
    """
    assert TEMPLATE.is_file()
    assert "docs/product/intents" not in str(TEMPLATE.relative_to(ROOT).as_posix())
    intents = ROOT / "docs" / "product" / "intents"
    assert TEMPLATE.parent != intents
