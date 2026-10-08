# Architecture

The converter is organized as a pipeline:

```text
user-supplied source files
        |
        v
byte decoder
        |
        v
record parser
        |
        v
neutral lexical model
        |
        +----> markup renderer
        |
        +----> morphology and alias processing
        |
        v
StarDict writer
```

The implementation deliberately separates decoding, parsing, rendering,
morphology, and output generation so that each stage can be independently
tested with synthetic data.

Source files are treated as read-only inputs.
