# Dependencies

## Runtime

| Package | Version constraint | Purpose |
|---|---|---|
| `loguru` | `>=0.7.2` | Structured debug/info/warning logging in parser and editor |
| `pillow` | `>=12.1.1` | JPEG conversion and canvas-fit resizing in `replace_source_image()` |

Both are declared in `pyproject.toml` under `[project] dependencies`.

The parser (`parse()`, `parse_string()`, `extract_*`) is entirely offline — no
network access, no Vexy Lines app, no C extensions. `loguru` and `pillow` are
the only non-stdlib imports.

### Note on `svglab`

`vexy-lines-apy` (the MCP API client layer) optionally uses `svglab` for its
`svg_parsed()` helper. `vexy-lines-py` has no dependency on `svglab` and no
import of it anywhere in the source tree.

## Development / test (hatch default environment)

| Package | Version constraint | Purpose |
|---|---|---|
| `pytest` | `>=8.3.4` | Test runner |
| `pytest-cov` | `>=6.0.0` | Coverage reporting |
| `ruff` | `>=0.9.7` | Linter and formatter |
| `mypy` | `>=1.15.0` | Static type checking |
| `mkdocs` | `>=1.6` | Documentation site builder |
| `mkdocs-materialx` | `>=2.0` | MaterialX theme for documentation |
| `Pygments` | `>=2.18,<2.19` | Syntax highlighting in docs |

See `[tool.hatch.envs.default]` in `pyproject.toml` for the authoritative list.
