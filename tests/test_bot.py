# tests/test_bot.py
import pytest
from unittest.mock import Mock, patch
from main import validate_word_pair, process_new_word_pair, \
    start_training_session


@pytest.fixture
def mock_message():
    message = Mock()
    message.chat.id = 123456
    message.text = "hello - world"
    message.from_user.id = 789
    return message


@pytest.fixture
def mock_state_manager():
    return Mock()


def test_validate_word_pair_valid():
    """Test word pair validation with valid input"""
    result = validate_word_pair("hello - world")
    assert result == ("hello", "world")


def test_validate_word_pair_invalid():
    """Test word pair validation with invalid input"""
    with pytest.raises(ValueError):
        validate_word_pair("invalid format")


def test_validate_word_pair_empty():
    """Test word pair validation with empty parts"""
    with pytest.raises(ValueError):
        validate_word_pair(" - ")


@patch('editbot.Users')
def test_process_new_word_pair_success(mock_users, mock_message,
                                       mock_state_manager):
    """Test successful word pair processing"""
    mock_user = Mock()
    mock_users.get_or_create_user.return_value = (mock_user, True)

    success, message = process_new_word_pair(mock_message, mock_state_manager)
    assert success is True
    assert "saved" in message.lower()


@patch('editbot.Words')
def test_start_training_session_no_words(mock_words):
    """Test training session start with no words"""
    mock_words.get_random_word.return_value = None

    success, message = start_training_session(123, 456, Mock())
    assert success is False
    assert "no words" in message.lower()


@patch('editbot.Words')
def test_start_training_session_success(mock_words):
    """Test successful training session start"""
    mock_word = Mock()
    mock_word.first_part = "test"
    mock_word.all_translations = ["тест"]
    mock_words.get_random_word.return_value = mock_word

    mock_state_manager = Mock()
    success, word = start_training_session(123, 456, mock_state_manager)

    assert success is True
    assert word == "test"
