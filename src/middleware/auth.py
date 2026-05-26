from functools import wraps

import jwt
from flask import current_app, g, jsonify, request


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        token = header.replace("Bearer ", "")
        if not token:
            return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Token gerekli."}}), 401
        try:
            payload = jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
            g.current_user_id = int(payload["sub"])
        except jwt.InvalidTokenError:
            return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Gecersiz token."}}), 401
        return f(*args, **kwargs)

    return decorated
