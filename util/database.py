from util import config

import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

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

    def get_server_cfg(self, db, guild_id):
        try:
            cfg = db.query(ServerConfig).filter(ServerConfig.server == guild_id).one_or_none()
        except MultipleResultsFound as e:
            raise e

        if not cfg:
            cfg = ServerConfig(server=guild_id)
            db.add(cfg)

        return cfg

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

    def _create_task(self, guild_id, channel_id, task_name, command, first_run_msg_id):
        with self.get_session() as db:
            self.get_server_cfg(db, guild_id)

            row = ScheduledTasks(server=guild_id,
                                 channel=channel_id,
                                 task_name=task_name,
                                 command=command,
                                 last_run_msg_id=first_run_msg_id)
            try:
                db.add(row)
            except Exception as e:
                raise e

    def _update_task(self, guild_id, task_name, last_run_msg_id):
        with self.get_session() as db:
            try:
                row = db.query(ScheduledTasks).\
                    filter(ScheduledTasks.server == guild_id).\
                    filter(ScheduledTasks.task_name == task_name).\
                    one_or_none()
            except MultipleResultsFound as e:
                raise e

            row.last_run_msg_id = last_run_msg_id
            db.add(row)

    def _delete_task(self, guild_id, task_name):
        with self.get_session() as db:
            try:
                row = db.query(ScheduledTasks).\
                    filter(ScheduledTasks.server == guild_id).\
                    filter(ScheduledTasks.task_name == task_name).\
                    one_or_none()
            except MultipleResultsFound as e:
                raise e

            db.delete(row)

    def _fetch_task_list(self):
        with self.get_session() as db:
            try:
                rows = db.query(ScheduledTasks).all()
            except NoResultFound as e:
                raise e

        return rows

    async def get_custom_role_list(self, guild_id):
        return await self.execute(None, self._get_custom_role_list, guild_id)

    async def create_task(self, guild_id, channel_id, task_name, command, first_run_msg_id):
        return await self.execute(None, self._schedule_task, guild_id, channel_id, task_name, command, first_run_msg_id)

    async def update_task(self, guild_id, task_name, last_run_msg_id):
        return await self.execute(None, self._update_task, guild_id, task_name, last_run_msg_id)

    async def delete_task(self, guild_id, task_name):
        return await self.execute(None, self._delete_task, guild_id, task_name)

    async def fetch_task_list(self):
        return await self.execute(None, self._fetch_task_list)


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
    scheduled_tasks = relationship('ScheduledTasks', back_populates='server_rel')


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


class ScheduledTasks(Base):
    __tablename__ = 'scheduled_tasks'

    server = sql.Column(sql.BigInteger,
                        sql.ForeignKey('server_config.server'),
                        primary_key=True,
                        nullable=False)
    channel = sql.Column(sql.BigInteger,
                         nullable=False)
    task_name = sql.Column(sql.String(32),
                           primary_key=True,
                           nullable=False)
    command = sql.Column(sql.String(32),
                         nullable=False)
    last_run_msg_id = sql.Column(sql.BigInteger,
                                 unique=True,
                                 nullable=False)

    server_rel = relationship('ServerConfig', back_populates='scheduled_tasks')


def setup(bot):
    bot.db = DBHandler(bot)


def teardown(bot):
    bot.db = None
