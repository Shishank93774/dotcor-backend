from datetime import UTC, datetime, timedelta
from random import randbytes

from app.core.exceptions import InvalidTokenError, ResourceNotFoundError
from app.core.logging import get_logger
from app.db.models.auth import Auth
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = get_logger(__name__)

AUTH_EXPIRY_TIME_MINUTES = 30


class AuthService:
    def __init__(self, db: Session):
        self._db = db

    def login(self, user_id: int) -> Auth:
        from app.services.user import UserService

        user = UserService(self._db).get_user(user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            raise ResourceNotFoundError("User not found")

        auth = self._db.scalars(select(Auth).where(Auth.user_id == user_id)).first()
        token = randbytes(32).hex()

        if not auth:
            auth = Auth(user_id=user_id, token=token)
            self._db.add(auth)
            logger.info(f"Generated token for user {user_id}")
        else:
            auth.token = token
            logger.info(f"Updated token for user {user_id}")

        self._db.commit()
        self._db.refresh(auth)

        return auth

    def verify(self, token: str) -> Auth:
        auth = self._db.scalars(select(Auth).where(Auth.token == token)).first()
        if not auth:
            logger.warning("Auth rejected: unknown token presented (token material not logged)")
            raise InvalidTokenError("Invalid token")

        expiry_time = auth.updated_at + timedelta(minutes=AUTH_EXPIRY_TIME_MINUTES)
        if expiry_time < datetime.now(UTC):
            logger.warning(f"Auth rejected: expired token for user {auth.user_id} (token material not logged)")
            raise InvalidTokenError("Token Expired, please login again")

        logger.info(f"Verified token for user {auth.user_id}")

        return auth
