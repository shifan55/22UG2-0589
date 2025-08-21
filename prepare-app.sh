#!/bin/bash
set -e
echo "Preparing app ..."

# Create network if missing
docker network inspect app-net >/dev/null 2>&1 || docker network create app-net

# Create named volume for DB persistence if missing
docker volume inspect pg-data >/dev/null 2>&1 || docker volume create pg-data

# Build the web image
docker build -t flask-web ./web

echo "Preparation complete."
