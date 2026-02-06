#!/usr/bin/env bash
uv pip compile requirements.external.in \
  ../models/pyproject.toml \
  ../gristcli/pyproject.toml \
  ../services/pyproject.toml \
  -o requirements.external.txt