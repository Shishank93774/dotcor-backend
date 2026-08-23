from app.core.exceptions import ResourceNotFoundError
from app.db.models.user import User
from sqlalchemy import select
from sqlalchemy.orm import Session


class UserService:
    def __init__(self, db: Session):
        self._db = db

    def get_user(self, user_id: int):
        user = self._db.scalars(select(User).where(User.id == user_id)).first()
        if not user:
            raise ResourceNotFoundError("User not found")
        return user

    def get_chat_rooms(self, user_id: int):
        user = self.get_user(user_id)
        return user.chat_rooms
