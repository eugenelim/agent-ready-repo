"""`content-design`'s template and eval harness carry the mode its skill requires.

``content-design/SKILL.md`` requires every content brief to declare
``communication_mode`` in its frontmatter and to be written to the configured
``<output_dir>``. Three surfaces have to agree for that requirement to survive
contact with an adopter: the skill that states it, the template an author
actually fills in, and the eval harness that judges whether a produced brief
met it. A template with no slot for the field, or an eval pinning one
repository's ``docs/design`` layout, lets a brief ship without the field a
downstream skill reads and lets the harness pass it anyway.

The three mode names are derived from the two surfaces that own them — every
``communication_mode: <value>`` literal in ``SKILL.md``, and the mode headings
in ``references/communication-modes.md`` — rather than restated here, so a
fourth mode added to either surface fails this test instead of silently
outranking it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = (
    ROOT / "packs" / "experience-design" / ".apm" / "skills" / "content-design"
)
SKILL_MD = SKILL_DIR / "SKILL.md"
MODES_REFERENCE = SKILL_DIR / "references" / "communication-modes.md"
TEMPLATE = SKILL_DIR / "assets" / "content-brief-template.md"
EVALS = SKILL_DIR / "evals" / "evals.json"

FIELD = "communication_mode"
ARTIFACT_PATH = "<output_dir>/content/<slug>.md"
REPO_PINNED_PATH = "docs/design/content/<slug>.md"

# Every `communication_mode: product-copy` literal in the skill, wherever it is
# stated — the routing sentence and the hand-off step both name the full set,
# and pinning one prose span would certify the span, not the vocabulary. The
# literal value is what a brief must carry, so a `<mode>` placeholder is not one.
SKILL_MODE = re.compile(rf"`{FIELD}: ([a-z][a-z-]*)`")
# `## MODE 1 — product-copy` in the reference that defines each mode.
REFERENCE_MODE = re.compile(r"^## MODE \d+ — (\S+)\s*$", re.MULTILINE)
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
PLACEHOLDER_LINE = re.compile(rf"^{FIELD}: <([^>]*)>\s*$", re.MULTILINE)
# Any content-brief artifact path an eval states, however it is rooted and
# whatever leaf it names: `<output_dir>/content/<slug>.md`, and equally a
# concrete `docs/design/content/api-quickstart.md`, which is the same drift
# wearing a different spelling.
# The trailing boundary is load-bearing: without it `…<slug>.mdx` yields the
# `.md` prefix as a match and compares equal to the required path.
BRIEF_PATH_RE = re.compile(r"[\w<>./-]*content/[\w<>.-]+\.md(?![\w.-])")
# The mode an eval case requires, as a whole token: `communication_mode: x`
# must not be satisfied by `communication_mode: x-draft`.
EVAL_MODE_RE = re.compile(rf"{FIELD}: ([a-z][a-z-]*)(?![\w.-])")


def declared_modes() -> frozenset[str]:
    """The mode vocabulary, taken from the two surfaces that own it."""
    from_skill = frozenset(SKILL_MODE.findall(SKILL_MD.read_text(encoding="utf-8")))
    from_reference = frozenset(
        REFERENCE_MODE.findall(MODES_REFERENCE.read_text(encoding="utf-8"))
    )
    assert from_skill == from_reference, (
        "the skill and its communication-modes reference disagree on the mode "
        f"vocabulary: skill={sorted(from_skill)} reference={sorted(from_reference)}"
    )
    assert len(from_skill) == 3, f"expected three modes, found {sorted(from_skill)}"
    return from_skill


def eval_case(fragment: str) -> dict:
    """The one eval case whose prompt names ``fragment``."""
    cases = json.loads(EVALS.read_text(encoding="utf-8"))["evals"]
    matching = [case for case in cases if fragment in case["prompt"]]
    assert len(matching) == 1, (
        f"expected exactly one eval case naming {fragment!r}, found {len(matching)}"
    )
    return matching[0]


def case_text(case: dict) -> str:
    return case["expected_output"] + "\n" + "\n".join(case["assertions"])


def test_template_frontmatter_declares_the_field_exactly_once() -> None:
    frontmatter = FRONTMATTER.match(TEMPLATE.read_text(encoding="utf-8"))
    assert frontmatter is not None, f"{TEMPLATE} opens with no frontmatter block"
    keys = [
        line.split(":", 1)[0].strip()
        for line in frontmatter.group(1).splitlines()
        if ":" in line
    ]
    assert keys.count(FIELD) == 1, (
        f"{TEMPLATE} frontmatter declares {FIELD} {keys.count(FIELD)} times; "
        "an author filling a duplicated key leaves the artifact ambiguous"
    )


def test_template_placeholder_admits_exactly_the_declared_modes() -> None:
    frontmatter = FRONTMATTER.match(TEMPLATE.read_text(encoding="utf-8"))
    assert frontmatter is not None
    placeholder = PLACEHOLDER_LINE.search(frontmatter.group(1))
    assert placeholder is not None, (
        f"{TEMPLATE} frontmatter carries no `{FIELD}: <...>` placeholder"
    )
    offered = frozenset(part.strip() for part in placeholder.group(1).split("|"))
    assert offered == declared_modes(), (
        f"the template offers {sorted(offered)}; the skill owns "
        f"{sorted(declared_modes())}"
    )


def test_skill_requires_the_field_on_the_artifact_it_fills_from_the_template() -> None:
    """The skill states both halves of the contract the template has to serve.

    Deliberately silent on the order of the two sentences: the obligation is
    that a brief filled from the template carries the field, and a step 4 that
    copied the template first and required the field second would satisfy it.
    """
    skill = SKILL_MD.read_text(encoding="utf-8")
    assert re.search(rf"write `{FIELD}:[^`]*` in the artifact frontmatter", skill), (
        f"{SKILL_MD} no longer requires {FIELD} in the artifact frontmatter"
    )
    assert "Copy `assets/content-brief-template.md`" in skill, (
        f"{SKILL_MD} no longer fills the brief from the shipped template, so "
        "the template's frontmatter is no longer the surface this test guards"
    )


def assert_case_requires(prompt_fragment: str, mode: str) -> None:
    """The named case requires exactly ``mode``, at the configured path.

    Equality over extracted tokens, not containment: a substring test passes on
    ``product-copy-draft``, which is not a mode the skill owns.
    """
    assert mode in declared_modes(), (
        f"{mode!r} is not one of the modes the skill owns: "
        f"{sorted(declared_modes())}"
    )
    text = case_text(eval_case(prompt_fragment))
    required = set(EVAL_MODE_RE.findall(text))
    assert required == {mode}, (
        f"the {prompt_fragment!r} eval case requires {sorted(required)}; "
        f"it should require exactly {mode!r}"
    )
    paths = set(BRIEF_PATH_RE.findall(text))
    assert paths == {ARTIFACT_PATH}, (
        f"the {prompt_fragment!r} eval case names the brief path as "
        f"{sorted(paths)}; the only form it can require is {ARTIFACT_PATH!r}"
    )


def test_acquisition_eval_expects_product_copy_at_the_configured_path() -> None:
    assert_case_requires("acquisition surface", "product-copy")


def test_api_quickstart_eval_expects_reference_documentation_at_that_path() -> None:
    assert_case_requires("API quickstart", "reference-documentation")


def test_every_brief_path_the_evals_state_is_the_configured_one() -> None:
    """Positive: each `content/<slug>.md` an eval names carries the placeholder.

    Checking only that the previous `docs/design` literal is gone would pass a
    case that keeps the placeholder and adds a second, differently-rooted
    literal beside it, so the property is stated over every path the file
    contains rather than over one string it must not.
    """
    stated = BRIEF_PATH_RE.findall(EVALS.read_text(encoding="utf-8"))
    assert stated, f"{EVALS} states no content-brief artifact path at all"
    wrong = sorted({path for path in stated if path != ARTIFACT_PATH})
    assert not wrong, (
        f"{EVALS} states the brief path as {wrong}; the skill resolves it from "
        f"the adopter's configured [design] output_dir, so {ARTIFACT_PATH} is "
        "the only form an eval can require"
    )
    assert REPO_PINNED_PATH not in EVALS.read_text(encoding="utf-8")
