import uuid

from sqlalchemy import Column, String
from app.Database.db import Base

class User(Base):

    __tablename__ = "user"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    username = Column(String(64))

    email = Column(String(64))