import modelses
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import List, TYPE_CHECKING
import re
from enum import Enum


if TYPE_CHECKING:
    from modelses.models import PredictionResult
    from modelses.event import Event

class UserRole(Enum):
    # Роли пользователей
    USER = "user"
    ADMIN = "admin"

class User(SQLModel, table=True):
    __tablename__ = "user"
    user_id: int = Field(default=None, primary_key=True)
    username: str
    email: str
    password_hash: str
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    balance: float = Field(default=0.0)

    # Связи с другими моделями
    predictions: List["PredictionResult"] = Relationship(back_populates="user")
    #events: List["Event"] = Relationship(back_populates="creator")

    # Свойство роли пользователя
    @property
    def role(self) -> UserRole:
        return UserRole.ADMIN if self.is_admin else UserRole.USER

    @staticmethod
    def hash_password(password: str) -> str:
        import hashlib
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    @classmethod
    def create(cls, email: str, username: str, password: str) -> "User":
        return cls(
            email=email,
            username=username,
            password_hash=cls.hash_password(password),
            is_admin=False
        )

    def validate_email(self) -> None:
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(self.email):
            raise ValueError("Invalid email format")

    def validate_password(self, password: str) -> None:
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

