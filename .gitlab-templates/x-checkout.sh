#!/usr/bin/env sh

set -x

git fetch
git checkout "$CI_COMMIT_BRANCH"
git reset --hard "origin/$CI_COMMIT_BRANCH"

set +x