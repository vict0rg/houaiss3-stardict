# Development Notes

## Core Rules

1. Never commit proprietary dictionary content.
2. Never modify user source files in place.
3. Keep byte decoding separate from record parsing.
4. Preserve byte offsets when analyzing index structures.
5. Use only synthetic data in tests.
6. Run the repository safety checker before every commit.

## Running Tests

```bash
python3 -m unittest discover -s tests -v
```

## Running the Safety Check

```bash
python3 scripts/check_repository_safety.py
```

## Local Conversion Output

Generated dictionary files must remain outside the Git repository.

A typical invocation is:

```bash
houaiss3-stardict /path/to/user-owned/source \
  --output /path/to/local/dictionary/output
```

For a small local preview:

```bash
houaiss3-stardict /path/to/user-owned/source \
  --output /path/to/local/dictionary/output \
  --name Preview \
  --limit 100
```

The converter reads source data in memory and does not create decoded
intermediate files during normal operation.
