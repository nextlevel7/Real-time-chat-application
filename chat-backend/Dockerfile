FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.6 /uv /bin/uv

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY app ./app
COPY migrations ./migrations
RUN useradd --system app
USER app

EXPOSE 5000
CMD ["sh", "-c", "flask --app 'app:create_app()' db upgrade && exec gunicorn --worker-class gthread --threads 100 --bind 0.0.0.0:5000 --access-logfile - 'app:create_app()'"]
