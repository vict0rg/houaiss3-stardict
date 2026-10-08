# Architecture

The converter uses a validation-first pipeline:

```text
user-supplied local source files
        |
        v
in-memory byte decoder
        |
        +----> detailed lexical index
        +----> grouped search-key index
        +----> morphology indexes
        |
        v
strict structural validation
        |
        v
line-oriented lexical parser
        |
        +----> main lexical records
        +----> auxiliary morpheme records
        |
        v
authoritative search-key grouping
        |
        +----> explicit aliases
        +----> validated verbal aliases
        +----> conservative nominal aliases
        |
        v
HTML renderer
        |
        v
staged StarDict writer
        |
        v
structural StarDict validator
```

Source files are read-only. Normal conversion does not create decoded
intermediate files.

The public repository contains no proprietary dictionary data. Automated tests
use synthetic records only.
