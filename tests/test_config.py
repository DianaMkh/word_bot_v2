# tests/test_config.py
import pytest
from config import Config


def test_config_loading():
    """Test configuration loading"""
    config = Config()

    # Test Redis config
    assert hasattr(config, 'redis')
    assert config.redis.host is not None
    assert config.redis.port is not None

    # Test Database config
    assert hasattr(config, 'database')
    assert config.database.dbname is not None
    assert config.database.host is not None


def test_config_environment_override(monkeypatch):
    """Test environment variables override config"""
    # Set environment variables
    monkeypatch.setenv('REDIS_HOST', 'test_host')
    monkeypatch.setenv('REDIS_PORT', '6380')

    config = Config()
    assert config.redis.host == 'test_host'
    assert config.redis.port == 6380
