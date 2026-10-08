# houaiss3-stardict 1.0.0

First stable source-code release.

## Highlights

- Converts a lawfully obtained local source installation to StarDict for compatible dictionary readers.
- Preserves validated main lexical and morpheme search structures.
- Supports source-defined auxiliary lookup aliases and conservative optional nominal fallback.
- Handles multi-target aliases by materializing one merged StarDict entry, preventing compatible readers from silently losing valid targets.
- Preserves textual structure including definitions, examples, grammatical metadata, pronunciation, translation labels, etymology, usage information, subentries, and registered-trademark markers.
- Uses deterministic StarDict ordering and validates generated index, dictionary, and synonym structures.
- Includes an index-aware repository safety checker that examines the exact blobs staged in Git before commit.

## Validation

Version 1.0.0 passed:

- the complete synthetic test suite;
- staged-blob repository safety checks;
- the complete local conversion dry-run;
- StarDict structural validation;
- text-layer QA;
- command-line reader validation;
- KOReader desktop testing;
- KOReader testing on a Kindle device.

The final locally generated dictionary uses the book name `Houaiss3`.

## Scope

Version 1.0.0 is intentionally text-only. Standalone source media is not exported.

This GitHub release contains source code and documentation only. It does not contain dictionary source files, extracted lexical content, generated dictionaries, images from the source product, or other third-party data.

## Legal and Safety Notice

This project is an educational, experimental, academic, and interoperability tool. It is not intended for unauthorized access, security bypass, license circumvention, copyright infringement, or unauthorized redistribution.

Users must supply source files they are lawfully entitled to use and are responsible for complying with applicable law, licenses, and contracts. The project grants no rights to third-party dictionary content.

The software is provided AS IS, without warranty. Keep backups and use it at your own risk. This notice is not legal advice.

The project source code is licensed under GPL-3.0-or-later.
