from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import abort, current_app, g, request

from .extensions import db
from .models import User


def issue_token(user):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "iat": now,
        "exp": now + timedelta(hours=current_app.config["TOKEN_TTL_HOURS"]),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            abort(401, "missing bearer token")
        try:
            payload = jwt.decode(header[7:], current_app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            abort(401, "token expired")
        except jwt.InvalidTokenError:
            abort(401, "invalid token")
        user = db.session.get(User, int(payload["sub"]))
        if user is None:
            abort(401, "user no longer exists")
        g.user = user
        return view(*args, **kwargs)

    return wrapper
