from contextlib import contextmanager
from functools import wraps

import sqlalchemy as sql
from dogpile.cache import make_region
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from database.models import *
from util import config


class DBHandler:
    region = make_region().configure('dogpile.cache.redis')

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

    def async_via_threadpool(func):
        @wraps(func)
        async def wrapper_make_async(self, *args, **kwargs):
            return await self.execute(None, func, self, *args, **kwargs)
        return wrapper_make_async

    def provide_db(func):
        @wraps(func)
        def wrapper_provide_db(self, *args, **kwargs):
            with self.get_session() as db:
                return func(self, db, *args, **kwargs)
        return wrapper_provide_db

    @staticmethod
    def get_server_cfg(db, guild_id):
        try:
            cfg = db.query(ServerConfig).filter(ServerConfig.server == guild_id).one_or_none()
        except MultipleResultsFound as e:
            raise e

        if not cfg:
            cfg = ServerConfig(server=guild_id)
            db.add(cfg)

        return cfg

    @async_via_threadpool
    @provide_db
    def get_db_size(self,  db):
        res = db.execute(
            "SELECT sum((data_length + index_length) / 1024 / 1024) "
            "AS Size "
            "FROM information_schema.tables "
            "WHERE table_schema = 'rynbot' "
            "GROUP BY table_schema;"
        ).first().values()[0]
        return float(res)

    @async_via_threadpool
    @provide_db
    def get_custom_role_list(self, db, guild_id):
        try:
            custom_list = db.query(CustomRoleChart.role).\
                filter(CustomRoleChart.server == guild_id).\
                all()
            custom_list = [a[0] for a in custom_list]
        except NoResultFound:
            return []

        return custom_list

    @async_via_threadpool
    @provide_db
    def create_task(self, db, guild_id, channel_id, task_name, command, first_run_msg_id):
        self.get_server_cfg(db, guild_id)

        row = ScheduledTasks(server=guild_id,
                             channel=channel_id,
                             task_name=task_name,
                             command=command,
                             last_run_msg_id=first_run_msg_id)
        db.add(row)

    @async_via_threadpool
    @provide_db
    def update_task(self, db, guild_id, task_name, last_run_msg_id):
        try:
            row = db.query(ScheduledTasks).\
                filter(ScheduledTasks.server == guild_id).\
                filter(ScheduledTasks.task_name == task_name).\
                one_or_none()
        except MultipleResultsFound as e:
            raise e

        row.last_run_msg_id = last_run_msg_id
        db.add(row)

    @async_via_threadpool
    @provide_db
    def delete_task(self, db, guild_id, task_name):
        try:
            row = db.query(ScheduledTasks).\
                filter(ScheduledTasks.server == guild_id).\
                filter(ScheduledTasks.task_name == task_name).\
                one_or_none()
        except MultipleResultsFound as e:
            raise e

        db.delete(row)

    @async_via_threadpool
    @provide_db
    def fetch_task_list(self, db, guild_id = None):
        try:
            rows = db.query(ScheduledTasks.server,
                            ScheduledTasks.channel,
                            ScheduledTasks.task_name,
                            ScheduledTasks.command,
                            ScheduledTasks.last_run_msg_id)
            if guild_id is not None:
                rows = rows.filter(ScheduledTasks.server == guild_id)
            rows = rows.all()
            # rows = [a[0] for a in rows]
        except NoResultFound as e:
            raise e

        return rows

    @async_via_threadpool
    @provide_db
    def fetch_population_history(self, db, server_id):
        rows = db.query(Population.datetime, Population.user_count).\
            filter(Population.server == server_id).\
            order_by(Population.datetime).\
            all()

        return rows

    @async_via_threadpool
    @region.cache_on_arguments()
    @provide_db
    def fetch_starboard_channel(self, db, server_id):
        try:
            starboard = db.query(ServerConfig.starboard).\
                filter(ServerConfig.server == server_id).\
                one()[0]
        except NoResultFound:
            starboard = None
        except MultipleResultsFound as e:
            raise e

        return starboard

    @async_via_threadpool
    @region.cache_on_arguments()
    @provide_db
    def fetch_star_threshold(self, db, server_id):
        try:
            star_threshold = db.query(ServerConfig.star_threshold).\
                filter(ServerConfig.server == server_id).\
                one()[0]
        except NoResultFound:
            star_threshold = 1
        except MultipleResultsFound as e:
            raise e

        return star_threshold

    @async_via_threadpool
    @provide_db
    def fetch_star_entry(self, db, server_id, message_id):
        try:
            star = db.query(Star.card).\
                filter(Star.server == server_id).\
                filter(Star.message == message_id).\
                one()
        except NoResultFound:
            return None
        except MultipleResultsFound as e:
            raise e

        return star

    @async_via_threadpool
    @provide_db
    def delete_star_entry(self, db, server_id, message_id):
        try:
            star = db.query(Star).\
                filter(Star.server == server_id).\
                filter(Star.message == message_id).\
                one()
        except MultipleResultsFound as e:
            raise e

        db.delete(star)

    @async_via_threadpool
    @provide_db
    def create_star_entry(self, db, server_id, channel_id, message_id, author_id, msg_timestamp, card_id):
        try:
            star = Star(server=server_id,
                        channel=channel_id,
                        message=message_id,
                        author=author_id,
                        timestamp=msg_timestamp,
                        card=card_id)
            db.add(star)
        except Exception as e:
            raise e


def setup(bot):
    bot.db = DBHandler(bot)


def teardown(bot):
    bot.db = None
