# tests/test_state.py
import pytest
from main import RedisStateManager, UserState


def test_state_manager_initialization(redis_client, config):
    """Test RedisStateManager initialization"""
    state_manager = RedisStateManager(redis_client, config.redis)
    assert state_manager.redis == redis_client
    assert state_manager.config == config.redis


def test_get_key_format(redis_client, config):
    """Test _get_key method"""
    state_manager = RedisStateManager(redis_client, config.redis)
    chat_id = 123456
    expected_key = f"{config.redis.prefix}user:{chat_id}"
    assert state_manager._get_key(chat_id) == expected_key


def test_state_management_flow(redis_client, config):
    """Test full state management flow"""
    state_manager = RedisStateManager(redis_client, config.redis)
    chat_id = 123456

    # Initial state should be None
    assert state_manager.get_state(chat_id) is None

    # Set and verify each state
    for state in UserState:
        state_manager.set_state(chat_id, state)
        assert state_manager.get_state(chat_id) == state.value

    # Clear state
    state_manager.clear_state(chat_id)
    assert state_manager.get_state(chat_id) is None


def test_translations_management(redis_client, config):
    """Test translations management"""
    state_manager = RedisStateManager(redis_client, config.redis)
    chat_id = 123456
    translations = ["hello", "hi", "hey"]

    # Set translations
    key = f"{state_manager._get_key(chat_id)}:translations"
    redis_client.rpush(key, *translations)

    # Verify translations
    stored_translations = state_manager.get_translations(chat_id)
    assert stored_translations == translations

    # Clear and verify
    state_manager.clear_state(chat_id)
    assert state_manager.get_translations(chat_id) == []
