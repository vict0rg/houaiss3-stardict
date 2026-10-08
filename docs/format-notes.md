# Format Study Notes

This document records abstract technical observations about a legacy dictionary
data format for educational and interoperability research.

No proprietary lexical content is included.

## General Characteristics

The studied format appears to use:

- multiple related data and index files;
- a reversible byte transformation;
- a single-byte character encoding in decoded textual structures;
- line-oriented lexical records;
- record prefixes for lexical and grammatical metadata;
- separate index structures that map search keys to records or offsets;
- auxiliary structures for morphology and lexical relationships.

## Decoding Model

A source byte can be transformed into its decoded representation using a fixed
modular byte offset.

The implementation keeps byte transformation separate from character decoding
so that byte offsets remain stable when index structures depend on them.

## Parsing Strategy

The parser converts source-specific records into a neutral internal
representation.

Linguistic meaning should not be inferred unless it is supported by the
observed data structure and validated independently.

## Test Policy

All examples used by automated tests must be synthetic and must not be derived
from proprietary dictionary content.
