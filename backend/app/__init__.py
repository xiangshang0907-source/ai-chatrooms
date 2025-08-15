from flask import Flask
from flask_cors import CORS

from .config import Config


APP_VERSION = "0.1.0"

from .routes.health import health_blueprint


def create_app(config_overrides: dict | None = None) -> Flask:
    config = Config.from_env()
    if config_overrides:
        for key, value in config_overrides.items():
            setattr(config, key, value)

    app = Flask(__name__)
    app.config.from_object(config)

    CORS(app, resources={r"/*": {"origins": "*"}})

    app.register_blueprint(health_blueprint)

    # Health/version endpoint at root path for convenience
    @app.get("/")
    def root() -> tuple[dict, int]:
        return {"status": "ok", "service": "ai-chatrooms", "version": APP_VERSION}, 200

    return app