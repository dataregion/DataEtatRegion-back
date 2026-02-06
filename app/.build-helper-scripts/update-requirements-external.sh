#!/usr/bin/env bash
uv pip compile requirements.external.in \
  ../models/pyproject.toml \
  ../services/pyproject.toml \
  ../gristcli/pyproject.toml \
  -o requirements.external.txt