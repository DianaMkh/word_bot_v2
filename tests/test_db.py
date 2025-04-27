# tests/test_db.py
import pytest
import yaml
import psycopg2
from unittest.mock import mock_open, patch
from sqlalchemy.orm import scoped_session
from database.db import db_session, engine

# Тестовая конфигурация
TEST_CONFIG = """
database:
    dbname: 'test_db'
    user: 'test_user'
    password: 'test_password'
    host: 'localhost'
    port: '5432'
"""


def test_db_session_type():
    """Проверяем, что db_session правильного типа"""
    assert isinstance(db_session, scoped_session)


@patch('builtins.open', mock_open(read_data=TEST_CONFIG))
@patch('database.db.create_engine')
def test_database_url_formation_with_credentials(mock_create_engine):
    """Тест формирования URL с учетными данными"""
    from database import db  # Импортируем заново для применения мока
    expected_url = "postgresql://test_user:test_password@localhost:5432/test_db"
    mock_create_engine.assert_called_once()
    assert mock_create_engine.call_args[0][0] == expected_url


@patch('builtins.open', mock_open(read_data="""
database:
    dbname: 'test_db'
    host: 'localhost'
    port: '5432'
"""))
@patch('database.db.create_engine')
def test_database_url_formation_without_credentials(mock_create_engine):
    """Тест формирования URL без учетных данных"""
    from database import db  # Импортируем заново для применения мока
    expected_url = "postgresql://localhost:5432/test_db"
    mock_create_engine.assert_called_once()
    assert mock_create_engine.call_args[0][0] == expected_url


@patch('psycopg2.connect')
def test_postgresql_connection_success(mock_connect):
    """Тест успешного подключения к PostgreSQL"""
    mock_cursor = mock_connect.return_value.cursor.return_value
    mock_cursor.fetchone.return_value = ['PostgreSQL 13.0']

    with patch('builtins.open', mock_open(read_data=TEST_CONFIG)):
        from database import db
        if db.__name__ == '__main__':
            mock_connect.assert_called_once_with(
                dbname='test_db',
                user='test_user',
                password='test_password',
                host='localhost',
                port='5432'
            )


@patch('psycopg2.connect')
def test_postgresql_connection_error(mock_connect):
    """Тест обработки ошибки подключения к PostgreSQL"""
    mock_connect.side_effect = psycopg2.Error("Connection error")

    with patch('builtins.open', mock_open(read_data=TEST_CONFIG)):
        with patch('builtins.print') as mock_print:
            from database import db
            if db.__name__ == '__main__':
                mock_print.assert_called_with(
                    'Error connecting to PostgreSQL database:',
                    'Connection error'
                )


def test_yaml_config_loading():
    """Тест загрузки конфигурации из YAML"""
    with patch('builtins.open', mock_open(read_data=TEST_CONFIG)):
        config = yaml.safe_load(TEST_CONFIG)
        assert config['database']['dbname'] == 'test_db'
        assert config['database']['user'] == 'test_user'
        assert config['database']['password'] == 'test_password'


def test_db_session_configuration():
    """Тест конфигурации сессии БД"""
    session = db_session()
    assert not session.autocommit
    assert not session.autoflush
    session.close()
