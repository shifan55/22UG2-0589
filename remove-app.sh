#!/bin/bash
set -e
echo "Removing app ..."

# Remove containers (if exist)
docker rm -f webapp mydb >/dev/null 2>&1 || true

# Remove image (if exists)
docker rmi flask-web >/dev/null 2>&1 || true

# Remove network
docker network rm app-net >/dev/null 2>&1 || true

# Remove volume (this clears DB data)
docker volume rm pg-data >/dev/null 2>&1 || true

echo "Removed app."
