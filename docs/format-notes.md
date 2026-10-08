# Format Study Notes

This document records abstract technical observations about a legacy dictionary
data format for educational and interoperability research.

No proprietary lexical content is included.

## General Characteristics

The studied format uses multiple related data and index files, a reversible
byte transformation, a single-byte decoded text representation, line-oriented
lexical records, grouped search-key indexes, and auxiliary morphology tables.

## Search Keys and Display Headwords

The decoded lexical record and the search index are not assumed to be
identical.

The converter therefore treats the source application's grouped and detailed
indexes as authoritative for search keys. The lexical record keeps its own
display headword.

This distinction avoids silently losing indexed forms when multiple records are
grouped under one searchable key.

## Morphology

The conversion pipeline uses three layers:

1. aliases explicitly stored in lexical records;
2. verbal forms accepted only when two independent source indexes agree on the
   same target;
3. conservative nominal inflection rules applied only when exactly one
   existing source headword is a valid candidate.

Ambiguous generated mappings are skipped.

## StarDict Ordering

StarDict index and synonym records use ASCII case-insensitive primary ordering
with exact UTF-8 byte ordering as the tie-breaker. The same ordering is used by
the structural validator.

## Test Policy

All automated tests use synthetic data created specifically for this project.

## Capitalization Inside Grouped Search Keys

A grouped search-key row may cover detailed lexical rows whose spelling differs
only by capitalization.

The grouped index therefore defines the authoritative search key and group
boundary. Detailed rows are validated using normalized case-insensitive
comparison, while their original display headwords remain unchanged.

This rule was derived from structural comparison of locally supplied source
indexes. No proprietary lexical examples are included in this repository.

## Auxiliary Lookup References

The large auxiliary lookup table is not specific to verbs. It contains
inflected forms and other searchable surface variants.

The grouped reference behaves consistently as a one-based index into the
grouped search-key table and is used as the authoritative alias target.

The other numeric reference has a mixed adjacent-row convention in the
observed source data. Some rows validate against a zero-based detailed-index
position, some against the corresponding one-based position, and duplicate
groups can make both interpretations valid.

The converter does not guess which convention a row uses. It accepts an alias
only when at least one of the two adjacent detailed-index interpretations
independently resolves to the same source-defined group selected by the
authoritative grouped reference.

This rule is exhaustively validated against the locally supplied source data
during development. No proprietary lexical examples are included here.

## Optional Nominal Inference

Rule-based nominal inference remains available through
`--infer-nominal-aliases`, but it is disabled by default. The source auxiliary
lookup table is preferred because it is source-derived rather than heuristic.

## Conservative Nominal Fallback

The authoritative auxiliary lookup table is used first.

It does not cover every nominal inflection needed for practical lookup.
Therefore the default conversion pipeline applies a conservative nominal
fallback only to surface forms that are not already primary headwords or
source-derived aliases.

A fallback alias is emitted only when exactly one existing main headword is a
valid candidate. Ambiguous mappings are skipped and counted in the local audit.

This distinction is intentional:

- source-derived auxiliary aliases are authoritative;
- nominal fallback aliases are converter-generated and conservative;
- source aliases always take precedence;
- ambiguous generated mappings are never guessed.

The fallback can be disabled with `--no-nominal-fallback` for source-only
experiments.

## Text Fidelity Decisions

The stable text pipeline distinguishes source markers according to observed
structure rather than assigning unsupported semantics.

- `M` contributes additional searchable aliases separated by `|`.
- `o` and `p` are rendered as pronunciation information.
- `t` is rendered as a translation label.
- `®` is rendered as a registered-trademark flag without inventing a value.
- `v`, `S`, and `s` are treated as structural flags unless they carry
  meaningful payload beyond the observed flag values.
- Numeric auxiliary markers remain neutral notes unless their semantics are
  independently established.

Within subentry titles, `#` and `@` separate alternative forms. The renderer
shows both separators as a neutral slash while preserving the surrounding
lexical text.

## Media Scope

Source files 021 through 082 are standalone GIF resources. Version 1.0 of the
converter is intentionally text-only and does not export these media files.
This keeps the conversion scope focused on lexical interoperability and avoids
inventing an entry-to-image mapping that has not been demonstrated.
