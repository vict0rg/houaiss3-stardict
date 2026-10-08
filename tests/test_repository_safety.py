# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic tests for repository safety rules."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_repository_safety.py"

SPEC = importlib.util.spec_from_file_location(
    "check_repository_safety",
    MODULE_PATH,
)
assert SPEC is not None and SPEC.loader is not None

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RepositorySafetyTests(unittest.TestCase):
    def test_safe_source_blob_is_accepted(self) -> None:
        errors = MODULE.inspect_blob(
            PurePosixPath("src/example.py"),
            b'"""Synthetic module."""\nVALUE = "synthetic"\n',
        )
        self.assertEqual(errors, [])

    def test_forbidden_dictionary_extension_is_rejected(self) -> None:
        errors = MODULE.inspect_path(
            PurePosixPath("artifacts/example.dict")
        )
        self.assertTrue(errors)

    def test_forbidden_data_directory_is_rejected(self) -> None:
        errors = MODULE.inspect_path(
            PurePosixPath("data/example.txt")
        )
        self.assertTrue(errors)

    def test_source_style_filename_is_rejected_even_with_text_extension(self) -> None:
        errors = MODULE.inspect_path(
            PurePosixPath("notes/deah001.txt")
        )
        self.assertTrue(errors)

    def test_generated_audit_filename_is_rejected(self) -> None:
        errors = MODULE.inspect_path(
            PurePosixPath("notes/example-audit.txt")
        )
        self.assertTrue(errors)

    def test_binary_signature_is_rejected_under_safe_extension(self) -> None:
        errors = MODULE.inspect_blob(
            PurePosixPath("docs/example.txt"),
            b"\x89PNG\r\n\x1a\nSYNTHETIC",
        )
        self.assertTrue(
            any("PNG" in error for error in errors)
        )

    def test_nul_byte_is_rejected(self) -> None:
        errors = MODULE.inspect_blob(
            PurePosixPath("docs/example.txt"),
            b"SYNTHETIC\x00CONTENT",
        )
        self.assertTrue(
            any("NUL" in error for error in errors)
        )

    def test_large_blob_is_rejected(self) -> None:
        errors = MODULE.inspect_blob(
            PurePosixPath("docs/example.txt"),
            b"",
            declared_size=MODULE.MAX_INDEXED_BLOB_SIZE + 1,
        )
        self.assertTrue(
            any("large" in error for error in errors)
        )

    def test_source_like_lexical_stream_is_rejected(self) -> None:
        lines = []

        for number in range(20):
            lines.extend(
                [
                    f"*synthetic-{number}",
                    "C01|n.|synthetic noun",
                    "A0",
                    "-1",
                    ":synthetic definition",
                    "<synthetic example",
                ]
            )

        blob = ("\n".join(lines) + "\n").encode("utf-8")
        errors = MODULE.inspect_blob(
            PurePosixPath("docs/example.txt"),
            blob,
        )
        self.assertTrue(
            any("lexical record stream" in error for error in errors)
        )

    def test_dictionary_index_like_text_is_rejected(self) -> None:
        blob = (
            "\n".join(
                f"synthetic-{number};{number};0;p;"
                for number in range(100)
            )
            + "\n"
        ).encode("utf-8")

        errors = MODULE.inspect_blob(
            PurePosixPath("docs/example.txt"),
            blob,
        )
        self.assertTrue(
            any("dictionary-index-like" in error for error in errors)
        )


if __name__ == "__main__":
    unittest.main()
