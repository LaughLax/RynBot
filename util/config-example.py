# To use, rename this file to 'config.py'.

prefix = '!'
activity = 'mind games'

# Users
owner_id = 185095270986547200

# Servers
ryn_server_id = 329681826618671104

# Channels
ryn_starboard_id = 355477159629946882
pub_starboard_id = 382661096303230976
bot_log_id = 382657596458270720

cogs_core = ['cogs.base',
             'cogs.owner',
             'cogs.logs',
             'util.database']

cogs_other = ['cogs.chart',
              'cogs.data',
              'cogs.my_server',
              'cogs.server',
              'cogs.stars',
              'cogs.polls']

# URI for SQLAlchemy to connect to database server
db_uri = 'dialect+driver://username:password@host:port/database'
