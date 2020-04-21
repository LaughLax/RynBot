import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


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


class ServerConfig(Base):
    __tablename__ = 'server_config'

    server = sql.Column(sql.BigInteger,
                        primary_key=True,
                        unique=True,
                        nullable=False)
    prefix = sql.Column(sql.String,
                        nullable=True)
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
