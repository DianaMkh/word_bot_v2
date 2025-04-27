from datetime import datetime

from database.db import Base, db_session
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer)
    best_score = Column(Integer)
    language = Column(String, default="en")  # Новый столбец

    @classmethod
    def get_or_create_user(cls, telegram_id: int, best_score: int = 0):
        # db_session импортирован из database.db
        # (там создается инстанс подключения к базе
        # при первом обращеннии к ней, дальше мы его всюду используем)
        instance = db_session.query(cls).filter_by(
            telegram_id=telegram_id
        ).first()
        if instance:
            return instance, False
        new_user = cls(
            telegram_id=telegram_id,
            best_score=best_score
        )
        try:
            db_session.add(new_user)
            db_session.commit()
            return new_user, True
        except IntegrityError:
            db_session.rollback()
            return db_session.query(cls).filter_by(
                telegram_id=telegram_id
            ).first(), False

    def set_language(self, new_language: str):
        """Меняет язык пользователя."""
        self.language = new_language
        db_session.commit()

    def get_language(self) -> str:
        """Возвращает язык пользователя, если он есть, иначе 'en'."""
        return self.language if self.language else "en"


class Words(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    left_word = Column(String, index=True)
    right_word = Column(String, index=True)
    added_date = Column(DateTime, index=True, default=datetime.now())
    user_id = Column(Integer, ForeignKey("users.id"))

    @classmethod
    def get_word(cls, session: Session, word: str):
        return session.query(cls).filter(
            or_(
                cls.left_word == word,
                cls.right_word == word
            )
        ).first()

    @classmethod
    def get_or_create_word(
        cls, left_word: str, right_word: str, user_id: int
    ):
        instance = db_session.query(cls).filter_by(
            left_word=left_word, right_word=right_word
        ).first()

        if instance:
            return instance, False

        new_word_couple = cls(
            left_word=left_word,
            right_word=right_word,
            added_date=datetime.now(),
            user_id=user_id
        )
        try:
            db_session.add(new_word_couple)
            db_session.commit()
            return new_word_couple, True
        except IntegrityError:
            db_session.rollback()
            return db_session.query(cls).filter_by(
                left_word=left_word, right_word=right_word
            ).first(), False

    @property
    def first_part(self) -> str:
        """Получить левое слово для тренировки"""
        return self.left_word

    @property
    def second_part(self) -> str:
        """Получить правое слово для тренировки"""
        return self.right_word

    @classmethod
    def get_all_translations(cls, left_word: str, user_id: int) -> list[str]:
        """
        Получить все возможные переводы для слова
        """
        words = db_session.query(cls.right_word).filter_by(
            left_word=left_word, user_id=user_id
        ).all()
        return [word[0] for word in words]

    @classmethod
    def get_random_word(cls, user_id: int):
        """
        Получить случайную пару слов для конкретного пользователя
        """
        from sqlalchemy.sql.expression import func

        word = db_session.query(cls).filter_by(
            user_id=user_id
        ).order_by(func.random()).first()

        if word:
            # Получаем все возможные переводы для этого слова
            word.all_translations = cls.get_all_translations(
                word.left_word, user_id
            )

        return word
