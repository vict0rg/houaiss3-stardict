# SPDX-License-Identifier: GPL-3.0-or-later
"""Command-line interface."""

import argparse

from . import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="houaiss3-stardict",
        description=(
            "Educational legacy dictionary interoperability and "
            "StarDict conversion tool."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.parse_args()


if __name__ == "__main__":
    main()
