import database
import sys
from sqlmodel import SQLModel, Session, create_engine
from database.config import get_settings
from sqlalchemy import text
from contextlib import contextmanager


engine = create_engine(url=get_settings().DATABASE_URL_pymysql,
                       echo=True,
                       pool_size=5,
                       max_overflow=10)


def get_database_engine():
    settings = get_settings()
    return engine

@contextmanager
def get_session():
    with Session(engine) as session:
        yield session

def init_db(drop_all: bool = False) -> None:
    # SQLModel.metadata.drop_all(engine)
    # SQLModel.metadata.create_all(engine)

    try:
        engine = get_database_engine()
        if drop_all:
            with engine.begin() as conn:
                # Отключаем проверку внешних ключей
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
                # Сначала удаляем таблицы с foreign keys
                conn.execute(text("DROP TABLE IF EXISTS balance"))
                conn.execute(text("DROP TABLE IF EXISTS trans"))
                conn.execute(text("DROP TABLE IF EXISTS predictionresult"))
                # Затем основную таблицу
                conn.execute(text("DROP TABLE IF EXISTS user"))
                conn.execute(text("DROP TABLE IF EXISTS events"))
                # Включаем проверку обратно
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        raise