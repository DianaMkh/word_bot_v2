from pydantic import BaseModel
from typing import Optional, Annotated
from datetime import date
from sqlalchemy.orm import Session

from database.db import engine, db_session
from database.models import Base


Base.metadata.create_all(bind=engine)


class UserBase(BaseModel):
    telegram_id: str
    best_score: int


class WordBase(UserBase):
    left_word: str
    right_word: str
    added_date: Optional[date]


def get_db():
    db = db_session()
    try:
        yield db
    finally:
        db.close()


# db_dependency = Annotated[Session, Depe]
