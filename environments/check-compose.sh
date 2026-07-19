#!/usr/bin/env sh
# Runnable check: validates environments/test/docker-compose.yml is
# well-formed and every variable it references resolves — WITHOUT pulling
# or starting any container. `docker compose config` is a static
# operation (YAML parse + interpolation + merge); it does not talk to the
# Docker daemon, so this check works even where no daemon is running.
#
# Usage: environments/check-compose.sh
set -eu

cd "$(dirname "$0")/test"

if ! command -v docker >/dev/null 2>&1; then
  echo "FAIL: docker CLI not found on PATH" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "FAIL: 'docker compose' (v2 plugin) not available" >&2
  exit 1
fi

# .env.example already resolves every required-var interpolation
# ($VAR:?...) with non-secret placeholder text, including valid numeric
# placeholders for the port-mapping vars — so it doubles as the scratch
# env file for structural validation. Never reads/writes a real .env.
echo "Validating environments/test/docker-compose.yml ..."
if docker compose --env-file .env.example -f docker-compose.yml config --quiet; then
  echo "PASS: compose config is valid YAML, merges, and resolves."
  exit 0
else
  echo "FAIL: docker compose config rejected the file (see above)." >&2
  exit 1
fi
