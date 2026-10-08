# SPDX-License-Identifier: GPL-3.0-or-later
"""Byte-preserving decoding helpers.

This module contains format logic only. It does not contain dictionary data.
"""

from __future__ import annotations

from pathlib import Path

BYTE_OFFSET = 11
TEXT_ENCODING = "latin-1"


def decode_bytes(data: bytes, offset: int = BYTE_OFFSET) -> bytes:
    """Decode a byte sequence using a modular byte offset."""
    return bytes((byte + offset) & 0xFF for byte in data)


def decode_text(data: bytes, offset: int = BYTE_OFFSET) -> str:
    """Decode source bytes and interpret the result as single-byte text."""
    return decode_bytes(data, offset=offset).decode(TEXT_ENCODING)


def read_decoded_text(source: Path) -> str:
    """Read and decode a source file without creating an intermediate file."""
    return decode_text(Path(source).read_bytes())


def decode_file(source: Path, destination: Path) -> None:
    """Decode a source file into a separate destination file.

    This helper exists for research and diagnostics. The normal converter reads
    decoded content in memory and does not create intermediate decoded files.
    The source file is never modified.
    """
    source = Path(source)
    destination = Path(destination)

    if source.resolve() == destination.resolve():
        raise ValueError("Source and destination must be different files.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(decode_bytes(source.read_bytes()))
