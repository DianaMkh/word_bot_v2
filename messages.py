import json
from pathlib import Path
from typing import Any


class Messages:
    SUPPORTED_LANGUAGES = {'en', 'ru', 'uk'}  # Добавляем список поддерживаемых языков

    def __init__(self, language: str = 'en'):
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Language {language} not supported. "
                             f"Supported languages: {', '.join(self.SUPPORTED_LANGUAGES)}")
        self.language = language
        self._load_messages()

    def _load_messages(self) -> None:
        """Загрузка сообщений из JSON файла"""
        path = Path(__file__).parent / 'bot_messages.json'
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.messages = json.load(f)

            if self.language not in self.messages:
                raise ValueError(
                    f"Language {self.language} not found in messages file")
        except FileNotFoundError:
            raise FileNotFoundError("bot_messages.json not found")

    def get(self, key: str, **kwargs: Any) -> str:
        """
        Получить сообщение по ключу с форматированием.

        Args:
            key: путь к сообщению в формате "category.subcategory.message_key"
            **kwargs: параметры для форматирования

        Returns:
            str: отформатированное сообщение

        Raises:
            KeyError: если ключ не найден
        """
        keys = key.split('.')
        value = self.messages[self.language]

        for k in keys:
            value = value[k]

        return value.format(**kwargs)

    def change_language(self, language: str) -> None:
        """
        Сменить язык сообщений.

        Args:
            language: код языка ('en', 'ru', etc.)

        Raises:
            ValueError: если язык не поддерживается
        """
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Language {language} not supported. "
                             f"Supported languages: {', '.join(self.SUPPORTED_LANGUAGES)}")
        self.language = language
