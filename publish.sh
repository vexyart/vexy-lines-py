#!/usr/bin/env bash
cd "$(dirname "$0")"
python -m mkdocs build
uvx hatch clean
uvx hatch build
gitnextver
uv publish