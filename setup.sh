#!/usr/bin/env bash
# Build and start the whole TaskForge stack, then wait until the app is healthy.
set -euo pipefail
cd "$(dirname "$0")"

# 1. Docker must be installed and its daemon running.
if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is not installed. See https://docs.docker.com/get-docker/" >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker daemon is not running. Start Docker and retry." >&2
  exit 1
fi

# 2. Build and start everything in the background.
docker compose up -d --build

# 3. Wait (up to 60s) for /health to answer 200.
echo -n "Waiting for the app to become healthy"
for _ in $(seq 1 30); do
  if curl -fsS http://localhost:5000/health >/dev/null 2>&1; then
    echo " - ready!"
    cat <<'EOF'

  App:          http://localhost:5000
  Prometheus:   http://localhost:9090
  Grafana:      http://localhost:3000   (admin / admin)
  Alertmanager: http://localhost:9093
EOF
    exit 0
  fi
  echo -n "."
  sleep 2
done

echo; echo "ERROR: app did not become healthy. Check: docker compose logs app" >&2
exit 1
