from util import config

import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from contextlib import contextmanager

Base = declarative_base()


class DBHandler:
    def __init__(self):
        self.engine = sql.create_engine(config.db_uri)
        self.SessionFactory = sessionmaker(bind=self.engine)

        Base.metadata.create_all(self.engine)

    @contextmanager
    def get_session(self):
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()


class Population(Base):
    __tablename__ = 'server_pop'

    server = sql.Column(sql.BigInteger,
                        primary_key=True,
                        nullable=False)
    timestamp = sql.Column(sql.DateTime,
                           primary_key=True,
                           nullable=False)
    user_count = sql.Column(sql.Integer,
                            nullable=False)

