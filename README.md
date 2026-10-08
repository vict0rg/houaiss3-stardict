# houaiss3-stardict

An educational and experimental Python project for studying legacy dictionary
file interoperability and generating StarDict-compatible output from
user-supplied, lawfully obtained source files.

## Important Notice

**This repository contains source code and technical documentation only.**

It does not contain, distribute, reproduce, or provide:

- proprietary dictionary databases;
- dictionary entries or definitions;
- extracted lexical content;
- decoded dictionary datasets;
- screenshots or images from proprietary software;
- generated copies of proprietary dictionaries.

No proprietary dictionary content may be committed to this repository.

All examples and test data included here are entirely synthetic and were
created specifically for software testing.

## Purpose

The project is intended for educational, experimental, academic, and
interoperability research.

Its technical goals include:

- studying legacy file organization;
- decoding reversible byte representations;
- parsing structured lexical records;
- converting legacy formatting markup to HTML;
- preserving metadata where technically possible;
- studying index and morphology structures;
- generating StarDict-compatible output.

## What This Project Is Not

This project is not intended for hacking, unauthorized access, circumvention of
security controls, bypassing license restrictions, copyright infringement, or
redistribution of proprietary dictionary content.

Users must supply their own lawfully obtained source files and are responsible
for complying with applicable law, licenses, contracts, and third-party rights.

## Safety

Always work on copies of original files.

The software must never modify original dictionary source files in place.

The repository includes automated checks intended to reduce the risk of
accidentally committing proprietary or derived dictionary content. These checks
are safeguards, not a substitute for human review.

## Project Structure

```text
houaiss3-stardict/
├── src/
│   └── houaiss3_stardict/
│       ├── decoder.py
│       ├── parser.py
│       ├── markup.py
│       ├── morphology.py
│       ├── stardict.py
│       └── cli.py
├── tests/
│   └── synthetic/
├── docs/
├── scripts/
├── .githooks/
└── .github/
```

## Status

Experimental and under active development.

## License

The source code and documentation created for this repository are licensed
under the GNU General Public License, version 3 or any later version
(GPL-3.0-or-later).

This license applies only to material created for this repository. It does not
grant rights to any third-party dictionary, lexical database, image, trademark,
or other proprietary material.

See [LICENSE](LICENSE) and [DISCLAIMER.md](DISCLAIMER.md).

## Text and media scope

The converter targets lexical text, search keys, aliases, morphology, and
source-supported metadata. Standalone source media files are intentionally not
exported by the version 1.0 text pipeline.
