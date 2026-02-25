from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nick: str = Field(index=True, unique=True, max_length=50)
    hashed_pw: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    pair_id: Optional[int] = Field(
        default=None,
        foreign_key="pair.id",
        nullable=True,
    )

class Pair(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user1_id: int = Field(foreign_key="user.id")
    user2_id: int = Field(foreign_key="user.id")
    
    # Простые отношения без back_populates
    user1: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Pair.user1_id]"}
    )
    user2: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Pair.user2_id]"}
    )