#!/usr/bin/env bash

set -euo pipefail

API_CANCEL_TOKEN="$1"

echo >&2 "Annulation de la pipeline en cours..."

# Récupération des jobs de la pipeline
response=$(curl --silent --header "PRIVATE-TOKEN: $API_CANCEL_TOKEN" \
  "$CI_API_V4_URL/projects/$CI_PROJECT_ID/pipelines/$CI_PIPELINE_ID/jobs")

# Vérification que la réponse est un JSON valide (tableau)
if ! echo "$response" | jq -e '. | type == "array"' > /dev/null 2>&1; then
  echo >&2 "Erreur : la réponse de l'API GitLab n'est pas valide."
  echo >&2 "Réponse reçue : $response"
  echo >&2 "Vérifiez que le token API_CANCEL_TOKEN est valide et n'a pas expiré."
  exit 1
fi


jobs=$(echo "$response" | jq -r '.[] | select(.id != '"$CI_JOB_ID"') | .id')
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
