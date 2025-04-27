# tests/conftest.py
import pytest
import json
from pathlib import Path
from messages import Messages


@pytest.fixture
def test_messages_file(tmp_path):
    """Create temporary messages file"""
    messages_data = {
        "en": {
            "welcome": "Hello, {name}!",
            "main_menu": "You are in the main menu",
            "add_word": {
                "prompt": "Please enter word pair (word1 - word2)"
            }
        },
        "ru": {
            "welcome": "Привет, {name}!",
            "main_menu": "Вы в главном меню",
            "add_word": {
                "prompt": "Пожалуйста, введите пару слов (слово1 - слово2)"
            }
        }
    }

    messages_file = tmp_path / "bot_messages.json"
    with open(messages_file, 'w', encoding='utf-8') as f:
        json.dump(messages_data, f, ensure_ascii=False)
    return messages_file


@pytest.fixture
def messages(test_messages_file, monkeypatch):
    """Create Messages instance with test file"""

    # Патчим метод _load_messages, чтобы он использовал наш тестовый файл
    def mock_load_messages(self):
        with open(test_messages_file, 'r', encoding='utf-8') as f:
            self.messages = json.load(f)

    monkeypatch.setattr(Messages, '_load_messages', mock_load_messages)
    return Messages('en')
