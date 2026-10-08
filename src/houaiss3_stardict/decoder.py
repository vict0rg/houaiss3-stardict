# SPDX-License-Identifier: GPL-3.0-or-later
"""Byte-preserving decoding helpers.

This module contains format logic only. It does not contain dictionary data.
"""

from pathlib import Path

BYTE_OFFSET = 11


def decode_bytes(data: bytes, offset: int = BYTE_OFFSET) -> bytes:
    """Decode a byte sequence using a modular byte offset."""
    return bytes((byte + offset) & 0xFF for byte in data)


def decode_file(source: Path, destination: Path) -> None:
    """Decode a source file into a separate destination file.

    The source file is never modified.
    """
    source = Path(source)
    destination = Path(destination)

    if source.resolve() == destination.resolve():
        raise ValueError("Source and destination must be different files.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(decode_bytes(source.read_bytes()))
