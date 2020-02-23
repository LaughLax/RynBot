from discord import Activity, ActivityType
from discord.ext.commands import Bot, DefaultHelpCommand
from util import config
from concurrent.futures import ProcessPoolExecutor
# import logging

if __name__ == '__main__':
    game = Activity(type=ActivityType.playing, name=config.activity)

    bot = Bot(command_prefix=config.prefix,
              owner_id=config.owner_id,
              activity=game,
              help_command=DefaultHelpCommand(command_attrs={'aliases': ['halp']}))

    @bot.event
    async def on_ready():

        print('Logged in as')
        print(bot.user.name)
        print(bot.user.id)
        print('------')

        if 'cogs.logs' not in bot.extensions:
            print('Logs cog failed to load!')
            chan = bot.get_channel(config.bot_log_id)
            await chan.send("Help me <@{}>! I failed to load my logging cog!".format(config.owner_id))

    # logger = logging.getLogger('discord')
    # logger.setLevel(logging.WARNING)
    # handler = logging.FileHandler(filename=config.logfile, encoding='utf-8', mode='w')
    # handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    # logger.addHandler(handler)

    for extension in config.cogs_core:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}.'.format(extension))
            print(e)

    bot.process_pool = ProcessPoolExecutor(max_workers=config.max_process_workers)

    bot.run(config.token)
