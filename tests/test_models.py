# tests/test_models.py
import pytest
from database.models import Users, Words
from datetime import datetime, timedelta
from datetime import datetime


def test_user_creation(db_session):
    """Test User model creation"""
    telegram_id = 123456
    user = Users(telegram_id=telegram_id, best_score=0)
    db_session.add(user)
    db_session.commit()

    fetched_user = db_session.query(Users).filter_by(telegram_id=telegram_id).first()
    assert fetched_user is not None
    assert fetched_user.telegram_id == telegram_id


def test_word_creation_and_relations(db_session):
    """Test Word model creation and relations"""
    # Create user
    user = Users(telegram_id=123456, best_score=0)
    db_session.add(user)
    db_session.commit()

    # Create word pair
    word = Words(
        left_word="hello",
        right_word="привет",
        user_id=user.id,
        added_date=datetime.now()
    )
    db_session.add(word)
    db_session.commit()

    # Test fetch
    fetched_word = db_session.query(Words).first()
    assert fetched_word.left_word == "hello"
    assert fetched_word.right_word == "привет"
    assert fetched_word.user_id == user.id


def test_get_random_word(db_session):
    """Test get_random_word method"""
    # Create user
    user = Users(telegram_id=123456, best_score=0)
    db_session.add(user)
    db_session.commit()

    # Add multiple words
    words = [
        ("hello", "привет"),
        ("world", "мир"),
        ("cat", "кот")
    ]
    for left, right in words:
        word = Words(
            left_word=left,
            right_word=right,
            user_id=user.id,
            added_date=datetime.now()
        )
        db_session.add(word)
    db_session.commit()

    # Test random word
    random_word = Words.get_random_word(user.id)
    assert random_word is not None
    assert (random_word.left_word, random_word.right_word) in words


def test_get_all_translations(db_session):
    """Test getting all translations for a word"""
    user = Users(telegram_id=123456, best_score=0)
    db_session.add(user)
    db_session.commit()

    # Add multiple translations for the same word
    translations = ["привет", "здравствуйте", "хай"]
    for translation in translations:
        word = Words(
            left_word="hello",
            right_word=translation,
            user_id=user.id,
            added_date=datetime.now()
        )
        db_session.add(word)
    db_session.commit()

    result = Words.get_all_translations("hello", user.id)
    assert set(result) == set(translations)


def test_user_score_update(db_session):
    """Test updating user's best score"""
    user = Users(telegram_id=123456, best_score=0)
    db_session.add(user)
    db_session.commit()

    user.best_score = 100
    db_session.commit()

    updated_user = db_session.query(Users).first()
    assert updated_user.best_score == 100


def test_word_added_date(db_session):
    """Test word's added_date functionality"""
    user = Users(telegram_id=123456, best_score=0)
    db_session.add(user)
    db_session.commit()

    now = datetime.now()
    word = Words(
        left_word="test",
        right_word="тест",
        user_id=user.id,
        added_date=now
    )
    db_session.add(word)
    db_session.commit()

    fetched_word = db_session.query(Words).first()
    assert abs(fetched_word.added_date - now) < timedelta(seconds=1)