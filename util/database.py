from util import config

import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm.exc import NoResultFound

from contextlib import contextmanager

Base = declarative_base()


class DBHandler:
    def __init__(self, bot):
        self.engine = sql.create_engine(config.db_uri, pool_recycle=3600, pool_pre_ping=True)
        self.SessionFactory = sessionmaker(bind=self.engine)

        self.execute = bot.loop.run_in_executor

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

    def _get_custom_role_list(self, guild_id):
        with self.get_session() as db:
            try:
                custom_list = db.query(CustomRoleChart.role).\
                    filter(CustomRoleChart.server == guild_id).\
                    all()
                custom_list = [a[0] for a in custom_list]
            except NoResultFound:
                return []

        return custom_list

    async def get_custom_role_list(self, guild_id):
        return await self.execute(None, self._get_custom_role_list, guild_id)


class Population(Base):
    __tablename__ = 'server_pop_hourly'

    server = sql.Column(sql.BigInteger,
                        primary_key=True,
                        nullable=False)
    datetime = sql.Column(sql.DateTime,
                          primary_key=True,
                          nullable=False)
    user_count = sql.Column(sql.Integer,
                            nullable=False)


class ServerConfig(Base):
    __tablename__ = 'server_config'

    server = sql.Column(sql.BigInteger,
                        primary_key=True,
                        unique=True,
                        nullable=False)
    starboard = sql.Column(sql.BigInteger,
                           nullable=True)
    star_threshold = sql.Column(sql.SmallInteger,
                                default=1,
                                nullable=False)

    stars = relationship('Star', back_populates='server_rel')
    custom_role_chart = relationship('CustomRoleChart', back_populates='server_rel')


class Star(Base):
    __tablename__ = 'stars'

    card = sql.Column(sql.BigInteger,
                      primary_key=True,
                      autoincrement=False,
                      unique=True,
                      nullable=False)
    server = sql.Column(sql.BigInteger,
                        sql.ForeignKey('server_config.server'),
                        nullable=False)
    channel = sql.Column(sql.BigInteger,
                         nullable=False)
    message = sql.Column(sql.BigInteger,
                         unique=True,
                         nullable=False)
    author = sql.Column(sql.BigInteger,
                        nullable=False)
    timestamp = sql.Column(sql.DateTime,
                           nullable=False)

    server_rel = relationship('ServerConfig', back_populates='stars')


class CustomRoleChart(Base):
    __tablename__ = 'server_role_chart'

    server = sql.Column(sql.BigInteger,
                        sql.ForeignKey('server_config.server'),
                        nullable=False)
    role = sql.Column(sql.BigInteger,
                      primary_key=True,
                      unique=True,
                      nullable=False)

    server_rel = relationship('ServerConfig', back_populates='custom_role_chart')


def setup(bot):
    bot.db = DBHandler(bot)


def teardown(bot):
    bot.db = None
