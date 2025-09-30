from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from modelses.user import User


class Event(SQLModel, table=True): # Класс событий
    __tablename__ = 'events'
    event_id: int = Field(default=None, primary_key=True)
    description: str
    creator_id: int = Field(foreign_key="user.user_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # creator: Optional["User"] = Relationship(back_populates="events")
    #creator: "User" = Relationship(back_populates="events")