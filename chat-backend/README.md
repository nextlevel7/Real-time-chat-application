# Chat backend

## Start with Docker

Run these commands from `chat-backend`:

```sh
cp -n .env.example .env
```

Set `SECRET_KEY`, `JWT_SECRET_KEY`, and `POSTGRES_PASSWORD` in `.env`.
Generate each separately with:

```sh
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

Use the generated hex password so it can be embedded directly in the database URL.
`.env` is ignored by Git and excluded from the Docker build. The example contains
no secrets. Compose reads these values at startup; they are not baked into the image.
Environment variables are still visible to people with Docker administrative access.

```sh
docker compose up --build -d
curl http://localhost:5000/api/health
```

PostgreSQL uses username `user`, database `reatimechat`, and your `.env` password.
Inside Docker the database hostname is `db`; on your computer it is `localhost`.
An existing database volume retains its original credentials: changing `.env`
does not change the password of an existing PostgreSQL user.

## Dockerfile explained

- `FROM python:3.14-slim`: start with a small Python 3.14 Linux image.
- `COPY --from=... /uv /bin/uv`: copy the pinned uv executable from its official image.
- `WORKDIR /app`: use `/app` as the working directory for subsequent instructions.
- `ENV PYTHONUNBUFFERED=1`: send Python output directly to container logs.
- `PATH="/app/.venv/bin:$PATH"`: find executables installed in uv's virtual environment.
- `COPY pyproject.toml uv.lock ./`: copy dependency metadata first, so source-only edits
  can reuse the cached dependency installation.
- `RUN uv sync --locked --no-dev --no-install-project`: install locked runtime
  dependencies, exclude test/lint tools, and skip installing this application as a package.
- `COPY app ./app`: copy only application code, without local secrets or virtual environments.
- `RUN useradd --system app` and `USER app`: create a restricted account and run the
  server using that account. Application files remain read-only to this user.
- `EXPOSE 5000`: document the listening port; this does not publish the port by itself.
- `CMD [...]`: start Gunicorn when the container starts. `--bind 0.0.0.0:5000`
  listens on container interfaces; `--access-logfile -` writes request logs to stdout;
  `app:create_app()` invokes the Flask application factory. Gunicorn handles HTTP
  requests instead of Flask's development server.

## Why Compose is separate

The Dockerfile builds the backend image. `compose.yaml` runs that image alongside
PostgreSQL and connects them on a private Docker network.

- `build: .` builds the backend from the local Dockerfile.
- `environment` supplies settings at startup. `${VAR:?message}` fails clearly if a
  required value is missing or empty. Compose substitutes values from `.env` or the shell.
- `ports` publishes backend port 5000 and database port 5432 on localhost only.
- `depends_on` with `service_healthy` waits for PostgreSQL readiness at startup.
- `pg_isready` checks whether PostgreSQL accepts connections; it does not verify
  that the backend's credentials can authenticate.
- The named `postgres_data` volume keeps database files after containers are removed.
  PostgreSQL 18 stores its files beneath `/var/lib/postgresql`.

The backend HTTP health check, extra worker setting, automatic restart policies,
and optional uv/Python flags were removed to keep the local setup small.
The PostgreSQL readiness check remains useful because database startup takes time.

## Everyday commands

```sh
docker compose up --build -d
```

Build the backend image and start both services in the background (`-d`). Use this
after code or dependency changes; source files are copied into the image.

```sh
docker compose logs -f backend
docker compose ps
curl http://localhost:5000/api/health
```

Follow backend logs (`Ctrl+C` stops following, not the containers), show container
status, and check the HTTP endpoint. Health returns `{"status":"ok"}` and does
not check database connectivity.

```sh
docker compose exec db psql -U user -d reatimechat
```

Open PostgreSQL's command-line client inside the running database container.
Use `\q` to exit.

```sh
docker compose down
```

Stop and remove the containers and network. Database data stays in its volume.
Adding `-v` deletes the database volume and its data.

## Local Python and tests

To run Flask outside Docker, set `DATABASE_URL` in `.env` using the commented
example with your password and the `localhost` hostname. Then:

```sh
uv sync --locked
docker compose up -d db
uv run run.py
uv run pytest
uv run ruff check .
```

Tests use isolated SQLite databases and explicit test secrets. They do not need
PostgreSQL. The app retains its simple local fallback URL for compatibility;
Compose always supplies the PostgreSQL URL with your configured password.
