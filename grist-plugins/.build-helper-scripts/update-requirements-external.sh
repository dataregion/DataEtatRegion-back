#!/usr/bin/env bash
uv pip compile requirements.external.in \
  ../services/pyproject.toml \
  ../models/pyproject.toml \
  -o requirements.external.txt