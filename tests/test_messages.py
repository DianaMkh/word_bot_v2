# tests/test_messages.py
import pytest
from messages import Messages


def test_get_simple_message(messages):
    """Test getting simple message"""
    assert messages.get('main_menu') == "You are in the main menu"


def test_get_formatted_message(messages):
    """Test getting message with formatting"""
    name = "John"
    assert messages.get('welcome', name=name) == f"Hello, {name}!"


def test_get_nested_message(messages):
    """Test getting nested message"""
    assert "word pair" in messages.get('add_word.prompt').lower()


def test_change_language(messages):
    """Test language changing"""
    original = messages.get('main_menu')
    messages.change_language('ru')
    russian = messages.get('main_menu')
    assert original != russian
    assert "меню" in russian.lower()


def test_invalid_message_key(messages):
    """Test getting message with invalid key"""
    with pytest.raises(KeyError):
        messages.get('invalid.key')


def test_invalid_language():
    """Test initialization with invalid language"""
    with pytest.raises(ValueError):
        Messages('invalid_lang')


def test_missing_required_param(messages):
    """Test message formatting with missing parameter"""
    with pytest.raises(KeyError):
        messages.get('welcome')  # missing required 'name' parameter


def test_change_to_invalid_language(messages):
    """Test changing to invalid language"""
    with pytest.raises(ValueError):
        messages.change_language('invalid_lang')


def test_nested_key_not_found(messages):
    """Test accessing non-existent nested key"""
    with pytest.raises(KeyError):
        messages.get('add_word.invalid.key')
