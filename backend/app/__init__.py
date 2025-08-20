from flask import Flask
from flask_cors import CORS

from .auth import init_jwt
from .config import Config
from .constants import APP_VERSION
from .database import init_db
from .routes.auth import auth_blueprint
from .routes.health import health_blueprint
from .routes.rooms import room_blueprint
from .routes.messages import message_blueprint


def create_app(config_overrides: dict | None = None) -> Flask:
    config = Config.from_env()
    if config_overrides:
        for key, value in config_overrides.items():
            setattr(config, key, value)

    app = Flask(__name__)
    app.config.from_object(config)

    # 初始化扩展
    CORS(app, resources={r"/*": {"origins": "*"}})
    init_db(app)
    init_jwt(app)

    # 注册蓝图
    app.register_blueprint(health_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(room_blueprint)
    app.register_blueprint(message_blueprint)

    # Health/version endpoint at root path for convenience
    @app.get("/")
    def root() -> tuple[dict, int]:
        return {"status": "ok", "service": "ai-chatrooms", "version": APP_VERSION}, 200

    return app
