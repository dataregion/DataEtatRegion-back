#!/usr/bin/env bash
uv pip compile requirements.external.in \
  ../models/pyproject.toml \
  -o requirements.external.txt