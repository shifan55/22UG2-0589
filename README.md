# Two-Service Docker App (Flask + PostgreSQL)

## Deployment Requirements
- Docker 24+
- (Optional) Docker Compose v2+

## Application Description
A minimal notes app:
- Flask web service (port 8000)
- PostgreSQL database (port 5432) with a persistent named volume

## Network & Volume
- Network: `app-net`
- Volume: `pg-data` → mounted at `/var/lib/postgresql/data` for DB persistence

## Container Configuration
- **db (mydb)**: `postgres:15` with `POSTGRES_USER=admin`, `POSTGRES_PASSWORD=secret`, `POSTGRES_DB=appdb`
- **web (webapp)**: custom image `flask-web`, envs `DB_HOST=mydb`, `DB_PORT=5432`, `DB_NAME=appdb`, `DB_USER=admin`, `DB_PASS=secret`

## Container List
- `mydb` – PostgreSQL, stores notes
- `webapp` – Flask server serving UI on port 8000

## Instructions

### Prepare
```bash
./prepare-app.sh
