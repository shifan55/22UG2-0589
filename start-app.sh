#!/bin/bash
set -e
echo "Starting app ..."

# Start DB (idempotent: run if not exists, else start)
if [ -z "$(docker ps -aq -f name=^mydb$)" ]; then
  docker run -d \
    --name mydb \
    --network app-net \
    -e POSTGRES_USER=admin \
    -e POSTGRES_PASSWORD=secret \
    -e POSTGRES_DB=appdb \
    -v pg-data:/var/lib/postgresql/data \
    -p 5432:5432 \
    --restart=always \
    postgres:15
else
  docker start mydb >/dev/null
fi

# Start Web
if [ -z "$(docker ps -aq -f name=^webapp$)" ]; then
  docker run -d \
    --name webapp \
    --network app-net \
    -e DB_HOST=mydb \
    -e DB_PORT=5432 \
    -e DB_NAME=appdb \
    -e DB_USER=admin \
    -e DB_PASS=secret \
    -p 8000:8000 \
    --restart=always \
    flask-web
else
  docker start webapp >/dev/null
fi

echo "The app is available at http://localhost:8000"
