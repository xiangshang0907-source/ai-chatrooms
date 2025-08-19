from flask import Blueprint

from ..constants import APP_VERSION

health_blueprint = Blueprint("health", __name__)


@health_blueprint.get("/health")
def health() -> tuple[dict, int]:
    return {"status": "ok", "service": "ai-chatrooms", "version": APP_VERSION}, 200
