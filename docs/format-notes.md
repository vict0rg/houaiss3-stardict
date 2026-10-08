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
