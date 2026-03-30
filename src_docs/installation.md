# Installation

## Requirements

- Python 3.11 or newer
- No C extensions, no system libraries, no app required

## Install from PyPI

```bash
pip install vexy-lines-py
```

Or with `uv`:

```bash
uv add vexy-lines-py
```

## Runtime dependencies

| Package | Why |
|---------|-----|
| `loguru` | Structured debug logging (silent by default) |

That's it. One dependency.

## Verify the install

```python
from vexy_lines import parse
print("vexy-lines-py is ready")
```

## Development install

Clone the repo and install in editable mode:

```bash
git clone https://github.com/vexyart/vexy-lines.git
cd vexy-lines/vexy-lines-py
uv venv --python 3.12
uv pip install -e ".[dev]"
```

Run tests:

```bash
uvx hatch test
```

Run type checking:

```bash
uvx hatch run lint:typing
```

## Platform support

Works everywhere Python runs. The parser is pure Python using only `xml.etree.ElementTree`, `base64`, `zlib`, and `struct` from the standard library.

Tested on macOS, Linux, and Windows. CPython and PyPy.
