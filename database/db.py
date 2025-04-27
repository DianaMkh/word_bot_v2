import psycopg2
import yaml

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


with open('configs.yaml', 'r') as file:
    # Parse configs file
    configs = yaml.safe_load(file)
    configs = configs.get('database', {})
    dbname = configs.get('dbname')
    user = configs.get('user')
    password = configs.get('password')
    host = configs.get('host')
    port = configs.get('port')
    url = f"postgresql://{host}:{port}/{dbname}"
    if user and password:
        url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


engine = create_engine(url)

# Сущность подключения к базе, отсюда она будет импортироваться
# всюду где она нужна
db_session = scoped_session(
    sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False
    )
)
Base = declarative_base()

if __name__ == '__main__':
    # Test connection
    connection = None

    try:
        connection = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        with connection.cursor() as cursor:
            cursor.execute('SELECT version();')
            db_version = cursor.fetchone()
            print('PostgreSQL version:', db_version[0])

    except Exception as error:
        print('Error connecting to PostgreSQL database:', error)

    finally:
        if connection is not None:
            connection.close()
