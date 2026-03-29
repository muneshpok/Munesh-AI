from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self) -> None:
        self._users: dict[str, User] = {}

    def register(self, email: str, password: str) -> User:
        password_hash = pwd_context.hash(password)
        user = User(email=email, password_hash=password_hash)
        self._users[email] = user
        return user

    def authenticate(self, email: str, password: str) -> bool:
        user = self._users.get(email)
        if not user:
            return False
        return pwd_context.verify(password, user.password_hash)

    def create_token(self, subject: str) -> str:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
        payload = {"sub": subject, "exp": expire}
        return jwt.encode(payload, settings.secret_key, algorithm="HS256")


auth_service = AuthService()
