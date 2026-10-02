from isolated_helper import render_label


def test_render_label_trims_outer_whitespace() -> None:
    assert render_label("  ready  ") == "<ready>"
