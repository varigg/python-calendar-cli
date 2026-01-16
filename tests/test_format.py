"""
Unit tests for format.py (pretty_print_slots, get_calendar_colors, format_event).
"""

import gtool.cli.formatters as format


def test_get_calendar_colors_assigns_colors():
    ids = ["a", "b", "c", "d", "e", "f"]
    colors = format.get_calendar_colors(ids)
    assert colors["a"] == "green"
    assert colors["b"] == "blue"
    assert colors["c"] == "magenta"
    assert colors["d"] == "cyan"
    assert colors["e"] == "yellow"
    assert colors["f"] == "green"  # wraps around


# You can add more tests for format_event and pretty_print_slots using mocks if needed.
