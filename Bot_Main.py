import discord
from discord.ext import commands
from util import config
import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename=config.logfile, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

game = discord.Activity(type=discord.ActivityType.playing, name=config.activity)

bot = commands.Bot(command_prefix=config.prefix,
                   owner_id=config.owner_id,
                   activity=game,
                   help_command=commands.DefaultHelpCommand(command_attrs={'aliases': ['halp']}))

if __name__ == '__main__':
    for extension in config.cogs_core:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}.'.format(extension))
            print(e)


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


bot.run(config.token)
