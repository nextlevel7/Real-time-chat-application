from flask import Flask

from app.auth.routes import auth_bp
from app.common.errors import register_errors
from app.config import load_config, validate_config
from app.extensions import cors, db, jwt, migrate, socketio
from app.messages.routes import messages_bp
from app.rooms.routes import rooms_bp
from app.sockets import register_socket_events


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
    socketio.init_app(app, cors_allowed_origins="*")
    register_socket_events(socketio)
    register_errors(app)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    app.register_blueprint(auth_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(messages_bp)

    return app
