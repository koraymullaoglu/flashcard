from flask import Blueprint, current_app, jsonify, request

from extensions import db
from services.auth_service import AuthService
from services.errors import ServiceError

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.errorhandler(ServiceError)
def handle_service_error(error: ServiceError) -> tuple[object, int]:
    return jsonify({"error": {"code": error.code, "message": error.message}}), error.status_code


@auth_bp.post("/register")
def register() -> tuple[object, int]:
    body = request.get_json(silent=True) or {}
    service = AuthService(db.session, current_app.config["JWT_SECRET"])
    user = service.register(body.get("username", ""), body.get("password", ""))
    return jsonify({"data": {"id": user.id, "username": user.username}}), 201


@auth_bp.post("/login")
def login() -> tuple[object, int]:
    body = request.get_json(silent=True) or {}
    service = AuthService(db.session, current_app.config["JWT_SECRET"])
    token = service.login(body.get("username", ""), body.get("password", ""))
    return jsonify({"data": {"token": token}}), 200
