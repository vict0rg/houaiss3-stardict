# SPDX-License-Identifier: GPL-3.0-or-later
"""Conversion of legacy inline formatting markup to safe HTML."""

from __future__ import annotations

import html
import re

_HEX_ESCAPE = re.compile(r"^[0-9A-Fa-f]{2}$")


def _decode_hex_byte(value: str) -> str:
    try:
        return bytes([int(value, 16)]).decode("cp1252")
    except (ValueError, UnicodeDecodeError):
        return ""


def _read_control(text: str, position: int) -> tuple[str, str | None, int]:
    """Read an RTF-like control sequence after a backslash."""
    if position >= len(text):
        return "", None, position

    if text[position] == "'" and position + 2 < len(text):
        value = text[position + 1 : position + 3]
        if _HEX_ESCAPE.match(value):
            return "hex", value, position + 3

    if text[position] in r"{}\\":
        return "literal", text[position], position + 1

    start = position
    while position < len(text) and text[position].isalpha():
        position += 1

    word = text[start:position]
    sign = ""
    if position < len(text) and text[position] == "-":
        sign = "-"
        position += 1

    number_start = position
    while position < len(text) and text[position].isdigit():
        position += 1

    parameter = sign + text[number_start:position]
    if position < len(text) and text[position] == " ":
        position += 1

    return word, parameter or None, position


def _render(text: str, start: int = 0, stop_at_brace: bool = False) -> tuple[str, int]:
    output: list[str] = []
    position = start

    while position < len(text):
        char = text[position]

        if stop_at_brace and char == "}":
            return "".join(output), position + 1

        if char == "{":
            group_html, position = _render_group(text, position + 1)
            output.append(group_html)
            continue

        if char == "\\":
            control, parameter, position = _read_control(text, position + 1)

            if control == "hex" and parameter is not None:
                output.append(html.escape(_decode_hex_byte(parameter)))
            elif control == "literal" and parameter is not None:
                output.append(html.escape(parameter))
            else:
                # Standalone control words are formatting instructions and are
                # intentionally ignored here. Group-level styles are handled by
                # _render_group().
                pass
            continue

        if char == "}":
            output.append(html.escape(char))
            position += 1
            continue

        output.append(html.escape(char))
        position += 1

    return "".join(output), position


def _render_group(text: str, start: int) -> tuple[str, int]:
    position = start
    styles: list[str] = []

    while position < len(text):
        while position < len(text) and text[position].isspace():
            position += 1

        if position >= len(text) or text[position] != "\\":
            break

        control, parameter, new_position = _read_control(text, position + 1)

        if control == "b" and parameter != "0":
            styles.append("b")
        elif control == "i" and parameter != "0":
            styles.append("i")
        elif control == "super" and parameter != "0":
            styles.append("sup")
        elif control in {"f", "fs", "plain", "b", "i", "super"}:
            pass
        elif control in {"hex", "literal"}:
            # A group beginning with a literal is content, not a style control.
            break

        position = new_position

    inner_html, position = _render(text, position, stop_at_brace=True)

    for tag in reversed(styles):
        inner_html = f"<{tag}>{inner_html}</{tag}>"

    return inner_html, position


def inline_to_html(text: str) -> str:
    """Convert supported source inline markup into safe HTML.

    Unknown formatting controls are discarded rather than emitted as HTML.
    Plain text is always HTML-escaped.
    """
    rendered, _ = _render(text)
    return rendered.strip()
