#!/bin/bash
set -e
echo "Stopping app ..."
docker stop webapp mydb >/dev/null 2>&1 || true
echo "Stopped. Persistent data preserved."
