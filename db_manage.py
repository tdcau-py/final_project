import os

import sqlalchemy
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class People(Base):
    __tablename__ = 'people'

    id = Column(Integer, primary_key=True)
    first_name = Column(String(length=40), nullable=False)
    last_name = Column(String(length=40), nullable=False)
    vk_id = Column(Integer, nullable=False, unique=True)
    url_profile = Column(String(length=40), nullable=False)

    def __str__(self):
        return f'User_VK: {self.first_name} {self.last_name}, user_id: {self.user_id}'


def db_connection():
    """Поключение к БД"""
    LOGIN = os.getenv('DB_LOGIN')
    PASSWORD = os.getenv('DB_PASSWORD')
    HOST = os.getenv('DB_HOST')
    PORT = os.getenv('DB_PORT')
    DATABASE = 'vkinder_db'

    DSN = f'postgresql://{LOGIN}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}'
    engine = sqlalchemy.create_engine(DSN)
    return engine


def create_table(engine):
    """Создает таблицы"""
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def add_searching_users(session, first_name, last_name, vk_id, url_profile):
    """Добавление найденных пользователей в таблицу БД"""
    user = People(first_name=first_name,
                  last_name=last_name,
                  vk_id=vk_id,
                  url_profile=url_profile, )

    session.add(user)
    session.commit()

    return True


def check_repeated_users(session, vk_user_id):
    """Проверка повторяющихся анкет"""
    vk_user_id = int(vk_user_id)

    if session.query(People.vk_id).filter_by(vk_id=vk_user_id).first():
        return True

    else:
        return False
