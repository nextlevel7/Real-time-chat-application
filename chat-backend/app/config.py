import os


def load_config():
    return {
        "SECRET_KEY": os.environ.get("SECRET_KEY"),
        "JWT_SECRET_KEY": os.environ.get("JWT_SECRET_KEY"),
        "SQLALCHEMY_DATABASE_URI": os.environ.get("DATABASE_URL")
        or "postgresql+psycopg://chat:chat@localhost:5432/reatimechat",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "CORS_ORIGINS": [
            origin.strip()
            for origin in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(
                ","
            )
            if origin.strip()
        ],
        "CASSANDRA_HOSTS": [
            h.strip()
            for h in os.environ.get("CASSANDRA_HOSTS", "localhost").split(",")
            if h.strip()
        ],
        "CASSANDRA_KEYSPACE": os.environ.get("CASSANDRA_KEYSPACE", "chat"),
        "CASSANDRA_PORT": int(os.environ.get("CASSANDRA_PORT", "9042")),
    }


def validate_config(app):
    for name in ("SECRET_KEY", "JWT_SECRET_KEY"):
        value = app.config.get(name)
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError(
                f"{name} must be set in the environment or test configuration"
            )
