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
