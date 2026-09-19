from flask import Flask

from app.config import load_config, validate_config
from app.extensions import cors, db, jwt, migrate


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(load_config())
    if test_config is not None:
        app.config.update(test_config)
    validate_config(app)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app
