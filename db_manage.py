import os

import sqlalchemy
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class People(Base):
    __tablename__ = 'people'

    id = Column(Integer, primary_key=True)
    first_name = Column(String(length=40), nullable=False)
    last_name = Column(String(length=40), nullable=False)
    age = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False, unique=True)
    url_profile = Column(String(length=40), nullable=False)

    def __str__(self):
        return f'User_VK: {self.first_name} {self.last_name}, user_id: {self.user_id}'


def create_table(engine):
    """Создает таблицы"""
    ...


def create_db():
    """Создает базу данных"""
    LOGIN = os.getenv('DB_LOGIN')
    PASSWORD = os.getenv('DB_PASSWORD')
    HOST = os.getenv('DB_HOST')
    PORT = os.getenv('DB_PORT')
    DATABASE = 'vk_search_result'

    DSN = f'postgresql://{LOGIN}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}'
    engine = sqlalchemy.create_engine(DSN)

    create_table(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    session.close()
