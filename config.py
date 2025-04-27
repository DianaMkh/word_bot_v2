import os
from dotenv import load_dotenv
import yaml
from dataclasses import dataclass
from typing import Optional


@dataclass
class RedisConfig:
    host: str
    port: int
    password: str
    db: int
    ttl: int
    prefix: str


@dataclass
class DatabaseConfig:
    dbname: str
    user: str
    password: str
    host: str
    port: str
    db_url: str


class Config:
    def __init__(self):
        load_dotenv()

        # Загрузка конфигурации из файла
        with open('configs.yaml', 'r') as file:
            config = yaml.safe_load(file)

        # Конфигурация Redis
        redis_config = config['redis']
        self.redis = RedisConfig(
            host=os.getenv('REDIS_HOST', redis_config['host']),
            port=int(os.getenv('REDIS_PORT', redis_config['port'])),
            password=os.getenv('REDIS_PASSWORD', redis_config['password']),
            db=int(os.getenv('REDIS_DB', redis_config['db'])),
            ttl=int(os.getenv('REDIS_TTL', redis_config['ttl'])),
            prefix=redis_config['prefix']
        )

        # Конфигурация базы данных
        db_config = config['database']
        self.database = DatabaseConfig(
            dbname=db_config['dbname'],
            user=db_config['user'],
            password=db_config['password'],
            host=db_config['host'],
            port=db_config['port'],
            db_url=db_config['db_url']
        )


# Создаем экземпляр конфигурации при импорте
config = Config()
