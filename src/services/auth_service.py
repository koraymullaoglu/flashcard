from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from models import User
from services.errors import ConflictError, ValidationError


class AuthService:
    def __init__(self, session: Session, jwt_secret: str):
        self.session = session
        self.jwt_secret = jwt_secret

    def register(self, username: str, password: str) -> User:
        username = username.strip()
        if not username or not password:
            raise ValidationError("Kullanici adi ve sifre zorunlu.")
        if len(username) > 80:
            raise ValidationError("Kullanici adi en fazla 80 karakter olabilir.")
        if self.session.query(User).filter(User.username == username).one_or_none():
            raise ConflictError("Bu kullanici adi zaten alinmis.")

        user = User(username=username, password_hash=generate_password_hash(password))
        self.session.add(user)
        self.session.commit()
        return user

    def login(self, username: str, password: str) -> str:
        user = self.session.query(User).filter(User.username == username).one_or_none()
        if user is None or not check_password_hash(user.password_hash, password):
            raise ValidationError("Kullanici adi veya sifre hatali.")

        payload = {
            "sub": str(user.id),
            "usr": user.username,
            "exp": datetime.now(timezone.utc) + timedelta(hours=24),
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
