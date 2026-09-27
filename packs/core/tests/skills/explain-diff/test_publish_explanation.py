import base64
import hashlib
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest

CORE_ROOT = Path(__file__).resolve().parents[3]
PUBLISHER = CORE_ROOT / ".apm/skills/explain-diff/scripts/publish_explanation.py"
EXPECTED_RUNTIME = """(()=>{for(const q of document.querySelectorAll('[data-quiz-question]')){const b=q.querySelector('[data-quiz-check]'),f=q.querySelector('[data-quiz-feedback]'),r=q.dataset.quizRationale;b.addEventListener('click',()=>{const s=q.querySelector('input[type=\"radio\"]:checked'),ok=!!s&&s.dataset.correct==='true';q.dataset.state=s?(ok?'correct':'incorrect'):'unanswered';f.textContent=s?(ok?'Correct. ':'Not yet. ')+r:'Choose an answer first.';});}})();"""


def _quiz() -> str:
    """Return five complete native-control quiz questions."""
    questions = []
    for number in range(1, 6):
        option_items = []
        for letter in "abcd":
            correct = ' data-correct="true"' if letter == "a" else ""
            option_items.append(
                f'<label><input type="radio" name="q{number}" value="{letter}"'
                f'{correct}> Option {letter.upper()}</label>'
            )
        options = "".join(option_items)
        questions.append(
            f'<fieldset data-quiz-question data-quiz-rationale="The boundary keeps design '
            f'flexible while question {number} remains safe."><legend>Question {number}?</legend>'
            f'{options}<button type="button" data-quiz-check>Check answer</button>'
            '<p data-quiz-feedback aria-live="polite"></p></fieldset>'
        )
    return "".join(questions)


def _page(*, marker: str = "architecture", css: str = "") -> str:
    """Return a minimal valid, independently styled explanation draft."""
    return f"""<!doctype html>
<html lang="en"><head><!-- EXPLAIN_DIFF_CSP -->
<title>{marker} lesson</title>
<style>
* {{ box-sizing: border-box; }}
body {{ margin: 0; overflow-wrap: anywhere; }}
pre {{ white-space: pre; overflow: auto; }}
a:focus-visible, button:focus-visible, input:focus-visible {{ outline: 3px solid currentColor; }}
@media (max-width: 40rem) {{ main {{ display: block; }} }}
@media (prefers-reduced-motion: reduce) {{ * {{ scroll-behavior: auto !important; }} }}
{css}
</style></head><body>
<a href="#main">Skip to explanation</a>
<header><h1>{marker} change</h1></header>
<nav aria-label="Lesson"><a href="#background">Background</a><a href="#intuition">Intuition</a><a href="#code">Code</a><a href="#quiz">Quiz</a></nav>
<main id="main">
<section id="background" data-explain-role="background"><h2>Background</h2><p data-evidence="observed">Observed behavior.</p></section>
<article id="intuition" data-explain-role="intuition"><h2>Intuition</h2><p data-evidence="inference">A bounded inference.</p></article>
<section id="code" data-explain-role="code"><h2>Code</h2><pre><code>return value
</code></pre></section>
<section id="quiz" data-explain-role="quiz"><h2>Quiz</h2>{_quiz()}</section>
</main><!-- EXPLAIN_DIFF_RUNTIME --></body></html>"""


def _run(
    tmp_path: Path,
    draft: str | bytes,
    *,
    input_name: str = "draft.html",
    output_name: str = "lesson.html",
) -> subprocess.CompletedProcess[str]:
    """Invoke the public publisher CLI inside one approved root."""
    input_path = tmp_path / input_name
    data = draft.encode("utf-8") if isinstance(draft, str) else draft
    input_path.write_bytes(data)
    return _invoke(tmp_path, input_name, output_name)


def _invoke(
    tmp_path: Path, input_name: str, output_name: str = "lesson.html"
) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI without pre-resolving an untrusted input locator."""
    return subprocess.run(
        [
            sys.executable,
            str(PUBLISHER),
            "--input-root",
            str(tmp_path),
            "--input",
            input_name,
            "--output-root",
            str(tmp_path),
            "--output-name",
            output_name,
        ],
        check=False,
        capture_output=True,
        text=True,
    )


# STUB: AC-0003, AC-0007, AC-0008
def test_publisher_injects_only_the_fixed_runtime_and_matching_csp(tmp_path: Path) -> None:
    """A valid draft preserves its design and receives only trusted runtime bytes."""
    completed = _run(tmp_path, _page(css=".architecture { display: grid; }"))
    assert completed.returncode == 0, completed.stderr
    output_path = Path(completed.stdout.strip())
    rendered = output_path.read_text(encoding="utf-8")
    digest = base64.b64encode(hashlib.sha256(EXPECTED_RUNTIME.encode()).digest()).decode()
    assert output_path == tmp_path / "lesson.html"
    assert f"<script>{EXPECTED_RUNTIME}</script>" in rendered
    assert f"script-src 'sha256-{digest}'" in rendered
    assert "default-src 'none'" in rendered
    assert "EXPLAIN_DIFF_" not in rendered
    assert ".architecture { display: grid; }" in rendered


# STUB: AC-0003
@pytest.mark.parametrize(
    ("draft", "message"),
    # Explicit ids, not generated ones: pytest exports the node id as
    # PYTEST_CURRENT_TEST, the child inherits it, and a generated id carrying the
    # megabyte draft pushes the subprocess environment past ARG_MAX.
    [
        pytest.param(b"{" + b" " * 1_048_576, "1,048,576 bytes", id="oversize"),
        pytest.param(b"\xff", "UTF-8", id="undecodable"),
    ],
)
def test_publisher_rejects_size_and_encoding_before_output(
    tmp_path: Path, draft: bytes, message: str
) -> None:
    """Byte and decoding limits fail through the concise refusal channel."""
    completed = _run(tmp_path, draft)
    assert completed.returncode != 0
    assert message in completed.stderr
    assert not (tmp_path / "lesson.html").exists()


# STUB: AC-0003
def test_publisher_accepts_valid_draft_at_exact_input_limit(tmp_path: Path) -> None:
    """The declared byte ceiling is inclusive; only a larger draft is refused."""
    draft = _page()
    comment_overhead = len("/**/")
    padding = 1_048_576 - len(draft.encode("utf-8")) - comment_overhead
    assert padding > 0
    draft = draft.replace("</style>", f"/*{' ' * padding}*/</style>", 1)
    assert len(draft.encode("utf-8")) == 1_048_576

    completed = _run(tmp_path, draft)

    assert completed.returncode == 0, completed.stderr
    assert (tmp_path / "lesson.html").is_file()


# STUB: AC-0004, AC-0005
@pytest.mark.parametrize(
    "mutate",
    [
        lambda page: page.replace("<!doctype html>", ""),
        lambda page: page.replace('<html lang="en">', "<html>"),
        lambda page: page.replace("<h1>architecture change</h1>", ""),
        lambda page: page.replace('id="background"', 'id="code"'),
        lambda page: page.replace('href="#background"', 'href="#missing"'),
        lambda page: page.replace('data-explain-role="intuition"', 'data-explain-role="background"'),
        lambda page: page.replace("<h2>Code</h2>", "<h4>Code</h4>"),
        lambda page: page.replace("<pre><code>", "<pre><span>"),
    ],
)
def test_publisher_rejects_broken_document_and_teaching_structure(
    tmp_path: Path, mutate: object
) -> None:
    """Document, heading, ID, fragment, code, role, and TOC defects fail closed."""
    completed = _run(tmp_path, mutate(_page()))  # type: ignore[operator]
    assert completed.returncode != 0
    assert "invalid document" in completed.stderr.lower()
    assert not (tmp_path / "lesson.html").exists()


# STUB: AC-0006
@pytest.mark.parametrize(
    "injection",
    [
        "<script>alert(1)</script>",
        '<p onclick="alert(1)">event</p>',
        '<p style="color:red">style</p>',
        '<a href="https://example.invalid">external</a>',
        '<a href="https://example.invalid" href="#background">duplicate</a>',
        '<form action="#"><input></form>',
        '<svg><use href="#x"></use></svg>',
        '<img src="data:image/png;base64,AA==" alt="x">',
        '<meta http-equiv="Content-Security-Policy" content="default-src *">',
    ],
)
def test_publisher_rejects_active_or_external_html(tmp_path: Path, injection: str) -> None:
    """Untrusted markup cannot add executable or request-bearing capability."""
    completed = _run(tmp_path, _page().replace("</main>", f"{injection}</main>"))
    assert completed.returncode != 0
    assert "disallowed html" in completed.stderr.lower()
    assert not (tmp_path / "lesson.html").exists()


# STUB: AC-0007
@pytest.mark.parametrize(
    "css",
    [
        r".x { color: r\65 d; }",
        ".x { background: url(x); }",
        "@import 'x';",
        "@font-face { font-family: x; src: local(x); }",
        ".x { background: image-set('x' 1x); }",
        ".x { width: expression(alert(1)); }",
        ".x { -moz-binding: url(x); }",
    ],
)
def test_publisher_rejects_forbidden_css_capabilities(tmp_path: Path, css: str) -> None:
    """CSS obfuscation, resource loading, and legacy execution fail closed."""
    completed = _run(tmp_path, _page(css=css))
    assert completed.returncode != 0
    assert "disallowed css" in completed.stderr.lower()
    assert not (tmp_path / "lesson.html").exists()


# STUB: AC-0008
@pytest.mark.parametrize(
    "draft",
    [
        _page().replace("<!-- EXPLAIN_DIFF_CSP -->", ""),
        _page().replace("<!-- EXPLAIN_DIFF_RUNTIME -->", ""),
        _page().replace("<!-- EXPLAIN_DIFF_CSP -->", "<title>x</title><!-- EXPLAIN_DIFF_CSP -->"),
        _page().replace("<!-- EXPLAIN_DIFF_RUNTIME -->", "<!-- EXPLAIN_DIFF_RUNTIME --><p>late</p>"),
        _page().replace("<pre><code>", "<pre><code><!-- EXPLAIN_DIFF_RUNTIME -->"),
    ],
)
def test_publisher_rejects_missing_duplicate_or_misplaced_markers(
    tmp_path: Path, draft: str
) -> None:
    """Trusted injection seams have one exact structural location."""
    completed = _run(tmp_path, draft)
    assert completed.returncode != 0
    assert "placeholder" in completed.stderr.lower()
    assert not (tmp_path / "lesson.html").exists()


# STUB: AC-0009, AC-0010
def test_publisher_rejects_malformed_quiz_and_missing_css_floors(tmp_path: Path) -> None:
    """Native controls, feedback, responsive, focus, motion, and code floors are required."""
    bad_quiz = _page().replace('aria-live="polite"', 'aria-live="off"', 1)
    missing_rationale = _page().replace(
        ' data-quiz-rationale="The boundary keeps design flexible while question 1 remains safe."',
        "",
        1,
    )
    blank_rationale = _page().replace(
        'data-quiz-rationale="The boundary keeps design flexible while question 1 remains safe."',
        'data-quiz-rationale=""',
        1,
    )
    missing_legend = _page().replace("<legend>Question 1?</legend>", "", 1)
    bad_css = _page().replace(":focus-visible", ":focus")
    for draft in (
        bad_quiz,
        missing_rationale,
        blank_rationale,
        missing_legend,
        bad_css,
    ):
        completed = _run(tmp_path, draft, output_name=f"lesson-{len(draft)}.html")
        assert completed.returncode != 0
        assert "required" in completed.stderr.lower()


# STUB: AC-0009
@pytest.mark.parametrize(
    "draft",
    [
        _page().replace('name="q1"', 'name="q1-other"', 1),
        _page().replace('name="q2"', 'name="q1"'),
    ],
)
def test_publisher_rejects_radio_names_that_split_or_join_question_groups(
    tmp_path: Path, draft: str
) -> None:
    """Each question owns one non-empty radio group distinct from every other question."""
    completed = _run(tmp_path, draft)
    assert completed.returncode != 0
    assert "required quiz" in completed.stderr.lower()
    assert not (tmp_path / "lesson.html").exists()


# STUB: AC-0011
def test_publisher_default_output_is_dated_collision_resistant_and_owner_only(
    tmp_path: Path,
) -> None:
    """Omitting destination flags publishes two distinct files under OS temp."""
    input_path = tmp_path / "draft.html"
    input_path.write_text(_page(), encoding="utf-8")
    environment = os.environ.copy()
    environment["TMPDIR"] = str(tmp_path)
    outputs = []
    for _ in range(2):
        completed = subprocess.run(
            [
                sys.executable,
                str(PUBLISHER),
                "--input-root",
                str(tmp_path),
                "--input",
                input_path.name,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
        assert completed.returncode == 0, completed.stderr
        output_path = Path(completed.stdout.strip())
        assert output_path.is_absolute()
        assert output_path.parent.resolve() == tmp_path.resolve()
        assert re.fullmatch(r"explain-diff-\d{4}-\d{2}-\d{2}-[a-f0-9]+\.html", output_path.name)
        if os.name == "posix":
            assert stat.S_IMODE(output_path.stat().st_mode) == 0o600
        outputs.append(output_path)
    assert outputs[0] != outputs[1]


# STUB: AC-0011
def test_publisher_rejects_unconfined_symlinked_and_nonregular_input(
    tmp_path: Path,
) -> None:
    """Every input locator is confined and regular before draft bytes are read."""
    outside = tmp_path.parent / f"{tmp_path.name}-outside.html"
    outside.write_text(_page(), encoding="utf-8")
    directory = tmp_path / "directory"
    directory.mkdir()
    symlink = tmp_path / "linked.html"
    symlink.symlink_to(outside)
    attempts = (
        "../" + outside.name,
        str(outside.resolve()),
        symlink.name,
        directory.name,
    )
    for index, input_name in enumerate(attempts):
        output_name = f"unconfined-{index}.html"
        completed = _invoke(tmp_path, input_name, output_name)
        assert completed.returncode != 0
        assert "input" in completed.stderr.lower()
        assert not (tmp_path / output_name).exists()


# STUB: AC-0011
def test_publisher_confines_and_atomically_publishes_owner_only(tmp_path: Path) -> None:
    """Traversal and overwrite fail; accepted POSIX output remains mode 0600."""
    escaped = _run(tmp_path, _page(), output_name="../escape.html")
    assert escaped.returncode != 0
    existing = tmp_path / "lesson.html"
    existing.write_text("sentinel", encoding="utf-8")
    refused = _run(tmp_path, _page())
    assert refused.returncode != 0
    assert existing.read_text(encoding="utf-8") == "sentinel"
    existing.unlink()
    accepted = _run(tmp_path, _page())
    assert accepted.returncode == 0, accepted.stderr
    if os.name == "posix":
        assert stat.S_IMODE(existing.stat().st_mode) == 0o600
    assert not list(tmp_path.glob(".explain-diff-*.tmp"))


# STUB: AC-0014
def test_publisher_preserves_three_independent_page_designs(tmp_path: Path) -> None:
    """Publication does not collapse different authored structures or CSS."""
    drafts = [
        _page(marker="architecture", css=".architecture-map { display: grid; }"),
        _page(marker="data flow", css=".signal-path { display: flex; }"),
        _page(marker="fail closed", css=".decision-state { border-inline-start: 1rem solid; }"),
    ]
    rendered = []
    for index, draft in enumerate(drafts):
        completed = _run(tmp_path, draft, output_name=f"lesson-{index}.html")
        assert completed.returncode == 0, completed.stderr
        rendered.append((tmp_path / f"lesson-{index}.html").read_text(encoding="utf-8"))
    assert len({hashlib.sha256(page.encode()).digest() for page in rendered}) == 3
    assert all(token in page for token, page in zip(
        ("architecture-map", "signal-path", "decision-state"), rendered, strict=True
    ))


# STUB: AC-0015
@pytest.mark.parametrize(
    ("literal", "category"),
    [
        ("Bearer abcdefghijklmnopqrstuvwxyz012345", "credential"),
        ('api_key = "abcd1234abcd1234abcd1234abcd1234"', "credential"),
        ("person@example.invalid", "email"),
        ("/Users/private-user/project", "user-home path"),
        ("x7Qm9P2vL4nR8sT1uW3yZ6aB0cD5eF7g", "high-entropy token"),
    ],
)
def test_publisher_refuses_sensitive_literals_without_echo(
    tmp_path: Path, literal: str, category: str
) -> None:
    """Sensitive values fail before output resolution and never enter errors."""
    completed = _run(tmp_path, _page().replace("Observed behavior.", literal))
    assert completed.returncode != 0
    assert category in completed.stderr.lower()
    assert literal not in completed.stderr
    assert not (tmp_path / "lesson.html").exists()
