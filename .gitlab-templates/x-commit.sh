#!/usr/bin/env bash

set -euo pipefail

PAT="${1:?PAT token required as second argument}"
COMMIT_MESSAGE="${2:-[FORGE] Mise à jour}"

branch="${CI_MERGE_REQUEST_SOURCE_BRANCH_NAME:-${CI_COMMIT_BRANCH}}"

# Configure git to use the PAT for authentication
git config --local credential.helper '!f() { echo "username=oauth2"; echo "password='$PAT'"; }; f'
git remote set-url origin "https://oauth2:$PAT@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git"

echo >&2 "Will commit the local changes!"
git add -u
git commit -m "$COMMIT_MESSAGE"
git checkout -b "$branch"
git push origin "$branch"