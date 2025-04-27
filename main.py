import telebot
import os
import re
import redis

from dotenv import load_dotenv
from typing import Optional, Tuple
from enum import Enum
from database.db import engine
from database.models import Base, Words, Users
from config import config
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, Message
from messages import Messages
from typing import Callable


class BotCommands(Enum):
    """Commands and button texts of the bot."""
    ADD_WORD = ('add', '➕ Add word')
    TRAIN = ('train', '🎯 Train')
    BACK_TO_MENU = ('break', '🔙 Back to menu')
    START = ('start', None)
    CLUE = ('clue', '➕ Clue')
    SWITCH_LANGUAGE = ('switch_language', 'Switch language')

    def __init__(self, command: str, button_text: Optional[str]) -> None:
        self.command = command
        self.button_text = button_text


class UserState(Enum):
    IDLE = "idle"
    AWAITING_WORD_PAIR = "awaiting_word_pair"
    TRAINING = "training"
    SWITCH_LANGUAGE = "switch_language"


class RedisStateManager:
    def __init__(self, redis_client: redis.Redis, config_redis) -> None:
        self.redis = redis_client
        self.config = config_redis

    def _get_key(self, chat_id: int) -> str:
        return f"{self.config.prefix}user:{chat_id}"

    def get_state(self, chat_id: int) -> Optional[str]:
        key = self._get_key(chat_id)
        return self.redis.get(key)

    def set_state(self, chat_id: int, state: UserState) -> None:
        key = self._get_key(chat_id)
        self.redis.setex(key, self.config.ttl, state.value)

    def get_translations(self, chat_id: int) -> list[str]:
        """Get all possible translations."""
        key = f"{self._get_key(chat_id)}:translations"
        translations = self.redis.lrange(key, 0, -1)
        return translations if translations else []

    def increase_clue_counter(self, chat_id: int) -> None:
        """Increase prompt counter."""
        key = f"{self._get_key(chat_id)}:clue"
        value = self.redis.get(key)
        self.redis.set(key, int(value) + 1 if value else 1)

    def get_clue_counter(self, chat_id: int) -> Optional[int]:
        value = self.redis.get(f"{self._get_key(chat_id)}:clue")
        return int(value) if value else 0

    def clear_clue_counter(self, chat_id: int) -> None:
        self.redis.delete(f"{self._get_key(chat_id)}:clue")

    def clear_state(self, chat_id: int) -> None:
        """Clear user state and translations."""
        key = self._get_key(chat_id)
        training_key = f"{key}:translations"
        self.redis.delete(key, training_key)


# Initialization of the Redis base
Base.metadata.create_all(bind=engine)
redis_client = redis.Redis(
    host=config.redis.host,
    port=config.redis.port,
    password=config.redis.password or None,
    db=config.redis.db,
    decode_responses=True
)

# Initialization of bot, status manager and messages
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
state_manager = RedisStateManager(redis_client, config.redis)
messages = Messages('en')  # или 'ru' для русского языка


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Создает основную клавиатуру с кнопками."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    add_button = KeyboardButton(BotCommands.ADD_WORD.button_text)
    train_button = KeyboardButton(BotCommands.TRAIN.button_text)
    switch_language_button = KeyboardButton(BotCommands.SWITCH_LANGUAGE.button_text)
    keyboard.add(add_button, train_button, switch_language_button)
    return keyboard


def get_language_keyboard() -> ReplyKeyboardMarkup:
    """Creates a new keyboard with buttons."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        *[KeyboardButton(language) for language in Messages.SUPPORTED_LANGUAGES]
    )
    return keyboard


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Creates a cancellation keyboard."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_button = KeyboardButton(BotCommands.BACK_TO_MENU.button_text)
    keyboard.add(cancel_button)
    return keyboard


def training_keyboard() -> ReplyKeyboardMarkup:
    """Creates a keyboard with a prompt button."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    clues_button = KeyboardButton(BotCommands.CLUE.button_text)
    cancel_button = KeyboardButton(BotCommands.BACK_TO_MENU.button_text)
    keyboard.add(cancel_button, clues_button)
    return keyboard


def command_or_text(command: BotCommands) -> Callable[[], str or bool]:
    """
    Creates a function to check the command or message text.

    Args:
        command: command from BotCommands
    """

    def wrapper(message) -> str or bool:
        if message.content_type != 'text':
            return False

        if message.text.startswith('/'):
            return message.text[1:] == command.command

        return message.text == command.button_text

    return wrapper


def escape_markdown(text: str) -> str:
    """Filters special symbols MarkdownV2."""
    return re.sub(r'([_*\[\]()~`>#+=|{}.!-])', r'\\\1', text)


def validate_word_pair(message: str) -> Tuple[str, str]:
    """Validate and split message into word pair."""
    if '-' not in message:
        raise ValueError("Message must contain '-' symbol")

    parts = [part.strip() for part in message.split('-', 1)]
    if len(parts) != 2 or not all(parts):
        raise ValueError("Both words must be non-empty")

    return tuple(parts)


def process_new_word_pair(
    message,
    state_manager: RedisStateManager
) -> tuple[bool, str]:
    """
    Processing a new pair of words from user.

    Args:
        message: Users message
        state_manager: State manager

    Returns:
        tuple[bool, str]: (success og the operation, user message)
    """
    try:
        word1, word2 = validate_word_pair(message.text)
        user = Users.get_or_create_user(telegram_id=message.from_user.id)[0]
        word_pair, created = Words.get_or_create_word(word1, word2, user.id)

        if created:
            state_manager.set_state(message.chat.id, UserState.IDLE)
            return True, messages.get('add_word.saved')

        return False, messages.get('add_word.exists')

    except ValueError as e:
        return False, messages.get('add_word.invalid_format', error=str(e))


def start_training_session(
    chat_id: int,
    user_id: int,
    state_manager: RedisStateManager
) -> tuple[bool, str]:
    """
    Start a new training session.

    Args:
        chat_id: Chats ID
        user_id: Users ID
        state_manager: State manager

    Returns:
        tuple[bool, str]: (success, message/training status)
    """
    random_word = Words.get_random_word(user_id)

    if not random_word:
        state_manager.set_state(chat_id, UserState.IDLE)
        return False, messages.get('training.no_words')

    state_manager.set_state(chat_id, UserState.TRAINING)
    # Save all possible translations
    translations_key = f"{state_manager._get_key(chat_id)}:translations"
    state_manager.redis.delete(translations_key)
    state_manager.redis.rpush(
        translations_key,
        *[word.lower() for word in random_word.all_translations]
    )

    return True, random_word.first_part


def check_training_answer(
    message,
    state_manager: RedisStateManager
) -> tuple[bool, str]:
    """
    Test the users response in training mode.

    Args:
        message: Users message
        state_manager: State manager

    Returns:
        tuple[bool, str]: (success of the reply, message to the user)
    """
    translations = state_manager.get_translations(message.chat.id)
    if not translations:
        state_manager.set_state(message.chat.id, UserState.IDLE)
        return False, messages.get('training.session_expired')

    user_answer = message.text.strip().lower()
    if user_answer in translations:
        if len(translations) > 1:
            other_translations = [t for t in translations if t != user_answer]
            reply = messages.get(
                'training.other_translations',
                translations=escape_markdown(', '.join(other_translations))
            )
        else:
            reply = messages.get('training.correct')
            state_manager.clear_clue_counter(message.chat.id)
        return True, reply
    else:
        reply = messages.get(
            'training.wrong',
            translations=escape_markdown(', '.join(translations))
        )
        state_manager.clear_clue_counter(message.chat.id)
        return False, reply


@bot.message_handler(func=command_or_text(BotCommands.SWITCH_LANGUAGE))
def handle_switch_language(message) -> None:
    state_manager.set_state(message.chat.id, UserState.SWITCH_LANGUAGE)
    bot.reply_to(
        message,
        messages.get('wait_language'),
        parse_mode='MarkdownV2',
        reply_markup=get_language_keyboard()
    )


@bot.message_handler(commands=[BotCommands.START.command])
def handle_start(message) -> None:
    """Handle /start command."""
    state_manager.set_state(message.chat.id, UserState.IDLE)
    bot.reply_to(
        message,
        messages.get(
            'welcome',
            name=escape_markdown(message.from_user.first_name)
        ),
        parse_mode='MarkdownV2',
        reply_markup=get_main_keyboard()
    )


@bot.message_handler(func=command_or_text(BotCommands.BACK_TO_MENU))
def handle_back_to_menu(message) -> None:
    """Handle back to menu button/command."""
    state_manager.clear_state(message.chat.id)
    bot.reply_to(
        message,
        messages.get('main_menu'),
        reply_markup=get_main_keyboard()
    )


@bot.message_handler(func=command_or_text(BotCommands.ADD_WORD))
def handle_add(message) -> None:
    """Handle add word command/button."""
    state_manager.set_state(message.chat.id, UserState.AWAITING_WORD_PAIR)
    bot.reply_to(
        message,
        messages.get('add_word.prompt'),
        parse_mode='MarkdownV2',
        reply_markup=get_cancel_keyboard()
    )


@bot.message_handler(func=command_or_text(BotCommands.TRAIN))
def handle_train(message) -> None:
    """Handle train command/button"""
    user = Users.get_or_create_user(telegram_id=message.from_user.id)[0]
    success, new_word = start_training_session(
        message.chat.id,
        user.id,
        state_manager
    )

    if success:
        # Preparing a message with a random word and giving it to the user
        word_to_translate = messages.get(
            'training.word_prompt',
            word=escape_markdown(new_word)
        )
        bot.send_message(
            message.chat.id,
            word_to_translate,
            parse_mode='MarkdownV2',
            reply_markup=training_keyboard()
        )
    else:
        # The errors is that the user has no words.
        bot.send_message(
            message.chat.id,
            new_word,  # here new_word contains error message
            parse_mode='MarkdownV2',
            reply_markup=get_main_keyboard()
        )


@bot.message_handler(func=command_or_text(BotCommands.CLUE))
def handle_clue(message) -> None:
    # Check users status
    status = state_manager.get_state(message.chat.id)
    state = UserState(status)

    if state != UserState.TRAINING:
        bot.reply_to(
            message,
            messages.get('errors.clue_error'),
            reply_markup=get_main_keyboard()
        )
        return

    translations = state_manager.get_translations(message.chat.id)
    if not translations:
        # If no translations, start a new training.
        handle_train(message)
        return

    word = translations[0]
    state_manager.increase_clue_counter(message.chat.id)
    clue_counter = state_manager.get_clue_counter(message.chat.id)

    if len(word) <= clue_counter:
        # If all the letters are open, we show the correct answer and go to the next word
        bot.reply_to(
            message,
            messages.get(
                'training.wrong',
                translations=escape_markdown(', '.join(translations))
            ),
            parse_mode='MarkdownV2'
        )
        state_manager.clear_clue_counter(message.chat.id)
        handle_train(message)
        return

    if clue_counter == 1:
        word = f"{word[0]}{'*' * (len(word) - 1)}"
    else:
        first_part = word[:clue_counter - clue_counter // 2]
        last_part = word[-(clue_counter // 2):]
        word = f'{first_part}{"*" * (len(word) - clue_counter)}{last_part}'

    bot.reply_to(
        message,
        messages.get(
            'training.clue',
            word=escape_markdown(word)
        ),
        parse_mode='MarkdownV2',
        reply_markup=training_keyboard()
    )


@bot.message_handler(func=lambda message: True)
def handle_message(message: Message) -> None:
    """Handle all other messages"""

    global messages
    current_state = state_manager.get_state(message.chat.id)

    if not current_state:
        bot.reply_to(
            message,
            messages.get('errors.use_menu'),
            reply_markup=get_main_keyboard()
        )
        return

    try:
        state = UserState(current_state)
    except ValueError:
        state_manager.clear_state(message.chat.id)
        bot.reply_to(
            message,
            messages.get('errors.restart'),
            parse_mode='MarkdownV2',
            reply_markup=get_main_keyboard()
        )
        return

    match state:
        case UserState.IDLE:
            bot.reply_to(
                message,
                messages.get('errors.use_menu'),
                reply_markup=get_main_keyboard()
            )

        case UserState.AWAITING_WORD_PAIR:
            success, answer = process_new_word_pair(message, state_manager)
            bot.reply_to(
                message,
                answer,
                parse_mode='MarkdownV2',
                reply_markup=get_main_keyboard() if success else get_cancel_keyboard()
            )

        case UserState.TRAINING:
            success, reply = check_training_answer(message, state_manager)
            bot.reply_to(
                message,
                reply,
                parse_mode='MarkdownV2'
            )

            handle_train(message)
        case UserState.SWITCH_LANGUAGE:
            language_to_set = message.text
            # Add check that such language is in SUPPORTED_LANGUAGES
            if language_to_set not in Messages.SUPPORTED_LANGUAGES:
                bot.reply_to(
                    message,
                    message.get('errors.language_doesnt_exist'),
                    parse_mode='MarkdownV2',
                    reply_markup=get_main_keyboard()
                )
            user, _ = Users.get_or_create_user(telegram_id=message.chat.id)
            user.set_language(new_language=language_to_set)
            language = user.get_language()
            messages = Messages(language)
            bot.reply_to(
                message,
                messages.get("language_has_been_changed"),
                parse_mode='MarkdownV2',
                reply_markup=get_main_keyboard()
            )


if __name__ == '__main__':
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Bot stopped due to error: {e}")
