#!/usr/bin/env bash
# Reusable read-only smoke check for the page/capability in manifest.yaml.
# Rules: localhost targets only, GET requests only, no live external mutations.
# Exit 0 = PASS, non-zero = FAIL. Print one line per check: PASS|FAIL <name>.
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:3000}"
API_URL="${API_URL:-http://localhost:8000}"

echo "SMOKE example page — ${BASE_URL}"

# Example check 1: backend health endpoint responds.
if curl -fsS -o /dev/null -m 5 "${API_URL}/health"; then
  echo "PASS backend health"
else
  echo "FAIL backend health"
  exit 1
fi

# Example check 2: frontend serves the route (adjust path to the real route).
# if curl -fsS -o /dev/null -m 5 "${BASE_URL}/example"; then
#   echo "PASS frontend route"
# else
#   echo "FAIL frontend route"
#   exit 1
# fi

echo "SMOKE PASS"
