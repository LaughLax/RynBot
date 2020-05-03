from contextlib import contextmanager
from functools import wraps

from dogpile.cache import make_region
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.exc import NoResultFound

from database.models import *
from util import config


def async_via_threadpool(func):
    @wraps(func)
    async def wrapper_make_async(self, *args, **kwargs):
        return await self.execute(None, func, self, *args, **kwargs)

    return wrapper_make_async


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
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @async_via_threadpool
    def get_db_size(self):
        with self.get_session() as db:
            res = db.execute(
                "SELECT sum((data_length + index_length) / 1024 / 1024) "
                "AS Size "
                "FROM information_schema.tables "
                "WHERE table_schema = 'rynbot' "
                "GROUP BY table_schema;"
            ).first().values()[0]
            return float(res)

    '''
    BEGIN GUILD CONFIGURATION METHODS
    '''

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
    def set_prefix(self, guild_id, prefix):
        self.get_prefix.invalidate(self, guild_id)
        with self.get_session() as db:
            cfg = self.get_server_cfg(db, guild_id)
            cfg.prefix = prefix
            db.add(cfg)

    @async_via_threadpool
    @region.cache_on_arguments()
    def get_prefix(self, guild_id):
        with self.get_session() as db:
            cfg = self.get_server_cfg(db, guild_id)
            return cfg.prefix

    @async_via_threadpool
    def set_mod_role(self, guild_id, role_id):
        self.get_mod_role.invalidate(self, guild_id)
        with self.get_session() as db:
            cfg = self.get_server_cfg(db, guild_id)
            cfg.mod_role = role_id
            db.add(cfg)

    @async_via_threadpool
    @region.cache_on_arguments()
    def get_mod_role(self, guild_id):
        with self.get_session() as db:
            cfg = self.get_server_cfg(db, guild_id)
            return cfg.mod_role

    @async_via_threadpool
    def set_mute_role(self, guild_id, role_id):
        self.get_mute_role.invalidate(self, guild_id)
        with self.get_session() as db:
            cfg = self.get_server_cfg(db, guild_id)
            cfg.mute_role = role_id
            db.add(cfg)

    @async_via_threadpool
    @region.cache_on_arguments()
    def get_mute_role(self, guild_id):
        with self.get_session() as db:
            cfg = self.get_server_cfg(db, guild_id)
            return cfg.mute_role

    @async_via_threadpool
    def set_log_channel(self, guild_id, channel_id):
        self.get_log_channel.invalidate(self, guild_id)
        with self.get_session() as db:
            cfg = self.get_server_cfg(db, guild_id)
            cfg.log_channel = channel_id
            db.add(cfg)

    @async_via_threadpool
    @region.cache_on_arguments()
    def get_log_channel(self, guild_id):
        with self.get_session() as db:
            cfg = self.get_server_cfg(db, guild_id)
            return cfg.log_channel

    @async_via_threadpool
    def set_starboard_channel(self, server_id, channel_id):
        self.get_starboard_channel.invalidate(self, server_id)
        with self.get_session() as db:
            cfg = self.get_server_cfg(db, server_id)
            cfg.starboard = channel_id
            db.add(cfg)

    @async_via_threadpool
    @region.cache_on_arguments()
    def get_starboard_channel(self, server_id):
        with self.get_session() as db:
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
    def set_star_threshold(self, server_id, min_stars):
        self.get_star_threshold.invalidate(self, server_id)
        with self.get_session() as db:
            cfg = self.get_server_cfg(db, server_id)
            cfg.star_threshold = min_stars
            db.add(cfg)

    @async_via_threadpool
    @region.cache_on_arguments()
    def get_star_threshold(self, server_id):
        with self.get_session() as db:
            try:
                star_threshold = db.query(ServerConfig.star_threshold).\
                    filter(ServerConfig.server == server_id).\
                    one()[0]
            except NoResultFound:
                star_threshold = 1
            except MultipleResultsFound as e:
                raise e

            return star_threshold

    '''
    END GUILD CONFIGURATION METHODS
    
    BEGIN TASK METHODS
    '''

    @async_via_threadpool
    def get_custom_role_list(self, guild_id):
        with self.get_session() as db:
            try:
                custom_list = db.query(CustomRoleChart.role).\
                    filter(CustomRoleChart.server == guild_id).\
                    all()
                custom_list = [a[0] for a in custom_list]
            except NoResultFound:
                return []

            return custom_list

    @async_via_threadpool
    def create_task(self, guild_id, channel_id, task_name, command, first_run_msg_id):
        with self.get_session() as db:
            self.get_server_cfg(db, guild_id)

            row = ScheduledTasks(server=guild_id,
                                 channel=channel_id,
                                 task_name=task_name,
                                 command=command,
                                 last_run_msg_id=first_run_msg_id)
            db.add(row)

    @async_via_threadpool
    def update_task(self, guild_id, task_name, last_run_msg_id):
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

    @async_via_threadpool
    def delete_task(self, guild_id, task_name):
        with self.get_session() as db:
            try:
                row = db.query(ScheduledTasks).\
                    filter(ScheduledTasks.server == guild_id).\
                    filter(ScheduledTasks.task_name == task_name).\
                    one_or_none()
            except MultipleResultsFound as e:
                raise e

            db.delete(row)

    @async_via_threadpool
    def get_task_list(self, guild_id=None):
        with self.get_session() as db:
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

    '''
    END TASK METHODS
    
    BEGIN POPULATION TRACKING METHODS
    '''

    @async_via_threadpool
    def add_population_row(self, guild_id, time, user_count):
        with self.get_session() as db:
            row = Population(server=guild_id,
                             datetime=time,
                             user_count=user_count)
            db.merge(row)

    @async_via_threadpool
    def get_population_history(self, server_id):
        with self.get_session() as db:
            rows = db.query(Population.datetime, Population.user_count).\
                filter(Population.server == server_id).\
                order_by(Population.datetime).\
                all()

            return rows

    '''
    END POPULATION TRACKING METHODS
    
    BEGIN STARBOARD METHODS
    '''

    @async_via_threadpool
    def get_star_entry(self, server_id, message_id):
        with self.get_session() as db:
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
    def delete_star_entry(self, server_id, message_id):
        with self.get_session() as db:
            try:
                star = db.query(Star).\
                    filter(Star.server == server_id).\
                    filter(Star.message == message_id).\
                    one()
            except MultipleResultsFound as e:
                raise e

            db.delete(star)

    @async_via_threadpool
    def create_star_entry(self, server_id, channel_id, message_id, author_id, msg_timestamp, card_id):
        with self.get_session() as db:
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
