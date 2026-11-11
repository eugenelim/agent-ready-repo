"""A private formatting helper with one local caller."""


def _trim_label(label: str) -> str:
    return label.strip()


def render_label(label: str) -> str:
    return f"<{_trim_label(label)}>"
