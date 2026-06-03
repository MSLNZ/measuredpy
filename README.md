# measuredpy

Python package for semantic annotation and static extraction of
links between measurement code and technical procedures.

## Overview

`measuredpy` provides lightweight constructs for annotating Python
source with references to requirements and equations defined in a
technical procedure (TP).  Annotations are designed to be statically
extractable using the `ast` module, without executing the code.

## Annotation constructs

### `md_ref` — decorator for functions and methods

```python
from measuredpy import md_ref

@md_ref("req:calibration")
def compute_result(readings):
    ...
```

### `md_block` — context manager for code regions

```python
from measuredpy import md_block

def compute_result(readings):
    with md_block("req:noise-reduction", "average repeated observations"):
        smoothed = average(readings)
    ...
```

### `md_anchor` — marker call for a single point

```python
from measuredpy import md_anchor

def compute_result(readings):
    md_anchor("eq:Y", "measurement model")
    ...
```

## Extraction

```python
from measuredpy import extract, extract_from

# single file
records = extract("src/calibration.py")

# all Python files under a directory
records = extract_from("src")
```

Each record is a dictionary:

| Key        | Type         | Description                                |
|------------|--------------|--------------------------------------------|
| `type`     | `str`        | `"md_ref"`, `"md_block"`, or `"md_anchor"` |
| `label`    | `str`        | TP requirement or equation label            |
| `note`     | `str | None` | Optional descriptive note                   |
| `qualname` | `str`        | Enclosing function or method, e.g. `"Calibrator.correct"` |
| `line`     | `int`        | Source line number                          |
| `end_line` | `int`        | Last line of block (`md_block` only)        |
| `file`     | `str`        | Source file path                            |

## Labels

Labels are strings shared between the TP source and the Python
implementation.  They follow whatever convention is used in the TP
(e.g. `eq:Y`, `req:noise-reduction`).

## Installation

[TBD]

## Licence

MIT