#!/usr/bin/env bash

set -euo pipefail

API_CANCEL_TOKEN="$1"

echo >&2 "Annulation de la pipeline en cours..."
jobs=$(curl --silent --header "PRIVATE-TOKEN: $API_CANCEL_TOKEN" \
  "$CI_API_V4_URL/projects/$CI_PROJECT_ID/pipelines/$CI_PIPELINE_ID/jobs" | jq -r '.[] | select(.id != '"$CI_JOB_ID"') | .id')
for id in $jobs; do
  echo "Annulation du job $id"
  
  rc=0
  curl --silent --fail -X POST --header "PRIVATE-TOKEN: $API_CANCEL_TOKEN" \
    "$CI_API_V4_URL/projects/$CI_PROJECT_ID/jobs/$id/cancel" > /dev/null || rc=$?

  if [ $rc -ne 0 ]; then
    echo >&2 "Erreur lors de l'annulation de la pipeline. Peut être que le PAT API_CANCEL_TOKEN a expiré ?"
    exit 1
  fi

done

echo >&2 "Pipeline annulé."
